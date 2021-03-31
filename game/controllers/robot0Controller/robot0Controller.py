from controller import Robot
import struct

robot = Robot()

gps = robot.getGPS("gps")
gps.enable(32)

emitter = robot.getEmitter("emitter")

def sendMessage(v1, v2, victimType):
    message = struct.pack('i i c', v1, v2, victimType.encode())
    emitter.send(message)

def sendVictimMessage(victimType='N'):
    global messageSent
    position = gps.getValues()

    if not messageSent:
        #robot type, position x cm, position z cm, victim type
        # The victim type is hardcoded as "H", but this should be changed to different victims for your program
        # Harmed = "H"
        # Stable = "S"
        # Unharmed = "U"
        # Heated (Temperature) = "T"
        sendMessage(int(position[0] * 100), int(position[2] * 100), victimType)
        messageSent = True

messageSent = False
startTime = robot.getTime()
while robot.step(32) != -1:
    if (robot.getTime() - startTime) > 5:
        sendVictimMessage('H')