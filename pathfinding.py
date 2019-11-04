import numpy
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

SIZES = [10,10]
max_i = SIZES[0] * SIZES[1]
def paintMap(start, _map):
    filledMap = numpy.zeros(SIZES)
    newPoints = []
    newPoints.append(start)
    iteration = 0
    filledMap[start[1],start[0]] = -1
    while newPoints:
        for point in newPoints[::-1]:
            filledMap[point[1],point[0]] = iteration
            temp = getSurrounding(point)
            for newp in temp:
                newPoints.append(newp)

        for point in newPoints[::-1]:

            if not(point[0] in range(SIZES[0]) and point[1] in range(SIZES[1])): # if point is out of boundaries, remove it.
                newPoints.remove(point)
                # print("removed for out of boundaries: {}".format(point))
                continue

            if _map[point[1],point[0]] != 0: # if value of point on _map is not equal to 0, remove it.
                filledMap[point[1],point[0]] = max_i
                newPoints.remove(point)
                # print("removed for being an obstacle: {}".format(point))
                continue
            
            if filledMap[point[1],point[0]] != 0 or point == start: # if point is already indexed on filledMap, remove it.
                newPoints.remove(point)
                # print("removed for already filled: {}".format(point))
                continue
        iteration += 1
    
    return filledMap

def getSurrounding(pos):
    surrounding = []
    surrounding.append([pos[0] + 1,pos[1]]) # right
    surrounding.append([pos[0] - 1,pos[1]]) # left
    surrounding.append([pos[0],pos[1] + 1]) # down
    surrounding.append([pos[0],pos[1] - 1]) # up
    surrounding.append([pos[0] + 1,pos[1] + 1]) # right - down
    surrounding.append([pos[0] - 1,pos[1] - 1]) # left - up
    surrounding.append([pos[0] + 1,pos[1] - 1]) # right - up
    surrounding.append([pos[0] - 1,pos[1] + 1]) # left - down
    return surrounding

def getPath(end,_map):

    iteration = _map[end[1],end[0]]
    path = [end]
    actPoint = end

    while True:

        for newp in getSurrounding(actPoint):
            if not(newp[0] in range(SIZES[0]) and newp[1] in range(SIZES[1])):
                continue

            if _map[newp[1],newp[0]] < iteration:
                actPoint = newp # replace with new
                path.append(actPoint) # save to path
                break

        iteration -= 1
        if iteration < 0:
            break
    
    return path

map = numpy.array([
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

filledMap = paintMap(start,map)
path = getPath(end,filledMap)
print(path[::-1])