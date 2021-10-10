"""Supervisor Controller
   Written by Robbie Goldman and Alfred Roberts
"""

from controller import Supervisor
import os
import shutil
import struct
import math
import datetime
import threading
import shutil
import json
import AutoInstall
AutoInstall._import("np", "numpy")
AutoInstall._import("cl", "termcolor")
AutoInstall._import("req", "requests")
import ControllerUploader
import MapScorer
import obstacleCheck
import glob
import json
import filecmp
import obstacleCheck
import mapAnswer

# Version info
stream = 21
version = "21.2.2"


# Create the instance of the supervisor class
supervisor = Supervisor()

# Get this supervisor node - so that it can be rest when game restarts
mainSupervisor = supervisor.getFromDef("MAINSUPERVISOR")

maxTimeMinute = 8
# Maximum time for a match
maxTime = maxTimeMinute * 60

DEFAULT_MAX_VELOCITY = 6.28

#Room multipliers
roomMult = [1, 1.25, 1.5]

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

    def enqueue(self, data):
        #update master history when an event happens
        record = self.update_master_history(data)
        supervisor.wwiSendText("historyUpdate" + "," + ",".join(record))
        hisT = ""
        histories = list(reversed(self.master_history))
        for h in range(min(len(histories),5)):
            hisT = "[" + histories[h][0] + "] " + histories[h][1] + "\n" + hisT
        if configData[2]:
          supervisor.setLabel(2, hisT, 0.7, 0,0.05, 0xfbc531, 0.2)

    def update_master_history(self, data):
        #Get time
        time = int(timeElapsed)
        minute = str(datetime.timedelta(seconds=time))[2:]
        #update list with data in format [game time, event data]
        record = [minute, data]
        self.master_history.append(record)
        return record


class Robot:
    '''Robot object to hold values whether its in a base or holding a human'''

    def __init__(self, node=None):
        '''Initialises the in a base, has a human loaded and score values'''

        #webots node
        self.wb_node = node

        if self.wb_node != None:
            self.wb_translationField = self.wb_node.getField('translation')
            self.wb_rotationField = self.wb_node.getField('rotation')

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

    def setMaxVelocity(self, vel: float) -> None:
        self.wb_node.getField('max_velocity').setSFFloat(vel)

    def _isStopped(self) -> bool:
        vel = self.wb_node.getVelocity()
        return all(abs(ve) < 0.1 for ve in vel)


    def timeStopped(self) -> float:
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

    def increaseScore(self, message: str, score: int, multiplier = 1) -> None:
      point = round(score * multiplier, 2)
      if point > 0.0:
        self.history.enqueue(f"{message} +{point}")
      elif point < 0.0:
        self.history.enqueue(f"{message} {point}")
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

class VictimObject():
    '''Victim object holding the boundaries'''

    def __init__(self, node, ap: int, vtype: str, score: int):
        '''Initialises the radius and position of the human'''

        self.wb_node = node

        self.wb_translationField = self.wb_node.getField('translation')

        self.wb_rotationField = self.wb_node.getField('rotation')

        self.wb_typeField = self.wb_node.getField('type')
        self.wb_foundField = self.wb_node.getField('found')

        self.arrayPosition = ap
        self.scoreWorth = score
        self._victim_type = vtype

        self.simple_victim_type = self.get_simple_type()

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

    @property
    def victim_type(self) -> list:
        return self.wb_typeField.getSFString()

    @victim_type.setter
    def victim_type(self, v_type: str):
        self.wb_typeField.setSFString(v_type)

    @property
    def identified(self) -> list:
        return self.wb_foundField.getSFBool()

    @identified.setter
    def identified(self, idfy: int):
        self.wb_foundField.setSFBool(idfy)
        
    def get_simple_type(self):
        # Will be overloaded
        pass

    def checkPosition(self, pos: list, radius:float = 0.09) -> bool:
        '''Check if a position is near an object, based on the min_dist value'''
        # Get distance from the object to the passed position using manhattan distance for speed
        # TODO Check if we want to use euclidian or manhattan distance -- currently manhattan
        distance = math.sqrt(((self.position[0] - pos[0])**2) + ((self.position[2] - pos[2])**2))
        return distance <= radius
    
    def getDistance(self, pos: list) -> bool:
        return (((self.position[0] - pos[0])**2) + ((self.position[2] - pos[2])**2))
        
    def onSameSide(self, pos: list) -> bool:
        #Get side the victim pointing at

        #0 1 0 -pi/2 -> X axis
        #0 1 0 pi/2 -> -X axis
        #0 1 0 pi -> Z axis
        #0 1 0 0 -> -Z axis

        rot = self.rotation[3]
        rot = round(rot, 2)

        if rot == -1.57:
            #X axis
            robot_x = pos[0]
            if robot_x > self.position[0]:
                return True
        elif rot == 1.57:
            #-X axis
            robot_x = pos[0]
            if robot_x < self.position[0]:
                return True
        elif rot == 3.14:
            #Z axis
            robot_z = pos[2]
            if robot_z > self.position[2]:
                return True
        elif rot == 0:
            #-Z axis
            robot_z = pos[2]
            if robot_z < self.position[2]:
                return True

        return False

    def getSide(self) -> str:
        #Get side the victim pointing at
        rot = self.rotation[3]
        rot = round(rot, 2)

        if rot == -1.57:
            return "right"
        elif rot == 1.57:
            return "left"
        elif rot == 3.14:
            return "bottom"
        else:
            return "top"

class Victim(VictimObject):
    '''Human object holding the boundaries'''
    
    HARMED = 'harmed'
    UNHARMED = 'unharmed'
    STABLE = 'stable'
    
    VICTIM_TYPES = [HARMED,UNHARMED,STABLE]

    def get_simple_type(self):
      # Get victim type via proto node
      if self._victim_type == Victim.HARMED:
          return 'H'
      elif self._victim_type == Victim.UNHARMED:
          return 'U'
      elif self._victim_type == Victim.STABLE:
          return 'S'
      else:
          return self._victim_type

class HazardMap(VictimObject):
    
    HAZARD_TYPES = ['F','P','C','O']
    
    def get_simple_type(self):
        return self._victim_type
  
class Tile():
    '''Tile object holding the boundaries'''

    def __init__(self, min: list, max: list, center: list):
        '''Initialize the maximum and minimum corners for the tile'''
        self.min = min
        self.max = max
        self.center = center

    def checkPosition(self, pos: list) -> bool:
        '''Check if a position is in this checkpoint'''
        # If the x position is within the bounds
        if pos[0] >= self.min[0] and pos[0] <= self.max[0]:
            # if the z position is within the bounds
            if pos[2] >= self.min[1] and pos[2] <= self.max[1]:
                # It is in this checkpoint
                return True

        # It is not in this checkpoint
        return False


class Checkpoint(Tile):
    '''Checkpoint object holding the boundaries'''

    def __init__(self, min: list, max: list, center=None):
        super().__init__(min, max, center)


class Swamp(Tile):
    '''Swamp object holding the boundaries'''

    def __init__(self, min: list, max: list, center=None):
        super().__init__(min, max, center)


class StartTile(Tile):
    '''StartTile object holding the boundaries'''

    def __init__(self, min: list, max: list, wb_node, center=None):
        super().__init__(min, max, center)
        self.wb_node = wb_node


def resetControllerFile(manual=False) -> None:
    '''Remove the controller'''
    path = os.path.dirname(os.path.abspath(__file__))
    if path[-4:] == "game":
      path = os.path.join(path, "controllers/robot0Controller")
    else:
      path = os.path.join(path, "../robot0Controller")

    if configData[0] and not manual:
      files = glob.glob(os.path.join(path, "*"))
      if len(files) > 0:
        supervisor.wwiSendText("loaded0")
      return
    
    shutil.rmtree(path)
    os.mkdir(path)

def resetController(num: int) -> None:
    '''Send message to robot window to say that controller has been unloaded'''
    resetControllerFile(True)
    supervisor.wwiSendText("unloaded"+str(num))

def resetRobotProto(manual=False) -> None:
    '''
    - Send message to robot window to say that robot has been reset
    - Reset robot proto file back to default
    '''
    path = os.path.dirname(os.path.abspath(__file__))

    if path[-4:] == "game":
      default_robot_proto = os.path.join(path, 'protos/E-puck-custom-default.proto')
      robot_proto = os.path.join(path,'protos/custom_robot.proto')
    else: 
      default_robot_proto = os.path.join(path, '../../protos/E-puck-custom-default.proto')
      robot_proto = os.path.join(path,'../../protos/custom_robot.proto')
      
    try:
        if os.path.isfile(robot_proto):
          if configData[0] and not manual:
            if not filecmp.cmp(default_robot_proto, robot_proto):
              supervisor.wwiSendText("loaded1")
            return
          shutil.copyfile(default_robot_proto, robot_proto)
        else:
          shutil.copyfile(default_robot_proto, robot_proto)          
          supervisor.worldReload()
        supervisor.wwiSendText("unloaded1")
    except:
      print(cl.colored(f"Error resetting robot proto", "red"))

def getHumans(humans, numberOfHumans):
    '''Get humans in simulation'''
    humanNodes = supervisor.getFromDef('HUMANGROUP').getField("children")
    # Iterate for each human
    for i in range(numberOfHumans):
        # Get each human from children field in the human root node HUMANGROUP
        human = humanNodes.getMFNode(i)

        victimType = human.getField('type').getSFString()
        scoreWorth = human.getField('scoreWorth').getSFInt32()

        # Create victim Object from victim position
        humanObj = Victim(human, i, victimType, scoreWorth)
        humans.append(humanObj)
        
def getHazards(hazards, numberOfHazards):
    '''Get hazards in simulation'''
    hazardNodes = supervisor.getFromDef('HAZARDGROUP').getField("children")
    # Iterate for each hazard
    for i in range(numberOfHazards):
        # Get each hazard from children field in the hazard root node HAZARDGROUP
        human = hazardNodes.getMFNode(i)

        hazardType = human.getField('type').getSFString()
        scoreWorth = human.getField('scoreWorth').getSFInt32()

        # Create hazard Object from hazard position
        hazardObj = HazardMap(human, i, hazardType, scoreWorth)
        hazards.append(hazardObj)

def getSwamps(swamps, numberOfSwamps):
    '''Get swamps in simulation'''
    # Iterate for each swamp
    for i in range(numberOfSwamps):
        # Get the swamp minimum node and translation
        swampMin = supervisor.getFromDef("swamp" + str(i) + "min")
        minPos = swampMin.getField("translation")
        # Get maximum node and translation
        swampMax = supervisor.getFromDef("swamp" + str(i) + "max")
        maxPos = swampMax.getField("translation")
        # Get the vector positions
        minPos = minPos.getSFVec3f()
        maxPos = maxPos.getSFVec3f()

        centerPos = [(maxPos[0]+minPos[0])/2,maxPos[1],(maxPos[2]+minPos[2])/2]
        # Create a swamp object using the min and max (x,z)
        swampObj = Checkpoint([minPos[0], minPos[2]], [maxPos[0], maxPos[2]], centerPos)
        swamps.append(swampObj)

def coord2grid(xzCoord):
    side = 0.3 * supervisor.getFromDef("START_TILE").getField("xScale").getSFFloat()
    height = supervisor.getFromDef("START_TILE").getField("height").getSFFloat()
    width = supervisor.getFromDef("START_TILE").getField("width").getSFFloat()
    return int(round((xzCoord[0] + (width / 2 * side)) / side, 0) * height + round((xzCoord[2] + (height / 2 * side)) / side, 0))

def getCheckpoints(checkpoints, numberOfCheckpoints):
    '''Get checkpoints in simulation'''
    # Iterate for each checkpoint
    for i in range(numberOfCheckpoints):
        # Get the checkpoint minimum node and translation
        checkpointMin = supervisor.getFromDef("checkpoint" + str(i) + "min")
        minPos = checkpointMin.getField("translation")
        # Get maximum node and translation
        checkpointMax = supervisor.getFromDef("checkpoint" + str(i) + "max")
        maxPos = checkpointMax.getField("translation")
        # Get the vector positions
        minPos = minPos.getSFVec3f()
        maxPos = maxPos.getSFVec3f()

        centerPos = [(maxPos[0]+minPos[0])/2,maxPos[1],(maxPos[2]+minPos[2])/2]
        # Create a checkpoint object using the min and max (x,z)
        checkpointObj = Checkpoint([minPos[0], minPos[2]], [maxPos[0], maxPos[2]], centerPos)
        checkpoints.append(checkpointObj)


def getObstacles():
    '''Returns list containing all obstacle positions and dimensions'''
    #Count the obstacles
    numberObstacles = supervisor.getFromDef('OBSTACLES').getField("children").getCount()
    #Get the node containing all the obstacles
    obstacleNodes = supervisor.getFromDef('OBSTACLES').getField("children")

    allObstaclesData = []

    #Iterate through the obstacles
    for i in range(0, numberObstacles):
        try:
            #Attempt to get the position and shape of the obstacle
            obstacle = obstacleNodes.getMFNode(i)
            xPos = obstacle.getField("xPos").getSFFloat()
            zPos = obstacle.getField("zPos").getSFFloat()
            width = obstacle.getField("width").getSFFloat()
            depth = obstacle.getField("depth").getSFFloat()
            obstacleData = [[xPos, zPos], [width, depth]]
            allObstaclesData.append(obstacleData)
        except:
            #If an error occured then it was not a proto obstacle
            print(cl.colored(f"Invalid obstacle found, it could not be tested", "red"))
    
    return allObstaclesData

def deactivateObstacles(allowedObstacles):
    '''Takes a list of bools if the value is false the obstacle will be removed from the simulation'''
    #Count the obstacles
    numberObstacles = supervisor.getFromDef('OBSTACLES').getField("children").getCount()
    #Get the node containing all the obstacles
    obstacleNodes = supervisor.getFromDef('OBSTACLES').getField("children")

    currentObstacle = 0
    nodesToDeactivate = []

    #Iterate through the obstacles
    for i in range(0, numberObstacles):
        try:
            #Attempt to get the obstacle (and check if it is a proto node)
            obs = obstacleNodes.getMFNode(i)
            obs.getField("rectangular").getSFBool()
            #If there is a boolean value indicating if it is allowed
            if currentObstacle < len(allowedObstacles):
                #If it is not allowed
                if not allowedObstacles[i]:
                    #Add it to the list for deactivaing
                    nodesToDeactivate.append([obs, currentObstacle])
                
                #Increment counter (used to give id of obstacle when deactivating)
                currentObstacle = currentObstacle + 1
        except:
            pass
    
    #Iterate through the node, id pairs
    for nodeData in nodesToDeactivate:
        try:
            node = nodeData[0]
            #Switch off all shapes - removes obstacle from simulation but remains in place and hierachy
            node.getField("rectangular").setSFBool(False)
            node.getField("cylindrical").setSFBool(False)
            node.getField("conical").setSFBool(False)
            node.getField("spherical").setSFBool(False)
            #Message to console that it has been removed
            print(cl.colored(f"Obstacle {nodeData[1]} removed, insufficient clearance to walls.", "orange"))
        except:
            #It was not a proto obstacle so it was ignored
            print(cl.colored(f"Invalid obstacle found, could not remove.", "red"))

def getTiles(grid=False):
    '''Returns list containing all tile positions and which walls are present, if grid is true it will be arranged as a 2d array not a list'''
    #Count the number of tiles
    numberTiles = supervisor.getFromDef('WALLTILES').getField("children").getCount()
    #Retrieve the node containing the tiles
    tileNodes = supervisor.getFromDef('WALLTILES').getField("children")

    allTilesData = []
    allTilesGrid = []

    #Iterate through the tiles
    for i in range(0, numberTiles):
        tile = tileNodes.getMFNode(i)
        #Get the width and height of the grid of tiles (dimensions of grid)
        width = tile.getField("width").getSFFloat()
        height = tile.getField("height").getSFFloat()

        #If the grid has not been set up
        if len(allTilesGrid) < 1:
            #Iterate for each row
            for row in range(0, int(height)):
                #Create a row
                dataRow = []
                #Iterate for each column
                for column in range(0, int(width)):
                    #Add an empty tile
                    dataRow.append(None)
                #Add the row to the 2d array
                allTilesGrid.append(dataRow)
        
        #Get the scale from the tile
        scale = [tile.getField("xScale").getSFFloat(), tile.getField("yScale").getSFFloat(), tile.getField("zScale").getSFFloat()]
        #Find the start position
        xStart = -(width * (0.3 * scale[0]) / 2.0)
        zStart = -(height * (0.3 * scale[2]) / 2.0)
        #Get position of the tile in the grid
        xPos = tile.getField("xPos").getSFInt32()
        zPos = tile.getField("zPos").getSFInt32()
        #Get the position of the tile in the world
        x = xPos * (0.3 * scale[0]) + xStart
        z = zPos * (0.3 * scale[2]) + zStart

        #Array to hold the wall information
        walls = []
        curved = False
        #Add the normal wall data to the array
        walls.append([tile.getField("topWall").getSFInt32() > 0, tile.getField("rightWall").getSFInt32() > 0, tile.getField("bottomWall").getSFInt32() > 0, tile.getField("leftWall").getSFInt32() > 0])
        #If this is a half sized tile
        if tile.getField("tile1Walls") != None:
            #Get the four sections of walls
            tile1Node = tile.getField("tile1Walls")
            tile2Node = tile.getField("tile2Walls")
            tile3Node = tile.getField("tile3Walls")
            tile4Node = tile.getField("tile4Walls")
            #Convert to array of booleans for each of the four sections (if the top, right, bottom and left walls are present)
            topLeftSmall = [tile1Node.getMFInt32(0) > 0, tile1Node.getMFInt32(1) > 0, tile1Node.getMFInt32(2) > 0, tile1Node.getMFInt32(3) > 0]
            topRightSmall = [tile2Node.getMFInt32(0) > 0, tile2Node.getMFInt32(1) > 0, tile2Node.getMFInt32(2) > 0, tile2Node.getMFInt32(3) > 0]
            bottomLeftSmall = [tile3Node.getMFInt32(0) > 0, tile3Node.getMFInt32(1) > 0, tile3Node.getMFInt32(2) > 0, tile3Node.getMFInt32(3) > 0]
            bottomRightSmall = [tile4Node.getMFInt32(0) > 0, tile4Node.getMFInt32(1) > 0, tile4Node.getMFInt32(2) > 0, tile4Node.getMFInt32(3) > 0]
            #Combine data into 2d array
            smallData = [topLeftSmall, topRightSmall, bottomLeftSmall, bottomRightSmall]
            #Collect the information about the curve into a list
            curveNode = tile.getField("curve")
            curveData = [curveNode.getMFInt32(0), curveNode.getMFInt32(1), curveNode.getMFInt32(2), curveNode.getMFInt32(3)]
            #Iterate through the four sections
            for index in range(0, 4):
                #If there is a curve activate the appropriate small walls
                if curveData[index] == 1:
                    smallData[index][0] = True
                    smallData[index][1] = True
                    curved = True
                if curveData[index] == 2:
                    smallData[index][1] = True
                    smallData[index][2] = True
                    curved = True
                if curveData[index] == 3:
                    smallData[index][2] = True
                    smallData[index][3] = True
                    curved = True
                if curveData[index] == 4:
                    smallData[index][3] = True
                    smallData[index][0] = True
                    curved = True
            
            #Add the information regarding the smaller walls
            walls.append(smallData)
        else:
            #Add nothing for the small walls
            walls.append([[False, False, False, False], [False, False, False, False], [False, False, False, False], [False, False, False, False]])
        #Get transition data
        colour = tile.getField("tileColor").getSFColor()
        colour = [round(colour[0], 1), round(colour[1], 1), round(colour[2], 1)]
        #Add whether or not this tile is a transition between two of the regions to the wall data
        walls.append(colour == [0.1, 0.1, 0.9] or colour == [0.3, 0.1, 0.6] or colour == [0.9, 0.1, 0.1])
        walls.append(curved)
        #Add the tile data to the list
        allTilesData.append([[x, z], walls])
        #Add the tile data to the correct position in the array
        allTilesGrid[zPos][xPos] = [[x, z], walls]
    
    #Return the correct arrangement
    if not grid:
        return allTilesData
    else:
        return allTilesGrid


def checkObstacles():
    '''Performs a test on each obstacle's placement and if it does not have sufficient clearance the obstacle is removed (only works on proto obstacles)'''
    #Get the data for all the obstacles
    obstacles = getObstacles()
    #If there are obstacles (otherwise there is no point in checking)
    if len(obstacles) > 0:
        #Get the tiles
        allTiles = getTiles()
        #Perform the checks on the obstacles positions
        results = obstacleCheck.performChecks(allTiles, obstacles)
        #Deactivate the appropriate obstacles
        deactivateObstacles(results)


def resetVictimsTextures():
    # Iterate for each victim
    for i in range(numberOfHumans):
        humans[i].identified = False


def relocate(robot, robotObj):
    '''Relocate robot to last visited checkpoint'''
    # Get last checkpoint visited
    relocatePosition = robotObj.lastVisitedCheckPointPosition

    # Set position of robot
    robotObj.position = [relocatePosition[0], -0.03, relocatePosition[2]]
    robotObj.rotation = [0,1,0,0]

    # Reset physics
    robot.resetPhysics()

    # Notify robot
    emitter.send(struct.pack("c", bytes("L", "utf-8")))

    # Update history with event
    robotObj.increaseScore("Lack of Progress", -5)

def robot_quit(robotObj, num, timeup):
    '''Quit robot from simulation'''
    # Quit robot if present
    if robotObj.inSimulation:
        # Remove webots node
        robotObj.wb_node.remove()
        robotObj.inSimulation = False
        # Send message to robot window to update quit button
        supervisor.wwiSendText("robotNotInSimulation"+str(num))
        # Update history event whether its manual or via exit message
        if not timeup:
            robotObj.history.enqueue("Successful Exit")
        write_log()

def add_robot():
    '''Add robot via .wbo file'''
    global robot0
    # If robot not present
    if robot0 == None:
        # Get relative path
        filePath = os.path.dirname(os.path.abspath(__file__))

        # Get webots root
        root = supervisor.getRoot()
        root_children_field = root.getField('children')
        # Get .wbo file to insert into world
        if filePath[-4:] == "game":
          root_children_field.importMFNode(12, os.path.join(filePath,'nodes/robot0.wbo'))
        else:
          root_children_field.importMFNode(12, os.path.join(filePath, '../../nodes/robot0.wbo'))
        # Update robot0 variable
        robot0 = supervisor.getFromDef("ROBOT0")
        # Update robot window to say robot is in simulation
        supervisor.wwiSendText("robotInSimulation0")


def create_log_str():
    '''Create log text for log file'''
    # Get robot events
    r0_str = robot0Obj.get_log_str()

    log_str = f"""MAX_GAME_DURATION: {str(maxTimeMinute)}:00
ROBOT_0_SCORE: {str(robot0Obj.getScore())}

ROBOT_0: {str(robot0Obj.name)}
{r0_str}"""

    return log_str

def write_log():
    '''Write log file'''
    # Get log text
    log_str = create_log_str()
    # Get relative path to logs dir
    filePath = os.path.dirname(os.path.abspath(__file__))
    if filePath[-4:] == "game":
      filePath = os.path.join(filePath, "logs/")
    else:
      filePath = os.path.join(filePath, "../../logs/")

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
        print(cl.colored(f"Couldn't write log file, no log directory: {filePath}", "red"))

def set_robot_start_pos():
    '''Set robot starting position'''

    starting_tile_node = supervisor.getFromDef("START_TILE")


    # Get the starting tile minimum node and translation
    starting_PointMin = supervisor.getFromDef("start0min")
    starting_minPos = starting_PointMin.getField("translation")

    # Get maximum node and translation
    starting_PointMax = supervisor.getFromDef("start0max")
    starting_maxPos = starting_PointMax.getField("translation")

    # Get the vector positons
    starting_minPos = starting_minPos.getSFVec3f()
    starting_maxPos = starting_maxPos.getSFVec3f()
    starting_centerPos = [(starting_maxPos[0]+starting_minPos[0])/2,starting_maxPos[1],(starting_maxPos[2]+starting_minPos[2])/2]

    startingTileObj = StartTile([starting_minPos[0], starting_minPos[2]], [starting_maxPos[0], starting_maxPos[2]], starting_tile_node, center=starting_centerPos,)

    robot0Obj.startingTile = startingTileObj
    robot0Obj.lastVisitedCheckPointPosition = startingTileObj.center
    robot0Obj.startingTile.wb_node.getField("start").setSFBool(False)
    robot0Obj.visitedCheckpoints.append(startingTileObj.center)

    robot0Obj.position = [startingTileObj.center[0], startingTileObj.center[1], startingTileObj.center[2]]
    robot0Obj.set_starting_orientation()

def clamp(n, minn, maxn):
    '''Simple clamp function that limits a number between a specified range'''
    return max(min(maxn, n), minn)
  
def add_map_multiplier():  
    score_change = robot0Obj.getScore() * robot0Obj.map_score_percent
    robot0Obj.increaseScore("Map Bonus", score_change)    

def generate_robot_proto(robot_json):
    
    # Hard coded, values from website
    component_max_counts = {
        "Wheel": 4,
        "Distance Sensor": 8,
        "Camera": 3
    }
    
    component_counts = {}
    
    proto_code = """
    PROTO custom_robot [
      field SFVec3f            translation                  0 0 0                    
      field SFRotation         rotation                     0 1 0 0                  
      field SFString           name                         "e-puck"                 
      field SFString           controller                   "" 
      field MFString           controllerArgs               ""                       
      field SFString           customData                   ""                       
      field SFBool             supervisor                   FALSE                    
      field SFBool             synchronization              TRUE                     
      field SFString{"1"}      version                      "1"                      
      field SFFloat            camera_fieldOfView           0.84                     
      field SFInt32            camera_width                 52                       
      field SFInt32            camera_height                39                       
      field SFBool             camera_antiAliasing          FALSE                    
      field SFRotation         camera_rotation              1 0 0 0                  
      field SFFloat            camera_noise                 0.0                      
      field SFFloat            camera_motionBlur            0.0                      
      field SFInt32            emitter_channel              1                        
      field SFInt32            receiver_channel             1                        
      field MFFloat            battery                      []                       
      field MFNode             turretSlot                   []                       
      field MFNode             groundSensorsSlot            []                       
      field SFBool             kinematic                    FALSE                    
      hiddenField  SFFloat            max_velocity                 6.28
    ]
    {
    %{
      local v1 = fields.version.value:find("^1") ~= nil
      local v2 = fields.version.value:find("^2") ~= nil
      local kinematic = fields.kinematic.value
    }%
    Robot {
      translation IS translation
      rotation IS rotation
      children [ 
        DEF EPUCK_PLATE Transform {
          translation 0.0002 0.037 0
          rotation 0 1 0 3.14159
          children [
            Shape {
              appearance PBRAppearance {
                baseColorMap ImageTexture {
                  url [
                    %{ if v2 then }%
                      "textures/e-puck2_plate.jpg"
                    %{ else }%
                      "textures/e-puck1_plate_base_color.jpg"
                    %{ end }%
                  ]
                }
                roughnessMap ImageTexture {
                  url [
                    %{ if v2 then }%
                      "textures/e-puck2_plate.jpg"
                    %{ else }%
                      "textures/e-puck1_plate_roughness.jpg"
                    %{ end }%
                  ]
                }
                metalnessMap ImageTexture {
                  url [
                    %{ if v2 then }%
                      "textures/e-puck2_plate.jpg"
                    %{ else }%
                      "textures/e-puck1_plate_metalness.jpg"
                    %{ end }%
                  ]
                }
                normalMap ImageTexture {
                  url [
                    %{ if v2 then }%
                      "textures/e-puck2_plate.jpg"
                    %{ else }%
                      "textures/e-puck1_plate_normal.jpg"
                    %{ end }%
                  ]
                }
                occlusionMap ImageTexture {
                  url [
                    %{ if v2 then }%
                      "textures/e-puck2_plate.jpg"
                    %{ else }%
                      "textures/e-puck1_plate_occlusion.jpg"
                    %{ end }%
                  ]
                }
              }
              geometry  Cylinder {
                height 0.00001
                radius 0.035
              }
            }
          ]
        }
          DEF EPUCK_BODY_LED LED {
            rotation 0 1 0 4.712399693899575
            children [
              Shape {
                appearance PBRAppearance {
                  baseColor 0.5 0.5 0.5
                  transparency 0
                  roughness 0.5
                  metalness 0
                  emissiveIntensity 0.2
                }
                geometry IndexedFaceSet {
                  coord Coordinate {
                    point [
                      0 0 0, 0.031522 0.025 0.015211, 0.031522 0.009 0.015211, 0.020982 0.00775 0.022017, 0.033472 0.006 0.009667, 0.029252 0.009825 0.018942, 0.016991 0.00101 0.022014, -0.022019 0.037 0.021983, -0.022018 0.025 0.021982, 0.02707 0.001064 0.00781, 0.027116 0.037 0.00781, -0.034656 0.031 0.003517, 0.026971 0.025 0.022022, 0.02707 0.01 0.022022, -0.027018 0.001 0.021978, -0.034312 0.031 0.005972, -0.034677 0.02633 0.003018, 0.035 0.037 2.9e-05, -0.031546 0.001 0.015161, -0.027018 0.037 0.021981, -0.027018 0.025 0.02198, -0.034312 0.025 0.005972, -0.034312 0.001 0.005972, -0.035 0.001 -2.7e-05, -0.035 0.025 -2.7e-05, -0.031312 0.025 0.005974, -0.031312 0.031 0.005974, -0.031656 0.031 0.00352, -0.032002 0.02633 0.003, -0.026442 0.025 -2.4e-05, -0.031546 0.037 0.015161, -0.031546 0.025 0.015161, 0.034116 0.001 0.007816, 0.034116 0.037 0.007816, 0.034116 0.025 0.007816, 0.035 0.001 2.9e-05, 0.034129 0.025 -0.007759, 0.034129 0.037 -0.007759, 0.034129 0.001 -0.007759, -0.031522 0.025 -0.015209, -0.031522 0.037 -0.015209, -0.031998 0.02633 -0.003049, -0.031651 0.031 -0.003568, -0.031302 0.031 -0.006022, -0.031302 0.025 -0.006022, -0.034302 0.001 -0.006024, -0.034302 0.025 -0.006024, -0.021982 0.025 -0.022015, -0.026983 0.025 -0.022021, -0.031522 0.001 -0.015209, -0.026983 0.001 -0.022019, -0.034672 0.02633 -0.003071, -0.034302 0.031 -0.006024, -0.026983 0.037 -0.022022, 0.031546 0.025 -0.015158, 0.031546 0.009 -0.015158, 0.027018 0.01 -0.021976, 0.026971 0.025 -0.021976, -0.034651 0.031 -0.00357, 0.027129 0.037 -0.007764, 0.02707 0.001064 -0.007764, -0.021983 0.037 -0.022015, 0.017026 0.00101 -0.021984, 0.029282 0.009825 -0.018893, 0.033487 0.006 -0.009611, 0.021018 0.00775 -0.021981, -0.022012 0.001029 0.021984, -0.021988 0.001029 -0.022017, -0.022012 0.002114 0.020705, -0.021988 0.002114 -0.020739, 0.020982 0.007866 0.021216, 0.02707 0.006116 0.009667, 0.02707 0.009941 0.018942, 0.016991 0.001125 0.021213, 0.02707 0.010116 0.021221, 0.02707 0.009116 0.015211, -0.026411 0.037 -0.020914, 0.02707 0.010116 -0.021175, 0.017026 0.001125 -0.021183, 0.02707 0.009941 -0.018893, 0.02707 0.006116 -0.009611, 0.021018 0.007866 -0.02118, 0.02707 0.009116 -0.015158, 0.026971 0.025 0.02126, 0.026971 0.025 0.015211, 0.027032 0.024944 0.007813, 0.027035 0.024936 -0.007761, 0.026971 0.025 -0.021174, 0.026971 0.025 -0.015158, -0.022018 0.025 0.020881, -0.022019 0.037 0.020881, -0.021982 0.025 -0.020913, -0.021983 0.037 -0.020914, -0.022012 0.001029 0.020691, -0.021988 0.001029 -0.020724, -0.030453 0.025 0.014633, -0.030453 0.03692 0.014633, -0.030444 0.03692 -0.01468, -0.030444 0.025 -0.01468, -0.026555 0.037 0.02095, -0.026555 0.02482 0.02095, -0.026442 0.001685 0.014633, -0.026555 0.001504 0.02095, -0.026411 0.025004 -0.020914, -0.026442 0.001774 -0.01468, -0.026411 0.001778 -0.020914, -0.028504 0.03696 0.017791, -0.029479 0.03694 0.016212, -0.028427 0.03696 -0.017797, -0.026442 0.036868 -0.01468, -0.029436 0.03694 -0.016239, -0.026442 0.036868 0.014633, -0.026442 0.025 0.014633, -0.026442 0.025 -0.01468, -0.026426 0.036934 -0.017797, -0.026498 0.036934 0.017791, 0.030629 0.037 -0.007761, 0.027122 0.037 2.3e-05, 0.031064 0.037 -0.003868
                    ]
                  }
                  coordIndex [
                    36, 38, 64, -1, 29, 41, 24, -1, 51, 24, 41, -1, 51, 41, 58, -1, 42, 58, 41, -1, 51, 58, 46, -1, 52, 46, 58, -1, 44, 46, 43, -1, 52, 43, 46, -1, 49, 40, 50, -1, 53, 50, 40, -1, 54, 55, 57, -1, 63, 57, 55, -1, 56, 57, 63, -1, 17, 35, 37, -1, 65, 62, 48, -1, 56, 65, 48, -1, 38, 37, 36, -1, 57, 56, 48, -1, 49, 45, 46, -1, 45, 23, 24, -1, 42, 43, 52, -1, 51, 46, 24, -1, 35, 38, 36, -1, 35, 36, 37, -1, 33, 34, 35, -1, 34, 32, 35, -1, 24, 21, 16, -1, 15, 26, 27, -1, 23, 22, 21, -1, 22, 18, 31, -1, 20, 13, 12, -1, 34, 33, 10, -1, 37, 36, 116, -1, 20, 3, 13, -1, 20, 6, 3, -1, 6, 20, 14, -1, 33, 35, 17, -1, 5, 12, 13, -1, 21, 26, 15, -1, 26, 21, 25, -1, 11, 21, 15, -1, 21, 11, 16, -1, 28, 11, 27, -1, 11, 28, 16, -1, 28, 24, 16, -1, 24, 28, 29, -1, 4, 32, 34, -1, 1, 2, 4, -1, 1, 4, 34, -1, 28, 26, 25, -1, 42, 41, 43, -1, 69, 68, 66, -1, 63, 79, 77, -1, 56, 77, 81, -1, 78, 62, 65, -1, 74, 72, 5, -1, 13, 3, 70, -1, 73, 70, 3, -1, 81, 77, 87, -1, 81, 87, 78, -1, 74, 70, 83, -1, 73, 83, 70, -1, 87, 91, 78, -1, 83, 73, 89, -1, 73, 93, 89, -1, 66, 93, 73, -1, 67, 62, 78, -1, 78, 91, 94, -1, 60, 35, 9, -1, 9, 32, 4, -1, 72, 83, 84, -1, 75, 84, 85, -1, 71, 85, 9, -1, 36, 64, 54, -1, 64, 55, 54, -1, 47, 48, 61, -1, 53, 61, 48, -1, 50, 48, 62, -1, 2, 12, 5, -1, 12, 2, 1, -1, 20, 7, 19, -1, 7, 20, 8, -1, 30, 14, 19, -1, 14, 30, 18, -1, 22, 45, 14, -1, 67, 66, 49, -1, 1, 84, 83, -1, 85, 84, 1, -1, 54, 88, 86, -1, 87, 88, 54, -1, 64, 38, 60, -1, 55, 64, 80, -1, 82, 79, 63, -1, 2, 75, 71, -1, 5, 72, 75, -1, 82, 88, 79, -1, 92, 91, 47, -1, 87, 57, 47, -1, 7, 8, 89, -1, 83, 89, 8, -1, 96, 31, 30, -1, 97, 40, 39, -1, 98, 39, 46, -1, 95, 25, 21, -1, 76, 53, 40, -1, 61, 53, 76, -1, 99, 19, 7, -1, 107, 96, 30, -1, 99, 90, 89, -1, 113, 98, 44, -1, 105, 103, 113, -1, 102, 100, 89, -1, 103, 91, 92, -1, 98, 113, 109, -1, 91, 103, 105, -1, 113, 29, 104, -1, 101, 112, 100, -1, 29, 101, 104, -1, 118, 59, 117, -1, 39, 49, 46, -1, 46, 45, 24, -1, 58, 42, 52, -1, 11, 15, 27, -1, 24, 23, 21, -1, 21, 22, 31, -1, 28, 27, 26, -1, 25, 29, 28, -1, 44, 43, 41, -1, 41, 29, 44, -1, 69, 104, 101, -1, 67, 69, 66, -1, 56, 63, 77, -1, 65, 56, 81, -1, 81, 78, 65, -1, 13, 74, 5, -1, 74, 13, 70, -1, 6, 73, 3, -1, 6, 66, 73, -1, 94, 67, 78, -1, 32, 9, 35, -1, 60, 38, 35, -1, 71, 9, 4, -1, 84, 75, 72, -1, 72, 74, 83, -1, 71, 75, 85, -1, 49, 14, 45, -1, 18, 22, 14, -1, 23, 45, 22, -1, 14, 49, 66, -1, 50, 67, 49, -1, 12, 1, 83, -1, 34, 85, 1, -1, 36, 54, 86, -1, 57, 87, 54, -1, 80, 64, 60, -1, 82, 55, 80, -1, 55, 82, 63, -1, 4, 2, 71, -1, 2, 5, 75, -1, 80, 60, 86, -1, 87, 77, 79, -1, 82, 80, 86, -1, 87, 79, 88, -1, 86, 88, 82, -1, 61, 92, 47, -1, 91, 87, 47, -1, 90, 7, 89, -1, 12, 83, 8, -1, 95, 31, 96, -1, 98, 97, 39, -1, 44, 98, 46, -1, 31, 95, 21, -1, 108, 76, 40, -1, 92, 61, 76, -1, 90, 99, 7, -1, 19, 99, 30, -1, 100, 99, 89, -1, 111, 107, 106, -1, 93, 102, 89, -1, 76, 103, 92, -1, 109, 114, 108, -1, 29, 112, 101, -1, 94, 91, 105, -1, 10, 33, 17, -1, 118, 116, 59, -1, 103, 114, 113, -1, 112, 115, 100, -1, 95, 96, 111, -1, 25, 95, 112, -1, 37, 116, 118, -1, 17, 118, 117, -1, 86, 60, 10, -1, 59, 86, 117, -1, 34, 10, 85, -1, 60, 9, 85, -1, 30, 99, 106, -1, 106, 107, 30, -1, 29, 113, 44, -1, 104, 105, 113, -1, 97, 98, 109, -1, 102, 101, 100, -1, 102, 68, 101, -1, 69, 105, 104, -1, 101, 68, 69, -1, 40, 97, 110, -1, 110, 108, 40, -1, 106, 99, 115, -1, 115, 111, 106, -1, 96, 107, 111, -1, 110, 97, 109, -1, 76, 108, 114, -1, 110, 109, 108, -1, 109, 113, 114, -1, 103, 76, 114, -1, 99, 100, 115, -1, 112, 111, 115, -1, 112, 95, 111, -1, 29, 25, 112, -1, 17, 37, 118, -1, 10, 17, 117, -1, 117, 86, 10, -1, 36, 86, 116, -1, 59, 116, 86, -1, 10, 60, 85, -1
                  ]
                  creaseAngle 0.5
                }
              }
            ]
            name "led8"
            color [
              0 1 0
            ]
          }
          DEF EPUCK_FRONT_LED LED {
            translation 0.0125 0.0285 -0.031
            children [
              Shape {
                appearance PBRAppearance { # Don't use USE/DEF here
                  metalness 0.5
                  baseColor 0.8 0.8 0.8
                  transparency 0.3
                  roughness 0.2
                }
                geometry Sphere {
                  radius 0.0025
                }
                castShadows FALSE
              }
            ]
            name "led9"
            color [
              1 0.3 0
            ]
          }
          DEF EPUCK_SMALL_LOGO Transform {
            translation 0 0.031 0.035
            rotation 0 1 0 3.14159
            children [
              Shape {
                appearance PBRAppearance {
                  roughness 0.4
                  metalness 0
                  baseColorMap ImageTexture {
                    url [
                      "textures/rescue.png"
                    ]
                  }
                }
                geometry IndexedFaceSet {
                  coord Coordinate {
                    point [
                      0.005 -0.005 0 -0.005 -0.005 0 -0.005 0.005 0 0.005 0.005 0
                    ]
                  }
                  texCoord TextureCoordinate {
                    point [
                      0 0 1 0 1 1 0 1
                    ]
                  }
                  coordIndex [
                    0, 1, 2, 3
                  ]
                  texCoordIndex [
                    0, 1, 2, 3
                  ]
                }
                castShadows FALSE
              }
            ]
          }
          DEF EPUCK_RECEIVER Receiver {
            channel IS receiver_channel
          }
          DEF EPUCK_EMITTER Emitter {
            channel IS emitter_channel
          }

        Solid {
          name "ballCaster1"
          contactMaterial "NO_FRIC"
          translation 0 .001 -0.034
          boundingObject Transform {
            children [
              Sphere {
                radius .001
              }
            ]
          }
          physics Physics {
            density -1
            mass 0.1
          }
        }
        Solid {
          name "ballCaster2"
	  	    contactMaterial "NO_FRIC"
          translation 0 .001 0.034

          boundingObject Transform {
            children [
              Sphere {
                radius .001
              }
            ]
          }
          physics Physics {
            density -1
            mass 0.1
          }
        }

          

          
        """
    
    closeBracket = "\n\t\t}\n"

    budget = 3000
    cost = 0
    costs = {
      'Gyro': 100,
      'GPS': 250,
      'Camera': 500,
      'Colour sensor': 100,
      'Accelerometer': 100,
      'Lidar': 500,
      'Wheel': 300,
      'Distance Sensor': 50
    }

    genERR = False
    
    for component in robot_json:
        
        # Add component to component_counts
        if robot_json[component]["name"] not in component_counts:
            component_counts[robot_json[component]["name"]] = 1
        else:
            # Increase component count
            component_counts[robot_json[component]["name"]] += 1
        
        component_count = component_counts[robot_json[component]["name"]]
        # If the robot can have more than one of this component
        if robot_json[component]["name"] in component_max_counts:
            component_max_count = component_max_counts[robot_json[component]["name"]]
            # If there are more components in json than there should be, continue
            if component_count > component_max_count:
              print(cl.colored(f"[SKIP] The number of {robot_json[component]['name']} is limited to {component_max_count}.", "yellow"))
              continue
        else:
            # If there should only be one component
            # Skip if count is > 1
            if component_count > 1:
              print(cl.colored(f"[SKIP] The number of {robot_json[component]['name']} is limited to only one.", "yellow"))
              continue

        # Cost calculation
        try:
          cost += costs[robot_json[component]["name"]]
          if cost > budget:
            print(cl.colored("ERROR! The necessary costs exceed the budget.", "red"))
            print(cl.colored(f"Budget: {budget}  Cost: {cost}", "red"))
            genERR = True
            break
        except KeyError as e:
          print(cl.colored(f"[SKIP] {e.args[0]} is no longer supported in this version.", "orange"))
          continue

        if robot_json[component].get("customName") is None or robot_json[component].get("customName") == "":
          print(cl.colored(f"ERROR! No tag name has been specified for {robot_json[component].get('name')}. Please specify a suitable name in the robot generator.", "red"))
          genERR = True
          break
        
        if robot_json[component].get("name") == "Wheel":
          print(cl.colored(f"Adding motor... {robot_json[component].get('dictName')} ({robot_json[component].get('customName')} motor)", "blue"))
          print(cl.colored(f"Adding sensor... {robot_json[component].get('dictName')} ({robot_json[component].get('customName')} sensor)", "blue"))
        else:
          print(cl.colored(f"Adding sensor... {robot_json[component].get('dictName')} ({robot_json[component].get('customName')})", "blue"))


                      
        # Hard coded, so if ranges change in the website, 
        # I need to change them here too :(
        if(robot_json[component]["name"] == "Wheel"):
            x = clamp(robot_json[component]['x'], -370, 370) / 10000
            y = clamp(robot_json[component]['y'],-100,370) / 10000
            z = clamp(robot_json[component]['z'],-260,260) / 10000
        else:    
            x = clamp(robot_json[component]['x'],-370,370) / 10000
            y = clamp(robot_json[component]['y'],-100,370) / 10000
            z = clamp(robot_json[component]['z'],-370,370) / 10000
        
        y += 18.5/1000
        
        if(robot_json[component]["name"] == "Wheel"):
            proto_code += f"""
            HingeJoint {{
            jointParameters HingeJointParameters {{
                axis {robot_json[component]["rz"]} {robot_json[component]["ry"]} {robot_json[component]["rx"]}
                anchor {x} {y} {z}
            }}
            device [
                RotationalMotor {{
                name "{robot_json[component]["customName"]} motor"
                consumptionFactor -0.001 # small trick to encourage the movement (calibrated for the rat's life contest)
                maxVelocity IS max_velocity
                }}
                PositionSensor {{
                name "{robot_json[component]["customName"]} sensor"
                resolution 0.00628  # (2 * pi) / 1000
                }}
            ]
            endPoint Solid {{
                translation {x} {y} {z}
                rotation 1 0 0 0
                children [
                DEF EPUCK_WHEEL Transform {{
                    rotation {robot_json[component]["rx"]} {robot_json[component]["ry"]} {robot_json[component]["rz"]} {robot_json[component]["a"]}
                    children [
                    Shape {{
                        appearance PBRAppearance {{
                          baseColor 1 0.7 0
                          transparency 0
                          roughness 0.5
                          metalness 0
                        }}
                        geometry Cylinder {{
                        height 0.003
                        radius 0.02
                        subdivision 24
                        }}
                        castShadows FALSE
                    }}
                    Shape {{
                        appearance PBRAppearance {{
                        metalness 0
                        roughness 0.4
                        %{{ if v1 then }}%
                        baseColor 0.117647 0.815686 0.65098
                        %{{ else }}%
                        baseColor 0 0 0
                        %{{ end }}%
                        }}
                        geometry Cylinder {{
                        height 0.0015
                        radius 0.0201
                        subdivision 24
                        top FALSE
                        bottom FALSE
                        }}
                        castShadows FALSE
                    }}
                    Transform {{
                        translation 0 0.0035 0
                        children [
                        Shape {{
                            appearance DEF EPUCK_TRANSPARENT_APPEARANCE PBRAppearance {{
                              baseColor 0.5 0.5 0.5
                              transparency 0
                              roughness 0.5
                              metalness 0
                            }}
                            geometry Cylinder {{
                            height 0.004
                            radius 0.005
                            }}
                            castShadows FALSE
                        }}
                        ]
                    }}
                    Transform {{
                        children [
                        Shape {{
                            appearance PBRAppearance {{
                            }}
                            geometry Cylinder {{
                            height 0.013
                            radius 0.003
                            subdivision 6
                            }}
                            castShadows FALSE
                        }}
                        ]
                    }}
                    Transform {{
                        translation 0 0.0065 0
                        children [
                        Shape {{
                            appearance PBRAppearance {{
                            baseColor 1 0.647059 0
                            metalness 0
                            roughness 0.6
                            }}
                            geometry Cylinder {{
                            height 0.0001
                            radius 0.002
                            }}
                            castShadows FALSE
                        }}
                        ]
                    }}
                    ]
                }}
                ]
                name "{robot_json[component]["customName"]}"
                boundingObject DEF EPUCK_WHEEL_BOUNDING_OBJECT Transform {{
                rotation {robot_json[component]["rx"]} {robot_json[component]["ry"]} {robot_json[component]["rz"]} {robot_json[component]["a"]}
                children [
                    Cylinder {{
                    height 0.005
                    radius 0.02
                    subdivision 24
                    }}
                ]
                }}
                %{{ if kinematic == false then }}%
                physics DEF EPUCK_WHEEL_PHYSICS Physics {{
                    density -1
                    mass 0.8
                }}
                %{{ end }}%
            }}
            }}
            """
        
        if(robot_json[component]["name"] == "Camera"):
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["ry"]} {robot_json[component]["rz"]} {robot_json[component]["a"]}
            children [
                Camera {{
                name "{robot_json[component]["customName"]}"
                rotation 0 1 0 -1.57
                children [
                    Transform {{
                    rotation 0 0.707107 0.707107 3.14159
                    children [
                        Transform {{
                        rotation IS camera_rotation
                        children [
                            Shape {{
                              appearance PBRAppearance {{
                                  baseColor 0 0 0
                                  roughness 0.4
                                  metalness 0
                              }}
                              geometry IndexedFaceSet {{
                                  coord Coordinate {{
                                  point [
                                      -0.003 -0.000175564 0.003 -0.003 -0.00247555 -0.003 -0.003 -0.00247555 -4.65661e-09 -0.003 -0.00247555 0.003 -0.003 -2.55639e-05 0.0035 -0.003 -2.55639e-05 -0.003 -0.003 0.000427256 0.00574979 -0.003 -0.000175564 0.0035 -0.003 0.000557156 0.0056748 -0.003 0.00207465 0.00739718 -0.003 0.00214964 0.00726728 -0.003 0.00432444 0.008 -0.003 0.00432444 0.00785 -0.003 0.00757444 0.008 -0.003 0.00757444 0.0095 -0.003 0.0115744 0.0095 -0.003 0.0115744 0.008 -0.003 0.0128244 0.008 -0.003 0.0128244 0.00785 0.003 -2.55639e-05 -0.003 0.003 -0.000175564 0.0035 0.003 -0.000175564 0.003 0.003 -0.00247555 0.003 0.003 -0.00247555 -4.65661e-09 0.003 -0.00247555 -0.003 0.003 -2.55639e-05 0.0035 0.003 0.000427256 0.00574979 0.003 0.000557156 0.0056748 0.003 0.00207465 0.00739718 0.003 0.00214964 0.00726728 0.003 0.00432444 0.00785 0.003 0.00432444 0.008 0.003 0.0115744 0.0095 0.003 0.00757444 0.0095 0.003 0.0115744 0.008 0.003 0.00757444 0.008 0.003 0.0128244 0.00785 0.003 0.0128244 0.008 0 -0.00247555 -0.003 -0.00149971 -0.00247555 -0.0025982 0.00149971 -0.00247555 -0.0025982 0.00259801 -0.00247555 -0.00150004 -0.00259801 -0.00247555 -0.00150004 0.00149971 -0.00247555 0.00259821 0.00259801 -0.00247555 0.00150005 0 -0.00247555 0.003 -0.00149971 -0.00247555 0.00259821 -0.00259801 -0.00247555 0.00150005 0.00212127 -0.00377555 0.00212128 0 -0.00377555 0.003 -0.00212127 -0.00377555 0.00212128 -0.0015 -0.00377555 0.002 -0.002 -0.00377555 0.0015 -0.003 -0.00377555 -4.65661e-09 0.0015 -0.00377555 0.002 0.002 -0.00377555 0.0015 0.003 -0.00377555 -4.65661e-09 -0.002 -0.00377555 -0.0015 0.002 -0.00377555 -0.0015 -0.00212127 -0.00377555 -0.0021213 0.0015 -0.00377555 -0.002 -0.0015 -0.00377555 -0.002 0.00212127 -0.00377555 -0.0021213 0 -0.00377555 -0.003 -0.00256063 -0.00377555 0.00106064 -0.00106063 -0.00377555 0.00256064 0.00106063 -0.00377555 0.00256064 0.00256063 -0.00377555 0.00106064 0.00256063 -0.00377555 -0.00106063 0.00106063 -0.00377555 -0.0025606 -0.00106063 -0.00377555 -0.0025606 -0.00256063 -0.00377555 -0.00106063 0.0015 -0.00417556 -0.002 0.002 -0.00417556 -0.0015 -0.0015 -0.00417556 -0.002 -0.002 -0.00417556 -0.0015 0.002 -0.00417556 0.0015 0 -0.00417556 0.000245125 0.00021198 -0.00417556 0.000122716 0.00021198 -0.00417556 -0.000122714 0 -0.00417556 -0.000245124 -0.00021198 -0.00417556 -0.000122714 -0.00021198 -0.00417556 0.000122716 -0.002 -0.00417556 0.0015 0.0015 -0.00417556 0.002 -0.0015 -0.00417556 0.002
                                  ]
                                  }}
                                  coordIndex [
                                  33, 14, 35, -1, 13, 35, 14, -1, 15, 32, 16, -1, 34, 16, 32, -1, 14, 33, 15, -1, 32, 15, 33, -1, 72, 74, 60, -1, 61, 60, 74, -1, 74, 75, 61, -1, 57, 61, 75, -1, 75, 83, 57, -1, 52, 57, 83, -1, 83, 85, 52, -1, 51, 52, 85, -1, 85, 84, 51, -1, 54, 51, 84, -1, 84, 76, 54, -1, 55, 54, 76, -1, 76, 73, 55, -1, 58, 55, 73, -1, 73, 72, 58, -1, 60, 58, 72, -1, 72, 73, 74, -1, 75, 74, 73, -1, 76, 77, 78, -1, 76, 78, 79, -1, 79, 80, 75, -1, 79, 75, 73, -1, 73, 76, 79, -1, 75, 80, 81, -1, 75, 81, 82, -1, 82, 77, 76, -1, 82, 76, 83, -1, 83, 75, 82, -1, 76, 84, 83, -1, 85, 83, 84, -1, 56, 68, 23, -1, 41, 23, 68, -1, 68, 62, 41, -1, 40, 41, 62, -1, 62, 69, 40, -1, 40, 69, 63, -1, 38, 40, 63, -1, 63, 70, 38, -1, 39, 38, 70, -1, 70, 59, 39, -1, 42, 39, 59, -1, 59, 71, 42, -1, 42, 71, 53, -1, 2, 42, 53, -1, 53, 64, 2, -1, 47, 2, 64, -1, 64, 50, 47, -1, 46, 47, 50, -1, 50, 65, 46, -1, 46, 65, 49, -1, 45, 46, 49, -1, 49, 66, 45, -1, 43, 45, 66, -1, 66, 48, 43, -1, 44, 43, 48, -1, 48, 67, 44, -1, 44, 67, 56, -1, 23, 44, 56, -1, 48, 49, 50, -1, 51, 48, 50, -1, 52, 51, 50, -1, 50, 53, 52, -1, 48, 51, 54, -1, 48, 54, 55, -1, 56, 48, 55, -1, 57, 52, 53, -1, 55, 58, 56, -1, 59, 60, 61, -1, 59, 61, 57, -1, 53, 59, 57, -1, 60, 59, 62, -1, 58, 60, 62, -1, 62, 56, 58, -1, 59, 63, 62, -1, 0, 45, 22, -1, 21, 0, 22, -1, 45, 0, 3, -1, 38, 39, 1, -1, 40, 38, 24, -1, 41, 40, 24, -1, 24, 23, 41, -1, 1, 39, 42, -1, 2, 1, 42, -1, 22, 43, 44, -1, 23, 22, 44, -1, 45, 43, 22, -1, 46, 45, 3, -1, 47, 46, 3, -1, 3, 2, 47, -1, 20, 26, 7, -1, 6, 7, 26, -1, 26, 28, 6, -1, 9, 6, 28, -1, 28, 31, 9, -1, 11, 9, 31, -1, 31, 35, 11, -1, 13, 11, 35, -1, 34, 37, 16, -1, 17, 16, 37, -1, 36, 18, 37, -1, 17, 37, 18, -1, 36, 30, 18, -1, 12, 18, 30, -1, 4, 8, 25, -1, 27, 25, 8, -1, 8, 10, 27, -1, 29, 27, 10, -1, 10, 12, 29, -1, 30, 29, 12, -1, 25, 19, 4, -1, 5, 4, 19, -1, 24, 38, 19, -1, 19, 38, 1, -1, 5, 19, 1, -1, 20, 7, 21, -1, 0, 21, 7, -1, 19, 20, 21, -1, 19, 21, 22, -1, 19, 22, 23, -1, 24, 19, 23, -1, 20, 19, 25, -1, 26, 20, 25, -1, 25, 27, 26, -1, 28, 26, 27, -1, 27, 29, 28, -1, 28, 29, 30, -1, 31, 28, 30, -1, 32, 33, 34, -1, 34, 33, 35, -1, 36, 34, 35, -1, 36, 35, 31, -1, 30, 36, 31, -1, 37, 34, 36, -1, 0, 1, 2, -1, 3, 0, 2, -1, 0, 4, 5, -1, 1, 0, 5, -1, 4, 0, 6, -1, 6, 0, 7, -1, 8, 4, 6, -1, 6, 9, 8, -1, 10, 8, 9, -1, 9, 11, 10, -1, 12, 10, 11, -1, 11, 13, 12, -1, 14, 15, 13, -1, 13, 15, 16, -1, 12, 13, 16, -1, 12, 16, 17, -1, 18, 12, 17, -1
                                  ]
                                  creaseAngle 0.785398
                              }}
                              castShadows FALSE
                            }}
                        ]
                        }}
                    ]
                    }}
                ]
                fieldOfView IS camera_fieldOfView
                width IS camera_width
                height IS camera_height
                near 0.0055
                antiAliasing IS camera_antiAliasing
                motionBlur IS camera_motionBlur
                noise IS camera_noise
                zoom Zoom {{
                }}
                }}
            ]
            }}"""
        
        if robot_json[component]["name"] in ["Gyro","GPS"]:
            proto_code += f"""
            {robot_json[component]["name"]} {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["ry"]} {robot_json[component]["rz"]} {robot_json[component]["a"]}
            name "{robot_json[component]["customName"]}"
            }}
            """
        
        if(robot_json[component]["name"] == "Colour sensor"):
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["ry"]} {robot_json[component]["rz"]} {robot_json[component]["a"]}
            children [
                Camera {{
                name "{robot_json[component]["customName"]}"
                rotation 0 1 0 -1.57
                width 1
                height 1
                }}
                SpotLight {{
                attenuation 0 0 12.56
                intensity   0.01
                direction   1 0 0
                cutOffAngle 0.3
                }}
            ]
            }}
            """
        
        if robot_json[component]["name"] == "Distance Sensor":
            proto_code += f"""
            DistanceSensor {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["ry"]} {robot_json[component]["rz"]} {robot_json[component]["a"]}
            name "{robot_json[component]["customName"]}"
            lookupTable [
                0 0 0
                0.8 0.8 0
            ]
            type "infra-red"
            }}
            """
        
        if(robot_json[component]["name"]== "Accelerometer"):
            proto_code += f"""
            Accelerometer {{
            lookupTable [ -100 -100 0.003 100 100 0.003 ]
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["ry"]} {robot_json[component]["rz"]} {robot_json[component]["a"]}
            }}"""
        
        if(robot_json[component]["name"]== "Lidar"):
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["ry"]} {robot_json[component]["rz"]} {robot_json[component]["a"]}
            children [
                Lidar {{
                rotation 0 1 0 -1.57
                fieldOfView 6.2832
                }}
            ]
            }}"""
      
      
    
    proto_code += """DEF EPUCK_RING SolidPipe {
      translation 0 0.0393 0
      height 0.007
      radius 0.0356
      thickness 0.004
      subdivision 64
      appearance USE EPUCK_TRANSPARENT_APPEARANCE
      enableBoundingObject FALSE
    }"""
    proto_code += "\n\t]"
    proto_code += """
        name IS name
      %{ if v2 then }%
        model "GCtronic e-puck2"
      %{ else }%
        model "GCtronic e-puck"
      %{ end }%
      description "Educational robot designed at EPFL"
      boundingObject Group {
        children [
          Transform {
            translation 0 0.025 0
            children [
              Cylinder {
                height 0.045
                radius 0.037
                subdivision 24
              }
            ]
          }
        ]
      }
      %{ if kinematic == false then }%
        physics Physics {
          density -1
          %{ if v2 then }%
            mass 0.13
          %{ else }%
            mass 0.15
          %{ end }%
          centerOfMass [0 0.015 0]
          inertiaMatrix [8.74869e-05 9.78585e-05 8.64333e-05, 0 0 0]
        }
      %{ end }%
      controller IS controller
      controllerArgs IS controllerArgs
      customData IS customData
      supervisor IS supervisor
      synchronization IS synchronization
      battery IS battery
      cpuConsumption 1.11 # 100% to 0% in 90[s] (calibrated for the rat's life contest)
      window IS window
    """
    proto_code += "\n}"
    proto_code += closeBracket

    if not genERR:
      print(cl.colored("Your custom robot has been successfully generated!", "green"))
      print(cl.colored(f"Budget: {budget}  Cost: {cost}", "green"))
      

      path = os.path.dirname(os.path.abspath(__file__))

      if path[-4:] == "game":
        path = os.path.join(path, "protos")
      else:
        path = os.path.join(path, "../../protos")

      path = os.path.join(path, "custom_robot.proto")

      with open(path, 'w') as robot_file:
          robot_file.write(proto_code)
      supervisor.wwiSendText("loaded1")
    else:
      print(cl.colored("Your custom robot generation has been cancelled.", "red"))


def setViewPoint(robotObj, viewpoint_node, dir):
    if dir == "top":
      vp = [
        robotObj.position[0],
        robotObj.position[1] + 0.8,
        robotObj.position[2] - 0.8
      ]
      vo = [0.0, 0.9235793898666079, 0.3834072386035822, 3.141592653589793]
    elif dir == "right":
      vp = [
        robotObj.position[0] + 0.8,
        robotObj.position[1] + 0.8,
        robotObj.position[2]
      ]
      vo = [-0.357996176885067, 0.8623673664230065, 0.357996176885067, 1.7183320854248436]
    elif dir == "bottom":
      vp = [
        robotObj.position[0],
        robotObj.position[1] + 0.8,
        robotObj.position[2] + 0.8
      ]
      vo = [1.0, 0.0, 0.0, 5.4962200048483485]
    elif dir == "left":
      vp = [
        robotObj.position[0] - 0.8,
        robotObj.position[1] + 0.8,
        robotObj.position[2]
      ]
      vo = [0.357996176885067, 0.8623673664230065, 0.357996176885067, 4.564853221754743]
    viewpoint_node.getField('position').setSFVec3f(vp)
    viewpoint_node.getField('orientation').setSFRotation(vo)

def wait(sec):
  first = supervisor.getTime()
  while 1:
    supervisor.step(32)
    if supervisor.getTime() - first > sec:
      break
  return
    

def process_robot_json(json_data):
    '''Process json file to generate robot file'''
    robot_json = json.loads(json_data)
    generate_robot_proto(robot_json)

# -------------------------------
# CODED LOADED BEFORE GAME STARTS

if __name__ == '__main__':
    # Send message to robot window to perform setup
    supervisor.wwiSendText("startup")

    if supervisor.getCustomData() != '':
        customData = supervisor.getCustomData().split(',')
        maxTime = int(customData[0])
        supervisor.wwiSendText("update," + str(0) + "," + str(0) + "," + str(maxTime))
    
    # Load settings
    # configData
    # [0]: Keep controller/robot files
    # [1]: Disable auto LoP
    # [2]: Recording
    # [3]: Automatic camera

    configFilePath = os.path.dirname(os.path.abspath(__file__))
    if configFilePath[-4:] == "game":
      configFilePath = os.path.join(configFilePath, "controllers/MainSupervisor/config.txt")
    else:
      configFilePath = os.path.join(configFilePath, "config.txt")
    f = open(configFilePath, 'r')
    configData = f.read().split(',')
    f.close()
    supervisor.wwiSendText("config," + ','.join(configData))
    configData = list(map((lambda x: int(x)), configData))
    
    try:
      supervisor.wwiSendText(f"version,{version}")
      # Check updates
      url = "https://gitlab.com/api/v4/projects/22054848/releases"
      response = req.get(url)
      releases = response.json()
      releases = list(filter(lambda release: release['tag_name'].startswith(f"v{stream}"), releases))
      if len(releases) > 0:
        if releases[0]['tag_name'].replace('_', ' ') == f'v{version}':
          supervisor.wwiSendText(f"latest,{version}")
        elif any([r['tag_name'].replace('_', ' ') == f'v{version}' for r in releases]):
          supervisor.wwiSendText(f"outdated,{version},{releases[0]['tag_name'].replace('v','').replace('_', ' ')}")
        else:
          supervisor.wwiSendText(f"unreleased,{version}")
      else:
        supervisor.wwiSendText(f"version,{version}")
    except:
      supervisor.wwiSendText(f"version,{version}")

    uploader = threading.Thread(target=ControllerUploader.start)
    uploader.setDaemon(True)
    uploader.start()

    # Empty list to contain checkpoints
    checkpoints = []
    # Empty list to contain swamps
    swamps = []
    # Global empty list to contain human objects
    humans = []
    # Global empty list to contain hazard objects
    hazards = []

    # Get number of humans in map
    numberOfHumans = supervisor.getFromDef('HUMANGROUP').getField("children").getCount()

    # Get number of humans in map
    numberOfHazards = supervisor.getFromDef('HAZARDGROUP').getField("children").getCount()

    # Get number of checkpoints in map
    numberOfCheckpoints = supervisor.getFromDef('CHECKPOINTBOUNDS').getField('children').getCount()

    # Get number of swamps in map
    numberOfSwamps = supervisor.getFromDef('SWAMPBOUNDS').getField('children').getCount()
    
    # Get number of hazards in map
    numberOfHazards = supervisor.getFromDef('HAZARDGROUP').getField('children').getCount()

    #get swamps in world
    getSwamps(swamps, numberOfSwamps)

    #get checkpoints in world
    getCheckpoints(checkpoints, numberOfCheckpoints)

    #get humans in world
    getHumans(humans, numberOfHumans)
    
    #get hazards in world
    getHazards(hazards, numberOfHazards)

    #NOT WORKING DUE TO NEW TILES - do not use yet
    checkObstacles()

    #get hazards in world
    getHazards(humans, numberOfHazards)

    # Not currently running the match
    currentlyRunning = False
    previousRunState = False

    # The game has not yet started
    gameStarted = False

    # The simulation is running
    simulationRunning = True
    finished = False
    last = False

    # Reset the controllers
    resetControllerFile()

    # Reset the robot proto
    resetRobotProto()

    # Get Viewppoint Node
    viewpoint_node = supervisor.getFromDef("Viewpoint")

    if len(customData) > 1:
      nowSide = customData[1]
    else:
      nowSide = "bottom"

    # How long the game has been running for
    timeElapsed = 0
    lastTime = -1

    # For checking the first update with the game running
    first = True

    receiver = supervisor.getDevice('receiver')
    receiver.enable(32)
    
    emitter = supervisor.getDevice('emitter')

    # Init robot as object to hold their info
    robot0Obj = Robot()

    lastSentScore = 0
    lastSentTime = 0

    robotInitialized = False

    #Calculate the solution arrays for the map layout
    MapAnswer = mapAnswer.MapAnswer(supervisor)
    mapSolution = MapAnswer.generateAnswer(False)
    
    # -------------------------------

    # Until the match ends (also while paused)
    while simulationRunning or last == True:
        
        if last == True:
            last = -1
            finished = True
            if configData[2]:
                supervisor.setLabel(0, "Score: " + str(round(robot0Obj.getScore(),2)), 0.15, 0.3,0.3, 0xe74c3c, 0)
                supervisor.setLabel(1, "Game time: " + str(int(int(timeElapsed)/60)).zfill(2) + ":"+ str(int(int(timeElapsed)%60)).zfill(2), 0.15, 0.45,0.3, 0xe74c3c, 0)
                wait(5)
                supervisor.movieStopRecording()
        
        r0 = False
        r0s = False

        # The first frame of the game running only
        if first and currentlyRunning:
            if configData[2]:
              path = os.path.dirname(os.path.abspath(__file__))
              if path[-4:] == "game":
                path = os.path.join(path, "../recording.mp4")
              else:
                path = os.path.join(path, "../../../recording.mp4")
              supervisor.movieStartRecording(
                  path, width=1280, height=720, quality=70,
                  codec=0, acceleration=1, caption=False,
              )
              supervisor.setLabel(0, f'Platform Version: {version}' , 0, 0,0.05, 0xdff9fb, 0)
              wait(0.5)
              supervisor.setLabel(4, "3", 0.4, 0,0.7, 0xe74c3c, 0)
              wait(1)
              supervisor.setLabel(4, "2", 0.4, 0,0.7, 0xe74c3c, 0)
              wait(1)
              supervisor.setLabel(4, "1", 0.4, 0,0.7, 0xe74c3c, 0)
              wait(1)
              supervisor.setLabel(4, "START", 0.2, 0,0.7, 0xe74c3c, 0)
              wait(1)
              supervisor.setLabel(0, "Score: " + str(0), 0.15, 0,0.15, 0x4cd137, 0)
              supervisor.setLabel(1, "Clock: " + str(int(int(maxTime)/60)).zfill(2) + ":"+ str(int(int(maxTime)%60)).zfill(2), 0.4, 0,0.15, 0x4cd137, 0)
            # Get the robot nodes by their DEF names
            robot0 = supervisor.getFromDef("ROBOT0")
            # Add robot into world
            add_robot()
            # Init robot as object to hold their info
            robot0Obj = Robot(robot0)
            # Set robots starting position in world
            set_robot_start_pos()
            robot0Obj.inSimulation = True
            robot0Obj.setMaxVelocity(DEFAULT_MAX_VELOCITY)
            robotInitialized = True

            # Reset physics
            robot0.resetPhysics()

            
            if configData[3] and viewpoint_node:
                viewpoint_node.getField('follow').setSFString("e-puck 0")
                setViewPoint(robot0Obj, viewpoint_node, nowSide)


            # Restart controller code
            # robot0.restartController()
            first = False
            if configData[2]:
              supervisor.setLabel(4, "", 0.2, 0,0.4, 0xe74c3c, 0)
            #robot0Obj.increaseScore("Debug", 100)

            lastTime = supervisor.getTime()

        if robot0Obj.inSimulation:
            if configData[3] and viewpoint_node:
              nearVictims = [h for h in humans if h.checkPosition(robot0Obj.position, 0.20) and h.onSameSide(robot0Obj.position)]
              if len(nearVictims) > 0:
                if(len(nearVictims) > 1):
                  nearVictims.sort(key=lambda v: v.getDistance(robot0Obj.position))
                side = nearVictims[0].getSide()
                if side != nowSide:
                  setViewPoint(robot0Obj, viewpoint_node, side)
                  nowSide = side
            # Test if the robots are in checkpoints
            checkpoint = [c for c in checkpoints if c.checkPosition(robot0Obj.position)]
            if len(checkpoint):
              robot0Obj.lastVisitedCheckPointPosition = checkpoint[0].center
              alreadyVisited = False

              # Dont update if checkpoint is already visited
              if not any([c == checkpoint[0].center for c in robot0Obj.visitedCheckpoints]):
                  # Update robot's points and history
                  robot0Obj.visitedCheckpoints.append(checkpoint[0].center)
                  grid = coord2grid(checkpoint[0].center)
                  roomNum = supervisor.getFromDef("WALLTILES").getField("children").getMFNode(grid).getField("room").getSFInt32() - 1
                  robot0Obj.increaseScore("Found checkpoint", 10, roomMult[roomNum])

            # Check if the robots are in swamps
            inSwamp = any([s.checkPosition(robot0Obj.position) for s in swamps])
            # Check if robot is in swamp
            if robot0Obj.inSwamp != inSwamp:
                robot0Obj.inSwamp = inSwamp
                if robot0Obj.inSwamp:
                    # Cap the robot's velocity to 2
                    robot0Obj.setMaxVelocity(2)
                    # Reset physics
                    robot0.resetPhysics()
                    # Update history
                    robot0Obj.history.enqueue("Entered swamp")
                else:
                    # If not in swamp, reset max velocity to default
                    robot0Obj.setMaxVelocity(DEFAULT_MAX_VELOCITY)
                    # Reset physics
                    robot0.resetPhysics()
                    # Update history
                    robot0Obj.history.enqueue("Exited swamp")

            # If receiver has got a message
            if receiver.getQueueLength() > 0:
                # Get receiver data
                receivedData = receiver.getData()
                # Get length of bytes
                rDataLen = len(receivedData)
                try:
                    if rDataLen == 1:
                      tup = struct.unpack('c', receivedData)
                      robot0Obj.message = [tup[0].decode("utf-8")]
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
                        robot0Obj.message = [estimated_victim_position, victimType]
                    else:
                        """
                         For map data, the format sent should be:
                        
                         receivedData = b'_____ _________________'
                                            ^          ^
                                          shape     map data
                        """
                        # Shape data should be two bytes (2 integers)
                        shape_bytes = receivedData[:8] # Get shape of matrix
                        data_bytes = receivedData[8::] # Get data of matrix

                        # Get shape data
                        shape = struct.unpack('2i',shape_bytes)
                        # Size of flattened 2d array
                        shape_size = shape[0] * shape[1]
                        # Get map data
                        map_data = data_bytes.decode('utf-8').split(',')
                        # Reshape data using the shape data given
                        reshaped_data = np.array(map_data).reshape(shape)
                        
                        robot0Obj.map_data = reshaped_data
                except Exception as e:
                    print(cl.colored("Incorrect data format sent", "red"))
                    print(cl.colored(e, "red"))

                receiver.nextPacket()

                # If data sent to receiver
                if robot0Obj.message != []:

                    r0_message = robot0Obj.message
                    robot0Obj.message = []

                    # If exit message is correct
                    if r0_message[0] == 'E':
                      # Check robot position is on starting tile
                      if robot0Obj.startingTile.checkPosition(robot0Obj.position):
                        finished = True
                        supervisor.wwiSendText("ended")
                        if robot0Obj.victimIdentified:
                          robot0Obj.increaseScore("Exit Bonus", robot0Obj.getScore() * 0.1)
                        else:
                          robot0Obj.history.enqueue("No Exit Bonus")
                        add_map_multiplier()
                        # Update score and history
                        robot_quit(robot0Obj, 0, False)
                        last = True
                            
                    elif r0_message[0] == 'M':
                        try:
                          # If map_data submitted
                          if robot0Obj.map_data.size != 0:
                            # If not previously evaluated
                            if not robot0Obj.sent_maps: 
                              map_score = MapScorer.calculateScore(mapSolution, robot0Obj.map_data)
                                                      
                              robot0Obj.history.enqueue(f"Map Correctness {str(round(map_score * 100,2))}%")
                              
                              # Add percent
                              robot0Obj.map_score_percent = map_score
                              robot0Obj.sent_maps = True
                              
                              robot0Obj.map_data = np.array([])
                              # Do something...
                            else:
                              print(cl.colored(f"The map has already been evaluated.", "red"))
                          else:
                            print(cl.colored("Please send your map data before hand.", "red"))
                        except Exception as e:
                          print(cl.colored("Map scoring error. Please check your code. (except)", "red"))
                          print(cl.colored(e, "red"))
                    
                    elif r0_message[0] == 'L':
                      relocate(robot0, robot0Obj)
                      robot0Obj.robot_timeStopped = 0
                      robot0Obj.stopped = False
                      robot0Obj.stoppedTime = None
                      if configData[3] and viewpoint_node:
                        setViewPoint(robot0Obj, viewpoint_node, nowSide)

                    elif r0_message[0] == 'G':
                      emitter.send(struct.pack("c f i", bytes("G", "utf-8"), round(robot0Obj.getScore(),2), maxTime - int(timeElapsed)))

                    # If robot stopped for 1 second
                    elif robot0Obj.timeStopped() >= 1.0:

                        # Get estimated values
                        r0_est_vic_pos = r0_message[0]
                        r0_est_vic_type = r0_message[1]

                        # For each human
                        # TODO optimise
                        
                        def toLower(s):
                            return s.lower()
                        
                        iterator = humans
                        name = 'Victim'
                        
                        if r0_est_vic_type.lower() in list(map(toLower, HazardMap.HAZARD_TYPES)):
                            iterator = hazards
                            name = 'Hazard'
                            
                        misidentification = True
                        for i, h in enumerate(iterator):
                            # Check if in range
                            if h.checkPosition(robot0Obj.position):
                                # Check if estimated position is in range
                                if h.checkPosition(r0_est_vic_pos):
                                    # If robot on same side
                                    if h.onSameSide(robot0Obj.position):
                                        misidentification = False
                                        # If not already identified
                                        if not h.identified:
                                            # Get points scored depending on the type of victim
                                            #pointsScored = h.scoreWorth

                                            grid = coord2grid(h.wb_translationField.getSFVec3f())
                                            roomNum = supervisor.getFromDef("WALLTILES").getField("children").getMFNode(grid).getField("room").getSFInt32() - 1

                                            # Update score and history
                                            if r0_est_vic_type.lower() == h.simple_victim_type.lower():
                                                robot0Obj.increaseScore(f"Successful {name} Type Correct Bonus", 10, roomMult[roomNum])

                                            robot0Obj.increaseScore(f"Successful {name} Identification", h.scoreWorth, roomMult[roomNum])
                                            robot0Obj.victimIdentified = True

                                            h.identified = True

                        if misidentification:
                            robot0Obj.increaseScore(f"Misidentification of {name}", -5)

            
            

            if currentlyRunning and not finished:
              # Relocate robot if stationary for 20 sec
              if robot0Obj.timeStopped() >= 20:
                  if not configData[1]:
                    relocate(robot0, robot0Obj)
                    if configData[3] and viewpoint_node:
                        setViewPoint(robot0Obj, viewpoint_node, nowSide)
                  robot0Obj.robot_timeStopped = 0
                  robot0Obj.stopped = False
                  robot0Obj.stoppedTime = None

              if robot0Obj.position[1] < -0.035 and currentlyRunning and not finished:
                  if not configData[1]:
                    relocate(robot0, robot0Obj)
                    if configData[3] and viewpoint_node:
                        setViewPoint(robot0Obj, viewpoint_node, nowSide)
                  robot0Obj.robot_timeStopped = 0
                  robot0Obj.stopped = False
                  robot0Obj.stoppedTime = None


            if robotInitialized:
              # Send the update information to the robot window
              nowScore = robot0Obj.getScore()
              if lastSentScore != nowScore or lastSentTime != int(timeElapsed):
                  supervisor.wwiSendText("update," + str(round(nowScore,2)) + "," + str(int(timeElapsed)) + "," + str(maxTime))
                  lastSentScore = nowScore
                  lastSentTime = int(timeElapsed)
                  if configData[2]:
                    supervisor.setLabel(0, "Score: " + str(round(nowScore,2)), 0.15, 0,0.15, 0x4cd137, 0)
                    remainTime = maxTime - int(timeElapsed)
                    supervisor.setLabel(1, "Clock: " + str(int(int(remainTime)/60)).zfill(2) + ":"+ str(int(int(remainTime)%60)).zfill(2), 0.4, 0,0.15, 0x4cd137, 0)

              # If the time is up
              if timeElapsed >= maxTime and last != -1:
                  add_map_multiplier()
                  robot_quit(robot0Obj, 0, True)
                  finished = True
                  last = True
                  supervisor.wwiSendText("ended")

        # If the running state changes
        if previousRunState != currentlyRunning:
            # Update the value and #print
            previousRunState = currentlyRunning

        # Get the message in from the robot window(if there is one)
        message = supervisor.wwiReceiveText()
        # If there is a message
        if message != "":
            # split into parts
            parts = message.split(",")
            # If there are parts
            if len(parts) > 0:
                if parts[0] == "run":
                    # Start running the match
                    currentlyRunning = True
                    gameStarted = True
                if parts[0] == "pause":
                    # Pause the match
                    currentlyRunning = False
                if parts[0] == "reset":
                    robot_quit(robot0Obj, 0, False)
                    # Reset both controller files
                    resetControllerFile()
                    resetVictimsTextures()
                    resetRobotProto()

                    # Reset the simulation
                    supervisor.simulationReset()
                    simulationRunning = False
                    finished = True
                    # Restart this supervisor
                    mainSupervisor.restartController()

                    if robot0Obj.startingTile != None:
                        #Show start tile
                        robot0Obj.startingTile.wb_node.getField("start").setSFBool(True)

                    # Must restart world - to reload to .wbo file for the robot which only seems to be read and interpreted
                    # once per game, so if we load a new robot file, the new changes won't come into place until the world
                    # is reset!
                    supervisor.worldReload()

                if parts[0] == "robot0Unload":
                    # Unload the robot 0 controller
                    if not gameStarted:
                        resetController(0)
                
                if parts[0] == "robot1Unload":
                    # Remove the robot proto
                    if not gameStarted:
                        resetRobotProto(True)

                if parts[0] == 'relocate':
                    data = message.split(",", 1)
                    if len(data) > 1:
                        if int(data[1]) == 0:
                            relocate(robot0, robot0Obj)
                            if configData[3] and viewpoint_node:
                              setViewPoint(robot0Obj, viewpoint_node, nowSide)

                if parts[0] == 'quit':
                    data = message.split(",", 1)
                    if len(data) > 1:
                        if int(data[1]) == 0:
                            if gameStarted:
                                add_map_multiplier()
                                robot0Obj.history.enqueue("Give up!")
                                robot_quit(robot0Obj, 0, True)
                                finished = True
                                last = True
                                supervisor.wwiSendText("ended")
                
                if parts[0] == 'robotJson':
                    data = message.split(",", 1)
                    if len(data) > 1:
                        process_robot_json(data[1])
                
                if parts[0] == 'config':
                  configData = list(map((lambda x: int(x)), message.split(",")[1:]))
                  f = open(configFilePath, 'w')
                  f.write(','.join(message.split(",")[1:]))
                  f.close()

        

        # If the match is running
        if robotInitialized and currentlyRunning and not finished:
            # Get the time since the last frame
            frameTime = supervisor.getTime() - lastTime
            # Add to the elapsed time
            timeElapsed = timeElapsed + frameTime
            # Get the current time
            lastTime = supervisor.getTime()
            # Step the simulation on
            step = supervisor.step(32)
            # If the simulation is terminated or the time is up
            if step == -1:
                # Stop simulating
                finished = True
                  
        elif first or last or finished:
            supervisor.step(32)            