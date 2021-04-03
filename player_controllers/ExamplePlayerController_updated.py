from controller import Robot
from PIL import Image
import numpy as np
import time


timeStep = 32            # Set the time step for the simulation
max_velocity = 6.28      # Set a maximum velocity time constant

robot = Robot()


# wheel1 = robot.getMotor("wheel1 motor")   # Create an object to control the left wheel
# wheel2 = robot.getMotor("wheel2 motor") # Create an object to control the right wheel
# s1 = robot.getDistanceSensor("sensor1")
# s2 = robot.getDistanceSensor("sensor2")
# s3 = robot.getDistanceSensor("sensor3")
# s4 = robot.getDistanceSensor("sensor4")
# s5 = robot.getDistanceSensor("sensor5")
# s1.enable(timeStep)
# s2.enable(timeStep)
# s3.enable(timeStep)
# s4.enable(timeStep)
# s5.enable(timeStep)
# # wheel3 = robot.getMotor("wheel3 motor") # Create an object to control the right wheel
# # wheel4 = robot.getMotor("wheel4 motor") # Create an object to control the right wheel

# # Declare GPS
# gps = robot.getGPS("gps")
# gps.enable(timeStep)

# # colour_camera = robot.getCamera("colour sensor")
# # colour_camera.enable(timeStep)
# # camera = robot.getCamera("camera")
# # camera.enable(timeStep)

# wheel1.setPosition(float("inf"))
# wheel1.setVelocity(max_velocity)              # Send the speed values we have chosen to the robot
# wheel2.setPosition(float("inf"))
# wheel2.setVelocity(max_velocity)
# # wheel3.setPosition(float("inf"))
# # wheel3.setVelocity(max_velocity)
# # wheel4.setPosition(float("inf"))
# # wheel4.setVelocity(max_velocity)

# # Declare heat/temperature sensor
# left_heat_sensor = robot.getLightSensor("heat_sensor1")
# right_heat_sensor = robot.getLightSensor("heat_sensor2")
# left_heat_sensor.enable(timeStep)
# right_heat_sensor.enable(timeStep)

# acc = robot.getAccelerometer("accelerometer")
# acc.enable(timeStep)

# gyro = robot.getGyro("gyro")
# gyro.enable(timeStep)

lidar = robot.getLidar("lidar")
lidar.enable(timeStep)


def numToBlock(num):
    if num > 0.7:
        return '▁'
    elif num > 0.6:
        return '▂'
    elif num > 0.5:
        return '▃'
    elif num > 0.4:
        return '▄'
    elif num > 0.3:
        return '▅'
    elif num > 0.2:
        return '▆'
    elif num > 0.1:
        return '▇'
    elif num > 0:
        return '█'


start = robot.getTime()
while robot.step(timeStep) != -1:
    # print(numToBlock(s5.getValue()),numToBlock(s4.getValue()),numToBlock(s3.getValue()),numToBlock(s2.getValue()),numToBlock(s1.getValue()), gps.getValues())
    # print(left_heat_sensor.getValue(),right_heat_sensor.getValue())
    # print(acc.getValues(),gyro.getValues())
    print(robot.getTime() - start)
    # if (robot.getTime() - start) > 6:
    #     print("\n\n\n")
    #     print(lidar.getHorizontalResolution(), lidar.getNumberOfLayers())
    #     arr = lidar.getRangeImageArray ()
    #     # for row in arr:
    #     #     print([round(x, 2) for x in row])
    #     arr = np.rot90(np.array(arr),k=1,axes=(1,0))
    #     arr = arr[::,:64]
    #     print(arr)
    #     # for row in arr:
    #     #     print(row)

    #     img = Image.fromarray(arr, 'L')
    #     img.save('my.png')
    #     img.show()
    #     break
    
