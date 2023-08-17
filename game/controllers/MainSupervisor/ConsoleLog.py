class Console:
    """Simple helper class to print formatted Erebus text to the console
    """
    DEBUG_MODE: bool = False

    PREFIX_DEBUG: str = "EREBUS DEBUG"
    PREFIX_PASS: str = "EREBUS PASS"
    PREFIX_FAIL: str = "EREBUS FAIL"
    PREFIX_ERROR: str = "EREBUS ERROR"
    PREFIX_WARN: str = "EREBUS WARNING"
    PREFIX_SUCC: str = "EREBUS"
    PREFIX_INFO: str = "EREBUS INFO"
    PREFIX_CONTROLLER: str = "EREBUS CONTROLLER"

    COLOR_ERROR: str = "red"
    COLOR_WARN: str = "magenta"
    COLOR_SUCC: str = "green"
    COLOR_INFO: str = "blue"
    COLOR_CONTROLLER: str = "blue"
    COLOR_DEBUG: str = "yellow"

    COLORS: dict[str, int] = dict(
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

    COLOR_CODE_PREFIX: str = "\033"
    RESET: str = "\033[0m"

    @staticmethod
    def log_err(msg: str, sep: str = "\n") -> None:
        """Log error messages, displayed in red.

        Example output: [EREBUS ERROR] An error occurred!

        Args:
            msg (str): Message to display
            sep (str, optional): Separator used to split the message. 
            Defaults to "\n".
        """
        Console._log(Console.PREFIX_ERROR, msg, Console.COLOR_ERROR, sep)

    @staticmethod
    def log_fail(msg: str, sep: str = "\n") -> None:
        """Log failure messages, displayed in red.

        Example output: [EREBUS FAIL] Something failed!

        Args:
            msg (str): Message to display
            sep (str, optional): Separator used to split the message. 
            Defaults to "\n".
        """
        Console._log(Console.PREFIX_FAIL, msg, Console.COLOR_ERROR, sep)

    @staticmethod
    def log_pass(msg: str, sep: str = "\n") -> None:
        """Log pass messages, displayed in green.

        Example output: [EREBUS PASS] Something went well!

        Args:
            msg (str): Message to display
            sep (str, optional): Separator used to split the message. 
            Defaults to "\n".
        """
        Console._log(Console.PREFIX_PASS, msg, Console.COLOR_SUCC, sep)

    @staticmethod
    def log_succ(msg: str, sep: str = "\n") -> None:
        """Log success messages, displayed in green.

        Example output: [EREBUS] Something went well!

        Args:
            msg (str): Message to display
            sep (str, optional): Separator used to split the message. 
            Defaults to "\n".
        """
        Console._log(Console.PREFIX_SUCC, msg, Console.COLOR_SUCC, sep)

    @staticmethod
    def log_warn(msg: str, sep: str = "\n") -> None:
        """Log warning messages, displayed in purple.

        Example output: [EREBUS WARNING] We're warning you!

        Args:
            msg (str): Message to display
            sep (str, optional): Separator used to split the message. 
            Defaults to "\n".
        """
        Console._log(Console.PREFIX_WARN, msg, Console.COLOR_WARN, sep)

    @staticmethod
    def log_info(msg: str, sep: str = "\n") -> None:
        """Log info messages, displayed in blue.

        Example output: [EREBUS INFO] Heres some helpful info :)

        Args:
            msg (str): Message to display
            sep (str, optional): Separator used to split the message. 
            Defaults to "\n".
        """
        Console._log(Console.PREFIX_INFO, msg, Console.COLOR_INFO, sep)

    @staticmethod
    def log_controller(msg: str, sep: str = "\n") -> None:
        """Log controller messages, displayed in blue.

        This is reserved for displaying stdout from controller docker containers

        Example output: [EREBUS CONTROLLER] My controller is saying something...

        Args:
            msg (str): Message to display
            sep (str, optional): Separator used to split the message. 
            Defaults to "\n".
        """
        Console._log(Console.PREFIX_CONTROLLER,
                     msg.strip(), Console.COLOR_CONTROLLER, sep)

    @staticmethod
    def log_debug(msg: str, sep: str = "\n") -> None:
        """Log debug messages, displayed in yellow. 

        These are only displayed if debug logging is enabled.

        Example output: [EREBUS WARNING] We're warning you!

        Args:
            msg (str): Message to display
            sep (str, optional): Separator used to split the message. 
            Defaults to "\n".
        """
        if Console.DEBUG_MODE:
            Console._log(Console.PREFIX_DEBUG, msg, Console.COLOR_DEBUG, sep)

    @staticmethod
    def _log(prefix: str, msg: str, color: str, sep: str) -> None:
        """Log messages, with a specified prefix and color. Lines are separated
        into individual prints via the separator

        Example output: [EREBUS WARNING] We're warning you!

        Args:
            msg (str): Message to display
            sep (str): Separator used to split the message
        """
        lines = msg.split(sep)
        for line in lines:
            # TODO remove colour prefix for stdout isn't a terminal...
            print(
                f"{Console.COLOR_CODE_PREFIX}[{Console.COLORS[color]}m[{prefix}] {line}{Console.RESET}")
