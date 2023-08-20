from __future__ import annotations

from Tools import *

from typing import TYPE_CHECKING

if TYPE_CHECKING:    
    from MainSupervisor import Erebus

class Recorder:
    """Helper class for recording Erebus simulation runs
    """

    COLOR_WHITE: int = 0xdff9fb
    COLOR_GREEN: int = 0x4cd137
    COLOR_RED: int = 0xe74c3c

    ID_SCORE: int = 0
    ID_CLOCK: int = 1
    ID_COUNT_DOWN: int = 4

    @staticmethod
    def reset_countdown(erebus: Erebus):
        """Reset/remove the countdown label

        Args:
            erebus (Erebus): Erebus game supervisor object
        """
        erebus.setLabel(Recorder.ID_COUNT_DOWN, "", 
                        0.2, 0, 0.4, Recorder.COLOR_RED, 0)

    @staticmethod
    def start_recording(erebus: Erebus):
        """Start recording. Recordings are stored in the Erebus root directory
        as `recording.mp4`.

        Args:
            erebus (Erebus): Erebus game supervisor object
        """
        path: str = get_file_path("../recording.mp4", "../../../recording.mp4")
        
        platform_ver: str = f'Platform Version: {erebus.version}'
        max_clock: str = ("Clock: " + 
                          str(int(int(erebus.max_time)/60)).zfill(2) + ":" + 
                          str(int(int(erebus.max_time) % 60)).zfill(2))

        erebus.movieStartRecording(
            path, width=1280, height=720, quality=70,
            codec=0, acceleration=1, caption=False,
        )

        erebus.setLabel(Recorder.ID_SCORE, platform_ver, 
                        0, 0, 0.05, Recorder.COLOR_WHITE, 0)
        erebus.wait(0.5)
        erebus.setLabel(Recorder.ID_COUNT_DOWN, "3", 0.4,
                        0, 0.7, Recorder.COLOR_RED, 0)
        erebus.wait(1)
        erebus.setLabel(Recorder.ID_COUNT_DOWN, "2", 0.4,
                        0, 0.7, Recorder.COLOR_RED, 0)
        erebus.wait(1)
        erebus.setLabel(Recorder.ID_COUNT_DOWN, "1", 0.4,
                        0, 0.7, Recorder.COLOR_RED, 0)
        erebus.wait(1)
        erebus.setLabel(Recorder.ID_COUNT_DOWN, "START",
                        0.2, 0, 0.7, Recorder.COLOR_RED, 0)
        erebus.wait(1)
        erebus.setLabel(Recorder.ID_SCORE, "Score: 0",
                        0.15, 0, 0.15, Recorder.COLOR_GREEN, 0)
        erebus.setLabel(Recorder.ID_CLOCK, max_clock,
                        0.4, 0, 0.15, Recorder.COLOR_GREEN, 0)

    @staticmethod
    def update(erebus: Erebus):
        """Update the recording score and clock labels

        Args:
            erebus (Erebus): Erebus game supervisor object
        """
        timeRemaining: int = erebus.max_time - int(erebus.time_elapsed)
        score: str = "Score: " + str(round(erebus.robot_obj.get_score(), 2))
        clock: str = ("Clock: " + 
                      str(int(int(timeRemaining)/60)).zfill(2) + ":" + 
                      str(int(int(timeRemaining) % 60)).zfill(2))
        
        erebus.setLabel(Recorder.ID_SCORE, score, 
                        0.15, 0, 0.15, Recorder.COLOR_GREEN, 0)
        erebus.setLabel(Recorder.ID_CLOCK, clock, 
                        0.4, 0, 0.15, Recorder.COLOR_GREEN, 0)

    @staticmethod
    def stop_recording(erebus: Erebus):
        """Stops the recording. Displays the final score and time.

        Args:
            erebus (Erebus): Erebus game supervisor object
        """
        score: str = "Score: " + str(round(erebus.robot_obj.get_score(), 2))
        game_time: str = ("Game time: " + 
                          str(int(int(erebus.time_elapsed)/60)).zfill(2) + ":" + 
                          str(int(int(erebus.time_elapsed) % 60)).zfill(2))
        
        
        erebus.setLabel(Recorder.ID_SCORE, score, 
                        0.15, 0.3, 0.3, Recorder.COLOR_RED, 0)
        erebus.setLabel(Recorder.ID_CLOCK, game_time, 
                        0.15, 0.45, 0.3, Recorder.COLOR_RED, 0)
        erebus.wait(5)
        erebus.movieStopRecording()
