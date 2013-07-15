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
    return tuple(nums)

class HitBox(pygame.Rect):
    def __init__(self, dimensions, properties):
        pygame.Rect.__init__(self,dimensions)
        #Fill this out depending on your game
        self.damage = properties[damage]
        self.hitStun = properties[hitStun]
        self.knockBack = properties[knockBack]

class Move():
    def __init__(self, moveName, inputs, animation, hitboxes, properties):
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
    def __init__(self, x, y, inputs, facingRight):
        pygame.sprite.Sprite.__init__(self)
        self.meters = []
        self.health = 0
        self.velocity = [0,0]
        self.grounded = True
        self.hitStun = 0
        self.curAnimation = []
        self.state = 'neutral'
        self.curAnimationFrame = 0
        self.curMove = None
        self.keysDown = []
        self.curHurtBox = pygame.Rect(x, y, 66, 96)
        self.facingRight = facingRight
        self.inputs = inputs
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
            if i == 'standingBlock\n':
                    self.blockAnimation = load_animation('RyuSFA3.png', [convertTextToCode(sourceFile.readline())])
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
                stats = convertTextToCode(sourceFile.readline())
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
                self.moveList[moveName] = Move(moveName, moveInput, load_animation('RyuSFA3.png', tempAnimation), hitBoxCoords, stats)    
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
        self.interpretInputs(gameState)
        if self.state == 'blocking' and gameState != 'attacking':
            self.state = 'neutral'
            self.curAnimation = self.neutralAnimation
            self.curAnimationFrame = 0
        elif self.state == 'blocking':
            self.curAnimation = self.blockAnimation
        if self.curMove is None and self.hitStun == 0:
            self.curHurtBox.x += self.velocity[0]
            if not self.grounded:
                self.curHurtBox.y += self.velocity[1]
                self.velocity[1] += 1
                if self.curHurtBox.bottom >= 300:
                    self.curHurtBox.bottom = 300
                    self.grounded = True
            self.curAnimationFrame += 1
            if self.curAnimationFrame >= len(self.curAnimation): #Will need some more complicated parsing for state here later
                self.curAnimationFrame = 0
        elif self.hitStun:
            self.hitStun -= 1
            if self.hitStun <= 0:
                self.state = 'neutral'
                self.curAnimation = self.neutralAnimation
                self.curAnimationFrame = 0

    def keyPressed(self, state, pressedButton):
        # If Keys pushed down
        if pressedButton in self.inputs:
            button = self.inputs.get(pressedButton)
        else:
            return
        if state is True:
            if button == 'RIGHT':
                if self.facingRight:
                    if 'DOWN' in self.keysDown:
                        self.inputChain.append('DOWNTOWARD')
                        self.keysDown.append('TOWARD')
                    else:
                        self.keysDown.append('TOWARD')
                        self.curAnimation = self.walkforwardAnimation
                        self.curAnimationFrame = 0
                        self.inputChain.append('TOWARD')
                else:
                    if 'DOWN' in self.keysDown:
                        self.inputChain.append('DOWNBACK')
                        self.keysDown.append('BACK')
                    else:
                        self.keysDown.append('BACK')
                        #put walkbackwards animation in here
                        #self.curAnimation = self.walkBackwardAnimation
                        #self.curAnimationFrame = 0
                        self.inputChain.append('BACK')
            if button == 'LEFT':
                self.keysDown.append('BACK')
            if button == 'DOWN':
                if 'TOWARD' in self.keysDown:
                    self.inputChain.append('DOWNTOWARD')
                    self.keysDown.append('DOWN')
                else:
                    self.keysDown.append('DOWN')
                    self.curAnimation = self.crouchAnimation
                    self.curAnimationFrame = 0
                    self.inputChain.append('DOWN')
            if button == 'JAB':
                self.inputChain.append('JAB')
            if button == K_s:
                self.curAnimation = self.blockAnimation
            if button == 'UP':
                self.velocity[1] = -11
                self.grounded = False
        # On button release
        else:
            if button == 'RIGHT':
                del self.keysDown[self.keysDown.index('TOWARD')]
                self.curAnimation = self.neutralAnimation
            if button == 'LEFT':
                del self.keysDown[self.keysDown.index('BACK')]
            if button == 'DOWN':
                del self.keysDown[self.keysDown.index('DOWN')]
                if 'TOWARD' in self.keysDown:
                    self.inputChain.append('TOWARD')
                self.curAnimation = self.neutralAnimation
                

    def interpretInputs(self, gameState):
        if len(self.inputChain):
            if self.inputChain[-1] == 'JAB':
                self.state = 'attacking'
                if ",".join(self.inputChain[-4:]) == 'DOWN,DOWNTOWARD,TOWARD,JAB':
                    print "hadoken"
                else:
                    print self.inputChain[-4:]
                    self.curMove = self.moveList.get(self.inputChain[-1])
                    self.curMove.initialize()
                del self.inputChain[:]
        if 'DOWN' in self.keysDown:
            self.velocity[0]= 0
        elif 'TOWARD' in self.keysDown:
            if self.facingRight: self.velocity[0] = 10
            else: self.velocity[0] = -10
        elif 'BACK' in self.keysDown:
            if gameState is 'attacking':
                self.state = 'blocking'
            elif self.facingRight: self.velocity[0] = -10
            else: self.velocity[0] = 10
            
        else:
            self.velocity[0] = 0

    def getHit(self, hitStun):
        self.curAnimation = self.hitAnimation
        self.curAnimationFrame = 0
        self.hitStun = 10
        self.state = 'hit'

    def currentFrame(self):
        if self.curMove is None:
                return pygame.transform.flip(self.curAnimation[self.curAnimationFrame], not self.facingRight, False), Rect(-1000,0,0,0)
        else:
            returnVal, curHitBox = self.curMove.nextFrame()
            if self.curMove.done:
                self.curMove = None
                self.curAnimation = self.neutralAnimation
                self.state = 'neutral'
            curHitBox = curHitBox.move(self.curHurtBox.x, self.curHurtBox.y)
            return pygame.transform.flip(returnVal, not self.facingRight, False), curHitBox

class CombatManager():
    """ Class for managing collisions, inputs, gamestate, etc. """
    def __init__(self):
        player1InputKeys = {K_a: 'JAB', K_UP: 'UP', K_RIGHT: 'RIGHT', K_DOWN: 'DOWN', \
                            K_LEFT: 'LEFT'}
        player2InputKeys = {K_u: 'JAB'}
        self.player1 = Character(300,200, player1InputKeys, True)
        self.player2 = Character (600,200, player2InputKeys, False)
        self.player1HitBox = Rect(-1000,0,0,0)
        self.player2HitBox = Rect(-1000,0,0,0)

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
        if self.player1.curHurtBox.colliderect(self.player2HitBox):
            self.player1.getHit(10)

    def updateCharacters(self):
        self.player1.update(self.player2.state)
        self.player2.update(self.player1.state)

    def drawPlayers(self, screen):
        player1Frame, self.player1HitBox = self.player1.currentFrame()
        player2Frame, self.player2HitBox = self.player2.currentFrame()
        screen.blit(player1Frame, self.player1.curHurtBox.topleft)
        screen.blit(player2Frame, self.player2.curHurtBox.topleft)

    def keyPressed(self, down, key):
        self.player1.keyPressed(down, key)
        self.player2.keyPressed(down, key)

def main():
    
    #Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((1000, 300))
    pygame.mouse.set_visible(0)

    #Create the background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

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
