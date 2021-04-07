from controller import Robot
import struct

robot = Robot()
timeStep = 32


# Declare communication link between the robot and the controller
emitter = robot.getDevice("emitter")

message = struct.pack('c', 'E'.encode())
emitter.send(message)
