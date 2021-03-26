"""Map Solution Calculator v2
   Written by Robbie Goldman

ChangeLog:
 - V2
 - Added smaller and curved walls
 - Added transitions between regions
 - Tiles are now represented by a 5x5 area (edges overlap)
"""

def getWallData(tilesList:list):
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
                row.append([tilesList[y][x][1][0], tilesList[y][x][1][1], tilesList[y][x][1][2]])
            else:
                #Add nothing for both types and no transition
                row.append([None, None, False])
        
        #Add the row to the array
        onlyWallData.append(row)
    
    #Return the 2d array of wall booleans
    return onlyWallData

def wallsToArray(wallData):
    '''Convert array of wall booleans to numerical array representing wall information'''
    #Get the dimensions of the map
    yDim = len(wallData)
    xDim = 1
    if yDim > 0:
        xDim = len(wallData[0])
    
    #Array to store map layout
    wallArray = []
    #Iterate through rows of tiles (five for each with one overlap)
    for yPos in range(0, (yDim * 4) + 1):
        row = []
        #Iterate through columns of tiles (five for each with one overlap)
        for xPos in range(0, (xDim * 4) + 1):
            #Add an empty space
            row.append(9)
        #Add the row to the 2d array
        wallArray.append(row)

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
            #Calculate top left corner in array
            start = [tileX * 4, tileY * 4]

            #If there is a tile
            if tile != None:
                #Fill 5x5 space with floor (if there isn't something there already)
                for xP in range(start[0], start[0] + 5):
                    for yP in range(start[1], start[1] + 5):
                        if wallArray[yP][xP] == 9:
                            if transition:
                                wallArray[yP][xP] = 5
                            else:
                                wallArray[yP][xP] = 0

                #Add each of the walls if they are present
                if tile[0]:
                    for xP in range(start[0], start[0] + 5):
                        wallArray[start[1]][xP] = 1
                if tile[1]:
                    for yP in range(start[1], start[1] + 5):
                        wallArray[yP][start[0] + 4] = 1
                if tile[2]:
                    for xP in range(start[0], start[0] + 5):
                        wallArray[start[1] + 4][xP] = 1
                if tile[3]:
                    for yP in range(start[1], start[1] + 5):
                        wallArray[yP][start[0]] = 1
            
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
                            wallArray[currentStart[1]][xp] = 1
                    if tilePart[1]:
                        for yp in range(currentStart[1], currentStart[1] + 3):
                            wallArray[yp][currentStart[0] + 2] = 1
                    if tilePart[2]:
                        for xp in range(currentStart[0], currentStart[0] + 3):
                            wallArray[currentStart[1] + 2][xp] = 1
                    if tilePart[3]:
                        for yp in range(currentStart[1], currentStart[1] + 3):
                            wallArray[yp][currentStart[0]] = 1
    
    #Return completed 2d array
    return wallArray

def arrayToImage (wallArray):
    '''Create an image representation of the data'''
    #Import necessary libraries
    from PIL import Image
    import os

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
            #Connector - cyan
            if wallArray[y][x] == 5:
                img.putpixel((x,y), (0, 255, 255))

    #Save the file in this directory
    img.save(os.path.join(dirname, "mapSolution.png"), "PNG")

def convertTilesToArray (tileDataGrid):
    '''Turn a 2d array of tile data into 2d array map solution'''
    #Convert tile data arraty to wall data array
    wallData = getWallData(tileDataGrid)
    #Create map array from wall data array
    wallArray = wallsToArray(wallData)
    #Create an image of the array - (!used for testing purposes only!)
    #arrayToImage(wallArray)
    #Return completed array
    return wallArray