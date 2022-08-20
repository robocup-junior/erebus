class RWSender:
    def __init__(self):
        self.history = {}
    
    def updateHistory(self, command: str, args: str = ''):
        self.history[command] = args
    
    def send(self, supervisor, command: str, args: str = ''):
        supervisor.wwiSendText(command + ', ' + args)
        self.updateHistory(command, args)
    
    def sendAll(self, supervisor):
        for command in self.history:
            supervisor.wwiSendText(command + ', ' + self.history[command])