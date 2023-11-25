from __future__ import annotations
from typing import Any, Optional
from typing import TYPE_CHECKING

import datetime
import os
import shutil
import filecmp
import struct
import numpy as np

from controller import Supervisor
from controller import Node
from controller import Field

from Controller import Controller
from ConsoleLog import Console
from Tile import Checkpoint, StartTile, TileManager
from Config import Config
from ErebusObject import ErebusObject



if TYPE_CHECKING:
    from MainSupervisor import Erebus


class Queue:
    """Simple queue data structure
    """

    def __init__(self):
        self._queue: list[Any] = []

    def enqueue(self, data: Any) -> None:
        self._queue.append(data)

    def dequeue(self) -> Any:
        return self._queue.pop(0)

    def peek(self) -> Any:
        return self._queue[0]

    def is_empty(self) -> bool:
        return len(self._queue) == 0


class RobotHistory(ErebusObject, Queue):
    """Robot history, a queue structure, to store game action history
    """

    def __init__(self, erebus: Erebus):
        """Initialises new Robot history queue object to store game events

        Args:
            erebus (Erebus): Erebus supervisor game object
        """
        super().__init__(erebus)
        # Master history to store all events without dequeues
        self.master_history: list[tuple[str, str]] = []

        self.time_elapsed: float = 0.0
        self.display_to_recording_label: bool = False

    def _update_master_history(self, data: str) -> tuple[str, str]:
        """Update the master history, storing data as (game time, event data)
        records.

        Args:
            data (str): Data to enqueue

        Returns:
            tuple[str, str]: Game event record in the form (game time, data)
        """
        time: int = int(self.time_elapsed)
        # Convert elapsed time to minutes
        minute: str = str(datetime.timedelta(seconds=time))[2:]
        # Update list with data in format [game time, event data]
        record: tuple[str, str] = (minute, data)
        self.master_history.append(record)

        return record

    def enqueue(self, data: str):
        """Enqueue game data to the end of the robot's history queue, and update
        any relevant UI components.

        Args:
            data (str): Data to enqueue
        """
        # Update master history when an event happens
        record: tuple[str, str] = self._update_master_history(data)
        # Send the event data to the robot window to update the ui
        self._erebus.rws.send("historyUpdate", ",".join(record))

        if self.display_to_recording_label:
            history_label: str = ""
            histories: list[tuple[str, str]] = list(
                reversed(self.master_history))
            for h in range(min(len(histories), 5)):
                history_label = (f"[{histories[h][0]}] {histories[h][1]}\n"
                                 f"{history_label}")
            self._erebus.setLabel(2, history_label, 0.7, 0, 0.05, 0xfbc531, 0.2) # type: ignore


class Robot(ErebusObject):
    """Robot object used to store and process data about the competitor's
    robot in the simulation
    """

    def __init__(self, erebus: Erebus):
        """Initialises new competition Robot object

        Args:
            erebus (Erebus): Erebus supervisor game object
        """
        super().__init__(erebus)
        
        self._wb_node: Node
        self.wb_translationField: Field
        self.wb_rotationField: Field

        self.name: str = "NO_TEAM_NAME"
        self.in_simulation: bool = False

        self.history: RobotHistory = RobotHistory(self._erebus)
        self.controller: Controller = Controller(self._erebus)

        self.in_swamp: bool = False

        self._score: float = 0

        self._stopped: bool = False
        self._robot_time_stopped: float = 0
        self._stopped_time: Optional[float] = None

        self.message: list[Any] = []
        self.map_data = np.array([])
        self.sent_maps: bool = False
        self.map_score_percent: float = 0

        # If a victim has been identified, used to give an exit bonus iff one
        # victim has been identified
        self.victim_identified: bool = False

        # TODO these should be tuples... something to do when changing Tile code
        self.last_visited_checkpoint_pos: Optional[
            tuple[float,float, float]] = None
        self.visited_checkpoints: list = []

    @property
    def position(self) -> list[float]:
        return self.wb_translationField.getSFVec3f()

    @position.setter
    def position(self, pos: list[float]) -> None:
        self.wb_translationField.setSFVec3f(pos)

    @property
    def rotation(self) -> list[float]:
        return self.wb_rotationField.getSFRotation()

    @rotation.setter
    def rotation(self, pos: list[float]) -> None:
        self.wb_rotationField.setSFRotation(pos)
        
    @property
    def velocity(self) -> list[float]:
        return self._wb_node.getVelocity()
        
    def reset_physics(self) -> None:
        """Stops the inertia of the robot and its descendants.
        """
        self._wb_node.resetPhysics()
        
    def remove_node(self) -> None:
        """Removes the robot from the Webots scene tree
        """
        self._wb_node.remove()

    def set_node(self, node: Node) -> None:
        """Sets the robot's webots node object

        Args:
            node (Node): Webots node object associated with the robot
        """
        self._wb_node: Node = node
        self.wb_translationField: Field = self._wb_node.getField('translation')
        self.wb_rotationField: Field = self._wb_node.getField('rotation')

    def set_max_velocity(self, vel: float) -> None:
        """Set the max angular velocity the robot can move at.

        Args:
            vel (float): Maximum angular velocity
        """
        # TODO this doesn't actually work...
        self._wb_node.getField('wheel_mult').setSFFloat(vel)

    def _is_stopped(self) -> bool:
        """Returns whether the robot has stopped moving

        Returns:
            bool: True if the robot is not moving (still)
        """
        vel: list[float] = self._wb_node.getVelocity()
        return all(abs(ve) < 0.001 for ve in vel)

    def time_stopped(self) -> float:
        """Gets the amount of time the robot has been stopped for in seconds.

        Returns:
            float: Time stopped, in seconds
        """
        self._stopped = self._is_stopped()

        # if it isn't stopped yet
        if self._stopped_time == None:
            if self._stopped:
                # get time the robot stopped
                self._stopped_time = self._erebus.getTime()
        else:
            # if its stopped
            if self._stopped:
                # get current time
                current_time: float = self._erebus.getTime()
                # calculate the time the robot stopped
                self._robot_time_stopped = current_time - self._stopped_time
            else:
                # if it's no longer stopped, reset variables
                self._stopped_time = None
                self._robot_time_stopped = 0.0
        return self._robot_time_stopped

    def reset_time_stopped(self) -> None:
        """Resets the amount of time recorded for being stopped
        """
        self._robot_time_stopped = 0.0
        self._stopped = False
        self._stopped_time = None

    def increase_score(
        self,
        message: str,
        score: float,
        multiplier: float = 1,
    ) -> None:
        """Increases the robots score. The primary method used to increase the
        robots competition score.

        Args:
            message (str): Message to display in the web UI
            score (float): Score to add
            multiplier (float, optional): Score multiplier (`new_score = 
            score * multiplier`), used for room score multipliers.
            Defaults to 1.
        """
        point: float = round(score * multiplier, 2)
        if point > 0.0:
            self.history.enqueue(f"{message} +{point}")
        elif point < 0.0:
            self.history.enqueue(f"{message} {point}")
        self._score += point
        if self._score < 0:
            self._score = 0

    def get_score(self) -> float:
        """Gets the robot's current score

        Returns:
            float: Robot game score
        """
        return self._score

    def get_log_str(self) -> str:
        """Gets a string of all events the robot has done during the simulation

        Returns:
            str: String of event records, separated by a new line. Each record
            is in the form (minute, event message)
        """
        # Create a string of all events that the robot has done
        history: list[tuple[str, str]] = self.history.master_history
        log_str: str = ""
        for event in history:
            log_str += str(event[0]) + " " + event[1] + "\n"

        return log_str
    
    def set_start_pos(self, start_tile: StartTile) -> None:
        '''Set robot starting position'''

        start_tile.set_visible(False)
        
        self.last_visited_checkpoint_pos = start_tile.center
        self.visited_checkpoints.append(start_tile.center)

        self.position = [start_tile.center[0], start_tile.center[1], 
                         start_tile.center[2]]
        self._set_starting_orientation(start_tile)

    def _set_starting_orientation(self, start_tile: StartTile) -> None:
        """Sets starting orientation for robot using wall data from starting 
        tile
        """
        
        # Get starting tile walls
        top: bool = start_tile.is_wall_present("topWall")
        right: bool = start_tile.is_wall_present("rightWall")
        bottom: bool = start_tile.is_wall_present("bottomWall")
        left: bool = start_tile.is_wall_present("leftWall")

        # top: 0
        # left: pi/2
        # right: -pi/2
        # bottom: pi
        pi: float = 3.14
        direction: float = 0.0
        walls: list[tuple[bool, float]] = [(top, 0.0), (right, -pi/2),
                                           (bottom, pi), (left, pi/2)]

        for i in range(len(walls)):
            # If there isn't a wall in the direction
            if not walls[i][0]:
                direction = walls[i][1]
                break

        # Set robot rotation, rotating around y axis
        self.rotation = [0., 1., 0., direction]

    def set_message(self, received_data: bytes) -> None:
        """Formats received emitter/receiver packet data to a format useful
        for the different message types available for the competitors to use

        Args:
            received_data (bytes): Byte data received from the competitor's
            robot's emitter
        """

        # Get length of bytes
        data_len: int = len(received_data)
        Console.log_debug(f"Data: {received_data} with length {data_len}")
        try:
            if data_len == 1:
                tup = struct.unpack('c', received_data)
                self.message = [tup[0].decode("utf-8")]
            # Victim identification bytes data should be of length = 9
            elif data_len == 9:
                # Unpack data
                tup: tuple[Any, ...] = struct.unpack('i i c', received_data)

                # Get data in format:
                # (est. x position, est. z position, est. victim type)
                x = tup[0]
                z = tup[1]

                estimated_victim_position: tuple[float, ...] = (x / 100,
                                                                0,
                                                                z / 100)

                victimType = tup[2].decode("utf-8")

                # Store data recieved
                self.message = [estimated_victim_position, victimType]
            else:
                """
                    For map data, the format sent should be:

                    receivedData = b'_____ _________________'
                                    ^          ^
                                    shape     map data
                """
                # Shape data should be two bytes (2 integers)
                shape_bytes: bytes = received_data[:8]  # Get shape of matrix
                data_bytes: bytes = received_data[8::]  # Get data of matrix

                # Get shape data
                shape: tuple[int, int] = struct.unpack('2i', shape_bytes)
                # Get map data
                map_data = data_bytes.decode('utf-8').split(',')
                # Reshape data using the shape data given
                reshaped_data = np.array(map_data).reshape(shape)

                self.map_data = reshaped_data
        except Exception as e:
            Console.log_err("Incorrect data format sent")
            Console.log_err(str(e))

    def update_time_elapsed(self, time_elapsed: float) -> None:
        """Updates the robot's history with the current time elapsed. Used to
        keep the history's record timestamps up to date.

        Args:
            time_elapsed (float): Current time elapsed (in seconds)
        """
        self.history.time_elapsed = time_elapsed

    def update_config(self, config: Config) -> None:
        """Update the robot with new config data. Used to sure settings if
        recording or keeping controller files.

        Args:
            config (Config): Config object
        """
        self.history.display_to_recording_label = config.recording
        self.controller.update_keep_controller_config(config)

    def reset_proto(self, manual: bool = False) -> None:
        """Resets the robot's custom proto file, back to the default.
        - Send message to robot window to say that robot has been reset
        - Reset robot proto file back to default
        """
        path: str = os.path.dirname(os.path.abspath(__file__))

        # Get default proto file path
        if path[-4:] == "game":
            default_robot_proto = os.path.join(
                path, 'proto_defaults/E-puck-custom-default-FLU.proto')
            robot_proto = os.path.join(path, 'protos/custom_robot.proto')
        else:
            default_robot_proto = os.path.join(
                path, '../../proto_defaults/E-puck-custom-default-FLU.proto')
            robot_proto = os.path.join(path, '../../protos/custom_robot.proto')

        try:
            if os.path.isfile(robot_proto):
                if self.controller.keep_controller and not manual:
                    if not filecmp.cmp(default_robot_proto, robot_proto):
                        self._erebus.rws.send("loaded1")
                    return
                shutil.copyfile(default_robot_proto, robot_proto)
            else:
                shutil.copyfile(default_robot_proto, robot_proto)
                # Must reset world, since webots doesn't
                # recognise new protos otherwise
                self._erebus.worldReload()
            self._erebus.rws.send("unloaded1")
        except Exception as e:
            Console.log_err(f"Error resetting robot proto")
            Console.log_err(str(e))

    def update_checkpoints(self, checkpoint: Checkpoint) -> None:
        """Updates the robots visited checkpoint history. If the specified
        checkpoint has not been visited, points are awarded.

        Args:
            checkpoint (Checkpoint): Checkpoint to check
        """
        self.last_visited_checkpoint_pos = checkpoint.center

        # Dont update if checkpoint is already visited
        if not any([c == checkpoint.center for c in self.visited_checkpoints]):
            # Add the checkpoint to the list of visited checkpoints
            self.visited_checkpoints.append(checkpoint.center)

            # Update robot's points and history
            grid: int = TileManager.coord2grid(checkpoint.center, self._erebus)
            room_num: int = (
                self._erebus.getFromDef("WALLTILES")
                .getField("children")
                .getMFNode(grid) # type: ignore
                .getField("room").getSFInt32() - 1
            )
            self.increase_score("Found checkpoint", 10, 
                                multiplier=TileManager.ROOM_MULT[room_num])

    def update_in_swamp(self, in_swamp: bool, default_multiplier: float) -> None:
        """Updates the game's timer countdown multiplier when in a swamp.

        Args:
            in_swamp (bool): Whether the robot has entered a swamp
            default_multiplier (float): Default time multiplier
        """
        # Check if robot is in swamp
        if self.in_swamp != in_swamp:
            self.in_swamp = in_swamp
            if self.in_swamp:
                # Update time multiplier 
                self._erebus.set_time_multiplier(TileManager.SWAMP_TIME_MULT)
                # Update history
                self.history.enqueue("Entered swamp")
            else:
                # Reset time multiplier
                self._erebus.set_time_multiplier(default_multiplier)
                # Update history
                self.history.enqueue("Exited swamp,")
