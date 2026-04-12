'''
This script will update the maps in the selected folder by randomly transforming
some of its victims into fakes.

Example:
> python update_maps_with_fakes.py ../game/worlds
'''
import random
import re
import sys
import os

def random_sample(coll, prob):
    return [x for x in coll if random.random() < prob]

def get_victim_intervals(wbt):
    pattern = r"(?sm)^\s*Victim\s*\{.+?\}"
    return [(m.start(0), m.end(0)) for m in re.finditer(pattern, wbt)]

def transform_victim(victim):
    result = victim
    result = re.sub(r"Victim", "Fake", result)
    result = re.sub(r"unharmed", "omega", result)
    result = re.sub(r"harmed", "phi", result)
    result = re.sub(r"stable", "psi", result)
    return result

def transform_victims(wbt, intervals):
    return [transform_victim(wbt[begin:end]) for (begin, end) in intervals]

def remove_intervals(wbt, intervals):
    result = ""
    offset = 0
    for (begin, end) in intervals:
        result += wbt[offset:begin]
        offset = end
    result += wbt[offset:]
    return result

def make_fake_group(fakes):
    result = "        DEF FAKES Group {\n            children [\n"
    result += "\n".join(fakes)
    result += "\n            ]\n        }"
    return result

def inject_fakes(wbt, fake_group):
    def coderepl(matchobj):
        return "\n\n" + fake_group + matchobj.group(0)    
    return re.sub(r"\s*DEF\s+HUMANGROUP\s+Group", coderepl, wbt)

def inject_fake_import(wbt):
    victim_pattern = r"(?m)^\s*EXTERNPROTO\s+\"\.\.\/protos\/Victim\.proto\""
    victim_proto = re.search(victim_pattern, wbt).group(0)
    fake_proto = re.sub(r"Victim\.proto", "Fake.proto", victim_proto)
    return re.sub(victim_pattern, fake_proto + "\n" + victim_proto, wbt)

def transform_world(wbt):
    intervals = get_victim_intervals(wbt)
    if len(intervals) == 0:
        raise Exception("No victims found!")

    intervals = random_sample(intervals, 0.5)
    fakes = transform_victims(wbt, intervals)
    wbt = remove_intervals(wbt, intervals)
    wbt = inject_fakes(wbt, make_fake_group(fakes))
    wbt = inject_fake_import(wbt)
    return wbt

def transform_world_file(world):
    try:
        with open(world, 'r') as file:
            wbt = file.read()

        if re.search(r"Fake\.proto", wbt):
            return "Map already has fakes!"
        
        wbt = transform_world(wbt)

        filename, _ = os.path.splitext(world)
        with open(filename + " - fakes.wbt", "w") as file:
            file.write(wbt)

        return None
    except Exception as ex:
        return str(ex)

if len(sys.argv) > 1:
    maps_folder = os.path.normpath(sys.argv[1])
    for filename in os.listdir(maps_folder):
        _, extension = os.path.splitext(filename)
        if extension == ".wbt":
            full_filename = os.path.join(maps_folder, filename)
            error = transform_world_file(full_filename)
            print(filename, "->", "SUCCESS" if error == None else "ERROR: " + error)
else:
    print("No map folder supplied. Bye!")    
