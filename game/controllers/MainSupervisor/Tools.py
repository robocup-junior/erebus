"""List of helper functions used throughout the Erebus codebase"""

import os

def get_file_path(
    game_relative_path: str,
    supervisor_relative_path: str
) -> str:
    """Gets the file path relative Erebus at runtime

    Args:
        game_relative_path (str): Path relative to the Erebus game directory
        supervisor_relative_path (str): Path relative to the MainSupervisor 
        script

    Returns:
        str: _description_
    """
    path: str = os.path.dirname(os.path.abspath(__file__))
    if path[-4:] == "game":
        return os.path.join(path, game_relative_path)
    return os.path.join(path, supervisor_relative_path)

def clamp(n, minn, maxn):
    """Simple clamp function that limits a number between a specified range
    """
    return max(min(maxn, n), minn)

def to_lower(s: str):
    return s.lower()    