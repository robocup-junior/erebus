import os
import datetime

from ConsoleLog import Console
from Robot import Robot
from Tools import get_file_path


class Logger:

    @staticmethod
    def _create_log_str(robot: Robot, max_time: int):
        """Create log text for log file
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
    def write_log(robot: Robot, max_time: int) -> None:
        """Write log file to the project's log directory
        """
        # Get log text
        log_str: str = Logger._create_log_str(robot, max_time)
        # Get relative path to logs dir
        log_dir_path: str = get_file_path("logs/", "../../logs/")

        # Create file name using date and time
        file_date: datetime.datetime = datetime.datetime.now()
        file_name: str = file_date.strftime("gameLog %m-%d-%y %H,%M,%S")

        # Get log file path
        log_file_path: str = os.path.join(log_dir_path, f"{file_name}.txt")

        try:
            with open(log_file_path, "w") as f:
                f.write(log_str)
        except Exception as e:
            Console.log_err(f"Couldn't write log file. Most likely, the log "
                            f"dir: {log_dir_path} is missing")
            Console.log_err(f"\t{e}")
