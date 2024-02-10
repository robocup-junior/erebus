from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from controller import Supervisor
from controller import Node

from typing import TYPE_CHECKING

from ConsoleLog import Console
from ErebusObject import ErebusObject

if TYPE_CHECKING:
    from MainSupervisor import Erebus


class Tile(ABC):
    """Abstract Tile object holding boundary data"""

    @abstractmethod
    def __init__(
        self,
        min: tuple[float, float],
        max: tuple[float, float],
        center: tuple[float, float, float]
    ) -> None:
        """WARNING: This is an abstract class. Use `Checkpoint`, `Swamp` or
        `StartTile`

        Initialize min/max bounds of the tile, along with it's center 
        position

        Args:
            min (tuple[float, float]): Minimum x,y position
            max (tuple[float, float]): Maximum x,y position
            center (tuple[float, float, float]): Center x,y,z position
        """

        self.min: tuple[float, float] = min
        self.max: tuple[float, float] = max
        self.center: tuple[float, float, float] = center

    def check_position(self, pos: list[float]) -> bool:
        """Check if a 3D position within the bounds of this tile

        Args:
            pos (list[float]): x,y,z position

        Returns:
            bool: True if within the tile bounds, False otherwise
        """
        # If the x position is within the bounds
        if pos[0] >= self.min[0] and pos[0] <= self.max[0]:
            # if the z position is within the bounds
            if pos[2] >= self.min[1] and pos[2] <= self.max[1]:
                # It is in this checkpoint
                return True

        # It is not in this checkpoint
        return False


class Checkpoint(Tile):
    """Checkpoint Tile object holding boundary data"""

    def __init__(
        self,
        min: tuple[float, float],
        max: tuple[float, float],
        center: tuple[float, float, float]
    ) -> None:
        super().__init__(min, max, center)


class Swamp(Tile):
    """Swamp Tile object holding boundary data"""

    def __init__(
        self,
        min: tuple[float, float],
        max: tuple[float, float],
        center: tuple[float, float, float]
    ) -> None:
        super().__init__(min, max, center)


class StartTile(Tile):
    """StartTile Tile object holding boundary data"""

    def __init__(
        self,
        min: tuple[float, float],
        max: tuple[float, float],
        wb_node: Node,
        center: tuple[float, float, float]
    ) -> None:
        super().__init__(min, max, center)
        self._wb_node: Node = wb_node
        
    def set_visible(self, visible: bool) -> None:
        """Sets the visibility of the start tile

        Args:
            visible (bool): True to show green start tile color, False to
            disable
        """
        self._wb_node.getField("start").setSFBool(visible)
        
    def is_wall_present(self, wall_name: str) -> bool:
        """Returns whether a wall on a specified side is present on the start 
        tile

        Args:
            wall_name (str): Wall name to check. The valid strings for this are:
            `topWall`, `rightWall`, `bottomWall`, `leftWall`
        Returns:
            bool: True if a wall is present on the specified side, False 
            otherwise
        """
        if wall_name not in ["topWall", "rightWall", "bottomWall", "leftWall"]:
            Console.log_err(f"Invalid is_wall_present parameter: {wall_name}")
            return False
        return self._wb_node.getField(wall_name).getSFInt32() != 0


class TileManager(ErebusObject):
    """Manages swamp and checkpoint tiles for performing checks on entry
    """
    
    # Room multipliers
    ROOM_MULT: list[float] = [1, 1.25, 1.5, 2]
    SWAMP_TIME_MULT: float = 5.0

    def __init__(self, erebus: Erebus):
        """Creates a new TileManager object. Initialises start tile, checkpoint
        and swamp objects from the Webots world.

        Args:
            erebus (Erebus): Erebus supervisor game object
        """
        super().__init__(erebus)
        self.num_swamps: int = 0
        self.num_checkpoints: int = 0

        self.start_tile: StartTile = self._get_start_tile()
        self.checkpoints: list[Checkpoint] = self._get_checkpoints()
        self.swamps: list[Swamp] = self._get_swamps()

    def _get_swamps(self) -> list[Swamp]:
        """Get all swamps in simulation. Stores boundary information
        within a list of Swamp objects

        Returns:
            list[Swamp]: List of swamp objects
        """
        
        swamps: list[Swamp] = []

        self.num_swamps = (
            self._erebus.getFromDef('SWAMPBOUNDS')
            .getField('children')
            .getCount()
        )

        # Iterate for each swamp
        for i in range(self.num_swamps):
            # Get swamp min and max bounds positions
            min_pos: list[float] = (
                self._erebus.getFromDef(f"swamp{i}min")
                .getField("translation")
                .getSFVec3f()
            )
            max_pos: list[float] = (
                self._erebus.getFromDef(f"swamp{i}max")
                .getField("translation")
                .getSFVec3f()
            )

            center_pos: tuple = ((max_pos[0]+min_pos[0])/2,
                                 max_pos[1],
                                 (max_pos[2]+min_pos[2])/2)

            # Create a swamp object using the min and max (x,z)
            swamp: Swamp = Swamp((min_pos[0], min_pos[2]),
                                 (max_pos[0], max_pos[2]),
                                 center_pos)

            swamps.append(swamp)
            
        return swamps

    def _get_checkpoints(self) -> list[Checkpoint]:
        """Get all checkpoints in simulation. Stores boundary information
        within a list of Checkpoint objects

        Returns:
            list[Checkpoint]: List of checkpoint objects
        """

        checkpoints: list[Checkpoint] = []

        self.num_checkpoints = (
            self._erebus.getFromDef('CHECKPOINTBOUNDS')
            .getField('children')
            .getCount()
        )

        # Iterate for each checkpoint
        for i in range(self.num_checkpoints):
            # Get the checkpoint min and max bounds positions
            min_pos: list[float] = (
                self._erebus.getFromDef(f"checkpoint{i}min")
                .getField("translation")
                .getSFVec3f()
            )
            max_pos: list[float] = (
                self._erebus.getFromDef(f"checkpoint{i}max")
                .getField("translation")
                .getSFVec3f()
            )

            centerPos = ((max_pos[0]+min_pos[0])/2,
                         max_pos[1],
                         (max_pos[2]+min_pos[2])/2)

            # Create a checkpoint object using the min and max (x,z)
            checkpoint = Checkpoint((min_pos[0], min_pos[2]),
                                    (max_pos[0], max_pos[2]),
                                    centerPos)

            checkpoints.append(checkpoint)
            
        return checkpoints
            
    def _get_start_tile(self) -> StartTile:
        """Gets the world's start tile as a StartTile object, holding boundary
        information

        Returns:
            StartTile: StartTile object
        """
        start_tile_node = self._erebus.getFromDef("START_TILE")

        # Get the vector positions
        start_min_pos: list[float] = (
            self._erebus.getFromDef("start0min")
            .getField("translation")
            .getSFVec3f()
        )
        start_max_pos: list[float] = (
            self._erebus.getFromDef("start0max")
            .getField("translation")
            .getSFVec3f()
        )
        
        start_center_pos: tuple = ((start_max_pos[0]+start_min_pos[0])/2,
                                   start_max_pos[1],
                                   (start_max_pos[2]+start_min_pos[2])/2)

        return StartTile((start_min_pos[0], start_min_pos[2]),
                         (start_max_pos[0], start_max_pos[2]),
                         start_tile_node, 
                         center=start_center_pos,)

    @staticmethod
    def coord2grid(
        coord: list[float] | tuple[float, float, float],
        supervisor: Supervisor
    ) -> int:
        """Converts a world coordinate to the corresponding world tile node 
        index (only uses x,z components) 

        Args:
            coord (list[float] | tuple[float, float, float]): Webots world 
            coordinate 
            supervisor (Supervisor): Erebus supervisor object

        Returns:
            int: Index of world tile within Webots node hierarchy
        """
        side: float = 0.3 * (supervisor.getFromDef("START_TILE")
                             .getField("xScale")
                             .getSFFloat())
        height: float = (
            supervisor.getFromDef("START_TILE")
            .getField("height")
            .getSFFloat()
        )
        width: float = (
            supervisor.getFromDef("START_TILE")
            .getField("width")
            .getSFFloat()
        )
        return int(
            round((coord[0] + (width / 2 * side)) / side, 0) * height +
            round((coord[2] + (height / 2 * side)) / side, 0)
        )
        
    def check_swamps(self) -> None: 
        """Check if the simulation robot is in any swamps. Slows down the robot
        accordingly
        """
        # Check if the robot is in a swamps
        in_swamp: bool = any([s.check_position(self._erebus.robot_obj.position) 
                              for s in self.swamps])
        self._erebus.robot_obj.update_in_swamp(in_swamp, 
                                               self._erebus.DEFAULT_MAX_MULT)
    
    def check_checkpoints(self) -> None: 
        """Check if the simulation robot is in any checkpoints. Awards points
        accordingly
        """
        # Test if the robots are in checkpoints
        checkpoint = [c for c in self.checkpoints 
                      if c.check_position(self._erebus.robot_obj.position)]
        # If any checkpoints
        if len(checkpoint) > 0:
            self._erebus.robot_obj.update_checkpoints(checkpoint[0])
