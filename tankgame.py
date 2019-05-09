import pygame
import math


WIDTH = 500
HEIGHT = 500

bg = pygame.image.load("bg.jpg")
tank = [pygame.image.load("tank1.png"),pygame.image.load("tank2.png")]

class Player(object):
    def __init__(self,coords,img):
        self.x, self.y = coords
        self.angle = 0.0
        self.step = 1
        self.orig = img
        self.img = self.orig[0]
        self.rect = self.img.get_rect()
        self.img_len = len(img)
        self.count = 0

    def draw(self,win):
        num = int(self.count)%self.img_len
        self.img = pygame.transform.rotate(self.orig[num],self.angle)

        self.rect = self.img.get_rect()  # Replace old rect with new rect.
        self.rect.center = (self.x, self.y)  # Put the new rect's center at old center.

        win.blit(self.img,self.rect)
        

    def move(self,keys):
        rad = math.radians(self.angle)
        if keys[pygame.K_w]:
            self.y -= math.cos(rad)
            self.x -= math.sin(rad)
            self.count += 0.05

        elif keys[pygame.K_s]:
            self.y += math.cos(rad)
            self.x += math.sin(rad)
            self.count += 0.05
        
        if keys[pygame.K_d]:
            self.angle -= self.step
            self.count += 0.03

        elif keys[pygame.K_a]:
            self.angle += self.step
            self.count += 0.03
            
            


class GameManager():
    def __init__(self):
        pygame.init()

        self.player = Player((250,250),tank)

        self.win = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Tank Game")
        pygame.display.set_icon(tank[0])
    

    def redrawGameWindow(self):
        self.win.blit(bg,(0,0))
        self.player.draw(self.win)
        #self.win.blit(tank,(0,0))
        pygame.display.update()


    def main(self):

        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            
            keys =  pygame.key.get_pressed()
            self.player.move(keys)


            self.redrawGameWindow()

        pygame.quit()


if __name__ == "__main__":
    gameMgr = GameManager()
    gameMgr.main()