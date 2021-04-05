from controller import Robot
import struct

robot = Robot()
timeStep = 32


# Declare communication link between the robot and the controller
emitter = robot.getDevice("emitter")

message = struct.pack('i i c', 0, 0,'E'.encode())
emitter.send(message)
