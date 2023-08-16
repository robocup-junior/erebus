class Config():
    def __init__(self, configData, path):
        
        # configData
        # [0]: Keep controller/robot files
        # [1]: Disable auto LoP
        # [2]: Recording
        # [3]: Automatic camera
        # [4]: Keep remote
        # [5]: Docker path
                
        self.path = path
        
        self.keep_controller = bool(int(configData[0]))
        self.disableLOP = bool(int(configData[1]))
        self.recording = bool(int(configData[2]))
        self.automatic_camera = bool(int(configData[3]))
        self.keep_remote = False # Keep v23 compatibility
        self.docker_path = ""
        
        if len(configData) >= 5:
            self.keep_remote = bool(int(configData[4]))
            self.docker_path = str(configData[5])