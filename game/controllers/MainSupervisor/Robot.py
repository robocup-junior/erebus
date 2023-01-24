import AutoInstall
import datetime
import os
import shutil
import filecmp
import glob
import struct

from Controller import Controller
from ConsoleLog import Console

AutoInstall._import("cl", "termcolor")
AutoInstall._import("np", "numpy")

class Queue:
    #Simple queue data structure
    def __init__(self):
        self.queue = []

    def enqueue(self, data):
        return self.queue.append(data)

    def dequeue(self):
        return self.queue.pop(0)

    def peek(self):
        return self.queue[0]

    def is_empty(self):
        return len(self.queue) == 0

class RobotHistory(Queue):
    #Robot history class inheriting a queue structure
    def __init__(self):
        super().__init__()
        #master history to store all events without dequeues
        self.master_history = []
        self.timeElapsed = 0
        self.displayToRecordingLabel = False

    def enqueue(self, data, supervisor):
        #update master history when an event happens
        record = self.update_master_history(data)
        supervisor.rws.send("historyUpdate", ",".join(record))
        hisT = ""
        histories = list(reversed(self.master_history))
        for h in range(min(len(histories),5)):
            hisT = "[" + histories[h][0] + "] " + histories[h][1] + "\n" + hisT

        if self.displayToRecordingLabel:
            supervisor.setLabel(2, hisT, 0.7, 0,0.05, 0xfbc531, 0.2)

    def update_master_history(self, data):
        #Get time
        time = int(self.timeElapsed)
        minute = str(datetime.timedelta(seconds=time))[2:]
        #update list with data in format [game time, event data]
        record = [minute, data]
        self.master_history.append(record)
        return record

class Robot:
    '''Robot object to hold values whether its in a base or holding a human'''

    def __init__(self):
        '''Initialises the in a base, has a human loaded and score values'''

        #webots node
        # self.wb_node = node

        # if self.wb_node != None:
        #     self.wb_translationField = self.wb_node.getField('translation')
        #     self.wb_rotationField = self.wb_node.getField('rotation')

        self.inCheckpoint = True
        self.inSwamp = False

        self.history = RobotHistory()

        self._score = 0

        self.robot_timeStopped = 0
        self.stopped = False
        self.stoppedTime = None

        self.message = []
        self.map_data = np.array([])
        self.sent_maps = False
        self.map_score_percent = 0

        self.victimIdentified = False

        self.lastVisitedCheckPointPosition = []

        self.visitedCheckpoints = []

        self.startingTile = None

        self.inSimulation = False

        self.name = "NO_TEAM_NAME"

        self.left_exit_tile = False
        
        self.timeElapsed = 0
        
        self.controller = Controller()


    @property
    def position(self) -> list:
        return self.wb_translationField.getSFVec3f()

    @position.setter
    def position(self, pos: list) -> None:
        self.wb_translationField.setSFVec3f(pos)

    @property
    def rotation(self) -> list:
        return self.wb_rotationField.getSFRotation()

    @rotation.setter
    def rotation(self, pos: list) -> None:
        self.wb_rotationField.setSFRotation(pos)
        
    def add_node(self, node):
        self.wb_node = node
        self.wb_translationField = self.wb_node.getField('translation')
        self.wb_rotationField = self.wb_node.getField('rotation')

    def setMaxVelocity(self, vel: float) -> None:
        # self.wb_node.getField('max_velocity').setSFFloat(vel)
        # self.wb_node.getField('robot_mass').setSFFloat(vel)
        self.wb_node.getField('wheel_mult').setSFFloat(vel)
        # self.wb_node.getField('wheel_mass').setSFFloat(vel)

    def _isStopped(self) -> bool:
        vel = self.wb_node.getVelocity()
        return all(abs(ve) < 0.001 for ve in vel)

    def timeStopped(self, supervisor) -> float:
        self.stopped = self._isStopped()

        # if it isn't stopped yet
        if self.stoppedTime == None:
            if self.stopped:
                # get time the robot stopped
                self.stoppedTime = supervisor.getTime()
        else:
            # if its stopped
            if self.stopped:
                # get current time
                currentTime = supervisor.getTime()
                # calculate the time the robot stopped
                self.robot_timeStopped = currentTime - self.stoppedTime
            else:
                # if it's no longer stopped, reset variables
                self.stoppedTime = None
                self.robot_timeStopped = 0
        return self.robot_timeStopped
    
    def resetTimeStopped(self):
        self.robot_timeStopped = 0
        self.stopped = False
        self.stoppedTime = None

    def increaseScore(self, message: str, score: int, supervisor, multiplier = 1) -> None:
        point = round(score * multiplier, 2)
        if point > 0.0:
            self.history.enqueue(f"{message} +{point}", supervisor)
        elif point < 0.0:
            self.history.enqueue(f"{message} {point}", supervisor)
        self._score += point
        if self._score < 0:
            self._score = 0

    def getScore(self) -> int:
        return self._score

    def get_log_str(self):
        #Create a string of all events that the robot has done
        history = self.history.master_history
        log_str = ""
        for event in history:
            log_str += str(event[0]) + " " + event[1] + "\n"

        return log_str

    def set_starting_orientation(self):
        '''Gets starting orientation for robot using wall data from starting tile'''
        # Get starting tile walls
        top = self.startingTile.wb_node.getField("topWall").getSFInt32()
        right = self.startingTile.wb_node.getField("rightWall").getSFInt32()
        bottom = self.startingTile.wb_node.getField("bottomWall").getSFInt32()
        left = self.startingTile.wb_node.getField("leftWall").getSFInt32()

        # top: 0
        # left: pi/2
        # right: -pi/2
        # bottom: pi
        pi = 3.14
        walls = [[top, 0],[right, -pi/2],[bottom, pi],[left, pi/2]]
        direction = 0

        for i in range(len(walls)):
            # If there isn't a wall in the direction
            if not walls[i][0]:
                direction = walls[i][1]
                break

        self.rotation = [0,1,0,direction]
    
    def setMessage(self, receivedData):
        # Get length of bytes
        rDataLen = len(receivedData)
        Console.log_debug(f"Data: {receivedData} with length {rDataLen}")
        try:
            if rDataLen == 1:
                tup = struct.unpack('c', receivedData)
                self.message = [tup[0].decode("utf-8")]
            # Victim identification bytes data should be of length = 9
            elif rDataLen == 9:
                # Unpack data
                tup = struct.unpack('i i c', receivedData)

                # Get data in format (est. x position, est. z position, est. victim type)
                x = tup[0]
                z = tup[1]

                estimated_victim_position = (x / 100, 0, z / 100)

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
                shape_bytes = receivedData[:8]  # Get shape of matrix
                data_bytes = receivedData[8::]  # Get data of matrix

                # Get shape data
                shape = struct.unpack('2i', shape_bytes)
                # Size of flattened 2d array
                shape_size = shape[0] * shape[1]
                # Get map data
                map_data = data_bytes.decode('utf-8').split(',')
                # Reshape data using the shape data given
                reshaped_data = np.array(map_data).reshape(shape)

                self.map_data = reshaped_data
        except Exception as e:
            Console.log_err("Incorrect data format sent")
            Console.log_err(str(e))

    def updateTimeElapsed(self, timeElapsed: int):
        self.timeElapsed = timeElapsed
        self.history.timeElapsed = timeElapsed
        
    def updateConfig(self, config):
        self.history.displayToRecordingLabel = config.recording
        self.controller.updateKeepControllerConfig(config)
        
    def resetProto(self, supervisor, manual=False) -> None:
        '''
        - Send message to robot window to say that robot has been reset
        - Reset robot proto file back to default
        '''
        path = os.path.dirname(os.path.abspath(__file__))

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
                if self.controller.keepController and not manual:
                    if not filecmp.cmp(default_robot_proto, robot_proto):
                        supervisor.rws.send("loaded1")
                    return
                shutil.copyfile(default_robot_proto, robot_proto)
            else:
                shutil.copyfile(default_robot_proto, robot_proto)
                supervisor.worldReload()
            supervisor.rws.send("unloaded1")
        except Exception as e:
            Console.log_err(f"Error resetting robot proto")
            Console.log_err(str(e))
