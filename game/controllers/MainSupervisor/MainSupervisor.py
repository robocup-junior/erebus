"""Supervisor Controller
   Written by Robbie Goldman and Alfred Roberts
"""

from controller import Supervisor
import os
import random
import struct
import math
import datetime
import threading
import shutil
import AutoInstall
AutoInstall._import("np", "numpy")
import ControllerUploader
import MapScorer
import obstacleCheck
import glob
import json
import obstacleCheck
import mapSolutionCalculator

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
        self.inSwamp = True

        self.history = RobotHistory()

        self._score = 0

        self.robot_timeStopped = 0
        self.stopped = False
        self.stoppedTime = None

        self.message = []
        self.map_data = np.array([])
        self.sent_maps = [False, False, False]
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
        self.radius = 0.09
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

    def checkPosition(self, pos: list) -> bool:
        '''Check if a position is near an object, based on the min_dist value'''
        # Get distance from the object to the passed position using manhattan distance for speed
        # TODO Check if we want to use euclidian or manhattan distance -- currently manhattan
        distance = math.sqrt(((self.position[0] - pos[0])**2) + ((self.position[2] - pos[2])**2))
        return distance <= self.radius

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


def resetControllerFile() -> None:
    '''Remove the controller'''
    if configData[0]:
      return
    path = os.path.dirname(os.path.abspath(__file__))

    if path[-4:] == "game":
      path = os.path.join(path, "controllers/robot0Controller")
    else:
      path = os.path.join(path, "../robot0Controller")
    path = os.path.join(path, "robot0Controller.*")
    print(path)

    for file in glob.glob(path):
        os.remove(file)

def resetController(num: int) -> None:
    '''Send message to robot window to say that controller has been unloaded'''
    resetControllerFile()
    supervisor.wwiSendText("unloaded"+str(num))

def resetRobotProto() -> None:
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
          if configData[0]:
            return
          shutil.copyfile(default_robot_proto, robot_proto)
        else:
          shutil.copyfile(default_robot_proto, robot_proto)          
          supervisor.worldReload()
        supervisor.wwiSendText("unloaded1")
    except:
        print('Error resetting robot proto')

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
            print("Invalid obstacle found, it could not be tested")
    
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
            print("Obstacle {0} removed, insufficient clearance to walls.".format(nodeData[1]))
        except:
            #It was not a proto obstacle so it was ignored
            print("Invalid obstacle found, could not remove.")     

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

def robot_quit(robotObj, num, manualExit):
    '''Quit robot from simulation'''
    # Quit robot if present
    if robotObj.inSimulation:
        # Remove webots node
        robotObj.wb_node.remove()
        robotObj.inSimulation = False
        # Send message to robot window to update quit button
        supervisor.wwiSendText("robotNotInSimulation"+str(num))
        # Update history event whether its manual or via exit message
        if manualExit:
            robotObj.history.enqueue("Manual Exit")
        else:
            robotObj.history.enqueue("Successful Exit")

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
    logFileName = file_date.strftime("log %m-%d-%y %H,%M,%S")

    filePath = os.path.join(filePath, logFileName + ".txt")

    try:
        # Write file
        logsFile = open(filePath, "w")
        logsFile.write(log_str)
        logsFile.close()
    except:
        # If write file fails, most likely due to missing logs dir
        print("Couldn't write log file, no log directory " + filePath)

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
    robot0Obj.startingTile.wb_node.getField("start").setSFBool(True)
    robot0Obj.visitedCheckpoints.append(startingTileObj.center)

    robot0Obj.position = [startingTileObj.center[0], startingTileObj.center[1], startingTileObj.center[2]]
    robot0Obj.set_starting_orientation()

def clamp(n, minn, maxn):
    '''Simple clamp function that limits a number between a specified range'''
    return max(min(maxn, n), minn)
  
def add_map_multiplier():  
    score_change = robot0Obj.getScore() * (robot0Obj.map_score_percent / areaCount)
    robot0Obj.history.enqueue(f"Map Correctness (Total) {str(round((robot0Obj.map_score_percent / areaCount) * 100,1))}%")
    robot0Obj.increaseScore("Map Bonus", score_change)    

def generate_robot_proto(robot_json):
    
    # Hard coded, values from website
    component_max_counts = {
        "Wheel": 4,
        "Distance Sensor": 8,
        "Camera": 2
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
        
        DEF BATTERY_CONNECTOR Transform {
          rotation 0 1 0 3.14159
          children [
            Shape {
              appearance Copper {
              }
              geometry IndexedFaceSet {
                coord Coordinate {
                  point [
                    0.017813 0.036934 0.02632
                    -0.017776 0.036934 0.026276
                    0.014654 0.036868 0.026266
                    -0.014659 0.036868 0.026289
                    -0.017776 0.00184 0.026276
                    -0.014659 0.001774 0.026289
                    0.017813 0.002054 0.02632
                    0.014654 0.001987 0.026266
                    -0.014659 0.012265 0.026289
                    0.014654 0.012478 0.026266
                    0.00251 0.036993 -0.026929
                    0.00251 0.002646 -0.026929
                    -0.002508 0.036993 -0.026937
                    -0.002508 0.002646 -0.026937
                  ]
                }
                texCoord TextureCoordinate {
                  point [
                    0.7946 0.9656
                    0.6886 0.9674
                    0.6886 0.0287
                    0.7946 0.0269
                    0.9664 0.0287
                    0.9664 0.9731
                    0.8618 0.9713
                    0.8618 0.0269
                    0.0336 0.0269
                    0.3858 0.029
                    0.3858 0.8178
                    0.0336 0.8157
                    0.6214 0.0269
                    0.6214 0.9512
                    0.4529 0.9512
                    0.4529 0.0269
                  ]
                }
                coordIndex [
                  2, 0, 6, 7, -1, 4, 1, 3, 5, -1
                  9, 7, 5, 8, -1, 12, 13, 11, 10, -1
                ]
                texCoordIndex [
                  0, 1, 2, 3, -1, 4, 5, 6, 7, -1
                  8, 9, 10, 11, -1, 12, 13, 14, 15, -1
                ]
              }
            }
            Shape {
              appearance Copper {
              }
              geometry IndexedFaceSet {
                coord Coordinate {
                  point [
                    0.017813 0.036934 0.02632
                    -0.017776 0.036934 0.026276
                    0.014654 0.036868 0.026266
                    -0.014659 0.036868 0.026289
                    -0.017776 0.00184 0.026276
                    -0.014659 0.001774 0.026289
                    0.017813 0.002054 0.02632
                    0.014654 0.001987 0.026266
                    -0.014659 0.012265 0.026289
                    0.014654 0.012478 0.026266
                    0.00251 0.036993 -0.026929
                    0.00251 0.002646 -0.026929
                    -0.002508 0.036993 -0.026937
                    -0.002508 0.002646 -0.026937
                  ]
                }
                texCoord TextureCoordinate {
                  point [
                    0.7946 0.9656
                    0.6886 0.9674
                    0.6886 0.0287
                    0.7946 0.0269
                    0.9664 0.0287
                    0.9664 0.9731
                    0.8618 0.9713
                    0.8618 0.0269
                    0.0336 0.0269
                    0.3858 0.029
                    0.3858 0.8178
                    0.0336 0.8157
                    0.6214 0.0269
                    0.6214 0.9512
                    0.4529 0.9512
                    0.4529 0.0269
                  ]
                }
                ccw FALSE
                coordIndex [
                  2, 0, 6, 7, -1, 4, 1, 3, 5, -1
                  9, 7, 5, 8, -1, 12, 13, 11, 10, -1
                ]
                texCoordIndex [
                  0, 1, 2, 3, -1, 4, 5, 6, 7, -1
                  8, 9, 10, 11, -1, 12, 13, 14, 15, -1
                ]
              }
            }
          ]
        }
        DEF MOTORS Transform {
          translation 0 0.02 0
          rotation 0 0 1 1.5707996938995747
          children [
            Shape {
              appearance PBRAppearance {
                roughness 1
                metalness 0
              }
              geometry Cylinder {
                height 0.04
                radius 0.005
              }
            }
            Shape {
              appearance PBRAppearance {
                roughness 1
              }
              geometry Cylinder {
                height 0.02
                radius 0.0053
              }
            }
          ]
        }
        DEF EPUCK_PLATE Transform {
          translation 0.0002 0.037 0
          rotation 0 1 0 3.14159
          scale 0.01 0.01 0.01
          children [
            Shape {
              appearance DEF EPUCK_SIDE_PRINT_APPEARANCE PBRAppearance {
                baseColor 0.184314 0.635294 0.184314
                roughness 0.4
                metalness 0
              }
              geometry IndexedFaceSet {
                coord Coordinate {
                  point [
                    3.3287 0.152947 1.08156 2.83156 0.152947 2.05725 2.05725 0.152947 2.83156 1.08156 0.152947 3.3287 -1.5299e-07 0.152947 3.5 -1.08156 0.152947 3.3287 -2.05725 0.152947 2.83156 -2.83156 0.152947 2.05725 -3.3287 0.152947 1.08156 -3.5 0.152947 -7.23212e-07 -3.3287 0.152947 -1.08156 -2.83156 0.152947 -2.05725 -2.05725 0.152947 -2.83156 -1.08156 0.152947 -3.3287 2.96236e-06 0.152947 -3.5 1.08156 0.152947 -3.3287 2.05725 0.152947 -2.83156 2.83156 0.152947 -2.05724 3.3287 0.152947 -1.08155 3.5 0.152947 5.20152e-06 3.3287 1.93187e-08 1.08156 2.83156 1.93187e-08 2.05725 2.05725 1.93187e-08 2.83156 1.08156 1.93187e-08 3.3287 -1.5299e-07 1.93187e-08 3.5 -1.08156 1.93187e-08 3.3287 -2.05725 1.93187e-08 2.83156 -2.83156 1.93187e-08 2.05725 -3.3287 1.93187e-08 1.08156 -3.5 1.93187e-08 -7.23212e-07 -3.3287 1.93187e-08 -1.08156 -2.83156 1.93187e-08 -2.05725 -2.05725 1.93187e-08 -2.83156 -1.08156 1.93187e-08 -3.3287 2.96236e-06 1.93187e-08 -3.5 1.08156 1.93187e-08 -3.3287 2.05725 1.93187e-08 -2.83156 2.83156 1.93187e-08 -2.05724 3.3287 1.93187e-08 -1.08155 3.5 1.93187e-08 5.20152e-06 1.00136e-06 1.93187e-08 5.93862e-07
                  ]
                }
                coordIndex [
                  40, 39, 20, -1, 40, 38, 39, -1, 40, 37, 38, -1, 40, 36, 37, -1, 40, 35, 36, -1, 40, 34, 35, -1, 40, 33, 34, -1, 40, 32, 33, -1, 40, 31, 32, -1, 40, 30, 31, -1, 40, 29, 30, -1, 40, 28, 29, -1, 40, 27, 28, -1, 40, 26, 27, -1, 40, 25, 26, -1, 40, 24, 25, -1, 40, 23, 24, -1, 40, 22, 23, -1, 40, 21, 22, -1, 40, 20, 21, -1, 0, 20, 39, 19, -1, 19, 39, 38, 18, -1, 18, 38, 37, 17, -1, 17, 37, 36, 16, -1, 16, 36, 35, 15, -1, 15, 35, 34, 14, -1, 14, 34, 33, 13, -1, 13, 33, 32, 12, -1, 12, 32, 31, 11, -1, 11, 31, 30, 10, -1, 10, 30, 29, 9, -1, 9, 29, 28, 8, -1, 8, 28, 27, 7, -1, 7, 27, 26, 6, -1, 6, 26, 25, 5, -1, 5, 25, 24, 4, -1, 4, 24, 23, 3, -1, 3, 23, 22, 2, -1, 2, 22, 21, 1, -1, 1, 21, 20, 0, -1
                ]
                creaseAngle 0.785398
              }
            }
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
              geometry IndexedFaceSet {
                coord Coordinate {
                  point [
                    3.3287 0.152947 1.08156 2.83156 0.152947 2.05725 2.05725 0.152947 2.83156 1.08156 0.152947 3.3287 -1.5299e-07 0.152947 3.5 -1.08156 0.152947 3.3287 -2.05725 0.152947 2.83156 -2.83156 0.152947 2.05725 -3.3287 0.152947 1.08156 -3.5 0.152947 -7.23212e-07 -3.3287 0.152947 -1.08156 -2.83156 0.152947 -2.05725 -2.05725 0.152947 -2.83156 -1.08156 0.152947 -3.3287 2.96236e-06 0.152947 -3.5 1.08156 0.152947 -3.3287 2.05725 0.152947 -2.83156 2.83156 0.152947 -2.05724 3.3287 0.152947 -1.08155 3.5 0.152947 5.20152e-06 1.00136e-06 0.152947 5.93862e-07
                  ]
                }
                texCoord TextureCoordinate {
                  point [
                    0.500977 0.499023 0.977434 0.344213 1.00195 0.499023 0.500977 0.499023 1.00195 0.499023 0.977434 0.653833 0.500977 0.499023 0.977434 0.653833 0.906275 0.79349 0.500977 0.499023 0.906275 0.79349 0.795444 0.904322 0.500977 0.499023 0.795444 0.904322 0.655787 0.97548 0.500977 0.499023 0.655787 0.97548 0.500977 1 0.500977 0.499023 0.500977 1 0.346167 0.975481 0.500977 0.499023 0.346167 0.975481 0.20651 0.904322 0.500977 0.499023 0.20651 0.904322 0.0956782 0.79349 0.500977 0.499023 0.0956782 0.79349 0.0245196 0.653834 0.500977 0.499023 0.0245196 0.653834 0 0.499024 0.500977 0.499023 0 0.499024 0.0245195 0.344213 0.500977 0.499023 0.0245195 0.344213 0.0956781 0.204557 0.500977 0.499023 0.0956781 0.204557 0.20651 0.093725 0.500977 0.499023 0.20651 0.093725 0.346166 0.0225664 0.500977 0.499023 0.346166 0.0225664 0.500977 -0.00195312 0.500977 0.499023 0.500977 -0.00195312 0.655787 0.0225663 0.500977 0.499023 0.655787 0.0225663 0.795443 0.093725 0.500977 0.499023 0.795443 0.093725 0.906275 0.204557 0.500977 0.499023 0.906275 0.204557 0.977434 0.344213
                  ]
                }
                coordIndex [
                  20, 0, 19, -1, 20, 19, 18, -1, 20, 18, 17, -1, 20, 17, 16, -1, 20, 16, 15, -1, 20, 15, 14, -1, 20, 14, 13, -1, 20, 13, 12, -1, 20, 12, 11, -1, 20, 11, 10, -1, 20, 10, 9, -1, 20, 9, 8, -1, 20, 8, 7, -1, 20, 7, 6, -1, 20, 6, 5, -1, 20, 5, 4, -1, 20, 4, 3, -1, 20, 3, 2, -1, 20, 2, 1, -1, 20, 1, 0, -1
                ]
                texCoordIndex [
                  0, 1, 2, -1, 3, 4, 5, -1, 6, 7, 8, -1, 9, 10, 11, -1, 12, 13, 14, -1, 15, 16, 17, -1, 18, 19, 20, -1, 21, 22, 23, -1, 24, 25, 26, -1, 27, 28, 29, -1, 30, 31, 32, -1, 33, 34, 35, -1, 36, 37, 38, -1, 39, 40, 41, -1, 42, 43, 44, -1, 45, 46, 47, -1, 48, 49, 50, -1, 51, 52, 53, -1, 54, 55, 56, -1, 57, 58, 59, -1
                ]
                creaseAngle 0.785398
              }
            }
          ]
        }
        DEF EPUCK_BATTERY Transform {
          translation 0 0.007 0.026
          rotation 1 0 0 -1.5708053071795867
          children [
            Shape {
              appearance PBRAppearance {
                baseColor 0 0 0
                roughness 1
                metalness 0
              }
              geometry IndexedFaceSet {
                coord Coordinate {
                  point [
                    0.012914 0.050175 0.005215, 0.014813 0.050175 0.004421, 0.011886 0.050175 0.005317, 0.013902 0.050175 0.004912, -0.012933 0.050175 0.005215, -0.013922 0.050175 0.004912, -0.014833 0.050175 0.004421, -0.015631 0.050175 0.00376, -0.016287 0.050175 0.002954, -0.016774 0.050175 0.002035, -0.017074 0.050175 0.001037, -0.017175 0.050175 0, -0.017074 0.050175 -0.001037, -0.016774 0.050175 -0.002034, -0.016287 0.050175 -0.002954, -0.015631 0.050175 -0.003759, -0.014833 0.050175 -0.00442, -0.013922 0.050175 -0.004912, -0.012933 0.050175 -0.005214, -0.011905 0.050175 -0.005316, -0.011905 0.050175 0.005317, 0.012914 0.050175 -0.005214, 0.013902 0.050175 -0.004912, 0.014813 0.050175 -0.00442, 0.015612 0.050175 -0.003759, 0.016267 0.050175 -0.002954, 0.016754 0.050175 -0.002034, 0.017054 0.050175 -0.001037, 0.017155 0.050175 0, 0.017054 0.050175 0.001037, 0.016754 0.050175 0.002035, 0.016267 0.050175 0.002954, 0.015612 0.050175 0.00376, 0.012914 0.04381 0.005215, 0.014813 0.04381 0.004421, 0.011886 0.04381 0.005317, 0.013902 0.04381 0.004912, 0.012914 0.04381 -0.005214, 0.013902 0.04381 -0.004912, 0.014813 0.04381 -0.00442, 0.015612 0.04381 -0.003759, 0.016267 0.04381 -0.002954, 0.016754 0.04381 -0.002034, 0.017054 0.04381 -0.001037, 0.017155 0.04381 0, 0.017054 0.04381 0.001037, 0.016754 0.04381 0.002035, 0.016267 0.04381 0.002954, 0.015612 0.04381 0.00376, -0.012933 0.043756 0.005215, -0.013922 0.043756 0.004912, -0.014833 0.043756 0.004421, -0.015631 0.043756 0.00376, -0.016287 0.043756 0.002954, -0.016774 0.043756 0.002035, -0.017074 0.043756 0.001037, -0.017175 0.043756 0, -0.017074 0.043756 -0.001037, -0.016774 0.043756 -0.002034, -0.016287 0.043756 -0.002954, -0.015631 0.043756 -0.003759, -0.014833 0.043756 -0.00442, -0.013922 0.043756 -0.004912, -0.012933 0.043756 -0.005214, -0.011905 0.043756 -0.005316, -0.011905 0.043756 0.005317, 0.012106 0.050175 0.003134, 0.003471 0.050175 -0.003112, 0.003471 0.050175 0.003134, 0.012525 0.050175 -0.003052, -0.002733 0.050175 0.003134, -0.011822 0.050175 -0.003112, -0.011822 0.050175 0.003134, -0.002655 0.050175 -0.003052
                  ]
                }
                coordIndex [
                  37, 21, 22, -1, 22, 23, 39, -1, 40, 39, 23, -1, 41, 40, 24, -1, 42, 41, 25, -1, 43, 42, 26, -1, 44, 43, 27, -1, 45, 44, 28, -1, 46, 45, 29, -1, 47, 46, 30, -1, 48, 47, 31, -1, 34, 48, 32, -1, 36, 34, 1, -1, 33, 36, 3, -1, 35, 33, 0, -1, 65, 20, 4, -1, 50, 49, 4, -1, 51, 50, 5, -1, 52, 51, 6, -1, 53, 52, 7, -1, 54, 53, 8, -1, 55, 54, 9, -1, 56, 55, 10, -1, 57, 56, 11, -1, 58, 57, 12, -1, 59, 58, 13, -1, 60, 59, 14, -1, 61, 60, 15, -1, 62, 61, 16, -1, 63, 62, 17, -1, 64, 63, 18, -1, 30, 66, 31, -1, 11, 72, 71, -1, 68, 67, 73, -1, 68, 70, 2, -1, 73, 69, 21, -1, 56, 64, 65, -1, 64, 19, 20, -1, 47, 48, 35, -1, 35, 2, 21, -1, 19, 2, 20, -1, 38, 37, 22, -1, 39, 38, 22, -1, 22, 21, 23, -1, 24, 40, 23, -1, 25, 41, 24, -1, 26, 42, 25, -1, 27, 43, 26, -1, 28, 44, 27, -1, 29, 45, 28, -1, 30, 46, 29, -1, 31, 47, 30, -1, 32, 48, 31, -1, 1, 34, 32, -1, 3, 36, 1, -1, 0, 33, 3, -1, 2, 35, 0, -1, 49, 65, 4, -1, 5, 50, 4, -1, 6, 51, 5, -1, 7, 52, 6, -1, 8, 53, 7, -1, 9, 54, 8, -1, 10, 55, 9, -1, 11, 56, 10, -1, 12, 57, 11, -1, 13, 58, 12, -1, 14, 59, 13, -1, 15, 60, 14, -1, 16, 61, 15, -1, 17, 62, 16, -1, 18, 63, 17, -1, 19, 64, 18, -1, 32, 31, 66, -1, 30, 29, 66, -1, 28, 27, 69, -1, 26, 25, 69, -1, 24, 23, 69, -1, 22, 21, 69, -1, 66, 2, 3, -1, 22, 69, 23, -1, 25, 24, 69, -1, 29, 28, 66, -1, 1, 32, 66, -1, 0, 3, 2, -1, 69, 66, 28, -1, 27, 26, 69, -1, 3, 1, 66, -1, 4, 20, 5, -1, 72, 10, 9, -1, 19, 18, 17, -1, 17, 16, 71, -1, 15, 14, 71, -1, 13, 12, 71, -1, 11, 10, 72, -1, 9, 8, 72, -1, 7, 6, 72, -1, 5, 20, 72, -1, 71, 19, 17, -1, 16, 15, 71, -1, 12, 11, 71, -1, 8, 7, 72, -1, 5, 72, 6, -1, 14, 13, 71, -1, 70, 68, 73, -1, 20, 2, 70, -1, 66, 68, 2, -1, 70, 72, 20, -1, 21, 19, 73, -1, 71, 73, 19, -1, 64, 56, 57, -1, 49, 50, 65, -1, 51, 52, 65, -1, 53, 54, 65, -1, 55, 56, 65, -1, 57, 58, 64, -1, 59, 60, 64, -1, 61, 62, 64, -1, 63, 64, 62, -1, 50, 51, 65, -1, 54, 55, 65, -1, 58, 59, 64, -1, 61, 64, 60, -1, 52, 53, 65, -1, 65, 64, 20, -1, 35, 37, 44, -1, 38, 39, 37, -1, 40, 41, 37, -1, 42, 43, 37, -1, 44, 45, 35, -1, 46, 47, 35, -1, 48, 34, 35, -1, 36, 33, 35, -1, 37, 39, 40, -1, 41, 42, 37, -1, 45, 46, 35, -1, 34, 36, 35, -1, 37, 43, 44, -1, 37, 35, 21, -1, 21, 2, 19, -1
                ]
                creaseAngle 0.5
              }
            }
            Shape {
              appearance PBRAppearance {
              }
              geometry IndexedFaceSet {
                coord Coordinate {
                  point [
                    0.012168 0.04944 0.004577, 0.013958 0.04944 0.00388, 0.011199 0.04944 0.004666, 0.013099 0.04944 0.004311, -0.012188 0.04944 0.004577, -0.013119 0.04944 0.004311, -0.013977 0.04944 0.00388, -0.01473 0.04944 0.0033, -0.015347 0.04944 0.002593, -0.015806 0.04944 0.001786, -0.016089 0.04944 0.000911, -0.016184 0.04944 0, -0.016089 0.04944 -0.00091, -0.015806 0.04944 -0.001785, -0.015347 0.04944 -0.002592, -0.01473 0.04944 -0.003299, -0.013977 0.04944 -0.00388, -0.013119 0.04944 -0.004311, -0.012188 0.04944 -0.004576, -0.011219 0.04944 -0.004666, -0.011219 0.04944 0.004666, 0.012168 0.04944 -0.004576, 0.013099 0.04944 -0.004311, 0.013958 0.04944 -0.00388, 0.01471 0.04944 -0.003299, 0.015328 0.04944 -0.002592, 0.015787 0.04944 -0.001785, 0.016069 0.04944 -0.00091, 0.016165 0.04944 0, 0.016069 0.04944 0.000911, 0.015787 0.04944 0.001786, 0.015328 0.04944 0.002593, 0.01471 0.04944 0.0033, 0.008543 0 0.003561, 0.009282 0 0.003492, 0.009993 0 0.00329, 0.010648 0 0.002961, 0.011222 0 0.002518, 0.011693 0 0.001978, 0.012044 0 0.001363, 0.012259 0 0.000695, 0.012332 0 0, 0.012259 0 -0.000694, 0.012044 0 -0.001362, 0.011693 0 -0.001978, 0.011222 0 -0.002517, 0.010648 0 -0.00296, 0.009993 0 -0.003289, 0.009282 0 -0.003492, 0.008543 0 -0.00356, -0.008563 0 0.003561, -0.008563 0 -0.00356, -0.009302 0 -0.003492, -0.010013 0 -0.003289, -0.010668 0 -0.00296, -0.011242 0 -0.002517, -0.011713 0 -0.001978, -0.012063 0 -0.001362, -0.012279 0 -0.000694, -0.012352 0 0, -0.012279 0 0.000695, -0.012063 0 0.001363, -0.011713 0 0.001978, -0.011242 0 0.002518, -0.010668 0 0.002961, -0.010013 0 0.00329, -0.009302 0 0.003492, 0.008543 0 0.004674, 0.008543 0 -0.004673, -0.008563 0 0.004674, -0.008563 0 -0.004673, 0.008543 0.001605 0.004674, 0.008543 0.001605 -0.004673, -0.008563 0.001605 0.004674, -0.008563 0.001605 -0.004673
                  ]
                }
                coordIndex [
                  1, 17, 13, -1, 74, 72, 68, -1, 70, 68, 49, -1, 50, 33, 67, -1, 67, 71, 73, -1, 50, 49, 33, -1, 5, 4, 20, -1, 20, 2, 0, -1, 0, 3, 1, -1, 31, 30, 29, -1, 20, 0, 1, -1, 31, 29, 28, -1, 5, 20, 1, -1, 31, 28, 27, -1, 6, 5, 1, -1, 31, 27, 26, -1, 7, 6, 1, -1, 31, 26, 25, -1, 8, 7, 1, -1, 31, 25, 24, -1, 9, 8, 1, -1, 32, 31, 24, -1, 10, 9, 1, -1, 1, 32, 24, -1, 24, 23, 22, -1, 22, 21, 19, -1, 19, 18, 17, -1, 17, 16, 15, -1, 15, 14, 13, -1, 13, 12, 11, -1, 11, 10, 1, -1, 1, 24, 22, -1, 22, 19, 17, -1, 17, 15, 13, -1, 13, 11, 1, -1, 1, 22, 17, -1, 70, 74, 68, -1, 51, 70, 49, -1, 69, 50, 67, -1, 69, 67, 73, -1, 66, 65, 64, -1, 37, 36, 35, -1, 66, 64, 63, -1, 38, 37, 35, -1, 66, 63, 62, -1, 39, 38, 35, -1, 66, 62, 61, -1, 40, 39, 35, -1, 66, 61, 60, -1, 41, 40, 35, -1, 66, 60, 59, -1, 42, 41, 35, -1, 66, 59, 58, -1, 43, 42, 35, -1, 66, 58, 57, -1, 44, 43, 35, -1, 66, 57, 56, -1, 45, 44, 35, -1, 66, 56, 55, -1, 46, 45, 35, -1, 66, 55, 54, -1, 47, 46, 35, -1, 66, 54, 53, -1, 47, 35, 34, -1, 66, 53, 52, -1, 47, 34, 33, -1, 66, 52, 51, -1, 48, 47, 33, -1, 50, 66, 51, -1, 49, 48, 33, -1, 50, 51, 49, -1
                ]
              }
            }
            Shape {
              appearance PBRAppearance {
                baseColor 0.12549 0.290196 0.529412
                metalness 0
              }
              geometry IndexedFaceSet {
                coord Coordinate {
                  point [
                    0.012168 0.04944 0.004577, 0.013958 0.04944 0.00388, 0.011199 0.04944 0.004666, 0.013099 0.04944 0.004311, 0.011199 0 0.004666, 0.012168 0 0.004577, 0.013099 0 0.004311, 0.013958 0 0.00388, 0.01471 0 0.0033, 0.015328 0 0.002593, 0.015787 0 0.001786, 0.016069 0 0.000911, 0.016165 0 0, 0.016069 0 -0.00091, 0.015787 0 -0.001785, 0.015328 0 -0.002592, 0.01471 0 -0.003299, 0.013958 0 -0.00388, 0.013099 0 -0.004311, 0.012168 0 -0.004576, 0.011199 0 -0.004666, -0.012188 0.04944 0.004577, -0.013119 0.04944 0.004311, -0.013977 0.04944 0.00388, -0.01473 0.04944 0.0033, -0.015347 0.04944 0.002593, -0.015806 0.04944 0.001786, -0.016089 0.04944 0.000911, -0.016184 0.04944 0, -0.016089 0.04944 -0.00091, -0.015806 0.04944 -0.001785, -0.015347 0.04944 -0.002592, -0.01473 0.04944 -0.003299, -0.013977 0.04944 -0.00388, -0.013119 0.04944 -0.004311, -0.012188 0.04944 -0.004576, -0.011219 0 0.004666, -0.011219 0.04944 -0.004666, -0.011219 0.04944 0.004666, 0.012168 0.04944 -0.004576, 0.013099 0.04944 -0.004311, 0.013958 0.04944 -0.00388, 0.01471 0.04944 -0.003299, 0.015328 0.04944 -0.002592, 0.015787 0.04944 -0.001785, 0.016069 0.04944 -0.00091, 0.016165 0.04944 0, 0.016069 0.04944 0.000911, 0.015787 0.04944 0.001786, 0.015328 0.04944 0.002593, 0.01471 0.04944 0.0033, -0.011219 0 -0.004666, -0.012188 0 -0.004576, -0.013119 0 -0.004311, -0.013977 0 -0.00388, -0.01473 0 -0.003299, -0.015347 0 -0.002592, -0.015806 0 -0.001785, -0.016089 0 -0.00091, -0.016184 0 0, -0.016089 0 0.000911, -0.015806 0 0.001786, -0.015347 0 0.002593, -0.01473 0 0.0033, -0.013977 0 0.00388, -0.013119 0 0.004311, -0.012188 0 0.004577, 0.008543 0 0.003561, 0.009282 0 0.003492, 0.009993 0 0.00329, 0.010648 0 0.002961, 0.011222 0 0.002518, 0.011693 0 0.001978, 0.012044 0 0.001363, 0.012259 0 0.000695, 0.012332 0 0, 0.012259 0 -0.000694, 0.012044 0 -0.001362, 0.011693 0 -0.001978, 0.011222 0 -0.002517, 0.010648 0 -0.00296, 0.009993 0 -0.003289, 0.009282 0 -0.003492, 0.008543 0 -0.00356, -0.008563 0 0.003561, -0.008563 0 -0.00356, -0.009302 0 -0.003492, -0.010013 0 -0.003289, -0.010668 0 -0.00296, -0.011242 0 -0.002517, -0.011713 0 -0.001978, -0.012063 0 -0.001362, -0.012279 0 -0.000694, -0.012352 0 0, -0.012279 0 0.000695, -0.012063 0 0.001363, -0.011713 0 0.001978, -0.011242 0 0.002518, -0.010668 0 0.002961, -0.010013 0 0.00329, -0.009302 0 0.003492, 0.008543 0 0.004674, 0.008543 0 -0.004673, -0.008563 0 0.004674, -0.008563 0 -0.004673, 0.008543 0.001605 0.004674, 0.008543 0.001605 -0.004673, -0.008563 0.001605 0.004674, -0.008563 0.001605 -0.004673
                  ]
                }
                coordIndex [
                  3, 0, 5, -1, 28, 29, 58, -1, 20, 106, 39, -1, 1, 3, 6, -1, 27, 28, 59, -1, 50, 1, 7, -1, 26, 27, 60, -1, 49, 50, 8, -1, 25, 26, 61, -1, 48, 49, 9, -1, 24, 25, 62, -1, 47, 48, 10, -1, 23, 24, 63, -1, 46, 47, 11, -1, 22, 23, 64, -1, 35, 37, 51, -1, 45, 46, 12, -1, 21, 22, 65, -1, 34, 35, 52, -1, 44, 45, 13, -1, 38, 21, 66, -1, 33, 34, 53, -1, 43, 44, 14, -1, 32, 33, 54, -1, 42, 43, 15, -1, 31, 32, 55, -1, 41, 42, 16, -1, 30, 31, 56, -1, 40, 41, 17, -1, 0, 2, 4, -1, 29, 30, 57, -1, 39, 40, 18, -1, 104, 51, 108, -1, 51, 37, 108, -1, 102, 106, 20, -1, 37, 39, 106, -1, 101, 4, 105, -1, 107, 36, 103, -1, 36, 107, 38, -1, 4, 2, 105, -1, 2, 38, 107, -1, 36, 100, 103, -1, 66, 100, 36, -1, 65, 100, 66, -1, 53, 86, 87, -1, 67, 68, 101, -1, 54, 87, 88, -1, 100, 65, 99, -1, 86, 53, 52, -1, 100, 84, 103, -1, 98, 63, 97, -1, 61, 96, 62, -1, 54, 53, 87, -1, 61, 95, 96, -1, 60, 95, 61, -1, 60, 94, 95, -1, 59, 94, 60, -1, 59, 93, 94, -1, 58, 92, 59, -1, 86, 52, 51, -1, 58, 91, 92, -1, 57, 91, 58, -1, 57, 90, 91, -1, 56, 90, 57, -1, 56, 89, 90, -1, 56, 55, 89, -1, 63, 62, 97, -1, 55, 54, 88, -1, 86, 51, 104, -1, 55, 88, 89, -1, 64, 63, 98, -1, 92, 93, 59, -1, 96, 97, 62, -1, 65, 64, 99, -1, 85, 86, 104, -1, 99, 64, 98, -1, 6, 68, 69, -1, 68, 5, 4, -1, 8, 70, 71, -1, 7, 6, 69, -1, 82, 83, 102, -1, 8, 7, 70, -1, 18, 17, 81, -1, 9, 8, 71, -1, 71, 72, 9, -1, 7, 69, 70, -1, 10, 72, 73, -1, 11, 10, 73, -1, 11, 73, 74, -1, 12, 11, 74, -1, 12, 74, 75, -1, 12, 75, 76, -1, 13, 12, 76, -1, 13, 76, 77, -1, 14, 13, 77, -1, 14, 77, 78, -1, 15, 14, 78, -1, 15, 78, 79, -1, 80, 16, 79, -1, 68, 6, 5, -1, 81, 17, 80, -1, 82, 18, 81, -1, 17, 16, 80, -1, 68, 4, 101, -1, 20, 82, 102, -1, 72, 10, 9, -1, 18, 82, 19, -1, 19, 82, 20, -1, 16, 15, 79, -1, 6, 3, 5, -1, 59, 28, 58, -1, 19, 20, 39, -1, 7, 1, 6, -1, 60, 27, 59, -1, 8, 50, 7, -1, 61, 26, 60, -1, 9, 49, 8, -1, 62, 25, 61, -1, 10, 48, 9, -1, 63, 24, 62, -1, 11, 47, 10, -1, 64, 23, 63, -1, 12, 46, 11, -1, 65, 22, 64, -1, 52, 35, 51, -1, 13, 45, 12, -1, 66, 21, 65, -1, 53, 34, 52, -1, 14, 44, 13, -1, 36, 38, 66, -1, 54, 33, 53, -1, 15, 43, 14, -1, 55, 32, 54, -1, 16, 42, 15, -1, 56, 31, 55, -1, 17, 41, 16, -1, 57, 30, 56, -1, 18, 40, 17, -1, 5, 0, 4, -1, 58, 29, 57, -1, 19, 39, 18, -1, 108, 37, 106, -1, 105, 2, 107, -1
                ]
                creaseAngle 1
              }
            }
          ]
        }
        %{ if v1 then }%
          DEF EPUCK_TURRET Transform {
            translation 0 0.0466 0.004
            scale 0.0128 0.0128 0.0128
            children [
              Shape {
              appearance PBRAppearance {
                baseColorMap ImageTexture {
                  url [
                    "textures/e-puck1_turret_base_color.jpg"
                  ]
                }
                roughnessMap ImageTexture {
                  url [
                    "textures/e-puck1_turret_roughness.jpg"
                  ]
                }
                metalnessMap ImageTexture {
                  url [
                    "textures/e-puck1_turret_metalness.jpg"
                  ]
                }
                normalMap ImageTexture {
                  url [
                    "textures/e-puck1_turret_normal.jpg"
                  ]
                }
                occlusionMap ImageTexture {
                  url [
                    "textures/e-puck1_turret_occlusion.jpg"
                  ]
                }
              }
                geometry IndexedFaceSet {
                  coord Coordinate {
                    point [ 0.419895 0.151244 2.421000 0.948889 0.151244 2.256830 1.435320 0.151244 1.971050 1.228590 0.151244 -0.710407 1.100900 0.151244 -1.014430 0.954969 0.151244 -1.184670 0.577985 0.151244 -1.482610 0.213162 0.151244 -1.640700 1.301550 0.151244 -2.376430 1.380600 0.151244 -2.467640 1.496130 0.151244 -2.516280 1.617740 0.151244 -2.498040 1.690700 0.151244 -2.418990 1.727180 0.151244 -2.309550 1.629900 0.151244 -2.078490 1.490050 0.151244 -2.048090 1.283310 0.151244 -2.266980 -0.419901 0.151244 2.421000 -1.100900 0.151244 -1.014430 -0.419901 0.151244 -1.579900 -0.213167 0.151244 -1.640690 -1.301550 0.151244 -2.376430 -1.380600 0.151244 -2.467640 -1.617740 0.151244 -2.498040 -1.690700 0.151244 -2.418990 -1.727180 0.151244 -2.309550 -1.629900 0.151244 -2.078490 -0.577991 0.151244 -1.482610 -0.954975 0.151244 -1.184670 -1.283310 0.151244 -2.266980 -1.490050 0.151244 -2.048090 -1.715020 0.151244 -2.181860 -1.496130 0.151244 -2.516280 -0.000003 0.151244 2.463560 -0.000003 0.151244 -1.652860 1.715020 0.151244 -2.181860 -1.435310 0.151244 1.971050 -0.948890 0.151244 2.256830 -1.228580 0.151244 -0.710411 0.419894 0.151244 -1.579900 ]
                  }
                  texCoord TextureCoordinate {
                    point [ 0.4979 0.0000 0.5862 0.0085 0.4097 0.0085 0.4097 0.0085 0.5862 0.0085 0.2986 0.0415 0.5862 0.0085 0.6973 0.0415 0.2986 0.0415 0.2986 0.0415 0.6973 0.0415 0.1964 0.0989 0.6973 0.0415 0.7995 0.0989 0.1964 0.0989 0.7995 0.0989 0.2398 0.6374 0.1964 0.0989 0.7995 0.0989 0.7561 0.6374 0.2398 0.6374 0.7561 0.6374 0.2666 0.6984 0.2398 0.6374 0.7561 0.6374 0.7293 0.6984 0.2666 0.6984 0.7293 0.6984 0.2973 0.7326 0.2666 0.6984 0.7293 0.6984 0.6986 0.7326 0.2973 0.7326 0.6986 0.7326 0.3765 0.7924 0.2973 0.7326 0.6986 0.7326 0.6194 0.7924 0.3765 0.7924 0.6194 0.7924 0.4097 0.8120 0.3765 0.7924 0.6194 0.7924 0.5862 0.8120 0.4097 0.8120 0.5427 0.8242 0.4979 0.8266 0.4532 0.8242 0.5862 0.8120 0.4532 0.8242 0.4097 0.8120 0.6194 0.7924 0.8110 0.9060 0.7676 0.9499 0.8609 0.9585 0.7880 0.9902 0.7676 0.9499 0.1350 0.9585 0.1849 0.9060 0.2283 0.9499 0.1849 0.9060 0.3765 0.7924 0.2283 0.9499 0.5427 0.8242 0.4532 0.8242 0.5862 0.8120 0.6194 0.7924 0.6986 0.7326 0.8110 0.9060 0.7714 0.9719 0.7676 0.9499 0.7880 0.9902 0.8110 0.9060 0.8404 0.9121 0.8583 0.9328 0.8583 0.9328 0.8609 0.9585 0.8110 0.9060 0.8532 0.9805 0.8379 0.9963 0.8123 1.0000 0.8123 1.0000 0.7880 0.9902 0.8532 0.9805 0.7676 0.9499 0.8110 0.9060 0.8609 0.9585 0.8609 0.9585 0.8532 0.9805 0.7880 0.9902 0.2283 0.9499 0.2245 0.9719 0.2079 0.9902 0.2079 0.9902 0.1836 1.0000 0.1427 0.9805 0.1580 0.9963 0.1427 0.9805 0.1836 1.0000 0.1350 0.9585 0.1376 0.9328 0.1849 0.9060 0.1555 0.9121 0.1849 0.9060 0.1376 0.9328 0.2283 0.9499 0.2079 0.9902 0.1350 0.9585 0.1427 0.9805 0.1350 0.9585 0.2079 0.9902 0.1849 0.9060 0.2973 0.7326 0.3765 0.7924 ]
                  }
                  texCoordIndex [ 0 1 2 -1 3 4 5 -1 6 7 8 -1 9 10 11 -1 12 13 14 -1 15 16 17 -1 18 19 20 -1 21 22 23 -1 24 25 26 -1 27 28 29 -1 30 31 32 -1 33 34 35 -1 36 37 38 -1 39 40 41 -1 42 43 44 -1 45 46 47 -1 48 49 50 -1 51 52 53 -1 54 55 56 -1 57 58 59 -1 60 61 62 -1 63 64 65 -1 66 67 68 -1 69 70 71 -1 72 73 74 -1 75 76 77 -1 78 79 80 -1 81 82 83 -1 84 85 86 -1 87 88 89 -1 90 91 92 -1 93 94 95 -1 96 97 98 -1 99 100 101 -1 102 103 104 -1 105 106 107 -1 108 109 110 -1 111 112 113 -1 ]
                  coordIndex [ 33 0 17 -1 17 0 37 -1 0 1 37 -1 37 1 36 -1 1 2 36 -1 2 38 36 -1 2 3 38 -1 3 18 38 -1 3 4 18 -1 4 28 18 -1 4 5 28 -1 5 27 28 -1 5 6 27 -1 6 19 27 -1 6 39 19 -1 7 34 20 -1 39 20 19 -1 6 15 16 -1 13 9 16 -1 25 30 29 -1 30 27 29 -1 7 20 39 -1 6 5 15 -1 8 16 9 -1 15 14 35 -1 35 13 15 -1 12 11 10 -1 10 9 12 -1 16 15 13 -1 13 12 9 -1 29 21 22 -1 22 32 24 -1 23 24 32 -1 25 31 30 -1 26 30 31 -1 29 22 25 -1 24 25 22 -1 30 28 27 -1 ]
                  creaseAngle 0.785398
                }
              }
              Shape {
                appearance USE EPUCK_SIDE_PRINT_APPEARANCE
                geometry IndexedFaceSet {
                  coord Coordinate {
                    point [
                      0.419895 0.151244 2.421 0.948889 0.151244 2.25683 1.43532 0.151244 1.97105 1.22859 0.151244 -0.710407 1.1009 0.151244 -1.01443 0.954969 0.151244 -1.18467 0.603673 0.151244 -1.46549 0.419895 0.151244 -1.56421 0.213162 0.151244 -1.62501 1.30155 0.151244 -2.37643 1.3806 0.151244 -2.46764 1.49613 0.151244 -2.51628 1.61774 0.151244 -2.49804 1.6907 0.151244 -2.41899 1.72718 0.151244 -2.30955 1.6299 0.151244 -2.07849 1.49005 0.151244 -2.04809 1.2914 0.151244 -2.2132 -0.419901 0.151244 2.421 -1.1009 0.151244 -1.01443 -0.419901 0.151244 -1.56421 -0.213167 0.151244 -1.625 -1.30155 0.151244 -2.37643 -1.3806 0.151244 -2.46764 -1.61774 0.151244 -2.49804 -1.6907 0.151244 -2.41899 -1.72718 0.151244 -2.30955 -1.6299 0.151244 -2.07849 -0.624158 0.151244 -1.44904 -0.954975 0.151244 -1.18467 -0.419901 0.0012444 2.421 -1.1009 0.0012443 -1.01443 -0.954975 0.0012443 -1.18467 -0.624158 0.0012443 -1.44904 -0.419901 0.0012443 -1.56421 -1.6299 0.0012442 -2.07849 -1.72718 0.0012442 -2.30955 -1.6907 0.0012442 -2.41899 -1.61774 0.0012442 -2.49804 1.2914 0.0012442 -2.2132 1.30155 0.0012442 -2.37643 1.3806 0.0012442 -2.46764 1.49613 0.0012442 -2.51628 1.61774 0.0012442 -2.49804 1.6907 0.0012442 -2.41899 1.72718 0.0012442 -2.30955 1.6299 0.0012442 -2.07849 1.49005 0.0012442 -2.04809 0.603723 0.0012943 -1.46554 0.954969 0.0012443 -1.18467 1.1009 0.0012443 -1.01443 1.22859 0.0012443 -0.710407 1.43532 0.0012444 1.97105 0.948889 0.0012444 2.25683 0.419895 0.0012444 2.421 -1.28751 0.0012442 -2.21662 -1.49005 0.0012442 -2.04809 -1.30155 0.0012442 -2.37643 -1.71502 0.0012442 -2.18186 -1.49613 0.0012442 -2.51628 -1.3806 0.0012442 -2.46764 3.054e-05 0.0012778 2.46353 3.05623e-05 0.0012776 -1.6372 1.71502 0.0012442 -2.18186 -1.28751 0.151244 -2.21662 -1.49005 0.151244 -2.04809 -1.71502 0.151244 -2.18186 -1.49613 0.151244 -2.51628 -2.83867e-06 0.151244 2.46356 -2.84612e-06 0.151244 -1.63717 1.71502 0.151244 -2.18186 -1.43531 0.151244 1.97105 -0.94889 0.0012444 2.25683 -0.94889 0.151244 2.25683 -1.22858 0.151244 -0.710411 -1.22858 0.0012443 -0.710411 -1.43526 0.0012794 1.97099 -0.213167 0.0012443 -1.625 0.213158 0.0012443 -1.625 0.419945 0.0012943 -1.56426 0.419894 0.151244 -1.56421 0.213154 0.151244 -1.625
                    ]
                  }
                  coordIndex [
                    77, 78, 79, -1, 81, 80, 79, 78, -1, 52, 53, 76, -1, 53, 72, 76, -1, 53, 54, 72, -1, 54, 30, 72, -1, 75, 76, 71, -1, 74, 75, 71, -1, 22, 64, 55, 57, -1, 23, 22, 57, 60, -1, 23, 60, 59, 67, -1, 34, 20, 21, 77, -1, 33, 28, 20, 34, -1, 31, 19, 29, 32, -1, 75, 74, 19, 31, -1, 30, 18, 73, 72, -1, 61, 68, 18, 30, -1, 54, 0, 68, 61, -1, 53, 1, 0, 54, -1, 52, 2, 1, 53, -1, 51, 3, 2, 52, -1, 50, 4, 3, 51, -1, 49, 5, 4, 50, -1, 79, 7, 6, 48, -1, 62, 69, 8, 78, -1, 77, 21, 69, 62, -1, 47, 16, 5, 49, -1, 48, 6, 17, 39, -1, 46, 15, 16, 47, -1, 63, 70, 15, 46, -1, 45, 14, 70, 63, -1, 44, 13, 14, 45, -1, 43, 12, 13, 44, -1, 42, 11, 12, 43, -1, 41, 10, 11, 42, -1, 40, 9, 10, 41, -1, 39, 17, 9, 40, -1, 38, 24, 67, 59, -1, 37, 25, 24, 38, -1, 36, 26, 25, 37, -1, 58, 66, 26, 36, -1, 35, 27, 66, 58, -1, 56, 65, 27, 35, -1, 32, 29, 65, 56, -1, 55, 64, 28, 33, -1, 39, 47, 49, 48, -1, 40, 41, 42, 43, 44, 45, 63, 46, 47, 39, -1, 55, 56, 35, 58, 36, 37, 38, 59, 60, 57, -1, 33, 32, 56, 55, -1, 51, 52, 75, -1, 75, 52, 76, -1, 54, 61, 30, -1, 62, 78, 77, -1, 77, 78, 79, -1, 77, 79, 34, -1, 79, 48, 34, -1, 34, 48, 33, -1, 48, 49, 33, -1, 33, 49, 32, -1, 49, 50, 32, -1, 32, 50, 31, -1, 50, 51, 31, -1, 31, 51, 75, -1, 76, 72, 73, 71, -1
                  ]
                  creaseAngle 0.785398
                }
              }
            ]
          }
        %{ end }%
        DEF EPUCK_RIGHT_COLUMN Transform {
          translation 0.0193 0.0426 -0.0254
          children [
            DEF EPUCK_COLUMN Shape {
              appearance PBRAppearance {
                roughness 0.2
              }
              geometry Cylinder {
                height 0.014
                radius 0.00225
              }
            }
          ]
        }
        DEF EPUCK_LEFT_COLUMN Transform {
          translation -0.0193 0.0426 -0.0254
          children [
            USE EPUCK_COLUMN
          ]
        }
        DEF EPUCK_REAR_COLUMN Transform {
          translation 0 0.0426 0.032
          children [
            USE EPUCK_COLUMN
          ]
        }
          DEF EPUCK_RIGHT_CONNECTOR Transform {
            translation 0.0033 0.0426 0.0033
            children [
              DEF EPUCK_CONNECTOR Shape {
                appearance PBRAppearance {
                  baseColor 0 0 0
                  roughness 0.4
                  metalness 0
                }
                geometry Box {
                  size 0.005 0.008 0.02
                }
              }
            ]
          }
          DEF EPUCK_LEFT_CONNECTOR Transform {
            translation -0.012 0.0426 0.0024
            children [
              DEF EPUCK_CONNECTOR Shape {
                appearance PBRAppearance {
                  baseColor 0 0 0
                  roughness 0.4
                  metalness 0
                }
                geometry Box {
                  size 0.005 0.008 0.02
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
                  transparency 0.4
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
                      "textures/gctronic_logo.png"
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
              }
            ]
          }
          DEF EPUCK_RECEIVER Receiver {
            channel IS receiver_channel
          }
          DEF EPUCK_EMITTER Emitter {
            channel IS emitter_channel
          }
          

          
        """
    
    closeBracket = "\n\t\t}\n"
    
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
                continue
        else:
            # If there should only be one component
            # Skip if count is > 1
            if component_count > 1:
                continue
                
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
                        appearance DEF EPUCK_TRANSPARENT_APPEARANCE PBRAppearance {{
                        baseColor 0.5 0.5 0.5
                        transparency 0.4
                        roughness 0.5
                        metalness 0
                        }}
                        geometry Cylinder {{
                        height 0.003
                        radius 0.02
                        subdivision 24
                        }}
                    }}
                    Transform {{
                        translation 0 0.0016 0
                        children [
                        Shape {{
                            appearance PBRAppearance {{
                            metalness 0
                            roughness 0.4
                            baseColorMap ImageTexture {{
                                url [
                                "textures/gctronic_logo.png"
                                ]
                            }}
                            }}
                            geometry IndexedFaceSet {{
                            coord Coordinate {{
                                point [
                                -0.014 0 -0.014 -0.014 0 0.014 0.014 0 0.014 0.014 0 -0.014
                                ]
                            }}
                            texCoord TextureCoordinate {{
                                point [
                                0 0 1 0 1 1 0 1
                                ]
                            }}
                            coordIndex [
                                0, 1, 2, 3
                            ]
                            texCoordIndex [
                                0, 1, 2, 3
                            ]
                            }}
                        }}
                        ]
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
                    }}
                    Transform {{
                        translation 0 0.0035 0
                        children [
                        Shape {{
                            appearance USE EPUCK_TRANSPARENT_APPEARANCE
                            geometry Cylinder {{
                            height 0.004
                            radius 0.005
                            }}
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
                    mass 0.005
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
            SpotLight {{
            attenuation      0 0 12.56
            intensity   0.01
            location    {x} {y} {z}
            direction   0 -1 0
            cutOffAngle 0.3
            }}
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
          Transform {
            translation 0 0.0051 0
            children [
              Box {
                size 0.04 0.01 0.05
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
    

    path = os.path.dirname(os.path.abspath(__file__))

    if path[-4:] == "game":
      path = os.path.join(path, "protos")
    else:
      path = os.path.join(path, "../../protos")

    path = os.path.join(path, "custom_robot.proto")

    with open(path, 'w') as robot_file:
        robot_file.write(proto_code)


def process_robot_json(json_data):
    '''Process json file to generate robot file'''
    robot_json = json.loads(json_data)
    generate_robot_proto(robot_json)

# -------------------------------
# CODED LOADED BEFORE GAME STARTS

if __name__ == '__main__':

    if supervisor.getCustomData() != '':
        maxTime = int(supervisor.getCustomData())
        supervisor.wwiSendText("update," + str(0) + "," + str(0) + "," + str(maxTime))
    
    # Load settings
    # configData
    # [0]: Keep controller/robot files
    # [1]: Disable auto LoP

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

    # How long the game has been running for
    timeElapsed = 0
    lastTime = -1

    # Send message to robot window to perform setup
    supervisor.wwiSendText("startup")

    # For checking the first update with the game running
    first = True

    receiver = supervisor.getDevice('receiver')
    receiver.enable(32)
    
    emitter = supervisor.getDevice('emitter')

    # Init robot as object to hold their info
    robot0Obj = Robot()

    lastSentScore = 0
    lastSentTime = 0

    #Calculate the solution arrays for the map layout
    #Can be moved to another location - only here for testingwe
    mapSolution = mapSolutionCalculator.convertTilesToArray(getTiles(grid=True))
    areaCount = sum(1 for m in mapSolution if len(m)!=0)
    
    # -------------------------------

    # Until the match ends (also while paused)
    while simulationRunning or last == True:
        
        if last == True:
            last = -1
            finished = True
        
        r0 = False
        r0s = False

        # The first frame of the game running only
        if first and currentlyRunning:
            # Get the robot nodes by their DEF names
            robot0 = supervisor.getFromDef("ROBOT0")
            # Add robot into world
            add_robot()
            # Init robot as object to hold their info
            robot0Obj = Robot(robot0)
            # Set robots starting position in world
            set_robot_start_pos()
            robot0Obj.inSimulation = True

            # Reset physics
            robot0.resetPhysics()


            # Restart controller code
            # robot0.restartController()
            first = False

            #robot0Obj.increaseScore("Debug", 100)

        if robot0Obj.inSimulation:
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
                    # Update history
                    robot0Obj.history.enqueue("Entered swamp")
                else:
                    # If not in swamp, reset max velocity to default
                    robot0Obj.setMaxVelocity(DEFAULT_MAX_VELOCITY)

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
                    elif rDataLen == 8:
                      #Check map answer
                      tup = struct.unpack('c i', receivedData)
                      robot0Obj.message = [tup[0].decode("utf-8"), tup[1]]
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
                        map_data = struct.unpack(f'{shape_size}i',data_bytes)
                        # Reshape data using the shape data given
                        reshaped_data = np.array(map_data).reshape(shape, order='f')
                        
                        robot0Obj.map_data = reshaped_data
                except:
                    print("Incorrect data format sent")

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
                          robot0Obj.increaseScore("Exit bonus", robot0Obj.getScore() * 0.1)
                        else:
                          robot0Obj.history.enqueue("No exit bonus")
                        add_map_multiplier()
                        # Update score and history
                        robot_quit(robot0Obj, 0, False)
                            
                    elif r0_message[0] == 'M':
                        try:
                          # If map_data submitted
                          if robot0Obj.map_data.size != 0:
                            area = r0_message[1]
                            # If not previously evaluated
                            if not robot0Obj.sent_maps[area-1]: 
                              #robot0Obj.history.enqueue("Map entry successful")
                              if area == 1:
                                map_score = MapScorer.calculateScore(mapSolution[0], robot0Obj.map_data)
                              elif area == 2:
                                map_score = MapScorer.calculateScore(mapSolution[1], robot0Obj.map_data)
                              elif area == 3:
                                map_score = MapScorer.calculateScore(mapSolution[2], robot0Obj.map_data)
                              else:
                                print("Map scoring error. Please check your code.")
                                                      
                              robot0Obj.history.enqueue(f"Map Correctness (Area{area}) {str(round(map_score * 100,1))}%")
                              
                              # Add percent
                              robot0Obj.map_score_percent += map_score
                              robot0Obj.sent_maps[area-1] = True
                              
                              robot0Obj.map_data = np.array([])
                              # Do something...
                            else:
                              print(f"The map of area {area} has already been evaluated.")
                          else:
                            print("Please send your map data before hand.")
                        except:
                          print("Map scoring error. Please check your code. (except)")

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

            # Relocate robot if stationary for 20 sec
            if robot0Obj.timeStopped() >= 20 and not finished:
                if not configData[1]:
                  relocate(robot0, robot0Obj)
                robot0Obj.robot_timeStopped = 0
                robot0Obj.stopped = False
                robot0Obj.stoppedTime = None

            if robot0Obj.position[1] < -0.035 and currentlyRunning and not finished:
                if not configData[1]:
                  relocate(robot0, robot0Obj)
                robot0Obj.robot_timeStopped = 0
                robot0Obj.stopped = False
                robot0Obj.stoppedTime = None
            

            if currentlyRunning:
                # Check if robot has not left the starting tile
                if not robot0Obj.left_exit_tile:
                    # Check robot position is on starting tile
                    if not robot0Obj.startingTile.checkPosition(robot0Obj.position):
                        robot0Obj.left_exit_tile = True
                        robot0Obj.startingTile.wb_node.getField("start").setSFBool(False)


            # Send the update information to the robot window
            nowScore = robot0Obj.getScore()
            if lastSentScore != nowScore or lastSentTime != int(timeElapsed):
                supervisor.wwiSendText("update," + str(round(nowScore,2)) + "," + str(int(timeElapsed)) + "," + str(maxTime))
                lastSentScore = nowScore
                lastSentTime = int(timeElapsed)

            # If the time is up
            if timeElapsed >= maxTime and last != -1:
                add_map_multiplier()
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
                    lastTime = supervisor.getTime()
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
                        resetRobotProto()

                if parts[0] == 'relocate':
                    data = message.split(",", 1)
                    if len(data) > 1:
                        if int(data[1]) == 0:
                            relocate(robot0, robot0Obj)

                if parts[0] == 'quit':
                    data = message.split(",", 1)
                    if len(data) > 1:
                        if int(data[1]) == 0:
                            if gameStarted:
                                robot_quit(robot0Obj, 0, True)
                
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
        if currentlyRunning and not finished:
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
                if  timeElapsed > 0:
                  #write log for game if the game ran for more than 0 seconds
                  write_log()
        elif first or last or finished:
            supervisor.step(32)            