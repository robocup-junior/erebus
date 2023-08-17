from abc import abstractmethod
import math
import AutoInstall
from Robot import Robot
from ConsoleLog import Console
from Camera import FollowSide

AutoInstall._import("np", "numpy")


def rotate_2d_vector(
    v: np.array, 
    theta: float
) -> np.array:
    """Rotate 2D vector by angle (in radians)

    Args:
        v (np.array): Vector to rotate
        theta (float): Angle to rotate by (in radias)

    Returns:
        np.array: Output rotated angle
    """
    rot_matrix = np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
    return np.dot(rot_matrix, v)

def normalise_vector(v: np.array) -> np.array:
    """Normalise vector

    Args:
        v (np.array): Vector to normalise

    Returns:
        np.array: Normalised vector
    """
    return v / np.linalg.norm(v)

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
    def position(self) -> list[float]:
        return self.wb_translationField.getSFVec3f()

    @position.setter
    def position(self, pos: list) -> None:
        self.wb_translationField.setSFVec3f(pos)

    @property
    def rotation(self) -> list[float]:
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

    @abstractmethod
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
    
    def get_surface_normal(self) -> np.array:  
        """Gets the victim's webots object surface normal vector
        """
        # Angle of 0 (no rotation), e.g. [0,0,0,0], points upwards, therefore
        # has surface normal of [0,0,-1]
        
        # Rotate by rotation of victim
        rot: np.array = rotate_2d_vector(np.array([0,-1]), -self.rotation[3]) 
        # Convert back to 3d vector
        return np.array([rot[0], 0, rot[1]])
    
    def _get_vec_to_robot(
        self, 
        robot: Robot
    ) -> np.array:
        """Get normalised direction vector from victim to robot

        Args:
            robot (Robot): Robot object

        Returns:
            np.array: Normalised vector pointing to robot direction
        """
        vec: np.array = np.array(robot.position) - np.array(self.position)
        # Normalise vector
        return normalise_vector(vec)
    
    def on_same_side(
        self, 
        robot: Robot
    ) -> bool:
        """Check if a robot is on the same side as the victim is facing

        Args:
            robot (Robot): Robot object

        Returns:
            bool: True if the robot is on the same side as the victim
        """
        norm: np.array = self.get_surface_normal()
        to_bot: np.array = self._get_vec_to_robot(robot)
        # https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
        angle: float = np.arccos(np.clip(np.dot(norm, to_bot), -1.0, 1.0))
        # Return if angle between two vectors is less than 90 degrees
        return angle < math.pi/2

    def get_side(self) -> FollowSide:
        # Get side the victim pointing at
        rot: float = round(self.rotation[3], 2)

        # TODO These aren't accurate with more complex victim rotations
        if rot == -1.57:
            return FollowSide.RIGHT
        elif rot == 1.57:
            return FollowSide.LEFT
        elif rot == 3.14:
            return FollowSide.BOTTOM
        return FollowSide.TOP

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