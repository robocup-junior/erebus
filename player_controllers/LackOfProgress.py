from controller import Robot
import struct

timeStep = 32            # Set the time step for the simulation

# Make robot controller instance
robot = Robot()

'''
Every component on the robot is initialised through robot.getDevice("name") 
If the "name" does not register well, check the custom_robot.proto file in the /games/protos folder
There you will find the configuration for the robot including each component name
'''

# Define the wheels 
wheel1 = robot.getDevice("wheel1 motor")   # Create an object to control the left wheel
wheel2 = robot.getDevice("wheel2 motor") # Create an object to control the right wheel

# Set the wheels to have infinite rotation 
wheel1.setPosition(float("inf"))       
wheel2.setPosition(float("inf"))

emitter = robot.getDevice("emitter")
receiver = robot.getDevice("receiver")
receiver.enable(timeStep) # Enable the receiver. Note that the emitter does not need to call enable()

lastRequestTime = robot.getTime()
while robot.step(timeStep) != -1:
    if robot.getTime() - lastRequestTime > 1:
        message = struct.pack('c', 'L'.encode()) # Send a LoP command once a second
        emitter.send(message)
        lastRequestTime = robot.getTime()
    
    if receiver.getQueueLength() > 0: # Check if receiver queue size is not empty
        receivedData = receiver.getBytes()
        # Get length of bytes
        rDataLen = len(receivedData)
        if rDataLen == 1:
            tup = struct.unpack('c', receivedData)
            if tup[0].decode("utf-8") == 'L':
                print("Detected Lack of Progress!") 
        receiver.nextPacket() # Discard the current data packet
