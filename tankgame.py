import pygame as pg

#pylint: disable=no-member
WIDTH = 500
HEIGHT = 500

class Player(object):
    def __init__(self,coords):
        self.x, self.y = coords
        self.orientations = ["n","ne","e","es","s","sw","w","wn"]
        self.orientation = "n"
        self.step

    def draw(self,win):
        win.blit(self.x,self.y)

    def move(self,keys):
        if keys[pg.K_w]:
            pass
        elif keys[pg.K_s]:
            pass
        
        if keys[pg.K_d]:
            self.orientation = self.orientations[(self.orientations.index(self.orientation)+1)%len(self.orientations)]
            print(self.orientation)
        elif keys[pg.K_a]:
            self.orientation = self.orientations[(self.orientations.index(self.orientation)-1)%len(self.orientations)]
            print(self.orientation)

def main():
    pg.init()
    win = pg.display.set_mode((WIDTH,HEIGHT))
    pg.display.set_caption("Tank Game","Tank Game")
    pg.display.update()


if __name__ == "__main__":
    main()