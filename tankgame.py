import pygame
import math


WIDTH = 500
HEIGHT = 500
DEBUG = False

bg = pygame.image.load("bg.jpg")
tank1 = [pygame.image.load("tank1.png"),pygame.image.load("tank2.png")]
tank2 = [pygame.image.load("tank3.png"),pygame.image.load("tank4.png")]
bullet = pygame.image.load("bullet.png")

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

class Player():
    def __init__(self,coords,vel,img,keyset,bullet_cooldown,bullet_vel):
        #print("{}, {}, {}, {}, {}, {}".format(coords,vel,img,keyset,bullet_cooldown,bullet_vel))
        self.x, self.y = coords
        self.angle = 0.0
        self.step = 2
        self.orig = img
        self.vel = vel
        self.img = self.orig[0]
        self.rect = self.img.get_rect()
        self.img_len = len(img)
        self.count = 0
        self.keyset = keyset
        self.bulletMgr = BulletManager(self,bullet_cooldown,self.keyset[4],bullet_vel)

    def draw(self,win):
        num = int(self.count)%self.img_len
        self.img = pygame.transform.rotate(self.orig[num],self.angle)

        self.rect = self.img.get_rect()  # Replace old rect with new rect.
        self.rect.center = (self.x, self.y)  # Put the new rect's center at old center.

        self.bulletMgr.drawBullets(win)
        win.blit(self.img,self.rect)

        if DEBUG:
            drawDebug(self.x,self.y,self.angle,win)
            

    def move(self,keys):
        self.bulletMgr.moveBullets()
        x_move, y_move = returnXYforAngle(self.angle,self.vel)

        if keys[self.keyset[0]]:
            self.y -= y_move
            self.x -= x_move 
            self.count += 0.05

        elif keys[self.keyset[1]]:
            self.y += y_move
            self.x += x_move
            self.count += 0.05
        
        
        if keys[self.keyset[2]]:
            self.angle += self.step
            self.count += 0.03

        elif keys[self.keyset[3]]:
            self.angle -= self.step
            self.count += 0.03
        
        self.bulletMgr.createBullets(keys)

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

    def createBullets(self,keys):
        time = pygame.time.get_ticks()
        if keys[self.key] and time-self.cooldown > self.alt:
            newbullet = Bullet(self.player.angle,self.vel,(self.player.x,self.player.y),bullet)
            self.bullets.append(newbullet)
            self.alt = time
        
    def moveBullets(self):
        for bullet in self.bullets[::-1]:
            bullet.move()
            if bullet.x > WIDTH or bullet.x < 0 or bullet.y > HEIGHT or bullet.y < 0:
                self.bullets.remove(bullet)
            #TODO Add collision here!
    
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
        self.player1 = Player((WIDTH-100,HEIGHT-100),tank_vel,tank1,keyset1,bullet_cooldown,bullet_vel)
        self.player2 = Player((100,100),tank_vel,tank2,keyset2,bullet_cooldown,bullet_vel)

        
    def redrawGameWindow(self):
        self.win.blit(bg,(0,0)) 
        self.player1.draw(self.win)
        self.player2.draw(self.win)
        pygame.display.update()


    def main(self):
        clock = pygame.time.Clock()
        run = True
        while run:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            
            keys =  pygame.key.get_pressed()
            self.player1.move(keys)
            self.player2.move(keys)
            self.redrawGameWindow()

        pygame.quit()
    
    

if __name__ == "__main__":
    gameMgr = GameManager()
    gameMgr.main()