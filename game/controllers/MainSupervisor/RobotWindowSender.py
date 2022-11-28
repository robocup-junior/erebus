class RWSender:
    def __init__(self, supervisor):
        self.history = []
        self.supervisor = supervisor
    
    def updateHistory(self, command: str, args: str = ''):
        self.history.append([command,args])
    
    def send(self,command: str, args: str = ''):
        self.supervisor.wwiSendText(command + ',' + args)
        self.updateHistory(command, args)
    
    def sendAll(self):
        for command, args in self.history:
            self.supervisor.wwiSendText(command + ',' + args)