import pygame
import math
from random import randint
import os
import numpy as np
from time import time,sleep

#========CONFIGURATION========
WIDTH = 500
HEIGHT = 500
DEBUG = False
ShellCollide = True
BULLET_COOLDOWN = 500
TANK_VEL = 1
BULLET_VEL = 5
BORDER = 10
SIZE_X = 10
SIZE_Y = 10
AI_TURN_VEL = 1
#=============================
SIZES = np.array([SIZE_X,SIZE_Y])
SCREEN = np.array([WIDTH,HEIGHT])

#Loading images 
bg = pygame.image.load("bg.jpg")
tank1 = [pygame.image.load("tank1.png"),pygame.image.load("tank2.png")]
tank2 = [pygame.image.load("tank3.png"),pygame.image.load("tank4.png")]
bullet = pygame.image.load("bullet.png")
rock = pygame.image.load("rock.png")

def UID_create(len):
    UID = ""
    for i in range(len):
        UID += str(randint(0,9))
    return UID

def returnXYforAngle(angle,vel):
    rad = math.radians(angle)
    res = np.zeros(2)
    res[0] = math.sin(rad)
    res[1] = math.cos(rad)
    res = np.multiply(res,vel)
    return res

def drawDebug(pos,angle,win):
    res = returnXYforAngle(angle,50)
    pygame.draw.line(win, (0,255,0),(pos[0]-res[0],pos[1]),(pos[0]-res[0],pos[1]-res[1]))
    pygame.draw.line(win, (0,255,255),pos,(pos[0]-res[0],pos[1]))
    pygame.draw.line(win, (255,0,255),pos,(pos[0]-res[0],pos[1]-res[1]))

def constrain(x,min_,max_):
    return min(max(x,min_),max_)

def map(value, inMin, inMax, outMin, outMax):
    value = constrain(value,inMin,inMax)
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

def calcDistance(obj1,obj2):
        diff = np.subtract(obj1.pos,obj2.pos)
        distance = math.sqrt(diff[0]**2+diff[1]**2)
        return distance

class Representer():
    def __init__(self,obj,hitbox):
        self.obj = obj
        self.hitbox = hitbox
    
    def update(self):
        self.hitbox = self.obj.coll_rect

class Tank():
    def __init__(self,imgset,coords,name,uid):
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
        self.HP = 100
        self.name = name
        self.slider = Slider(self,5,30,(0,100),40)
        self.slider.update(self.HP)
        self.rep = Representer(self,self.coll_rect)
        self.border = self.coll_rect.width//2
        self.DeleteFlag = False
        self.uid = uid
        self.bulletMgr = BulletManager(self)
    
    def draw(self,win):
        self.bulletMgr.drawBullets(win)

        num = int(self.count)%self.img_len
        self.img = pygame.transform.rotate(self.orig[num],self.angle)

        self.rect = self.img.get_rect()
        self.rect.center = self.pos

        win.blit(self.img,self.rect)
        self.slider.draw(win)

        if DEBUG:
            drawDebug(self.pos,self.angle,win)
            pygame.draw.rect(win,(255,0,0),self.coll_rect,1)
    
    def move(self,keys,tanks,obstacles):
        
        if self.HP > 0:
            self.bulletMgr.moveBullets(tanks,obstacles)
        else:
            self.DeleteFlag = True
        self.slider.update(self.HP)
        self.updateCollideRect()
        self.bulletMgr.createBullets(keys)

    def updateCollideRect(self):
        self.coll_rect.center = self.pos
    
    def correctMovement(self,obstacles):
        for obstacle in obstacles:
            if self.coll_rect.colliderect(obstacle.coll_rect):
                diff = np.multiply(np.subtract((obstacle.coll_rect.center),(self.coll_rect.center)),-1)
                diff = normalize(diff)
                self.pos = np.add(diff,self.pos)
            
        self.pos[0] = constrain(self.pos[0],self.border,WIDTH-self.border)
        self.pos[1] = constrain(self.pos[1],self.border,HEIGHT-self.border)

class Player(Tank):
    def __init__(self,imgset,coords,name,keyset,rep_matrix,uid):
        super().__init__(imgset,coords,name,uid)
        self.keyset = keyset
        self.bulletMgr.setPlayer(keyset[4])
            
    def move(self,keys,tanks,obstacles):
        if keys[self.keyset[0]] or keys[self.keyset[1]]:  #moving
            change = returnXYforAngle(self.angle,TANK_VEL)
            if keys[self.keyset[0]]:
                self.pos = np.subtract(self.pos,change)
                self.count += 0.05

            elif keys[self.keyset[1]]:
                self.pos = np.add(self.pos,change)
                self.count += 0.05
            self.correctMovement(obstacles)
            
        if keys[self.keyset[2]]: #left
            self.angle += self.step
            self.count += 0.03

        elif keys[self.keyset[3]]: #right
            self.angle -= self.step
            self.count += 0.03

        super().move(keys,tanks,obstacles) 
    
class AI(Tank):
    def __init__(self,imgset,coords,name,rep_matrix,uid):
        super().__init__(imgset,coords,name,uid)
        self.rep_matrix =rep_matrix
        self.bulletMgr.setAI()

    def move(self,keys,tanks,obstacles):
        angle_goal = self.calcTargetAngle(tanks)
        self.angle = constrain(angle_goal,self.angle-AI_TURN_VEL,self.angle+AI_TURN_VEL)
        self.pos = np.subtract(self.pos,returnXYforAngle(self.angle,TANK_VEL))
        self.correctMovement(obstacles)
        super().move(0,tanks,obstacles)
    
    def calcTargetAngle(self,tanks):
        if len(tanks) > 1:
            dist = int(math.sqrt(WIDTH**2 + HEIGHT**2))
            for rep in tanks:
                thisDist = calcDistance(self,rep.obj)
                if thisDist < dist:
                    target = rep.obj
                    dist = thisDist
        elif len(tanks) == 1:
            target = tanks[0].obj
            dist = calcDistance(self,tanks[0].obj)
        else:
            raise Warning("Error while calculating AI movement: no opponents found!")
            return
        diff = np.subtract(target.pos,self.pos)
        return math.degrees(math.atan2(-diff[1],diff[0]))-90

class Bullet():
    def __init__(self,angle,coords,img):
        self.img = pygame.transform.rotate(img,angle)
        self.pos = np.array(coords)
        self.rect = img.get_rect()
        self.angle = angle
        self.rect.width /= 2
        self.rect.height /= 2
        self.rect.center = self.pos
    
    def move(self):
        change = returnXYforAngle(self.angle,BULLET_VEL)
        self.pos = np.subtract(self.pos,change)
    
    def draw(self,win):
        self.rect.center = self.pos
        win.blit(self.img,self.rect)
        if DEBUG:
            pygame.draw.rect(win,(255,0,255),self.rect,1)
            
class BulletManager():
    def __init__(self,player):
        self.player = player
        self.bullets = []
        self.alt = pygame.time.get_ticks()    
        self.dmg = 20
        self.setup = False
    
    def setAI(self):
        if(not(self.setup)):
            self.setup = True
            self.type = "AI"
        else:
            raise Warning("multiple setup of Bulletmgr is not valid")

    def setPlayer(self,key):
        if(not(self.setup)):
            self.setup = True
            self.type = "Player"
            self.key = key
        else:
            raise Warning("multiple setup of Bulletmgr is not valid")

    def createBullets(self,keys):
        time = pygame.time.get_ticks()
        if (((self.type == "Player") and keys[self.key]) or (self.type == "AI")): #(if player and Key pressed) or if AI
            if time-BULLET_COOLDOWN > self.alt:
                angle = self.player.angle
                change = returnXYforAngle(angle,-45)
                newpos = np.add(self.player.pos,change)
                newbullet = Bullet(angle,newpos,bullet)
                self.bullets.append(newbullet)
                self.alt = time
        
    def moveBullets(self,reps,obstacles):
        for bullet in self.bullets[::-1]:
            bullet.move()

            #checking for on-screen
            if not((int(bullet.pos[0]) in range(0,SCREEN[0])) and (int(bullet.pos[1]) in range(0,SCREEN[1]))):
                self.bullets.remove(bullet)
                continue                
            
            #checking for collision with another tank
            exist = True
            for rep in reps:
                tank = rep.obj
                if bullet.rect.colliderect(rep.hitbox) and tank != self.player:
                    tank.HP -= self.dmg
                    exist = False

            if not(exist):
                self.bullets.remove(bullet)
                continue                
            
            #checking for collision with obstacles
            if ShellCollide:
                for obstacle in obstacles:
                    if bullet.rect.colliderect(obstacle.shell_rect):
                        self.bullets.remove(bullet)
                        break

    def drawBullets(self,win):
        for bullet in self.bullets:
            bullet.draw(win)

class GameManager():
    def __init__(self):
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Tank Game")
        pygame.display.set_icon(tank1[0])
        self.font = pygame.font.Font("Perfect_DOS_VGA_437.ttf",SCREEN[0]//15)
        self.debug_font = pygame.font.Font("Perfect_DOS_VGA_437.ttf",SCREEN[0]//30)

        self.obstMgr = ObstacleManager(SIZES,rock)
        self.obstMgr.build()

        keyset = [pygame.K_w,pygame.K_s,pygame.K_a,pygame.K_d,pygame.K_SPACE]

        self.tanks = []
        player = Player(tank1,(400,400),"Player",keyset,self.obstMgr.repMatrix,UID_create(10))
        self.tanks.append(player.rep)
        ai = AI(tank2,(100,100),"AI",self.obstMgr.repMatrix,UID_create(10))
        self.tanks.append(ai.rep)

    def redrawGameWindow(self):
        self.win.blit(bg,(0,0))
        if DEBUG:
            self.drawDebugText()
        for tank in self.tanks:
            tank.obj.draw(self.win)
        self.obstMgr.draw(self.win)
        pygame.display.update()

    def main(self):
        clock = pygame.time.Clock()
        run = True
        winner = 0
        while run:
            clock.tick(240)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            
            keys =  pygame.key.get_pressed()

            for tank in self.tanks[::1]:
                custom = self.tanks.copy()

                for rep in custom[::1]:
                    if (rep.obj.uid == tank.obj.uid):
                        custom.remove(rep)

                tank.obj.move(keys,custom,self.obstMgr.obstacles)
                if tank.obj.DeleteFlag:
                    self.tanks.remove(tank)
            
            if len(self.tanks) <= 1:
                run = False
                if len(self.tanks) == 1:
                    winner = self.tanks[0].obj
            self.redrawGameWindow()

        if(winner != 0):
            text = self.font.render("The {} won the game!".format(winner.name),True,(255,0,0))
            pos = (SCREEN[0]//20,SCREEN[1]*2//5)
            self.win.blit(text,pos)
            pygame.display.update()
            sleep(2)
        pygame.quit()

    def drawDebugText(self):
        bulletCount = 0
        Player_HP = 0
        AI_HP = 0
        for tank in self.tanks:
            bulletCount += len(tank.obj.bulletMgr.bullets)
            if (tank.obj.name == "Player"):
                Player_HP = tank.obj.pos.astype("int32")
            if (tank.obj.name == "AI"):
                AI_HP = tank.obj.pos.astype("int32")

        obstCount = len(self.obstMgr.obstacles)
        obst_Size = self.obstMgr.repMatrix.shape
        
        text1 = "bullets: {} obstacles: {} obstacle_matrix: {} ".format(bulletCount,obstCount,obst_Size)
        text2 = "HP AI: {} HP Pl: {}".format(AI_HP,Player_HP)
        debug_text1 = self.debug_font.render(text1,True,(255,0,0))
        debug_text2 = self.debug_font.render(text2,True,(255,0,0))
        pos = np.array([5,HEIGHT*(9/10)])
        pos1 = pos.copy()
        pos2 = pos.copy()
        pos2[1] += self.debug_font.get_height()*1.5
        self.win.blit(debug_text1,pos1)
        self.win.blit(debug_text2,pos2)

class Slider():
    def __init__(self,obj,height,max_width,in_range,gap):
        self.obj = obj
        self.height = height
        self.max_width = max_width
        self.in_min, self.in_max = in_range
        self.gap = gap
        self.val = self.in_max
    
    def update(self,input):
        self.val = map(input,self.in_min,self.in_max,0,self.max_width)
        r = int(map(input,self.in_min,self.in_max,255,0))
        g = int(map(input,self.in_min,self.in_max,0,255))
        self.color = pygame.Color(r, g, 0)

    def draw(self,win):
        x,y = self.obj.rect.center
        y += self.gap - self.height
        x -= self.val/2
        rect = pygame.Rect(x,y,self.val,self.height)
        rect2 = pygame.Rect(x-2,y+5,self.val+4,self.height-10)
        pygame.draw.rect(win,pygame.Color(100,100,100),rect2)
        pygame.draw.rect(win,self.color,rect)

class Obstacle():
    def __init__(self,img,pos,sizes):
        self.coll_rect = pygame.Rect(pos[0],pos[1],sizes[0],sizes[1])
        self.shell_rect = self.coll_rect.copy()
        self.img = pygame.transform.rotate(img,randint(0,359))
        self.img_pos = np.subtract(pos,np.divide(sizes,3))
        self.shell_rect.width /= 2
        self.shell_rect.height /= 2
        self.shell_rect.center = self.coll_rect.center

    def draw(self,win):
        win.blit(self.img,self.img_pos)
        if DEBUG:
            pygame.draw.rect(win,(0,255,255),self.coll_rect,1)
            pygame.draw.rect(win,(255,0,255),self.shell_rect,1)

class ObstacleManager():
    def __init__(self,sizes,obst_img):
        self.obstacles = []
        self.levels = []
        self.sizes = sizes 
        self.gaps = np.divide(SCREEN,sizes).astype("int32")
        self.obstImg = obst_img
        self.repMatrix = np.zeros(self.sizes)

        #get all .lvl files
        for _,_,f in os.walk("../"):
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

            if len(lines) != self.sizes[1]: #number of lines not matching
                print("Error 0 while reading {}: Err0: number of lines invalid! \Found {} lines instead of {}!\n".format(lvl,len(lines),self.sizes[1]))
                isValid = False
            else:
                for line in lines:
                    line = line.replace("\n","")
                    if len(line) != self.sizes[0]: #number of columns not matching
                        print("Error 1 while reading {}: Err1: length of line {} invalid! \nLength of line was {} chars instead of {} !\n".format(lvl,lines.index(line)+"\n",len(line),self.sizes[1]))
                        isValid = False
        
            if not(Valid):
                self.levels[::1].remove(lvl)

        #checking for a valid level 
        if len(self.levels) < 1:
            print("No valid level file found! Exiting...")
            raise SystemExit()                
        

        self.level = self.levels[randint(0,len(self.levels)-1)]
        print("Level chosen: {}".format(self.level))

    def build(self):
        level_file = open(self.level)
        pos = np.zeros(2,dtype=int)
        grid = np.zeros(2,dtype=int)
        for line in level_file:
            pos[0] = 0
            grid[0] = 0
            for char in line:
                if char == "X":
                    self.obstacles.append(Obstacle(self.obstImg,pos,self.gaps))
                    self.repMatrix[grid] = 1
                pos[0] += self.gaps[0]
                grid[0] += 1
            pos[1]+= self.gaps[1]
            grid[1] += 1
    
    def draw(self,win):
        for obstacle in self.obstacles:
            obstacle.draw(win)

if __name__ == "__main__":
    gameMgr = GameManager()
    gameMgr.main()