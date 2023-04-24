from ConsoleLog import Console
import struct
import AutoInstall
from abc import abstractmethod
import math
from Victim import HazardMap

AutoInstall._import("np", "numpy")

class Test:
    def __init__(self):
        self._report = ""
        
    def getTestReport(self) -> str:
        return self._report
    
    def setTestReport(self, s: str):
        self._report = s
    
    @abstractmethod
    def preTest(self, supervisor) -> tuple : raise NotImplementedError

    @abstractmethod
    def test(self, supervisor) : raise NotImplementedError
    
    @abstractmethod
    def postTest(self, supervisor) : raise NotImplementedError
    
class TestVictim(Test):
    
    def __init__(self, index, offset, victimList):
        super().__init__()
        self.victim = None
        self.startScore = 0
        self.index = index
        self.offset = offset
        self.victimList = victimList
    
    def preTest(self, supervisor):
        Console.log_info(f"Testing Offset {self.offset}")
        self.startScore = supervisor.robot0Obj.getScore()  
        supervisor.robot0Obj.resetTimeStopped()
        
        self.victim = self.victimList[self.index]
        TestRunner.robotToVictim(supervisor.robot0Obj, self.victim, self.offset)
        victimType = bytes(self.victim.get_simple_type(), "utf-8") # The victim type being sent is the letter 'H' for harmed victim
        # identify human, wait , wheel 1, wheel 2, human type
        return (1, 3, 0, 0, victimType)

    def test(self, supervisor):
        grid = supervisor.tileManager.coord2grid(self.victim.wb_translationField.getSFVec3f(), supervisor)
        roomNum = supervisor.getFromDef("WALLTILES").getField("children").getMFNode(grid).getField("room").getSFInt32() - 1
        multiplier = supervisor.tileManager.ROOM_MULT[roomNum]
        if self.offset > 0.09:
            self.setTestReport(f"Expected score: {self.startScore - 5}, but was: {supervisor.robot0Obj.getScore()}")
            return supervisor.robot0Obj.getScore() == self.startScore - 5
        correctTypeBonus = 10
        if type(self.victim) == HazardMap:
            correctTypeBonus = 20
        return supervisor.robot0Obj.getScore() - self.startScore == (correctTypeBonus * multiplier) + ( self.victim.scoreWorth * multiplier)
    
    def postTest(self, supervisor):
        supervisor.victimManager.resetVictimsTextures()

class TestCheckpoint(Test):
    def __init__(self,index):
        super().__init__()
        self.startScore = 0
        self.checkpoint = None
        self.index = index
        
    def preTest(self, supervisor):
        self.startScore = supervisor.robot0Obj.getScore()  
        checkpoints = supervisor.tileManager.checkpoints
        self.checkpoint = checkpoints[self.index]
        supervisor.robot0Obj.position = self.checkpoint.center
        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 1, 0, 0, b'U')
    
    def test(self, supervisor):
        grid = supervisor.tileManager.coord2grid(self.checkpoint.center, supervisor)
        roomNum = supervisor.getFromDef("WALLTILES").getField("children").getMFNode(grid).getField("room").getSFInt32() - 1
        multiplier = supervisor.tileManager.ROOM_MULT[roomNum]
        return supervisor.robot0Obj.getScore() == self.startScore + (10 * multiplier)
    
    def postTest(self, supervisor):
        pass

class TestRelocate(Test):
    def __init__(self,index):
        super().__init__()
        self.startScore = 0
        self.index = index
        
    def preTest(self, supervisor):
        self.startScore = supervisor.robot0Obj.getScore()  
        humans = supervisor.victimManager.humans
        self.victim = humans[self.index]
        TestRunner.robotToVictim(supervisor.robot0Obj, self.victim)
        supervisor.relocate_robot()
        supervisor.robot0Obj.resetTimeStopped()
        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 1, 0, 0, b'U')
    
    def test(self, supervisor):
        return supervisor.robot0Obj.getScore() == self.startScore - 5
    
    def postTest(self, supervisor):
        pass

class TestBlackHole(Test):
    def __init__(self):
        super().__init__()
        self.startScore = 0
        
    def preTest(self, supervisor):
        supervisor.robot0Obj.increaseScore("TestBlackHole staring test score", 100, supervisor)
        self.startScore = supervisor.robot0Obj.getScore()  
        supervisor.config.disableLOP = False
        supervisor.robot0Obj.resetTimeStopped()
        supervisor.robot0Obj.position = [-10,-1,-10]
        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 1, 0, 0, b'U')
    
    def test(self, supervisor):
        return supervisor.robot0Obj.getScore() == self.startScore - 5
    
    def postTest(self, supervisor):
        supervisor.config.disableLOP = True
        
class TestSwamp(Test):
    def __init__(self, index):
        super().__init__()
        self.startScore = 0
        self.index = index
        
    def preTest(self, supervisor):
        self.startScore = supervisor.robot0Obj.getScore()  
        swamps = supervisor.tileManager.swamps
        swamp = swamps[self.index]
        supervisor.robot0Obj.position = swamp.center
        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 1, 1, 1, b'U')
    
    def test(self, supervisor):
        vel = supervisor.robot0Obj.wb_node.getVelocity()
        # 0.02 for wheel velocity of 1
        # 0.02 * 0.32 multiplier = 0.006
        ans = any(math.isclose(abs(v),0.006, abs_tol=0.0005) for v in vel)
        return ans
    
    def postTest(self, supervisor):
        supervisor.config.disableLOP = True

class TestLOP(Test):
    """Test auto LOP after 20 seconds
    Make sure this isn't run first, since auto LOPs dont happen from the starting tile 
    """
    def __init__(self):
        super().__init__()
        self.startScore = 0
        
    def preTest(self, supervisor):
        supervisor.robot0Obj.increaseScore("TestLOP staring test score", 100, supervisor)
        supervisor.config.disableLOP = False
        supervisor.robot0Obj.resetTimeStopped()
        self.startScore = supervisor.robot0Obj.getScore() 
        # identify human, wait , wheel 1, wheel 2, human type
        return (0, 25, 0, 0, b'U')
    
    def test(self, supervisor):
        return supervisor.robot0Obj.getScore() == self.startScore - 5
    
    def postTest(self, supervisor):
        supervisor.robot0Obj.resetTimeStopped()
        supervisor.config.disableLOP = True

class TestRunner:
    
    
    def __init__(self, supervisor):
        self.tests = []
        
        self.stage = 0
        self.startTest = False
        self.preTest = False
        self.finishedTest = False
            
        self.fails = 0
        self.passes = 0
        self.finished = False
        
        init = self.tests
        init += [TestBlackHole()]
        init += [TestSwamp(i) for i in range(len(supervisor.tileManager.swamps))]
        init += [TestLOP()]
        init += [TestCheckpoint(i) for i in range(len(supervisor.tileManager.checkpoints))]
        init += [TestVictim(i, ofst, supervisor.victimManager.hazards) for ofst in np.linspace(0.03,0.13,5) for i in range(len(supervisor.victimManager.hazards))]
        init += [TestVictim(i, ofst, supervisor.victimManager.humans) for ofst in np.linspace(0.03,0.13,5) for i in range(len(supervisor.victimManager.humans))]
        init += [TestRelocate(i) for i in range(len(supervisor.victimManager.humans))]
        self.tests = init
    
    def getStage(self, receivedData) -> bool:
        if len(receivedData) == 8:
            try: 
                tup = struct.unpack('c i', receivedData)
                message = [tup[0].decode("utf-8"), tup[1]]
                                        
                if message[0] == 'T' and message[1] == self.stage:
                    self.startTest = True    
                if message[0] == 'F' and message[1] == self.stage:
                    self.finishedTest = True
                return True
            except:
                pass
        return False
    

    @staticmethod
    def sideToVector(side: str) -> np.array:
        # [0,0,1] = bot
        # [0,0,-1] = top
        # [1,0,0] = right
        # [-1,0,0] = left
        if side == 'bottom':
            return np.array([0,0,1])
        if side == 'top':
            return np.array([0,0,-1])
        if side == 'right':
            return np.array([1,0,0])
        if side == 'left':
            return np.array([-1,0,0])
    
    @staticmethod
    def robotToVictim(robot, victim, offset=0.06) -> None:
        side = victim.getSide()
        vOffset = TestRunner.sideToVector(side)
            
        robot.position = list(np.array([victim.position[0],robot.position[1],victim.position[2]]) + (vOffset * offset))
    
    def runTest(self, supervisor) -> None:
        # self.stage == 0 and 
        if self.startTest and not self.preTest:
            Console.log_warn(f"Starting test {str(self.stage)} ({self.tests[self.stage].__class__.__name__}) ")

            params = self.tests[self.stage].preTest(supervisor)
            # G, stage, identify human, wait , wheel 1, wheel 2, human type
            message = struct.pack("c i i i i i c", b'G', self.stage, *params)
            supervisor.emitter.send(message)

            self.preTest = True

        if self.startTest and self.finishedTest:
            if self.tests[self.stage].test(supervisor):
                Console.log_pass(f"Test {str(self.stage)}/{len(self.tests)} Passed")
                self.passes += 1
            else:
                Console.log_fail(f"Test {str(self.stage)}/{len(self.tests)-1} Failed")
                if self.tests[self.stage].getTestReport() != "":
                    Console.log_fail(f"Report: {self.tests[self.stage].getTestReport()}")
                self.fails += 1
                
            self.tests[self.stage].postTest(supervisor)
                
            self.tests[self.stage].setTestReport("")
            self.startTest = False
            self.finishedTest = False
            self.preTest = False
            self.stage += 1
            
    
    def run(self, supervisor) -> None:
        if self.stage >= len(self.tests) and not self.finished:
            Console.log_info(f"Tests Finished\n{self.passes} / {len(self.tests)} Passed. ({self.fails} Fails)")
            self.finished = True
        if not self.finished:
            self.runTest(supervisor)
            
            
