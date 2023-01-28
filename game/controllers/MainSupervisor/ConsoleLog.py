class Console:
    DEBUG_MODE = False
    
    PREFIX_DEBUG: str = "EREBUS DEBUG"
    PREFIX_PASS: str = "EREBUS PASS"
    PREFIX_FAIL: str = "EREBUS FAIL"
    PREFIX_ERROR: str = "EREBUS ERROR"
    PREFIX_WARN: str = "EREBUS WARNING"
    PREFIX_SUCC: str = "EREBUS"
    PREFIX_INFO: str = "EREBUS INFO"

    COLOR_ERROR: str = "red"
    COLOR_WARN: str = "magenta"
    COLOR_SUCC: str = "green"
    COLOR_INFO: str = "blue"
    COLOR_DEBUG: str = "yellow"
    
    COLORS = dict(
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
    
    RESET = "\033[0m"

    @staticmethod
    def log_err(msg: str) -> None:
        Console._log(Console.PREFIX_ERROR, msg, Console.COLOR_ERROR)
    
    @staticmethod
    def log_fail(msg: str) -> None:
        Console._log(Console.PREFIX_FAIL, msg, Console.COLOR_ERROR)
        
    @staticmethod
    def log_pass(msg: str) -> None:
        Console._log(Console.PREFIX_PASS, msg, Console.COLOR_SUCC)
    
    @staticmethod
    def log_succ(msg: str) -> None:
        Console._log(Console.PREFIX_SUCC, msg, Console.COLOR_SUCC)

    @staticmethod
    def log_warn(msg: str) -> None:
        Console._log(Console.PREFIX_WARN, msg, Console.COLOR_WARN)

    @staticmethod
    def log_info(msg: str) -> None:
        Console._log(Console.PREFIX_INFO, msg, Console.COLOR_INFO)
        
    @staticmethod
    def log_debug(msg: str) -> None:
        if Console.DEBUG_MODE:
            Console._log(Console.PREFIX_DEBUG, msg, Console.COLOR_DEBUG)
    
    @staticmethod
    def _log(prefix: str, msg: str, color: str):
        lines = msg.split("\n")
        for line in lines:
            # TODO remove colour prefix for stdout isn't a terminal...
            print(f"\033[{Console.COLORS[color]}m[{prefix}] {line}" + Console.RESET)
