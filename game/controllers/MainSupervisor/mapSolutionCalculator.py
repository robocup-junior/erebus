"""Map Solution Calculator v3
   Written by Robbie Goldman

ChangeLog:
 - V2
 - Added smaller and curved walls
 - Added transitions between regions
 - Tiles are now represented by a 5x5 area (edges overlap)
 - V3
 - Now split into three regions - normal, small and curved walls
"""
import os
import AutoInstall
AutoInstall._import("Image", "PIL.Image", "Pillow")

def getWallData(tilesList:list) -> list:
    '''Iterates through 2d array of tile data leaving only the wall information'''
    onlyWallData = []

    #Iterate through rows
    for y in range(0, len(tilesList)):
        row = []
        #Iterate through columns
        for x in range(0, len(tilesList[y])):
            #If there is a tile here
            if tilesList[y][x] != None:
                #Add the wall data
                row.append([tilesList[y][x][1][0], tilesList[y][x][1][1], tilesList[y][x][1][2], tilesList[y][x][1][3]])
            else:
                #Add nothing for both types and no transition or curve
                row.append([None, None, False, False])
        
        #Add the row to the array
        onlyWallData.append(row)
    
    #Return the 2d array of wall booleans
    return onlyWallData

def wallsToArray(wallData) -> (list, list, list):
    '''Convert array of wall booleans to numerical array representing wall information'''
    #Get the dimensions of the map
    yDim = len(wallData)
    xDim = 1
    if yDim > 0:
        xDim = len(wallData[0])

    #Array to hold modified data about the walls and tiles 
    wallInfoArray = []
    #Which part of the map each tile belongs to
    partType = []

    #Iterate through each row of tiles
    for yPos in range(0, yDim):
        #Row of data for wall info
        infoRow = []
        #Row of data for the type info
        typeRow = []
        #Iterate through the tiles
        for xPos in range(0, xDim):
            #Add No tile, not small walls, not curved walls [No upper wall, no right wall, no bottom wall, no left wall]
            infoRow.append([False, False, False, [False, False, False, False]])
            #Add - does not belong to any region yet
            typeRow.append(0)
        #Add rows to arrays
        wallInfoArray.append(infoRow)
        partType.append(typeRow)

    #Iterate through rows of tiles
    for tileY in range(0, len(wallData)):
        #Iterate through columns of tiles
        for tileX in range(0, len(wallData[tileY])):
            #Get the tiles large walls
            tile = wallData[tileY][tileX][0]
            #Get the tiles small walls
            smallTile = wallData[tileY][tileX][1]
            #Get the transition state
            transition = wallData[tileY][tileX][2]
            #Get the curved state
            curved = wallData[tileY][tileX][3]
            wallInfoArray[tileY][tileX][2] = curved
            #Calculate top left corner in array
            start = [tileX * 4, tileY * 4]

            #If there is a tile
            if tile != None:
                #There is a tile here
                wallInfoArray[tileY][tileX][0] = True
                #Add data to the wall info array
                wallInfoArray[tileY][tileX][3][0] = tile[0]
                wallInfoArray[tileY][tileX][3][1] = tile[1]
                wallInfoArray[tileY][tileX][3][2] = tile[2]
                wallInfoArray[tileY][tileX][3][3] = tile[3]
            
            #If there is a tile
            if smallTile != None:
                #Iterate through sub tiles
                for index in range(0, 4):
                    #Get the wall data
                    tilePart = smallTile[index]
                    #Add to data if there are any small walls
                    wallInfoArray[tileY][tileX][1] = tilePart[0] or tilePart[1] or tilePart[2] or tilePart[3] or curved

    #List of surrounding tile changes
    around = [[0,-1], [1,0], [0,1], [-1,0]]
    #Opposite direction positions
    opposite = [2, 3, 0, 1]

    #Iterate through tiles
    for tileY in range(0, len(wallInfoArray)):
        for tileX in range(0, len(wallInfoArray[tileY])):
            #Iterate through directions
            for dire in range(0, 4):
                #Get the other tile position
                other = [tileX + around[dire][0], tileY + around[dire][1]]
                #If it is within the array
                if other[0] > -1 and other[0] < len(wallInfoArray[0]) and other[1] > -1 and other[1] < len(wallInfoArray):
                    #If there is a wall on the opposing side
                    if wallInfoArray[other[1]][other[0]][3][opposite[dire]]:
                        #Add a corresponding wall on this side
                        wallInfoArray[tileY][tileX][3][dire] = True

    #List of transition tiles
    transitions = []
    #List to hold corresponding regions for each transition
    transitionParts = []

    #Iterate for each of the regions (represented by 1, 2 and 3)
    for tileType in range(1, 4):
        
        #List of tiles yet to be tested
        tilesToCheck = []
        #Not yet ready to start
        done = False

        #Iterate tiles
        for tileY in range(0, len(wallData)):
            for tileX in range(0, len(wallData[tileY])):
                #If a start has not been found
                if not done:
                    #If the tile is not part of another group
                    if partType[tileY][tileX] == 0:
                        #Get the tile data
                        tileData = wallInfoArray[tileY][tileX]
                        #If the current pass is normal walls and the tile exists and does not have small or curved walls
                        if tileType == 1 and (tileData[0] and not tileData[1] and not tileData[2]):
                            #Add the tile
                            tilesToCheck.append([tileX, tileY])
                            #Ready to start
                            done = True
                        
                        #If the current pass is small walls and the tile exists and has small but not curved walls
                        if tileType == 3 and (tileData[0] and tileData[1] and not tileData[2]):
                            #Add the tile
                            tilesToCheck.append([tileX, tileY])
                            #Ready to start
                            done = True
                        
                        #If the current pass is curved walls and the tile exists and has small and curved walls
                        if tileType == 2 and (tileData[0] and tileData[1] and tileData[2]):
                            #Add the tile
                            tilesToCheck.append([tileX, tileY])
                            #Ready to start
                            done = True

        #Repeat until there are no tiles to check
        while len(tilesToCheck) > 0:
            #Pop the first tile position
            checkingTile = tilesToCheck[0]
            del tilesToCheck[0]

            #Get the information about the tile
            tileData = wallInfoArray[checkingTile[1]][checkingTile[0]]
            
            #If it is not a transition tile
            if not wallData[checkingTile[1]][checkingTile[0]][2]:
                #Set the type of this tile
                partType[checkingTile[1]][checkingTile[0]] = tileType
                #For the directions around
                for dire in range(0, 4):
                    #Get the direction
                    a = around[dire]
                    #Get the position of the tile
                    otherPos = [checkingTile[0] + a[0], checkingTile[1] + a[1]]
                    #If it is within the array
                    if otherPos[0] > -1 and otherPos[0] < len(wallInfoArray[checkingTile[1]]) and otherPos[1] > -1 and otherPos[1] < len(wallInfoArray):
                        #If there is not a blocking wall in this direction and the tile has not yet been used
                        if not tileData[3][dire] and partType[otherPos[1]][otherPos[0]] == 0:
                            #If the tile is not already marked for checking
                            if otherPos not in tilesToCheck:
                                #Add the tile to the list for checking
                                tilesToCheck.append(otherPos)
            else:
                #If the transition tile has not been marked yet
                if checkingTile not in transitions:
                    #Add it to the list
                    transitions.append(checkingTile)
                    #Add this type to its region list
                    transitionParts.append([tileType])
                else:
                    #Add this type to its region list
                    transitionParts[transitions.index(checkingTile)].append(tileType)

    #Add a marker to each of the transition tiles
    for transition in transitions:
        partType[transition[1]][transition[0]] = 5

    #List to contain each of the three regions
    partialMaps = [[], [], []]

    #Iterate for the region numbers
    for tileType in range(1, 4):
        
        #Array to hold the partial map at full size
        dataArray = []

        #Iterate through rows of tiles (five for each with one overlap)
        for yPos in range(0, (yDim * 4) + 1):
            row = []
            #Iterate through columns of tiles (five for each with one overlap)
            for xPos in range(0, (xDim * 4) + 1):
                #Add an empty space
                row.append(9)
            #Add the row to the 2d array
            dataArray.append(row)

        #Iterate through rows of tiles
        for tileY in range(0, len(wallData)):
            #Iterate through columns of tiles
            for tileX in range(0, len(wallData[tileY])):
                #If this is a transition tile that belongs to this region
                thisTransition = [tileX, tileY] in transitions and tileType in transitionParts[transitions.index([tileX, tileY])]
                if partType[tileY][tileX] == tileType or thisTransition:
                    #Get the tiles large walls
                    tile = wallInfoArray[tileY][tileX][3]
                    #Get the tiles small walls
                    smallTile = wallData[tileY][tileX][1]
                    #Get the transition state
                    transition = wallData[tileY][tileX][2]
                    #Get the curved state
                    curved = wallData[tileY][tileX][3]
                    #Calculate top left corner in array
                    start = [tileX * 4, tileY * 4]

                    #If there is a tile
                    if tile != None:
                        #Fill 5x5 space with floor (if there isn't something there already)
                        for xP in range(start[0], start[0] + 5):
                            for yP in range(start[1], start[1] + 5):
                                if dataArray[yP][xP] == 9:
                                    if transition:
                                        dataArray[yP][xP] = 5
                                    else:
                                        dataArray[yP][xP] = 0

                        #Add each of the walls if they are present
                        if tile[0]:
                            for xP in range(start[0], start[0] + 5):
                                dataArray[start[1]][xP] = 1
                        if tile[1]:
                            for yP in range(start[1], start[1] + 5):
                                dataArray[yP][start[0] + 4] = 1
                        if tile[2]:
                            for xP in range(start[0], start[0] + 5):
                                dataArray[start[1] + 4][xP] = 1
                        if tile[3]:
                            for yP in range(start[1], start[1] + 5):
                                dataArray[yP][start[0]] = 1
                    
                    #If there is a tile
                    if smallTile != None:
                        #Offset arrangement for each of the sub tiles
                        startOffsets = [[0, 0], [2, 0], [0, 2], [2, 2]]
                        #Iterate through sub tiles
                        for index in range(0, 4):
                            #Calculate new start position for sub tile
                            currentStart = [start[0] + startOffsets[index][0], start[1] + startOffsets[index][1]]
                            #Get the wall data
                            tilePart = smallTile[index]
                            #Add each of the small walls if they are present
                            if tilePart[0]:
                                for xp in range(currentStart[0], currentStart[0] + 3):
                                    dataArray[currentStart[1]][xp] = 1
                            if tilePart[1]:
                                for yp in range(currentStart[1], currentStart[1] + 3):
                                    dataArray[yp][currentStart[0] + 2] = 1
                            if tilePart[2]:
                                for xp in range(currentStart[0], currentStart[0] + 3):
                                    dataArray[currentStart[1] + 2][xp] = 1
                            if tilePart[3]:
                                for yp in range(currentStart[1], currentStart[1] + 3):
                                    dataArray[yp][currentStart[0]] = 1

        #Boundaries of map data (reversed so the check will correctly size them to the limit of the information in the map)
        xStart = len(dataArray[0])
        xEnd = 0
        yStart = len(dataArray)
        yEnd = 0

        #Iterate through the map
        for yPos in range(0, len(dataArray)):
            for xPos in range(0, len(dataArray[yPos])):
                #If there is something in this position
                if dataArray[yPos][xPos] != 9:
                    #If it moves the boundaries - adjust them accordingly
                    if xPos < xStart:
                        xStart = xPos
                    if xPos > xEnd:
                        xEnd = xPos
                    if yPos < yStart:
                        yStart = yPos
                    if yPos > yEnd:
                        yEnd = yPos

        #Iterate through the array between the boundaries
        for yPos in range(yStart, yEnd + 1):
            row = []
            for xPos in range(xStart, xEnd + 1):
                #Add the data to the row
                row.append(dataArray[yPos][xPos])
            #Add the row to the final array
            partialMaps[tileType - 1].append(row)

    #Return completed 2d arrays of walls: normal, small, curved
    return partialMaps[0], partialMaps[2], partialMaps[1]

def arrayToImage (wallArray: list) -> None:
    '''Create an image representation of the data'''    

    #Get directory name
    dirname = os.path.dirname(__file__)

    #Create a new image (black background)
    img = Image.new("RGB", (len(wallArray[0]), len(wallArray)), "#000000")

    #Iterate through items in the array
    for y in range(0, len(wallArray)):
        for x in range(0, len(wallArray[y])):
            #Floors - white
            if wallArray[y][x] == 0:
                img.putpixel((x,y), (255, 255, 255))
            #Walls - blue
            if wallArray[y][x] == 1:
                img.putpixel((x,y), (0, 0, 255))
            #Second section (curved) - red
            if wallArray[y][x] == 2:
                img.putpixel((x,y), (255, 0, 0))
            #Third section (small) - green
            if wallArray[y][x] == 3:
                img.putpixel((x,y), (0, 255, 0))
            #Connector - cyan
            if wallArray[y][x] == 5:
                img.putpixel((x,y), (0, 255, 255))

    #Save the file in this directory
    img.save(os.path.join(dirname, "mapSolution.png"), "PNG")

def convertTilesToArray (tileDataGrid: list) -> (list, list, list):
    '''Turn a 2d array of tile data into 2d array map solution'''
    #Convert tile data arraty to wall data array
    wallData = getWallData(tileDataGrid)
    #Create map arrays from wall data array
    normalWallArray, smallWallArray, curvedWallArray = wallsToArray(wallData)
    #Create an image of the array - (!used for testing purposes only!)
    arrayToImage(curvedWallArray)
    #Return completed arrays
    return normalWallArray, smallWallArray, curvedWallArray
