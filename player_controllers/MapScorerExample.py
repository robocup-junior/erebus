from controller import Robot
from PIL import Image
import numpy as np
import struct

timeStep = 32            # Set the time step for the simulation
max_velocity = 6.28      # Set a maximum velocity time constant

robot = Robot()

emitter = robot.getDevice("emitter")

while robot.step(timeStep) != -1:

    # Test array
    subMatrix = np.array([
        [0,0,0,1,5,1,0,0,0,1,5,1],
        [0,0,0,1,5,1,0,0,0,1,5,1],
        [0,0,0,1,5,1,1,1,1,1,5,1],
        [0,0,0,1,3,3,3,3,3,3,3,1],
        [0,1,1,1,3,1,1,1,3,3,3,1],
        [0,1,3,1,3,1,3,1,3,3,3,1],
        [0,1,3,1,3,1,3,1,1,1,3,1],
        [0,1,3,3,3,3,3,2,2,2,3,1],
        [0,1,1,1,1,1,1,1,1,1,1,1]
    ])

    # Get shape
    s = subMatrix.shape
    # Get shape as bytes
    s_bytes = struct.pack('2i',*s)
    # Get matrix as bytes
    sub_bytes = subMatrix.flatten('f').tobytes()

    # Add togeather, shape + map
    a_bytes = s_bytes + sub_bytes
    # Send
    emitter.send(a_bytes)
    
    exit_message = struct.pack('iic', 0, 0, b'M')
    emitter.send(exit_message)
    break
    
    
