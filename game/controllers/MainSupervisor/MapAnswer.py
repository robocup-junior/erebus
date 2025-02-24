from typing import Union
import numpy as np
import numpy.typing as npt
import json
import math

def pretty_print_map(map: Union[list, npt.NDArray]) -> None:
    """Print a formatted view of an Erebus map matrix

    Args:
        map (Union[list, npt.NDArray]): Erebus map matrix to print
    """
    for m in map:
        for mm in m:
            # Default (for victims)
            color = Color.CYAN
            bkg = Color.BG_WHITE
            if mm == '0': #Normal
                color = Color.WHITE
                bkg = Color.BG_DEFAULT
            elif mm == '1': #Walls
                bkg = Color.BG_WHITE
                color = Color.BLACK
            elif mm == '2': #Holes
                bkg = Color.BG_WHITE
                color = Color.BOLD
            elif mm == '3': #Swamps
                color = Color.YELLOW
                bkg = Color.BG_DEFAULT
            elif mm == '4': #Checkpoints
                color = Color.UNDERLINE
                bkg = Color.BG_DEFAULT
            elif mm == '5': #Stating tile
                color = Color.GREEN
                bkg = Color.BG_DEFAULT
            elif mm == 'b': #1 to 2
                color = Color.BLUE
                bkg = Color.BG_DEFAULT
            elif mm == 'y': #1 to 3
                color = Color.YELLOW
                bkg = Color.BG_DEFAULT
            elif mm == 'g': #1 to 4
                color = Color.GREEN
                bkg = Color.BG_DEFAULT
            elif mm == 'p': #2 to 3
                color = Color.MAGENTA
                bkg = Color.BG_DEFAULT
            elif mm == 'o': #2 to 4
                color = Color.RED
                bkg = Color.BG_YELLOW
            elif mm == 'r': #3 to 4
                color = Color.RED
                bkg = Color.BG_DEFAULT
            else: #Victims
                color = Color.CYAN
                bkg = Color.BG_WHITE
            print(f'{bkg}{color}{mm}{Color.RESET}', end='')
        print('')

class MapAnswer:
    @classmethod
    def from_supervisor(cls, supervisor):
        #Count the number of tiles
        numberTiles = supervisor.getFromDef('WALLTILES').getField("children").getCount()
        #Retrieve the node containing the tiles
        tileNodes = supervisor.getFromDef('WALLTILES').getField("children")
        
        # TODO(Richo): I don't understand this. If the last node is not a TILE or START_TILE we just ignore it? When could that happen?
        if tileNodes.getMFNode(numberTiles - 1).getDef() != "TILE" and tileNodes.getMFNode(numberTiles - 1).getDef() != "START_TILE":
            numberTiles -= 1
        
        tiles = []
        for i in range(numberTiles):
            tiles.append(Tile.from_node(tileNodes.getMFNode(i)))
        
        #Retrieve the node containing the victims
        victimNodes = supervisor.getFromDef('HUMANGROUP').getField("children")
        victims = []
        for i in range(victimNodes.getCount()):
            node = victimNodes.getMFNode(i)
            victims.append(Sign.from_node(node))

        #Retrieve the node containing the victims
        hazardNodes = supervisor.getFromDef('HAZARDGROUP').getField("children")
        hazards = []
        for i in range(hazardNodes.getCount()):
            node = hazardNodes.getMFNode(i)
            hazards.append(Sign.from_node(node))

        return cls(tiles, victims, hazards)
    
    @classmethod
    def from_dict(cls, dict):
        tiles = []
        for t in dict["tiles"]:
            tiles.append(Tile.from_dict(t))

        victims = []
        for v in dict["victims"]:
            victims.append(Sign.from_dict(v))

        hazards = []
        for h in dict["hazards"]:
            hazards.append(Sign.from_dict(h))
        return cls(tiles, victims, hazards)
    
    def __init__(self, tiles, victims, hazards):
        self.tiles = tiles
        self.victims = victims
        self.hazards = hazards
        
        xPos = [t.xPos for t in tiles]
        zPos = [t.zPos for t in tiles]
        x_size = max(xPos) - min(xPos) + 1
        z_size = max(zPos) - min(zPos) + 1
        self.answerMatrix = [[0] * (x_size * 4 + 1) for _ in range(z_size * 4 + 1)]

        self.xStart = -(tiles[0].width * (0.3 * tiles[0].xScale) / 2.0) -0.06
        self.zStart = -(tiles[0].height * (0.3 * tiles[0].zScale) / 2.0) -0.06
    
    def to_dict(self):
        tiles = []
        for tile in self.tiles:
            tiles.append(tile.to_dict())
    
        victims = []
        for victim in self.victims:
            victims.append(victim.to_dict())
        
        hazards = []
        for hazard in self.hazards:
            hazards.append(hazard.to_dict())
        
        return {
            "tiles": tiles,
            "victims": victims,
            "hazards": hazards
        }
    
    def writeJSON(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

    def setAnswer(self,z,x,k):
        if self.answerMatrix[z][x] == '*':
            return
        self.answerMatrix[z][x] = k

    def generateAnswer(self, debug = False):
        # try:
            for tile in self.tiles:
                x = 4*tile.xPos
                z = 4*tile.zPos
                room = tile.room

                # Room 4
                # self.answerMatrix[z+a][x+b] = '*'
                if room == 4:
                    for a in range(5):
                        for b in range(5):
                            self.answerMatrix[z+a][x+b] = '*'
                    continue

                # Wall
                if tile.topWall > 0:
                    self.setAnswer(z, x, 1)
                    self.setAnswer(z, x+1, 1)
                    self.setAnswer(z, x+2, 1)
                    self.setAnswer(z, x+3, 1)
                    self.setAnswer(z, x+4, 1)
                if tile.bottomWall > 0:
                    self.setAnswer(z+4, x, 1)
                    self.setAnswer(z+4, x+1, 1)
                    self.setAnswer(z+4, x+2, 1)
                    self.setAnswer(z+4, x+3, 1)
                    self.setAnswer(z+4, x+4, 1)
                if tile.rightWall > 0:
                    self.setAnswer(z, x+4, 1)
                    self.setAnswer(z+1, x+4, 1)
                    self.setAnswer(z+2, x+4, 1)
                    self.setAnswer(z+3, x+4, 1)
                    self.setAnswer(z+4, x+4, 1)
                if tile.leftWall > 0:
                    self.setAnswer(z, x, 1)
                    self.setAnswer(z+1, x, 1)
                    self.setAnswer(z+2, x, 1)
                    self.setAnswer(z+3, x, 1)
                    self.setAnswer(z+4, x, 1)
                
                ## Half wall
                if tile.type == "halfTile":
                    if tile.tile1Walls[0] > 0:
                        self.setAnswer(z, x, 1)
                        self.setAnswer(z, x+1, 1)
                        self.setAnswer(z, x+2, 1)
                    if tile.tile1Walls[1] > 0:
                        self.setAnswer(z, x+2, 1)
                        self.setAnswer(z+1, x+2, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if tile.tile1Walls[2] > 0:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+2, x+1, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if tile.tile1Walls[3] > 0:
                        self.setAnswer(z, x, 1)
                        self.setAnswer(z+1, x, 1)
                        self.setAnswer(z+2, x, 1)
                    if tile.tile2Walls[0] > 0:
                        self.setAnswer(z, x+2, 1)
                        self.setAnswer(z, x+3, 1)
                        self.setAnswer(z, x+4, 1)
                    if tile.tile2Walls[1] > 0:
                        self.setAnswer(z, x+4, 1)
                        self.setAnswer(z+1, x+4, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if tile.tile2Walls[2] > 0:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+2, x+3, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if tile.tile2Walls[3] > 0:
                        self.setAnswer(z, x+2, 1)
                        self.setAnswer(z+1, x+2, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if tile.tile3Walls[0] > 0:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+2, x+1, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if tile.tile3Walls[1] > 0:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+3, x+2, 1)
                        self.setAnswer(z+4, x+2, 1)
                    if tile.tile3Walls[2] > 0:
                        self.setAnswer(z+4, x, 1)
                        self.setAnswer(z+4, x+1, 1)
                        self.setAnswer(z+4, x+2, 1)
                    if tile.tile3Walls[3] > 0:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+3, x, 1)
                        self.setAnswer(z+4, x, 1)
                    if tile.tile4Walls[0] > 0:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+2, x+3, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if tile.tile4Walls[1] > 0:
                        self.setAnswer(z+2, x+4, 1)
                        self.setAnswer(z+3, x+4, 1)
                        self.setAnswer(z+4, x+4, 1)
                    if tile.tile4Walls[2] > 0:
                        self.setAnswer(z+4, x+2, 1)
                        self.setAnswer(z+4, x+3, 1)
                        self.setAnswer(z+4, x+4, 1)
                    if tile.tile4Walls[3] > 0:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+3, x+2, 1)
                        self.setAnswer(z+4, x+2, 1)
            
                
                    # Curved walls
                    # Left top
                    lt = tile.curve[0]
                    if lt == 1:
                        self.setAnswer(z, x, 1)
                        self.setAnswer(z, x+1, 1)
                        self.setAnswer(z, x+2, 0)
                        self.setAnswer(z+1, x+2, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if lt == 2:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+2, x+1, 1)
                        self.setAnswer(z+2, x+2, 0)
                        self.setAnswer(z+1, x+2, 1)
                        self.setAnswer(z, x+2, 1)
                    if lt == 3:
                        self.setAnswer(z, x, 1)
                        self.setAnswer(z+1, x, 1)
                        self.setAnswer(z+2, x, 0)
                        self.setAnswer(z+2, x+1, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if lt == 4:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+1, x, 1)
                        self.setAnswer(z, x, 0)
                        self.setAnswer(z, x+1, 1)
                        self.setAnswer(z, x+2, 1)
                    
                    # Right top
                    rt = tile.curve[1]
                    if rt == 1:
                        self.setAnswer(z, x+2, 1)
                        self.setAnswer(z, x+3, 1)
                        self.setAnswer(z, x+4, 0)
                        self.setAnswer(z+1, x+4, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if rt == 2:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+2, x+3, 1)
                        self.setAnswer(z+2, x+4, 0)
                        self.setAnswer(z+1, x+4, 1)
                        self.setAnswer(z, x+4, 1)
                    if rt == 3:
                        self.setAnswer(z, x+2, 1)
                        self.setAnswer(z+1, x+2, 1)
                        self.setAnswer(z+2, x+2, 0)
                        self.setAnswer(z+2, x+3, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if rt == 4:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+1, x+2, 1)
                        self.setAnswer(z, x+2, 0)
                        self.setAnswer(z, x+3, 1)
                        self.setAnswer(z, x+4, 1)
                    
                    # Left bottom
                    lb = tile.curve[2]
                    if lb == 1:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+2, x+1, 1)
                        self.setAnswer(z+2, x+2, 0)
                        self.setAnswer(z+3, x+2, 1)
                        self.setAnswer(z+4, x+2, 1)
                    if lb == 2:
                        self.setAnswer(z+4, x, 1)
                        self.setAnswer(z+4, x+1, 1)
                        self.setAnswer(z+4, x+2, 0)
                        self.setAnswer(z+3, x+2, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if lb == 3:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+3, x, 1)
                        self.setAnswer(z+4, x, 0)
                        self.setAnswer(z+4, x+1, 1)
                        self.setAnswer(z+4, x+2, 1)
                    if lb == 4:
                        self.setAnswer(z+4, x, 1)
                        self.setAnswer(z+3, x, 1)
                        self.setAnswer(z+2, x, 0)
                        self.setAnswer(z+2, x+1, 1)
                        self.setAnswer(z+2, x+2, 1)
                    
                    # Right bottom
                    rb = tile.curve[3]
                    if rb == 1:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+2, x+3, 1)
                        self.setAnswer(z+2, x+4, 0)
                        self.setAnswer(z+3, x+4, 1)
                        self.setAnswer(z+4, x+4, 1)
                    if rb == 2:
                        self.setAnswer(z+4, x+2, 1)
                        self.setAnswer(z+4, x+3, 1)
                        self.setAnswer(z+4, x+4, 0)
                        self.setAnswer(z+3, x+4, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if rb == 3:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+3, x+2, 1)
                        self.setAnswer(z+4, x+2, 0)
                        self.setAnswer(z+4, x+3, 1)
                        self.setAnswer(z+4, x+4, 1)
                    if rb == 4:
                        self.setAnswer(z+4, x+2, 1)
                        self.setAnswer(z+3, x+2, 1)
                        self.setAnswer(z+2, x+2, 0)
                        self.setAnswer(z+2, x+3, 1)
                        self.setAnswer(z+2, x+4, 1)

                if tile.trap:
                    self.answerMatrix[z+1][x+1] = 2
                    self.answerMatrix[z+1][x+3] = 2
                    self.answerMatrix[z+3][x+1] = 2
                    self.answerMatrix[z+3][x+3] = 2
                if tile.swamp:
                    self.answerMatrix[z+1][x+1] = 3
                    self.answerMatrix[z+1][x+3] = 3
                    self.answerMatrix[z+3][x+1] = 3
                    self.answerMatrix[z+3][x+3] = 3
                if tile.checkpoint:
                    self.answerMatrix[z+1][x+1] = 4
                    self.answerMatrix[z+1][x+3] = 4
                    self.answerMatrix[z+3][x+1] = 4
                    self.answerMatrix[z+3][x+3] = 4
                if tile.start:
                    self.answerMatrix[z+1][x+1] = 5
                    self.answerMatrix[z+1][x+3] = 5
                    self.answerMatrix[z+3][x+1] = 5
                    self.answerMatrix[z+3][x+3] = 5
                
                if tile.tileColor == [0.0, 0.8, 0.0]: # Green
                    # 1 to 4
                    self.answerMatrix[z+1][x+1] = 'g'
                    self.answerMatrix[z+1][x+3] = 'g'
                    self.answerMatrix[z+3][x+1] = 'g'
                    self.answerMatrix[z+3][x+3] = 'g'
                elif tile.tileColor == [0.1, 0.1, 0.9]: # Blue
                    # 1 to 2
                    self.answerMatrix[z+1][x+1] = 'b'
                    self.answerMatrix[z+1][x+3] = 'b'
                    self.answerMatrix[z+3][x+1] = 'b'
                    self.answerMatrix[z+3][x+3] = 'b'
                elif tile.tileColor == [0.3, 0.1, 0.6]: # Purple
                    # 2 to 3
                    self.answerMatrix[z+1][x+1] = 'p'
                    self.answerMatrix[z+1][x+3] = 'p'
                    self.answerMatrix[z+3][x+1] = 'p'
                    self.answerMatrix[z+3][x+3] = 'p'
                elif tile.tileColor == [0.9, 0.1, 0.1]: # Red
                    # 3 to 4
                    self.answerMatrix[z+1][x+1] = 'r'
                    self.answerMatrix[z+1][x+3] = 'r'
                    self.answerMatrix[z+3][x+1] = 'r'
                    self.answerMatrix[z+3][x+3] = 'r'
                elif tile.tileColor == [0.9, 0.6, 0.1]: # Orange
                    # 2 to 4
                    self.answerMatrix[z+1][x+1] = 'o'
                    self.answerMatrix[z+1][x+3] = 'o'
                    self.answerMatrix[z+3][x+1] = 'o'
                    self.answerMatrix[z+3][x+3] = 'o'
                elif tile.tileColor == [0.9, 0.9, 0.1]: # Yellow
                    # 1 to 3
                    self.answerMatrix[z+1][x+1] = 'y'
                    self.answerMatrix[z+1][x+3] = 'y'
                    self.answerMatrix[z+3][x+1] = 'y'
                    self.answerMatrix[z+3][x+3] = 'y'
            
            # Victims & Hazards
            signs = self.victims + self.hazards

            # Sort signs top to bottom, left to right
            signs.sort(key=lambda s: (s.translation[2], s.translation[0]))

            for victim in signs:                               
                victimType = victim.type
                if victimType == "harmed":
                    victimType = "H"
                elif victimType == "unharmed":
                    victimType = "U"
                elif victimType == "stable":
                    victimType = "S"

                # NOTE(Richo): First we take the victim's translation and transform it relative
                # to the map's start coordinate (which should be the top left corner). Then, we
                # estimate a pair of col/row coordinates based on the victim's position. These
                # coordinates will later have to be adjusted depending on the victim's rotation.
                translation = victim.translation
                t_x = translation[0] - self.xStart
                col_temp = int(t_x / 0.024) - int(t_x / 0.12)
                t_z = translation[2] - self.zStart
                row_temp = int(t_z / 0.024) - int(t_z / 0.12)

                yaw = round(victim.get_rotation_yaw(), 2)
                if math.isclose(abs(yaw), 1.57):
                    # Vertical
                    # NOTE(Richo): col_temp should be ok, we need to calculate row_temp. To do it, we
                    # calculate the distance between the victim and the corresponding tile's center
                    # (in the Z coordinate). Depending on this distance value, we either put the victim
                    # on the center of the tile, 1 cell up, or 1 cell down.
                    tile_idx = int(t_z / 0.12)
                    tile_center = tile_idx * 0.12 + 0.06
                    dist_center = t_z - tile_center
                    row_temp = tile_idx * 4 + 2 # Assume center first
                    if dist_center < -0.02:
                        # Move it UP
                        row_temp -= 1
                    elif dist_center > 0.02:
                        # Move it DOWN
                        row_temp += 1
                elif math.isclose(abs(yaw), 0) or math.isclose(abs(yaw), 3.14):
                    # Horizontal                    
                    # NOTE(Richo): row_temp should be ok, we need to calculate col_temp. To do it, we
                    # calculate the distance between the victim and the corresponding tile's center
                    # (in the X coordinate). Depending on this distance value, we either put the victim
                    # on the center of the tile, 1 cell to the left, or 1 cell to the right.
                    tile_idx = int(t_x / 0.12)
                    tile_center = tile_idx * 0.12 + 0.06
                    dist_center = t_x - tile_center
                    col_temp = tile_idx * 4 + 2 # Assume center first
                    if dist_center < -0.02:
                        # Move it to the LEFT
                        col_temp -= 1
                    elif dist_center > 0.02:
                        # Move it to the RIGHT
                        col_temp += 1
                else:
                    # Curved
                    # NOTE(Richo): Curved victims need special case for both coordinates.
                    # We start by computing the tile center coordinates (col and row), then
                    # we adjust each one depending on the victim's position.

                    # In the case of the column, we have to either add or subtract 1 depending
                    # on whether the victim position is before or after the tile's center.
                    col_temp = int(t_x / 0.12) * 4 + 2
                    tile_center_x = int(t_x / 0.12) * 0.12 + 0.06                    
                    if t_x < tile_center_x:
                        col_temp -= 1
                    elif t_x > tile_center_x:
                        col_temp += 1

                    # In the case of the row, we add or subtract 2 but only if the distance
                    # to the center is larger than a certain threshold.
                    row_temp = int(t_z / 0.12) * 4 + 2
                    tile_center_z = int(t_z / 0.12) * 0.12 + 0.06
                    dist_center = t_z - tile_center_z
                    if dist_center < -0.03:
                        row_temp -= 2
                    elif dist_center > 0.03:
                        row_temp += 2


                # Concatenate if victims on either side of the wall
                if self.answerMatrix[row_temp][col_temp] != '*':
                    if type(self.answerMatrix[row_temp][col_temp]) == str:
                        self.answerMatrix[row_temp][col_temp] += victimType
                    else:
                        self.answerMatrix[row_temp][col_temp] = victimType
                    
            
            for i in range(len(self.answerMatrix)):
                self.answerMatrix[i] = list(map(str, self.answerMatrix[i]))
            
            # DO NOT PRINT MAP PROGRAMMATICALLY
            if debug:
                pretty_print_map(self.answerMatrix)

            return self.answerMatrix
            
        # except Exception as e:
        #     Console.log_err("Generating map answer error.")
        #     print(e)

class Color:
	BLACK          = '\033[30m'
	RED            = '\033[31m'
	GREEN          = '\033[32m'
	YELLOW         = '\033[33m'
	BLUE           = '\033[34m'
	MAGENTA        = '\033[35m'
	CYAN           = '\033[36m'
	WHITE          = '\033[37m'
	COLOR_DEFAULT  = '\033[39m'
	BOLD           = '\033[1m'
	UNDERLINE      = '\033[4m'
	INVISIBLE      = '\033[08m'
	REVERCE        = '\033[07m'
	BG_BLACK       = '\033[40m'
	BG_RED         = '\033[41m'
	BG_GREEN       = '\033[42m'
	BG_YELLOW      = '\033[43m'
	BG_BLUE        = '\033[44m'
	BG_MAGENTA     = '\033[45m'
	BG_CYAN        = '\033[46m'
	BG_WHITE       = '\033[47m'
	BG_DEFAULT     = '\033[49m'
	RESET          = '\033[0m'

class Tile:
    @classmethod
    def from_node(cls, tile):
        xPos = tile.getField("xPos").getSFInt32()
        zPos = tile.getField("zPos").getSFInt32()
        room = tile.getField("room").getSFInt32()
        width = tile.getField("width").getSFFloat()
        height = tile.getField("height").getSFFloat()
        xScale = tile.getField("xScale").getSFFloat()
        zScale = tile.getField("zScale").getSFFloat()
        topWall = tile.getField("topWall").getSFInt32()
        bottomWall = tile.getField("bottomWall").getSFInt32()
        leftWall = tile.getField("leftWall").getSFInt32()
        rightWall = tile.getField("rightWall").getSFInt32()
        trap = tile.getField("trap").getSFBool()
        swamp = tile.getField("swamp").getSFBool()
        checkpoint = tile.getField("checkpoint").getSFBool()
        start = tile.getField("start").getSFBool()
        
        colour = tile.getField("tileColor").getSFColor()
        tileColor = [round(colour[0], 1), round(colour[1], 1), round(colour[2], 1)]
        
        # TODO(Richo): Maybe subclasses are better?
        type = tile.getTypeName()
        tile1Walls = None
        tile2Walls = None
        tile3Walls = None
        tile4Walls = None
        curve = None
        if tile.getTypeName() == "halfTile":
            tile1Walls = [
                tile.getField("tile1Walls").getMFInt32(0),
                tile.getField("tile1Walls").getMFInt32(1),
                tile.getField("tile1Walls").getMFInt32(2),
                tile.getField("tile1Walls").getMFInt32(3)
            ]
            tile2Walls = [
                tile.getField("tile2Walls").getMFInt32(0),
                tile.getField("tile2Walls").getMFInt32(1),
                tile.getField("tile2Walls").getMFInt32(2),
                tile.getField("tile2Walls").getMFInt32(3)
            ]
            tile3Walls = [
                tile.getField("tile3Walls").getMFInt32(0),
                tile.getField("tile3Walls").getMFInt32(1),
                tile.getField("tile3Walls").getMFInt32(2),
                tile.getField("tile3Walls").getMFInt32(3)
            ]
            tile4Walls = [
                tile.getField("tile4Walls").getMFInt32(0),
                tile.getField("tile4Walls").getMFInt32(1),
                tile.getField("tile4Walls").getMFInt32(2),
                tile.getField("tile4Walls").getMFInt32(3)
            ]
            curve = [
                tile.getField("curve").getMFInt32(0),
                tile.getField("curve").getMFInt32(1),
                tile.getField("curve").getMFInt32(2),
                tile.getField("curve").getMFInt32(3)
            ]

        return cls(type, xPos, zPos, room, width, height, xScale, zScale, \
                   topWall, bottomWall, leftWall, rightWall, trap, swamp, checkpoint, start, \
                   tileColor, tile1Walls, tile2Walls, tile3Walls, tile4Walls, curve)
    
    @classmethod
    def from_dict(cls, dict):
        xPos = dict["xPos"]
        zPos = dict["zPos"]
        room = dict["room"]
        width = dict["width"]
        height = dict["height"]
        xScale = dict["xScale"]
        zScale = dict["zScale"]
        topWall = dict["topWall"]
        bottomWall = dict["bottomWall"]
        leftWall = dict["leftWall"]
        rightWall = dict["rightWall"]
        trap = dict["trap"]
        swamp = dict["swamp"]
        checkpoint = dict["checkpoint"]
        start = dict["start"]
        tileColor = dict["tileColor"]
        type = dict["type"]
        tile1Walls = dict.get("tile1Walls")
        tile2Walls = dict.get("tile2Walls")
        tile3Walls = dict.get("tile3Walls")
        tile4Walls = dict.get("tile4Walls")
        curve = dict.get("curve")

        return cls(type, xPos, zPos, room, width, height, xScale, zScale, \
                   topWall, bottomWall, leftWall, rightWall, trap, swamp, checkpoint, start, \
                   tileColor, tile1Walls, tile2Walls, tile3Walls, tile4Walls, curve)

    def __init__(self, type, xPos, zPos, room, width, height, xScale, zScale, \
                topWall, bottomWall, leftWall, rightWall, trap, swamp, checkpoint, start, \
                tileColor, tile1Walls, tile2Walls, tile3Walls, tile4Walls, curve):
        self.type = type
        self.xPos = xPos
        self.zPos = zPos
        self.room = room
        self.width = width
        self.height = height
        self.xScale = xScale
        self.zScale = zScale
        self.topWall = topWall
        self.bottomWall = bottomWall
        self.leftWall = leftWall
        self.rightWall = rightWall
        self.trap = trap
        self.swamp = swamp
        self.checkpoint = checkpoint
        self.start = start
        self.tileColor = tileColor
        self.tile1Walls = tile1Walls
        self.tile2Walls = tile2Walls
        self.tile3Walls = tile3Walls
        self.tile4Walls = tile4Walls
        self.curve = curve
        
    def to_dict(self):
        result = {
            "xPos": self.xPos,
            "zPos": self.zPos,
            "room": self.room,
            "width": self.width,
            "height": self.height,
            "xScale": self.xScale,
            "zScale": self.zScale,
            "topWall": self.topWall,
            "bottomWall": self.bottomWall,
            "leftWall": self.leftWall,
            "rightWall": self.rightWall,
            "trap": self.trap,
            "swamp": self.swamp,
            "checkpoint": self.checkpoint,
            "start": self.start,
            "tileColor": self.tileColor,
            "type": self.type
        }

        if self.type == "halfTile":
            result["tile1Walls"] = self.tile1Walls
            result["tile2Walls"] = self.tile2Walls
            result["tile3Walls"] = self.tile3Walls
            result["tile4Walls"] = self.tile4Walls
            result["curve"] = self.curve

        return result

# NOTE(Richo): Code taken from 
# https://www.euclideanspace.com/maths/geometry/rotations/conversions/angleToQuaternion/index.htm
def angle_axis_to_quaternion(x, y, z, a):
    w = math.cos(a/2)
    x = x*math.sin(a/2)
    y = y*math.sin(a/2)
    z = z*math.sin(a/2)
    return [w, x, y, z]

# NOTE(Richo): Code taken from
# https://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToEuler/
def quaternion_to_euler(w, x, y, z):
    sqw = w*w
    sqx = x*x
    sqy = y*y
    sqz = z*z
    unit = sqx + sqy + sqz + sqw # if normalised is one, otherwise is correction factor
    test = x*y + z*w
    # if test > 0.499*unit: # singularity at north pole
    #     print("NORTH <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    #     heading = 2 * math.atan2(x,w)
    #     attitude = math.pi/2
    #     bank = 0
    #     return heading, attitude, bank

    # if test < -0.499*unit: # singularity at south pole
    #     print("SOUTH <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    #     heading = -2 * math.atan2(x,w)
    #     attitude = -math.pi/2
    #     bank = 0
    #     return heading, attitude, bank

    heading = math.atan2(2*y*w-2*x*z , sqx - sqy - sqz + sqw)
    attitude = math.asin(2*test/unit)
    bank = math.atan2(2*x*w-2*y*z , -sqx + sqy - sqz + sqw)
    return heading, attitude, bank

class Sign:
    @classmethod
    def from_node(cls, node):
        type = node.getField("type").getSFString()

        t = node.getField("translation").getSFVec3f()
        translation = [t[0], t[1], t[2]]

        r = node.getField("rotation").getSFRotation()
        rotation = [r[0], r[1], r[2], r[3]]
        
        return cls(type, translation, rotation)
    
    @classmethod
    def from_dict(cls, dict):
        return cls(dict["type"], dict["translation"], dict["rotation"])

    def __init__(self, type, translation, rotation):
        self.type = type
        self.translation = translation
        self.rotation = rotation
    
    def get_rotation_quaternion(self):
        x = self.rotation[0]
        y = self.rotation[1]
        z = self.rotation[2]
        a = self.rotation[3]
        return angle_axis_to_quaternion(x, y, z, a)
    
    def get_rotation_euler(self):
        w, x, y, z = self.get_rotation_quaternion()
        return quaternion_to_euler(w, x, y, z)
    
    def get_rotation_yaw(self):
        yaw, _, _ = self.get_rotation_euler()
        return yaw
    
    def to_dict(self):
        return {
            "type": self.type,
            "translation": self.translation,
            "rotation": self.rotation
        }