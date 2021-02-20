import math

def f(x):
    return math.sqrt(0.09 - (math.cos(x) * 0.3) ** 2)

resolution = 20
wallThickness = 0.01
wallHeight = 0.15
pi = 3.14

file = open('../game/worlds/curved.wbt', 'w')
header = open('WorldHeader.txt', 'r')
file.write(header.read())

x = 0
#coordinates
while (x <= pi / 2):
    file.write(str((math.cos(x) * 0.3 + math.cos(x) * wallThickness / 2)) + ' 0 ' + str(f(x) + math.sin(x) * wallThickness / 2) + ', ')
    file.write(str((math.cos(x) * 0.3 + math.cos(x) * wallThickness / 2)) + ' ' + str(wallHeight) + ' ' + str(f(x) + math.sin(x) * wallThickness / 2) + ', ')
    file.write(str((math.cos(x) * 0.3 - math.cos(x) * wallThickness / 2)) + ' 0 ' + str(f(x) - math.sin(x) * wallThickness / 2) + ', ')
    file.write(str((math.cos(x) * 0.3 - math.cos(x) * wallThickness / 2)) + ' ' + str(wallHeight) + ' ' + str(f(x) - math.sin(x) * wallThickness / 2) + ', ')
    x = x + pi / 2 / resolution

file.write('\n          ]\n        }\n        coordIndex [\n          ')
#coordinate indices

x = 0
while (x / 4 < resolution):
    file.write(str(x) + ', ' + str(x + 1) + ', ' + str(x + 4) + ', -1, ')
    file.write(str(x + 1) + ', ' + str(x + 5) + ', ' + str(x + 4) + ', -1, ')
    file.write(str(x + 2) + ', ' + str(x + 6) + ', ' + str(x + 3) + ', -1, ')
    file.write(str(x + 3) + ', ' + str(x + 6) + ', ' + str(x + 7) + ', -1, ')
    file.write(str(x + 1) + ', ' + str(x + 3) + ', ' + str(x + 7) + ', -1, ')
    file.write(str(x + 5) + ', ' + str(x + 1) + ', ' + str(x + 7) + ', -1, ')
    x = x + 4
x = resolution * 4
file.write('0, 2, 1, -1, 1, 2, 3, -1, ')
file.write(str(x) + ', ' + str(x + 1) + ', ' + str(x + 2) + ', -1, ' + str(x + 1) + ', ' + str(x + 3) + ', ' + str(x + 2) + ', -1')

file.write('\n        ]\n      }\n    }\n  ]\n  name "solid(1)"\n}')