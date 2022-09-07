import os

def getFilePath(file_path, file_path1):
    path = os.path.dirname(os.path.abspath(__file__))
    if path[-4:] == "game":
        return os.path.join(path, file_path)
    return os.path.join(path, file_path1)

def clamp(n, minn, maxn):
        '''Simple clamp function that limits a number between a specified range'''
        return max(min(maxn, n), minn)

def toLower(s):
    return s.lower()    