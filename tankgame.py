import pygame
import math


WIDTH = 500
HEIGHT = 500
DEBUG = False

bg = pygame.image.load("bg.jpg")
tank = [pygame.image.load("tank1.png"),pygame.image.load("tank2.png")]
bullet = pygame.image.load("bullet.png")

def returnXYforAngle(angle):
    rad = math.radians(angle)
    x = math.sin(rad)
    y = math.cos(rad)
    return x,y

class Player():
    def __init__(self,coords,img):
        self.x, self.y = coords
        self.angle = 0.0
        self.step = 2
        self.orig = img
        self.img = self.orig[0]
        self.rect = self.img.get_rect()
        self.img_len = len(img)
        self.count = 0
        self.wasTurning = False

    def draw(self,win):
        num = int(self.count)%self.img_len
        self.img = pygame.transform.rotate(self.orig[num],self.angle)

        self.rect = self.img.get_rect()  # Replace old rect with new rect.
        self.rect.center = (self.x, self.y)  # Put the new rect's center at old center.

        win.blit(self.img,self.rect)
        if DEBUG:
            rad = math.radians(self.angle)
            x_dir = 100*math.sin(rad)
            y_dir = 100*math.cos(rad)

            pygame.draw.line(win, (0,255,0),(self.x-x_dir,self.y),(self.x-x_dir,self.y-y_dir))
            pygame.draw.line(win, (0,255,255),(self.x,self.y),(self.x-x_dir,self.y))
            pygame.draw.line(win, (255,0,255),(self.x,self.y),(self.x-x_dir,self.y-y_dir))

    def move(self,keys):
        x_move, y_move = returnXYforAngle(self.angle)
        if keys[pygame.K_w]:
            self.y -= y_move
            self.x -= x_move
            self.count += 0.05

        elif keys[pygame.K_s]:
            self.y += y_move
            self.x += x_move
            self.count += 0.05
        
        
        if keys[pygame.K_d]:
            self.angle -= self.step
            self.count += 0.03
            self.wasTurningRight = True

        elif keys[pygame.K_a]:
            self.angle += self.step
            self.count += 0.03
            self.wasTurningLeft = True
        
        else:
            self.wasTurningLeft = False
            self.wasTurningRight = False
            
class GameManager():
    def __init__(self):
        pygame.init()
        self.player = Player((250,250),tank)
        self.win = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Tank Game")
        pygame.display.set_icon(tank[0])

        self.bullets = []
        self.cooldown = 500
        self.alt = pygame.time.get_ticks()
    

    def redrawGameWindow(self):
        self.win.blit(bg,(0,0))
        self.drawBullets()
        self.player.draw(self.win)
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
            self.player.move(keys)
            self.moveBullets()
            self.createBullets(keys)
            self.redrawGameWindow()

        pygame.quit()
    
    def createBullets(self,keys):
        time = pygame.time.get_ticks()
        if keys[pygame.K_SPACE] and (len(self.bullets) < 10) and time-self.cooldown > self.alt:
            if self.player.wasTurningLeft:
                angle = self.player.angle - self.player.step*2
            elif self.player.wasTurningLeft:
                angle = self.player.angle + self.player.step*2
            else:
                angle = self.player.angle
            newbullet = Bullet(angle,2,(self.player.x,self.player.y),bullet)
            self.bullets.append(newbullet)
            self.alt = time
    
    def moveBullets(self):
        for bullet in self.bullets[::-1]:
            bullet.move()
            if bullet.x > WIDTH or bullet.x < 0 or bullet.y > HEIGHT or bullet.y < 0:
                self.bullets.remove(bullet)
            #TODO Add collision here!
    
    def drawBullets(self):
        for bullet in self.bullets:
            bullet.draw(self.win)

class Bullet():
    def __init__(self,angle,vel,coords,img):
        self.angle = angle
        self.vel = vel
        self.orig = img
        self.img = img
        self.x, self.y = coords
        self.rect = self.orig.get_rect()
    
    def move(self):
        x_move, y_move = returnXYforAngle(self.angle)
        self.x -= x_move*self.vel
        self.y -= y_move*self.vel
    
    def draw(self,win):
        self.img = pygame.transform.rotate(self.orig,self.angle)
        self.rect.center = (self.x,self.y)
        win.blit(self.img,self.rect)

if __name__ == "__main__":
    gameMgr = GameManager()
    gameMgr.main()