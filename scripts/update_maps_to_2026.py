'''
This script will update all the maps in the given folder to the 2026 version.
The update consists basically on replacing hazmats with cognitive targets.

Example:
> python update_maps_to_2026.py ../game/worlds
'''
import random
import re
import sys
import os

score_letter = {-2: "K", -1: "R", 0: "Y", 1: "G", 2: "B"}
hazard_score = {"F": 0, "P": 1, "C": 2, "O": 3}

def generate_code(expected_score):
    while True:
        code = []
        for i in range(5):
            code.append(random.randint(-2, 2))
        score = sum(code)    
        if expected_score == score:
            return "".join([score_letter[n] for n in code])

def coderepl(matchobj):
    return f"type \"{generate_code(hazard_score[matchobj.group(1)])}\"" 

def transform_world_file(world):
    with open(world, 'r') as file:
        wbt = file.read()
        wbt = re.sub(r"\bHazardMap\b", "CognitiveTarget", wbt)
        wbt = re.sub(r"\bHAZARDGROUP\b", "TARGETGROUP", wbt)
        wbt = re.sub(r"type\s+\"([FPCO])\"", coderepl, wbt)
    
    filename, _ = os.path.splitext(world)
    with open(filename + " - 2026.wbt", "w") as file:
        file.write(wbt)

if len(sys.argv) > 1:
    maps_folder = os.path.normpath(sys.argv[1])
    for filename in os.listdir(maps_folder):
        _, extension = os.path.splitext(filename)
        if extension == ".wbt":
            full_filename = os.path.join(maps_folder, filename)
            print(full_filename)
            transform_world_file(full_filename)
else:
    print("No map folder supplied. Bye!")    
