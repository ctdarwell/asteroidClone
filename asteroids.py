# asteroids!!!
import random, sys, time, math, pygame, numpy as np
from pygame.locals import *

FPS = 30 # frames per second to update the screen
WINWIDTH = 1400 # width of the program's window, in pixels
WINHEIGHT = 800 # height in pixels
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

PURPLE = (72, 0, 72)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = ( 0, 255, 0)
ORANGE = (255, 128, 0)

CAMERASLACK = 0 # how far player from center before moving the camera NOW CHANGED TO 0 FROM 90!!!!
ROTRATE = 6 # how fast the ship rotates
SHIPSPEED = 7 # ship speed
SHIPSIZE = 70 # how big the player starts off
INVULNTIME = 4 # how long the player is invulnerable after being hit in seconds
GAMEOVERTIME = 4 # how long the "game over" text stays on the screen in seconds
LIVES = 5 # how much health the player starts with
ORIENT = 90 # starting angle of ship
NUMPLANETS = 100 # number of planets in the active area
ROIDMINSPEED = 3 # slowestspeed
ROIDMAXSPEED = 7 # fastest speed
LEFT = 'left'
RIGHT = 'right'
PHOTON_SPEED = 15

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, PHOTON_IMG, PLANET_IMGS, SPACESHIP_IMG, ROID_IMGS, EXPLOSION_IMG

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))
    pygame.display.set_caption('Asteroids')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 32)

    # load the image files
    SPACESHIP_IMG = pygame.image.load('spaceship-png-icon-19.png')
    PHOTON_IMG = pygame.image.load('photon.png')
    EXPLOSION_IMG = pygame.image.load('explosion.png')

    PLANET_IMGS=[]
    for i in range(1, 11):
        PLANET_IMGS.append(pygame.image.load('cartoon_planet%s.png' % i))

    ROID_IMGS=[]
    for i in range(1, 5):
        ROID_IMGS.append(pygame.image.load('asteroid%s.png' % i))

    while True:
        runGame()

def runGame():
    # set up variables for the start of a new game
    HISCORE = load_state()
    canShoot = True
    noShootStartTime = 0
    invulnerableMode = False  # if the player is invulnerable
    invulnerableStartTime = 0 # time the player became invulnerable
    gameOverMode = False      # has the player lost
    gameOverStartTime = 0     # time the player lost
    NUMROIDS = 40 # number of asteroids in the active area
    NOSHOOTTIME = 0.25
    SCORE = 0
    SCORETHRESH =0 #counts multiples of 500 to incr difficulty
    ROIDINCR = False #switch off asteroid increase

    # create the surfaces if game lost
    gameOverSurf = BASICFONT.render('Game Over', True, WHITE)
    gameOverRect = gameOverSurf.get_rect()
    gameOverRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)

    winSurf2 = BASICFONT.render('(Press "r" to restart.)', True, WHITE)
    winRect2 = winSurf2.get_rect()
    winRect2.center = (HALF_WINWIDTH, HALF_WINHEIGHT + 30)

    # camerax and cameray are the top left of where the camera view is
    camerax = 0
    cameray = 0

    planetObjs = [] # stores all the planet objects in the game
    roidObjs = [] # stores all the asteroid objects
    photonObjs = []

    # stores the player object:
    playerObj = {'surface': pygame.transform.scale(SPACESHIP_IMG, (SHIPSIZE, SHIPSIZE)),
                 'x': HALF_WINWIDTH,
                 'y': HALF_WINHEIGHT,
                 'rotate': ORIENT,
                 'shipsize' : SHIPSIZE, # ISSUE HERE: NO SHIP WIDTH OR HT ONLY SIZE - see 3 lines above
                 'lives': LIVES} 
    # make collision object that tracks ship (has smaller rectangle so makes crashes more accurate)
    collisionObj = {'surface': pygame.transform.scale(SPACESHIP_IMG, (int(SHIPSIZE/2), int(SHIPSIZE/2))),
                 'x': HALF_WINWIDTH,
                 'y': HALF_WINHEIGHT,
                 'rotate': ORIENT,
                 'shipsize' : int(SHIPSIZE/2)}

    rotLeft  = False # was 'moveLeft'
    rotRight = False # was 'moveRight'
    moveFWD  = False # was 'moveUp'
    shoot    = False # was 'moveDown'

    # start off with some random planets on the screen
    for i in range(6):
        planetObjs.append(makeNewPlanets(camerax, cameray))
        planetObjs[i]['x'] = random.randint(0, WINWIDTH) #forces starting planets to appear in camera
        planetObjs[i]['y'] = random.randint(0, WINHEIGHT) #ie this is overwriting normal makeNewPlanets coords

    while True: #main game loop  - handles updates
        # Check if we should turn off invulnerability
        if invulnerableMode and time.time() - invulnerableStartTime > INVULNTIME:
            invulnerableMode = False

        # Check if we should permit photon fire
        if not canShoot and time.time() - noShootStartTime > NOSHOOTTIME:
            canShoot = True

        # move all the asteroids
        for roidObj in roidObjs:
            # move the asteroid
            roidObj['x'] += roidObj['movex']
            roidObj['y'] += roidObj['movey']

        # move photons
        for phObj in photonObjs:
            phObj['x'], phObj['y'] = moveObj(phObj['x'], phObj['y'], phObj['angle'], PHOTON_SPEED)

        # go through all the objects and see if any need to be deleted.
        for i in range(len(planetObjs) - 1, -1, -1): #GOES THRU LIST BACKWARDS SO "DEL" CALL HITS RIGHT OBJ
            if isOutsideActiveArea(camerax, cameray, planetObjs[i]):
                del planetObjs[i]
        for i in range(len(roidObjs) - 1, -1, -1):
            if isOutsideActiveArea(camerax, cameray, roidObjs[i]):
                del roidObjs[i]
        for i in range(len(photonObjs) - 1, -1, -1):
            if isOutsideActiveArea(camerax, cameray, photonObjs[i]):
                del photonObjs[i]

        # add more planets & asteroids if we don't have enough.
        while len(planetObjs) < NUMPLANETS:
            planetObjs.append(makeNewPlanets(camerax, cameray))
        while len(roidObjs) < NUMROIDS:
            roidObjs.append(makeNewRoids(camerax, cameray))

        # adjust camerax and cameray if beyond the "camera slack"
        playerCenterx = playerObj['x'] + int(playerObj['shipsize'] / 2)
        playerCentery = playerObj['y'] + int(playerObj['shipsize'] / 2)
        if (camerax + HALF_WINWIDTH) - playerCenterx > CAMERASLACK:
            camerax = playerCenterx + CAMERASLACK - HALF_WINWIDTH
        elif playerCenterx - (camerax + HALF_WINWIDTH) > CAMERASLACK:
            camerax = playerCenterx - CAMERASLACK - HALF_WINWIDTH
        if (cameray + HALF_WINHEIGHT) - playerCentery > CAMERASLACK:
            cameray = playerCentery + CAMERASLACK - HALF_WINHEIGHT
        elif playerCentery - (cameray + HALF_WINHEIGHT) > CAMERASLACK:
            cameray = playerCentery - CAMERASLACK - HALF_WINHEIGHT

        # draw the background
        DISPLAYSURF.fill(PURPLE)

        # draw all the planets on the screen
        for plObj in planetObjs:
            plRect = pygame.Rect( (plObj['x'] - camerax,
                                  plObj['y'] - cameray,
                                  plObj['width'],
                                  plObj['height']))
            DISPLAYSURF.blit(PLANET_IMGS[plObj['planetImage']], plRect)

        # draw the asteroids
        for roidObj in roidObjs:
            roidObj['rect'] = pygame.Rect( (roidObj['x'] - camerax,
                                  roidObj['y'] - cameray,
                                  roidObj['width'],
                                roidObj['height']) )
            DISPLAYSURF.blit(ROID_IMGS[roidObj['roidImage']], roidObj['rect'])

        # draw the photon
        for phObj in photonObjs:
            phObj['rect'] = pygame.Rect( (phObj['x'] - camerax,
                                  phObj['y'] - cameray,
                                  phObj['width'],
                                phObj['height']) )
            DISPLAYSURF.blit(phObj['photonImage'], phObj['rect'])

        # draw the player spaceship
        flashIsOn = round(time.time(), 1) * 10 % 2 == 1
        if not gameOverMode and not (invulnerableMode and flashIsOn):
            playerObj['rect'] = pygame.Rect( (playerObj['x'] - camerax,
                                              playerObj['y'] - cameray,
                                              playerObj['shipsize'],
                                              playerObj['shipsize']))
            rotatedSHIP = pygame.transform.rotate(playerObj['surface'], playerObj['rotate'] - 90)
            rotatedShipRECT = rotatedSHIP.get_rect()
            rotatedShipRECT.center = (HALF_WINWIDTH, HALF_WINHEIGHT)
            DISPLAYSURF.blit(rotatedSHIP, rotatedShipRECT)
            #now make it's reduced collision object
            collisionObj['rect'] = pygame.Rect( (playerObj['x'] - (camerax - int(collisionObj['shipsize']/2)), # centre the midpoint relative to its size
                                              playerObj['y'] - (cameray - int(collisionObj['shipsize']/2)),
                                              collisionObj['shipsize'],
                                              collisionObj['shipsize']))

        # draw the health meter
        drawHealthMeter(playerObj['lives'])
        # score
        drawScore(SCORE)
        drawHiScore(HISCORE)
        #increase amount of asteroids every 1000 points
        if ROIDINCR and (SCORE / 1000) > SCORETHRESH:
            SCORETHRESH += 1
            NUMROIDS += 10
            ROIDINCR = False
            if NOSHOOTTIME > 0.05: #REMOVE FOR NO SHOOT TIME INCREASE!!!!!!!!!!!!!!!!!!!!!
                NOSHOOTTIME -= 0.005

        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                terminate()

            elif event.type == KEYDOWN:
                if event.key in (K_UP, K_z):
                    moveFWD = True
                elif event.key in (K_DOWN, K_a):
                    shoot = True
                elif event.key in (K_LEFT, K_n):
                    rotRight = False
                    rotLeft = True
                elif event.key in (K_RIGHT, K_m):
                    rotLeft = False
                    rotRight = True

            elif event.type == KEYUP:
                # stop moving the player's ship
                if event.key in (K_LEFT, K_n):
                    rotLeft = False
                elif event.key in (K_RIGHT, K_m):
                    rotRight = False
                elif event.key in (K_UP, K_z):
                    moveFWD = False
                elif event.key in (K_DOWN, K_a):
                    shoot = False

                elif event.key == K_ESCAPE:
                    terminate()

        if not gameOverMode:
            # actually move the player
            if rotLeft:
                playerObj['rotate'] += ROTRATE
                playerObj['rotate'] = playerObj['rotate'] % 360 #maybe not necessary
            if rotRight:
                playerObj['rotate'] -= ROTRATE
                playerObj['rotate'] = playerObj['rotate'] % 360 #maybe not necessary
            if moveFWD:
                playerObj['x'], playerObj['y'] = moveObj(playerObj['x'], playerObj['y'], playerObj['rotate'], SHIPSPEED) # as moveFWD already pressed we know we need to calc movement
            if shoot and canShoot: # COULD MAXIMISE NO. OF PHOTONS
                photonObjs.append(makeNewPhotons(playerObj['x'] + int(SHIPSIZE/2), playerObj['y'] + int(SHIPSIZE/2), playerObj['rotate'])) # make a photon
                canShoot = False
                noShootStartTime = time.time()

            # check if the player has collided with any asteroids
            for i in range(len(roidObjs)-1, -1, -1):
                roidObj = roidObjs[i]
                if not invulnerableMode:
                    if 'rect' in roidObj and collisionObj['rect'].colliderect(roidObj['rect']): #I DON'T KNOW WHY HAVE "'rect' in roidObj" HERE
                        # a player/asteroid collision has occurred
                        playerObj['lives'] -= 1
                        invulnerableMode = True
                        invulnerableStartTime = time.time()
                        if playerObj['lives'] == 0:
                            gameOverMode = True # turn on "game over mode"
                            gameOverStartTime = time.time()

            # check if the player has shot any asteroids
            for i in range(len(photonObjs)-1, -1, -1):
                photonObj = photonObjs[i]
                for j in range(len(roidObjs)-1, -1, -1):
                    roidObj = roidObjs[j]
                    if photonObj['rect'].colliderect(roidObj['rect']):
                        roidObj['photonImage'] = EXPLOSION_IMG
                        DISPLAYSURF.blit(roidObj['photonImage'], roidObj['rect'])
                        try:
                            del photonObjs[i], roidObjs[j]
                        except IndexError:
                            del roidObjs[j]
                        ROIDINCR = True
                        if roidObj['width'] > 30:
                            for i in range(random.randint(1,3)):
                                roidObjs.append(makeSmallRoids(roidObj['x'], roidObj['y'])) #split up large asteroids
                            SCORE += 20
                        else:
                            SCORE += 100

        else:
            if SCORE > HISCORE:
                save_state(SCORE)
            # game is over, show "game over" text
            DISPLAYSURF.blit(gameOverSurf, gameOverRect)
            if time.time() - gameOverStartTime > GAMEOVERTIME:
                return # end the current game

        pygame.display.update() #update needed here to draw new surf (as always)

        pygame.display.update()
        FPSCLOCK.tick(FPS)

def getRandomOffCameraPos(camerax, cameray, objWidth, objHeight):
    # create a Rect of the camera view
    cameraRect = pygame.Rect(camerax, cameray, WINWIDTH, WINHEIGHT)
    while True:
        x = random.randint(camerax - WINWIDTH, camerax + (2 * WINWIDTH))
        y = random.randint(cameray - WINHEIGHT, cameray + (2 * WINHEIGHT))
        # create a Rect object with the random coordinates and use colliderect()
        # to make sure the right edge isn't in the camera view.
        objRect = pygame.Rect(x, y, objWidth, objHeight)
        if not objRect.colliderect(cameraRect):
            return x, y

def makeNewPlanets(camerax, cameray):
    pl = {}
    pl['planetImage'] = random.randint(0, len(PLANET_IMGS) - 1)
    pl['width']  = PLANET_IMGS[0].get_width()
    pl['height'] = PLANET_IMGS[0].get_height()
    pl['x'], pl['y'] = getRandomOffCameraPos(camerax, cameray, pl['width'], pl['height'])
    pl['rect'] = pygame.Rect( (pl['x'], pl['y'], pl['width'], pl['height']) )
    return pl

def makeNewRoids(camerax, cameray):
    rd = {}
    rd['roidImage'] = random.randint(0, len(ROID_IMGS) - 2)
    rd['width']  = ROID_IMGS[rd['roidImage']].get_width()
    rd['height'] = ROID_IMGS[rd['roidImage']].get_height()
    rd['x'], rd['y'] = getRandomOffCameraPos(camerax, cameray, rd['width'], rd['height'])
    rd['movex'] = getRandomVelocity()
    rd['movey'] = getRandomVelocity()
    rd['rect'] = pygame.Rect( (rd['x'], rd['y'], rd['width'], rd['height']) )
    return rd

def makeSmallRoids(x, y):
    rd = {}
    rd['roidImage'] = 3
    rd['width']  = ROID_IMGS[rd['roidImage']].get_width()
    rd['height'] = ROID_IMGS[rd['roidImage']].get_height()
    rd['x'], rd['y'] = x, y
    rd['movex'] = getRandomVelocity()
    rd['movey'] = getRandomVelocity()
    rd['rect'] = pygame.Rect( (rd['x'], rd['y'], rd['width'], rd['height']) )
    return rd

def moveObj(x, y, rotate, speed): # calc coords of ship & photons
    rotate = rotate % 360
    vert = np.sin(np.deg2rad(rotate)) * speed
    horiz = np.cos(np.deg2rad(rotate)) * speed
    y -= vert
    x += horiz
    return int(x), int(y)

def makeNewPhotons(x, y, angle):
    photon = {}
    photon['x'], photon['y'] = x, y
    photon['angle'] = angle
    photon['photonImage'] = PHOTON_IMG
    photon['speed'] = PHOTON_SPEED
    photon['width']  = photon['photonImage'].get_width()
    photon['height'] = photon['photonImage'].get_height()
    photon['rect'] = pygame.Rect( (photon['x'], photon['y'], photon['width'], photon['height']) )
    return photon

def getRandomVelocity():
    speed = random.randint(ROIDMINSPEED, ROIDMAXSPEED)
    if random.randint(0, 1) == 0:
        return speed
    else:
        return -speed

def isOutsideActiveArea(camerax, cameray, obj):
    # Return False if camerax and cameray are more than
    # a half-window length beyond the edge of the window.
    boundsLeftEdge = camerax - WINWIDTH
    boundsTopEdge = cameray - WINHEIGHT
    boundsRect = pygame.Rect(boundsLeftEdge, boundsTopEdge, WINWIDTH * 3, WINHEIGHT * 3)
    objRect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])
    return not boundsRect.colliderect(objRect)

def drawScore(score):
    scoreSurf = BASICFONT.render('Score: %s' % (score), True, GREEN)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (WINWIDTH - 220, 10)
    DISPLAYSURF.blit(scoreSurf, scoreRect)

def drawHiScore(hiscore):
    scoreSurf = BASICFONT.render('High: %s' % (hiscore), True, ORANGE)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (WINWIDTH - 220, 40)
    DISPLAYSURF.blit(scoreSurf, scoreRect)

def drawHealthMeter(currentHealth):
    for i in range(currentHealth): # draw red health bars
        pygame.draw.rect(DISPLAYSURF, RED,   (15, 5 + (10 * LIVES) - i * 10, 20, 10))
    for i in range(LIVES): # draw the white outlines
        pygame.draw.rect(DISPLAYSURF, WHITE, (15, 5 + (10 * LIVES) - i * 10, 20, 10), 1)

def save_state(x):
    with open("state.txt", "w") as f:
        f.write("{}".format(x))
        f.close()

def load_state():
    try:
        with open("state.txt", "r") as f:
            x = f.read()
            x = int(x)
            f.close()
        return x
    except:
        return 0

def terminate():
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
