from __future__ import annotations

import os
import shutil
import glob
import stat

from ErebusObject import ErebusObject

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainSupervisor import Erebus
from Config import Config


class Controller(ErebusObject):
    """Handles resetting of controller files
    """

    def __init__(self, erebus: Erebus, keep_control: bool = False) -> None:
        """Initialises a controller object

        Args:
            erebus (Erebus): Erebus game supervisor object
            keep_control (bool, optional): Config option to keep controllers
            (not reset after world reload). Defaults to False.
        """
        super().__init__(erebus)
        self.keep_controller: bool = keep_control

    def update_keep_controller_config(self, config: Config) -> None:
        """Update keep controller configuration option

        Args:
            config (Config): Config object holding keep controller data
        """
        self.keep_controller = config.keep_controller

    def reset_file(self, manual: bool = False) -> None:
        """Reset the robot controller 

        Args:
            manual (bool, optional): Whether manually reset via the UI. 
            Defaults to False.
        """
        path: str = os.path.dirname(os.path.abspath(__file__))
        if path[-4:] == "game":
            path = os.path.join(path, "controllers/robot0Controller")
        else:
            path = os.path.join(path, "../robot0Controller")

        files: list[str] = glob.glob(os.path.join(path, "*"))
        if self.keep_controller and not manual:
            if len(files) > 0:
                self._erebus.rws.send("loaded0")
            return

        for file_path in files:
            if not os.access(file_path, os.W_OK):
                currentPermissions = os.stat(file_path).st_mode
                os.chmod(file_path, currentPermissions |
                         stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        shutil.rmtree(path)
        os.mkdir(path)
        # 2022b bug: if a player controller crashes, the mainsupervisor will not
        # step the simulation if the robot is running a generic controller
        # Therefore, run empty controller file to fix this
        with open(os.path.join(path, "robot0Controller.py"), "w") as f:
            pass

    def reset(self) -> None:
        """Force reset the robot controller, ignoring any keep controller 
        setting

        Sends a message to robot window saying the controller has been unloaded
        """
        self.reset_file(True)
        self._erebus.rws.send("unloaded0")
