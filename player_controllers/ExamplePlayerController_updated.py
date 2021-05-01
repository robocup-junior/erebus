from controller import Robot

timeStep = 32            # Set the time step for the simulation
max_velocity = 6.28      # Set a maximum velocity time constant

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

# Define distance sensors
s1 = robot.getDevice("ps5")
s2 = robot.getDevice("ps7")
s3 = robot.getDevice("ps0")
s4 = robot.getDevice("ps2")

'''
The names ps0, ps2, etc corresponds to the distance sensors located on the e-puck robot. 
When you create your custom robot the names should change to "distance sensor1", "distance sensor2", etc
The custom_robot.proto file should be refered for any such differences. 
'''

# Enable distance sensors N.B.: This needs to be done for every sensor
s1.enable(timeStep)
s2.enable(timeStep)
s3.enable(timeStep)
s4.enable(timeStep)


# Mini visualiser for the distance sensors on the console
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
    # Display distance values of the sensors
    # For any sensor its readings are obtained via the .getValue() funciton. 
    print(numToBlock(s1.getValue()),numToBlock(s2.getValue()),numToBlock(s3.getValue()),numToBlock(s4.getValue()))
    
    # pre-set each wheel velocity
    speed1 = max_velocity
    speed2 = max_velocity


    # Very simple (but also poor) strategy to demonstrate simple motion
    if s1.getValue() < 0.1:
        speed2 = max_velocity/2
    
    if s4.getValue() < 0.1:
        speed1 = max_velocity/2
    
    if s2.getValue() < 0.1:
            speed1 = max_velocity
            speed2 = -max_velocity
        
    # Set the wheel velocity 
    wheel1.setVelocity(speed1)              
    wheel2.setVelocity(speed2)
    
