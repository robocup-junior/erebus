from ConsoleLog import Console


class Config():
    """Holds data for the settings configuration of Erebus
    """

    def __init__(self, config_data: list[str], path: str):
        """Initialises config settings data

        Args:
            config_data (list[str]): List of config settings
            path (str): Path to config.txt file
        """
        # config_data format
        # [0]: Keep controller/robot files
        # [1]: Disable auto LoP
        # [2]: Recording
        # [3]: Automatic camera
        # [4]: Keep remote
        # [5]: Debug enabled
        # [6]: Docker path

        self.path: str = path

        self.keep_controller: bool = bool(int(config_data[0]))
        self.disable_lop: bool = bool(int(config_data[1]))
        self.recording: bool = bool(int(config_data[2]))
        self.automatic_camera: bool = bool(int(config_data[3]))
        
        # Keep v23 compatibility
        self.keep_remote: bool = False  
        self.docker_path: str = ""

        if len(config_data) >= 5:
            self.keep_remote = bool(int(config_data[4]))
            Console.update_debug_mode(bool(int(config_data[5])))
            self.docker_path = str(config_data[6])
