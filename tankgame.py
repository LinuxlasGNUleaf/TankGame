"""
TankGame
a game by JaWs
"""
import pygame
import math
from random import randint
import os
import numpy as np
from time import time, sleep
import threading

# ============================>> CONFIG <<============================

# basic video settings
WIDTH = 500
HEIGHT = 500
DEBUG = True

# game settings

# bullets
SHELLCOLLIDE = True
BULLET_COOLDOWN = 500
BULLET_DMG = 20
BULLET_VEL = 5

# obstacles
BORDER = 10
SIZE_X = 10
SIZE_Y = 10

# player and AI
TANK_VEL = 1
AI_TURN_VEL = 1
HP_TANK = 100

# advanced pathfinding settings
AI_PATH_FINDING_COOLDOWN = 1
# ====================================================================
SIZES = np.array([SIZE_X, SIZE_Y])
SCREEN = np.array([WIDTH, HEIGHT])
GAPS = np.divide(SCREEN, SIZES).astype("int32")

#Loading images
bg = pygame.image.load("bg.jpg")
tank1 = [pygame.image.load("tank1.png"), pygame.image.load("tank2.png")]
tank2 = [pygame.image.load("tank3.png"), pygame.image.load("tank4.png")]
bullet = pygame.image.load("bullet.png")
rock = pygame.image.load("rock.png")

def debug(string):
    """
    printing message when debug is turned on.
    """
    if DEBUG:
        print(string)

def uid_create(uidlen):
    """
    create a UID with a certain length.
    """
    uid = ""
    for _ in range(uidlen):
        uid += str(randint(0, 9))
    return uid

def sin_tan_for_Angle(angle, rad):
    rad = math.radians(angle)
    res = np.zeros(2)
    res[0] = math.sin(rad)
    res[1] = math.cos(rad)
    res = np.multiply(res, rad)
    return res

def drawDebug(pos, angle, win):
    res = sin_tan_for_Angle(angle, 50)
    pygame.draw.line(win, (0, 255, 0), (pos[0]-res[0], pos[1]), (pos[0]-res[0], pos[1]-res[1]))
    pygame.draw.line(win, (0, 255, 255), pos, (pos[0]-res[0], pos[1]))
    pygame.draw.line(win, (255, 0, 255), pos, (pos[0]-res[0], pos[1]-res[1]))

def constrain(x, min_, max_):
    return min(max(x, min_), max_)

def mapValue(value, inMin, inMax, outMin, outMax):
    value = constrain(value, inMin, inMax)
    #inRange = max(inMax - inMin,1)
    inRange = inMax - inMin
    outRange = outMax - outMin
    valueScaled = float(value - inMin) / float(inRange)
    return outMin + (valueScaled * outRange)

def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def getSurrounding(pos, diagonal):
    surrounding = []
    surrounding.append([pos[0] + 1, pos[1]]) # right
    surrounding.append([pos[0] - 1, pos[1]]) # left
    surrounding.append([pos[0], pos[1] + 1]) # down
    surrounding.append([pos[0], pos[1] - 1]) # up
    if diagonal:
        surrounding.append([pos[0] + 1, pos[1] + 1]) # right - down
        surrounding.append([pos[0] - 1, pos[1] - 1]) # left - up
        surrounding.append([pos[0] + 1, pos[1] - 1]) # right - up
        surrounding.append([pos[0] - 1, pos[1] + 1]) # left - down
    return surrounding

class AIPathFinder(threading.Thread):
    def __init__(self, _map, AI):
        self.map = _map
        self.AI = AI
        super.__init__(self)

    def run(start, end, diagonal=False):
        """
        run(startpoint, endpoint, map)\n
        \n
        startpoint -> array with len 2, representing start position on map\n
        endpoint -> array with len 2, representing start position on map\n
        diagonal -> boolean, default false, switching between including diagonals in
        pathfinding or not.\n\n
        it uses a floodfill algorithm to find the shortest between two points\n
        on a two-dimensional array. map is used as the input matrix, representing\n
        "walkable" and "unwalkable" areas. Each field with a value bigger than zero\n
        will be handled as "unwalkable" and will not be part of the returning path.\n\n
        The output will be a 2d-array, but each index is a position, representing the\n
        path to the goal.The start position will NOT be included in the path, but the\n
        end position will be.\n
        """

        map_size = np.shape(self.map)
        max_i = map_size[0] * map_size[1]

        # initialize map with zeroes
        filledMap = np.zeros(map_size)
        # add the start point as init point
        newPoints = [start]
        # set the iteration to zero
        iteration = 0

        filledMap[start[1], start[0]] = -1
        while newPoints:
            # iterate through points
            for point in newPoints[::-1]:
                # marking the current point with the current iteration
                filledMap[point[1], point[0]] = iteration
                # add all adjacent positions
                for newp in getSurrounding(point, diagonal):
                    newPoints.append(newp)
                # remove this point from list (is done)
                newPoints.remove(point)

            # check for invalid points
            for point in newPoints[::-1]:

                # if point is out of boundaries, remove it.
                if not(point[0] in range(map_size[0]) and point[1] in range(map_size[1])):
                    newPoints.remove(point)
                    continue

                # if value of point on self.map is not equal to 0 (=obstacle), remove it.
                if self.map[point[1], point[0]] != 0:
                    filledMap[point[1], point[0]] = max_i
                    newPoints.remove(point)
                    continue

                # if point is already marked on filledMap, remove it.
                if filledMap[point[1], point[0]] != 0 or np.array_equal(point, start):
                    newPoints.remove(point)
                    continue

            # next iteration, increase counter
            iteration += 1

        # find the way back to the start pos
        iteration = filledMap[end[1], end[0]]
        # add the last point (starting point) to path (path will be reversed at the end)
        path = [end]
        # set the current point to end
        actPoint = end

        while iteration >= 0:

            for newp in getSurrounding(actPoint, diagonal):
                # if point is out of boundaries, remove it.
                if not(newp[0] in range(map_size[0]) and newp[1] in range(map_size[1])):
                    continue

                # otherwise, if point is marked with index lower than current iteration...
                if filledMap[newp[1], newp[0]] < iteration:
                    # ...replace current point with new,...
                    actPoint = newp
                    # ...save new point to path...
                    path.append(actPoint)
                    # and break. I only want to get the first point that has a lower index.
                    break

            iteration -= 1 # decrease the index

        # remove the last item, which is the start position. We don't want to have that in the path
        path.pop()
        # returning the reversed path to get from "end --> start" to "start --> end"
        self.AI.path = path[::-1]


# class Representer():
#     def __init__(self,obj,hitbox):
#         self.obj = obj
#         self.hitbox = hitbox

#     def update(self):
#         self.hitbox = self.obj.coll_rect


class Tank():
    def __init__(self, imgset, coords, name, uid):
        self.pos = np.array(coords)
        self.angle = 0.0
        self.orig = imgset
        self.step = 2
        self.img = self.orig[0]
        self.coll_rect = self.img.get_rect()
        self.coll_rect.width /= 2
        self.coll_rect.height /= 2
        self.coll_rect.center = self.img.get_rect().center
        self.img_len = len(imgset)
        self.count = 0
        self.HP = HP_TANK
        self.name = name
        self.slider = Slider(self, 5, 30, (0, 100), 40)
        self.slider.update(self.HP)
        self.rep = Representer(self, self.coll_rect)
        self.border = self.coll_rect.width//2
        self.DeleteFlag = False
        self.uid = uid
        self.bulletMgr = BulletManager(self)

    def draw(self, win):
        self.bulletMgr.drawBullets(win)

        num = int(self.count)%self.img_len
        self.img = pygame.transform.rotate(self.orig[num], self.angle)

        self.rect = self.img.get_rect()
        self.rect.center = self.pos

        win.blit(self.img, self.rect)
        self.slider.draw(win)

        if DEBUG:
            drawDebug(self.pos, self.angle, win)
            pygame.draw.rect(win, (255, 0, 0), self.coll_rect, 1)

    def move(self, keys, tanks, obstacles):
        self.repPos = np.divide(self.pos, GAPS).astype("int32")

        if self.HP > 0:
            self.bulletMgr.moveBullets(tanks, obstacles)
        else:
            self.DeleteFlag = True
        self.slider.update(self.HP)
        self.updateCollideRect()
        self.bulletMgr.createBullets(keys)

    def updateCollideRect(self):
        self.coll_rect.center = self.pos

    def correctMovement(self, obstacles):
        for obstacle in obstacles:
            if self.coll_rect.colliderect(obstacle.coll_rect):
                diff = np.multiply(np.subtract((obstacle.coll_rect.center),
                                               (self.coll_rect.center)), -1)
                diff = normalize(diff)
                self.pos = np.add(diff, self.pos)

        self.pos[0] = constrain(self.pos[0], self.border, WIDTH-self.border)
        self.pos[1] = constrain(self.pos[1], self.border, HEIGHT-self.border)


class Player(Tank):
    def __init__(self, imgset, coords, name, keyset, rep_matrix, uid):
        super().__init__(imgset, coords, name, uid)
        self.keyset = keyset
        self.bulletMgr.setPlayer(keyset[4])

    def move(self, keys, tanks, obstacles):
        if keys[self.keyset[0]] or keys[self.keyset[1]]:  #moving
            change = sin_tan_for_Angle(self.angle, TANK_VEL)
            if keys[self.keyset[0]]:
                self.pos = np.subtract(self.pos, change)
                self.count += 0.05

            elif keys[self.keyset[1]]:
                self.pos = np.add(self.pos, change)
                self.count += 0.05
            self.correctMovement(obstacles)

        if keys[self.keyset[2]]: #left
            self.angle += self.step
            self.count += 0.03

        elif keys[self.keyset[3]]: #right
            self.angle -= self.step
            self.count += 0.03

        super().move(keys, tanks, obstacles)


class AI(Tank):
    def __init__(self, imgset, coords, name, rep_matrix, uid):
        super().__init__(imgset, coords, name, uid)
        self.pathfinder = AIPathFinder(rep_matrix)
        self.rep_matrix = rep_matrix
        self.path = []
        self.updatePathFlag = False
        self.bulletMgr.setAI()
        self.repPos = []

    def move(self, keys, tanks, obstacles):

        if self.updatePathFlag:
            self.path = findPath(self.repPos, tanks[0].obj.repPos, self.rep_matrix)
            self.updatePathFlag = False

        # self.pos = np.subtract(self.pos,sin_tan_for_Angle(self.angle,TANK_VEL))
        self.correctMovement(obstacles)
        super().move(0, tanks, obstacles)


class Bullet():
    def __init__(self, angle, coords, img):
        self.img = pygame.transform.rotate(img, angle)
        self.pos = np.array(coords)
        self.rect = img.get_rect()
        self.angle = angle
        self.rect.width /= 2
        self.rect.height /= 2
        self.rect.center = self.pos

    def move(self):
        change = sin_tan_for_Angle(self.angle, BULLET_VEL)
        self.pos = np.subtract(self.pos, change)

    def draw(self, win):
        self.rect.center = self.pos
        win.blit(self.img, self.rect)
        if DEBUG:
            pygame.draw.rect(win, (255, 0, 255), self.rect, 1)


class BulletManager():
    def __init__(self, player):
        self.player = player
        self.bullets = []
        self.alt = pygame.time.get_ticks()
        self.dmg = BULLET_DMG
        self.setup = False

    def setAI(self):
        if not self.setup:
            self.setup = True
            self.type = "AI"
        else:
            raise Warning("multiple setup of Bulletmgr is not valid")

    def setPlayer(self, key):
        if not self.setup:
            self.setup = True
            self.type = "Player"
            self.key = key
        else:
            raise Warning("multiple setup of Bulletmgr is not valid")

    def createBullets(self, keys):
        time = pygame.time.get_ticks()
        #(if player and Key pressed) or if AI
        if (((self.type == "Player") and keys[self.key]) or (self.type == "AI")):
            if time-BULLET_COOLDOWN > self.alt:
                angle = self.player.angle
                change = returnXYforAngle(angle, -45)
                newpos = np.add(self.player.pos, change)
                newbullet = Bullet(angle, newpos, bullet)
                self.bullets.append(newbullet)
                self.alt = time

    def moveBullets(self, reps, obstacles):
        for bullet in self.bullets[::-1]:
            bullet.move()

            #checking for on-screen
            if not (int(bullet.pos[0]) in range(0, SCREEN[0]) and
                    int(bullet.pos[1]) in range(0, SCREEN[1])):
                self.bullets.remove(bullet)
                continue

            #checking for collision with another tank
            exist = True
            for rep in reps:
                tank = rep.obj
                if bullet.rect.colliderect(rep.hitbox) and tank != self.player:
                    tank.HP -= self.dmg
                    exist = False

            if not exist:
                self.bullets.remove(bullet)
                continue

            #checking for collision with obstacles
            if SHELLCOLLIDE:
                for obstacle in obstacles:
                    if bullet.rect.colliderect(obstacle.shell_rect):
                        self.bullets.remove(bullet)
                        break

    def drawBullets(self, win):
        for bullet in self.bullets:
            bullet.draw(win)


class GameManager():
    def __init__(self):
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tank Game")
        pygame.display.set_icon(tank1[0])
        self.font = pygame.font.Font("Perfect_DOS_VGA_437.ttf", SCREEN[0]//15)
        self.debug_font = pygame.font.Font("Perfect_DOS_VGA_437.ttf", SCREEN[0]//30)

        self.obstMgr = ObstacleManager(rock)
        self.obstMgr.build()

        keyset = [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, pygame.K_SPACE]

        self.tanks = []
        self.AIs = []

        player = Player(tank1, (400, 400), "Player", keyset, self.obstMgr.repMatrix, uid_create(10))
        self.tanks.append(player.rep)
        ai = AI(tank2, (100, 100), "AI", self.obstMgr.repMatrix, uid_create(10))
        self.tanks.append(ai.rep)
        self.AIs.append(ai.rep)

    def redrawGameWindow(self):
        self.win.blit(bg, (0, 0))
        if DEBUG:
            self.drawDebugText()
        for tank in self.tanks:
            tank.obj.draw(self.win)
        self.obstMgr.draw(self.win)
        pygame.display.update()

    def main(self):
        pf_time = time()
        clock = pygame.time.Clock()
        run = True
        winner = 0
        while run:
            clock.tick(240)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

            keys = pygame.key.get_pressed()

            for tank in self.tanks[::1]:
                custom = self.tanks.copy()

                for rep in custom[::1]:
                    if rep.obj.uid == tank.obj.uid:
                        custom.remove(rep)

                tank.obj.move(keys, custom, self.obstMgr.obstacles)
                if tank.obj.DeleteFlag:
                    self.tanks.remove(tank)

            if len(self.tanks) <= 1:
                run = False
                if len(self.tanks) == 1:
                    winner = self.tanks[0].obj

            if (time() - pf_time) > AI_PATH_FINDING_COOLDOWN:
                for ai in self.AIs:
                    ai.obj.updatePathFlag = True
                pf_time = time()

            self.redrawGameWindow()

        if winner:
            text = self.font.render("The {} won the game!".format(winner.name), True, (255, 0, 0))
            pos = (SCREEN[0]//20, SCREEN[1]*2//5)
            self.win.blit(text, pos)
            pygame.display.update()
            sleep(2)
        pygame.quit()

    def drawDebugText(self):
        bulletCount = 0
        Player_HP = 0
        AI_HP = 0
        for tank in self.tanks:
            bulletCount += len(tank.obj.bulletMgr.bullets)
            if tank.obj.name == "Player":
                Player_HP = tank.obj.pos.astype("int32")
            if tank.obj.name == "AI":
                AI_HP = tank.obj.pos.astype("int32")

        obstCount = len(self.obstMgr.obstacles)
        obst_Size = self.obstMgr.repMatrix.shape

        text1 = "bullets: {} obstacles: {} obstacle_matrix: {} "
        text1.format(bulletCount, obstCount, obst_Size)
        text2 = "HP AI: {} HP Pl: {}"
        text2.format(AI_HP, Player_HP)
        debug_text1 = self.debug_font.render(text1, True, (255, 0, 0))
        debug_text2 = self.debug_font.render(text2, True, (255, 0, 0))
        pos = np.array([5, HEIGHT*(9/10)])
        pos1 = pos.copy()
        pos2 = pos.copy()
        pos2[1] += self.debug_font.get_height()*1.5
        self.win.blit(debug_text1, pos1)
        self.win.blit(debug_text2, pos2)


class Slider():
    def __init__(self, obj, height, max_width, in_range, gap):
        self.obj = obj
        self.height = height
        self.max_width = max_width
        self.in_min, self.in_max = in_range
        self.gap = gap
        self.val = self.in_max

    def update(self, inputVal):
        self.val = mapValue(inputVal, self.in_min, self.in_max, 0, self.max_width)
        r = int(mapValue(inputVal, self.in_min, self.in_max, 255, 0))
        g = int(mapValue(inputVal, self.in_min, self.in_max, 0, 255))
        self.color = pygame.Color(r, g, 0)

    def draw(self, win):
        x, y = self.obj.rect.center
        y += self.gap - self.height
        x -= self.val/2
        rect = pygame.Rect(x, y, self.val, self.height)
        rect2 = pygame.Rect(x-2, y+5, self.val+4, self.height-10)
        pygame.draw.rect(win, pygame.Color(100, 100, 100), rect2)
        pygame.draw.rect(win, self.color, rect)


class Obstacle():
    def __init__(self, img, pos, sizes):
        self.coll_rect = pygame.Rect(pos[0], pos[1], sizes[0], sizes[1])
        self.shell_rect = self.coll_rect.copy()
        self.img = pygame.transform.rotate(img, randint(0, 359))
        self.img_pos = np.subtract(pos, np.divide(sizes, 3))
        self.shell_rect.width /= 2
        self.shell_rect.height /= 2
        self.shell_rect.center = self.coll_rect.center

    def draw(self, win):
        win.blit(self.img, self.img_pos)
        if DEBUG:
            pygame.draw.rect(win, (0, 255, 255), self.coll_rect, 1)
            pygame.draw.rect(win, (255, 0, 255), self.shell_rect, 1)


class ObstacleManager():
    def __init__(self, obst_img):
        self.obstacles = []
        self.levels = []
        self.obstImg = obst_img
        self.repMatrix = np.zeros(SIZES)

        #get all .lvl files
        for _, _, f in os.walk("../"):
            for file in f:
                if file.endswith(".lvl"):
                    print(file)
                    self.levels.append(file)

        #level validation
        for lvl in self.levels[::1]:
            Valid = True

            #retrieving level data
            lvl_file = open(lvl)
            lines = lvl_file.readlines()
            lvl_file.close()

            if len(lines) != SIZES[1]: #number of lines not matching
                print(("Error 0 while reading {}: Err0: number of lines invalid! \n"+
                       "Found {} lines instead of {}!\n").format(lvl, len(lines), SIZES[1]))
                Valid = False
            else:
                for line in lines:
                    line = line.replace("\n", "")
                    if len(line) != SIZES[0]: #number of columns not matching
                        print(("Error 1 while reading {}: Err1: length of line {} invalid! \n"+
                               "Length of line was {} chars instead of {} !\n")
                              .format(lvl, lines.index(line)+"\n", len(line), SIZES[1]))
                        Valid = False

            if not Valid:
                self.levels[::1].remove(lvl)

        #checking for a valid level
        if len(self.levels) < 1:
            print("No valid level file found! Exiting...")
            raise SystemExit()


        self.level = self.levels[randint(0, len(self.levels)-1)]
        print("Level chosen: {}".format(self.level))

    def build(self):
        level_file = open(self.level)
        pos = np.zeros(2, dtype=int)
        grid = np.zeros(2, dtype=int)
        for line in level_file:
            pos[0] = 0
            grid[0] = 0
            for char in line:
                if char == "X":
                    self.obstacles.append(Obstacle(self.obstImg, pos, GAPS))
                    self.repMatrix[grid[1], grid[0]] = 1
                pos[0] += GAPS[0]
                grid[0] += 1
            pos[1] += GAPS[1]
            grid[1] += 1

    def draw(self, win):
        for obstacle in self.obstacles:
            obstacle.draw(win)


if __name__ == "__main__":
    gameMgr = GameManager()
    gameMgr.main()
