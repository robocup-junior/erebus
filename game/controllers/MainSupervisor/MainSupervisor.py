"""Supervisor Controller
   Written by Robbie Goldman and Alfred Roberts
"""
import AutoInstall

AutoInstall._import("np", "numpy")
AutoInstall._import("cl", "termcolor")
AutoInstall._import("req", "requests")

import mapAnswer
import filecmp
import glob
import MapScorer
import ControllerUploader
from controller import Supervisor
import os
import shutil
import struct
import math
import datetime
import threading
import shutil
import json
import time

from ProtoGenerator import generate_robot_proto
from Tools import *
from ConsoleLog import Console

from Camera import Camera
from Tile import *
from Victim import *
from Robot import *
from Recorder import Recorder
from Test import TestRunner
from RobotWindowSender import RWSender




TIME_STEP = 16

DEFAULT_MAX_VELOCITY = 6.28
DEFAULT_MAX_MULT = 1.0

MATCH_NOT_STARTED = 'MATCH_NOT_STARTED'
MATCH_RUNNING = 'MATCH_RUNNING'
MATCH_FINISHED = 'MATCH_FINISHED'
MATCH_PAUSED = 'MATCH_PAUSED'

ROBOT_NAME = "Erebus_Bot"


class Config():
    def __init__(self, configData, path):
        
        # configData
        # [0]: Keep controller/robot files
        # [1]: Disable auto LoP
        # [2]: Recording
        # [3]: Automatic camera
        self.configDataList = configData
        self.path = path
        
        self.keep_controller = bool(configData[0])
        self.disableLOP = bool(configData[1])
        self.recording = bool(configData[2])
        self.automatic_camera = bool(configData[3])   
        
class Game(Supervisor):
    def __init__(self):
        super().__init__()
        
        # Version info
        self.stream = 23
        self.version = "23.0.3"
        
        uploader = threading.Thread(target=ControllerUploader.start, daemon=True)
        uploader.start()
        
        # Get this supervisor node - so that it can be rest when game restarts
        self.mainSupervisor = self.getFromDef("MAINSUPERVISOR")
        
        # Robot window send text wrapper
        self.rws = RWSender(self)
        
        # Send message to robot window to perform setup
        self.rws.send("startup")
        
        self.gameState = MATCH_NOT_STARTED
        self.lastFrame = False
        self.firstFrame = True
        # How long the game has been running for
        self.timeElapsed = 0
        self.lastTime = -1
        self.realTimeElapsed = 0
        self.lastRealTime = -1
        self.firstRealTime = True
        
        self.lastSentScore = 0
        self.lastSentTime = 0
        self.lastSentRealTime = 0

        self.robotInitialized = False
                
        # Maximum time for a match
        self.maxTime = 8 * 60
        
        self.sWarnCooldown = False
        customData = []
        if self.getCustomData() != '':
            customData = self.getCustomData().split(',')
            self.maxTime = int(customData[0])
        self.maxRealWorldTime = max(self.maxTime + 60, self.maxTime * 1.25)
        self.rws.send("update", str(0) + "," + str(0) + "," + str(self.maxTime) + "," + str(0))
        
        self.getSimulationVersion()
        
        configFilePath = getFilePath("controllers/MainSupervisor/config.txt", "config.txt")
        self.config = self.getConfig(configFilePath)


        self.tileManager = TileManager()
        self.tileManager.getSwamps(self)
        self.tileManager.getCheckpoints(self)
        
        self.victimManager = VictimManager()
        self.victimManager.getHumans(self)
        self.victimManager.getHazards(self)

        # Get Viewppoint Node
        viewpoint_node = self.getFromDef("Viewpoint")
        nowSide = "bottom"
        if len(customData) > 1:
            nowSide = customData[1]
            
        self.camera = Camera(viewpoint_node, nowSide)

        self.receiver = self.getDevice('receiver')
        self.receiver.enable(TIME_STEP)

        self.emitter = self.getDevice('emitter')

        # Init robot as object to hold their info
        self.robot0Obj = Robot()
        self.robot0Obj.updateConfig(self.config)
        self.robot0Obj.controller.resetFile(self)
        self.robot0Obj.resetProto(self)

        # Calculate the solution arrays for the map layout
        self.MapAnswer = mapAnswer.MapAnswer(self)
        self.mapSolution = self.MapAnswer.generateAnswer(False)
        
        self.testRunner = TestRunner(self)
        self.runTests = False
        
        # Toggle for enabling remote webots controllers
        self.remoteEnabled = False
    
    def game_init(self):
        # If recording
        if self.config.recording:
            Recorder.startRecording(self)

        # Get the robot node by DEF name
        robot0 = self.getFromDef("ROBOT0")
        # Add robot into world
        if robot0 == None:
            robot0 = self.add_robot()
        # Init robot as object to hold their info
        # self.robot0Obj = Robot(node=robot0)
        self.robot0Obj.add_node(robot0)
        
        # Set robots starting position in world
        self.set_robot_start_pos()
        self.robot0Obj.inSimulation = True
        self.robot0Obj.setMaxVelocity(DEFAULT_MAX_MULT)
        
        # Reset physics
        self.robot0Obj.wb_node.resetPhysics()

        # If automatic camera
        if self.config.automatic_camera and self.camera.wb_viewpoint_node:
            self.camera.follow(self.robot0Obj, ROBOT_NAME)

        if self.config.recording:
            Recorder.resetCountDown(self)

        self.lastTime = self.getTime()
        self.firstFrame = False
        self.robotInitialized = True
        
        self.lastRealTime = time.time()
    
    def relocate_robot(self):
        '''Relocate robot to last visited checkpoint'''
        # Get last checkpoint visited
        relocatePosition = self.robot0Obj.lastVisitedCheckPointPosition

        # Set position of robot
        self.robot0Obj.position = [relocatePosition[0], -0.03, relocatePosition[2]]
        self.robot0Obj.rotation = [0, 1, 0, 0]

        # Reset physics
        self.robot0Obj.wb_node.resetPhysics()

        # Notify robot
        self.emitter.send(struct.pack("c", bytes("L", "utf-8")))

        # Update history with event
        self.robot0Obj.increaseScore("Lack of Progress", -5, self)
        
        if self.config.automatic_camera and self.camera.wb_viewpoint_node:
            self.camera.setViewPoint(self.robot0Obj)


    def robot_quit(self, num, timeup):
        '''Quit robot from simulation'''
        # Quit robot if present
        if self.robot0Obj.inSimulation:
            # Remove webots node
            self.robot0Obj.wb_node.remove()
            self.robot0Obj.inSimulation = False
            # Send message to robot window to update quit button
            self.rws.send("robotNotInSimulation"+str(num))
            # Update history event whether its manual or via exit message
            if not timeup:
                self.robot0Obj.history.enqueue("Successful Exit", self)
            self.write_log()


    def add_robot(self):
        '''Add robot via MFNode from a string'''
        
        controller = "robot0Controller"
        if self.remoteEnabled:
            controller = "<extern>"

        # Get webots root
        root = self.getRoot()
        root_children_field = root.getField('children')
        # Get robot to insert into world
        root_children_field.importMFNodeFromString(
                -1, 'DEF ROBOT0 custom_robot { translation 1000 1000 1000 rotation 0 1 0 0 name "'+ROBOT_NAME+'" controller "'+controller+'" camera_fieldOfView 1 camera_width 64 camera_height 40 }')
        # Update robot window to say robot is in simulation
        self.rws.send("robotInSimulation0")

        return self.getFromDef("ROBOT0")


    def create_log_str(self):
        '''Create log text for log file'''
        # Get robot events
        r0_str = self.robot0Obj.get_log_str()

        log_str = f"""MAX_GAME_DURATION: {str(int(self.maxTime/60))}:00
ROBOT_0_SCORE: {str(self.robot0Obj.getScore())}

ROBOT_0: {str(self.robot0Obj.name)}
{r0_str}"""

        return log_str


    def write_log(self):
        '''Write log file'''
        # Get log text
        log_str = self.create_log_str()
        # Get relative path to logs dir 
        filePath = getFilePath("logs/", "../../logs/")

        # Create file name using date and time
        file_date = datetime.datetime.now()
        logFileName = file_date.strftime("gameLog %m-%d-%y %H,%M,%S")

        filePath = os.path.join(filePath, logFileName + ".txt")

        try:
            # Write file
            logsFile = open(filePath, "w")
            logsFile.write(log_str)
            logsFile.close()
        except:
            # If write file fails, most likely due to missing logs dir
            Console.log_err(f"Couldn't write log file, no log directory: {filePath}")


    def set_robot_start_pos(self):
        '''Set robot starting position'''

        starting_tile_node = self.getFromDef("START_TILE")

        # Get the starting tile minimum node and translation
        starting_PointMin = self.getFromDef("start0min")
        starting_minPos = starting_PointMin.getField("translation")

        # Get maximum node and translation
        starting_PointMax = self.getFromDef("start0max")
        starting_maxPos = starting_PointMax.getField("translation")

        # Get the vector positons
        starting_minPos = starting_minPos.getSFVec3f()
        starting_maxPos = starting_maxPos.getSFVec3f()
        starting_centerPos = [(starting_maxPos[0]+starting_minPos[0])/2,
                            starting_maxPos[1], (starting_maxPos[2]+starting_minPos[2])/2]

        startingTileObj = StartTile([starting_minPos[0], starting_minPos[2]], [
                                    starting_maxPos[0], starting_maxPos[2]], starting_tile_node, center=starting_centerPos,)

        self.robot0Obj.startingTile = startingTileObj
        self.robot0Obj.lastVisitedCheckPointPosition = startingTileObj.center
        self.robot0Obj.startingTile.wb_node.getField("start").setSFBool(False)
        self.robot0Obj.visitedCheckpoints.append(startingTileObj.center)

        self.robot0Obj.position = [startingTileObj.center[0],
                            startingTileObj.center[1], startingTileObj.center[2]]
        self.robot0Obj.set_starting_orientation()


    def add_map_multiplier(self):
        score_change = self.robot0Obj.getScore() * self.robot0Obj.map_score_percent
        self.robot0Obj.increaseScore("Map Bonus", score_change, self)

    def process_robot_json(self, json_data):
        '''Process json file to generate robot file'''
        robot_json = json.loads(json_data)
        if generate_robot_proto(robot_json):
            self.rws.send("loaded1")

    def wait(self, sec):
        first = self.getTime()
        while True:
            self.step(TIME_STEP)
            if self.getTime() - first > sec:
                break
        return

    def get_worlds(self):           
        path = getFilePath("worlds", "../../worlds")    

        files = [file for file in os.listdir(path) if file[-3:] == 'wbt']
        return ','.join(files)


    def load_world(self, world):
        path = getFilePath("worlds", "../../worlds")

        path = os.path.join(path, world)
        self.worldLoad(path)
        
    def load_test_script(self):
        path = getFilePath("controllers/MainSupervisor/tests.py", "tests.py")
        dest = getFilePath("controllers/robot0Controller/robot0Controller.py", "../robot0Controller/robot0Controller.py")
        shutil.copyfile(path, dest)

    def getSimulationVersion(self):
        try:
            self.rws.send("version", f"{self.version}")
            # Check updates
            url = "https://gitlab.com/api/v4/projects/22054848/releases"
            response = req.get(url)
            releases = response.json()
            releases = list(
                filter(lambda release: release['tag_name'].startswith(f"v{self.stream}"), releases))
            if len(releases) > 0:
                if releases[0]['tag_name'].replace('_', ' ') == f'v{self.version}':
                    self.rws.send("latest", f"{self.version}")
                elif any([r['tag_name'].replace('_', ' ') == f'v{self.version}' for r in releases]):
                   self.rws.send("outdated", f"{self.version},{releases[0]['tag_name'].replace('v','').replace('_', ' ')}")
                else:
                    self.rws.send("unreleased", f"{self.version}")
            else:
                self.rws.send("version", f"{self.version}")
        except:
            self.rws.send("version", f"{self.version}")

    def processMessage(self, robotMessage):
        Console.log_debug(f"Robot Stopped for {self.robot0Obj.timeStopped(self)}s")
        # If exit message is correct
        if robotMessage[0] == 'E':
            # Check robot position is on starting tile
            if self.robot0Obj.startingTile.checkPosition(self.robot0Obj.position):
                self.gameState = MATCH_FINISHED
                self.rws.send("ended")
                if self.robot0Obj.victimIdentified:
                    self.robot0Obj.increaseScore(
                        "Exit Bonus", self.robot0Obj.getScore() * 0.1, self)
                else:
                    self.robot0Obj.history.enqueue("No Exit Bonus", self)
                self.add_map_multiplier()
                # Update score and history
                self.robot_quit(0, False)
                self.lastFrame = True

        elif robotMessage[0] == 'M':
            try:
                # If map_data submitted
                if self.robot0Obj.map_data.size != 0:
                    # If not previously evaluated
                    if not self.robot0Obj.sent_maps:
                        map_score = MapScorer.calculateScore(
                            self.mapSolution, self.robot0Obj.map_data)

                        self.robot0Obj.history.enqueue(
                            f"Map Correctness {str(round(map_score * 100,2))}%", self)

                        # Add percent
                        self.robot0Obj.map_score_percent = map_score
                        self.robot0Obj.sent_maps = True

                        self.robot0Obj.map_data = np.array([])
                    else:
                        Console.log_err(f"The map has already been evaluated.")
                else:
                    Console.log_err("Please send your map data before hand.")
            except Exception as e:
                Console.log_err("Map scoring error. Please check your code. (except)")
                Console.log_err(str(e))

        elif robotMessage[0] == 'L':
            self.relocate_robot()
            self.robot0Obj.resetTimeStopped()

        elif robotMessage[0] == 'G':
            self.emitter.send(struct.pack("c f i", bytes(
                "G", "utf-8"), round(self.robot0Obj.getScore(), 2), self.maxTime - int(self.timeElapsed)))

        # If robot stopped for 1 second
        elif self.robot0Obj.timeStopped(self) >= 1.0:

            # Get estimated values
            est_vic_pos = robotMessage[0]
            est_vic_type = robotMessage[1]
            
            iterator = self.victimManager.humans
            name = 'Victim'

            if est_vic_type.lower() in list(map(toLower, HazardMap.HAZARD_TYPES)):
                iterator = self.victimManager.hazards
                name = 'Hazard'

            misidentification = True
            
            nearby_map_issues = [h for h in iterator if h.checkPosition(self.robot0Obj.position) and h.checkPosition(est_vic_pos) and h.onSameSide(self.robot0Obj.position) and not h.identified]
            
            Console.log_debug(f"--- Victim Data ---")
            for h in iterator:
                Console.log_debug(f"Distance {h.getDistance(self.robot0Obj.position)}/0.09 in range ({h.checkPosition(self.robot0Obj.position)})")
                Console.log_debug(f"Est distance in range: {h.checkPosition(est_vic_pos)}")
                Console.log_debug(f"On same side: {h.onSameSide(self.robot0Obj.position)}")
                Console.log_debug(f"Identified: {h.identified}")
            Console.log_debug(f"--- ----------- ---")
            Console.log_debug(f"Nearby issues: {len(nearby_map_issues)}")
            
            if len(nearby_map_issues) > 0:
                # TODO Should it iterate through all nearby map issues or just take the first one???
                nearby_issue = nearby_map_issues[0]
                
                misidentification = False
                # Get points scored depending on the type of victim
                #pointsScored = nearby_issue.scoreWorth

                grid = self.tileManager.coord2grid(nearby_issue.wb_translationField.getSFVec3f(), self)
                roomNum = self.getFromDef("WALLTILES").getField("children").getMFNode(grid).getField("room").getSFInt32() - 1

                Console.log_debug(f"Victim type est. {est_vic_type.lower()} vs {nearby_issue.simple_victim_type.lower()}")

                # Update score and history
                if est_vic_type.lower() == nearby_issue.simple_victim_type.lower():
                    self.robot0Obj.increaseScore(
                        f"Successful {name} Type Correct Bonus", 10, self, multiplier=self.tileManager.ROOM_MULT[roomNum])
                        
                self.robot0Obj.increaseScore(
                    f"Successful {name} Identification", nearby_issue.scoreWorth, self, multiplier=self.tileManager.ROOM_MULT[roomNum])
                self.robot0Obj.victimIdentified = True

                nearby_issue.identified = True

            if misidentification:
                self.robot0Obj.increaseScore(f"Misidentification of {name}", -5, self)

    def receive(self, message):
        
        parts = message.split(",")

        # If there are parts
        if len(parts) > 0:
            if parts[0] == "run":
                # Start running the match
                self.gameState = MATCH_RUNNING
                self.rws.updateHistory("runPressed")
            if parts[0] == "pause":
                # Pause the match
                self.gameState = MATCH_PAUSED
                self.rws.updateHistory("pausedPressed")
            if parts[0] == "reset":
                self.robot_quit(0, False)
                # Reset both controller files
                #self.robot0Obj.controller.resetFile(self)
                #self.robot0Obj.resetProto(self)
                self.victimManager.resetVictimsTextures()

                # Reset the simulation
                self.simulationReset()
                self.gameState = MATCH_FINISHED
                
                # Restart this supervisor
                self.mainSupervisor.restartController()

                if self.robot0Obj.startingTile != None:
                    # Show start tile
                    self.robot0Obj.startingTile.wb_node.getField("start").setSFBool(True)

                # Must restart world - to reload to .wbo file for the robot which only seems to be read and interpreted
                # once per game, so if we load a new robot file, the new changes won't come into place until the world
                # is reset!
                self.worldReload()

            if parts[0] == "robot0Unload":
                # Unload the robot 0 controller
                if self.gameState == MATCH_NOT_STARTED:
                    self.robot0Obj.controller.reset(self)

            if parts[0] == "robot1Unload":
                # Remove the robot proto
                if self.gameState == MATCH_NOT_STARTED:
                    self.robot0Obj.resetProto(self, True)

            if parts[0] == 'relocate':
                data = message.split(",", 1)
                if len(data) > 1:
                    if int(data[1]) == 0:
                        self.relocate_robot()

            if parts[0] == 'quit':
                data = message.split(",", 1)
                if len(data) > 1:
                    if int(data[1]) == 0:
                        if self.gameState == MATCH_RUNNING:
                            self.add_map_multiplier()
                            self.robot0Obj.history.enqueue("Give up!", self)
                            self.robot_quit(0, True)
                            self.gameState = MATCH_FINISHED
                            self.lastFrame = True
                            self.rws.send("ended")

            if parts[0] == 'robotJson':
                data = message.split(",", 1)
                if len(data) > 1:
                    self.process_robot_json(data[1])

            if parts[0] == 'config':
                configData = list(map((lambda x: int(x)), message.split(",")[1:]))
                self.config = Config(configData, self.config.path)
                self.robot0Obj.updateConfig(self.config)
                
                with open(self.config.path, 'w') as f:
                    f.write(','.join(message.split(",")[1:]))

            if parts[0] == 'loadWorld':
                self.load_world(parts[1])
                
            if parts[0] == 'loadTest':
                self.load_test_script()
            if parts[0] == 'runTest':
                self.gameState = MATCH_RUNNING
                self.runTests = True
                self.config.disableLOP = True
            if parts[0] == 'rw_reload':
                self.rws.sendAll()
                # TODO might be better way -- may cause bugs
                configFilePath = getFilePath("controllers/MainSupervisor/config.txt", "config.txt")
                self.config = self.getConfig(configFilePath)
                
            if parts[0] == 'loadControllerPressed':
                self.rws.updateHistory("loadControllerPressed,", parts[1])
            if parts[0] == 'unloadControllerPressed':
                self.rws.updateHistory("unloadControllerPressed,", parts[1])
                
            if parts[0] == 'remoteEnable':
                self.remoteEnabled = True
                self.rws.updateHistory("remoteEnabled")
            if parts[0] == 'remoteDisable':
                self.remoteEnabled = False
                self.rws.updateHistory("remoteDisabled")
            if parts[0] == 'getWorlds':
                self.rws.send('worlds', f'{str(self.get_worlds())}')

    def getConfig(self, configFilePath):
            
        with open(configFilePath, 'r') as f:
            configData = f.read().split(',')
            
        self.rws.send("config",  ','.join(configData))
        configData = list(map((lambda x: int(x)), configData))
        
        return Config(configData, configFilePath)

    def update(self):
        
        # If last frame
        if self.lastFrame == True:
            self.lastFrame = -1
            self.gameState = MATCH_FINISHED
            if self.config.recording:              
                Recorder.stopRecording(self)

        # The first frame of the game running only
        if self.firstFrame and self.gameState == MATCH_RUNNING:
            self.game_init()

        if self.runTests:
            self.testRunner.run(self)

        # Main game loop
        if self.robot0Obj.inSimulation:
            self.robot0Obj.updateTimeElapsed(self.timeElapsed)

            # Automatic camera movement
            if self.config.automatic_camera and self.camera.wb_viewpoint_node:
                nearVictims = [h for h in (self.victimManager.humans + self.victimManager.hazards) if h.checkPosition(self.robot0Obj.position, 0.20) and h.onSameSide(self.robot0Obj.position)]
                if len(nearVictims) > 0:
                    if(len(nearVictims) > 1):
                        # Sort by closest
                        nearVictims.sort(key=lambda v: v.getDistance(self.robot0Obj.position))
                    side = nearVictims[0].getSide()
                    self.camera.updateView(side, self.robot0Obj)

            # Test if the robots are in checkpoints
            checkpoint = [c for c in self.tileManager.checkpoints if c.checkPosition(self.robot0Obj.position)]
            # If any checkpoints
            if len(checkpoint) > 0:
                self.tileManager.updateCheckpoints(self.robot0Obj, checkpoint[0], self)

            # Check if the robots are in swamps
            inSwamp = any([s.checkPosition(self.robot0Obj.position) for s in self.tileManager.swamps])
            self.tileManager.updateInSwamp(self.robot0Obj, inSwamp, DEFAULT_MAX_MULT, self)

            # If receiver has got a message
            if self.receiver.getQueueLength() > 0:
                # Get receiver data
                receivedData = self.receiver.getBytes()
                testMsg = False
                if self.runTests:
                    testMsg = self.testRunner.getStage(receivedData)
                    self.receiver.nextPacket()
                if not testMsg:
                    self.robot0Obj.setMessage(receivedData)
                    self.receiver.nextPacket()

                # If data sent to receiver
                if self.robot0Obj.message != []:
                    r0_message = self.robot0Obj.message
                    Console.log_debug(f"Robot Message: {r0_message}")
                    self.robot0Obj.message = []
                    self.processMessage(r0_message)

            if self.gameState == MATCH_RUNNING:
                # Relocate robot if stationary for 20 sec
                if self.robot0Obj.timeStopped(self) >= 20:
                    if not self.config.disableLOP:
                        self.relocate_robot()
                    self.robot0Obj.resetTimeStopped()
                elif self.robot0Obj.timeStopped(self) >= 3 and self.robot0Obj.inSwamp:
                    if not self.sWarnCooldown:
                        self.sWarnCooldown = True
                        Console.log_warn("Detected the robot stopped moving in a swamp. This could be due to not setting the wheel motor velocities every time step.\nSee Erebus 22.0.0 changelog for more details.")

                if self.robot0Obj.position[1] < -0.035 and self.gameState == MATCH_RUNNING:
                    if not self.config.disableLOP:
                        self.relocate_robot()
                    self.robot0Obj.resetTimeStopped()

        if self.robotInitialized:
            # Send the update information to the robot window
            nowScore = self.robot0Obj.getScore()
            self.timeElapsed = min(self.timeElapsed, self.maxTime)
            self.realTimeElapsed = min(self.realTimeElapsed, self.maxRealWorldTime)
            if self.lastSentScore != nowScore or self.lastSentTime != int(self.timeElapsed) or self.lastSentRealTime != int(self.realTimeElapsed):
                self.rws.send("update", str(round(nowScore, 2)) + "," + str(int(self.timeElapsed)) + "," + str(self.maxTime) + "," + str(int(self.realTimeElapsed)))
                self.lastSentScore = nowScore
                self.lastSentTime = int(self.timeElapsed)
                self.lastSentRealTime = int(self.realTimeElapsed)
                if self.config.recording:
                    Recorder.update(self)

            # If the time is up
            if (self.timeElapsed >= self.maxTime or self.realTimeElapsed >= self.maxRealWorldTime) and self.lastFrame != -1:
                self.add_map_multiplier()
                self.robot_quit(0, True)
                
                self.gameState = MATCH_FINISHED
                self.lastFrame = True
                
                self.rws.send("ended")

        # Get the message in from the robot window(if there is one)
        message = self.wwiReceiveText()
        while message not in ['', None]:
            self.receive(message)
            message = self.wwiReceiveText()

        if self.gameState == MATCH_PAUSED:
            self.step(0)
            time.sleep(0.01)
            self.lastRealTime = time.time()

        # If the match is running
        if self.robotInitialized and self.gameState == MATCH_RUNNING:
            # If waiting for a remote controller, don't count time waiting
            if self.remoteEnabled and self.firstRealTime and self.lastTime != self.getTime():
                self.lastRealTime = time.time()
                self.firstRealTime = False
            # Get real world time (for 9 min real world time elapsed rule)
            self.realTimeElapsed += (time.time() - self.lastRealTime)
            self.lastRealTime = time.time()
            # Get the time since the last frame
            frameTime = self.getTime() - self.lastTime
            # Add to the elapsed time
            self.timeElapsed += frameTime
            # Get the current time
            self.lastTime = self.getTime()
            # Step the simulation on
            step = self.step(TIME_STEP)
            # If the simulation is terminated or the time is up
            if step == -1:
                # Stop simulating
                self.gameState = MATCH_FINISHED

        elif self.firstFrame or self.lastFrame or self.gameState == MATCH_FINISHED:
            # Step simulation
            self.step(TIME_STEP)


if __name__ == '__main__':
    
    game = Game()
       
    while True: # Main loop
        game.update()
