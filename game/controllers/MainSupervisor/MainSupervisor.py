# Auto install any pip modules used throughout the code base
import AutoInstall
AutoInstall._import("np", "numpy")
AutoInstall._import("cl", "termcolor")
AutoInstall._import("req", "requests")
AutoInstall._import("overrides", "overrides")
AutoInstall._import("PIL", "PIL", "pillow")

import os
import shutil
import struct
from threading import Thread
import shutil
import json
import time
import subprocess
import requests as req

from controller import Supervisor
from controller import Emitter
from controller import Receiver

import MapScorer
import ControllerUploader

from Tools import *
from ConsoleLog import Console
from Logger import Logger
from ProtoGenerator import generate_robot_proto
from MapAnswer import MapAnswer, pretty_print_map
from Config import Config
from Camera import *
from Tile import *
from Victim import *
from Robot import *
from Recorder import Recorder
from Test import TestRunner
from RobotWindowSender import RWSender
from ThumbnailWriter import export_map_to_img
from DockerHelper import run_docker_container

from typing import Sequence, cast

from controller.wb import wb

class GameState(Enum):
    MATCH_NOT_STARTED = 1
    MATCH_RUNNING = 2
    MATCH_FINISHED = 3
    MATCH_PAUSED = 4


class Erebus(Supervisor):

    ROBOT_NAME = "Erebus_Bot"
    TIME_STEP = 16
    DEFAULT_MAX_MULT = 1.0

    def __init__(self):
        super().__init__()

        # Version info
        self._stream = 24
        self.version = "24.1.0"

        # Start controller uploader
        uploader: Thread = Thread(target=ControllerUploader.start, daemon=True)
        uploader.start()

        # Robot window send text wrapper
        self.rws: RWSender = RWSender(self)
        
        # Get the config data from config.txt
        config_file_path = get_file_path(
            "controllers/MainSupervisor/config.txt",
            "config.txt"
        )
        self.config: Config = self._get_config(config_file_path)
        
        self.simulation_mode = self.SIMULATION_MODE_REAL_TIME
        
        # Send message to robot window to perform setup
        self.rws.send("startup")
        self._get_erebus_version()

        # Subprocess for running controllers in docker containers
        self._docker_process: Optional[subprocess.Popen] = None

        self._game_state: GameState = GameState.MATCH_NOT_STARTED
        self._last_frame: Optional[bool] = False
        self._first_frame: bool = True
        self._robot_initialised: bool = False

        # How long the game has been running for
        self.time_elapsed: float = 0.0
        self._last_time: float = -1.0
        self._real_time_elapsed: float = 0.0
        self._last_real_time: float = -1.0
        self._first_real_time: bool = True
        self._time_muliplier: float = 1.0
        # Maximum time for a match
        self.max_time: int = 8 * 60

        self._last_sent_score: float = 0.0
        self._last_sent_time: float = 0.0
        self._last_sent_real_time: float = 0.0

        # Get custom world data, to get max game time
        custom_world_data: list[str] = []
        if self.getCustomData() != '':
            custom_world_data = self.getCustomData().split(',')
            self.max_time = int(custom_world_data[0])

        # Max real world time is max_time + 1 min or 125% of max_time
        # which ever is greater
        self._max_real_world_time: int = int(max(self.max_time + 60,
                                                self.max_time * 1.25))

        # Init tile and victim managers
        self.tile_manager: TileManager = TileManager(self)
        self.victim_manager: VictimManager = VictimManager(self)

        cam_side: FollowSide = FollowSide.BOTTOM
        if len(custom_world_data) > 1:
            cam_side = FollowSide[custom_world_data[1].upper()]
        self._camera: Camera = Camera(self.getFromDef("Viewpoint"), cam_side)

        # Typing casts have to be used here to get proper type hints. Webots
        # returns Devices from `getDevice`, but e.g. an Emitter or Receiver
        # dont inherit from Device...
        self._receiver: Receiver = cast(Receiver, self.getDevice('receiver'))
        self._receiver.enable(Erebus.TIME_STEP)

        self.emitter: Emitter = cast(Emitter, self.getDevice('emitter'))

        # Init robot as object to hold game data
        self.robot_obj: Robot = Robot(self)
        self.robot_obj.update_config(self.config)
        self.robot_obj.controller.reset_file()
        self.robot_obj.reset_proto()

        # Calculate the solution arrays for the map layout
        self._map_ans = MapAnswer.from_supervisor(self)
        map_ans: Optional[list[list]] = self._map_ans.generateAnswer()
        if map_ans is None:
            raise Exception("Critical error: Could not generate answer matrix")
        self._map_sol: list[list] = map_ans

        # Init test runner to run (unit) tests
        self._test_runner: TestRunner = TestRunner(self)
        self._run_tests: bool = False

        # Toggle for enabling remote webots controllers
        self._remote_enabled: bool = False
        self._update_remote_enabled()

        # Export the answer map to an image used within the world selector UI
        export_map_to_img(self, self._map_sol)
        
        self.rws.send("currentWorld", self._get_current_world())

        self.rws.send("update", f"0,0,{self.max_time},0")

    def wwiReceiveText(self) -> Optional[str]:
        """
        Allow a robot controller to receive a message sent from a JavaScript
        function running in the HTML robot window

        This overrides Webot's Robot class implementation

        Returns:
            Optional[str]: Decoded robot window message
        """
        
        text: bytes = wb.wb_robot_wwi_receive_text()
        if text is None:
            return None
        else: 
            try:
                return text.decode()
            except:
                Console.log_debug(f"<wwiReceiveText> failed to decode {text}")
                pass

    def _game_init(self) -> None:
        """Initialises Erebus' initial game state. This should be run on the 
        first frame of simulation run time.
        """
        # If recording
        if self.config.recording:
            Recorder.start_recording(self)

        # Get the robot node by DEF name
        robot_node: Optional[Node] = self.getFromDef("ROBOT0")
        # Add robot into world
        if robot_node == None:
            robot_node = self._add_robot()
        # Init robot as object to hold their info
        self.robot_obj.set_node(robot_node)

        # Set robots starting position in world
        self.robot_obj.set_start_pos(self.tile_manager.start_tile)
        self.robot_obj.in_simulation = True
        self.robot_obj.set_max_velocity(self.DEFAULT_MAX_MULT)
        # Reset physics
        self.robot_obj.reset_physics()

        # If automatic camera
        if self.config.automatic_camera and self._camera.wb_viewpoint_node:
            self._camera.follow(self.robot_obj, Erebus.ROBOT_NAME)

        if self.config.recording:
            Recorder.reset_countdown(self)
            
        # Enqueue warning if debug mode is on when game the starts
        if Console.DEBUG_MODE:
            self.robot_obj.history.enqueue("WARNING: Debug mode is on. This "
                                           "should not be on during competitions.")

        self._last_time = self.getTime()
        self._first_frame = False
        self._robot_initialised = True
        self._last_real_time = time.time()

    def relocate_robot(self, manual = False) -> None:
        """Relocate robot to last visited checkpoint

        Args:
            manual (bool, optional): Whether the robot relocate is manual (from
            the UI) or not (via robot packet info). Defaults to False.
        """
        if self.robot_obj.last_visited_checkpoint_pos is None:
            Console.log_err("Last visited checkpoint was None.")
            return

        # Get last checkpoint visited
        relocate_position: tuple = self.robot_obj.last_visited_checkpoint_pos

        # Set position and rotation of robot
        self.robot_obj.position = [relocate_position[0],
                                   -0.03,
                                   relocate_position[2]]
        self.robot_obj.rotation = [0, 1, 0, 0]

        # Reset physics
        self.robot_obj.reset_physics()
        # Notify robot
        self.emitter.send(struct.pack("c", bytes("L", "utf-8")))
        
        # Suffix for event history to log what causes a relocate
        suffix = "(via robot)"
        if manual:
            suffix = "(via UI)"
        
        # Update history with event
        self.robot_obj.increase_score(f"Lack of Progress {suffix}", -5)

        # Update the camera position since the robot has now suddenly moved
        if self.config.automatic_camera and self._camera.wb_viewpoint_node:
            self._camera.set_view_point(self.robot_obj)

    def _robot_quit(self, time_up: bool) -> None:
        """Quit robot from simulation

        Args:
            time_up (bool): Whether the cause of the robot quit is due to the 
            timer running out 
        """
        # Quit robot if present
        if self.robot_obj.in_simulation:
            # Remove webots node
            self.robot_obj.remove_node()
            self.robot_obj.in_simulation = False
            # Send message to robot window to update quit button
            self.rws.send("robotNotInSimulation0")
            # Update history event whether its manual or via exit message
            if not time_up:
                self.robot_obj.history.enqueue("Successful Exit")
            # Write to a log file to write game events to file
            Logger.write_log(self.robot_obj, self.rws, self.max_time)


    def _add_physicsless_robot_proto(self) -> None:
        """Copies a physics-less version of the default robot proto to 
        the custom_robot.proto proto location, forcing the use of this proto
        instead of any other that may have been loaded
        
        Note: This should really only be used for automated testing
        """

        # Copy physicsless proto file to be used as custom robot proto
        path: str = get_file_path("proto_defaults/E-puck-custom-default-FLU-physicsless.proto",
                                  "../../proto_defaults/E-puck-custom-default-FLU-physicsless.proto")
        dest: str = get_file_path("protos/custom_robot.proto",
                                  "../../protos/custom_robot.proto")
        shutil.copyfile(path, dest)

    def _add_robot(self) -> Node:
        """Add a robot Node to the root of the Webots scene tree.
        
        Sets the robot's controller to either point to the robot0Controller 
        file, or if the remote enabled setting is set, sets the robot to take
        "extern" controllers

        Returns:
            Node: Node reference to newly added robot
        """
        
        if self._run_tests:
            self._add_physicsless_robot_proto()

        controller: str = "robot0Controller"
        if self._remote_enabled:
            controller = "<extern>"

        # Get webots root
        root: Node = self.getRoot()
        root_children_field: Field = root.getField('children')

        node_string: str = f"""DEF ROBOT0 custom_robot {{ 
                                    translation 1000 1000 1000 
                                    rotation 0 1 0 0 
                                    name "{Erebus.ROBOT_NAME}"
                                    controller "{controller}"
                                    camera_fieldOfView 1 
                                    camera_width 64 
                                    camera_height 40 
                                }}
                            """

        # Get robot to insert into world
        root_children_field.importMFNodeFromString(-1, node_string)
        # Update robot window to say robot is in simulation
        self.rws.send("robotInSimulation0")
        # Return the robot node
        return self.getFromDef("ROBOT0")

    def _add_map_multiplier(self) -> None:
        """Apply the map multiplier from the robot's map score to the score
        """
        score_change: float = self.robot_obj.get_score() * self.robot_obj.map_score_percent
        self.robot_obj.increase_score("Map Bonus", score_change)

    def _process_robot_json(self, json_data: str) -> None:
        """Process custom robot json data to generate a new robot proto file.
        
        The custom robot proto file is used when importing the robot at game 
        start
        """
        robot_json: dict = json.loads(json_data)
        if generate_robot_proto(robot_json):
            self.rws.send("loaded1")

    def wait(self, sec: float) -> None:
        """Waits for x amount of seconds, while still stepping the Webots
        simulation to avoid simulation pauses

        Args:
            sec (float): Seconds to wait
        """
        first: float = self.getTime()
        while True:
            self.step(Erebus.TIME_STEP)
            if self.getTime() - first > sec:
                break
    
    def set_time_multiplier(self, multiplier: float) -> None:
        """Set time multiplier for game countdown timer

        Args:
            multiplier (float): Countdown time multiplier
        """
        self._time_muliplier = multiplier
            
    def _get_current_world(self) -> str:
        """Gets the current world name, with no file extension

        Returns:
            str: Current world name
        """
        return os.path.basename(self.getWorldPath())[:-4]

    def _get_worlds(self) -> str:
        """Gets all worlds from the `worlds` directory as a list of file names,
        separated by commas. File extensions are stripped and hidden files
        are ignored.

        Returns:
            str: List of worlds as a string. Example: `"world1,world2,room4"`
        """
        path: str = get_file_path("worlds", "../../worlds")
        files: list[str] = [file for file in os.listdir(path)
                            if file[-3:] == 'wbt' and file[0] != '.']
        return ','.join(files)

    def _load_world(self, world: str) -> None:
        """Loads a specified Webots world world file located in the worlds 
        directory. This will close the current running world.

        Args:
            world (str): World file name within the worlds directory
        """
        # If game started
        if self.robot_obj.in_simulation:
            # Write to a log file to write game events to file
            Logger.write_log(self.robot_obj, self.rws, self.max_time)
        path: str = get_file_path("worlds", "../../worlds")
        path = os.path.join(path, world)
        self.worldLoad(path)

    def _load_test_script(self) -> None:
        """Loads the test controller script, used to run Erebus (unit) tests,
        as the robot0Controller. This effectively achieves what the load
        controller UI does, but directly.
        """
        path: str = get_file_path("controllers/MainSupervisor/tests.py",
                                  "tests.py")
        dest: str = get_file_path("controllers/robot0Controller/robot0Controller.py",
                                  "../robot0Controller/robot0Controller.py")
        shutil.copyfile(path, dest)

    def _get_erebus_version(self) -> None:
        """Updates the Erebus web UI with the version of the platform. Extra
        data is sent to specify if the version if up to date, or needs updating.
        """
        try:
            self.rws.send("version", f"{self.version}")
            # Check updates
            url = "https://gitlab.com/api/v4/projects/22054848/releases"
            response = req.get(url)
            releases = response.json()
            releases = list(filter(lambda release: release['tag_name'].startswith(
                f"v{self._stream}"), releases))
            if len(releases) > 0:
                if releases[0]['tag_name'].replace('_', ' ') == f'v{self.version}':
                    self.rws.send("latest", f"{self.version}")
                elif any([r['tag_name'].replace('_', ' ') == f'v{self.version}' for r in releases]):
                    self.rws.send(
                        "outdated", f"{self.version},{releases[0]['tag_name'].replace('v','').replace('_', ' ')}")
                else:
                    self.rws.send("unreleased", f"{self.version}")
            else:
                self.rws.send("version", f"{self.version}")
        except:
            self.rws.send("version", f"{self.version}")

    def _detect_victim(self, robot_message: list[Any]) -> None:
        """Runs victim detection to give points based on the victim's estimated
        type and location

        Args:
            robot_message (list[Any]): The competitor's robot message data
        """
        # Get estimated position and type values
        est_vic_pos = robot_message[0]
        est_vic_type = robot_message[1]

        iterator: Sequence[VictimObject] = self.victim_manager.victims
        name: str = 'Victim'
        correct_type_bonus: int = 10
        misidentification: bool = True

        if est_vic_type.lower() in list(map(to_lower, HazardMap.HAZARD_TYPES)):
            iterator = self.victim_manager.hazards
            name = 'Hazard'
            correct_type_bonus = 20

        # Get nearby victim/hazards that are within range (as per the rules)
        nearby_map_issues: Sequence[VictimObject] = [
            h for h in iterator
            if h.check_position(self.robot_obj.position) and
            h.check_position(est_vic_pos) and
            h.on_same_side(self.robot_obj) and
            not h.identified
        ]

        Console.log_debug(f"--- Victim Data ---")
        for h in iterator:
            Console.log_debug("===")
            Console.log_debug(
                f"Position {self.robot_obj.position}")
            Console.log_debug(
                f"Distance {h.get_distance(self.robot_obj.position)}/0.09")
            Console.log_debug(
                f"In range: ({h.check_position(self.robot_obj.position)})")
            Console.log_debug(f"Est pos: {est_vic_pos}")
            Console.log_debug(
                f"Est distance {h.get_distance(est_vic_pos)}/0.09")
            Console.log_debug(
                f"Est distance in range: {h.check_position(est_vic_pos)}")
            Console.log_debug(
                f"On same side: {h.on_same_side(self.robot_obj)}")
            Console.log_debug(f"Identified: {h.identified}")
            Console.log_debug("===")
        Console.log_debug(f"Nearby issues: {len(nearby_map_issues)}")
        Console.log_debug(f"--- ----------- ---")

        # Award points based on correct victim identifications etc.
        if len(nearby_map_issues) > 0:
            misidentification: bool = False

            # TODO should it take the nearest, or perhaps also account
            # for which victim type was trying to be identified?

            # Take the nearest map issue by distance to the estimated coordinate
            distances: list[float] = [h.get_distance(est_vic_pos)
                                      for h in nearby_map_issues]

            nearby_issue: VictimObject = nearby_map_issues[np.argmin(
                distances)]

            # Get points scored depending on the type of victim
            grid: int = self.tile_manager.coord2grid(
                nearby_issue.wb_translation_field.getSFVec3f(),
                self)

            room_num: int = (
                self.getFromDef("WALLTILES")
                .getField("children")
                .getMFNode(grid)  # type: ignore
                .getField("room")
                .getSFInt32() - 1
            )

            Console.log_debug(f"Victim type est. {est_vic_type.lower()} vs "
                              f"{nearby_issue.simple_victim_type.lower()}")

            # Update score and history
            if est_vic_type.lower() == nearby_issue.simple_victim_type.lower():
                self.robot_obj.increase_score(
                    f"Successful {name} Type Correct Bonus",
                    correct_type_bonus,
                    multiplier=self.tile_manager.ROOM_MULT[room_num]
                )

            self.robot_obj.increase_score(
                f"Successful {name} Identification",
                nearby_issue.score_worth,
                multiplier=self.tile_manager.ROOM_MULT[room_num]
            )

            self.robot_obj.victim_identified = True
            nearby_issue.identified = True

        if misidentification:
            self.robot_obj.increase_score(f"Misidentification of {name}",
                                          -5)

    def _process_message(self, robot_message: list[Any]) -> None:
        """Processes the messages recieved from the competitor's robot's emitter
        as specified in the simulation rules

        Args:
            robot_message (list[Any]): The competitor's robot message data 
        """
        Console.log_debug(
            f"Robot Stopped for {self.robot_obj.time_stopped()}s")
        
        # Process exit commands
        if robot_message[0] == 'E':
            # TODO check this is inline with rules
            # Check robot position is on starting tile
            if self.tile_manager.start_tile.check_position(self.robot_obj.position):
                if self.robot_obj.victim_identified:
                    self.robot_obj.increase_score("Exit Bonus",
                                                  self.robot_obj.get_score() * 0.1)
                else:
                    self.robot_obj.history.enqueue("No Exit Bonus")
            # Update score and history
            self._add_map_multiplier()
            self._robot_quit(False)
            
            self.rws.send("ended")
            self._game_state = GameState.MATCH_FINISHED
            self._last_frame = True
        # Process map scoring commands
        elif robot_message[0] == 'M':
            try:
                # If map_data submitted
                if self.robot_obj.map_data.size == 0:
                    Console.log_err("Please send your map data before hand.")
                    return
                # If not previously evaluated
                if self.robot_obj.sent_maps:
                    Console.log_err(f"The map has already been evaluated.")
                    return
                
                if Console.DEBUG_MODE:
                    Console.log_debug("Map solution matrix:")
                    pretty_print_map(self._map_sol)
                    Console.log_debug("Submitted map matrix")
                    pretty_print_map(self.robot_obj.map_data)

                map_score: float = MapScorer.calculateScore(
                    self._map_sol, self.robot_obj.map_data
                )

                self.robot_obj.history.enqueue(
                    f"Map Correctness {str(round(map_score * 100,2))}%"
                )

                # Add percent
                self.robot_obj.map_score_percent = map_score
                self.robot_obj.sent_maps = True
                self.robot_obj.map_data = np.array([])

            except Exception as e:
                Console.log_err("Map scoring error, please check your code.")
                Console.log_err(str(e))
        # Process robot relocation commands
        elif robot_message[0] == 'L':
            self.relocate_robot()
            self.robot_obj.reset_time_stopped()
        # Process game info commands
        elif robot_message[0] == 'G':
            # Send game info in format:
            # (G, score, game time left, real time left)
            self.emitter.send(
                struct.pack(
                    "c f i i",
                    bytes("G", "utf-8"),
                    round(self.robot_obj.get_score(), 2),
                    self.max_time - int(self.time_elapsed),
                    self._max_real_world_time - int(self._real_time_elapsed)
                )
            )

        # If robot stopped for 1 second, run victim detection 
        elif self.robot_obj.time_stopped() >= 1.0:
            self._detect_victim(robot_message)

    def _process_rw_message(self, message: str) -> None:
        """Processes messages received from the MainSupervisor's robot window

        Args:
            message (str): Message to process
        """
        
        # Split the message to get extra command arguments if needed 
        parts: list[str] = message.split(",")

        if len(parts) > 0:
            command: str = parts[0]
            self.rws.update_received_history(command, str(parts[1:]))

            # Start running the match
            if command == "run":
                self._game_state = GameState.MATCH_RUNNING
                self.rws.update_history("runPressed")
                
            # Run tests
            if command == 'runTest':
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    self._game_state = GameState.MATCH_RUNNING
                    self._run_tests = True
                    self.config.disable_lop = True
                    self.simulation_mode = self.SIMULATION_MODE_FAST

            # Start running the match using a docker controller
            if command == "runDocker":
                Console.log_info("Running docker helper script (this may take "
                                 "a few minutes depending on project size)")
                self.step(Erebus.TIME_STEP)
                self._docker_process = run_docker_container(self, parts[1])
                if self._docker_process != None:
                    self._remote_enabled = True
                    # Start running the match
                    self._game_state = GameState.MATCH_RUNNING
                    self.rws.update_history("runDockerPressed")
                    self.rws.send("dockerSuccess")
                else:
                    self.step(Erebus.TIME_STEP)

            # Pause the match
            if command == "pause":
                self._game_state = GameState.MATCH_PAUSED
                self.rws.update_history("pausedPressed")

            # Reset the simulation (reload the world)
            if command == "reset":
                self._robot_quit(False)
                self.victim_manager.reset_victim_textures()

                self.simulationReset()
                self._game_state = GameState.MATCH_FINISHED

                # Show start tile
                self.tile_manager.start_tile.set_visible(True)

                # Must restart world - to reload to .wbo file for the robot
                # which only seems to be read and interpreted once per game, so
                # if we load a new robot file, the new changes won't come into
                # place until the world is reset!
                self.worldReload()

            # Unload the robot controller
            if command == "robot0Unload":
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    self.robot_obj.controller.reset()

            # Unload the custom robot json
            if command == "robot1Unload":
                # Remove the robot proto
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    self.robot_obj.reset_proto(True)

            # Relocate the robot
            if command == 'relocate':
                data = message.split(",", 1)
                if len(data) > 1:
                    if int(data[1]) == 0:
                        self.relocate_robot(manual=True)

            # Quite the robot from the simulation
            if command == 'quit':
                data = message.split(",", 1)
                if len(data) > 1:
                    if int(data[1]) == 0:
                        if self._game_state == GameState.MATCH_RUNNING:
                            self._add_map_multiplier()
                            self.robot_obj.history.enqueue("Manual give up!")
                            self._robot_quit(True)
                            self._game_state = GameState.MATCH_FINISHED
                            self._last_frame = True
                            self.rws.send("ended")

            # If custom robot json is loaded
            if command == 'robotJson':
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    data = message.split(",", 1)
                    if len(data) > 1:
                        self._process_robot_json(data[1])

            # If config is updated
            if command == 'config':
                configData = message.split(",")[1:]
                self.config = Config(configData, self.config.path)
                self.robot_obj.update_config(self.config)
                
                # Enqueue warning when config is updated when the game is running
                if self._game_state == GameState.MATCH_RUNNING:
                    self.robot_obj.history.enqueue("WARNING: Erebus config updated")

                with open(self.config.path, 'w') as f:
                    f.write(','.join(message.split(",")[1:]))
            
            # Load a specific world file
            if command == 'loadWorld':
                self._load_world(parts[1])

            # Load test controller
            if command == 'loadTest':
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    self._load_test_script()

            # The robot window was reloaded, commands must be re-sent to
            # achieve the same state it was previously in
            if command == 'rw_reload':
                self.rws.send_all()
                config_file_path = get_file_path(
                    "controllers/MainSupervisor/config.txt",
                    "config.txt"
                )
                self.config = self._get_config(config_file_path)

            # Robot controller ui button was pressed 
            if command == 'loadControllerPressed':
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    self.rws.update_history("loadControllerPressed,", parts[1])

            # Robot unload controller ui button was pressed
            if command == 'unloadControllerPressed':
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    self.rws.update_history("unloadControllerPressed,", parts[1])

            # Enable remote controller
            if command == 'remoteEnable':
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    self._remote_enabled = True
                    self.rws.update_history("remoteEnabled")

            # Disable remote controller
            if command == 'remoteDisable':
                if self._game_state == GameState.MATCH_NOT_STARTED:
                    self._remote_enabled = False
                    self.rws.update_history("remoteDisabled")

            # Send the list of Erebus worlds
            if command == 'getWorlds':
                self.rws.send('worlds', f'{str(self._get_worlds())}')

    def _get_config(self, config_file_path: str) -> Config:
        """Processes the simulation's `config.txt` csv file to create
        a config object to use during game runtime

        Args:
            config_file_path (str): Config file path location

        Returns:
            Config: Config data object
        """

        with open(config_file_path, 'r') as f:
            configData = f.read().replace('\\', '/').split(',')

        self.rws.send("config", ','.join(configData))

        return Config(configData, config_file_path)

    def _update_remote_enabled(self) -> None:
        """Updates internal variables to align with the settings from the
        current `Config` data (`self.config`).

        Updates the web UI's remote enabled button enable state to reflect the
        current state of the config setting 
        """
        self._remote_enabled = self.config.keep_remote
        if self._remote_enabled:
            self.rws.update_history("remoteEnabled")
        else:
            self.rws.update_history("remoteDisabled")

    def update(self) -> None:
        """Main Erebus update loop, used to process anything needed during the
        runtime of the simulation
        """

        # If last frame
        if self._last_frame == True:
            self._last_frame = None
            self._game_state = GameState.MATCH_FINISHED
            if self.config.recording:
                Recorder.stop_recording(self)

        # The first frame of the game running only
        if self._first_frame and self._game_state == GameState.MATCH_RUNNING:
            self._game_init()

        if self._run_tests:
            self._test_runner.run()

        # Main game loop
        if self.robot_obj.in_simulation:
            self.robot_obj.update_time_elapsed(self.time_elapsed)

            # Automatic camera movement
            if self.config.automatic_camera and self._camera.wb_viewpoint_node:
                all_hazards: Sequence[VictimObject] = (
                    self.victim_manager.victims + self.victim_manager.hazards
                )
                self._camera.rotate_to_victim(self.robot_obj, all_hazards)

            self.tile_manager.check_checkpoints()
            self.tile_manager.check_swamps()

            # If receiver has got a message
            if self._receiver.getQueueLength() > 0:
                # Get receiver data
                received_data = self._receiver.getBytes()
                
                # Process robot messages
                test_msg = False
                if self._run_tests:
                    test_msg = self._test_runner.get_stage(received_data)
                    self._receiver.nextPacket()
                if not test_msg:
                    self.robot_obj.set_message(received_data)
                    self._receiver.nextPacket()

                # If data received from competitor's robot
                if self.robot_obj.message != []:
                    robot_message: list[Any] = self.robot_obj.message
                    Console.log_debug(f"Robot Message: {robot_message}")
                    self.robot_obj.message = []
                    self._process_message(robot_message)

            if self._game_state == GameState.MATCH_RUNNING:
                # Relocate robot if stationary for 20 sec
                if self.robot_obj.time_stopped() >= 20:
                    if not self.config.disable_lop:
                        self.relocate_robot()
                    self.robot_obj.reset_time_stopped()
                    
                # Relocate robot if fallen in black hole
                if (self.robot_obj.position[1] < -0.035 and
                        self._game_state == GameState.MATCH_RUNNING):
                    if not self.config.disable_lop:
                        self.relocate_robot()
                    self.robot_obj.reset_time_stopped()

        if self._robot_initialised:
            # Send the update information to the robot window, the current
            # simulation time and score etc.
            current_score: float = self.robot_obj.get_score()

            self.time_elapsed = min(self.time_elapsed, self.max_time)
            self._real_time_elapsed = min(self._real_time_elapsed,
                                         self._max_real_world_time)

            if (self._last_sent_score != current_score or
                self._last_sent_time != int(self.time_elapsed) or
                    self._last_sent_real_time != int(self._real_time_elapsed)):

                self.rws.send("update", f"{round(current_score, 2)},"
                                        f"{int(self.time_elapsed)},"
                                        f"{self.max_time},"
                                        f"{int(self._real_time_elapsed)}")

                self._last_sent_score = current_score
                self._last_sent_time = int(self.time_elapsed)
                self._last_sent_real_time = int(self._real_time_elapsed)
                if self.config.recording:
                    Recorder.update(self)

            # If the time is up
            if ((self.time_elapsed >= self.max_time or
                 self._real_time_elapsed >= self._max_real_world_time) and
                    self._last_frame != None):
                self._add_map_multiplier()
                self._robot_quit(True)

                self._game_state = GameState.MATCH_FINISHED
                self._last_frame = True

                self.rws.send("ended")

        # Get the message in from the robot window(if there is one)
        message: Optional[str] = self.wwiReceiveText()
        while message not in ['', None]:
            Console.log_debug(f"Received wwi message: {message}")
            self._process_rw_message(message)  # type: ignore
            message = self.wwiReceiveText()

        if self._game_state == GameState.MATCH_PAUSED:
            self.step(0)
            # Sleep the script every loop while paused to do "busy work", so
            # the loop doesn't use unnecessary amounts of CPU time
            time.sleep(0.01)
            self._last_real_time = time.time()

        # If the match is running
        if self._robot_initialised and self._game_state == GameState.MATCH_RUNNING:
            # If waiting for a remote controller, don't count time waiting
            if (self._remote_enabled and self._first_real_time and
                    self._last_time != self.getTime()):
                self._last_real_time = time.time()
                self._first_real_time = False
            # Get real world time (for 9 min real world time elapsed rule)
            self._real_time_elapsed += (time.time() - self._last_real_time)
            self._last_real_time = time.time()
            # Get the time since the last frame
            frameTime = self.getTime() - self._last_time
            # Scale frame time by countdown time multiplier (used for swamps)
            frameTime *= self._time_muliplier
            # Add to the elapsed time
            self.time_elapsed += frameTime
            # Get the current time
            self._last_time = self.getTime()
            # Step the simulation on
            step = self.step(Erebus.TIME_STEP)
            # If the simulation is terminated or the time is up
            if step == -1:
                # Stop simulating
                self._game_state = GameState.MATCH_FINISHED

        elif (self._first_frame or
              self._last_frame == True or
              self._game_state == GameState.MATCH_FINISHED):
            # Step simulation
            self.step(Erebus.TIME_STEP)


if __name__ == '__main__':

    erebus: Erebus = Erebus()

    while True:  # Main loop
        erebus.update()
