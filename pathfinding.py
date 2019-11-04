import numpy

def getSurrounding(pos,diagonal):
    surrounding = []
    surrounding.append([pos[0] + 1,pos[1]]) # right
    surrounding.append([pos[0] - 1,pos[1]]) # left
    surrounding.append([pos[0],pos[1] + 1]) # down
    surrounding.append([pos[0],pos[1] - 1]) # up
    if diagonal:
        surrounding.append([pos[0] + 1,pos[1] + 1]) # right - down
        surrounding.append([pos[0] - 1,pos[1] - 1]) # left - up
        surrounding.append([pos[0] + 1,pos[1] - 1]) # right - up
        surrounding.append([pos[0] - 1,pos[1] + 1]) # left - down
    return surrounding

def findPath(start,end,_map,diagonal=False):
    """
    findPath(startpoint, endpoint, map)\n
    \n
    startpoint -> array with len 2, representing start position on map\n
    endpoint -> array with len 2, representing start position on map\n
    diagonal -> boolean, default false, switching between including diagonals in pathfinding or not.\n
    \n
    uses a floodfill algorithm to find the shortest between two points on a two-dimensional array.\n
    map is used as the input matrix, representing "walkable" and "unwalkable" areas. Each field with\n
    a value bigger than zero will be handled as "unwalkable" and will not be part of the returning path.\n
    \n
    The output will be a 2d-array, but each index is a position, representing the path to the goal.\n
    The start position will NOT be included in the path, but the end position will be.\n
    """

    SIZES = numpy.shape(_map)
    max_i = SIZES[0] * SIZES[1]

    filledMap = numpy.zeros(SIZES) # initialize map with zeroes
    newPoints = [start] # add the start point as init point
    iteration = 0 # set the iteration to zero
    filledMap[start[1],start[0]] = -1
    while newPoints:
        for point in newPoints[::-1]: # iterate through points
            filledMap[point[1],point[0]] = iteration # marking athe current point with the current iteration
            for newp in getSurrounding(point,diagonal): # add all adjacent positions
                newPoints.append(newp)
            newPoints.remove(point) # remove this point from list (is done)#

        for point in newPoints[::-1]: # check for invalid points

            if not(point[0] in range(SIZES[0]) and point[1] in range(SIZES[1])): # if point is out of boundaries, remove it.
                newPoints.remove(point)
                continue

            if _map[point[1],point[0]] != 0: # if value of point on _map is not equal to 0 (=obstacle), remove it.
                filledMap[point[1],point[0]] = max_i
                newPoints.remove(point)
                continue
            
            if filledMap[point[1],point[0]] != 0 or point == start: # if point is already marked on filledMap, remove it.
                newPoints.remove(point)
                continue

        iteration += 1 # next iteration, increase counter
    
    print(filledMap)

    # find the way back to the start pos
    iteration = filledMap[end[1],end[0]]
    print(iteration)
    path = [end] # add the last point (starting point) to path (path will be reversed at the end)
    actPoint = end # set the current point to end

    while True:

        for newp in getSurrounding(actPoint,diagonal):
            if not(newp[0] in range(SIZES[0]) and newp[1] in range(SIZES[1])): # if point is out of boundaries, remove it.
                continue

            if filledMap[newp[1],newp[0]] < iteration: # otherwise, if point is marked with index lower than current iteration...
                actPoint = newp # ...replace current point with new,...
                path.append(actPoint) # ...save new point to path...
                break # and break. I only want to get the first point that has a lower index.

        iteration -= 1 # decrease the index
        if iteration < 0: # if the index is lower than zero now, the start point is reached and the algorithm will exit.
            break
    print(path)
    path.pop() # remove the last item, which is the start position. We don't want to have that in the path
    return path[::-1] # returning the reversed path to get from "end --> start" to "start --> end"

test_map = numpy.array([
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0],
    [1,1,1,0,0,0,0,1,1,1],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0],
])
start = [5,5]
end = [4,1]

print(findPath(start,end,test_map))