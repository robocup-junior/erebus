from enum import Enum
from controller import Robot, Keyboard
import struct
import numpy as np

ROBOT_NUM = 0

subMatrix = np.array([
        ['1', '1', '1', '1', '1', '1', '1', 'U', '1', 'H', '1', '1', '1', '1', '1', 'S', '1'],
        ['1', '5', '0', '5', '0', 'b', '0', 'b', '0', '0', '0', '0', '0', '3', '0', '3', '1'],
        ['1', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '1'],
        ['1', '5', '0', '5', '0', 'b', '0', 'b', '0', '0', '0', '0', '0', '3', '0', '3', '1'],
        ['1', '0', '0', '0', '0', '0', '0', '0', '1', '0', '0', '0', '0', '0', '1', '1', '1'],
        ['1', '0', '0', '0', '0', '2', '0', '2', '1', 'p', '0', 'p', '0', '4', '0', '4', '1'],
        ['1', '0', '0', '0', '0', '0', '0', '0', '1', '0', '0', '0', '0', '0', '0', '0', '1'],
        ['F', '0', '0', '0', '0', '2', '0', '2', '1', 'p', '0', 'p', '0', '4', '0', '4', '1'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', '0', '0', '0', '1', '1', '1', '1', '1'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', '0', '0', '0', '0', '0', '1', '0', '1'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', '0', '0', '0', '0', '0', '0', '1', '1'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', '0', '0', '0', '0', '0', '0', '0', 'P'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', '0', '0', '0', '0', '0', '0', '0', '1'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', 'r', '0', 'r', '0', '0', '0', '0', '1'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', '0', '0', '0', '1', '1', '0', 'C', '1'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', 'r', '0', 'r', '0', '0', '1', '0', '1'],
        ['*', '*', '*', '*', '*', '*', '*', '*', '*', '1', '1', '1', '1', '1', '1', '1', '1'],
        ['*', '*', '*', '*', '*', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
        ['*', '*', '*', '*', '*', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
        ['*', '*', '*', '*', '*', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
        ['*', '*', '*', '*', '*', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0']
    ])

class WaitingStateEnum(Enum):
    NONE = "none"
    GAME_INFO = "game_info"
    RELOCATION = "relocation"
    ORDER= "order"

timeStep = 32            # Set the time step for the simulation

# Make robot controller instance
robot = Robot()
keyboard = Keyboard(timeStep)

emitter = robot.getDevice("emitter")
receiver = robot.getDevice("receiver")
receiver.enable(timeStep) # Enable the receiver. Note that the emitter does not need to call enable()

gps = robot.getDevice("gps") # Step 2: Retrieve the sensor, named "gps", from the robot. Note that the sensor name may differ between robots
gps.enable(timeStep) # Step 3: Enable the sensor, using the timestep as the update rate

# Define the wheels 
wheel1 = robot.getDevice("wheel1 motor")   # Create an object to control the left wheel
wheel2 = robot.getDevice("wheel2 motor") # Create an object to control the right wheel

# Set the wheels to have infinite rotation 
wheel1.setPosition(float("inf"))       
wheel2.setPosition(float("inf"))

waiting_state = WaitingStateEnum.NONE
is_key_down = False

robot_playing = 0

def send_game_request(*args):
    message = struct.pack('c', b'G') # Send game info request once a second
    emitter.send(message)

def get_game_info():
    global waiting_state
    while receiver.getQueueLength() > 0:
        receivedData = receiver.getBytes()
        rDataLen = len(receivedData)
        if rDataLen == 20:
            tup = struct.unpack('c f i i f', receivedData)
            if tup[0].decode("utf-8", errors="ignore") == 'G':
                print(f"-> [INFO JUEGO] Score: {tup[1]:.1f} | Tiempo Restante: {tup[2]}s | Tiempo Real: {tup[3]}s | Batería: {tup[4]:.1f}%")
                waiting_state = WaitingStateEnum.NONE
                
        receiver.nextPacket()
        
def send_relo(*args):
    message = struct.pack('c', b'L')
    emitter.send(message)
        
def get_relo_info():
    global waiting_state
    if receiver.getQueueLength() > 0:
        receivedData = receiver.getBytes()
        # Get length of bytes
        rDataLen = len(receivedData)
        if rDataLen == 1:
            tup = struct.unpack('c', receivedData)
            if tup[0].decode("utf-8") == 'L':
                print("Detected Lack of Progress!") 
        receiver.nextPacket() # Discard the current data packet
        waiting_state = WaitingStateEnum.NONE

def get_order_info():
    global waiting_state
    if receiver.getQueueLength() > 0:
        receivedData = receiver.getBytes()
        # Get length of bytes
        rDataLen = len(receivedData)
        print(f"Robot {ROBOT_NUM} received data length: {rDataLen}")
        if rDataLen == 6:
            tup = struct.unpack('c c c c c c', receivedData)
            if tup[0].decode("utf-8") == 'O':
                print(f"Robot {ROBOT_NUM} Order received!", tup[1].decode("utf-8"), tup[2].decode("utf-8"), tup[3].decode("utf-8"), tup[4].decode("utf-8"), tup[5].decode("utf-8"))
        elif rDataLen == 4:
            tup = struct.unpack('c c c c', receivedData)
            if tup[0].decode("utf-8") == 'O':
                print("Order received!", tup[1].decode("utf-8"), tup[2].decode("utf-8"), tup[3].decode("utf-8"))
        receiver.nextPacket() # Discard the current data packet
        waiting_state = WaitingStateEnum.NONE

def send_exit(*args):
    print("Sending exit message")
    message = struct.pack('c', 'E'.encode())
    emitter.send(message)

def send_victim(*args):
    position = gps.getValues() # Get the current gps position of the robot
    x = int(position[0] * 100) # Get the xy coordinates, multiplying by 100 to convert from meters to cm 
    y = int(position[2] * 100) # We will use these coordinates as an estimate for the victim's position
    message = struct.pack('i i c', x, y, chr(args[0][0]).encode()) # Send game info request once a second
    emitter.send(message)
    
def send_map(*args):
    s = subMatrix.shape
    # Get shape as bytes
    s_bytes = struct.pack('2i',*s)

    # Flattening the matrix and join with ','
    flatMap = ','.join(subMatrix.flatten())
    # Encode
    sub_bytes = flatMap.encode('utf-8')

    # Add togeather, shape + map
    a_bytes = s_bytes + sub_bytes

    # Send map data
    emitter.send(a_bytes)
    # Send map evaluate request
    map_evaluate_request = struct.pack('c', b'M')
    emitter.send(map_evaluate_request)


def send_change_player(*args):
    global robot_playing
    print(f"NOW USING ROBOT {chr(args[0][0])}")
    robot_playing = int(chr(args[0][0]))
    
    
def send_test(*args):
    # message = struct.pack('c i i i', 'A'.encode(), 255, 0, 0) # 'A' is my unique command to let my controllers know robot 0 has sent data
    print("Sending test message to the other robot")
    message = struct.pack('c c c c c c','O'.encode(), 'Y'.encode(), 'Y'.encode(), 'G'.encode(), 'G'.encode(), 'R'.encode()) # 'M', 'H', 'U', 'S' is a test message
    emitter.send(message)


def handle_key_press(key, func, waiting_state_setter, *args):
    global waiting_state, is_key_down
    if key_input in key:
        func(args)
        waiting_state = waiting_state_setter
        is_key_down = True

def manage_waiting_state(state):
    if state == WaitingStateEnum.GAME_INFO:
        get_game_info()
    if state == WaitingStateEnum.RELOCATION:
        get_relo_info()
    if state == WaitingStateEnum.ORDER:
        get_order_info()

print(
    """
    --------------------------------------------------------
    Robot 0 Key bindings:
        - 0, 1: change to robot 0 (blue), robot 1 (red)
        - G: Game info
        - R: Relocate
        - E: Exit
        - T: Send test msg to the other robot
        - S, H, U: Send victim identification
        - F, C, P, O: Cognitive Targets
        - Arrows Up, Down, Left, Right: Move robot
        - M: Send Map data
    --------------------------------------------------------

    """
)


while robot.step(timeStep) != -1:
    wheel_velos = [0,0]
    
    key_input = keyboard.getKey()
    
    if key_input == -1:
        is_key_down = False
    
    if is_key_down == False:
        handle_key_press([ord('0'), ord('1'), ord('2')], send_change_player, WaitingStateEnum.NONE, key_input)
        
        if robot_playing != ROBOT_NUM:
            continue
        
        handle_key_press([ord('G')], send_game_request, WaitingStateEnum.GAME_INFO)
        handle_key_press([ord('R')], send_relo, WaitingStateEnum.RELOCATION)
        handle_key_press([ord('E')], send_exit, WaitingStateEnum.NONE)
        handle_key_press([ord('M')], send_map, WaitingStateEnum.NONE)
        handle_key_press([ord('T')], send_test, WaitingStateEnum.ORDER)
        
        handle_key_press([ord('S'), ord('H'), ord('U'), ord('F'), ord('C'), ord('P'), ord('O')], send_victim, WaitingStateEnum.NONE, key_input)
        
        if key_input == Keyboard.UP:
            wheel_velos = [6,6]
        if key_input == Keyboard.DOWN:
            wheel_velos = [-6, -6]
        if key_input == Keyboard.RIGHT:
            wheel_velos = [-6,6]
        if key_input == Keyboard.LEFT:
            wheel_velos = [6,-6]
            
        wheel1.setVelocity(wheel_velos[0])              
        wheel2.setVelocity(wheel_velos[1])
    
    
    manage_waiting_state(waiting_state)