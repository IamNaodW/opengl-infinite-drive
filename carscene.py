import sys
import math
import random
import time  # Required for frame-rate independent physics
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# ---------------------------------------------------------------
# Window state
# ---------------------------------------------------------------
windowWidth  = 1200
windowHeight = 800

# ---------------------------------------------------------------
# Scenery state  —  S key cycles through all three
# ---------------------------------------------------------------
CITY   = 0
FOREST = 1
DESERT = 2
currentScenery = CITY

PI = 3.14159265

# ---------------------------------------------------------------
# Weather state  —  W key cycles through all four
# ---------------------------------------------------------------
CLEAR = 0
RAIN  = 1
STORM = 2
SNOW  = 3
currentWeather = CLEAR

# ---------------------------------------------------------------
# Day/Night state  —  T key toggles between day and night
# ---------------------------------------------------------------
DAY   = 0
NIGHT = 1
currentTimeOfDay = DAY

# ---------------------------------------------------------------
# Precipitation particle system
# ---------------------------------------------------------------
MAX_PARTICLES = 350

particles = [{'x': 0.0, 'y': 0.0, 'z': 0.0, 'speed': 0.0, 'drift': 0.0}
             for _ in range(MAX_PARTICLES)]
particlesInited = False

def randf(lo, hi):
    return lo + (hi - lo) * random.random()

def spawnParticle(p, isSnow):
    p['x']     = randf(-10.0, 10.0)
    p['y']     = randf(3.0,  9.0)
    p['z']     = randf(-8.0, 14.0)
    p['speed'] = randf(0.8, 1.6) if isSnow else randf(4.0, 8.0)
    p['drift'] = randf(-0.3, 0.3) if isSnow else randf(-0.1, 0.1)

def initParticles():
    global particlesInited
    for i in range(MAX_PARTICLES):
        spawnParticle(particles[i], False)
        particles[i]['y'] = randf(-1.0, 9.0)
    particlesInited = True

# ---------------------------------------------------------------
# Lightning state  (STORM only)
# ---------------------------------------------------------------
lightningTimer = 0.0
lightningFlash = 0.0

# ---------------------------------------------------------------
# Animation state
# ---------------------------------------------------------------
roadOffset = 0.0
propOffset = 0.0
wheelAngle = 0.0
bounceT    = 0.0
bounceY    = 0.0
carSpeed   = 1.0

DASH_PERIOD = 2.5

# ===============================================================
# LOW-LEVEL HELPERS
# ===============================================================
def cylinder(r, h, segs):
    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)
    gluCylinder(q, r, r, h, segs, 1)
    gluDisk(q, 0, r, segs, 1)
    glTranslatef(0, 0, h)
    gluDisk(q, 0, r, segs, 1)
    glTranslatef(0, 0, -h)
    gluDeleteQuadric(q)

def sphere(r, sl):
    glutSolidSphere(r, sl, sl)

def cone(r, h, segs):
    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)
    gluCylinder(q, r, 0, h, segs, 1)
    gluDisk(q, 0, r, segs, 1)
    gluDeleteQuadric(q)

def mat(r, g, b, specR=0.2, specG=0.2, specB=0.2, shine=24.0):
    diff = [r,       g,       b,       1.0]
    amb  = [r*0.30,  g*0.30,  b*0.30,  1.0]
    spec = [specR,   specG,   specB,   1.0]
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE,   diff)
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT,   amb)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,  spec)
    glMaterialf (GL_FRONT_AND_BACK, GL_SHININESS, shine)

# ===============================================================
# SKY
# ===============================================================
def drawSky():
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    glMatrixMode(GL_MODELVIEW);  glPushMatrix(); glLoadIdentity()

    if currentTimeOfDay == NIGHT:
        topR=0.02; topG=0.04; topB=0.12
        botR=0.08; botG=0.10; botB=0.20
    elif currentScenery == CITY:
        topR=0.18; topG=0.26; topB=0.48
        botR=0.55; botG=0.68; botB=0.85
    elif currentScenery == FOREST:
        topR=0.08; topG=0.20; topB=0.50
        botR=0.45; botG=0.72; botB=0.90
    else:
        topR=0.45; topG=0.60; topB=0.88
        botR=0.92; botG=0.76; botB=0.48

    glBegin(GL_QUADS)
    glColor3f(topR, topG, topB); glVertex2f(-1,  1)
    glColor3f(topR, topG, topB); glVertex2f( 1,  1)
    glColor3f(botR, botG, botB); glVertex2f( 1, -1)
    glColor3f(botR, botG, botB); glVertex2f(-1, -1)
    glEnd()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    if currentWeather == RAIN:
        glColor4f(0.05, 0.08, 0.15, 0.38)
        glBegin(GL_QUADS)
        glVertex2f(-1, 1); glVertex2f(1, 1); glVertex2f(1,-1); glVertex2f(-1,-1)
        glEnd()
    elif currentWeather == STORM:
        flashAdd = lightningFlash * 0.55
        glColor4f(0.05 + flashAdd, 0.06 + flashAdd, 0.10 + flashAdd * 0.5,
                  0.60 - lightningFlash * 0.25)
        glBegin(GL_QUADS)
        glVertex2f(-1, 1); glVertex2f(1, 1); glVertex2f(1,-1); glVertex2f(-1,-1)
        glEnd()
    elif currentWeather == SNOW:
        glColor4f(0.75, 0.82, 0.92, 0.22)
        glBegin(GL_QUADS)
        glVertex2f(-1, 1); glVertex2f(1, 1); glVertex2f(1,-1); glVertex2f(-1,-1)
        glEnd()
    glDisable(GL_BLEND)

    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW);  glPopMatrix()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

# ===============================================================
# LIGHTING
# ===============================================================
def setupLighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)

    l0Pos = [4.0, 12.0, 3.0, 0.0]

    if currentTimeOfDay == NIGHT:
        d = [0.15, 0.12, 0.18, 1]; a = [0.04, 0.04, 0.08, 1]
        s = [0.3,  0.3,  0.4,  1]; f = [0.35, 0.25, 0.15, 1]
    elif currentScenery == CITY:
        d = [0.82, 0.82, 0.88, 1]; a = [0.20, 0.20, 0.22, 1]
        s = [0.9,  0.9,  1.0,  1]; f = [0.18, 0.20, 0.28, 1]
    elif currentScenery == FOREST:
        d = [0.90, 0.88, 0.72, 1]; a = [0.18, 0.22, 0.14, 1]
        s = [1.0,  1.0,  0.85, 1]; f = [0.10, 0.22, 0.10, 1]
    else:
        d = [1.00, 0.92, 0.70, 1]; a = [0.28, 0.22, 0.12, 1]
        s = [1.0,  0.95, 0.80, 1]; f = [0.28, 0.18, 0.06, 1]

    l0Diff = d; l0Amb = a; l0Spec = s; l1Diff = f

    glLightfv(GL_LIGHT0, GL_POSITION, l0Pos)
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  l0Diff)
    glLightfv(GL_LIGHT0, GL_AMBIENT,  l0Amb)
    glLightfv(GL_LIGHT0, GL_SPECULAR, l0Spec)

    l1Pos = [-8.0, 5.0, -5.0, 0.0]
    l1Amb = [0.0, 0.0, 0.0, 1.0]
    glLightfv(GL_LIGHT1, GL_POSITION, l1Pos)
    glLightfv(GL_LIGHT1, GL_DIFFUSE,  l1Diff)
    glLightfv(GL_LIGHT1, GL_AMBIENT,  l1Amb)

    nv = 0.03 if currentTimeOfDay == NIGHT else 0.10
    globalAmb = [nv, nv, 0.05 if currentTimeOfDay == NIGHT else nv, 1.0]
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, globalAmb)

    weatherScale = 1.0
    if   currentWeather == RAIN:  weatherScale = 0.65
    elif currentWeather == STORM: weatherScale = 0.35 + lightningFlash * 1.10
    elif currentWeather == SNOW:  weatherScale = 0.80

    if weatherScale != 1.0:
        d2 = list(glGetLightfv(GL_LIGHT0, GL_DIFFUSE))
        a2 = list(glGetLightfv(GL_LIGHT0, GL_AMBIENT))
        s2 = list(glGetLightfv(GL_LIGHT0, GL_SPECULAR))
        for i in range(3):
            d2[i] *= weatherScale; a2[i] *= weatherScale; s2[i] *= weatherScale
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  d2)
        glLightfv(GL_LIGHT0, GL_AMBIENT,  a2)
        glLightfv(GL_LIGHT0, GL_SPECULAR, s2)
        d3 = list(glGetLightfv(GL_LIGHT1, GL_DIFFUSE))
        for i in range(3): d3[i] *= weatherScale
        glLightfv(GL_LIGHT1, GL_DIFFUSE, d3)

    glDisable(GL_COLOR_MATERIAL)

# ===============================================================
# Shadow
# ===============================================================
def drawShadowQuad(centerX, centerZ, widthX, depthZ, heightY=0.0):
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.01, 0.02, 0.05, 0.45)

    hW = widthX
    hD = depthZ

    sunDirX = -0.5
    sunDirY = -1.0
    sunDirZ = -0.3

    shadowOffsetFactorX = -(sunDirX / sunDirY)
    shadowOffsetFactorZ = -(sunDirZ / sunDirY)

    shiftX = heightY * shadowOffsetFactorX
    shiftZ = heightY * shadowOffsetFactorZ

    xMin = centerX - hW
    xMax = centerX + hW
    zMin = centerZ - hD
    zMax = centerZ + hD

    glBegin(GL_QUADS)
    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(xMin,         0.01, zMin)
    glVertex3f(xMax,         0.01, zMin)
    glVertex3f(xMax + shiftX, 0.01, zMax + shiftZ)
    glVertex3f(xMin + shiftX, 0.01, zMax + shiftZ)
    glEnd()

    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)

# ===============================================================
# ROAD
# ===============================================================
def drawRoad():
    mat(0.18, 0.18, 0.20, 0.05, 0.05, 0.05, 5.0)
    glBegin(GL_QUADS)
    glNormal3f(0,1,0)
    glVertex3f(-3.0,-0.01, 20.0); glVertex3f( 3.0,-0.01, 20.0)
    glVertex3f( 3.0,-0.01,-20.0); glVertex3f(-3.0,-0.01,-20.0)
    glEnd()

    if currentScenery != FOREST:
        mat(0.55,0.55,0.55, 0.1,0.1,0.1, 8.0)
        for side in [-1, 1]:
            sx = side*3.0; ex = side*3.35
            glBegin(GL_QUADS); glNormal3f(0,1,0)
            glVertex3f(sx,0.0, 20.0); glVertex3f(ex,0.0, 20.0)
            glVertex3f(ex,0.0,-20.0); glVertex3f(sx,0.0,-20.0)
            glEnd()
            glBegin(GL_QUADS); glNormal3f(float(side),0,0)
            glVertex3f(ex, 0.0, 20.0); glVertex3f(ex,-0.01, 20.0)
            glVertex3f(ex,-0.01,-20.0);glVertex3f(ex, 0.0,-20.0)
            glEnd()

    if currentScenery != FOREST:
        if currentScenery == DESERT:
            pavR=0.82; pavG=0.70; pavB=0.45
        else:
            pavR=0.72; pavG=0.68; pavB=0.62
        mat(pavR,pavG,pavB, 0.05,0.05,0.05, 4.0)
        for side in [-1, 1]:
            sx = side*3.35; ex = side*8.5
            glBegin(GL_QUADS); glNormal3f(0,1,0)
            glVertex3f(sx,0.0, 20.0); glVertex3f(ex,0.0, 20.0)
            glVertex3f(ex,0.0,-20.0); glVertex3f(sx,0.0,-20.0)
            glEnd()

    mat(0.92,0.88,0.30, 0.1,0.1,0.05, 10.0)
    z = -20.0
    while z < 22.0:
        dz = z + roadOffset
        glBegin(GL_QUADS); glNormal3f(0,1,0)
        glVertex3f(-0.06,0.005,dz);      glVertex3f( 0.06,0.005,dz)
        glVertex3f( 0.06,0.005,dz+1.4); glVertex3f(-0.06,0.005,dz+1.4)
        glEnd()
        z += DASH_PERIOD

    mat(0.92,0.92,0.92, 0.1,0.1,0.1, 8.0)
    for side in [-1, 1]:
        lx = side*1.5
        glBegin(GL_QUADS); glNormal3f(0,1,0)
        glVertex3f(lx-0.04,0.005, 20.0); glVertex3f(lx+0.04,0.005, 20.0)
        glVertex3f(lx+0.04,0.005,-20.0); glVertex3f(lx-0.04,0.005,-20.0)
        glEnd()

# ===============================================================
# GROUND PLANE
# ===============================================================
def drawGround():
    if   currentScenery == CITY:   gR=0.25; gG=0.28; gB=0.25
    elif currentScenery == FOREST: gR=0.18; gG=0.42; gB=0.16
    else:                           gR=0.82; gG=0.68; gB=0.38
    mat(gR,gG,gB, 0.03,0.03,0.03, 3.0)
    glBegin(GL_QUADS); glNormal3f(0,1,0)
    glVertex3f(-40.0,-0.02, 25.0); glVertex3f( 40.0,-0.02, 25.0)
    glVertex3f( 40.0,-0.02,-25.0); glVertex3f(-40.0,-0.02,-25.0)
    glEnd()

# ===============================================================
# STREET LIGHT POLE
# ===============================================================
def drawLightPole(x, z):
    glPushMatrix()
    glTranslatef(x, 0.0, z)
    glRotatef(-90, 1,0,0)

    poleHeight     = 3.5
    poleShadowWidth = 0.03
    poleShadowDepth = 0.03

    mat(0.55,0.55,0.58, 0.5,0.5,0.5, 60.0)
    cylinder(0.045, 3.8, 12)

    drawShadowQuad(x, z, poleShadowWidth, poleShadowDepth, poleHeight)

    glPushMatrix()
    glTranslatef(0,0,3.8)
    glRotatef(90.0 if x < 0 else -90.0, 0,1,0)
    cylinder(0.03, 0.55, 10)
    glTranslatef(0,0,0.55)

    if currentTimeOfDay == NIGHT:
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.95, 0.70)
        sphere(0.10, 12)
    else:
        mat(1.0,0.98,0.80, 1.0,1.0,0.9, 120.0)
        sphere(0.10, 12)
    glPopMatrix()

    glPopMatrix()
    glEnable(GL_LIGHTING)

# ===============================================================
# PINE TREE
# ===============================================================
def drawPineTree(x, z, scale):
    glPushMatrix()
    glTranslatef(x, 0.0, z)
    glScalef(scale, scale, scale)

    mat(0.35,0.20,0.08, 0.04,0.03,0.02, 5.0)
    glPushMatrix()
    glRotatef(-90,1,0,0)
    cylinder(0.12, 1.1, 10)
    glPopMatrix()

    tierBase = [0.85, 0.55, 0.32]
    tierH    = [1.10, 0.85, 0.65]
    tierY    = [0.80, 1.55, 2.18]
    lr = 0.15 + 0.05*math.sin(x*1.7)
    lg = 0.48 + 0.10*math.cos(z*1.3)
    mat(lr, lg, 0.12, 0.04,0.08,0.03, 6.0)

    for t in range(3):
        glPushMatrix()
        glTranslatef(0, tierY[t], 0)
        glRotatef(-90,1,0,0)
        cone(tierBase[t], tierH[t], 18)
        glPopMatrix()

    glPopMatrix()

# ===============================================================
# OAK / DECIDUOUS TREE
# ===============================================================
def drawOakTree(x, z, scale):
    glPushMatrix()
    glTranslatef(x, 0.0, z)
    glScalef(scale, scale, scale)

    mat(0.40,0.24,0.10, 0.04,0.03,0.02, 5.0)
    glPushMatrix(); glRotatef(-90,1,0,0); cylinder(0.10,1.4,10); glPopMatrix()

    cr = 0.16+0.06*math.sin(x*2.1)
    cg = 0.44+0.10*math.cos(z*1.7)
    mat(cr,cg,0.10, 0.03,0.06,0.02, 5.0)
    glPushMatrix(); glTranslatef( 0.0,2.0, 0.0); sphere(0.65,14); glPopMatrix()
    glPushMatrix(); glTranslatef( 0.4,1.7, 0.3); sphere(0.45,12); glPopMatrix()
    glPushMatrix(); glTranslatef(-0.3,1.8,-0.2); sphere(0.42,12); glPopMatrix()

    glPopMatrix()

# ===============================================================
# FOREST SCENERY
# ===============================================================
def drawForest():
    glPushMatrix()

    boundaryStart = -50.0
    boundaryRange = 90.0

    def wrapZ(rawZ):
        return boundaryStart + math.fmod(rawZ - boundaryStart + boundaryRange * 10.0, boundaryRange)

    nearZ = [-33.0,-28.5,-24.0,-19.5,-15.0,-10.5,-6.0,
             -1.5, 3.0, 7.5, 12.0, 16.5, 21.0, 24.5]
    for i in range(14):
        currentZ = wrapZ(nearZ[i] + propOffset)
        sc = 0.9 + 0.3*math.sin(nearZ[i]*0.7)
        drawShadowQuad(-4.2+0.2, currentZ-0.2, sc*0.6, sc*0.6)
        drawShadowQuad( 4.2+0.2, currentZ-0.2, sc*0.6, sc*0.6)
        drawPineTree(-4.2, currentZ, sc)
        drawPineTree( 4.2, currentZ, sc*0.88)

    midZ = [-31.5,-26.0,-21.0,-16.0,-11.0,-6.0,
            -1.0, 4.0, 9.0, 14.0, 19.0, 23.5]
    for i in range(12):
        currentZ = wrapZ(midZ[i] + propOffset)
        sc = 0.7 + 0.25*math.cos(midZ[i]*0.5)
        drawOakTree(-6.5, currentZ, sc)
        drawOakTree( 6.5, currentZ, sc*0.92)

    farZ = [-34.0,-30.0,-26.0,-22.0,-18.0,-14.0,-10.0,-6.0,
            -2.0, 2.0, 6.0, 10.0, 14.0, 18.0, 22.0, 25.0]
    for i in range(16):
        currentZ = wrapZ(farZ[i] + propOffset)
        sc = 0.5 + 0.15*math.sin(farZ[i]*1.1)
        drawPineTree(-9.5, currentZ, sc)
        drawPineTree( 9.5, currentZ, sc)

    zOffset = -50.0
    while zOffset <= 40.0:
        zA = wrapZ(zOffset + propOffset)
        scA = 0.65 + 0.15*math.sin(zOffset*0.5)
        drawOakTree(-12.0, zA, scA)
        drawOakTree( 12.0, zA, scA*0.9)

        zB = wrapZ((zOffset+1.0) + propOffset)
        scB = 0.55 + 0.12*math.cos(zOffset*0.8)
        drawPineTree(-15.5, zB, scB)
        drawPineTree( 15.5, zB, scB*0.95)

        zC = wrapZ((zOffset+2.0) + propOffset)
        scC = 0.60 + 0.10*math.sin(zOffset*1.2)
        drawOakTree(-19.0, zC, scC)
        drawOakTree( 19.0, zC, scC*0.85)

        zOffset += 3.0

    bushPos = [
        [-4.0,-31.0],[-4.5,-22.0],[-3.8,-13.0],[-4.2,-4.0],[-4.5,5.0],[-3.8,14.0],[-4.0,22.0],
        [ 4.2,-27.5],[ 4.0,-18.5],[ 4.6,-9.0], [ 4.2,0.5], [ 4.0,9.5],[ 4.6,18.0],[ 4.2,24.0]
    ]
    mat(0.14,0.38,0.10, 0.03,0.05,0.02, 4.0)
    for i in range(14):
        currentZ = wrapZ(bushPos[i][1] + propOffset)
        glPushMatrix()
        glTranslatef(bushPos[i][0], 0.22, currentZ)
        sphere(0.28, 10)
        glPopMatrix()

    glPopMatrix()

# ===============================================================
# CACTUS
# ===============================================================
def drawCactus(x, z, scale):
    glPushMatrix()
    glTranslatef(x, 0.0, z)
    glScalef(scale, scale, scale)

    mat(0.22,0.48,0.18, 0.05,0.10,0.04, 8.0)

    glPushMatrix()
    glRotatef(-90,1,0,0)
    cylinder(0.18, 2.0, 12)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0,2.0,0)
    sphere(0.18,10)
    glPopMatrix()

    # Left arm
    glPushMatrix()
    glTranslatef(-0.18, 1.0, 0)
    glRotatef(90, 0,0,1)
    glRotatef(-90,1,0,0)
    cylinder(0.11, 0.55, 10)
    glTranslatef(0,0,0.55)
    glRotatef(-90,0,1,0)
    glRotatef(-90,1,0,0)
    cylinder(0.11, 0.75, 10)
    glTranslatef(0,0,0.75)
    sphere(0.11,8)
    glPopMatrix()

    # Right arm
    glPushMatrix()
    glTranslatef( 0.18, 1.3, 0)
    glRotatef(-90, 0,0,1)
    glRotatef(-90,1,0,0)
    cylinder(0.11, 0.45, 10)
    glTranslatef(0,0,0.45)
    glRotatef( 90,0,1,0)
    glRotatef(-90,1,0,0)
    cylinder(0.11, 0.65, 10)
    glTranslatef(0,0,0.65)
    sphere(0.11,8)
    glPopMatrix()

    glPopMatrix()

def drawRock(x, z, scale):
    glPushMatrix()
    glTranslatef(x, scale*0.18, z)
    glScalef(scale, scale*0.45, scale*0.85)
    mat(0.58,0.52,0.44, 0.08,0.08,0.08, 6.0)
    sphere(0.40, 10)
    glPopMatrix()

# ===============================================================
# DESERT
# ===============================================================
def drawDesert():
    glPushMatrix()

    bStart = -50.0
    bRange = 100.0

    def wrapZ(rawZ):
        return bStart + math.fmod(rawZ - bStart + bRange * 10.0, bRange)

    nearCactus = [
        [-4.5,-45.0,0.90,0],[-4.0,-35.0,1.10,1],[-5.0,-25.0,0.75,0],
        [-4.8,-15.0,1.00,1],[-6.5, -5.0,0.65,0],[-6.0,  5.0,0.80,1],
        [-4.5, 15.0,0.88,0],[-4.0, 25.0,1.05,1],[-5.2, 35.0,0.72,0],
        [-4.8, 45.0,0.95,1],
        [ 4.5,-40.0,1.05,0],[ 4.2,-30.0,0.85,1],[ 5.1,-20.0,0.95,0],
        [ 4.8,-10.0,0.70,1],[ 6.2,  0.0,0.60,0],[ 5.8, 10.0,0.90,1],
        [ 4.5, 20.0,1.00,0],[ 4.2, 30.0,0.82,1],[ 5.1, 40.0,0.92,0],
        [ 4.8, 48.0,0.68,1],
    ]
    for i in range(20):
        cz  = wrapZ(nearCactus[i][1] + propOffset)
        sc  = nearCactus[i][2]
        cx  = nearCactus[i][0]
        typ = int(nearCactus[i][3])
        drawShadowQuad(cx, cz, sc*0.25, sc*0.20)
        if typ == 0: drawCactus(cx, cz, sc)
        else:        drawCactus(cx, cz, sc * 0.9)

    rockData = [
        [-7.5,-44.0,0.90],[-8.0,-34.0,0.65],[-7.2,-24.0,0.75],
        [-7.5,-14.0,0.80],[-8.0, -4.0,0.70],[-7.2,  6.0,0.55],
        [-5.5, 16.0,0.50],[-7.8, 26.0,0.60],[-7.2, 36.0,0.75],
        [-8.0, 46.0,0.65],
        [ 7.5,-41.0,0.80],[ 8.2,-31.0,0.70],[ 7.0,-21.0,0.55],
        [ 6.0,-11.0,0.60],[ 7.5, -1.0,0.75],[ 8.2,  9.0,0.65],
        [ 7.0, 19.0,0.80],[ 6.0, 29.0,0.60],[ 7.5, 39.0,0.70],
        [ 8.2, 47.0,0.55]
    ]
    for i in range(20):
        cz = wrapZ(rockData[i][1] + propOffset)
        drawRock(rockData[i][0], cz, rockData[i][2])

    midPlant = [
        [-11.0,-48.0,0.45,0],[-13.5,-38.0,0.38,1],[-10.5,-28.0,0.42,0],
        [-12.0,-18.0,0.35,1],[-11.5, -8.0,0.40,0],[-13.0,  2.0,0.36,1],
        [-10.0, 12.0,0.44,0],[-12.5, 22.0,0.38,1],[-11.0, 32.0,0.41,0],
        [-13.5, 42.0,0.35,1],
        [ 11.5,-43.0,0.42,0],[ 13.0,-33.0,0.36,1],[ 10.5,-23.0,0.44,0],
        [ 12.5,-13.0,0.38,1],[ 11.0, -3.0,0.40,0],[ 13.5,  7.0,0.35,1],
        [ 10.5, 17.0,0.43,0],[ 12.0, 27.0,0.37,1],[ 11.5, 37.0,0.41,0],
        [ 13.0, 47.0,0.34,1]
    ]
    for i in range(20):
        cz  = wrapZ(midPlant[i][1] + propOffset)
        sc  = midPlant[i][2]
        drawCactus(midPlant[i][0], cz, sc)

    mat(0.80, 0.65, 0.35, 0.05, 0.05, 0.03, 3.0)
    duneX = [10.0,13.5,17.0,11.5,15.0,10.5,14.0,18.0,12.0,16.0]
    duneZ = [-45.0,-35.0,-25.0,-15.0,-5.0,5.0,15.0,25.0,35.0,45.0]
    duneS = [ 2.5,  1.8,  3.0,  1.5, 2.2,2.3, 1.9, 2.8, 1.6, 2.4]
    for i in range(10):
        cz = wrapZ(duneZ[i] + propOffset)
        glPushMatrix()
        glTranslatef(duneX[i], duneS[i]*0.22, cz)
        glScalef(duneS[i]*1.8, duneS[i]*0.30, duneS[i]*1.1)
        sphere(1.0, 14)
        glPopMatrix()

    glPopMatrix()

# ===============================================================
# BUILDINGS
# ===============================================================
def solidBox(x0, x1, y0, y1, z0, z1, r, g, b):
    mat(r, g, b, 0.18, 0.18, 0.22, 32.0)
    glBegin(GL_QUADS)
    # Front  (-X)
    glNormal3f(-1, 0, 0)
    glVertex3f(x1,y0,z1); glVertex3f(x1,y0,z0)
    glVertex3f(x1,y1,z0); glVertex3f(x1,y1,z1)
    # Back   (+X)
    glNormal3f( 1, 0, 0)
    glVertex3f(x0,y0,z0); glVertex3f(x0,y0,z1)
    glVertex3f(x0,y1,z1); glVertex3f(x0,y1,z0)
    # Left   (-Z)
    glNormal3f( 0, 0,-1)
    glVertex3f(x1,y0,z0); glVertex3f(x0,y0,z0)
    glVertex3f(x0,y1,z0); glVertex3f(x1,y1,z0)
    # Right  (+Z)
    glNormal3f( 0, 0, 1)
    glVertex3f(x0,y0,z1); glVertex3f(x1,y0,z1)
    glVertex3f(x1,y1,z1); glVertex3f(x0,y1,z1)
    # Roof   (+Y)
    glNormal3f( 0, 1, 0)
    glVertex3f(x0,y1,z0); glVertex3f(x1,y1,z0)
    glVertex3f(x1,y1,z1); glVertex3f(x0,y1,z1)
    glEnd()

def windowGrid(xFront, bh, zMin, zMax, r, g, b):
    if currentTimeOfDay == NIGHT:
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.95, 0.6)
    elif currentWeather == CLEAR:
        glEnable(GL_LIGHTING)
        glColor3f(0.6, 0.75, 0.95)
        mat(0.6, 0.75, 0.95, 0.3, 0.3, 0.3, 64.0)
    else:
        glDisable(GL_LIGHTING)
        glColor3f(0.20, 0.22, 0.28)

    glBegin(GL_QUADS)
    wy = 0.5
    while wy < bh - 0.4:
        wz = zMin + 0.15
        while wz < zMax - 0.25:
            if (int(wz * 9 + wy * 11) % 4) == 0:
                wz += 0.45; continue
            if currentTimeOfDay == DAY and currentWeather == CLEAR:
                glNormal3f(-1.0, 0.0, 0.0)
            glVertex3f(xFront - 0.02, wy,        wz)
            glVertex3f(xFront - 0.02, wy,        wz + 0.15)
            glVertex3f(xFront - 0.02, wy + 0.25, wz + 0.15)
            glVertex3f(xFront - 0.02, wy + 0.25, wz)
            wz += 0.45
        wy += 0.60
    glEnd()
    glEnable(GL_LIGHTING)

def drawSteppedBuilding(cx, cz, bw, bh, bd, r, g, b):
    tW = [1.0, 0.70, 0.45]
    tH = [bh * 0.50, bh * 0.30, bh * 0.20]
    yBase = 0.0
    for t in range(3):
        hw = bw * tW[t]
        hd = bd * (0.9 - t * 0.15)
        x0 = cx + hd; x1 = cx
        z0 = cz - hw; z1 = cz + hw
        y0 = yBase;   y1 = yBase + tH[t]
        br = r * (1.0 + t * 0.08)
        bg = g * (1.0 + t * 0.08)
        bb = b * (1.0 + t * 0.08)
        solidBox(x0, x1, y0, y1, z0, z1, br, bg, bb)
        windowGrid(x1, tH[t], z0, z1, br, bg, bb)
        yBase = y1

def drawLBuilding(cx, cz, bw, bh, bd, r, g, b):
    x0 = cx + bd; x1 = cx
    solidBox(x0, x1, 0.0, bh, cz - bw, cz, r, g, b)
    windowGrid(x1, bh, cz - bw, cz, r, g, b)

    hh  = bh * 0.60
    bd2 = bd * 0.65
    solidBox(cx + bd2, x1, 0.0, hh, cz, cz + bw * 0.85,
             r * 0.92, g * 0.92, b * 0.92)
    windowGrid(x1, hh, cz, cz + bw * 0.85, r, g, b)

def drawCylinderBuilding(cx, cz, bw, bh, bd, r, g, b):
    radius = bw * 0.85
    glPushMatrix()
    glTranslatef(cx + radius, 0.0, cz)
    glRotatef(-90.0, 1, 0, 0)
    mat(r, g, b, 0.45, 0.45, 0.55, 80.0)
    qc = gluNewQuadric()
    gluQuadricNormals(qc, GLU_SMOOTH)
    gluCylinder(qc, radius, radius * 0.88, bh, 24, 2)
    glTranslatef(0, 0, bh)
    gluDisk(qc, 0, radius * 0.88, 24, 1)
    gluDeleteQuadric(qc)
    glPopMatrix()

    if currentTimeOfDay == NIGHT:
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.95, 0.6)
    elif currentWeather == CLEAR:
        glEnable(GL_LIGHTING)
        glColor3f(0.6, 0.75, 0.95)
        mat(0.6, 0.75, 0.95, 0.3, 0.3, 0.3, 64.0)
    else:
        glDisable(GL_LIGHTING)
        glColor3f(0.20, 0.22, 0.28)

    glBegin(GL_QUADS)
    strips = 8
    for s in range(strips):
        ang = s * (2.0 * PI / strips)
        nx = math.cos(ang); nz = math.sin(ang)
        px = cx + radius + nx * radius * 0.99
        pz = cz + nz * radius * 0.99
        dx = -nz * 0.06; dz = nx * 0.06
        wy = 0.5
        while wy < bh - 0.6:
            if currentTimeOfDay == DAY and currentWeather == CLEAR:
                glNormal3f(nx, 0, nz)
            glVertex3f(px - dx, wy,        pz - dz)
            glVertex3f(px + dx, wy,        pz + dz)
            glVertex3f(px + dx, wy + 0.4,  pz + dz)
            glVertex3f(px - dx, wy + 0.4,  pz - dz)
            wy += 0.8
    glEnd()
    glEnable(GL_LIGHTING)

def drawBuilding3D(cx, cz, bw, bh, bd, r, g, b):
    x1 = cx; x0 = cx + bd
    z0 = cz - bw; z1 = cz + bw
    y0 = 0.0; y1 = bh

    mat(r, g, b, 0.18, 0.18, 0.22, 32.0)
    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)
    glVertex3f(x1,y0,z1); glVertex3f(x1,y0,z0)
    glVertex3f(x1,y1,z0); glVertex3f(x1,y1,z1)
    glNormal3f( 1, 0, 0)
    glVertex3f(x0,y0,z0); glVertex3f(x0,y0,z1)
    glVertex3f(x0,y1,z1); glVertex3f(x0,y1,z0)
    glNormal3f( 0, 0,-1)
    glVertex3f(x1,y0,z0); glVertex3f(x0,y0,z0)
    glVertex3f(x0,y1,z0); glVertex3f(x1,y1,z0)
    glNormal3f( 0, 0, 1)
    glVertex3f(x0,y0,z1); glVertex3f(x1,y0,z1)
    glVertex3f(x1,y1,z1); glVertex3f(x0,y1,z1)
    glNormal3f( 0, 1, 0)
    glVertex3f(x0,y1,z0); glVertex3f(x1,y1,z0)
    glVertex3f(x1,y1,z1); glVertex3f(x0,y1,z1)
    glEnd()

    if currentTimeOfDay == NIGHT:
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.95, 0.6)
    elif currentWeather == CLEAR:
        glEnable(GL_LIGHTING)
        glColor3f(0.6, 0.75, 0.95)
        mat(0.6, 0.75, 0.95, 0.3, 0.3, 0.3, 64.0)
    else:
        glDisable(GL_LIGHTING)
        glColor3f(0.20, 0.22, 0.28)

    glBegin(GL_QUADS)
    wy = 0.5
    while wy < bh - 0.4:
        wz = cz - bw + 0.15
        while wz < cz + bw - 0.25:
            if (int(wz*9 + wy*11) % 4) == 0:
                wz += 0.45; continue
            if currentTimeOfDay == DAY and currentWeather == CLEAR:
                glNormal3f(-1.0, 0.0, 0.0)
            glVertex3f(x1-0.02, wy,        wz)
            glVertex3f(x1-0.02, wy,        wz+0.15)
            glVertex3f(x1-0.02, wy+0.25,   wz+0.15)
            glVertex3f(x1-0.02, wy+0.25,   wz)
            wz += 0.45
        wy += 0.60
    glEnd()
    glEnable(GL_LIGHTING)

# ===============================================================
# CITY
# ===============================================================
def drawCity():
    glPushMatrix()

    cols = [
        [0.14,0.18,0.26],[0.19,0.23,0.32],
        [0.16,0.16,0.22],[0.22,0.20,0.28],
        [0.11,0.13,0.18],[0.08,0.10,0.15]
    ]

    boundaryStart = -35.0
    boundaryRange = 60.0

    def wrapZ(rawZ):
        return boundaryStart + math.fmod(rawZ - boundaryStart + boundaryRange * 10.0, boundaryRange)

    # LAYER 1: FOREGROUND STREET BUILDINGS
    fg = [
        (-32.0, 2.2, 7.5, 8.5, 2.8, 1),
        (-27.5, 2.0, 6.2, 8.5, 2.4, 3),
        (-23.0, 1.8, 8.0, 8.5, 3.0, 0),
        (-18.5, 2.1, 6.8, 8.5, 2.6, 2),
        (-14.0, 1.6, 8.5, 8.5, 2.2, 1),
        ( -9.5, 2.0, 7.0, 8.5, 2.8, 0),
        ( -5.0, 1.7, 9.0, 8.5, 3.2, 3),
        ( -0.5, 1.9, 7.2, 8.5, 2.5, 2),
        (  4.0, 1.6, 8.2, 8.5, 2.0, 1),
        (  8.5, 2.0, 6.5, 8.5, 2.7, 0),
        ( 13.0, 1.7, 8.8, 8.5, 2.4, 3),
        ( 17.5, 1.8, 7.4, 8.5, 2.6, 2),
        ( 22.0, 2.1, 8.1, 8.5, 2.9, 1),
    ]

    for i, (zBase, halfW, height, xPos, depth, shape) in enumerate(fg):
        currentZ = wrapZ(zBase + propOffset)
        cr = cols[i%4][0]; cg = cols[i%4][1]; cb = cols[i%4][2]
        hw = halfW; h = height; d = depth

        drawShadowQuad(xPos, currentZ - 0.2, hw / 2.0, hw)

        if   shape == 1: drawSteppedBuilding (xPos, currentZ, hw/2.0, h, d, cr, cg, cb)
        elif shape == 2: drawLBuilding        (xPos, currentZ, hw/2.0, h, d, cr, cg, cb)
        elif shape == 3: drawCylinderBuilding (xPos, currentZ, hw/2.0, h, d, cr, cg, cb)
        else:            drawBuilding3D        (xPos, currentZ, hw/2.0, h, d, cr, cg, cb)

    # LAYERS 2 & 3: CITY SKYLINE
    blocks = [
        (-28.0,-13.0,1.0,19.0,2.6,1,0.88,True, 1),
        (-23.5,-12.5,1.2,14.0,2.4,0,0.82,False,3),
        (-19.0,-13.5,0.9,16.5,2.5,2,0.86,True, 1),
        (-26.0,-15.5,2.0, 6.5,3.4,3,0.68,False,0),
        (-21.0,-15.0,1.6, 5.0,2.8,4,0.62,False,2),
        ( -4.0,-13.5,1.1,21.0,2.8,1,0.92,True, 3),
        ( -8.5,-14.0,1.0,12.5,2.4,0,0.76,False,1),
        (  0.5,-13.0,1.1,15.0,2.6,2,0.80,False,0),
        ( -6.5,-16.0,2.2, 5.5,3.6,5,0.58,False,2),
        ( -3.0,-15.5,1.5, 4.0,2.8,3,0.58,False,0),
        ( 15.0,-13.0,1.1,11.0,2.4,2,0.74,False,0),
        ( 19.5,-14.0,1.6, 8.5,3.0,0,0.70,False,2),
        ( 23.5,-13.5,1.2,12.0,2.6,1,0.78,False,1),
        ( 17.5,-16.0,2.0, 4.5,3.2,4,0.56,False,0),
        ( 22.0,-15.5,1.4, 3.5,2.6,5,0.54,False,0),
        (-30.0,-19.5,2.4,23.0,4.2,0,0.52,True, 1),
        (-14.0,-20.0,2.6,18.0,3.8,1,0.48,False,0),
        (  2.0,-19.0,2.2,25.5,4.4,2,0.54,True, 3),
        ( 17.5,-20.5,2.5,20.0,3.6,0,0.46,False,1),
    ]

    for (zBase, xPos, halfW, height, depth, colIdx, bright, antenna, shape) in blocks:
        cz = wrapZ(zBase + propOffset)

        fade = 1.0
        if cz < -28.0:
            fade = (cz - boundaryStart) / 7.0
            if fade < 0.0: fade = 0.0
        h = height * fade
        if h < 0.3: continue

        cr = cols[colIdx][0] * bright
        cg = cols[colIdx][1] * bright
        cb = cols[colIdx][2] * bright

        if   shape == 1: drawSteppedBuilding ( xPos, cz, halfW, h, depth, cr, cg, cb)
        elif shape == 2: drawLBuilding        ( xPos, cz, halfW, h, depth, cr, cg, cb)
        elif shape == 3: drawCylinderBuilding ( xPos, cz, halfW, h, depth, cr, cg, cb)
        else:            drawBuilding3D        ( xPos, cz, halfW, h, depth, cr, cg, cb)

        if   shape == 1: drawSteppedBuilding (-xPos, cz, halfW, h, depth, cr, cg, cb)
        elif shape == 2: drawLBuilding       (-xPos, cz, halfW, h, depth, cr, cg, cb)
        elif shape == 3: drawCylinderBuilding(-xPos, cz, halfW, h, depth, cr, cg, cb)
        else:            drawBuilding3D       (-xPos, cz, halfW, h, depth, cr, cg, cb)

        if antenna and fade > 0.5:
            antH = 1.8 * fade
            glDisable(GL_LIGHTING)
            glColor3f(0.52, 0.52, 0.56)
            for side in [-1, 1]:
                glPushMatrix()
                glTranslatef(side * xPos, h, cz)
                glRotatef(-90.0, 1, 0, 0)
                qa = gluNewQuadric()
                gluCylinder(qa, 0.05, 0.008, antH, 6, 1)
                gluDeleteQuadric(qa)
                glPopMatrix()
            glEnable(GL_LIGHTING)

    # STREET LIGHTS
    poleZ = [-30.0, -20.0, -10.0, 0.0, 10.0, 20.0]
    for i in range(6):
        currentPoleZ = poleZ[i] + propOffset
        currentPoleZ = boundaryStart + math.fmod(
            currentPoleZ - boundaryStart + boundaryRange * 10.0, boundaryRange)
        drawLightPole(-4.0, currentPoleZ)
        drawLightPole( 4.0, currentPoleZ)

    glPopMatrix()

# ===============================================================
# WHEEL & CAR
# ===============================================================
def drawWheel(x, y, z, isLeft):
    glPushMatrix()
    glTranslatef(x,y,z)
    glRotatef(-90.0 if isLeft else 90.0, 0,1,0)
    glRotatef(-wheelAngle, 0,0,1)

    q = gluNewQuadric()
    gluQuadricNormals(q, GLU_SMOOTH)

    # Tyre
    tc=[0.05,0.05,0.05,1]; ta=[0.02,0.02,0.02,1]; ts=[0.1,0.1,0.1,1]
    glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT,ta)
    glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,tc)
    glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,ts)
    glMaterialf(GL_FRONT_AND_BACK,GL_SHININESS,10)
    tr=0.42; tw=0.25
    glPushMatrix(); glTranslatef(0,0,-tw/2)
    gluCylinder(q,tr,tr,tw,48,1)
    glTranslatef(0,0,tw); gluDisk(q,tr*0.65,tr,48,1)
    glPopMatrix()

    # Rim
    rc=[0.8,0.82,0.85,1]; ra=[0.4,0.42,0.45,1]; rs=[1,1,1,1]
    glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT,ra)
    glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,rc)
    glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,rs)
    glMaterialf(GL_FRONT_AND_BACK,GL_SHININESS,128)
    rr=tr*0.65
    glPushMatrix(); glTranslatef(0,0,tw/2+0.002)
    gluDisk(q,0,rr,48,1)
    sc2=[0.4,0.4,0.42,1]
    glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT_AND_DIFFUSE,sc2)
    for i in range(5):
        glPushMatrix(); glRotatef(i*72.0,0,0,1)
        glBegin(GL_QUADS); glNormal3f(0,0,1)
        glVertex3f(-0.025,0,0.005); glVertex3f(0.025,0,0.005)
        glVertex3f(0.018,rr,0.002); glVertex3f(-0.018,rr,0.002)
        glEnd(); glPopMatrix()
    glPopMatrix()

    gluDeleteQuadric(q)
    glPopMatrix()

def drawCar():
    glPushMatrix()
    glTranslatef(0.0, bounceY, 0.0)
    bc=[0.85,0.05,0.05,1]; ba=[0.4,0.02,0.02,1]; bs=[1,0.8,0.8,1]
    glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT,ba)
    glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,bc)
    glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,bs)
    glMaterialf(GL_FRONT_AND_BACK,GL_SHININESS,128)
    glPushMatrix(); glTranslatef(0,0.8,0);    glScalef(1.6,0.7,3.5); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(0,1.5,-0.2); glScalef(1.3,0.7,1.8); glutSolidCube(1); glPopMatrix()

    wc=[0.2,0.4,0.6,0.7]; wa=[0.1,0.2,0.3,1]; ws=[1,1,1,1]
    glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT,wa)
    glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,wc)
    glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,ws)
    glMaterialf(GL_FRONT_AND_BACK,GL_SHININESS,128)
    glPushMatrix(); glTranslatef(0,1.51, 0.91); glScalef(1.22,0.42,0.02); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(0,1.51,-1.11); glScalef(1.12,0.42,0.02); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(-0.66,1.5,-0.2); glScalef(0.02,0.40,1.4); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef( 0.66,1.5,-0.2); glScalef(0.02,0.40,1.4); glutSolidCube(1); glPopMatrix()

    drawWheel(-0.82,0.42, 1.1, True)
    drawWheel( 0.82,0.42, 1.1, False)
    drawWheel(-0.82,0.42,-1.2, True)
    drawWheel( 0.82,0.42,-1.2, False)

    hd=[1,1,0.85,1]; ha=[0.5,0.5,0.4,1]
    glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT,ha)
    glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,hd)
    glMaterialf(GL_FRONT_AND_BACK,GL_SHININESS,64)
    glPushMatrix(); glTranslatef(-0.5,0.7,1.76); glutSolidSphere(0.12,16,16); glPopMatrix()
    glPushMatrix(); glTranslatef( 0.5,0.7,1.76); glutSolidSphere(0.12,16,16); glPopMatrix()

    glPopMatrix()

# ===============================================================
# PRECIPITATION
# ===============================================================
def drawPrecipitation():
    if currentWeather == CLEAR: return
    isSnow  = (currentWeather == SNOW)
    isStorm = (currentWeather == STORM)

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    if isSnow:
        glPointSize(2.8)
        glBegin(GL_POINTS)
        for i in range(MAX_PARTICLES):
            alpha = 0.70 + 0.30 * math.sin(particles[i]['y'] * 3.1)
            glColor4f(0.92, 0.95, 1.0, alpha)
            glVertex3f(particles[i]['x'], particles[i]['y'], particles[i]['z'])
        glEnd()
    else:
        streakLen = 0.55 if isStorm else 0.35
        alpha     = 0.55 if isStorm else 0.40
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for i in range(MAX_PARTICLES):
            glColor4f(0.65, 0.75, 0.90, alpha)
            glVertex3f(particles[i]['x'],        particles[i]['y'],             particles[i]['z'])
            glColor4f(0.65, 0.75, 0.90, 0.0)
            glVertex3f(particles[i]['x']+0.05,   particles[i]['y']+streakLen,   particles[i]['z']+0.05)
        glEnd()
        glLineWidth(1.0)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glDisable(GL_BLEND)

def drawSnowGround():
    if currentWeather != SNOW: return
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.88, 0.92, 0.96, 0.60)
    glBegin(GL_QUADS); glNormal3f(0,1,0)
    glVertex3f(-40.0, 0.005,  25.0)
    glVertex3f( 40.0, 0.005,  25.0)
    glVertex3f( 40.0, 0.005, -25.0)
    glVertex3f(-40.0, 0.005, -25.0)
    glEnd()
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)

# ===============================================================
# HUD LABEL
# ===============================================================
def drawHUD():
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, windowWidth, 0, windowHeight)
    glMatrixMode(GL_MODELVIEW);  glPushMatrix(); glLoadIdentity()

    sceneryLabels = ["CITY", "FOREST", "DESERT"]
    weatherLabels = ["CLEAR", "RAIN", "STORM", "SNOW"]
    timeLabels    = ["DAY", "NIGHT"]
    buf = ("Scenery: %s [S]   Weather: %s [W]   Time: %s [T]   Speed: %.2fx [+/-]" %
           (sceneryLabels[currentScenery],
            weatherLabels[currentWeather],
            timeLabels[currentTimeOfDay],
            carSpeed))

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0,0,0,0.45)
    glBegin(GL_QUADS)
    glVertex2f(  8, windowHeight-32)
    glVertex2f(720, windowHeight-32)
    glVertex2f(720, windowHeight- 8)
    glVertex2f(  8, windowHeight- 8)
    glEnd()

    glColor3f(1,1,1)
    glRasterPos2i(16, windowHeight-22)
    for c in buf:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(c))

    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW);  glPopMatrix()
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

# ===============================================================
# DISPLAY
# ===============================================================
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    drawSky()

    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45.0, float(windowWidth)/windowHeight, 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    gluLookAt(-10.0,3.5,-3.0,
               0.5,1.2,0.0,
               0.0,1.0,0.0)

    setupLighting()
    drawGround()
    drawSnowGround()
    drawRoad()

    glPushMatrix()
    drawShadowQuad(0.0, 0.0, 0.75, 1.4)
    glPopMatrix()

    if currentWeather == RAIN or currentWeather == STORM:
        fogColor = [0.35, 0.38, 0.42, 1.0]
        glFogi (GL_FOG_MODE,  GL_LINEAR)
        glFogfv(GL_FOG_COLOR, fogColor)
        glFogf (GL_FOG_START, 10.0 if currentWeather == STORM else 20.0)
        glFogf (GL_FOG_END,   28.0 if currentWeather == STORM else 48.0)
        glEnable(GL_FOG)
    elif currentWeather == SNOW:
        fogColor = [0.80, 0.84, 0.90, 1.0]
        glFogi (GL_FOG_MODE,  GL_LINEAR)
        glFogfv(GL_FOG_COLOR, fogColor)
        glFogf (GL_FOG_START, 14.0)
        glFogf (GL_FOG_END,   38.0)
        glEnable(GL_FOG)

    if currentScenery == CITY:
        drawCity()
    elif currentScenery == FOREST:
        if currentWeather == CLEAR:
            fogColor = [0.42, 0.64, 0.50, 1.0]
            glFogi (GL_FOG_MODE,  GL_LINEAR)
            glFogfv(GL_FOG_COLOR, fogColor)
            glFogf (GL_FOG_START, 18.0)
            glFogf (GL_FOG_END,   42.0)
            glEnable(GL_FOG)
            drawForest()
            glDisable(GL_FOG)
        else:
            drawForest()
    else:
        drawDesert()

    if currentWeather != CLEAR:
        glDisable(GL_FOG)

    drawCar()
    drawPrecipitation()
    drawHUD()

    glutSwapBuffers()

# ===============================================================
# TIMER (FIXED DELTA-TIME TO ACCOUNT FOR CPU BOTTLENECK LAG)
# ===============================================================
def timer(value):
    global roadOffset, propOffset, wheelAngle, bounceT, bounceY
    global lightningTimer, lightningFlash, particlesInited

    # Dynamically initialize and track delta time via function attribute 
    if not hasattr(timer, "lastTime"):
        timer.lastTime = time.perf_counter()

    currentTime = time.perf_counter()
    dt = currentTime - timer.lastTime
    timer.lastTime = currentTime

    # Cap delta-time to avoid sudden massive teleportations during extreme lag spikes
    if dt > 0.1: 
        dt = 0.1

    roadOffset -= carSpeed * 4.5 * dt
    if roadOffset < -DASH_PERIOD:
        roadOffset += DASH_PERIOD

    propOffset -= carSpeed * 4.5 * dt
    if propOffset < -80.0:
        propOffset += 80.0

    distPerFrame = carSpeed * 4.5 * dt
    wheelAngle += (distPerFrame / (2.0 * PI * 0.42)) * 360.0
    if wheelAngle > 360.0:
        wheelAngle -= 360.0

    bounceT += carSpeed * dt
    bounceY  = math.sin(bounceT * 8.0) * 0.022 * carSpeed

    if not particlesInited:
        initParticles()

    precipActive = (currentWeather == RAIN or currentWeather == STORM or currentWeather == SNOW)
    if precipActive:
        isSnow = (currentWeather == SNOW)
        for i in range(MAX_PARTICLES):
            particles[i]['y'] -= particles[i]['speed'] * dt
            particles[i]['x'] += particles[i]['drift'] * dt
            if particles[i]['y'] < -0.5:
                spawnParticle(particles[i], isSnow)

    if currentWeather == STORM:
        lightningTimer -= dt
        if lightningTimer <= 0.0:
            lightningFlash = 1.0
            lightningTimer = randf(2.0, 6.0)
        if lightningFlash > 0.0:
            lightningFlash -= dt * 7.0
            if lightningFlash < 0.0:
                lightningFlash = 0.0
    else:
        lightningFlash = 0.0
        if currentWeather != STORM:
            lightningTimer = randf(2.0, 5.0)

    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

def reshape(w, h):
    global windowWidth, windowHeight
    windowWidth  = w
    windowHeight = h if h != 0 else 1
    glViewport(0, 0, w, h)

def keyboard(key, x, y):
    global currentScenery, currentWeather, currentTimeOfDay, carSpeed
    global lightningFlash, lightningTimer

    if key == b's' or key == b'S':
        currentScenery = (currentScenery + 1) % 3
        glutPostRedisplay()
    if key == b'w' or key == b'W':
        currentWeather = (currentWeather + 1) % 4
        isSnow = (currentWeather == SNOW)
        for i in range(MAX_PARTICLES):
            spawnParticle(particles[i], isSnow)
        lightningFlash = 0.0
        lightningTimer = randf(2.0, 5.0)
        glutPostRedisplay()
    if key == b't' or key == b'T':
        currentTimeOfDay = (currentTimeOfDay + 1) % 2
        glutPostRedisplay()
    if key == b'+' or key == b'=':
        carSpeed += 0.25
        if carSpeed > 4.0: carSpeed = 4.0
    if key == b'-' or key == b'_':
        carSpeed -= 0.25
        if carSpeed < 0.0: carSpeed = 0.0
    if key == b'\x1b':
        sys.exit(0)

# ===============================================================
# MAIN
# ===============================================================
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(windowWidth, windowHeight)
    glutCreateWindow(b"Car Scene - City / Forest / Desert   |   Weather: Clear / Rain / Storm / Snow   |   Day / Night")

    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutTimerFunc(16, timer, 0)
    glutMainLoop()

if __name__ == '__main__':
    main()