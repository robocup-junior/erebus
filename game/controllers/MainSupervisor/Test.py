# Tests that need to be added:
# - Victim detection overlap
# - Game info
# - Maps
# - Curved victim mis-identification

from __future__ import annotations

import random
import struct
import math
from abc import ABC, abstractmethod

from ConsoleLog import Console
from Victim import VictimObject
from Victim import HazardMap
from Victim import Victim
from Robot import Robot
from Tile import Checkpoint, Swamp
from typing import TYPE_CHECKING
from typing import Sequence
from typing import Optional

from ErebusObject import ErebusObject

import numpy as np
from overrides import override

if TYPE_CHECKING:
    from MainSupervisor import Erebus
    
def rotate(
    vector: tuple[float, float], 
    angle: float
) -> tuple[float, float]:
    """Rotates a 2d vector by a specified angle

    Args:
        vector (tuple[float, float]): Vector to rotate
        angle (float): Angle to rotate by (in degrees)

    Returns:
        tuple[float, float]: Newly rotated vector
    """    
    (x,y) = vector
    angle_rad = angle*math.pi/180
    new_x = x*math.cos(angle_rad) - y*math.sin(angle_rad)
    new_y = x*math.sin(angle_rad) + y*math.cos(angle_rad)
    return (new_x, new_y)

def wrong_victim(simple_type: str) -> str:
    """Helper function to get a different victim type to the open given

    Args:
        simple_type (str): Simple victim/hazard type

    Returns:
        str: Random wrong victim/hazard type
    """
    if simple_type == 'H':
        return random.choice(['S','U','F','P','C','O'])
    if simple_type == 'S':
        return random.choice(['H','U','F','P','C','O'])
    if simple_type == 'U':
        return random.choice(['S','H','F','P','C','O'])

    if simple_type == 'F':
        return random.choice(['P','C','O','H','S','U'])
    if simple_type == 'P':
        return random.choice(['F','C','O','H','S','U'])
    if simple_type == 'C':
        return random.choice(['P','F','O','H','S','U'])
    if simple_type == 'O':
        return random.choice(['P','C','F','H','S','U'])
    
    Console.log_err(f"Include simple type: {simple_type}. Returning 'H'")
    return 'H'

class Test(ErebusObject, ABC):
    def __init__(self, erebus: Erebus):
        """Initialises a new Erebus (unit) test

        Args:
            erebus (Erebus): Erebus supervisor game object
        """
        super().__init__(erebus)
        self._report: str = ""

    def get_test_report(self) -> str:
        """Get test report string, a string detailing the result of the test if
        it fails 

        Returns:
            str: Test report message
        """
        return self._report

    def set_test_report(self, s: str):
        """Set test report string, a string detailing the result of the test if
        it fails

        Args:
            s (str): Test report message
        """
        self._report = s

    
    @abstractmethod
    def pre_test(self) -> tuple[int, int, int, int, bytes, bytes, bytes]:
        """Abstract method run before the test is computed. Used to initialise
        what the robot will do during the test.

        Returns:
            tuple[int, int, int, int, bytes, bytes, bytes]: Data sent to the 
            robot test controller in the form [identify human, wait length, 
            wheel 1 vel, wheel 2 vel, human type, command, command args]
        """
        ...

        
    @abstractmethod
    def test(self) -> bool:
        """Abstract method to return the result of the test to be run.

        Returns:
            bool: Whether the test has passed or not. True if passed, False 
            otherwise
        """
        ...

    
    @abstractmethod
    def post_test(self) -> None:
        """Abstract method run after the test is computed. Anything that needs
        to be cleaned up or done after a test (e.g. reset victim textures)
        should be done here
        """
        ...


class TestVictim(Test):
    """Test victim detection at various different ranges away from both
    victim and hazards
    """
    # TODO tests for different waiting times

    def __init__(
        self, 
        erebus: Erebus,
        index: int,
        offset: float,
        angle: float,
        victim_list: Sequence[VictimObject],
        misidentify: bool = False,
        delay: int = 3
    ) -> None:
        """Initialises a new victim test

        Args:
            erebus (Erebus): Erebus supervisor game object
            index (int): victim index of `victim_list` to test
            offset (float): position offset from victim to test (in meters)
            angle (float): angle from the victim normal (from -90 to 90)
            victim_list (Sequence[VictimObject]): list of all victims (e.g. all
            hazards or victims) 
            misidentify (bool, optional): whether to purposefully misidentify the victim
            type. Defaults to False.
            delay (int, optional): Delay before identification
        """
        super().__init__(erebus)
        self._index: int = index
        self._offset: float = offset
        self._angle: float = angle
        self._misidentify: bool = misidentify
        self._delay: int = delay

        self._start_score: float = 0
        self._to_victim_valid: bool = True
        self._start_time: float = 0

        self._simple_victim_type: str = ''

        self._victim: Optional[VictimObject] = None
        self._victim_list: Sequence[VictimObject] = victim_list

    @override
    def pre_test(self) -> tuple[int, int, int, int, bytes, bytes, bytes]:
        """Moves the robot to it's respective offset and angle from the victim. 
        Sends info to the robot controller to stop and identify the correct 
        victim type

        Returns:
            tuple[int, int, int, int, bytes, bytes, bytes]: Data to send to 
            test controller
        """
        Console.log_info(f"Testing Offset {self._offset} with Angle {self._angle}, "
                         f"with misidentifications: {self._misidentify} and "
                         f"delay: {self._delay}")
        
        self._start_time = self._erebus.getTime()
        
        self._erebus.robot_obj.increase_score("TestVictim starting test score",
                                              100)
        
        self._start_score = self._erebus.robot_obj.get_score()
        self._erebus.robot_obj.reset_time_stopped()

        self._victim = self._victim_list[self._index]
        self._to_victim_valid =  TestRunner.robotToVictim(
            self._erebus.robot_obj, self._victim, self._offset, self._angle)
        
        self._simple_victim_type: str = self._victim.get_simple_type()
        if self._misidentify:
            # If testing misidentifications, test the wrong victim
            self._simple_victim_type = wrong_victim(self._simple_victim_type)
        
        victim_type: bytes = bytes(self._simple_victim_type, "utf-8")
        # identify human, wait , wheel 1, wheel 2, human type, command
        # command args
        return (1, self._delay, 0, 0, victim_type, b' ', b' ')

    @override
    def test(self) -> bool:
        """Test whether the test controller correctly detected the victim, and
        the correct number of points were awarded, accounting for correct
        victim identification and room multiplier

        Returns:
            bool: Whether or not the correct score was awarded to the robot.
        """
        if self._victim is None:
            self.set_test_report("Could not find victim")
            return False
        
        # If to victim re-position is not valid (would be out of range from
        # rounding errors)
        if not self._to_victim_valid:
            Console.log_warn("Skipping test due to distance from "
                             "the victim is too large (from rounding errors)")
            return True

        grid: int = self._erebus.tile_manager.coord2grid(
            self._victim.wb_translation_field.getSFVec3f(),
            self._erebus
        )
        room_num: int = (
            self._erebus.getFromDef("WALLTILES")
            .getField("children")
            .getMFNode(grid) # type: ignore
            .getField("room")
            .getSFInt32() - 1
        )
        multiplier: float = self._erebus.tile_manager.ROOM_MULT[room_num]
        
        # Test time stopped, if too short, no points should be awarded
        if (self._erebus.getTime() - self._start_time) < 1:
            self.set_test_report(f"Time stopped: "
                                 f"{self._erebus.getTime() - self._start_time} "
                                 f"(Internal {self._erebus.robot_obj.time_stopped()})")
            return self._erebus.robot_obj.get_score() == self._start_score

        if self._offset > 0.093:
            self.set_test_report((
                f"Expected score: {self._start_score - 5}, "
                f"but was: {self._erebus.robot_obj.get_score()}"
            ))
            return self._erebus.robot_obj.get_score() == self._start_score - 5

        types: list[str] = ['H', 'S', 'U']
        correct_type_bonus: float = 10.0
        if type(self._victim) == HazardMap:
            correct_type_bonus = 20.0
            types = ['F', 'O', 'C', 'P']
        
        # Check various scores from mis-identifications of victims to hazards
        # or if the type is just wrong...
        if self._misidentify:
            if self._simple_victim_type in types:
                return (self._erebus.robot_obj.get_score() - self._start_score ==
                        (self._victim.score_worth * multiplier))
            return self._erebus.robot_obj.get_score() == self._start_score - 5 

        return (self._erebus.robot_obj.get_score() - self._start_score ==
                (correct_type_bonus * multiplier) +
                (self._victim.score_worth * multiplier))

    @override
    def post_test(self) -> None:
        """Resets the victim textures, so the next test has victim textures
        as unidentified
        """
        self._erebus.robot_obj.reset_time_stopped()
        self._erebus.victim_manager.reset_victim_textures()


class TestCheckpoint(Test):
    """Test checkpoints give points on entry
    """
        
    def __init__(self, erebus: Erebus, index: int, re_entry: bool = False):
        """Initialises a new checkpoint test

        Args:
            erebus (Erebus): Erebus supervisor game object
            index (int): Index of checkpoint to test (from list in tile manager)
            re_entry (bool, optional): Test for checkpoint re-entry (e.g. giving
            no more points). Defaults to False.
        """
        super().__init__(erebus)
        self._index: int = index
        self._start_score: float = 0.0
        self._re_entry: bool = re_entry
        self._checkpoint: Optional[Checkpoint] = None

    @override
    def pre_test(self) -> tuple[int, int, int, int, bytes, bytes, bytes]:
        """Moves the robot to the corresponding checkpoint to test

        Returns:
            tuple[int, int, int, int, bytes, bytes, bytes]: Data to send to 
            test controller
        """
        self._start_score = self._erebus.robot_obj.get_score()
        checkpoints: list[Checkpoint] = self._erebus.tile_manager.checkpoints
        self._checkpoint = checkpoints[self._index]
        self._erebus.robot_obj.position = list(self._checkpoint.center)
        # identify human, wait , wheel 1, wheel 2, human type, command
        # command args
        return (0, 1, 0, 0, b'U', b' ', b' ')

    @override
    def test(self) -> bool:
        """Test whether the correct amount of points (10 * room multiplier) are
        awarded to the robot on checkpoint entry.
        
        If re-entry is set to true, checks that no points are given.

        Returns:
            bool: If the correct amount of points were awarded
        """
        if self._re_entry:
            Console.log_info("Testing checkpoint re-entry")
            return self._erebus.robot_obj.get_score() == self._start_score
        
        if self._checkpoint is None:
            self.set_test_report("Could not find checkpoint")
            return False

        grid: int = self._erebus.tile_manager.coord2grid(
            self._checkpoint.center, self._erebus)
        room_num: int = (
            self._erebus
            .getFromDef("WALLTILES")
            .getField("children")
            .getMFNode(grid) # type: ignore
            .getField("room")
            .getSFInt32() - 1
        )

        multiplier = self._erebus.tile_manager.ROOM_MULT[room_num]
        return (self._erebus.robot_obj.get_score() ==
                self._start_score + (10 * multiplier))

    @override
    def post_test(self) -> None: pass


class TestRelocate(Test):
    """Test if relocates give a -5 penalty and relocated to the last visited
    checkpoint
    """
    
    def __init__(self, erebus: Erebus, index: int):
        """Initialises a new relocate test

        Args:
            erebus (Erebus): Erebus supervisor game object
            index (int): Index of human victim to move to before relocate
        """
        super().__init__(erebus)
        self._index: int = index
        self._start_score: float = 0.0
        self._start_pos: list[float] = []

    @override
    def pre_test(self) -> tuple[int, int, int, int, bytes, bytes, bytes]:
        """Moves the robot to a specified victim before relocating.
        Increases the robot's score, to ensure the penalty will be applied.

        Returns:
            tuple[int, int, int, int, bytes, bytes, bytes]: Data to send to 
            test controller
        """
        self._erebus.robot_obj.increase_score("TestRelocate starting test score",
                                              100)
        self._start_score = self._erebus.robot_obj.get_score()
        self._start_pos = self._erebus.robot_obj.position
        
        humans: list[Victim] = self._erebus.victim_manager.victims
        victim: Victim = humans[self._index]

        TestRunner.robotToVictim(self._erebus.robot_obj, victim)
        
        self._relocate_tile: Checkpoint = random.choice(
            self._erebus.tile_manager.checkpoints)
        self._erebus.robot_obj.last_visited_checkpoint_pos = self._relocate_tile.center
        # identify human, wait , wheel 1, wheel 2, human type, command
        # command args
        return (0, 1, 0, 0, b'U', b' ', b' ')

    @override
    def test(self) -> bool:
        """Tests a -5 point penalty is given to the robot after a relocate is
        given, and the robot correctly relocates to a random checkpoint in the
        world

        Returns:
            bool: If the correct penalty was given and the robot relocated to 
            the correct position
        """
        
        self._erebus.relocate_robot()
        self._erebus.robot_obj.reset_time_stopped()
        return (self._erebus.robot_obj.get_score() == self._start_score - 5 and
                self._relocate_tile.check_position(self._erebus.robot_obj.position))

    @override
    def post_test(self) -> None: pass


class TestBlackHole(Test):
    """Test blackholes correctly relocate and give a point penalty (similar to
    relocates)
    """
    def __init__(self, erebus: Erebus):
        """Intialises a new black hole test

        Args:
            erebus (Erebus): Erebus supervisor game object
        """        
        super().__init__(erebus)
        self._start_score: float = 0.0

    @override
    def pre_test(self) -> tuple[int, int, int, int, bytes, bytes, bytes]:
        """Moves the robot below the world, to simulate falling into a 
        black-hole. 
        Increases the robot's score, to ensure the penalty will be applied.

        Returns:
            tuple[int, int, int, int, bytes, bytes, bytes]: Data to send to 
            test controller
        """
        self._erebus.robot_obj.increase_score("TestBlackHole starting test score",
                                              100)
        self._start_score = self._erebus.robot_obj.get_score()

        self._erebus.config.disable_lop = False
        self._erebus.robot_obj.reset_time_stopped()
        self._erebus.robot_obj.position = [-10., -1., -10.]

        # identify human, wait , wheel 1, wheel 2, human type, command
        # command args
        return (0, 1, 0, 0, b'U', b' ', b' ')

    @override
    def test(self) -> bool:
        """Tests a -5 point penalty is given to the robot.

        Returns:
            bool: If the correct penalty was given
        """
        return self._erebus.robot_obj.get_score() == self._start_score - 5

    @override
    def post_test(self) -> None:
        """Disables lack of progress, since most other tests need this off
        """
        self._erebus.config.disable_lop = True


class TestSwamp(Test):
    """Tests swamps give a slow penalty when entering
    """
    def __init__(self, erebus: Erebus, index: int):
        """Initialises a new swamp test

        Args:
            erebus (Erebus): Erebus supervisor game object
            index (int): Index of swamp to test slow on (from 
            `TileManager.swamps`)
        """
        super().__init__(erebus)
        self._index: int = index
        self._start_score: float = 0.0

    @override
    def pre_test(self) -> tuple[int, int, int, int, bytes, bytes, bytes]:
        """Moves the robot to the specified swamp, and enables wheel movement

        Returns:
            tuple[int, int, int, int, bytes, bytes, bytes]: Data to send to 
            test controller
        """
        self._start_score = self._erebus.robot_obj.get_score()
        swamps: list[Swamp] = self._erebus.tile_manager.swamps
        swamp: Swamp = swamps[self._index]

        self._erebus.robot_obj.position = list(swamp.center)
        # identify human, wait , wheel 1, wheel 2, human type, command
        # command args
        return (0, 1, 6, 6, b'U', b' ', b' ')

    @override
    def test(self) -> bool:
        """Tests whether robot movement is slowed by the swamp

        Returns:
            bool: Whether the robot is slowed by the correct multiplier amount
        """
        vel: list[float] = self._erebus.robot_obj.velocity
        # 0.02 for wheel velocity of 1
        # 0.02 * 0.32 multiplier = 0.006
        return any(math.isclose(abs(v), 0.006, abs_tol=0.0005) for v in vel)

    @override
    def post_test(self) -> None:
        """Disables lack of progress, since most other tests need this off
        """
        self._erebus.config.disable_lop = True


class TestLOP(Test):
    """Test auto LOP after 20 seconds.
    
    Note: Make sure this isn't run first, since auto LOPs dont happen from the
    starting tile 
    """

    def __init__(self, erebus: Erebus):
        """Initialises new automated lack of progress test 

        Args:
            erebus (Erebus): Erebus supervisor game object
        """
        super().__init__(erebus)
        self._start_score: float = 0.0

    @override
    def pre_test(self) -> tuple[int, int, int, int, bytes, bytes, bytes]:
        """Waits for 20s until an automatic relocation is applied.
        Increases the robot's score, to ensure the penalty will be applied.

        Returns:
            tuple[int, int, int, int, bytes, bytes, bytes]: Data to send to 
            test controller
        """
        self._erebus.robot_obj.increase_score("TestLOP starting test score",
                                              100)
        self._erebus.config.disable_lop = False
        self._erebus.robot_obj.reset_time_stopped()
        self._start_score = self._erebus.robot_obj.get_score()

        # identify human, wait , wheel 1, wheel 2, human type, command
        # command args
        return (0, 25, 0, 0, b'U', b' ', b' ')

    @override
    def test(self) -> bool:
        """Tests a -5 point penalty is given to the robot.

        Returns:
            bool: If the correct penalty was given
        """
        return self._erebus.robot_obj.get_score() == self._start_score - 5

    @override
    def post_test(self) -> None:
        """Disables lack of progress, since most other tests need this off
        """
        self._erebus.robot_obj.reset_time_stopped()
        self._erebus.config.disable_lop = True

class TestLOPMessage(TestRelocate):
    """Tests for lack of progress calls given from the robot controller
    
    Make sure these tests are done after checkpoint checks, to ensure the 
    checkpoints don't give the robot points
    """

    def __init__(self, erebus: Erebus, index: int):
        """Initialises new lack of progress tests called from a robot controller 

        Args:
            erebus (Erebus): Erebus supervisor game object
            index (int): Index of human victim to move to before relocate
        """
        super().__init__(erebus, index)

    @override
    def pre_test(self) -> tuple[int, int, int, int, bytes, bytes, bytes]:
        """Moves the robot to a specified victim before the test
        controller calls a relocate.
        Increases the robot's score, to ensure the penalty will be applied.

        Returns:
            tuple[int, int, int, int, bytes, bytes, bytes]: Data to send to 
            test controller
        """
        super().pre_test()
        # identify human, wait , wheel 1, wheel 2, human type, command
        # command args
        return (0, 2, 0, 0, b'U', b'L', b' ')

    @override
    def test(self) -> bool:
        """Tests a -5 point penalty is given to the robot.

        Returns:
            bool: If the correct penalty was given and the robot relocated to 
            the correct position
        """
        return (self._erebus.robot_obj.get_score() == 
                self._start_score - 5 and
                self._relocate_tile.check_position(
                    self._erebus.robot_obj.position))

    @override
    def post_test(self) -> None: pass
        
        

class TestRunner(ErebusObject):
    """Erebus test runner manager, used to run all Erebus (unit) tests. Records
    test successes and failures for each test run
    """

    def __init__(self, erebus: Erebus):
        """Initialises new test runner

        Args:
            erebus (Erebus): Erebus supervisor game object
        """
        super().__init__(erebus)
        self._tests: list[Test] = []

        self._stage: int = 0
        self._start_test: bool = False
        self._pre_test: bool = False
        self._finished_test: bool = False

        self._fails: int = 0
        self._passes: int = 0
        self._finished: bool = False

        self._tests = self.add_tests()

    def add_tests(self) -> list[Test]:
        """Adds all tests to be run by the test runner

        Returns:
            list[Test]: List of tests to run
        """
        init: list[Test] = self._tests     
        
        init += [TestBlackHole(self._erebus)]
        # init += [TestSwamp(self._erebus, i)
        #          for i in range(len(self._erebus.tile_manager.swamps))]
        init += [TestLOP(self._erebus)]
        init += [TestCheckpoint(self._erebus, i)
                 for i in range(len(self._erebus.tile_manager.checkpoints))]
        
                
        init += [TestRelocate(self._erebus, i)
                 for i in range(len(self._erebus.victim_manager.victims))]
        init += [TestLOPMessage(self._erebus, i) 
                 for i in range(len(self._erebus.victim_manager.victims))]  
        
        # Check for re-entry to checkpoints
        init += [TestCheckpoint(self._erebus, i, True)
            for i in range(len(self._erebus.tile_manager.checkpoints))]


        ###### VICTIM ######
        # Negative tests for distance
        init += [TestVictim(self._erebus, 0, offset, angle,
                            self._erebus.victim_manager.victims)
                 for offset in np.linspace(0.9, 0.15, 4)
                 for angle in np.linspace(-80, 80, 4)]
        
        # Tests for victim position
        init += [TestVictim(self._erebus, i, offset, angle,
                            self._erebus.victim_manager.victims)
                 for i in range(len(self._erebus.victim_manager.victims))
                 for offset in np.linspace(0.03, 0.089, 6)
                 for angle in np.linspace(-80, 80, 5)]        
        # Tests for victim misidentification
        init += [TestVictim(self._erebus, i, offset, 0,
                            self._erebus.victim_manager.victims, True)
                 for offset in np.linspace(0.05, 0.07, 2)
                 for i in range(len(self._erebus.victim_manager.victims))]
        # Tests for victim delays
        init += [TestVictim(self._erebus, i, 0.06, 0,
                            self._erebus.victim_manager.victims, 
                            delay=int(delay))
                 for delay in np.linspace(0, 5, 5)
                 for i in range(len(self._erebus.victim_manager.victims))]
        ###################
        
        ###### HAZARD ######
        # Negative tests for distance
        init += [TestVictim(self._erebus, 0, offset, angle,
                            self._erebus.victim_manager.hazards)
                 for offset in np.linspace(0.9, 0.15, 4)
                 for angle in np.linspace(-80, 80, 4)]
        
        # Tests for victim position
        init += [TestVictim(self._erebus, i, offset, angle,
                            self._erebus.victim_manager.hazards)
                 for i in range(len(self._erebus.victim_manager.hazards))
                 for offset in np.linspace(0.03, 0.089, 6)
                 for angle in np.linspace(-80, 80, 5)]        
        # Tests for victim misidentification
        init += [TestVictim(self._erebus, i, offset, 0,
                            self._erebus.victim_manager.hazards, True)
                 for offset in np.linspace(0.05, 0.07, 2)
                 for i in range(len(self._erebus.victim_manager.hazards))]
        # Tests for victim delays
        init += [TestVictim(self._erebus, i, 0.06, 0,
                            self._erebus.victim_manager.hazards, 
                            delay=int(delay))
                 for delay in np.linspace(0, 5, 5)
                 for i in range(len(self._erebus.victim_manager.hazards))]
        #################
        
        return init

    def get_stage(self, received_data: bytes) -> bool:
        """Gets the current stage of the test runner via the received data
        from the test controller. Data is also received about if a test
        needs to be started or finished.

        Args:
            received_data (bytes): Emitter data from test controller to process

        Returns:
            bool: Whether valid stage data was received from the emitter bytes.
            True if a test or end test message was received. False otherwise.
        """
        if len(received_data) == 8:
            try:
                tup = struct.unpack('c i', received_data)
                message = [tup[0].decode("utf-8"), tup[1]]

                if message[0] == 'T' and message[1] == self._stage:
                    self._start_test = True
                if message[0] == 'F' and message[1] == self._stage:
                    self._finished_test = True
                return True
            except:
                pass
        return False

    @staticmethod
    def robotToVictim(
        robot: Robot,
        victim: VictimObject,
        offset: float = 0.06,
        angle: float = 0,
    ) -> bool:
        """Moves the robot to a specified victim, with an offset directly 
        perpendicular away from it

        Args:
            robot (Robot): Robot game object
            victim (VictimObject): Victim object to move to
            offset (float, optional): Offset away from victim in meters.
            Defaults to 0.06.
            angle (float, optional): Angle offset away from the victim normal, 
            in degrees. Defaults to 0. 
        
        Returns:
            bool: True if the new position is within the valid detection range,
            False otherwise
        """
        norm = victim.get_surface_normal()
        
        rot = rotate((norm[0], norm[2]), angle)

        new_position: list[float] = list(np.array([
            victim.position[0],
            robot.position[1],
            victim.position[2]
        ]) + (np.array([rot[0], 0, rot[1]]) * offset))
        
        # Rounding to simulate rounding precision errors found due to only
        # being able to send cm positions for estimated victim positions
        rounded_pos: list[float] = [int(new_position[0] * 100) / 100, 0, int(new_position[2] * 100) / 100]
        if (victim.get_distance(rounded_pos) > 0.09):
            return False
        
        robot.position = new_position
        return True
        

    def _run_test(self) -> None:
        """Runs the current test, and handles moving to the next test when
        the previous has ended
        """
        if self._start_test and not self._pre_test:
            Console.log_warn((
                f"Starting test {str(self._stage)} "
                f"({self._tests[self._stage].__class__.__name__})"
            ))

            params: tuple = self._tests[self._stage].pre_test()
            # G, stage, identify human, wait , wheel 1, wheel 2, human type,
            # command, command args
            message = struct.pack("c i i i i i c c", b'G', self._stage, *params[:-1])
            message += params[-1]
            self._erebus.emitter.send(message)

            self._pre_test = True

        if self._start_test and self._finished_test:
            if self._tests[self._stage].test():
                Console.log_pass((f"Test {str(self._stage)}/"
                                  f"{len(self._tests)} Passed"))
                self._passes += 1
            else:
                Console.log_fail((f"Test {str(self._stage)}/"
                                  f"{len(self._tests)-1} Failed"))
                test_report: str = self._tests[self._stage].get_test_report()
                if test_report != "":
                    Console.log_fail(f"Report: {test_report}")
                self._fails += 1

            self._tests[self._stage].post_test()

            self._tests[self._stage].set_test_report("")
            self._start_test = False
            self._finished_test = False
            self._pre_test = False
            self._stage += 1

    def run(self) -> None:
        """Run all Erebus tests
        """
        if self._stage >= len(self._tests) and not self._finished:
            Console.log_info("Tests Finished")
            Console.log_info((f"{self._passes} / {len(self._tests)} Passed. "
                              f"({self._fails} Fails)"))
            self._finished = True
        if not self._finished:
            self._run_test()
