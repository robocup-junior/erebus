from controller import Robot
from controller import Receiver
import struct

myRobot = Robot()
timeStep = 32

receiver = myRobot.getReceiver('receiver')
receiver.enable(32)

while myRobot.step(timeStep) != -1:
	if receiver.getQueueLength() > 0:
		receivedData = receiver.getData()
		receiver.nextPacket()
		tup = struct.unpack('c', receivedData)
		print('yay')
		print(len(tup))
		print(tup[0])
		print()