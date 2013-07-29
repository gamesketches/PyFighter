import pygame, sys, os, character
from pygame.locals import *

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

main_dir = os.path.split(os.path.abspath(sys.argv[0]))[0]
data_dir = os.path.join(main_dir, 'data')

projectiles = []

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
    master_image, master_rect = load_image(filename, -1)
    theAnimation = []
    for i in coords:
        theAnimation.append(master_image.subsurface(i))

    return theAnimation

def towardsZero(num, interval):
    if num > 0:
        num -= interval
        if num < 0:
            return 0
    else:
        num += interval
        if num > 0:
            return 0
    return num

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

class Meter():
    def __init__(self,dimensions,barColor,frameColor,startingAmount, maxAmount,isPlayerOne):
        self.frame = pygame.Surface((dimensions[2],dimensions[3]))
        self.frame.fill(frameColor)
        self.barHeight = dimensions[3] *0.8
        self.barColor = barColor
        self.bar = pygame.Surface((dimensions[2] * 0.95, self.barHeight))
        self.bar.fill(barColor)
        self.isPlayerOne = isPlayerOne
        self.perPixel = self.bar.get_width() / (maxAmount + 0.0)
        self.update(startingAmount)
        self.x = dimensions[0]
        self.y = dimensions[1]
        self.isPlayerOne = isPlayerOne

    def update(self,amount):
        self.bar = pygame.Surface((self.perPixel * amount, self.barHeight))

    def draw(self,screen):
        screen.blit(self.frame, (self.x, self.y))                
        screen.blit(self.bar, (self.frame.get_width() * 0.975 - self.bar.get_width(), self.frame.get_height() * 0.1))

class HitBox(pygame.Rect):
    def __init__(self, dimensions=(-1000,0,0,0), properties={'damage':0,'hitstun':0,'knockback':0, 'knockdown':False,'blocktype':'mid'}):
        pygame.Rect.__init__(self,dimensions)
        #Fill this out depending on your game
        self.damage = properties['damage']
        self.hitStun = properties['hitstun']
        self.knockBack = properties['knockback']
        self.blockType = properties['blocktype']
        self.knockDown = properties['knockdown']

    def getProperties(self):
        if self.blockType is 'throw':
            return (self.damage, self.x, self.y, self.knockDown, self.blockType)
        else:
            return (self.damage, self.hitStun, self.knockBack, self.knockDown, self.blockType)

    def adjustHitBox(self, x, y):
        # Shenanigans because pygame.Rect.move returns a rect :\
        tempRect = self.move(x - self.x,y - self.y)
        self.x = tempRect.x
        self.y = tempRect.y

class Projectile(pygame.sprite.Sprite):
    def __init__(self, animation, hitBox, velocity, owner):
        self.animation = animation
        self.hitBox = HitBox(hitBox, {'damage':0,'hitstun':10,'knockback':1,'knockdown':False,'blocktype':'mid'})
        self.velocity = velocity
        self.curAnimationFrame = 0
        self.image = self.animation[self.curAnimationFrame]
        projectiles.append(self)

    def update(self):
        self.calcNewPos()
        self.image = self.animation[self.curAnimationFrame]
        self.curAnimationFrame += 1
        if self.curAnimationFrame >= len(self.animation):
            self.curAnimationFrame = 0

    def calcNewPos(self):
        self.hitBox.x += 10

    def kill(self):
        del self
        

class Move():
    def __init__(self, moveName, inputs, animation, hitboxes, properties, velocities, state):
        self.name = moveName
        self.inputs = inputs
        self.animation = animation
        self.hitboxes = []
        self.velocities = velocities
        self.state = state
        for i in hitboxes:
            self.hitboxes.append(HitBox(i,properties))
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

    def getVelocities(self, facingRight):
        if facingRight:
            return self.velocities[self.animationFrame][0], self.velocities[self.animationFrame][1]
        else:
            return self.velocities[self.animationFrame][0] * -1, self.velocities[self.animationFrame][1] * -1

class Character(pygame.sprite.Sprite):
    """ Class holds all info on a Character and interprets it's actions """
    def __init__(self, x, y, inputs, facingRight):
        pygame.sprite.Sprite.__init__(self)
        self.healthMeter = Meter((0,0,400,30),(150,150,0),(0,0,200),400,400,facingRight)
        self.health = 400
        self.velocity = [0,0]
        self.grounded = True
        self.hitStun = 0
        self.curAnimation = []
        self.state = 'standing'
        self.neutralAnimations = {}
        self.blockAnimations = {}
        self.curAnimationFrame = 0
        self.curMove = None
        self.keysDown = []
        self.curHurtBox = pygame.Rect(x, y, 66, 96)
        self.facingRight = facingRight
        self.inputs = inputs
        sourceFile = open('datafile.txt')
        self.moveList= {}
        #Read all the data from the file
        while True:
            i = sourceFile.readline()
            tempAnimation = []
            if i == '@':
                break
            if i == 'standing\n':
                i = sourceFile.readline()
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.neutralAnimations['standing'] = load_animation('RyuSFA3.png', tempAnimation)
                i = sourceFile.readline()
                tempAnimation = []
                tempMoveList = {}
                while i != '@\n':
                    if i == 'normalMove\n':
                        self.loadNormalMove(sourceFile,tempMoveList,'standing')
                    if i == 'block\n':
                        self.blockAnimations['standing'] = load_animation('RyuSFA3.png', [convertTextToCode(sourceFile.readline())])
                    i = sourceFile.readline()
                self.moveList['standing'] = tempMoveList
            if i == 'walkingForward\n':
                i = sourceFile.readline()
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.walkforwardAnimation = load_animation('RyuSFA3.png', tempAnimation)
            if i == 'knockDown\n':
                i = sourceFile.readline()
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.knockDownAnimation = load_animation('RyuSFA3.png', tempAnimation)
            if i == 'crouch\n':
                self.neutralAnimations['crouching'] = load_animation('RyuSFA3.png', [convertTextToCode(sourceFile.readline())])
                i = sourceFile.readline()
                tempAnimation = []
                tempMoveList = {}
                while i != '@\n':
                    if i == 'normalMove\n':
                        self.loadNormalMove(sourceFile,tempMoveList,'crouching')
                    if i == 'block\n':
                        self.blockAnimations['crouching'] = load_animation('RyuSFA3.png', [convertTextToCode(sourceFile.readline())])
                    #for i in self.crouchingMoveList.items():
                    #    self.crouchingMoveList[i].state = 'crouching'
                    i = sourceFile.readline()
                self.moveList['crouching'] = tempMoveList
            if i == 'hit\n':
                i = sourceFile.readline()
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.hitAnimation = load_animation('RyuSFA3.png', tempAnimation)
            if i == 'thrown\n':
                i = sourceFile.readline()
                while i != '&\n':
                    tempAnimation.append(convertTextToCode(i))
                    i = sourceFile.readline()
                self.getThrown = Move("getThrown", "getThrown", load_animation('RyuSFA3.png', tempAnimation), [(0,0,0,0)],{'damage':0,'hitstun':0,'knockback':0, 'knockdown':False,'blocktype':'mid'}, [(-10,-10)], 'knockedDown')
        self.curAnimation = self.neutralAnimations['standing']
        self.inputChain = [] # Keeps track of inputs for interpretting
        self.blockImage = None

    def loadNormalMove(self,sourceFile,moveList, state):
        tempAnimation = []
        moveName = sourceFile.readline()
        moveName = moveName[:-1]
        moveInput = sourceFile.readline()
        tempProperties = convertTextToCode(sourceFile.readline())
        blockType = sourceFile.readline()[:-1]
        properties = {'damage':tempProperties[0], 'hitstun':tempProperties[1],'knockback':tempProperties[2], 'knockdown': tempProperties[3],'blocktype': blockType}
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
        # read in velocities
        velocityCoords = []
        i = sourceFile.readline()
        while i != '&\n':
            velocityCoords.append(convertTextToCode(i))
            i = sourceFile.readline()
        moveList[moveName] = Move(moveName, moveInput, load_animation('RyuSFA3.png', tempAnimation), hitBoxCoords, properties, velocityCoords, state)
        

    def update(self, gameState):
        if self.hitStun and self.state != 'knockedDown':
            self.hitStun -= 1
            self.curHurtBox.x += self.velocity[0]
            self.velocity[0] = towardsZero(self.velocity[0], 1)
            if self.hitStun <= 0:
                self.state = 'standing'
                self.curAnimation = self.neutralAnimations[self.state]
                self.curAnimationFrame = 0
        elif self.hitStun and self.state == 'knockedDown':
            if self.curHurtBox.bottom >= 300:
                self.curHurtBox.bottom = 300
                self.velocity[0] = 0
                self.hitStun -= 1
                if self.hitStun <= 0:
                    self.state = 'standing'
                    self.curAnimation = self.neutralAnimations[self.state]
                    self.curAnimationFrame = 0
            else:
                self.curHurtBox.y += 5
                self.curHurtBox.x += self.velocity[0]
        else:
            self.interpretInputs(gameState)
            #If opponent is not attacking, return to neutral
            if self.state == 'standBlocking' and gameState != 'attacking':
                self.state = 'standing'
                self.curAnimation = self.neutralAnimations[self.state]
                self.curAnimationFrame = 0
            elif self.state == 'crouchBlocking' and gameState != 'attacking':
                self.state = 'crouching'
                self.curAnimation = self.neutralAnimations[self.state]
                self.curAnimationFrame = 0
            # If opponent is attacking and you're holding back
            elif self.state == 'blocking':
                self.curAnimation = self.blockAnimations['standing']
                self.curAnimationFrame = 0
            # Pre-jump, transition to jumping frames
            if self.state == 'prejump':
                if self.curAnimationFrame >= 3:
                    self.grounded = False
                    self.state = 'jumping'
                self.curAnimationFrame += 1
            if self.state == 'jumping':
                self.curHurtBox.y += self.velocity[1]
                self.curHurtBox.x += self.velocity[0]
                self.velocity[1] += 1
                if self.curHurtBox.bottom >= 300:
                    self.curHurtBox.bottom = 300
                    self.grounded = True
                    self.state = 'standing'
            #If you are just walking
            if self.state == 'standing':
                self.curHurtBox.y = 300 - self.curAnimation[0].get_height()
                self.curHurtBox.x += self.velocity[0]
                self.curAnimationFrame += 1
                if self.curAnimationFrame >= len(self.curAnimation): #Will need some more complicated parsing for state here later
                    self.curAnimationFrame = 0
            #elif self.state == 'crouching':
                #self.curHurtBox.y = 300 - self.curHurtBox.h
                #print ""

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
            elif button == 'LEFT':
                if self.facingRight:
                    if 'DOWN' in self.keysDown:
                        self.inputChain.append('DOWNBACK')
                        print "Downback"
                        self.keysDown.append('BACK')
                    else:
                        self.keysDown.append('BACK')
                        #put walkbackwards animation in here
                        #self.curAnimation = self.walkBackwardAnimation
                        #self.curAnimationFrame = 0
                        self.inputChain.append('BACK')
                else:
                    if 'DOWN' in self.keysDown:
                        self.inputChain.append('DOWNTOWARD')
                        self.keysDown.append('TOWARD')
                    else:
                        self.keysDown.append('TOWARD')
                        self.curAnimation = self.walkforwardAnimation
                        self.curAnimationFrame = 0
                        self.inputChain.append('TOWARD')
            elif button == 'DOWN':
                if 'TOWARD' in self.keysDown:
                    self.inputChain.append('DOWNTOWARD')
                    self.keysDown.append('DOWN')
                elif 'BACK' in self.keysDown:
                    self.inputChain.append('DOWNBACK')
                    self.keysDown.append('DOWN')
                else:
                    self.keysDown.append('DOWN')
                    self.state = 'crouching'
                    self.curAnimation = self.neutralAnimations['crouching']
                    self.curAnimationFrame = 0
                    self.curHurtBox.y = 300 - self.neutralAnimations['crouching'][0].get_height()
                    self.inputChain.append('DOWN')
            elif button == 'UP':
                self.state = 'prejump'
                self.curAnimationFrame = 0
                self.velocity[1] = -11
            # This handles all other inputs
            elif button in self.inputs.values():
                self.inputChain.append(button)
        # On button release
        else:
            if button == 'RIGHT':
                if self.facingRight:
                    del self.keysDown[self.keysDown.index('TOWARD')]
                    self.curAnimation = self.neutralAnimations['standing']
                else:
                    del self.keysDown[self.keysDown.index('BACK')]
                    self.curAnimation = self.neutralAnimations['standing']
            if button == 'LEFT':
                if self.facingRight:
                    del self.keysDown[self.keysDown.index('BACK')]
                    self.curAnimation = self.neutralAnimations['standing']
                else:
                    del self.keysDown[self.keysDown.index('TOWARD')]
                    self.curAnimation = self.neutralAnimations['standing']
            if button == 'DOWN':
                del self.keysDown[self.keysDown.index('DOWN')]
                self.state = 'standing'
                if 'TOWARD' in self.keysDown:
                    self.inputChain.append('TOWARD')
                self.curAnimation = self.neutralAnimations['standing']

    def switchSides(self):
        if 'TOWARD' in self.keysDown:
            del self.keysDown[self.keysDown.index('TOWARD')]
            self.keysDown.append('BACK')
        if 'BACK' in self.keysDown:
            del self.keysDown[self.keysDown.index('BACK')]
            self.keysDown.append('TOWARD')
        self.facingRight = not self.facingRight
                

    def interpretInputs(self, gameState):
        if len(self.inputChain):
            if self.inputChain[-1] == 'JAB':
                if ",".join(self.inputChain[-4:]) == 'DOWN,DOWNTOWARD,TOWARD,JAB':
                    Projectile(load_animation('RyuSFA3.png', [(541,3109,73,38)]), HitBox((self.curHurtBox.x, self.curHurtBox.y, 73, 38)), 10, 'p1')
                    # These two lines are just to stop Ryu from crashing.
                    # #They should be removed once special moves are properly implemented
                    self.curMove = self.moveList[self.state].get(self.inputChain[-1])
                    self.curMove.initialize()
                else:
                    self.curMove = self.moveList[self.state].get(self.inputChain[-1])
                    self.curMove.initialize()
                del self.inputChain[:]
                self.state = 'attacking'
            elif self.inputChain[-1] == 'FIERCE':
                self.curMove = self.moveList[self.state].get(self.inputChain[-1])
                self.curMove.initialize()
                del self.inputChain[:]
                self.state = 'attacking'
            elif self.inputChain[-1] == 'THROW':
                self.curMove = self.moveList[self.state].get(self.inputChain[-1])
                self.curMove.initialize()
                del self.inputChain[:]
                self.state = 'attacking'
        if 'TOWARD' in self.keysDown:
            if self.facingRight: self.velocity[0] = 10
            else: self.velocity[0] = -10
        elif 'BACK' in self.keysDown:
            if gameState is 'attacking':
                if 'DOWN' in self.keysDown:
                    self.curAnimation = self.blockAnimations['crouching']
                    self.state = 'crouchBlocking'
                    self.curAnimationFrame = 0
                else:
                    self.curAnimation = self.blockAnimations['standing']
                    self.state = 'standBlocking'
                    self.curAnimationFrame = 0
            elif self.facingRight: self.velocity[0] = -10
            else: self.velocity[0] = 10
        elif 'DOWN' in self.keysDown:
            self.velocity[0] = 0
            
        elif self.state != 'prejump' and self.state != 'jumping':
            self.velocity[0] = 0

    def checkHit(self, properties):
        if self.state == 'standBlocking':
            if properties[3] == 'mid' or properties[3] == 'high':
                if self.facingRight:
                    self.velocity[0] = properties[2] * - 0.2
                else:
                    self.velocity[0] = properties[2] * 0.2
            else:
                self.getHit(properties)
        elif self.state == 'crouchBlocking':
            if properties.blockType == 'mid' or properties.blockType == 'low':
                if self.facingRight:
                    self.velocity[0] = properties[2] * - 0.2
                else:
                    self.velocity[0] = properties[2] * 0.2
        if properties[4] == 'throw':
            self.state = 'thrown'
            self.curMove = self.getThrown
            #self.curHurtBox.x += properties[1]
            #self.curHurtBox.y += properties[2]
        else:
            print properties
            self.getHit(properties)
            
    def getHit(self, properties):
        self.curMove = None
        if not properties[3]:    
            self.curAnimation = self.hitAnimation
            self.curAnimationFrame = 0
            #Put in damage here
            self.hitStun = properties[1]
            self.state = 'hit'
        else:
            self.curAnimation = self.knockDownAnimation
            self.curAnimationFrame = 0
            self.curHurtBox.h = self.knockDownAnimation[0].get_height()
            self.hitStun = 50
            self.state = 'knockedDown'
        if self.facingRight:
            self.velocity[0] = properties[2] * -1
        else:
            self.velocity[0] = properties[2]

    def currentFrame(self):
        if self.curMove is None:
                return pygame.transform.flip(self.curAnimation[self.curAnimationFrame], not self.facingRight, False), HitBox()
        else:
            xOffset, yOffset = self.curMove.getVelocities(self.facingRight)
            self.curHurtBox.x += xOffset
            self.curHurtBox.y += yOffset
            returnVal, curHitBox = self.curMove.nextFrame()
            if self.curMove.done:
                self.state = self.curMove.state
                self.curMove = None
                if self.state == 'knockedDown':
                    self.curAnimation = self.knockDownAnimation
                    self.hitStun = 100
                    self.curHurtBox.h = self.knockDownAnimation[0].get_height()
                    if self.facingRight:
                        self.velocity[0] = 10
                    else:
                        self.velocity[0] = -10
                else:
                    self.curAnimation = self.neutralAnimations[self.state]
                self.curAnimationFrame = 0
            curHitBox.adjustHitBox(self.curHurtBox.x + self.curHurtBox.w, self.curHurtBox.y)
            return pygame.transform.flip(returnVal, not self.facingRight, False), curHitBox

class CombatManager():
    """ Class for managing collisions, inputs, gamestate, etc. """
    def __init__(self):
        player1InputKeys = {K_a: 'JAB', K_s:'FIERCE', K_d:'THROW', K_UP: 'UP', K_RIGHT: 'RIGHT', K_DOWN: 'DOWN', \
                            K_LEFT: 'LEFT'}
        player2InputKeys = {K_u: 'JAB', K_i: 'RIGHT'}
        self.player1 = Character(300,200, player1InputKeys, True)
        self.player2 = Character (600,200, player2InputKeys, False)
        self.player1HitBox = HitBox()
        self.player2HitBox = HitBox()

    def update(self):
        if self.player1.curHurtBox.x >= self.player2.curHurtBox.x and self.player1.facingRight:
            self.player1.switchSides()
            self.player2.switchSides()
        elif self.player1.curHurtBox.x < self.player2.curHurtBox.x and self.player2.facingRight:
            self.player1.switchSides()
            self.player2.switchSides()
        self.checkCollisions()
        self.updateCharacters()

    def checkCollisions(self):
        # Handle attack collisions
        if self.player2.curHurtBox.colliderect(self.player1HitBox):
            self.player2.checkHit(self.player1HitBox.getProperties())
        if self.player1.curHurtBox.colliderect(self.player2HitBox):
            self.player1.checkHit(self.player2HitBox.getProperties())
        # Handle players walking into each other
        if self.player2.curHurtBox.colliderect(self.player1.curHurtBox) and self.player2.velocity[0] == 0:
            self.player2.curHurtBox.x += self.player1.velocity[0]
        if self.player1.curHurtBox.colliderect(self.player2.curHurtBox) and self.player1.velocity[0] == 0:
            self.player1.curHurtBox.x += self.player2.velocity[0]
        # Handle projectile collisions
        for i in projectiles:
            if self.player2.curHurtBox.colliderect(i.hitBox):
                self.player2.checkHit(i.hitBox.getProperties())
                projectiles.remove(i)
            if self.player1.curHurtBox.colliderect(i.hitBox):
                self.player1.checkHit(i.hitBox.getProperties())

    def updateCharacters(self):
        self.player1.update(self.player2.state)
        self.player2.update(self.player1.state)
        for i in projectiles:
            i.update()

    def drawPlayers(self, screen):
        player1Frame, self.player1HitBox = self.player1.currentFrame()
        player2Frame, self.player2HitBox = self.player2.currentFrame()
        screen.blit(player1Frame, self.player1.curHurtBox.topleft)
        screen.blit(player2Frame, self.player2.curHurtBox.topleft)
        for i in projectiles:
            screen.blit(i.image, (i.hitBox.x, i.hitBox.y))
        self.player1.healthMeter.draw(screen)

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
