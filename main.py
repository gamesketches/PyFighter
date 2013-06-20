import pygame, sys, os
from pygame.locals import *

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

main_dir = os.path.split(os.path.abspath(sys.argv[0]))[0]
data_dir = os.path.join(main_dir, 'data')

#def enum(*sequential, **named):
#    enums = dict(zip(sequential, range(len(sequential))), **named)
#    return type('Enum', (), enums)

#Inputs = enum('DOWN','DOWNRIGHT','RIGHT','UPRIGHT','UP','UPLEFT','LEFT','DOWNLEFT', 'TERMINAL')

class Character(pygame.sprite.Sprite):
    """ Class holds all info on a Character and interprets it's actions """
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.meters = []
        self.health = 0
        self.neutralAnimation = []
        self.inputChain = [] # Keeps track of inputs for interpretting
        self.hitAnimation = []
        self.blockImage = None

    def update(self, curInputs, gameState):
        if curInputs == K_DOWN:
            self.inputChain.append('DOWN')
        if curInputs == K_RIGHT:
            self.inputChain.append('RIGHT')
        if curInputs == K_SPACE:
            self.inputChain.append('TERMINAL')
        self.interpretInputs()

    def interpretInputs(self):
        if self.inputChain == ['DOWN', 'RIGHT']:
            print "hadoken"
            self.inputChain.append('TERMINAL')
        if self.inputChain[-1] == 'TERMINAL':
            del self.inputChain[:]

class CombatManager():
    """ Class for managing collisions, inputs, gamestate, etc. """
    def __init__(self):

        self.player1 = Character()
        self.player2 = Character()

    def update(self):

        self.checkCollisions()
        self.updateCharacters()

    def checkCollision():
        print "Checking Collisions here"

    def updateCharacters():
        self.player1.update([], 0)
        self.player2.update([],0)
    

def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

def load_sound(name):
    class NoneSound:
        def play(self):pass
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join(data_dir, name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error:
        print ('Cannot load sound: %s' % fullname)
        raise SystemExit(str(geterror()))
    return sound

def main():
    
    #Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((468, 100))
    pygame.mouse.set_visible(0)

    #Create the background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))

    #Create the background
    background = pygame.Surface(screen.get_size())
    backgtround = background.convert()
    background.fill((250, 250, 250))

    #Display The Background
    screen.blit(background, (0,0))
    pygame.display.flip()

    #Prepare Game Objects
    clock = pygame.time.Clock()
    player1 = Character()
       
    going = True
    while going:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                player1.update(event.key, None)

        screen.blit(background, (0,0))
        pygame.display.flip()

if __name__ == '__main__':
    main()
