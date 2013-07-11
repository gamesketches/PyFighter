import pygame, sys, os, character
from pygame.locals import *

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

main_dir = os.path.split(os.path.abspath(sys.argv[0]))[0]
data_dir = os.path.join(main_dir, 'data')

#def enum(*sequential, **named):
#    enums = dict(zip(sequential, range(len(sequential))), **named)
#    return type('Enum', (), enums)

#Inputs = enum('DOWN','DOWNRIGHT','RIGHT','UPRIGHT','UP','UPLEFT','LEFT','DOWNLEFT', 'TERMINAL')

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

def convertTextToCode(line):
    nums = []
    tempNum = ''
    for i in range(len(line)):
        if line[i] == ',' or line[i] == '\n':
            nums.append(int(tempNum))
            tempNum = ''
        else:
            tempNum += line[i]

    return (nums[0], nums[1], nums[2], nums[3])

class Move():
    def __init__(self, moveName, inputs, animation, hitboxes):
        self.name = moveName
        self.inputs = inputs
        self.animation = animation
        self.hitboxes = []
        for i in hitboxes:
            self.hitboxes.append(Rect(i))
        self.animationFrame = 0
        self.done = False
        
    def nextFrame(self):
        returnedImage = self.animation[self.animationFrame]
        returnedHitBox = self.hitboxes[self.animationFrame]
        self.animationFrame += 1
        if self.animationFrame >= len(self.animation):
            self.done = True
        return returnedImage, returnedHitBox
    
    def initialize(self):
        self.done = False
        self.animationFrame = 0

class Character(pygame.sprite.Sprite):
    """ Class holds all info on a Character and interprets it's actions """
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.meters = []
        self.health = 0
        self.velocity = [0,0]
        self.hitStun = 0
        self.curAnimation = []
        self.state = 'neutral'
        self.curAnimationFrame = 0
        self.curMove = None
        self.keysDown = []
        self.curHurtBox = pygame.Rect(x, y, 66, 96)
        self.facingLeft = False
        sourceFile = open('datafile.txt')
        self.moveList = {}
        #Read all the data from the file
        while True:
            i = sourceFile.readline()
            tempAnimation = []
            if i == 'neutral\n':
                i = sourceFile.readline()
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.neutralAnimation = load_animation('RyuSFA3.png', tempAnimation)

            if i == 'walkingForward\n':
                i = sourceFile.readline()
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.walkforwardAnimation = load_animation('RyuSFA3.png', tempAnimation)
            if i == 'normalMove\n':
                moveName = sourceFile.readline()
                moveName = moveName[:-1]
                moveInput = sourceFile.readline()
                i = sourceFile.readline()
                # read in animation
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                #read in hitboxes
                hitBoxCoords = []
                i = sourceFile.readline()
                while i != '&\n':
                    hitBoxCoords.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.moveList[moveName] = Move(moveName, moveInput, load_animation('RyuSFA3.png', tempAnimation), hitBoxCoords)    
            if i == 'crouch\n':
                self.crouchAnimation = load_animation('RyuSFA3.png', [convertTextToCode(sourceFile.readline())])
            if i == 'hit\n':
                i = sourceFile.readline()
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.hitAnimation = load_animation('RyuSFA3.png', tempAnimation)
            if i == '@':
                break
        self.curAnimation = self.neutralAnimation
        self.inputChain = [] # Keeps track of inputs for interpretting
        self.blockImage = None

    def update(self, gameState):
        self.interpretInputs()
        if self.curMove is None and self.hitStun == 0:
            self.curHurtBox.x += self.velocity[0]
            self.curAnimationFrame += 1
            if self.curAnimationFrame >= len(self.curAnimation): #Will need some more complicated parsing for state here later
                self.curAnimationFrame = 0
        elif self.hitStun:
            self.hitStun -= 1
            if self.hitStun <= 0:
                self.state = 'neutral'
                self.curAnimation = self.neutralAnimation
                self.curAnimationFrame = 0

    def keyPressed(self, state, button):
        if state is True:
            if button == K_RIGHT:
                self.keysDown.append('RIGHT')
                self.curAnimation = self.walkforwardAnimation
                self.curAnimationFrame = 0
                self.inputChain.append('RIGHT')
            if button == K_LEFT:
                self.keysDown.append('LEFT')
            if button == K_DOWN:
                self.keysDown.append('DOWN')
                self.curAnimation = self.crouchAnimation
                self.curAnimationFrame = 0
                self.inputChain.append('DOWN')
            if button == K_a:
                self.inputChain.append('JAB')
            if button == K_s:
                self.getHit(10)
        else:
            if button == K_RIGHT:
                del self.keysDown[self.keysDown.index('RIGHT')]
                self.curAnimation = self.neutralAnimation
            if button == K_LEFT:
                del self.keysDown[self.keysDown.index('LEFT')]
            if button == K_DOWN:
                del self.keysDown[self.keysDown.index('DOWN')]
                self.curAnimation = self.neutralAnimation
                

    def interpretInputs(self):
        if len(self.inputChain): #and self.moveList.get(self.inputChain[-1]) is not None:
            if self.inputChain[-1] == 'JAB':
                if ",".join(self.inputChain[-3:]) == 'DOWN,RIGHT,JAB':
                    print "hadoken"
                else:
                    self.curMove = self.moveList.get(self.inputChain[-1])
                    self.curMove.initialize()
                del self.inputChain[:]
        if 'DOWN' in self.keysDown:
            self.velocity[0]= 0
        elif 'RIGHT' in self.keysDown:
            self.velocity[0] = 1
        elif 'LEFT' in self.keysDown:
            self.velocity[0] = -1
        else:
            self.velocity[0] = 0

    def getHit(self, hitStun):
        self.curAnimation = self.hitAnimation
        self.curAnimationFrame = 0
        self.hitStun = 10
        self.state = 'hit'

    def currentFrame(self):
        if self.curMove is None:
                return pygame.transform.flip(self.curAnimation[self.curAnimationFrame], self.facingLeft, False), Rect(-1000,0,0,0)
        else:
            returnVal, curHitBox = self.curMove.nextFrame()
            if self.curMove.done:
                self.curMove = None
                self.curAnimation = self.neutralAnimation
            curHitBox = curHitBox.move(self.curHurtBox.x, self.curHurtBox.y)
            return pygame.transform.flip(returnVal, self.facingLeft, False), curHitBox

class CombatManager():
    """ Class for managing collisions, inputs, gamestate, etc. """
    def __init__(self):
        self.player1 = Character(300,200)
        self.player2 = Character (600,200)
        self.player1HitBox = Rect(-1000,0,0,0)
        self.player2HitBox = None

    def update(self):
        if self.player1.curHurtBox.x >= self.player2.curHurtBox.x:
            self.player1.facingLeft = True
            self.player2.facingLeft = False
        else:
            self.player1.facingLeft = False
            self.player2.facingLeft = True
        self.checkCollisions()
        self.updateCharacters()

    def checkCollisions(self):
        if self.player2.curHurtBox.colliderect(self.player1HitBox):
            self.player2.getHit(10)

    def updateCharacters(self):
        self.player1.update(None)
        self.player2.update(None)

    def drawPlayers(self, screen):
        player1Frame, self.player1HitBox = self.player1.currentFrame()
        player2Frame, self.player2HitBox = self.player2.currentFrame()
        screen.blit(player1Frame, self.player1.curHurtBox.topleft)
        screen.blit(player2Frame, self.player2.curHurtBox.topleft)

    def keyPressed(self, down, key):
        self.player1.keyPressed(down, key)

def main():
    
    #Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((1000, 300))
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
    #player1 = Character()
    combatManager = CombatManager()   
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
                    combatManager.keyPressed(True, event.key)
            elif event.type == KEYUP:
                combatManager.keyPressed(False, event.key)
        combatManager.update()
        screen.blit(background, (0,0))
        combatManager.drawPlayers(screen)
        pygame.display.flip()

if __name__ == '__main__':
    main()
