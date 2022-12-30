from controller import Robot
import cv2
import numpy as np
import struct

class TestRobot(Robot):

    def __init__(self):
        super().__init__()
        self.timeStep = 32

        self.camera = self.getDevice("camera_centre")
        self.camera.enable(self.timeStep)

        self.emitter = self.getDevice("emitter")
        self.receiver = self.getDevice("receiver")
        self.receiver.enable(self.timeStep)


        self.gps = self.getDevice("gps")
        self.gps.enable(self.timeStep)
        
        # Define the wheels 
        self.wheel1 = self.getDevice("wheel1 motor")   # Create an object to control the left wheel
        self.wheel2 = self.getDevice("wheel2 motor") # Create an object to control the right wheel        
        self.wheel1.setPosition(float("inf"))       
        self.wheel2.setPosition(float("inf"))
        self.wheel1.setVelocity(0)
        self.wheel2.setVelocity(0)
        
        self.stage = 0
        self.testStartSent = False
        self.testStart = False
        
        # self.tests = [self.test0, self.test1, self.test2]
        self.tests = [self.test0]
        
    def wait(self, time):
        startTime = self.getTime()
        while (self.getTime() - startTime < time ):
            self.step(self.timeStep)    

    def runTest(self):
        # Send message to start test
        if not self.testStartSent:
            message = struct.pack("c i", b'T', self.stage)
            self.emitter.send(message)
            self.testStartSent = True
        
        # Wait for confirmation
        if self.receiver.getQueueLength() > 0:
            try:
                receivedData = self.receiver.getBytes()
                rDataLen = len(receivedData)
                if rDataLen > 8:
                    tup = struct.unpack('c i i i i i c', receivedData)
                    message = [tup[0].decode("utf-8"), *tup[1:-1], tup[-1].decode("utf-8")]
                    if message[0] == 'G' and message[1] == self.stage:
                        self.test0(*message[2:])
                        self.wait(0.5)
                        message = struct.pack("c i", b'F', self.stage)
                        self.emitter.send(message)
                        self.testStartSent = False
                        self.testStart = False
                        self.stage += 1
                self.receiver.nextPacket()
            except:
                # ignore anything else
                pass

    def test0(self, ident, wait, wheel1, wheel2, vtype):
        self.wheel1.setVelocity(wheel1)
        self.wheel2.setVelocity(wheel2)
        self.wait(wait)
        if ident:
            posX = int(self.gps.getValues()[0] * 100)    # Convert from cm to m
            posZ = int(self.gps.getValues()[2] * 100)
            message = struct.pack("i i c", posX, posZ, bytes(vtype, "utf-8")) # Pack the message. The estimated position of the victim is 0 cm, 0 cm.
            self.emitter.send(message)

    def runTests(self):
        while self.step(self.timeStep) != -1:
            self.runTest()

robot = TestRobot()
robot.runTests()


            
        