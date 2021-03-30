from controller import Robot
import math
import struct

robot = Robot()
emitter = robot.getEmitter("emitter")
gps = robot.getGPS("gps")
gps.enable(32)

def sendMessage(v1, v2, v3):
    message = struct.pack('i i c', v1, v2, v3)
    emitter.send(message)

def sendVictimMessage():
    print('sent message')
    position = gps.getValues()
    sendMessage(int(position[0] * 100), int(position[2] * 100), b'U')

startTime = robot.getTime()
sentMessage = False
while robot.step(32) != -1:
    if (not sentMessage) and robot.getTime() - startTime > 5:
        sendVictimMessage()
        sentMessage = True