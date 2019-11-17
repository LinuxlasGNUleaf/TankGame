"""
TankGame
a game by JaWs
"""

# std imports
import math
from random import randint
import os
from time import sleep, time
import threading

# extra imports
import numpy as np
import pygame

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
AI_PATH_FINDING_COOLDOWN = 0.5
DIAGONAL = False

# fonts
STD_FONT = "Perfect_DOS_VGA_437.ttf"
# ====================================================================
SIZES = np.array([SIZE_X, SIZE_Y])
SCREEN = np.array([WIDTH, HEIGHT])
GAPS = np.divide(SCREEN, SIZES).astype("int32")

#Loading images
BACKDROP = pygame.image.load("bg.jpg")
TANK_1 = [pygame.image.load("tank1.png"), pygame.image.load("tank2.png")]
TANK_2 = [pygame.image.load("tank3.png"), pygame.image.load("tank4.png")]
BULLET = pygame.image.load("bullet.png")
ROCK = pygame.image.load("rock.png")

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

def sin_cos_for_angle(angle, vel):
    """
    returns a array of sin(x) and cos(x) of a given angle.\n
    multiplies these values with the radius.
    """
    rad = math.radians(angle)
    res = np.zeros(2)
    res[0] = math.sin(rad)
    res[1] = math.cos(rad)
    res = np.multiply(res, vel)
    return res

def draw_debug(pos, angle, win):
    """
    draws a triangle (symbolizing the sin/cos\n
    of the current angle) on the given screen.
    """
    res = sin_cos_for_angle(angle, 50)
    pygame.draw.line(win, (0, 255, 0), (pos[0]-res[0], pos[1]), (pos[0]-res[0], pos[1]-res[1]))
    pygame.draw.line(win, (0, 255, 255), pos, (pos[0]-res[0], pos[1]))
    pygame.draw.line(win, (255, 0, 255), pos, (pos[0]-res[0], pos[1]-res[1]))

def constrain(val, min_, max_):
    """
    constrains a value into a given interval.
    """
    return min(max(val, min_), max_)

def mapvalue(value, in_min, in_max, out_min, out_max):
    """
    maps the input value (in the given input interval)\n
    to the given output interval
    """
    value = constrain(value, in_min, in_max)
    in_range = in_max - in_min
    out_range = out_max - out_min
    value_scaled = float(value - in_min) / float(in_range)
    return out_min + (value_scaled * out_range)

def normalize(vec):
    """
    shrinks the vector to the length of 1
    """
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm

def get_surrounding(pos, map_size):
    """
    returns all appending positions of the position.\n
    if diagonal is given, it will return the diagonal\n
    appending blocks as well.
    """
    surrounding = [[pos[0] + 1, pos[1]], # right
                   [pos[0] - 1, pos[1]], # left
                   [pos[0], pos[1] + 1], # down
                   [pos[0], pos[1] - 1]] # up

    # if point is out of boundaries, remove it.
    for point in surrounding[::-1]:
        if not(point[0] in range(map_size[0]) and point[1] in range(map_size[1])):
            surrounding.remove(point)
    return surrounding

def get_pos_from_rep(pos):
    """
    converts representer position to normal position
    """
    pos1 = np.multiply(pos, GAPS)
    pos2 = np.add(pos, [1, 1])
    pos2 = np.multiply(pos2, GAPS)
    pos3 = np.add(pos1, pos2)
    pos3 = np.divide(pos3, 2)
    return pos3

def val_map(_map, pos):
    """
    returns value on y-x map
    """
    return _map[pos[1], pos[0]]

class AIPathFinder(threading.Thread):
    """
    AIPathFinder(ai_instance)\n
    \n
    AI object requirements:\n
    - a rep_matrix which is the map for pathfinding\n
    - a rep_pos attribute (1d array with len 2 ==> 2d-pos)\n
    - a target attribute with a rep_pos attr (same requirements as above)\n
    - a new_path attribute, to write path to\n
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
    def __init__(self, ai_instance):
        threading.Thread.__init__(self)
        self.ai_instance = ai_instance
        self.is_running = True
        self.map = self.ai_instance.rep_matrix
        self.map_size = np.shape(self.map)
        self.max_i = self.map_size[0] * self.map_size[1]
        self.startpos = []
        self.goal = []
        self.flood_map = []
        self.path = []

    def run(self):
        while self.is_running:

            old_time = time()
            self.floodfill()

            print("[{}]: elapsed while floodfilling: {}s"
                  .format(self.ai_instance.name, time()-old_time))

            old_time2 = time()
            self.calc_path()

            print("[{}]elapsed while pathfinding: {}s"
                  .format(self.ai_instance.name, time()-old_time2))
            print("[{}]total elapsed time: {}s".format(self.ai_instance.name, time()-old_time))

            sleep(AI_PATH_FINDING_COOLDOWN)

        print("stopped path-finding thread for "+self.ai_instance.name)

    # def find_path(self):
    #     """
    #     finds path
    #     """
    #     target = self.ai_instance.target

    #     if not target:
    #         return
    #     endpos = target.rep_pos
    #     startpos = self.ai_instance.rep_pos

    #     # initialize map with zeroes
    #     filled_map = np.ndarray(self.map_size)
    #     filled_map.fill(-1)
    #     # add the start point as init point
    #     new_points = [startpos]
    #     # set the iteration to zero
    #     iteration = 0

    #     filled_map[startpos[1], startpos[0]] = -1
    #     end_reached = False
    #     while new_points and not end_reached:
    #         print(len(new_points))
    #         # iterate through points
    #         for point in new_points[::-1]:
    #             # marking the current point with the current iteration
    #             filled_map[point[1], point[0]] = iteration
    #             # add all adjacent positions
    #             for newp in get_surrounding(point, self.map_size):
    #                 new_points.append(newp)
    #             # remove this point from list (is done)
    #             new_points.remove(point)

    #         # check for invalid points and endposition
    #         for point in new_points[::-1]:

    #             # if value of point on _map is not equal to 0 (=obstacle), remove it.
    #             if self.map[point[1], point[0]] != 0:
    #                 filled_map[point[1], point[0]] = self.max_i
    #                 new_points.remove(point)
    #                 continue

    #             # if point is already marked on filled_map, remove it.
    #             if filled_map[point[1], point[0]] != 0 or np.array_equal(point, startpos):
    #                 new_points.remove(point)
    #                 continue

    #             if np.array_equal(point, endpos):
    #                 # marking the current point with the current iteration
    #                 filled_map[point[1], point[0]] = iteration
    #                 end_reached = True
    #                 continue

    #         # next iteration, increase counter
    #         iteration += 1

    #     # find the way back to the start pos
    #     iteration = filled_map[endpos[1], endpos[0]]
    #     # add the last point (starting point) to path (path will be reversed at the end)
    #     path = [endpos]
    #     # set the current point to end
    #     act_point = endpos

    #     while iteration >= 0:

    #         for newp in get_surrounding(act_point, self.map_size):
    #             # otherwise, if point is marked with index lower than current iteration...
    #             if filled_map[newp[1], newp[0]] < iteration and filled_map[newp[1], newp[0]] >= 0:
    #                 # ...replace current point with new,...
    #                 act_point = newp
    #                 # ...save new point to path...
    #                 path.append(act_point)
    #                 # and break. I only want to get the first point that has a lower index.
    #                 break

    #         iteration -= 1 # decrease the index

    #     # remove the last item, which is the startpos position.
    #     # We don't want to have that in the path
    #     path.pop()
    #     # returning the reversed path to get from
    #     # "self.endpos --> self.startpos" to "startpos --> self.endpos"
    #     new_path = []
    #     for entry in path:
    #         new_path.append(get_pos_from_rep(entry))
    #     self.ai_instance.new_path = new_path[::-1]

    def floodfill(self):
        """
        floodfill
        """
        # clean the flood map. If the target is not valid, the calcPath func will recognise it
        # because the flood map is empty

        self.flood_map = np.zeros(self.map_size) # 0 means: unindexed

        if not self.ai_instance.target:
            return

        self.goal = self.ai_instance.target.rep_pos
        self.startpos = self.ai_instance.rep_pos

        points = [self.startpos]
        goal_reached = False
        indexed = []
        index = 1
        while points and not goal_reached:
            # print(len(points))
            for point in points[::-1]:

                for new_point in get_surrounding(point, self.map_size):

                    if val_map(self.map, new_point) == 0:

                        if val_map(self.flood_map, new_point) == 0:

                            if not np.array_equal(new_point, self.startpos):

                                if not new_point in indexed:

                                    if np.array_equal(new_point, self.goal):
                                        print("goal reached!")
                                        goal_reached = True
                                        self.flood_map[new_point[1], new_point[0]] = index+1
                                        break

                                    points.append(new_point)
                                    indexed.append(new_point)

                self.flood_map[point[1], point[0]] = index
                points.remove(point)
            index += 1
        print(self.flood_map)

    def calc_path(self):
        """
        calculates the path with the given floodMap
        """
        # if flood map is empty, which means the target val of the AI is not set, exit.
        if not self.flood_map.any():
            return

        act_pos = self.goal
        act_index = val_map(self.flood_map, act_pos)
        new_path = [self.goal]
        while act_index > 1:
            for new_point in get_surrounding(act_pos, self.map_size):
                if (val_map(self.flood_map, new_point) < act_index
                        and val_map(self.flood_map, new_point) > 0):

                    act_pos = new_point
                    act_index -= 1
                    new_path.append(act_pos)
                    break
        
        # proccessing inputs
        self.path = []
        for entry in new_path:
            self.path.append(get_pos_from_rep(entry))
        self.path = self.path[::-1]

class Tank():
    """
    super class for AI and Player. \n
    has all the basic functionalities the tanks have.
    """
    def __init__(self, imgset, coords, name, uid):
        self.pos = np.array(coords)
        self.angle = 0.0
        self.orig = imgset
        self.step = 2
        self.img = self.orig[0]
        self.rect = self.img.get_rect()
        self.hitbox = self.img.get_rect()
        self.hitbox.width /= 2
        self.hitbox.height /= 2
        self.hitbox.center = self.img.get_rect().center
        self.img_len = len(imgset)
        self.count = 0
        self.health = HP_TANK
        self.name = name
        self.slider = Slider(self, 5, 30, (0, 100), 40)
        self.slider.update(self.health)
        self.border = self.hitbox.width//2
        self.delete_flag = False
        self.uid = uid
        self.bullet_mgr = BulletManager(self)
        self.rep_pos = np.divide(self.pos, GAPS).astype("int32")

    def draw(self, win):
        """
        draw the tank, its shells, slider (and debug).
        """
        self.bullet_mgr.draw_bullets(win)

        num = int(self.count)%self.img_len
        self.img = pygame.transform.rotate(self.orig[num], self.angle)

        self.rect = self.img.get_rect()
        self.rect.center = self.pos

        win.blit(self.img, self.rect)
        self.slider.draw(win)

        if DEBUG:
            draw_debug(self.pos, self.angle, win)
            pygame.draw.rect(win, (255, 0, 0), self.hitbox, 1)

    def move(self, keys, tanks, obstacles):
        """
        moves the tank, it's shells, slider and updates collideRect.
        """
        self.rep_pos = np.divide(self.pos, GAPS).astype("int32")

        if self.health > 0:
            self.bullet_mgr.move_bullets(tanks, obstacles)
        else:
            self.delete_flag = True
        self.slider.update(self.health)
        self.hitbox.center = self.pos
        self.bullet_mgr.create_bullets(keys)
        self.correct_movement(obstacles)

    def correct_movement(self, obstacles):
        """
        checks whether the tanks is inside any obstacle, and uses vectors to move\n
        it into the coorect direction out of the obstacle.
        """
        for obstacle in obstacles:
            if self.hitbox.colliderect(obstacle.hitbox):
                diff = np.multiply(np.subtract((obstacle.hitbox.center),
                                               (self.hitbox.center)), -1)
                diff = normalize(diff)
                self.pos = np.add(diff, self.pos)

        self.pos[0] = constrain(self.pos[0], self.border, WIDTH-self.border)
        self.pos[1] = constrain(self.pos[1], self.border, HEIGHT-self.border)


class Player(Tank):
    """
    inherits from Tank superclass.\n
    has additionally a keyset to control it.
    """
    def __init__(self, imgset, coords, name, keyset, _, uid):
        super().__init__(imgset, coords, name, uid)
        self.keyset = keyset
        self.bullet_mgr.set_player(keyset[4])

    def move(self, keys, tanks, obstacles):
        if keys[self.keyset[0]] or keys[self.keyset[1]]:
            change = sin_cos_for_angle(self.angle, TANK_VEL)
            if keys[self.keyset[0]]:
                self.pos = np.subtract(self.pos, change)
                self.count += 0.05

            elif keys[self.keyset[1]]:
                self.pos = np.add(self.pos, change)
                self.count += 0.05
            self.correct_movement(obstacles)

        if keys[self.keyset[2]]: #left
            self.angle += self.step
            self.count += 0.03

        elif keys[self.keyset[3]]: #right
            self.angle -= self.step
            self.count += 0.03

        super().move(keys, tanks, obstacles)


class AI(Tank):
    """
    inherits from Tank superclass.\n
    has additionally a pathfinder.
    """
    def __init__(self, imgset, coords, name, rep_matrix, uid):
        super().__init__(imgset, coords, name, uid)
        self.rep_matrix = rep_matrix
        self.path = []
        self.bullet_mgr.set_ai()
        self.new_path = []
        self.target = 0
        self.thread = AIPathFinder(self,)
        self.thread.start()

    def move(self, keys, tanks, obstacles):
        if not tanks:
            return

        self.target = tanks[0]

        # get new path from pathfinding thread
        self.path = self.thread.path

        if self.path:
            diff = np.subtract(self.path[0], self.pos).astype("int32")
            if math.sqrt(diff[0]**2 + diff[1]**2) < math.sqrt((GAPS[0]/2)**2 + (GAPS[1]/2)**2):
                self.path.pop(0)
            else:
                self.angle = math.degrees(math.atan2(diff[1], -diff[0])) + 90
            self.pos = np.subtract(self.pos, sin_cos_for_angle(self.angle, TANK_VEL))
        super().move(0, tanks, obstacles)

    def draw(self, win):
        super().draw(win)
        if DEBUG:
            if len(self.path) > 1:
                maxl = len(self.path)-1
                i = 0
                for point in self.path:
                    rect = pygame.Rect(point[0]-10, point[1]-10, 20, 20)
                    col_val = mapvalue(i, 0, maxl, 0, 255)
                    pygame.draw.rect(win, (col_val, col_val, col_val), rect, 2)
                    i += 1
            elif self.path:
                rect = pygame.Rect(self.path[0][0]-10, self.path[0][1]-10, 20, 20)
                pygame.draw.rect(win, (255, 255, 255), rect, 2)


class Bullet():
    """
    Shell class. Instances are created by the BulletManager, which is controlled by\n
    the Ai / Player Object. They have a constant speed, angle and damage.
    """
    def __init__(self, angle, coords, img):
        self.img = pygame.transform.rotate(img, angle)
        self.pos = np.array(coords)
        self.rect = img.get_rect()
        self.angle = angle
        self.rect.width /= 2
        self.rect.height /= 2
        self.rect.center = self.pos

    def move(self):
        """
        move the bullet with its velocity in \n
        the direction it was spawned.
        """
        change = sin_cos_for_angle(self.angle, BULLET_VEL)
        self.pos = np.subtract(self.pos, change)

    def draw(self, win):
        """
        draw the bullet, if debug is on, draw hitbox, too.
        """
        self.rect.center = self.pos
        win.blit(self.img, self.rect)
        if DEBUG:
            pygame.draw.rect(win, (255, 0, 255), self.rect, 1)


class BulletManager():
    """
    belongs to a Tank Object. Has two modes: Player / AI\n
    controls the shells of a tank (moving /drawing)
    manages cooldown
    """
    def __init__(self, player):
        self.player = player
        self.bullets = []
        self.alt = pygame.time.get_ticks()
        self.dmg = BULLET_DMG
        self.setup = False
        self.type = ""
        self.key = 0

    def set_ai(self):
        """
        sets type of BulletManager to AI.\n
        The bullet manager will shot a bullet whenever\n
        possible instead of when the corresponding key is pressed. (player)
        """
        if not self.setup:
            self.setup = True
            self.type = "AI"
        else:
            raise Warning("multiple setup of Bulletmgr is not valid")

    def set_player(self, key):
        """
        sets type of BulletManager to AI.\n
        The bullet manager will shot a bullet whenever\n
        the corresponding key is pressed.\n
        """
        if not self.setup:
            self.setup = True
            self.type = "Player"
            self.key = key
        else:
            raise Warning("multiple setup of Bulletmgr is not valid")

    def create_bullets(self, keys):
        """
        creates a new bullet and appends it to the bullet list...\n
        ...when the cooldown has expired\n
        ...the corresponding key has been pressed (only player)\n
        """
        systime = pygame.time.get_ticks()
        #(if player and Key pressed) or if AI
        if (((self.type == "Player") and keys[self.key]) or (self.type == "AI")):
            if systime - BULLET_COOLDOWN > self.alt:
                angle = self.player.angle
                change = sin_cos_for_angle(angle, -45)
                newpos = np.add(self.player.pos, change)
                newbullet = Bullet(angle, newpos, BULLET)
                self.bullets.append(newbullet)
                self.alt = systime

    def move_bullets(self, tanks, obstacles):
        """
        calls the move() function for each bullet in its list.\n
        For more info see docstring of Bullet.move()
        """
        for bullet in self.bullets[::-1]:
            bullet.move()

            #checking for on-screen
            if not (int(bullet.pos[0]) in range(0, SCREEN[0]) and
                    int(bullet.pos[1]) in range(0, SCREEN[1])):
                self.bullets.remove(bullet)
                continue

            #checking for collision with another tank
            exist = True
            for tank in tanks:
                if bullet.rect.colliderect(tank.hitbox) and tank != self.player:
                    tank.health -= self.dmg
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

    def draw_bullets(self, win):
        """
        calls the draw() function for each bullet in its list.\n
        For more info see docstring of Bullet.draw()
        """
        for bullet in self.bullets:
            bullet.draw(win)


class GameManager():
    """
    handles the game itself. It calls the move, draw, etc.\n
    functions of the different instances and is responsible for\n
    init and end.
    """
    def __init__(self):
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tank Game")
        pygame.display.set_icon(TANK_1[0])
        self.font = pygame.font.Font(STD_FONT, SCREEN[0]//15)
        self.debug_font = pygame.font.Font(STD_FONT, SCREEN[0]//30)

        self.obst_mgr = ObstacleManager(ROCK)
        self.obst_mgr.build()

        keyset = [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, pygame.K_SPACE]

        self.tanks = []
        self.ais = []

        player = Player(TANK_1, (400, 400), "Player 1", keyset,
                        self.obst_mgr.rep_matrix, uid_create(10))
        self.tanks.append(player)

        ai_instance = AI(TANK_2, (100, 100), "AI 1", self.obst_mgr.rep_matrix, uid_create(10))
        self.tanks.append(ai_instance)
        self.ais.append(ai_instance)

    def redraw_game_window(self):
        """
        draws the different layers\n
        (background, tanks, obstacles, shells, debug)
        """
        self.win.blit(BACKDROP, (0, 0))
        if DEBUG:
            self.draw_debug_text()
        for tank in self.tanks:
            tank.draw(self.win)
        self.obst_mgr.draw(self.win)
        pygame.display.update()

    def main(self):
        """
        main loop of the game.
        """
        clock = pygame.time.Clock()
        run = True
        winner = 0
        try:
            while run:
                clock.tick(240)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        run = False

                keys = pygame.key.get_pressed()

                for tank in self.tanks[::1]:
                    custom = self.tanks.copy()

                    for ctank in custom[::1]:
                        if ctank.uid == tank.uid:
                            custom.remove(ctank)

                    tank.move(keys, custom, self.obst_mgr.obstacles)
                    if tank.delete_flag:
                        self.tanks.remove(tank)
                        if isinstance(tank, AI):
                            debug(tank.name +
                                  " was killed, removing it from list and stopping pathfinding.")
                            debug("sending kill signal to path-finding thread for "
                                  +tank.name+" ...")
                            tank.thread.is_running = False
                            self.ais.remove(tank)

                if len(self.tanks) <= 1:
                    run = False
                    if len(self.tanks) == 1:
                        winner = self.tanks[0]

                self.redraw_game_window()
        except KeyboardInterrupt:
            debug("Game interrupted by Keystroke (Ctrl + C)")

        for ai_inst in self.ais:
            debug("sending kill signal to path-finding thread for "+ai_inst.name+" ...")
            ai_inst.thread.is_running = False

        if winner:
            text = self.font.render("The {} won the game!".format(winner.name), True, (255, 0, 0))
            pos = (SCREEN[0]//20, SCREEN[1]*2//5)
            self.win.blit(text, pos)
            pygame.display.update()
            sleep(2)
        pygame.quit()

    def draw_debug_text(self):
        """
        draws some infos to the bottom of the screen.
        """
        bullet_count = 0
        player_health = 0
        ai_health = 0
        for tank in self.tanks:
            bullet_count += len(tank.bullet_mgr.bullets)
            if tank.name == "Player":
                player_health = tank.pos.astype("int32")
            if tank.name == "AI":
                ai_health = tank.pos.astype("int32")

        obst_count = len(self.obst_mgr.obstacles)
        obst_size = self.obst_mgr.rep_matrix.shape

        text1 = "bullets: {} obstacles: {} obstacle_matrix: {} "
        text1 = text1.format(bullet_count, obst_count, obst_size)
        text2 = "HP AI: {} HP Pl: {}"
        text2 = text2.format(ai_health, player_health)
        debug_text1 = self.debug_font.render(text1, True, (255, 0, 0))
        debug_text2 = self.debug_font.render(text2, True, (255, 0, 0))
        pos = np.array([5, HEIGHT*(9/10)])
        pos1 = pos.copy()
        pos2 = pos.copy()
        pos2[1] += self.debug_font.get_height()*1.5
        self.win.blit(debug_text1, pos1)
        self.win.blit(debug_text2, pos2)


class Slider():
    """
    shows the health of a tank on screen.\n
    is always relative to tank obj.
    """
    def __init__(self, obj, height, max_width, in_range, gap):
        self.obj = obj
        self.height = height
        self.max_width = max_width
        self.in_min, self.in_max = in_range
        self.gap = gap
        self.val = self.in_max
        self.color = pygame.Color(0, 255, 0)

    def update(self, input_val):
        """
        update slider value.
        """
        self.val = mapvalue(input_val, self.in_min, self.in_max, 0, self.max_width)
        red = int(mapvalue(input_val, self.in_min, self.in_max, 255, 0))
        green = int(mapvalue(input_val, self.in_min, self.in_max, 0, 255))
        self.color = pygame.Color(red, green, 0)

    def draw(self, win):
        """
        draw slider relative to tank obj.
        """
        temp_pos = list(self.obj.rect.center)
        temp_pos[1] += self.gap - self.height
        temp_pos[0] -= self.val/2
        rect = pygame.Rect(temp_pos[0], temp_pos[1], self.val, self.height)
        rect2 = pygame.Rect(temp_pos[0]-2, temp_pos[1]+5, self.val+4, self.height-10)
        pygame.draw.rect(win, pygame.Color(100, 100, 100), rect2)
        pygame.draw.rect(win, self.color, rect)


class Obstacle():
    """
    In-game obstacle. Is handled by ObstacleManage.\n
    Has a hitbox for tanks and one for shells.
    """
    def __init__(self, img, pos, sizes):
        self.hitbox = pygame.Rect(pos[0], pos[1], sizes[0], sizes[1])
        self.shell_rect = self.hitbox.copy()
        self.img = pygame.transform.rotate(img, randint(0, 359))
        self.img_pos = np.subtract(pos, np.divide(sizes, 3))
        self.shell_rect.width /= 2
        self.shell_rect.height /= 2
        self.shell_rect.center = self.hitbox.center

    def draw(self, win):
        """
        draw the obstacle and if necessary debug.
        """
        win.blit(self.img, self.img_pos)
        if DEBUG:
            pygame.draw.rect(win, (0, 255, 255), self.hitbox, 1)
            pygame.draw.rect(win, (255, 0, 255), self.shell_rect, 1)


class ObstacleManager():
    """
    handles obstacles (=draws them)\n
    Reads level data from files and builds map.
    """
    def __init__(self, obst_img):
        self.obstacles = []
        self.levels = []
        self.obst_img = obst_img
        self.rep_matrix = np.zeros(SIZES)

        #get all .lvl files
        for _, _, files in os.walk("../"):
            for file in files:
                if file.endswith(".lvl"):
                    debug(file)
                    self.levels.append(file)

        #level validation
        for lvl in self.levels[::1]:
            valid = True

            #retrieving level data
            lvl_file = open(lvl)
            lines = lvl_file.readlines()
            lvl_file.close()

            if len(lines) != SIZES[1]: #number of lines not matching
                print(("Error 0 while reading {}: Err0: number of lines invalid! \n"+
                       "Found {} lines instead of {}!\n").format(lvl, len(lines), SIZES[1]))
                valid = False
            else:
                for line in lines:
                    line = line.replace("\n", "")
                    if len(line) != SIZES[0]: #number of columns not matching
                        print(("Error 1 while reading {}: Err1: length of line {} invalid! \n"+
                               "Length of line was {} chars instead of {} !\n")
                              .format(lvl, lines.index(line)+"\n", len(line), SIZES[1]))
                        valid = False

            if not valid:
                self.levels[::1].remove(lvl)

        #checking for a valid level
        if not self.levels:
            print("No valid level file found! Exiting...")
            raise SystemExit()


        self.level = self.levels[randint(0, len(self.levels)-1)]
        print("Level chosen: {}".format(self.level))

    def build(self):
        """
        build the map from chosen level file.\n
        Writing simultanously in the representer-matrix.
        """
        level_file = open(self.level)
        pos = np.zeros(2, dtype=int)
        grid = np.zeros(2, dtype=int)
        for line in level_file:
            pos[0] = 0
            grid[0] = 0
            for char in line:
                if char == "X":
                    self.obstacles.append(Obstacle(self.obst_img, pos, GAPS))
                    self.rep_matrix[grid[1], grid[0]] = 1
                pos[0] += GAPS[0]
                grid[0] += 1
            pos[1] += GAPS[1]
            grid[1] += 1

    def draw(self, win):
        """
        draw all the obstacles.\n
        For more details see Obstacle.draw()
        """
        for obstacle in self.obstacles:
            obstacle.draw(win)


if __name__ == "__main__":
    GAME_MGR = GameManager()
    GAME_MGR.main()
