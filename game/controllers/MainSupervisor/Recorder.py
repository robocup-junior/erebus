from Tools import *

class Recorder:

    COLOR_WHITE = 0xdff9fb
    COLOR_GREEN = 0x4cd137
    COLOR_RED = 0xe74c3c
    
    ID_SCORE = 0
    ID_CLOCK = 1
    ID_COUNT_DOWN = 4
    
    @staticmethod
    def resetCountDown(game):
        game.setLabel(Recorder.ID_COUNT_DOWN, "", 0.2, 0, 0.4, Recorder.COLOR_RED, 0)
    
    @staticmethod
    def startRecording(game):
        path = getFilePath("../recording.mp4", "../../../recording.mp4")
            
        game.movieStartRecording(
            path, width=1280, height=720, quality=70,
            codec=0, acceleration=1, caption=False,
        )
        
        game.setLabel(Recorder.ID_SCORE, f'Platform Version: {game.version}', 0, 0, 0.05, Recorder.COLOR_WHITE, 0)
        game.wait(0.5)
        game.setLabel(Recorder.ID_COUNT_DOWN, "3", 0.4, 0, 0.7, Recorder.COLOR_RED, 0)
        game.wait(1)
        game.setLabel(Recorder.ID_COUNT_DOWN, "2", 0.4, 0, 0.7, Recorder.COLOR_RED, 0)
        game.wait(1)
        game.setLabel(Recorder.ID_COUNT_DOWN, "1", 0.4, 0, 0.7, Recorder.COLOR_RED, 0)
        game.wait(1)
        game.setLabel(Recorder.ID_COUNT_DOWN, "START", 0.2, 0, 0.7, Recorder.COLOR_RED, 0)
        game.wait(1)
        game.setLabel(Recorder.ID_SCORE, "Score: " + str(0), 0.15, 0, 0.15, Recorder.COLOR_GREEN, 0)
        game.setLabel(Recorder.ID_CLOCK, "Clock: " + str(int(int(game.maxTime)/60)).zfill(2) + ":" + str(int(int(game.maxTime) % 60)).zfill(2), 0.4, 0, 0.15, Recorder.COLOR_GREEN, 0)
    
    @staticmethod
    def update(game):
        timeRemaining = game.maxTime - int(game.timeElapsed)
        game.setLabel(Recorder.ID_SCORE, "Score: " + str(round(game.robot0Obj.getScore(), 2)), 0.15, 0, 0.15, Recorder.COLOR_GREEN, 0)
        game.setLabel(Recorder.ID_CLOCK, "Clock: " + str(int(int(timeRemaining)/60)).zfill(2) + ":" + str(int(int(timeRemaining) % 60)).zfill(2), 0.4, 0, 0.15, Recorder.COLOR_GREEN, 0)
    
    @staticmethod
    def stopRecording(game):
        game.setLabel(Recorder.ID_SCORE, "Score: " + str(round(game.robot0Obj.getScore(), 2)), 0.15, 0.3, 0.3, Recorder.COLOR_RED, 0)
        game.setLabel(Recorder.ID_CLOCK, "Game time: " + str(int(int(game.timeElapsed)/60)).zfill(2) + ":" + str(int(int(game.timeElapsed) % 60)).zfill(2), 0.15, 0.45, 0.3, Recorder.COLOR_RED, 0)
        game.wait(5)
        game.movieStopRecording()
