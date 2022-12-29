

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
        
        
class TileManager():
    # Room multipliers
    ROOM_MULT = [1, 1.25, 1.5, 2]
    SWAMP_SLOW_MULT = 0.32
    
    def __init__(self):
        self.numberOfSwamps = 0
        self.numberOfCheckpoints = 0
        
        self.checkpoints = []
        self.swamps = []
    
    def getSwamps(self, supervisor):
        '''Get swamps in simulation'''
        self.numberOfSwamps = supervisor.getFromDef('SWAMPBOUNDS').getField('children').getCount()
        # Iterate for each swamp
        for i in range(self.numberOfSwamps):
            # Get the swamp minimum node and translation
            swampMin = supervisor.getFromDef("swamp" + str(i) + "min")
            minPos = swampMin.getField("translation")
            # Get maximum node and translation
            swampMax = supervisor.getFromDef("swamp" + str(i) + "max")
            maxPos = swampMax.getField("translation")
            # Get the vector positions
            minPos = minPos.getSFVec3f()
            maxPos = maxPos.getSFVec3f()

            centerPos = [(maxPos[0]+minPos[0])/2, maxPos[1],
                        (maxPos[2]+minPos[2])/2]
            # Create a swamp object using the min and max (x,z)
            swampObj = Swamp([minPos[0], minPos[2]], [maxPos[0], maxPos[2]], centerPos)
            self.swamps.append(swampObj)
            
    def getCheckpoints(self, supervisor):
        '''Get checkpoints in simulation'''
        self.numberOfCheckpoints = supervisor.getFromDef('CHECKPOINTBOUNDS').getField('children').getCount()
        # Iterate for each checkpoint
        for i in range(self.numberOfCheckpoints):
            # Get the checkpoint minimum node and translation
            checkpointMin = supervisor.getFromDef("checkpoint" + str(i) + "min")
            minPos = checkpointMin.getField("translation")
            # Get maximum node and translation
            checkpointMax = supervisor.getFromDef("checkpoint" + str(i) + "max")
            maxPos = checkpointMax.getField("translation")
            # Get the vector positions
            minPos = minPos.getSFVec3f()
            maxPos = maxPos.getSFVec3f()

            centerPos = [(maxPos[0]+minPos[0])/2, maxPos[1],
                        (maxPos[2]+minPos[2])/2]
            # Create a checkpoint object using the min and max (x,z)
            checkpointObj = Checkpoint([minPos[0], minPos[2]], [
                                    maxPos[0], maxPos[2]], centerPos)
            self.checkpoints.append(checkpointObj)
            
    def coord2grid(self, xzCoord, supervisor):
        side = 0.3 * supervisor.getFromDef("START_TILE").getField("xScale").getSFFloat()
        height = supervisor.getFromDef("START_TILE").getField("height").getSFFloat()
        width = supervisor.getFromDef("START_TILE").getField("width").getSFFloat()
        return int(round((xzCoord[0] + (width / 2 * side)) / side, 0) * height + round((xzCoord[2] + (height / 2 * side)) / side, 0))

    
    def updateCheckpoints(self, robotObj, checkpoint, supervisor):
        robotObj.lastVisitedCheckPointPosition = checkpoint.center
        alreadyVisited = False

        # Dont update if checkpoint is already visited
        if not any([c == checkpoint.center for c in robotObj.visitedCheckpoints]):
            # Update robot's points and history
            robotObj.visitedCheckpoints.append(checkpoint.center)
            grid = self.coord2grid(checkpoint.center, supervisor)
            roomNum = supervisor.getFromDef("WALLTILES").getField("children").getMFNode(grid).getField("room").getSFInt32() - 1
            robotObj.increaseScore("Found checkpoint", 10, supervisor, multiplier=TileManager.ROOM_MULT[roomNum])
            
    def updateInSwamp(self, robotObj, inSwamp, max_velocity, supervisor):
        # Check if robot is in swamp
        if robotObj.inSwamp != inSwamp:
            robotObj.inSwamp = inSwamp
            if robotObj.inSwamp:
                # Cap the robot's velocity to 2
                # robotObj.setMaxVelocity(2)
                robotObj.setMaxVelocity(TileManager.SWAMP_SLOW_MULT)
                # Reset physics
                robotObj.wb_node.resetPhysics()
                # Update history
                robotObj.history.enqueue("Entered swamp", supervisor)
            else:
                # If not in swamp, reset max velocity to default
                # robotObj.setMaxVelocity(max_velocity)
                robotObj.setMaxVelocity(max_velocity)
                # Reset physics
                robotObj.wb_node.resetPhysics()
                # Update history
                robotObj.history.enqueue("Exited swamp,", supervisor)
            