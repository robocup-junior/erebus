import AutoInstall
AutoInstall._import("np", "numpy")

class MapAnswer:
    def __init__(self, supervisor):
        self.supervisor = supervisor
        #Count the number of tiles
        self.numberTiles = supervisor.getFromDef('WALLTILES').getField("children").getCount()
        #Retrieve the node containing the tiles
        self.tileNodes = supervisor.getFromDef('WALLTILES').getField("children")
        
        self.xPos = [self.tileNodes.getMFNode(i).getField("xPos").getSFInt32() for i in range(self.numberTiles)]
        self.zPos = [self.tileNodes.getMFNode(i).getField("zPos").getSFInt32() for i in range(self.numberTiles)]

        self.x_size = max(self.xPos) - min(self.xPos) + 1
        self.z_size = max(self.zPos) - min(self.zPos) + 1
        self.answerMatrix = [[0] * (self.x_size * 4 + 1) for i in range(self.z_size * 4 + 1)]

        self.xStart = -(self.tileNodes.getMFNode(0).getField("width").getSFFloat() * (0.3 * self.tileNodes.getMFNode(0).getField("xScale").getSFFloat()) / 2.0) -0.06
        self.zStart = -(self.tileNodes.getMFNode(0).getField("height").getSFFloat() * (0.3 * self.tileNodes.getMFNode(0).getField("zScale").getSFFloat()) / 2.0) -0.06
    
    def setAnswer(self,z,x,k):
        self.answerMatrix[z][x] = max(self.answerMatrix[z][x], k)

    def generateAnswer(self):
        try:
            for i in range(self.numberTiles):
                tile = self.tileNodes.getMFNode(i)
                x = 4*tile.getField("xPos").getSFInt32()
                z = 4*tile.getField("zPos").getSFInt32()

                # Wall
                if tile.getField("topWall").getSFInt32() > 0:
                    self.setAnswer(z, x, 1)
                    self.setAnswer(z, x+1, 1)
                    self.setAnswer(z, x+2, 1)
                    self.setAnswer(z, x+3, 1)
                    self.setAnswer(z, x+4, 1)
                if tile.getField("bottomWall").getSFInt32() > 0:
                    self.setAnswer(z+4, x, 1)
                    self.setAnswer(z+4, x+1, 1)
                    self.setAnswer(z+4, x+2, 1)
                    self.setAnswer(z+4, x+3, 1)
                    self.setAnswer(z+4, x+4, 1)
                if tile.getField("rightWall").getSFInt32() > 0:
                    self.setAnswer(z, x+4, 1)
                    self.setAnswer(z+1, x+4, 1)
                    self.setAnswer(z+2, x+4, 1)
                    self.setAnswer(z+3, x+4, 1)
                    self.setAnswer(z+4, x+4, 1)
                if tile.getField("leftWall").getSFInt32() > 0:
                    self.setAnswer(z, x, 1)
                    self.setAnswer(z+1, x, 1)
                    self.setAnswer(z+2, x, 1)
                    self.setAnswer(z+3, x, 1)
                    self.setAnswer(z+4, x, 1)
                
                room = tile.getField("room").getSFInt32()
                ## Half wall
                if room >= 2:
                    if tile.getField("tile1Walls").getMFInt32(0) > 0:
                        self.setAnswer(z, x, 1)
                        self.setAnswer(z, x+1, 1)
                        self.setAnswer(z, x+2, 1)
                    if tile.getField("tile1Walls").getMFInt32(1) > 0:
                        self.setAnswer(z, x+2, 1)
                        self.setAnswer(z+1, x+2, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if tile.getField("tile1Walls").getMFInt32(2) > 0:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+2, x+1, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if tile.getField("tile1Walls").getMFInt32(3) > 0:
                        self.setAnswer(z, x, 1)
                        self.setAnswer(z+1, x, 1)
                        self.setAnswer(z+2, x, 1)
                    if tile.getField("tile2Walls").getMFInt32(0) > 0:
                        self.setAnswer(z, x+2, 1)
                        self.setAnswer(z, x+3, 1)
                        self.setAnswer(z, x+4, 1)
                    if tile.getField("tile2Walls").getMFInt32(1) > 0:
                        self.setAnswer(z, x+4, 1)
                        self.setAnswer(z+1, x+4, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if tile.getField("tile2Walls").getMFInt32(2) > 0:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+2, x+3, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if tile.getField("tile2Walls").getMFInt32(3) > 0:
                        self.setAnswer(z, x+2, 1)
                        self.setAnswer(z+1, x+2, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if tile.getField("tile3Walls").getMFInt32(0) > 0:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+2, x+1, 1)
                        self.setAnswer(z+2, x+2, 1)
                    if tile.getField("tile3Walls").getMFInt32(1) > 0:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+3, x+2, 1)
                        self.setAnswer(z+4, x+2, 1)
                    if tile.getField("tile3Walls").getMFInt32(2) > 0:
                        self.setAnswer(z+4, x, 1)
                        self.setAnswer(z+4, x+1, 1)
                        self.setAnswer(z+4, x+2, 1)
                    if tile.getField("tile3Walls").getMFInt32(3) > 0:
                        self.setAnswer(z+2, x, 1)
                        self.setAnswer(z+3, x, 1)
                        self.setAnswer(z+4, x, 1)
                    if tile.getField("tile4Walls").getMFInt32(0) > 0:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+2, x+3, 1)
                        self.setAnswer(z+2, x+4, 1)
                    if tile.getField("tile4Walls").getMFInt32(1) > 0:
                        self.setAnswer(z+2, x+4, 1)
                        self.setAnswer(z+3, x+4, 1)
                        self.setAnswer(z+4, x+4, 1)
                    if tile.getField("tile4Walls").getMFInt32(2) > 0:
                        self.setAnswer(z+4, x+2, 1)
                        self.setAnswer(z+4, x+3, 1)
                        self.setAnswer(z+4, x+4, 1)
                    if tile.getField("tile4Walls").getMFInt32(3) > 0:
                        self.setAnswer(z+2, x+2, 1)
                        self.setAnswer(z+3, x+2, 1)
                        self.setAnswer(z+4, x+2, 1)
                
                # Curved walls
                if room >= 3:
                    # Left top
                    lt = tile.getField("curve").getMFInt32(0)
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
                    rt = tile.getField("curve").getMFInt32(1)
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
                    lb = tile.getField("curve").getMFInt32(2)
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
                    rb = tile.getField("curve").getMFInt32(3)
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
                
                if tile.getField("trap").getSFBool():
                    self.answerMatrix[z+1][x+1] = 2
                    self.answerMatrix[z+1][x+3] = 2
                    self.answerMatrix[z+3][x+1] = 2
                    self.answerMatrix[z+3][x+3] = 2
                if tile.getField("swamp").getSFBool():
                    self.answerMatrix[z+1][x+1] = 3
                    self.answerMatrix[z+1][x+3] = 3
                    self.answerMatrix[z+3][x+1] = 3
                    self.answerMatrix[z+3][x+3] = 3
                if tile.getField("checkpoint").getSFBool():
                    self.answerMatrix[z+1][x+1] = 4
                    self.answerMatrix[z+1][x+3] = 4
                    self.answerMatrix[z+3][x+1] = 4
                    self.answerMatrix[z+3][x+3] = 4
                if tile.getField("start").getSFBool():
                    self.answerMatrix[z+1][x+1] = 5
                    self.answerMatrix[z+1][x+3] = 5
                    self.answerMatrix[z+3][x+1] = 5
                    self.answerMatrix[z+3][x+3] = 5
                
                colour = tile.getField("tileColor").getSFColor()
                colour = [round(colour[0], 1), round(colour[1], 1), round(colour[2], 1)]
                if colour == [0.3, 0.1, 0.6]:
                    # 1 to 3
                    self.answerMatrix[z+1][x+1] = 7
                    self.answerMatrix[z+1][x+3] = 7
                    self.answerMatrix[z+3][x+1] = 7
                    self.answerMatrix[z+3][x+3] = 7
                elif colour == [0.1, 0.1, 0.9]:
                    # 1 to 2
                    self.answerMatrix[z+1][x+1] = 6
                    self.answerMatrix[z+1][x+3] = 6
                    self.answerMatrix[z+3][x+1] = 6
                    self.answerMatrix[z+3][x+3] = 6
                elif colour == [0.9, 0.1, 0.1]:
                    # 2 to 3
                    self.answerMatrix[z+1][x+1] = 8
                    self.answerMatrix[z+1][x+3] = 8
                    self.answerMatrix[z+3][x+1] = 8
                    self.answerMatrix[z+3][x+3] = 8
            
            # Victims

            #Count the number of victims
            numberVictims = self.supervisor.getFromDef('HUMANGROUP').getField("children").getCount()
            numberHazards = self.supervisor.getFromDef('HAZARDGROUP').getField("children").getCount()
            #Retrieve the node containing the victims
            victimNodes = self.supervisor.getFromDef('HUMANGROUP').getField("children")
            hazardNodes = self.supervisor.getFromDef('HAZARDGROUP').getField("children")

            for i in range(numberVictims + numberHazards):
                if i < numberVictims:
                    victim = victimNodes.getMFNode(i)
                else:
                    victim = hazardNodes.getMFNode(i - numberVictims)
                translation = victim.getField("translation").getSFVec3f()
                xCount = 0
                while translation[0] - self.xStart > 0.03:
                    translation[0] -= 0.03
                    xCount += 1
                zCount = 0
                while translation[2] - self.zStart > 0.03:
                    translation[2] -= 0.03
                    zCount += 1

                xShift = 0
                zShift = 0
                #if round(translation[0] - xStart, 4) == 0.03:
                #    xShift = 1
                #if round(translation[2] - zStart, 4) == 0.03:
                #    zShift = 1

                
                victimType = victim.getField("type").getSFString()
                if victimType == "harmed":
                    victimType = "H"
                elif victimType == "unharmed":
                    victimType = "U"
                elif victimType == "stable":
                    victimType = "S"

                rotation = victim.getField("rotation").getSFRotation()
                if abs(round(rotation[3],2)) == 1.57:
                    # Vertical
                    zCount = int(zCount/2)
                    if xCount % 2 == 0:
                        row_temp = 2*zCount + 1 + zShift
                        col_temp = xCount
                    else:
                        row_temp = 2*zCount + 1 + zShift
                        col_temp = xCount+1
                else:
                    # Horizontal
                    xCount = int(xCount/2)
                    if zCount % 2 == 0:
                        row_temp = zCount
                        col_temp = 2*xCount + 1 + xShift
                    else:
                        row_temp = zCount+1
                        col_temp = 2*xCount + 1 + xShift

                # Concatenate if victims on either side of the wall
                if type(self.answerMatrix[row_temp][col_temp]) == str:
                    self.answerMatrix[row_temp][col_temp] += victimType
                else:
                   self. answerMatrix[row_temp][col_temp] = victimType
            
            for i in range(len(self.answerMatrix)):
                self.answerMatrix[i] = list(map(str, self.answerMatrix[i]))
            
            return self.answerMatrix
            
        except:
            print("Generating map answer error.")
