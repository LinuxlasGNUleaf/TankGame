import pygame
import math
from random import randint
import os
import numpy

WIDTH = 500
HEIGHT = 500
DEBUG = True

bg = pygame.image.load("bg.jpg")
tank1 = [pygame.image.load("tank1.png"),pygame.image.load("tank2.png")]
tank2 = [pygame.image.load("tank3.png"),pygame.image.load("tank4.png")]
bullet = pygame.image.load("bullet.png")
rock = pygame.image.load("rock.png")

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

class Player():
    def __init__(self,coords,vel,img,keyset,bullet_cooldown,bullet_vel,border,name):
        self.x, self.y = coords
        self.angle = 0.0
        self.step = 2
        self.orig = img
        self.vel = vel
        self.img = self.orig[0]
        self.rect = self.img.get_rect()
        self.coll_rect = self.rect
        self.coll_rect.width /= 2
        self.coll_rect.height /= 2
        self.img_len = len(img)
        self.count = 0
        self.keyset = keyset
        self.bulletMgr = BulletManager(self,bullet_cooldown,self.keyset[4],bullet_vel)
        self.border = border
        self.slider = Slider(self,5,30,(0,100),50)
        self.HP = 100
        self.name = name

    def draw(self,win):
        num = int(self.count)%self.img_len
        self.img = pygame.transform.rotate(self.orig[num],self.angle)

        self.rect = self.img.get_rect()  # Replace old rect with new rect.
        self.rect.center = (self.x, self.y)  # Put the new rect's center at old center.

        self.bulletMgr.drawBullets(win)
        win.blit(self.img,self.rect)
        self.slider.draw(win)

        if DEBUG:
            drawDebug(self.x,self.y,self.angle,win)
            pygame.draw.rect(win,(255,0,0),self.coll_rect,1)
            
    def move(self,keys,players,obstacles):
        if self.HP > 0:
            self.bulletMgr.moveBullets(players)

            if keys[self.keyset[0]]: #forward
                self.moveIfNoCollision("forward",obstacles)
                self.count += 0.05

            elif keys[self.keyset[1]]: #backward
                self.moveIfNoCollision("backward",obstacles)
                self.count += 0.05
            
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
            players.remove(self)
    
    def updateCollideRect(self):
        self.coll_rect.center = (self.x,self.y)
    
    def onScreen(self):
        if self.x > self.border and self.x < WIDTH-self.border and self.y > self.border and self.y < HEIGHT-self.border:
            return True
        return False
    
    def moveIfNoCollision(self,direction,obstacles):
        x_move, y_move = returnXYforAngle(self.angle,self.vel)
        if direction == "forward":
            self.y -= y_move
            self.x -= x_move 
            if self.onScreen():
                self.undoObstacleCollision(obstacles)
            else:
                self.y += y_move
                self.x += x_move

        elif direction == "backward":
            self.y += y_move
            self.x += x_move
            if self.onScreen():
                self.undoObstacleCollision(obstacles)
            else:
                self.y -= y_move
                self.x -= x_move
    
    def undoObstacleCollision(self,obstacles):
        colliding = []
        for obstacle in obstacles:
            if self.coll_rect.colliderect(obstacle.rect):
                colliding.append(obstacle)
        
        for obstacle in colliding:
            diff = numpy.multiply(numpy.subtract((obstacle.rect.center),(self.coll_rect.center)),-1)
            diff = normalize(diff)
            self.x,self.y = numpy.add((diff),(self.x,self.y))

class Bullet():
    def __init__(self,angle,vel,coords,img):
        self.angle = angle
        self.vel = vel
        self.orig = img
        self.img = img
        self.x, self.y = coords
        self.rect = self.orig.get_rect()
    
    def move(self):
        x_move, y_move = returnXYforAngle(self.angle,self.vel)
        self.x -= x_move
        self.y -= y_move
    
    def draw(self,win):
        self.img = pygame.transform.rotate(self.orig,self.angle)
        self.rect.center = (self.x,self.y)
        win.blit(self.img,self.rect)

class BulletManager():
    def __init__(self,player,cooldown,trigger_key,vel):
        self.player = player
        self.bullets = []
        self.cooldown = cooldown
        self.alt = pygame.time.get_ticks()    
        self.key = trigger_key
        self.vel = vel
        self.dmg = 20

    def createBullets(self,keys):
        time = pygame.time.get_ticks()
        if keys[self.key] and time-self.cooldown > self.alt:
            angle = self.player.angle
            x_diff, y_diff = returnXYforAngle(angle,-45)
            x = self.player.x + x_diff
            y = self.player.y + y_diff
            newbullet = Bullet(angle,self.vel,(x,y),bullet)
            self.bullets.append(newbullet)
            self.alt = time
        
    def moveBullets(self,players):
        for bullet in self.bullets[::-1]:
            bullet.move()
            if bullet.x > WIDTH or bullet.x < 0 or bullet.y > HEIGHT or bullet.y < 0:
                self.bullets.remove(bullet)
            for player in players:
                if bullet.rect.colliderect(player.rect) and player != self.player:
                    player.HP -= self.dmg
                    self.bullets.remove(bullet)
    
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
        keyset1 = [pygame.K_w,pygame.K_s,pygame.K_a,pygame.K_d,pygame.K_SPACE]
        keyset2 = [pygame.K_UP,pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT,pygame.K_RCTRL]

        tank_vel = 1
        bullet_vel = 10
        bullet_cooldown = 500
        border = 10

        self.players = []

        player1 = Player((WIDTH-100,HEIGHT-100),tank_vel,tank1,keyset1,bullet_cooldown,bullet_vel,border,"Player Green")
        self.players.append(player1)
        player2 = Player((100,100),tank_vel,tank2,keyset2,bullet_cooldown,bullet_vel,border,"Player Red")
        self.players.append(player2)

        self.obstMgr = ObstacleManager(50,rock)
        self.obstMgr.build()
        
    def redrawGameWindow(self):
        self.win.blit(bg,(0,0))
        for player in self.players: 
            player.draw(self.win)
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

            if len(self.players) > 1:
                for player in self.players:
                    player.move(keys,self.players,self.obstMgr.obstacles)
            else:
                run = False
            self.redrawGameWindow()
        if len(self.players) == 1:
            txt = pygame.font.SysFont("Impact",32).render("{} won!".format(self.players[0].name),True,(255,0,0))
            self.win.blit(txt,(WIDTH/4,HEIGHT/4))
            pygame.display.update()
            pygame.time.delay(2000)

        pygame.quit()

class Slider():
    def __init__(self,obj,height,max_width,in_range,gap):
        self.obj = obj
        self.height = height
        self.max_width = max_width
        self.in_min, self.in_max = in_range
        self.gap = gap
    
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
    def __init__(self,img,pos):
        self.x, self.y = pos
        self.img = pygame.transform.rotate(img,randint(0,360))
        self.rect = self.img.get_rect()
        self.rect.width /= 3
        self.rect.height /= 3
        self.rect.center = (self.x,self.y)
    
    def draw(self,win):
        win.blit(self.img,self.rect)
        if DEBUG:
            pygame.draw.rect(win,(0,255,255),self.rect,1)

class ObstacleManager():
    def __init__(self,spaces,obst_img):
        self.obstacles = []
        self.spaces = spaces
        self.levels = []

        self.spacex = WIDTH//self.spaces
        self.spacey = HEIGHT//self.spaces

        self.obstImg = obst_img

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
            y+= self.spaces
            x = 0
            
            for char in line:
                x+= self.spaces

                if char == "X":
                    self.obstacles.append(Obstacle(self.obstImg,(x,y)))
    
    def draw(self,win):
        for obstacle in self.obstacles:
            obstacle.draw(win)

if __name__ == "__main__":
    gameMgr = GameManager()
    gameMgr.main()