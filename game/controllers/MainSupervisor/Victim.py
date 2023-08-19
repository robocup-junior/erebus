from overrides import override
import numpy.typing as npt
import numpy as np
from abc import ABC, abstractmethod
import math
import AutoInstall

from controller import Node
from controller import Field
from controller import Supervisor

from Robot import Robot
from Camera import FollowSide

AutoInstall._import("np", "numpy")

AutoInstall._import("overrides", "overrides")


def rotate_2d_vector(v: npt.NDArray, theta: float) -> npt.NDArray:
    """Rotate 2D vector by angle (in radians)

    Args:
        v (np.array): Vector to rotate
        theta (float): Angle to rotate by (in radians)

    Returns:
        np.array: Output rotated angle
    """
    rot_matrix = np.array([[math.cos(theta), -math.sin(theta)],
                           [math.sin(theta), math.cos(theta)]])
    return np.dot(rot_matrix, v)


def normalise_vector(v: npt.NDArray) -> npt.NDArray:
    """Normalise vector

    Args:
        v (np.array): Vector to normalise

    Returns:
        np.array: Normalised vector
    """
    return v / np.linalg.norm(v)


class VictimObject(ABC):
    """Abstract object holding data about Victim/Hazard maps within the world
    """

    def __init__(self, node: Node, victim_type: str, score: int):
        """Initialises a new VictimObject, representing a Victim or Hazard
        within the world.
    
        Args:
            node (Node): Webots node associated with the victim
            victim_type (str): Victim type (e.g. Harmed, F, etc.)
            score (int): Score worth of the victim on identification
            (e.g. 10 or 20)
        """
        
        self.wb_node: Node = node

        self.score_worth: int = score
        self._victim_type: str = victim_type
        self.simple_victim_type: str = self.get_simple_type()

        self.wb_translation_field: Field = self.wb_node.getField('translation')
        self._wb_rotation_field: Field = self.wb_node.getField('rotation')
        self._wb_type_field: Field = self.wb_node.getField('type')
        self._wb_found_field: Field = self.wb_node.getField('found')

    @property
    def position(self) -> list[float]:
        return self.wb_translation_field.getSFVec3f()

    @position.setter
    def position(self, pos: list[float]) -> None:
        self.wb_translation_field.setSFVec3f(pos)

    @property
    def rotation(self) -> list[float]:
        return self._wb_rotation_field.getSFRotation()

    @rotation.setter
    def rotation(self, pos: list[float]) -> None:
        self._wb_rotation_field.setSFRotation(pos)

    @property
    def victim_type(self) -> str:
        return self._wb_type_field.getSFString()

    @victim_type.setter
    def victim_type(self, v_type: str):
        self._wb_type_field.setSFString(v_type)

    @property
    def identified(self) -> bool:
        return self._wb_found_field.getSFBool()

    @identified.setter
    def identified(self, found: bool):
        self._wb_found_field.setSFBool(found)

    @abstractmethod
    def get_simple_type(self) -> str:
        """Gets the simple victim type string (e.g. Harmed = 'H')

        Returns:
            str: Simplified type as char
        """
        ...

    def check_position(self, pos: list[float], radius: float = 0.09) -> bool:
        """Check if a position is within a specified radius of the victim

        Args:
            pos (list[float]): Position to check
            radius (float, optional): Radius of search. Defaults to 0.09.

        Returns:
            bool: Whether the given position is within the specified range of 
            the victim 
        """
        # Get distance from the object to the passed position
        distance = math.sqrt(
            ((self.position[0] - pos[0])**2) +
            ((self.position[2] - pos[2])**2)
        )
        return distance <= radius

    def get_distance(self, pos: list[float]) -> float:
        """Gets the distance of a specific position from the victim

        Args:
            pos (list[float]): Position to check

        Returns:
            float: Distance from victim, in meters
        """
        return math.sqrt(
            ((self.position[0] - pos[0])**2) +
            ((self.position[2] - pos[2])**2)
        )

    def get_surface_normal(self) -> npt.NDArray:
        """Gets the victim's webots object surface normal vector

        Returns:
            npt.NDArray: Normalised surface normal vector
        """
        # Angle of 0 (no rotation), e.g. [0,0,0,0], points upwards, therefore
        # has surface normal of [0,0,-1]

        # Rotate by rotation of victim
        rot: npt.NDArray = rotate_2d_vector(np.array([0, -1]), 
                                            -self.rotation[3])
        # Convert back to 3d vector
        return np.array([rot[0], 0, rot[1]])

    def _get_vec_to_robot(self, robot: Robot) -> npt.NDArray:
        """Get normalised direction vector from victim to robot

        Args:
            robot (Robot): Robot object

        Returns:
            npt.NDArray: Normalised vector pointing to robot direction
        """
        vec: npt.NDArray = np.array(robot.position) - np.array(self.position)
        # Normalise vector
        return normalise_vector(vec)

    def on_same_side(self, robot: Robot) -> bool:
        """Checks if the robot is on the same side parallel to the rotated 
        victim

        Args:
            robot (Robot): Robot object

        Returns:
            bool: True if the robot is on the same side as the victim
        """
        norm: npt.NDArray = self.get_surface_normal()
        to_bot: npt.NDArray = self._get_vec_to_robot(robot)
        # https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
        angle: float = np.arccos(np.clip(np.dot(norm, to_bot), -1.0, 1.0))
        # Return if angle between two vectors is less than 90 degrees
        return angle < math.pi/2

    def get_side(self) -> FollowSide:
        """Gets the (rought) side the victim is facing

        Returns:
            FollowSide: Enum of the side the victim is (roughly) facing
        """
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
    """Victim object holding data about a Victim (Human) within the world
    """

    HARMED: str = 'harmed'
    UNHARMED: str = 'unharmed'
    STABLE: str = 'stable'

    VICTIM_TYPES: list[str] = [HARMED, UNHARMED, STABLE]

    @override
    def get_simple_type(self) -> str:
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
    """HazardMap object holding data about a Hazard within the world
    """

    HAZARD_TYPES: list[str] = ['F', 'P', 'C', 'O']

    @override
    def get_simple_type(self) -> str:
        return self._victim_type


class VictimManager():
    """VictimManager Object for managing Hazards and Victims actions within the
    simulation
    """
    
    def __init__(self):
        """Initialises a new VictimManager object to manage both Hazards and 
        Victims
        """
        self._num_humans: int = 0
        self._num_hazards: int = 0

        self.humans: list[Victim] = []
        self.hazards: list[HazardMap] = []

    def get_humans(self, supervisor: Supervisor):
        """Gets and initialises all Victim objects from the simulation world

        Args:
            supervisor (Supervisor): Supervisor object
        """

        self._num_humans = (
            supervisor.getFromDef('HUMANGROUP')
            .getField("children")
            .getCount()
        )

        victim_nodes: Field = (
            supervisor.getFromDef('HUMANGROUP')
            .getField("children")
        )
        # Iterate for each human
        for i in range(self._num_humans):
            # Get each human from children field in the human root
            # node HUMANGROUP
            human: Node = victim_nodes.getMFNode(i) # type: ignore

            victim_type: str = human.getField('type').getSFString()
            score_worth: int = human.getField('scoreWorth').getSFInt32()

            # Create victim Object from node info
            victim: Victim = Victim(human, victim_type, score_worth)
            self.humans.append(victim)

    def get_hazards(self, supervisor: Supervisor):
        """Gets and initialises all Hazard objects from the simulation world

        Args:
            supervisor (Supervisor): Supervisor object
        """

        self._num_hazards = (
            supervisor.getFromDef('HAZARDGROUP')
            .getField("children")
            .getCount()
        )

        hazard_nodes: Field = (
            supervisor.getFromDef('HAZARDGROUP')
            .getField("children")
        )

        # Iterate for each hazard
        for i in range(self._num_hazards):
            # Get each hazard from children field in the hazard root node 
            # HAZARDGROUP
            human: Node = hazard_nodes.getMFNode(i) # type: ignore

            hazard_type: str = human.getField('type').getSFString()
            score_worth: int = human.getField('scoreWorth').getSFInt32()

            # Create hazard Object from node info
            hazard: HazardMap = HazardMap(human, hazard_type, score_worth)
            self.hazards.append(hazard)

    def reset_victim_textures(self):
        """Resets all Victim and Hazard textures to unidentified
        """
        # Iterate for each victim
        for i in range(self._num_humans):
            self.humans[i].identified = False
        for i in range(self._num_hazards):
            self.hazards[i].identified = False
