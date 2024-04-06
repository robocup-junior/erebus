from ast import List
import os
import datetime

from ConsoleLog import Console
from Robot import Robot
from RobotWindowSender import RWSender
from Tools import get_file_path


class Logger:

    @staticmethod
    def _create_robot_log_str(robot: Robot, max_time: int) -> str:
        """Create log text for robot log file
        """
        # Get robot events
        events: str = robot.get_log_str()

        log_str = (
            f"MAX_GAME_DURATION: {int(max_time/60)}:00\n"
            f"ROBOT_0_SCORE: {round(robot.get_score(), 2)}\n\n"
            f"ROBOT_0: {robot.name}\n"
            f"{events}"
        )

        return log_str

    @staticmethod
    def _write_robot_history_log(robot: Robot, max_time: int) -> None:
        """Write robot history log file to the project's log directory

        Args:
            robot (Robot): Robot object
            max_time (int): The current world's max game time 
        """
        # Get log text
        log_str: str = Logger._create_robot_log_str(robot, max_time)
        # Get relative path to logs dir
        log_dir_path: str = get_file_path("logs/", "../../logs/")

        # Create file name using date and time
        file_date: datetime.datetime = datetime.datetime.now()
        file_name: str = file_date.strftime("gameLog %m-%d-%y %H,%M,%S")

        # Get log file path
        log_file_path: str = os.path.join(log_dir_path, f"{file_name}.txt")

        try:
            # Create log directory if it doesn't exist
            os.makedirs(log_dir_path, exist_ok=True)
            with open(log_file_path, "w") as f:
                f.write(log_str)
        except Exception as e:
            Console.log_err(f"Couldn't write log file. Most likely, the log "
                            f"dir: {log_dir_path} is missing")
            Console.log_err(f"\t{e}")
            
    @staticmethod
    def _create_rws_log_str(rws: RWSender) -> str:
        """Create log text for robot window log file
        """
        return '\n'.join(str(record) for record in rws.log_history)
    
    @staticmethod
    def _write_rws_log(rws: RWSender) -> None:
        """Write debug log for messages sent between the robot window and
        the Erebus engine/supervisor

        Args:
            rws (RWSender): Supervisor's robot window sender object
        """
        # Get log text
        log_str: str = Logger._create_rws_log_str(rws)
        # Get relative path to logs dir
        log_dir_path: str = get_file_path("logs/debug/", "../../logs/debug/")

        # Create file name using date and time
        file_date: datetime.datetime = datetime.datetime.now()
        file_name: str = file_date.strftime("rwsLog %m-%d-%y %H,%M,%S")

        # Get log file path
        log_file_path: str = os.path.join(log_dir_path, f"{file_name}.txt")

        try:
            # Create log directory if it doesn't exist
            os.makedirs(log_dir_path, exist_ok=True)
            with open(log_file_path, "w") as f:
                f.write(log_str)
        except Exception as e:
            Console.log_err(f"Couldn't write log file. Most likely, the log "
                            f"dir: {log_dir_path} is missing")
            Console.log_err(f"\t{e}")
    
    @staticmethod
    def write_log(robot: Robot, rws: RWSender, max_time: int) -> None:
        """Write log files for the robot history events, and the debug
        robot window log files for recording messages sent between
        the robot window and the Erebus supervisor

        Args:
            robot (Robot): Game robot object
            rws (RWSender): Supervisor's robot window sender object
            max_time (int): The current world's max game time
        """
        Logger._write_robot_history_log(robot, max_time)
        Logger._write_rws_log(rws)
