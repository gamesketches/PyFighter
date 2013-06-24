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
        self.velocity = [0,0]
        self.curAnimation = []
        self.curAnimationFrame = 0
        self.keysDown = []
        self.curHurtBox = pygame.Rect(0, 0, 66, 96) 
        self.neutralAnimation = load_animation('RyuSFA3.png', [(190, 126, 66, 96),\
                                                               (269, 126, 66, 96),\
                                                               (349, 126, 66, 96),\
                                                               (426, 126, 66, 96),\
                                                               (505, 126, 66, 96)])
        self.walkforwardAnimation = load_animation('RyuSFA3.png', [(63, 237, 71, 94),\
                                                                   (144, 237, 71, 94),\
                                                                   (227, 237, 60, 94),\
                                                                   (306, 237, 55, 94), \
                                                                   (454, 237, 57, 94),\
                                                                   (454, 237, 64, 94)])
        self.curAnimation = self.neutralAnimation
        self.inputChain = [] # Keeps track of inputs for interpretting
        self.hitAnimation = []
        self.blockImage = None

    def update(self, gameState):
        #if curInputs is not None:
        #    if curInputs == K_DOWN:
        #        self.inputChain.append('DOWN')
        #    if curInputs == K_RIGHT:
        #        self.inputChain.append('RIGHT')
        #    if curInputs == K_SPACE:
        #        self.inputChain.append('TERMINAL')
        #    self.interpretInputs()
        #    self.curHurtBox.x += self.velocity[0]
        self.interpretInputs()
        self.curHurtBox.x += self.velocity[0]
        self.curAnimationFrame += 1
        if self.curAnimationFrame >= len(self.curAnimation): #Will need some more complicated parsing for state here later
            self.curAnimationFrame = 0

    def keyPressed(self, state, button):
        if state is True:
            if button == K_RIGHT:
                self.keysDown.append('RIGHT')
                self.curAnimation = self.walkforwardAnimation
                self.curAnimationFrame = 0
            if button == K_LEFT:
                self.keysDown.append('LEFT')
        else:
            if button == K_RIGHT:
                del self.keysDown[self.keysDown.index('RIGHT')]
                self.curAnimation = self.neutralAnimation
            if button == K_LEFT:
                del self.keysDown[self.keysDown.index('LEFT')]

    def interpretInputs(self):
        #if self.inputChain == ['DOWN', 'RIGHT']:
        #    print "hadoken"
        #    self.inputChain.append('TERMINAL')
        #if self.inputChain[-1] == 'TERMINAL':
        #    del self.inputChain[:]
        if 'RIGHT' in self.keysDown:
            self.velocity[0] = 1
        elif 'LEFT' in self.keysDown:
            self.velocity[0] = -1
        else:
            self.velocity[0] = 0

    def currentFrame(self):
        return self.curAnimation[self.curAnimationFrame]

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

def load_animation(filename, coords, colorkey=None):
    master_image, master_rect = load_image(filename)
    theAnimation = []
    for i in coords:
        theAnimation.append(master_image.subsurface(i))

    return theAnimation

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
        clock.tick(15)
        key = None
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                else:
                    key = event.key
                    player1.keyPressed(True, event.key)
            elif event.type == KEYUP:
                player1.keyPressed(False, event.key)
        player1.update( None)        
        screen.blit(background, (0,0))
        screen.blit(player1.currentFrame(), player1.curHurtBox.topleft)
        pygame.display.flip()

if __name__ == '__main__':
    main()
