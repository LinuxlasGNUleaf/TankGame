import pygame
import math
from random import randint
import os
import numpy

#========CONFIGURATION========
WIDTH = 500
HEIGHT = 500
DEBUG = True
ShellCollide = True
BULLET_COOLDOWN = 500
TANK_VEL = 1
BULLET_VEL = 10
BORDER = 10
#=============================

bg = pygame.image.load("bg.jpg")
tank1 = [pygame.image.load("tank1.png"),pygame.image.load("tank2.png")]
tank2 = [pygame.image.load("tank3.png"),pygame.image.load("tank4.png")]
bullet = pygame.image.load("bullet.png")
rock = pygame.image.load("rock.png")

SCREEN = pygame.Rect(0,0,WIDTH,HEIGHT)

def returnXYforAngle(angle,vel):
    rad = math.radians(angle)
    x = math.sin(rad)
    y = math.cos(rad)
    x *= vel
    y *= vel
    return x,y

def drawDebug(x,y,angle,win):
    x_dir,y_dir = returnXYforAngle(angle,100)

    pygame.draw.line(win, (0,255,0),(x-x_dir,y),(x-x_dir,y-y_dir))
    pygame.draw.line(win, (0,255,255),(x,y),(x-x_dir,y))
    pygame.draw.line(win, (255,0,255),(x,y),(x-x_dir,y-y_dir))

def map(value, inMin, inMax, outMin, outMax):
    if value < inMin:
        value = inMin
    elif value > inMax:
        value = inMax
    inRange = max(inMax - inMin,1)
    outRange = outMax - outMin
    valueScaled = float(value - inMin) / float(inRange)

    return outMin + (valueScaled * outRange)

def normalize(v):
    norm = numpy.linalg.norm(v)
    if norm == 0: 
       return v
    return v / norm

class Representer():
    def __init__(self,obj,hitbox):
        self.obj = obj
        self.hitbox = hitbox
    
    def update(self):
        self.hitbox = self.obj.coll_rect

class Sprite:
    def __init__(self,img,coords):
        self.img = img
        self.x,self.y = coords
        self.orig  = img
        self.angle = 0.0
        self.rect = self.orig.get_rect()
    
    def draw(self,win):
        self.img = pygame.transform.rotate(self.orig,self.angle)
        self.rect.center = (self.x,self.y)
        win.blit(self.img,(self.x,self.y))
        if DEBUG:
            pygame.draw.rect(win,(255,0,255),self.rect,1)

class Tank():
    def __init__(self,imgset,coords,name):
        self.x, self.y = coords
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
        self.slider = Slider(self,5,30,(0,100),50)
        self.slider.update(self.HP)
        self.rep = Representer(self,self.coll_rect)
    
    def draw(self,win):
        num = int(self.count)%self.img_len
        self.img = pygame.transform.rotate(self.orig[num],self.angle)

        self.rect = self.img.get_rect()
        self.rect.center = (self.x, self.y)

        win.blit(self.img,self.rect)
        self.slider.draw(win)

        if DEBUG:
            drawDebug(self.x,self.y,self.angle,win)
            pygame.draw.rect(win,(255,0,0),self.coll_rect,1)
    
    def updateCollideRect(self):
        self.coll_rect.center = (self.x,self.y)
    
    def undoObstacleCollision(self,obstacles):
        colliding = []
        for obstacle in obstacles:
            if self.coll_rect.colliderect(obstacle.coll_rect):
                colliding.append(obstacle)
        
        for obstacle in colliding:
            diff = numpy.multiply(numpy.subtract((obstacle.coll_rect.center),(self.coll_rect.center)),-1)
            diff = normalize(diff)
            self.x,self.y = numpy.add((diff),(self.x,self.y))
       
    def onScreen(self):
        return SCREEN.contains(self.coll_rect)

class Player(Tank):
    def __init__(self,imgset,coords,name,keyset):
        super().__init__(imgset,coords,name)
        self.keyset = keyset
        self.bulletMgr = BulletManager(self,self.keyset[4])
            
    def move(self,keys,tanks,obstacles):
        if self.HP > 0:
            self.bulletMgr.moveBullets(tanks,obstacles)

            if keys[self.keyset[0]] or keys[self.keyset[1]]:  #moving
                oldpos = (self.x,self.y)
                x_move, y_move = returnXYforAngle(self.angle,TANK_VEL)
                if keys[self.keyset[0]]:
                    self.y -= y_move
                    self.x -= x_move 
                    self.count += 0.05
                elif keys[self.keyset[1]]:
                    self.y += y_move
                    self.x += x_move
                    self.count += 0.05
                if self.onScreen():
                    self.undoObstacleCollision(obstacles)
                else:
                    self.x,self.y = oldpos 

            if keys[self.keyset[2]]: #left
                self.angle += self.step
                self.count += 0.03

            elif keys[self.keyset[3]]: #right
                self.angle -= self.step
                self.count += 0.03
            
            self.bulletMgr.createBullets(keys)
            self.slider.update(self.HP)
            self.updateCollideRect()
        else:
            tanks.remove(self)
    
    def draw(self,win):
        self.bulletMgr.drawBullets(win)
        super().draw(win)
    
class AI(Tank):
    def __init__(self,imgset,coords,name):
        super().__init__(imgset,coords,name)

    def move(self,keys,tanks,obstacles):
        pass

class Bullet(Sprite):
    def __init__(self,angle,coords,img):
        super().__init__(img,coords)
        self.angle = angle
        self.rect.width /= 2
        self.rect.height /= 2
        self.rect.center = self.orig.get_rect().center
    
    def move(self):
        x_move, y_move = returnXYforAngle(self.angle,BULLET_VEL)
        self.x -= x_move
        self.y -= y_move
        
class BulletManager():
    def __init__(self,player,trigger_key):
        self.player = player
        self.bullets = []
        self.alt = pygame.time.get_ticks()    
        self.key = trigger_key
        self.dmg = 20

    def createBullets(self,keys):
        time = pygame.time.get_ticks()
        if keys[self.key] and time-BULLET_COOLDOWN > self.alt:
            angle = self.player.angle
            x_diff, y_diff = returnXYforAngle(angle,-45)
            x = self.player.x + x_diff
            y = self.player.y + y_diff
            newbullet = Bullet(angle,(x,y),bullet)
            self.bullets.append(newbullet)
            self.alt = time
        
    def moveBullets(self,reps,obstacles):
        for bullet in self.bullets[::-1]:
            existing = True
            bullet.move()
            if bullet.x > WIDTH or bullet.x < 0 or bullet.y > HEIGHT or bullet.y < 0:
                self.bullets.remove(bullet)
                existing = False

            if not(existing):
                continue
            
            for rep in reps:
                tank = rep.obj
                if bullet.rect.colliderect(rep.hitbox) and tank != self.player:
                    tank.HP -= self.dmg
                    self.bullets.remove(bullet)
                    existing = False
            
            if not(existing):
                continue

            if ShellCollide:
                for obstacle in obstacles:
                    if bullet.rect.colliderect(obstacle.shell_rect):
                        self.bullets.remove(bullet)
                        existing = False
                        break

    
    def drawBullets(self,win):
        for bullet in self.bullets:
            bullet.draw(win)

class GameManager():
    def __init__(self):
        #window setup
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Tank Game")
        pygame.display.set_icon(tank1[0])

        #player instanciation
        keyset = [pygame.K_w,pygame.K_s,pygame.K_a,pygame.K_d,pygame.K_SPACE]

        self.tanks = []
        self.player = Player(tank1,(400,400),"Player",keyset)
        self.tanks.append(self.player.rep)
        self.ai = AI(tank2,(100,100),"AI")
        self.tanks.append(self.ai.rep)

        self.obstMgr = ObstacleManager(50,rock)
        self.obstMgr.build()
        
    def redrawGameWindow(self):
        self.win.blit(bg,(0,0))
        self.player.draw(self.win)
        self.ai.draw(self.win)
        self.obstMgr.draw(self.win)
        pygame.display.update()


    def main(self):
        clock = pygame.time.Clock()
        run = True
        while run:
            clock.tick(120)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            
            keys =  pygame.key.get_pressed()

            self.player.move(keys,self.tanks,self.obstMgr.obstacles)
            self.ai.move
            self.redrawGameWindow()

        pygame.quit()

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

class Obstacle(Sprite):
    def __init__(self,img,rect):
        self.coll_rect = rect
        self.shell_rect = pygame.Rect(rect.x,rect.y,rect.width,rect.height)
        self.img = pygame.transform.rotate(img,randint(0,360))
        self.img_rect = pygame.Rect(rect.x-rect.width//3,rect.y-rect.height//3,rect.width,rect.height)
        self.shell_rect.width /= 2
        self.shell_rect.height /= 2
        self.shell_rect.center = self.coll_rect.center

    def draw(self,win):
        win.blit(self.img,self.img_rect)
        if DEBUG:
            pygame.draw.rect(win,(0,255,255),self.coll_rect,1)
            pygame.draw.rect(win,(255,0,255),self.shell_rect,1)

class ObstacleManager():
    def __init__(self,spaces,obst_img):
        self.obstacles = []
        self.spaces = spaces
        self.levels = []

        self.spacex = WIDTH//self.spaces
        self.spacey = HEIGHT//self.spaces

        self.obstImg = obst_img

        #get all .lvl files
        for _,_,f in os.walk("../"):
            for file in f:
                if file.endswith(".lvl"):
                    print(file)
                    self.levels.append(file)

        #level validation
        for lvl in self.levels[::1]:
            Valid = True

            lvl_file = open(lvl)
            lines = lvl_file.readlines()
            lvl_file.close()

            if len(lines) != self.spacey:
                print("Error while reading "+lvl+": Err0: number of lines invalid! \nNumber of lines are "+str(len(lines))+" lines instead of "+str(self.spacey)+" !\n")
                isValid = False
            else:
                num = 0
                for line in lines:
                    num += 1
                    line = line.replace("\n","")
                    if len(line) != self.spacex:
                        print("Error while reading "+lvl+": Err1: length of line "+str(num)+" invalid! \nLength of line was "+str(len(line))+" chars instead of "+str(self.spacey)+" !\n")
                        isValid = False
                        break

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
        x,y = (0,0)
        for line in level_file:
            x = 0
            for char in line:
                if char == "X":
                    self.obstacles.append(Obstacle(self.obstImg,pygame.Rect(x,y,self.spaces,self.spaces)))
                x+= self.spaces
            y+= self.spaces
    
    def draw(self,win):
        for obstacle in self.obstacles:
            obstacle.draw(win)

if __name__ == "__main__":
    gameMgr = GameManager()
    gameMgr.main()