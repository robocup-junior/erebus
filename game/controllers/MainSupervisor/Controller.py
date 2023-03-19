import os
import shutil
import glob
import stat


class Controller():
    def __init__(self, keepControl = False):
        self.keepController = keepControl
    
    def updateKeepControllerConfig(self, config):
        self.keepController = config.keep_controller
    
    def resetFile(self, supervisor, manual=False) -> None:
        '''Remove the controller'''
        path = os.path.dirname(os.path.abspath(__file__))
        if path[-4:] == "game":
            path = os.path.join(path, "controllers/robot0Controller")
        else:
            path = os.path.join(path, "../robot0Controller")

        files = glob.glob(os.path.join(path, "*"))
        if self.keepController and not manual:
            if len(files) > 0:
                supervisor.rws.send("loaded0")
            return

        for file_path in files:
            if not os.access(file_path, os.W_OK):
                currentPermissions = os.stat(file_path).st_mode
                os.chmod(file_path, currentPermissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            
        shutil.rmtree(path)
        os.mkdir(path)
        # 2022b bug: if a player controller crashes, the mainsupervisor will not
        # step the simulation if the robot is running a generic controller
        # Therefore, run empty controller file to fix this 
        with open(os.path.join(path, "robot0Controller.py"), "w") as f:
            pass
    
    def reset(self, supervisor) -> None:
        '''Send message to robot window to say that controller has been unloaded'''
        self.resetFile(supervisor, True)
        supervisor.rws.send("unloaded0")
