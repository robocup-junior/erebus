from __future__ import annotations

from ConsoleLog import Console
from ErebusObject import ErebusObject

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainSupervisor import Erebus


class RWSender(ErebusObject):
    """Object for sending message to the robot window. Records history of 
    messages sent, in the case that they must be all re-sent (e.g. if the
    robot window is reloaded)  
    """

    def __init__(self, erebus: Erebus):
        """Initialises a new robot window message sensor object

        Args:
            erebus (Erebus): Erebus supervisor game object
        """
        super().__init__(erebus)
        self.history: list[list[str]] = []
        self.log_history: list[str] = []

    def _update_log_history(self, command: str, args: str = '') -> None:
        """Update rws history for outputting to debug logs

        Args:
            command (str): Robot window command
            args (str, optional): Optional args associated with the robot window
            command. Defaults to ''.
        """
        self.log_history.append(f"{command}\t{args}")

    def update_history(self, command: str, args: str = '') -> None:
        """Updates the robot window message history

        Args:
            command (str): Robot window command
            args (str, optional): Optional args associated with the robot window
            command. Defaults to ''.
        """
        self.history.append([command, args])
        self._update_log_history(command, args)
        
    def update_received_history(self, command: str, args: str = '') -> None:
        """Updates the robot window message received history

        Args:
            command (str): Robot window command
            args (str, optional): Optional args associated with the robot window
            command. Defaults to ''.
        """
        self._update_log_history(command, args)
        

    def send(self, command: str, args: str = '') -> None:
        """Sends a command to the robot window

        Args:
            command (str): Command to send to the robot window
            args (str, optional): Optional args associated with the robot window
            command. Defaults to ''.
        """
        wwi_msg: str = f"{command},{args}"
        Console.log_debug(f"Sent wwi message: {wwi_msg}")
        self._erebus.wwiSendText(wwi_msg)
        self.update_history(command, args)

    def send_all(self) -> None:
        """Sends the entire command history to the robot window. Used in the 
        case the browser window is reloaded, and thus the previous state
        must be recreated.
        """
        for command, args in self.history:
            self._erebus.wwiSendText(f"{command},{args}")
