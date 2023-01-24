import math


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
        # Will be overrided
        pass

    def checkPosition(self, pos: list, radius:float = 0.09) -> bool:
        '''Check if a position is near an object, based on the min_dist value'''
        # Get distance from the object to the passed position using manhattan distance for speed
        distance = math.sqrt(((self.position[0] - pos[0])**2) + ((self.position[2] - pos[2])**2))
        return distance <= radius
    
    def getDistance(self, pos: list):
        return math.sqrt(((self.position[0] - pos[0])**2) + ((self.position[2] - pos[2])**2))
        
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
        else:
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
    
    
class VictimManager():
    def __init__(self):
        self.numberOfHumans = 0
        self.numberOfHazards = 0
        
        self.humans = []
        self.hazards = []
    
    
    def getHumans(self, supervisor):
        '''Get humans in simulation'''
        self.numberOfHumans = supervisor.getFromDef('HUMANGROUP').getField("children").getCount()
        humanNodes = supervisor.getFromDef('HUMANGROUP').getField("children")
        # Iterate for each human
        for i in range(self.numberOfHumans):
            # Get each human from children field in the human root node HUMANGROUP
            human = humanNodes.getMFNode(i)

            victimType = human.getField('type').getSFString()
            scoreWorth = human.getField('scoreWorth').getSFInt32()

            # Create victim Object from victim position
            humanObj = Victim(human, i, victimType, scoreWorth)
            self.humans.append(humanObj)


    def getHazards(self, supervisor):
        '''Get hazards in simulation'''
        self.numberOfHazards = supervisor.getFromDef('HAZARDGROUP').getField("children").getCount()
        hazardNodes = supervisor.getFromDef('HAZARDGROUP').getField("children")
        # Iterate for each hazard
        for i in range(self.numberOfHazards):
            # Get each hazard from children field in the hazard root node HAZARDGROUP
            human = hazardNodes.getMFNode(i)

            hazardType = human.getField('type').getSFString()
            scoreWorth = human.getField('scoreWorth').getSFInt32()

            # Create hazard Object from hazard position
            hazardObj = HazardMap(human, i, hazardType, scoreWorth)
            self.hazards.append(hazardObj)
    
    def resetVictimsTextures(self):
        # Iterate for each victim
        for i in range(self.numberOfHumans):
            self.humans[i].identified = False
        for i in range(self.numberOfHazards):
            self.hazards[i].identified = False