import pygame
import math


WIDTH = 500
HEIGHT = 500

bg = pygame.image.load("bg.jpg")
tank = pygame.image.load("tank.png")

class Player(object):
    def __init__(self,coords,img):
        self.x, self.y = coords
        self.orientation = 0.0
        self.step = math.radians(10)
        self.img = img
        self.orig = img

    def draw(self,win):
        win.blit(self.x,self.y)

    def move(self,keys):
        if keys[pygame.K_w]:
            self.x += math.cos(self.orientation)
            self.y += math.sin(self.orientation)
        elif keys[pygame.K_s]:
            self.x -= math.cos(self.orientation)
            self.y -= math.sin(self.orientation)
        
        if keys[pygame.K_d]:
            self.img = self.orig
            pygame.transform.rotate(self.img,self.orientation+self.step)
        elif keys[pygame.K_a]:
            pygame.transform.rotate(self.img,self.orientation-self.step)


class GameManager():
    def __init__(self):
        pygame.init()

        self.player = Player((250,250),tank)

        self.win = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Tank Game")
        pygame.display.set_icon(tank)
    

    def redrawGameWindow(self):
        self.win.blit(bg,(0,0))
        self.player.draw(self.win)
        pygame.display.update()


    def main(self):

        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            
            keys =  pygame.keys.get_pressed_keys()


            self.redrawGameWindow()

        pygame.quit()


if __name__ == "__main__":
    gameMgr = GameManager()
    gameMgr.main()