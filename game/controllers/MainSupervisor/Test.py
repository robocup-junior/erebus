from __future__ import annotations
from ConsoleLog import Console
from Victim import VictimObject
from Victim import HazardMap
from Victim import Victim
from Robot import Robot
from Tile import Checkpoint, Swamp
from typing import TYPE_CHECKING
from typing import Sequence

import struct
import math
from abc import ABC, abstractmethod

import numpy as np
from overrides import override


if TYPE_CHECKING:
    from MainSupervisor import Erebus

class Test(ABC):
    def __init__(self):
        self._report: str = ""

    def get_test_report(self) -> str:
        """Get test report string, a string detailing the result of the test 

        Returns:
            str: Test report message
        """
        return self._report

    def set_test_report(self, s: str):
        """Set test report string, a string detailing the result of the test

        Args:
            s (str): Test report message
        """
        self._report = s

    
    @abstractmethod
    def pre_test(
        self,
        supervisor: Erebus
    ) -> tuple[int, int, int, int, bytes]:
        """Abstract method run before the test is computed. Used to initialise
        what the robot will do during the test.

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            tuple[int, int, int, int, bytes]: Data sent to the robot test 
            controller in the form [identify human, wait length, wheel 1 vel, 
            wheel 2 vel, human type]
        """
        ...

        
    @abstractmethod
    def test(self, supervisor: Erebus) -> bool:
        """Abstract method to return the result of the test to be run.

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            bool: Whether the test has passed or not. True if passed, False 
            otherwise
        """
        ...

    
    @abstractmethod
    def post_test(self, supervisor: Erebus) -> None:
        """Abstract method run after the test is computed. Anything that needs
        to be cleaned up or done after a test (e.g. reset victim textures)
        should be done here

        Args:
            supervisor (Erebus): Erebus game supervisor object
        """
        ...


class TestVictim(Test):
    """Test victim detection at various different ranges away from both
    victim and hazards
    """
    # TODO position offset is not very reliable (gets stuck in walls)
    # TODO there are no negative tests (e.g. incorrect victim type)

    def __init__(
        self,
        index: int,
        offset: float,
        victim_list: Sequence[VictimObject]
    ) -> None:
        """Initialises a new victim test

        Args:
            index (int): victim index of `victim_list` to test
            offset (float): position offset from victim to test (in meters)
            victim_list (Sequence[VictimObject]): list of all victims (e.g. all
            hazards or victims) 
        """
        super().__init__()
        self._index: int = index
        self._offset: float = offset

        self._start_score: float = 0

        self._victim: None | VictimObject = None
        self._victim_list: list[VictimObject] = victim_list

    @override
    def pre_test(
        self,
        supervisor: Erebus,
    ) -> tuple[int, int, int, int, bytes]:
        """Moves the robot to it's respective offset from the victim. Sends
        info to the robot controller to stop and identify the correct victim 
        type

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            tuple[int, int, int, int, bytes]: Data to send to test controller
        """
        Console.log_info(f"Testing Offset {self._offset}")
        self._start_score = supervisor.robot0Obj.get_score()
        supervisor.robot0Obj.reset_time_stopped()

        self._victim = self._victim_list[self._index]
        TestRunner.robotToVictim(supervisor.robot0Obj,
                                 self._victim, self._offset)
        # The victim type being sent is the letter 'H' for harmed victim
        victim_type: bytes = bytes(self._victim.get_simple_type(), "utf-8")
        # identify human, wait , wheel 1, wheel 2, human type
        return (1, 3, 0, 0, victim_type)

    @override
    def test(self, supervisor: Erebus) -> bool:
        """Test whether the test controller correctly detected the victim, and
        the correct number of points were awarded, accounting for correct
        victim identification and room multiplier

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            bool: Whether or not the correct score was awarded to the robot.
        """
        if self._victim is None:
            self.set_test_report("Could not find victim")
            return False

        grid: int = supervisor.tileManager.coord2grid(
            self._victim.wb_translation_field.getSFVec3f(),
            supervisor
        )
        room_num: int = (
            supervisor.getFromDef("WALLTILES")
            .getField("children")
            .getMFNode(grid)
            .getField("room")
            .getSFInt32() - 1
        )
        multiplier: float = supervisor.tileManager.ROOM_MULT[room_num]

        if self._offset > 0.09:
            self.set_test_report((
                f"Expected score: {self._start_score - 5}, "
                f"but was: {supervisor.robot0Obj.get_score()}"
            ))
            return supervisor.robot0Obj.get_score() == self._start_score - 5

        correct_type_bonus: float = 10.0
        if type(self._victim) == HazardMap:
            correct_type_bonus = 20.0

        return (supervisor.robot0Obj.get_score() - self._start_score ==
                (correct_type_bonus * multiplier) +
                (self._victim.score_worth * multiplier))

    @override
    def post_test(self, supervisor: Erebus) -> None:
        """Resets the victim textures, so the next test has victim textures
        as unidentified

        Args:
            supervisor (Erebus): Erebus game supervisor object
        """
        supervisor.victimManager.reset_victim_textures()


class TestCheckpoint(Test):
    """Test checkpoints give points on entry
    """
    # TODO no tests that they dont give points on re-entry
    
    def __init__(self, index: int):
        """Initialises a new checkpoint test

        Args:
            index (int): Index of checkpoint to test (from list in tile manager)
        """
        super().__init__()
        self._index: int = index
        self._start_score: float = 0.0
        self._checkpoint: None | Checkpoint = None

    @override
    def pre_test(
        self,
        supervisor: Erebus,
    ) -> tuple[int, int, int, int, bytes]:
        """Moves the robot to the corresponding checkpoint to test

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            tuple[int, int, int, int, bytes]: Data to send to test controller
        """
        self._start_score = supervisor.robot0Obj.get_score()
        checkpoints: list[Checkpoint] = supervisor.tileManager.checkpoints
        self._checkpoint = checkpoints[self._index]
        supervisor.robot0Obj.position = list(self._checkpoint.center)
        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 1, 0, 0, b'U')

    @override
    def test(self, supervisor: Erebus) -> bool:
        """Test whether the correct amount of points (10 * room multiplier) are
        awarded to the robot on checkpoint entry

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            bool: If the correct amount of points were awarded
        """
        if self._checkpoint is None:
            self.set_test_report("Could not find checkpoint")
            return False

        grid: int = supervisor.tileManager.coord2grid(
            self._checkpoint.center, supervisor)
        room_num: int = (
            supervisor
            .getFromDef("WALLTILES")
            .getField("children")
            .getMFNode(grid)
            .getField("room")
            .getSFInt32() - 1
        )

        multiplier = supervisor.tileManager.ROOM_MULT[room_num]
        return (supervisor.robot0Obj.get_score() ==
                self._start_score + (10 * multiplier))

    @override
    def post_test(self, supervisor: Erebus) -> None: pass


class TestRelocate(Test):
    """Test if relocates give a -5 penalty
    """
    # TODO doesn't check if the robot was actually moved
    
    def __init__(self, index: int):
        """Initialises a new relocate test

        Args:
            index (int): Index of human victim to move to before relocate
        """
        super().__init__()
        self._index: int = index
        self._start_score: float = 0.0

    @override
    def pre_test(
        self,
        supervisor: Erebus,
    ) -> tuple[int, int, int, int, bytes]:
        """Moves the robot to a specified victim before relocating.
        Increases the robot's score, to ensure the penalty will be applied.

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            tuple[int, int, int, int, bytes]: Data to send to test controller
        """
        self._start_score = supervisor.robot0Obj.get_score()
        humans: list[Victim] = supervisor.victimManager.humans
        victim: Victim = humans[self._index]

        TestRunner.robotToVictim(supervisor.robot0Obj, victim)
        supervisor.relocate_robot()
        supervisor.robot0Obj.reset_time_stopped()
        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 1, 0, 0, b'U')

    @override
    def test(self, supervisor: Erebus) -> bool:
        """Tests a -5 point penalty is given to the robot

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            bool: If the correct penalty was given
        """
        return supervisor.robot0Obj.get_score() == self._start_score - 5

    @override
    def post_test(self, supervisor: Erebus) -> None: pass


class TestBlackHole(Test):
    """Test blackholes correctly relocate and give a point penalty (similar to
    relocates)
    """
    def __init__(self):
        super().__init__()
        self._start_score: float = 0.0

    @override
    def pre_test(
        self,
        supervisor: Erebus,
    ) -> tuple[int, int, int, int, bytes]:
        """Moves the robot below the world, to simulate falling into a 
        black-hole. 
        Increases the robot's score, to ensure the penalty will be applied.

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            tuple[int, int, int, int, bytes]: Data to send to test controller
        """
        supervisor.robot0Obj.increase_score("TestBlackHole starting test score",
                                            100, supervisor)
        self._start_score = supervisor.robot0Obj.get_score()

        supervisor.config.disable_lop = False
        supervisor.robot0Obj.reset_time_stopped()
        supervisor.robot0Obj.position = [-10., -1., -10.]

        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 1, 0, 0, b'U')

    @override
    def test(self, supervisor: Erebus) -> bool:
        """Tests a -5 point penalty is given to the robot.

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            bool: If the correct penalty was given
        """
        return supervisor.robot0Obj.get_score() == self._start_score - 5

    @override
    def post_test(self, supervisor: Erebus) -> None:
        """Disables lack of progress, since most other tests need this off

        Args:
            supervisor (Erebus): Erebus game supervisor object
        """
        supervisor.config.disable_lop = True


class TestSwamp(Test):
    """Tests swamps give a slow penalty when entering
    """
    def __init__(self, index: int):
        """Initialises a new swamp test

        Args:
            index (int): Index of swamp to test slow on (from 
            `TileManager.swamps`)
        """
        super().__init__()
        self._index: int = index
        self._start_score: float = 0.0

    @override
    def pre_test(
        self,
        supervisor: Erebus,
    ) -> tuple[int, int, int, int, bytes]:
        """Moves the robot to the specified swamp, and enables wheel movement

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            tuple[int, int, int, int, bytes]: Data to send to test controller
        """
        self._start_score = supervisor.robot0Obj.get_score()
        swamps: list[Swamp] = supervisor.tileManager.swamps
        swamp: Swamp = swamps[self._index]

        supervisor.robot0Obj.position = list(swamp.center)
        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 1, 6, 6, b'U')

    @override
    def test(self, supervisor: Erebus) -> bool:
        """Tests whether robot movement is slowed by the swamp

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            bool: Whether the robot is slowed by the correct multiplier amount
        """
        vel: list[float] = supervisor.robot0Obj.wb_node.getVelocity()
        # 0.02 for wheel velocity of 1
        # 0.02 * 0.32 multiplier = 0.006
        return any(math.isclose(abs(v), 0.006, abs_tol=0.0005) for v in vel)

    @override
    def post_test(self, supervisor: Erebus) -> None:
        """Disables lack of progress, since most other tests need this off

        Args:
            supervisor (Erebus): Erebus game supervisor object
        """
        supervisor.config.disable_lop = True


class TestLOP(Test):
    """Test auto LOP after 20 seconds.
    
    Note: Make sure this isn't run first, since auto LOPs dont happen from the
    starting tile 
    """

    def __init__(self):
        super().__init__()
        self._start_score: float = 0.0

    @override
    def pre_test(
        self,
        supervisor: Erebus,
    ) -> tuple[int, int, int, int, bytes]:
        """Waits for 20s until an automatic relocation is applied.
        Increases the robot's score, to ensure the penalty will be applied.

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            tuple[int, int, int, int, bytes]: Data to send to test controller
        """
        supervisor.robot0Obj.increase_score("TestLOP starting test score",
                                            100, supervisor)
        supervisor.config.disable_lop = False
        supervisor.robot0Obj.reset_time_stopped()
        self._start_score = supervisor.robot0Obj.get_score()

        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 25, 0, 0, b'U')

    @override
    def test(self, supervisor: Erebus) -> bool:
        """Tests a -5 point penalty is given to the robot.

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            bool: If the correct penalty was given
        """
        return supervisor.robot0Obj.get_score() == self._start_score - 5

    @override
    def post_test(self, supervisor: Erebus) -> None:
        """Disables lack of progress, since most other tests need this off

        Args:
            supervisor (Erebus): Erebus game supervisor object
        """
        supervisor.robot0Obj.reset_time_stopped()
        supervisor.config.disable_lop = True


class TestRunner:

    def __init__(self, supervisor: Erebus):
        self._tests: list[Test] = []

        self._stage: int = 0
        self._start_test: bool = False
        self._pre_test: bool = False
        self._finished_test: bool = False

        self._fails: int = 0
        self._passes: int = 0
        self._finished: bool = False

        self._tests = self.add_tests(supervisor)

    def add_tests(self, supervisor: Erebus) -> list[Test]:
        """Adds all tests to be run by the test runner

        Args:
            supervisor (Erebus): Erebus game supervisor object

        Returns:
            list[Test]: List of tests to run
        """
        init: list[Test] = self._tests

        init += [TestBlackHole()]
        init += [TestSwamp(i)
                 for i in range(len(supervisor.tileManager.swamps))]
        init += [TestLOP()]
        init += [TestCheckpoint(i)
                 for i in range(len(supervisor.tileManager.checkpoints))]
        init += [TestVictim(i, offset, supervisor.victimManager.hazards)
                 for offset in np.linspace(0.03, 0.13, 5)
                 for i in range(len(supervisor.victimManager.hazards))]
        init += [TestVictim(i, offset, supervisor.victimManager.humans)
                 for offset in np.linspace(0.03, 0.13, 5)
                 for i in range(len(supervisor.victimManager.humans))]
        init += [TestRelocate(i)
                 for i in range(len(supervisor.victimManager.humans))]
        return init

    def get_stage(self, received_data: bytes) -> bool:
        """Gets the current stage of the test runner via the received data
        from the test controller.

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
        offset: float = 0.06
    ) -> None:
        """Moves the robot to a specified victim, with an offset directly 
        perpendicular away from it

        Args:
            robot (Robot): Robot game object
            victim (VictimObject): Victim object to move to
            offset (float, optional): Offset away from victim in meters.
            Defaults to 0.06.
        """
        norm = victim.get_surface_normal()

        robot.position = list(np.array([
            victim.position[0],
            robot.position[1],
            victim.position[2]
        ]) + (norm * offset))

    def _run_test(self, supervisor: Erebus) -> None:
        """Runs the current test, and handles moving to the next test when
        the previous has ended

        Args:
            supervisor (Erebus): Erebus game supervisor object
        """
        if self._start_test and not self._pre_test:
            Console.log_warn((
                f"Starting test {str(self._stage)} "
                f"({self._tests[self._stage].__class__.__name__})"
            ))

            params: tuple = self._tests[self._stage].pre_test(supervisor)
            # G, stage, identify human, wait , wheel 1, wheel 2, human type
            message = struct.pack("c i i i i i c", b'G', self._stage, *params)
            supervisor.emitter.send(message)

            self._pre_test = True

        if self._start_test and self._finished_test:
            if self._tests[self._stage].test(supervisor):
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

            self._tests[self._stage].post_test(supervisor)

            self._tests[self._stage].set_test_report("")
            self._start_test = False
            self._finished_test = False
            self._pre_test = False
            self._stage += 1

    def run(self, supervisor: Erebus) -> None:
        """Run all Erebus tests

        Args:
            supervisor (Erebus): Erebus game supervisor object
        """
        if self._stage >= len(self._tests) and not self._finished:
            Console.log_info("Tests Finished")
            Console.log_info((f"{self._passes} / {len(self._tests)} Passed. "
                              f"({self._fails} Fails)"))
            self._finished = True
        if not self._finished:
            self._run_test(supervisor)
