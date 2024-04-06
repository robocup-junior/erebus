from typing import Optional

class Console:
    """Simple helper class to print formatted Erebus text to the console
    """
    DEBUG_MODE: bool = False

    _PREFIX_DEBUG: str = "EREBUS DEBUG"
    _PREFIX_PASS: str = "EREBUS PASS"
    _PREFIX_FAIL: str = "EREBUS FAIL"
    _PREFIX_ERROR: str = "EREBUS ERROR"
    _PREFIX_WARN: str = "EREBUS WARNING"
    _PREFIX_SUCC: str = "EREBUS"
    _PREFIX_INFO: str = "EREBUS INFO"
    _PREFIX_CONTROLLER: str = "EREBUS CONTROLLER"

    _COLOR_ERROR: str = "red"
    _COLOR_WARN: str = "magenta"
    _COLOR_SUCC: str = "green"
    _COLOR_INFO: str = "blue"
    _COLOR_CONTROLLER: str = "blue"
    _COLOR_DEBUG: str = "yellow"

    _COLORS: dict[str, int] = dict(
        list(
            zip(
                [
                    "grey",
                    "red",
                    "green",
                    "yellow",
                    "blue",
                    "magenta",
                    "cyan",
                    "white",
                ],
                list(range(30, 38)),
            )
        )
    )

    _COLOR_CODE_PREFIX: str = "\033"
    _RESET: str = "\033[0m"
    
    @staticmethod
    def update_debug_mode(state: bool) -> None:
        """Update debugging state

        Args:
            state (bool): Debug state, True to enable, False to disable
        """
        if (Console.DEBUG_MODE == state):
            return
        Console.DEBUG_MODE = state
        if Console.DEBUG_MODE:
            Console.log_warn("Erebus debug logging enabled")
        else:
            Console.log_warn("Erebus debug logging disabled")

    @staticmethod
    def log_err(msg: str, sep: Optional[str] = "\n", end = "\n") -> None:
        """Log error messages, displayed in red.

        Example output: [EREBUS ERROR] An error occurred!

        Args:
            msg (str): Message to display
            sep (Optional[str], optional): Separator used to split the message. If
            the value is None, separations are ignored.
            Defaults to "\\n".
            end (str, optional): String appended to the last value. 
            Defaults to "\\n".
        """
        Console._log(Console._PREFIX_ERROR, msg, Console._COLOR_ERROR, sep, end)

    @staticmethod
    def log_fail(msg: str, sep: Optional[str] = "\n", end = "\n") -> None:
        """Log failure messages, displayed in red.

        Example output: [EREBUS FAIL] Something failed!

        Args:
            msg (str): Message to display
            sep (Optional[str], optional): Separator used to split the message. If
            the value is None, separations are ignored.
            Defaults to "\\n".
            end (str, optional): String appended to the last value. 
            Defaults to "\\n".
        """
        Console._log(Console._PREFIX_FAIL, msg, Console._COLOR_ERROR, sep, end)

    @staticmethod
    def log_pass(msg: str, sep: Optional[str] = "\n", end = "\n") -> None:
        """Log pass messages, displayed in green.

        Example output: [EREBUS PASS] Something went well!

        Args:
            msg (str): Message to display
            sep (Optional[str], optional): Separator used to split the message. If
            the value is None, separations are ignored.
            Defaults to "\\n".
            end (str, optional): String appended to the last value. 
            Defaults to "\\n".
        """
        Console._log(Console._PREFIX_PASS, msg, Console._COLOR_SUCC, sep, end)

    @staticmethod
    def log_succ(msg: str, sep: Optional[str] = "\n", end = "\n") -> None:
        """Log success messages, displayed in green.

        Example output: [EREBUS] Something went well!

        Args:
            msg (str): Message to display
            sep (Optional[str], optional): Separator used to split the message. If
            the value is None, separations are ignored.
            Defaults to "\\n".
            end (str, optional): String appended to the last value. 
            Defaults to "\\n".
        """
        Console._log(Console._PREFIX_SUCC, msg, Console._COLOR_SUCC, sep, end)

    @staticmethod
    def log_warn(msg: str, sep: Optional[str] = "\n", end = "\n") -> None:
        """Log warning messages, displayed in purple.

        Example output: [EREBUS WARNING] We're warning you!

        Args:
            msg (str): Message to display
            sep (Optional[str], optional): Separator used to split the message. If
            the value is None, separations are ignored.
            Defaults to "\\n".
            end (str, optional): String appended to the last value. 
            Defaults to "\\n".
        """
        Console._log(Console._PREFIX_WARN, msg, Console._COLOR_WARN, sep, end)

    @staticmethod
    def log_info(msg: str, sep: Optional[str] = "\n", end = "\n") -> None:
        """Log info messages, displayed in blue.

        Example output: [EREBUS INFO] Heres some helpful info :)

        Args:
            msg (str): Message to display
            sep (Optional[str], optional): Separator used to split the message. If
            the value is None, separations are ignored.
            Defaults to "\\n".
            end (str, optional): String appended to the last value. 
            Defaults to "\\n".
        """
        Console._log(Console._PREFIX_INFO, msg, Console._COLOR_INFO, sep, end)

    @staticmethod
    def log_controller(msg: str, sep: Optional[str] = "\n", end = "\n") -> None:
        """Log controller messages, displayed in blue.

        This is reserved for displaying stdout from controller docker containers

        Example output: [EREBUS CONTROLLER] My controller is saying something...

        Args:
            msg (str): Message to display
            sep (Optional[str], optional): Separator used to split the message. If
            the value is None, separations are ignored.
            Defaults to "\\n".
            end (str, optional): String appended to the last value. 
            Defaults to "\\n".
        """
        Console._log(Console._PREFIX_CONTROLLER, msg.strip(), 
                     Console._COLOR_CONTROLLER, sep, end)

    @staticmethod
    def log_debug(msg: str, sep: Optional[str] = "\n", end = "\n") -> None:
        """Log debug messages, displayed in yellow. 

        These are only displayed if debug logging is enabled.

        Example output: [EREBUS WARNING] We're warning you!

        Args:
            msg (str): Message to display
            sep (Optional[str], optional): Separator used to split the message. If
            the value is None, separations are ignored.
            Defaults to "\\n".
            end (str, optional): String appended to the last value. 
            Defaults to "\\n".
        """
        if Console.DEBUG_MODE:
            Console._log(Console._PREFIX_DEBUG, msg, Console._COLOR_DEBUG, 
                         sep, end)

    @staticmethod
    def _log(
        prefix: str, 
        msg: str, 
        color: str,
        sep: Optional[str],
        end: str
    ) -> None:
        """Log messages, with a specified prefix and color. Lines are separated
        into individual prints via the separator

        Example output: [EREBUS WARNING] We're warning you!

        Args:
            msg (str): Message to display
            sep (Optional[str]): Separator used to split the message. If
            the value is None, separations are ignored.
            end (str): String appended to the last value.
        """
        if sep is None:
            lines: list[str] = [msg]
        else:
            lines: list[str] = msg.split(sep)
        for line in lines:
            # TODO remove colour prefix for stdout isn't a terminal...
            print(
                f"{Console._COLOR_CODE_PREFIX}[{Console._COLORS[color]}m[{prefix}] {line}{Console._RESET}",
                end=end)
