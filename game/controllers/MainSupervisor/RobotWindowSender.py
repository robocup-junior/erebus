from controller import Supervisor

from ConsoleLog import Console

class RWSender:
    """Object for sending message to the robot window. Records history of 
    messages sent, in the case that they must be all re-sent (e.g. if the
    robot window is reloaded)  
    """

    def __init__(self, supervisor: Supervisor):
        self.history: list[list[str]] = []
        self.supervisor: Supervisor = supervisor

    def update_history(self, command: str, args: str = ''):
        """Updates the robot window message history

        Args:
            command (str): Robot window command
            args (str, optional): Optional args associated with the robot window
            command. Defaults to ''.
        """
        self.history.append([command, args])

    def send(self, command: str, args: str = ''):
        """Sends a command to the robot window

        Args:
            command (str): Command to send to the robot window
            args (str, optional): Optional args associated with the robot window
            command. Defaults to ''.
        """
        wwi_msg: str = f"{command},{args}"
        Console.log_debug(f"Sent wwi message: {wwi_msg}")
        self.supervisor.wwiSendText(wwi_msg)
        self.update_history(command, args)

    def send_all(self):
        """Sends the entire command history to the robot window. Used in the 
        case the browser window is reloaded, and thus the previous state
        must be recreated.
        """
        for command, args in self.history:
            self.supervisor.wwiSendText(f"{command},{args}")
