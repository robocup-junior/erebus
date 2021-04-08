import AutoInstall
AutoInstall._import("np", "numpy")

def generateAnswer(supervisor):
    try:
        #Count the number of tiles
        numberTiles = supervisor.getFromDef('WALLTILES').getField("children").getCount()
        #Retrieve the node containing the tiles
        tileNodes = supervisor.getFromDef('WALLTILES').getField("children")
        
        xPos = [tileNodes.getMFNode(i).getField("xPos").getSFInt32() for i in range(numberTiles)]
        zPos = [tileNodes.getMFNode(i).getField("zPos").getSFInt32() for i in range(numberTiles)]

        x_size = max(xPos) - min(xPos) + 1
        z_size = max(zPos) - min(zPos) + 1
        answerMatrix = [[0] * (x_size * 4 + 1) for i in range(z_size * 4 + 1)]

        xStart = -(tileNodes.getMFNode(0).getField("width").getSFFloat() * (0.3 * tileNodes.getMFNode(0).getField("xScale").getSFFloat()) / 2.0) -0.06
        zStart = -(tileNodes.getMFNode(0).getField("height").getSFFloat() * (0.3 * tileNodes.getMFNode(0).getField("zScale").getSFFloat()) / 2.0) -0.06

        for i in range(numberTiles):
            tmpMatrix = [[-1] * (x_size * 4 + 1) for i in range(z_size * 4 + 1)]
            tile = tileNodes.getMFNode(i)
            x = 4*tile.getField("xPos").getSFInt32()
            z = 4*tile.getField("zPos").getSFInt32()

            # Wall
            if tile.getField("topWall").getSFInt32() > 0:
                tmpMatrix[z][x] = 1
                tmpMatrix[z][x+1] = 1
                tmpMatrix[z][x+2] = 1
                tmpMatrix[z][x+3] = 1
                tmpMatrix[z][x+4] = 1
            if tile.getField("bottomWall").getSFInt32() > 0:
                tmpMatrix[z+4][x] = 1
                tmpMatrix[z+4][x+1] = 1
                tmpMatrix[z+4][x+2] = 1
                tmpMatrix[z+4][x+3] = 1
                tmpMatrix[z+4][x+4] = 1
            if tile.getField("rightWall").getSFInt32() > 0:
                tmpMatrix[z][x+4] = 1
                tmpMatrix[z+1][x+4] = 1
                tmpMatrix[z+2][x+4] = 1
                tmpMatrix[z+3][x+4] = 1
                tmpMatrix[z+4][x+4] = 1
            if tile.getField("leftWall").getSFInt32() > 0:
                tmpMatrix[z][x] = 1
                tmpMatrix[z+1][x] = 1
                tmpMatrix[z+2][x] = 1
                tmpMatrix[z+3][x] = 1
                tmpMatrix[z+4][x] = 1
            
            room = tile.getField("room").getSFInt32()
            ## Half wall
            if room >= 2:
                if tile.getField("tile1Walls").getMFInt32(0) > 0:
                    tmpMatrix[z][x] = 1
                    tmpMatrix[z][x+1] = 1
                    tmpMatrix[z][x+2] = 1
                if tile.getField("tile1Walls").getMFInt32(1) > 0:
                    tmpMatrix[z][x+2] = 1
                    tmpMatrix[z+1][x+2] = 1
                    tmpMatrix[z+2][x+2] = 1
                if tile.getField("tile1Walls").getMFInt32(2) > 0:
                    tmpMatrix[z+2][x] = 1
                    tmpMatrix[z+2][x+1] = 1
                    tmpMatrix[z+2][x+2] = 1
                if tile.getField("tile1Walls").getMFInt32(3) > 0:
                    tmpMatrix[z][x] = 1
                    tmpMatrix[z+1][x] = 1
                    tmpMatrix[z+2][x] = 1
                
                if tile.getField("tile2Walls").getMFInt32(0) > 0:
                    tmpMatrix[z][x+2] = 1
                    tmpMatrix[z][x+3] = 1
                    tmpMatrix[z][x+4] = 1
                if tile.getField("tile2Walls").getMFInt32(1) > 0:
                    tmpMatrix[z][x+4] = 1
                    tmpMatrix[z+1][x+4] = 1
                    tmpMatrix[z+2][x+4] = 1
                if tile.getField("tile2Walls").getMFInt32(2) > 0:
                    tmpMatrix[z+2][x+2] = 1
                    tmpMatrix[z+2][x+3] = 1
                    tmpMatrix[z+2][x+4] = 1
                if tile.getField("tile2Walls").getMFInt32(3) > 0:
                    tmpMatrix[z][x+2] = 1
                    tmpMatrix[z+1][x+2] = 1
                    tmpMatrix[z+2][x+2] = 1

                if tile.getField("tile3Walls").getMFInt32(0) > 0:
                    tmpMatrix[z+2][x] = 1
                    tmpMatrix[z+2][x+1] = 1
                    tmpMatrix[z+2][x+2] = 1
                if tile.getField("tile3Walls").getMFInt32(1) > 0:
                    tmpMatrix[z+2][x+2] = 1
                    tmpMatrix[z+3][x+2] = 1
                    tmpMatrix[z+4][x+2] = 1
                if tile.getField("tile3Walls").getMFInt32(2) > 0:
                    tmpMatrix[z+4][x] = 1
                    tmpMatrix[z+4][x+1] = 1
                    tmpMatrix[z+4][x+2] = 1
                if tile.getField("tile3Walls").getMFInt32(3) > 0:
                    tmpMatrix[z+2][x] = 1
                    tmpMatrix[z+3][x] = 1
                    tmpMatrix[z+4][x] = 1

                if tile.getField("tile4Walls").getMFInt32(0) > 0:
                    tmpMatrix[z+2][x+2] = 1
                    tmpMatrix[z+2][x+3] = 1
                    tmpMatrix[z+2][x+4] = 1
                if tile.getField("tile4Walls").getMFInt32(1) > 0:
                    tmpMatrix[z+2][x+4] = 1
                    tmpMatrix[z+3][x+4] = 1
                    tmpMatrix[z+4][x+4] = 1
                if tile.getField("tile4Walls").getMFInt32(2) > 0:
                    tmpMatrix[z+4][x+2] = 1
                    tmpMatrix[z+4][x+3] = 1
                    tmpMatrix[z+4][x+4] = 1
                if tile.getField("tile4Walls").getMFInt32(3) > 0:
                    tmpMatrix[z+2][x+2] = 1
                    tmpMatrix[z+3][x+2] = 1
                    tmpMatrix[z+4][x+2] = 1
            
            # Curved walls
            if room >= 3:
                # Left top
                lt = tile.getField("curve").getMFInt32(0)
                if lt == 1:
                    tmpMatrix[z][x] = 1
                    tmpMatrix[z][x+1] = 1
                    if answerMatrix[z][x+2] == 1:
                        tmpMatrix[z][x+2] = -1
                    else:
                        tmpMatrix[z][x+2] = 0
                    tmpMatrix[z+1][x+2] = 1
                    tmpMatrix[z+2][x+2] = 1
                if lt == 2:
                    tmpMatrix[z+2][x] = 1
                    tmpMatrix[z+2][x+1] = 1
                    if answerMatrix[z+2][x+2] == 1:
                        tmpMatrix[z+2][x+2] = -1
                    else:
                        tmpMatrix[z+2][x+2] = 0
                    tmpMatrix[z+1][x+2] = 1
                    tmpMatrix[z][x+2] = 1
                if lt == 3:
                    tmpMatrix[z][x] = 1
                    tmpMatrix[z+1][x] = 1
                    if answerMatrix[z+2][x] == 1:
                        tmpMatrix[z+2][x] = -1
                    else:
                        tmpMatrix[z+2][x] = 0
                    tmpMatrix[z+2][x+1] = 1
                    tmpMatrix[z+2][x+2] = 1
                if lt == 4:
                    tmpMatrix[z+2][x] = 1
                    tmpMatrix[z+1][x] = 1
                    if answerMatrix[z][x] == 1:
                        tmpMatrix[z][x] = -1
                    else:
                        tmpMatrix[z][x] = 0
                    tmpMatrix[z][x+1] = 1
                    tmpMatrix[z][x+2] = 1
                
                # Right top
                rt = tile.getField("curve").getMFInt32(1)
                if rt == 1:
                    tmpMatrix[z][x+2] = 1
                    tmpMatrix[z][x+3] = 1
                    if answerMatrix[z][x+4] == 1:
                        tmpMatrix[z][x+4] = -1
                    else:
                        tmpMatrix[z][x+4] = 0
                    tmpMatrix[z+1][x+4] = 1
                    tmpMatrix[z+2][x+4] = 1
                if rt == 2:
                    tmpMatrix[z+2][x+2] = 1
                    tmpMatrix[z+2][x+3] = 1
                    if answerMatrix[z+2][x+4] == 1:
                        tmpMatrix[z+2][x+4] = -1
                    else:
                        tmpMatrix[z+2][x+4] = 0
                    tmpMatrix[z+1][x+4] = 1
                    tmpMatrix[z][x+4] = 1
                if rt == 3:
                    tmpMatrix[z][x+2] = 1
                    tmpMatrix[z+1][x+2] = 1
                    if answerMatrix[z+2][x+2] == 1:
                        tmpMatrix[z+2][x+2] = -1
                    else:
                        tmpMatrix[z+2][x+2] = 0
                    tmpMatrix[z+2][x+3] = 1
                    tmpMatrix[z+2][x+4] = 1
                if rt == 4:
                    tmpMatrix[z+2][x+2] = 1
                    tmpMatrix[z+1][x+2] = 1
                    if answerMatrix[z][x+2] == 1:
                        tmpMatrix[z][x+2] = -1
                    else:
                        tmpMatrix[z][x+2] = 0
                    tmpMatrix[z][x+3] = 1
                    tmpMatrix[z][x+4] = 1
                
                # Left bottom
                lb = tile.getField("curve").getMFInt32(2)
                if lb == 1:
                    tmpMatrix[z+2][x] = 1
                    tmpMatrix[z+2][x+1] = 1
                    if answerMatrix[z+2][x+2] == 1:
                        tmpMatrix[z+2][x+2] = -1
                    else:
                        tmpMatrix[z+2][x+2] = 0
                    tmpMatrix[z+3][x+2] = 1
                    tmpMatrix[z+4][x+2] = 1
                if lb == 2:
                    tmpMatrix[z+4][x] = 1
                    tmpMatrix[z+4][x+1] = 1
                    if answerMatrix[z+4][x+2] == 1:
                        tmpMatrix[z+4][x+2] = -1
                    else:
                        tmpMatrix[z+4][x+2] = 0
                    tmpMatrix[z+3][x+2] = 1
                    tmpMatrix[z+2][x+2] = 1
                if lb == 3:
                    tmpMatrix[z+2][x] = 1
                    tmpMatrix[z+3][x] = 1
                    if answerMatrix[z+4][x] == 1:
                        tmpMatrix[z+4][x] = -1
                    else:
                        tmpMatrix[z+4][x] = 0
                    tmpMatrix[z+4][x+1] = 1 
                    tmpMatrix[z+4][x+2] = 1
                if lb == 4:
                    tmpMatrix[z+4][x] = 1
                    tmpMatrix[z+3][x] = 1
                    if answerMatrix[z+2][x] == 1:
                        tmpMatrix[z+2][x] = -1
                    else:
                        tmpMatrix[z+2][x] = 0
                    tmpMatrix[z+2][x+1] = 1
                    tmpMatrix[z+2][x+2] = 1
                
                # Right bottom
                rb = tile.getField("curve").getMFInt32(3)
                if rb == 1:
                    tmpMatrix[z+2][x+2] = 1
                    tmpMatrix[z+2][x+3] = 1
                    if answerMatrix[z+2][x+4] == 1:
                        tmpMatrix[z+2][x+4] = -1
                    else:
                        tmpMatrix[z+2][x+4] = 0
                    tmpMatrix[z+3][x+4] = 1
                    tmpMatrix[z+4][x+4] = 1
                if rb == 2:
                    tmpMatrix[z+4][x+2] = 1
                    tmpMatrix[z+4][x+3] = 1
                    if answerMatrix[z+4][x+4] == 1:
                        tmpMatrix[z+4][x+4] = -1
                    else:
                        tmpMatrix[z+4][x+4] = 0
                    tmpMatrix[z+3][x+4] = 1
                    tmpMatrix[z+2][x+4] = 1
                if rb == 3:
                    tmpMatrix[z+2][x+2] = 1
                    tmpMatrix[z+3][x+2] = 1
                    if answerMatrix[z+4][x+2] == 1:
                        tmpMatrix[z+4][x+2] = -1
                    else:
                        tmpMatrix[z+4][x+2] = 0
                    tmpMatrix[z+4][x+3] = 1
                    tmpMatrix[z+4][x+4] = 1
                if rb == 4:
                    tmpMatrix[z+4][x+2] = 1
                    tmpMatrix[z+3][x+2] = 1
                    if answerMatrix[z+2][x+2] == 1:
                        tmpMatrix[z+2][x+2] = -1
                    else:
                        tmpMatrix[z+2][x+2] = 0
                    tmpMatrix[z+2][x+3] = 1
                    tmpMatrix[z+2][x+4] = 1
                    


            
            if tile.getField("trap").getSFBool():
                tmpMatrix[z+1][x+1] = 2
                tmpMatrix[z+1][x+3] = 2
                tmpMatrix[z+3][x+1] = 2
                tmpMatrix[z+3][x+3] = 2
            if tile.getField("swamp").getSFBool():
                tmpMatrix[z+1][x+1] = 3
                tmpMatrix[z+1][x+3] = 3
                tmpMatrix[z+3][x+1] = 3
                tmpMatrix[z+3][x+3] = 3
            if tile.getField("checkpoint").getSFBool():
                tmpMatrix[z+1][x+1] = 4
                tmpMatrix[z+1][x+3] = 4
                tmpMatrix[z+3][x+1] = 4
                tmpMatrix[z+3][x+3] = 4
            if tile.getField("start").getSFBool():
                tmpMatrix[z+1][x+1] = 6
                tmpMatrix[z+1][x+3] = 6
                tmpMatrix[z+3][x+1] = 6
                tmpMatrix[z+3][x+3] = 6
            
            colour = tile.getField("tileColor").getSFColor()
            colour = [round(colour[0], 1), round(colour[1], 1), round(colour[2], 1)]
            if colour == [0.3, 0.1, 0.6]:
                # 1 to 3
                tmpMatrix[z+1][x+1] = 8
                tmpMatrix[z+1][x+3] = 8
                tmpMatrix[z+3][x+1] = 8
                tmpMatrix[z+3][x+3] = 8
            elif colour == [0.1, 0.1, 0.9]:
                # 1 to 2
                tmpMatrix[z+1][x+1] = 7
                tmpMatrix[z+1][x+3] = 7
                tmpMatrix[z+3][x+1] = 7
                tmpMatrix[z+3][x+3] = 7
            elif colour == [0.9, 0.1, 0.1]:
                # 2 to 3
                tmpMatrix[z+1][x+1] = 9
                tmpMatrix[z+1][x+3] = 9
                tmpMatrix[z+3][x+1] = 9
                tmpMatrix[z+3][x+3] = 9

            for i in range(len(answerMatrix)):
                for j in range(len(answerMatrix[i])):
                    if tmpMatrix[i][j] != -1:
                        answerMatrix[i][j] = tmpMatrix[i][j]
        
        # Victims

        #Count the number of victims
        numberVictims = supervisor.getFromDef('HUMANGROUP').getField("children").getCount()
        numberHazards = supervisor.getFromDef('HAZARDGROUP').getField("children").getCount()
        #Retrieve the node containing the victims
        victimNodes = supervisor.getFromDef('HUMANGROUP').getField("children")
        hazardNodes = supervisor.getFromDef('HAZARDGROUP').getField("children")

        for i in range(numberVictims + numberHazards):
            if i < numberVictims:
                victim = victimNodes.getMFNode(i)
            else:
                victim = hazardNodes.getMFNode(i - numberVictims)
            translation = victim.getField("translation").getSFVec3f()
            xCount = 0
            while translation[0] - xStart > 0.03:
                translation[0] -= 0.03
                xCount += 1
            zCount = 0
            while translation[2] - zStart > 0.03:
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
                    answerMatrix[2*zCount + 1 + zShift][xCount] = victimType
                else:
                    answerMatrix[2*zCount + 1 + zShift][xCount+1] = victimType
            else:
                # Horizontal
                xCount = int(xCount/2)
                if zCount % 2 == 0:
                    answerMatrix[zCount][2*xCount + 1 + xShift] = victimType
                else:
                    answerMatrix[zCount+1][2*xCount + 1 + xShift] = victimType

        
        for i in range(len(answerMatrix)):
            answerMatrix[i] = list(map(str, answerMatrix[i]))
        return answerMatrix
        
    except:
        print("Generating map answer error.")
