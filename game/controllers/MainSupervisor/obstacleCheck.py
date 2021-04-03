def checkIntersect(circleCentre:list, circleRadius:float, wallPos:list, wallDim:list) -> bool:
    '''Returns true if the circle intersects the wall'''
    #Calculate the closest point on the wall (rectangle) to the circle (obstacle)
    xChange = circleCentre[0] - max(wallPos[0], min(circleCentre[0], wallPos[0] + wallDim[0] / 2))
    yChange = circleCentre[1] - max(wallPos[1], min(circleCentre[1], wallPos[1] + wallDim[1] / 2))
    #Returns true if the closest point is inside the circle
    return ((xChange ** 2) + (yChange ** 2)) <= (circleRadius ** 2)


def checkManyIntersect(circleCentre:list, circleRadius:float, wallDimList:list) -> bool:
    '''Test if a given circle intersects any of the given walls'''
    #If this obstacle can be where it is
    allowed = True

    #Iterate through the walls
    for dimensions in wallDimList:
        #Only check if not yet intersected
        if allowed:
            #Check for intersection
            intersect = checkIntersect(circleCentre, circleRadius, dimensions[0], dimensions[1])
            if intersect:
                #If it intersects a wall, it is not allowed where it is
                allowed = False
    
    return allowed


def dimensionsToCircle(dimensions:list) -> float:
    '''Convert a width and depth to a radius'''
    #c = square root of a ^ + b ^
    radius = (((dimensions[0] / 2) ** 2) + ((dimensions[1] / 2) ** 2)) ** 0.5
    return radius


def getWallsFromTilePosition(position:list, walls:list, smallWalls:list, scale:float) -> list:
    '''Convert tile position and list of if walls are present to list of wall positions and dimensions, properly scaled'''
    wallsPresent = []

    #Calculate the tile side length and wall width
    sideLength = 0.3 * scale
    wallWidth = 0.015 * scale

    #Upper wall
    if walls[0]:
        wall = [[position[0], position[1] - (sideLength / 2) + (wallWidth / 2)], [sideLength, wallWidth]]
        wallsPresent.append(wall)
    #Right wall
    if walls[1]:
        wall = [[position[0] + (sideLength / 2) - (wallWidth / 2), position[1]], [wallWidth, sideLength]]
        wallsPresent.append(wall)
    #Bottom wall
    if walls[2]:
        wall = [[position[0], position[1] + (sideLength / 2) - (wallWidth / 2)], [sideLength, wallWidth]]
        wallsPresent.append(wall)
    #Left wall
    if walls[3]:
        wall = [[position[0] - (sideLength / 2) + (wallWidth / 2), position[1]], [wallWidth, sideLength]]
        wallsPresent.append(wall)

    #Half the side length for the walls
    smallSideLength = sideLength / 2
    #Offset of centres of tiles
    sideChange = sideLength / 4
    #Centre positions of all four sub tiles - top left, top right, bottom left, bottom right
    smallCentres = [[position[0] - sideChange, position[1] - sideChange], [position[0] + sideChange, position[1] - sideChange], [position[0] - sideChange, position[1] + sideChange], [position[0] + sideChange, position[1] + sideChange]]

    #Iterate through sub tiles
    for smallIndex in range(0, 4):
        #Get the data for the sub tile
        smallWallData = smallWalls[smallIndex]
        #Upper wall
        if smallWallData[0]:
            wall = [[smallCentres[smallIndex][0], smallCentres[smallIndex][1] - (smallSideLength / 2) + (wallWidth / 2)], [smallSideLength, wallWidth]]
            wallsPresent.append(wall)
        #Right wall
        if smallWallData[1]:
            wall = [[smallCentres[smallIndex][0] + (smallSideLength / 2) - (wallWidth / 2), smallCentres[smallIndex][1]], [wallWidth, smallSideLength]]
            wallsPresent.append(wall)
        #Bottom wall
        if smallWallData[2]:
            wall = [[smallCentres[smallIndex][0], smallCentres[smallIndex][1] + (smallSideLength / 2) - (wallWidth / 2)], [smallSideLength, wallWidth]]
            wallsPresent.append(wall)
        #Left wall
        if smallWallData[3]:
            wall = [[smallCentres[smallIndex][0] - (smallSideLength / 2) + (wallWidth / 2), smallCentres[smallIndex][1]], [wallWidth, smallSideLength]]
            wallsPresent.append(wall)
    
    return wallsPresent


def drawLayout(walls:list, obstacles:list, offset:float) -> None:
    '''Draws the layout using python turtle'''
    '''DEBUG ONLY - do not use when running simulations (due to duration and window it causes supervisor to crash)'''
    #List to contain the scaled up walls
    scaledWalls = []

    #Scale up the walls to a viewable size
    for w in walls:
        scaledWalls.append([[w[0][0] * 500, -w[0][1] * 500], [w[1][0] * 500, w[1][1] * 500]])
    
    #Create the turtle
    import turtle
    t = turtle.Turtle()
    t.color("red")
    t.penup()
    t.speed(0)

    #Iterate the walls
    for wall in scaledWalls:

        #Draw the wall from the bottom left
        t.setposition(wall[0][0] - (wall[1][0] / 2), wall[0][1] - (wall[1][1] / 2))
        t.setheading(0)
        t.pendown()
        t.forward(wall[1][0])
        t.left(90)
        t.forward(wall[1][1])
        t.left(90)
        t.forward(wall[1][0])
        t.left(90)
        t.forward(wall[1][1])
        t.penup()

    #Change colour for obstacles
    t.color("blue")

    #Iterate through the obstacles
    for obstacle in obstacles:
        #Calculate radius
        rad = dimensionsToCircle(obstacle[1])
        #Draw clearance sized radius
        t.setposition(obstacle[0][0] * 500, (-obstacle[0][1] * 500) - ((rad + offset) * 500))
        t.setheading(0)
        t.pendown()
        t.circle((rad + offset) * 500)
        t.penup()
        #Draw actual obstacle radius
        t.setposition(obstacle[0][0] * 500, (-obstacle[0][1] * 500) - (rad * 500))
        t.setheading(0)
        t.pendown()
        t.circle(rad * 500)
        t.penup()


def performChecks(tileData:list, obstacles:list) -> list:
    '''Check if any of the obstacles are too close to any of the walls of the tiles'''
    #Scale factor in use
    scale = 0.4
    #Calculate scaled offset
    offset = 0.2 * scale

    allWalls = []
    scaledWalls = []
    #Iterate through the tiles
    for tile in tileData:
        #Get the walls for this tile
        walls = getWallsFromTilePosition(tile[0], tile[1][0], tile[1][1], scale)
        #Add walls to list
        for w in walls:
            allWalls.append(w)
            
    allowed = []
    #Iterate through the obstacles
    for obstacle in obstacles:
        #Calculate the radius and add the offset
        rad = dimensionsToCircle(obstacle[1]) + offset
        #Determine if that obstacle is correctly placed
        allow = checkManyIntersect(obstacle[0], rad, allWalls)
        allowed.append(allow)

    #Used for debugging purposes only, useful if supervisor is removing or leaving obstacles incorrectly
    #drawLayout(allWalls, obstacles, offset)
    
    #List of booleans indicating if the obstacles are correctly placed
    return allowed
