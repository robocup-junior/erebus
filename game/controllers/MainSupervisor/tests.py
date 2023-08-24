import math
from controller import Robot
from controller import Emitter
from controller import Receiver
from controller import GPS
from controller import Motor

import struct

from typing import cast

TIME_STEP = 32


class TestRobot(Robot):
    """Webots robot controller used to run Erebus tests sent via 
    emitter/receiver messages from the MainSupervisor
    """

    def __init__(self):
        super().__init__()

        # Typing casts have to be used here to get proper type hints. Webots
        # returns Devices from `getDevice`, but e.g. an Emitter or Receiver
        # dont inherit from Device...
        self._emitter: Emitter = cast(Emitter, self.getDevice("emitter"))
        self._receiver: Receiver = cast(Receiver, self.getDevice("receiver"))
        self._receiver.enable(TIME_STEP)

        self._gps: GPS = cast(GPS, self.getDevice("gps"))
        self._gps.enable(TIME_STEP)

        self._wheel1: Motor = cast(Motor, self.getDevice("wheel1 motor"))
        self._wheel2: Motor = cast(Motor, self.getDevice("wheel2 motor"))

        self._wheel1.setPosition(float("inf"))
        self._wheel1.setVelocity(0)
        self._wheel2.setPosition(float("inf"))
        self._wheel2.setVelocity(0)

        self._stage: int = 0
        self._test_start_sent: bool = False
        self._test_start: bool = False

    def wait(self, time: float) -> None:
        """Wait for specified amount of seconds

        Args:
            time (float): Number of seconds to wait
        """
        start_time: float = self.getTime()
        while (self.getTime() - start_time < time):
            self.step(TIME_STEP)

    def run_test(self) -> None:
        """Runs a test. Communicates with the MainSupervisor to receive a test 
        to run and complete it.
        """
        # Send message to start test
        if not self._test_start_sent:
            emitter_message: bytes = struct.pack("c i", b'T', self._stage)
            self._emitter.send(emitter_message)
            self._test_start_sent = True

        # Wait for confirmation
        if self._receiver.getQueueLength() > 0:
            try:
                received_data: bytes = self._receiver.getBytes()
                data_len: int = len(received_data)
                if data_len > 8:
                    options: bytes = received_data[:26]
                    map_args: bytes = received_data[26::]
                    tup: tuple = struct.unpack('c i i i i i c c', options)
                    message = [tup[0].decode("utf-8"),
                               *tup[1:-2],
                               tup[-2].decode("utf-8"),
                               tup[-1].decode("utf-8")]
                    # Start test
                    if message[0] == 'G' and message[1] == self._stage:
                        self.test(*message[2:])
                        self.wait(0.5)
                        # Once finished, send 'F' finish command
                        message = struct.pack("c i", b'F', self._stage)
                        self._emitter.send(message)
                        self._test_start_sent = False
                        self._test_start = False
                        self._stage += 1
                self._receiver.nextPacket()
            except:
                # ignore anything else
                pass

    def test(
        self,
        identify: bool,
        wait: int,
        wheel1: int,
        wheel2: int,
        victim_type: str,
        command: str
    ) -> None:
        """Perform any actions need by a specific test (data from pre_test).

        Args:
            identify (bool): Whether to identify a victim
            wait (int): Time in seconds to wait (wheel velocities are set before
            this, and identification is set after)
            wheel1 (int): Wheel 1 velocity
            wheel2 (int): Wheel 2 velocity
            victim_type (str): Victim type to identify
            command (str): Emitter command to send to MainSupervisor
        """
        # Pack message to send to MainSupervisor
        if command == "L":
            message = struct.pack('c', 'L'.encode())
            self._emitter.send(message)
        self._wheel1.setVelocity(wheel1)
        self._wheel2.setVelocity(wheel2)
        self.wait(wait)
        if identify:
            # Convert from cm to m
            posX = int(self._gps.getValues()[0] * 100)
            posZ = int(self._gps.getValues()[2] * 100)
            # Pack the message. The estimated position of the victim is the
            # robots current position.
            message = struct.pack("i i c", posX, posZ,
                                  bytes(victim_type, "utf-8"))
            self._emitter.send(message)

    def runTests(self):
        """While the controller is running, run all tests received from the
        supervisor.
        """
        while self.step(TIME_STEP) != -1:
            self.run_test()


if __name__ == "__main__":
    robot: TestRobot = TestRobot()
    robot.runTests()
