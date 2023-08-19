

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from controller import Supervisor
from controller import Node

from typing import TYPE_CHECKING

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
        self.wb_node: Node = wb_node


class TileManager():
    """Manages swamp and checkpoint tiles for performing checks on entry
    """
    
    # Room multipliers
    ROOM_MULT: list[float] = [1, 1.25, 1.5, 2]
    SWAMP_SLOW_MULT: float = 0.32

    def __init__(self):
        self.num_swamps: int = 0
        self.num_checkpoints: int = 0

        self.checkpoints: list[Checkpoint] = []
        self.swamps: list[Swamp] = []

    def get_swamps(self, supervisor: Supervisor):
        """Get all swamps in simulation. Stores boundary information
        within Swamp objects in `TileManager.checkpoints`

        Args:
            supervisor (Supervisor): Erebus supervisor object
        """

        self.num_swamps = (
            supervisor.getFromDef('SWAMPBOUNDS')
            .getField('children')
            .getCount()
        )

        # Iterate for each swamp
        for i in range(self.num_swamps):
            # Get swamp min and max bounds positions
            min_pos: list[float] = (
                supervisor.getFromDef(f"swamp{i}min")
                .getField("translation")
                .getSFVec3f()
            )
            max_pos: list[float] = (
                supervisor.getFromDef(f"swamp{i}max")
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

            self.swamps.append(swamp)

    def get_checkpoints(self, supervisor: Supervisor):
        """Get all checkpoints in simulation. Stores boundary information
        within Checkpoint objects in `TileManager.checkpoints`

        Args:
            supervisor (Supervisor): Erebus supervisor object
        """

        self.num_checkpoints = (
            supervisor.getFromDef('CHECKPOINTBOUNDS')
            .getField('children')
            .getCount()
        )

        # Iterate for each checkpoint
        for i in range(self.num_checkpoints):
            # Get the checkpoint min and max bounds positions
            min_pos: list[float] = (
                supervisor.getFromDef(f"checkpoint{i}min")
                .getField("translation")
                .getSFVec3f()
            )
            max_pos: list[float] = (
                supervisor.getFromDef(f"checkpoint{i}max")
                .getField("translation")
                .getSFVec3f()
            )

            centerPos = ((max_pos[0]+min_pos[0])/2,
                         max_pos[1],
                         (max_pos[2]+min_pos[2])/2)

            # Create a checkpoint object using the min and max (x,z)
            checkpointObj = Checkpoint((min_pos[0], min_pos[2]),
                                       (max_pos[0], max_pos[2]),
                                       centerPos)

            self.checkpoints.append(checkpointObj)

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
        
    def check_swamps(self, erebus: Erebus): 
        """Check if the simulation robot is in any swamps. Slows down the robot
        accordingly

        Args:
            erebus (Erebus): Erebus game supervisor object
        """
        # Check if the robot is in a swamps
        in_swamp: bool = any([s.check_position(erebus.robot0Obj.position) 
                              for s in self.swamps])
        erebus.robot0Obj.update_in_swamp(erebus, in_swamp, 
                                         erebus.DEFAULT_MAX_MULT)
    
    def check_checkpoints(self, erebus: Erebus): 
        """Check if the simulation robot is in any checkpoints. Awards points
        accordingly

        Args:
            erebus (Erebus): Erebus game supervisor object
        """
        # Test if the robots are in checkpoints
        checkpoint = [c for c in self.checkpoints 
                      if c.check_position(erebus.robot0Obj.position)]
        # If any checkpoints
        if len(checkpoint) > 0:
            erebus.robot0Obj.update_checkpoints(erebus, checkpoint[0])
