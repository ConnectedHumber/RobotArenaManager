# ArenaProcessing.py
#
# Responsible for detecting robots in a camera image
# Stores found bots in botsFound
#
# Camera calibration is done beforehand with CameraScaling.py
#

import sys,traceback
import cv2
import json
import numpy as np
import time
from Params import *
import imutils
from imutils import contours
import math
from Camera import CameraStream
from Decorators import timeit,traceit,tracebot,FPS
from Robot import robot
from Exceptions import *

readParams() # load parameters from Settings.json (See Params.py)

# screen resolutions
# also passed to the camera stream  to set frame size
resolutions={
    # possible images sizes on screen
    1920:(1920,1080),
    1640:(1640,922),
    1440:(1440,810),
    1280:(1280,720),
    640:(640,480),
    480:(480,320)
}

class ArenaProcessor:

    botsFound=[]
    cameraScale=1.0
    showCrossHairs=False
    showMaskRect=False
    showScaleRect=False
    cam=None
    recording=False

    contours=None
    hierarchy=None
    video_writer=None
    scene=None
    botColors={}    # botColors[id]=tuple (R,G,B)

    # dimensions used to detect bot features
    # these will be over written with scaled values from PARAMS
    minBotR, maxBotR, minDirR, maxDirR, minDotR, maxDotR=0,0,0,0,0,0

    def __init__(self,size,cameraIndex=0,recording=False):

        self.recording=recording
        self.cam=CameraStream(size,cameraIndex)
        self.cam.start()

        self.botsFound=[]
        self.scale=Params[PARAM_CAMERA_SCALE]

        # temp - init bot colors
        for b in range(1,9):
            if b<=4:
                self.botColors[b]=(255,0,0)
            else:
                self.botColors[b]=(0,0,255)


        if recording:
            try:
                # print("VideoWriter recording resolution",resolutions[CAPTURE_IMAGE_RES],"fps",VIDEO_FPS )
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                this.video_writer = cv2.VideoWriter("output.avi", fourcc, VIDEO_FPS,size)  # resolutions[SCREEN_IMAGE_RES])
                assert this.video_writer.isOpened(), "Unable to open the VideoWriter."

            except Exception as e:
                print("Video Writer problem",e)
                exit()

        self.adjustBotDimensions()

    def __del__(self):
        """
        Close the camera.
        Destroy all cv2.imshow() windows - if any
        The windows are use for debugging.
        :return: nothing
        """
        if self.video_writer is not None: video_writer.release()
        self.cam.release()
        cv2.destroyAllWindows()

    def stop(self):
        if self.video_writer is not None: video_writer.release()
        self.cam.release()
        cv2.destroyAllWindows()

    def adjustBotDimensions(self):
        '''
        The size of bots and other features changes with screen resolution
        The sizes in the data file (Settings.json) were determined using a screen
        resolution of 1920x1080

        :return: Adjusted dimensions
        '''

        ratio = Params[PARAM_FRAME_WIDTH] / 1920

        self.minBotR = int(Params[PARAM_MIN_BOT_R] * ratio)
        self.maxBotR = int( Params[PARAM_MAX_BOT_R] * ratio)
        self.minDirR = int(Params[PARAM_MIN_DIRECTOR_R]* ratio)
        self.maxDirR = int(Params[PARAM_MAX_DIRECTOR_R] * ratio)
        self.minDotR = int(Params[PARAM_MIN_DOT_R] * ratio)
        self.maxDotR = int(Params[PARAM_MAX_DOT_R] * ratio)

    def setCameraProps(self):

        for PROP in [CV2_CAMERA_BRIGHTNESS, CV2_CAMERA_CONTRAST, CV2_CAMERA_SATURATION, CV2_CAMERA_EXPOSURE,
                     CV2_CAMERA_ISO_SPEED]:
            prop, option = PROP
            self.cam.setCAP(prop, Params[option])

    def setDefaultCameraProps(self):
        global cam, DefaultParams

        for PROP in [CV2_CAMERA_BRIGHTNESS, CV2_CAMERA_CONTRAST, CV2_CAMERA_SATURATION, CV2_CAMERA_EXPOSURE,
                     CV2_CAMERA_ISO_SPEED]:
            prop, option = PROP
            self.cam.set(prop, DefaultParams[option])

    def showImage(self,windowTitle, image, res=None):
        '''
        Display the image at the requested width (res)
        :param windowTitle: window title text
        :param image: image to display
        :param res: image width for display or -1 for no scaling
        :return: None
        '''
        assert image is not None, "showImage() requires an image. None was supplied."

        h,w = image.shape[:2]

        if res is None or w == res:
            # no scaling
            cv2.imshow(windowTitle, image)
            return

        # display the scaled image
        dim = resolutions[res]
        # method can be INTER_NEAREST, INTER_LINEAR,INTER_AREA,INTER_CUBIC,INTER_LANCZO4
        # all of them screw up text readability when image is scaled
        cv2.imshow(windowTitle, cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR))

    def addRobotDirector(self, x, y):
        '''
        Scan the botsFound list and try to add this director
        The director is a dot or rectangle larger than an ID dot
        and smaller than the minimum robot size. The v=centre coords of the
        director together with the centre coords of the robot allow us to determine
        the heading.

        :param x: float pixel x pos
        :param y: float pixel y pos
        :return: True if added otherwise False
        '''
        for bot in self.botsFound:
            # try to add a directory location
            if bot.setDirector((x, y)):
                return True
        return False

    def addRobotIdDot(self, x, y):
        '''
        Scan the list of robots and try to add this dot
        This is done by checking if the dot coords are within a robot.

        Dots identify the robot number

        :param x:   float pixel Dot xpos
        :param y:   float pixel Dot ypos
        :return: True if added otherwise false
        '''

        for bot in self.botsFound:
            # try to add a directory location
            if bot.addIdDot((x, y)):
                return True
        #print("Unable to add Id dot",x,y)
        return False

    def distBetween(self,pt1,pt2):
        '''
        Calculate the distance between points

        :param pt1: tuple (x,y) coords of point 1
        :param pt2: tuple (x,y) coords of point 2
        :return: float distance between the points
        '''
        diffX=abs(pt1[0]-pt2[0])
        diffY=abs(pt1[1],pts2[1])
        return math.sqrt(diffX*diffX+diffY*diffY)

    def addRobot(self,contour):
        '''
        Puts thisBot into the botsFound list

        checks the contour is of an appropriate size and
        that the robot isn't already in the list

        :return: True if added, False if not
        '''

        # check the rough size
        (x, y), r = cv2.minEnclosingCircle(contour)

        # minBotR and maxBotR were scaled for this scenne res
        if (r < self.minBotR) or (r > self.maxBotR): return False

        # todo there needs to be a significant distance between
        for prevBot in self.botsFound:
            r = cv2.pointPolygonTest(prevBot.getContour(), (x, y), False)
            if r >= 0:
                #print("addBot() WARNING: bot already exists")
                return False

        # hopefully get the four corners of the rectangle
        # they are needed for pointPolygonTest() and drawing
        # the bot outline

        rect = cv2.minAreaRect(contour)  # allows for rotation
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        thisBot = robot()
        thisBot.setLocation((x, y))
        thisBot.setSize(r)
        thisBot.setContour(box)
        # thisBot.drawOutline(scene) # defaults to cyan till the botId is known
        self.botsFound.append(thisBot)

    def drawScaleRect(self):
        '''
        Draws a scaled A4 rectangle to allow the camera scale to be set
        This gives us the
        :return:
        '''
        H, W = self.scene.shape[:2]
        CX = W / 2
        CY = H / 2
        # assum
        sx,sy=Params[PARAM_SCALE_RECT_SIZE]
        rw, rh = sx * Params[PARAM_CAMERA_SCALE], sy * Params[PARAM_CAMERA_SCALE]

        # target rectangle points
        TL = (int(CX - rw / 2), int(CY - rh / 2))
        BR = (int(CX + rw / 2), int(CY + rh / 2))

        # draw the scaled recangle
        cv2.rectangle(self.scene, TL, BR, (0, 255, 0), 1)

    def drawMaskRectangle(self):
        '''
        draws a rectangle showing the masked area
        :return: None
        '''
        frame_h, frame_w = self.scene.shape[:2]

        mask_scale = Params[PARAM_ARENA_MASK_SCALE]

        (mask_w, mask_h) = Params[PARAM_ARENA_MASK_SIZE]
        mask_w = int(mask_w * mask_scale)
        mask_h = int(mask_h * mask_scale)
        y = int((frame_h - mask_h) / 2)
        x = int((frame_w - mask_w) / 2)
        cv2.rectangle(self.scene, (x, y), (x + mask_w, y + mask_h), (0, 255, 255), 1)

    def drawCrossHairs(self):
        '''
        add a white cross to the scene. The cross passes through the centre of the scene
        horizontally and vertically - mostly for checking the heading values are correct
        :return: None
        '''
        H, W = self.scene.shape[:2]
        halfW = int(W / 2)
        halfH = int(H / 2)

        cv2.line(self.scene, (0, halfH), (W, halfH), (255, 255, 255), 1)
        cv2.line(self.scene, (halfW, 0), (halfW, H), (255, 255, 255), 1)

    def analyseThisContour(self,contour):
        '''
        checks contour to see if it fits any attributes of the robot
        :param contour: the contour to analyse
        :return: None but the robot director or dots are, possibly, updated
        '''

        # the enclosing circle works for all shapes
        (x, y), r = cv2.minEnclosingCircle(contour)
        x = int(x)
        y = int(y)
        r = int(r)

        if r > self.minBotR or r == 0:
            return  # robots are added first

        #print ("analyseThisContour dot or director at",x,y,"rad",r)
        #print("min,max Dir",self.minDirR,self.maxDirR, "min,max,dot",self.minDotR,self.maxDotR)

        if r >= self.minDirR and r < self.maxDirR:
            #print("Add director")
            self.addRobotDirector(x, y)

        # assume all small features are potential dots
        # this could be the wrong thing to do with a noisy
        # image
        else:
            #print("Add dot")
            self.addRobotIdDot(x, y)

    def processContours(self):
        '''
        Called after the bots have been identified and added to the
        botsFound list to locate ID dots and director shapes (used for heading)
        :param save: True means save the contorus to file
        :return: Nothing
        '''

        for c in self.contours:
            self.analyseThisContour(c)

        for bot in self.botsFound:
            # draw the bot outline and put its number in the middle so
            # people can see where their bots are
            botId=bot.getId()
            if botId in self.botColors:
                bot.setColor(self.botColors[botId])
            bot.drawOutline(self.scene)
            bot.drawId(self.scene)
            # bot.annotate(self.scene)


    ##############################################################################
    #
    # Main methods meant to be called by ArenaManager
    #
    ##############################################################################
    #@FPS
    def update(self):
        '''
        Called from ArenaManager to update the scene image and bot information
        :return: updated scene
        '''
        self.botsFound = []

        # print("Set camera props")
        self.setCameraProps()    # incase changed`dynamically
        # print("Update arena mask")
        # self.updateArenaMask()   # incase the mask has been dynamically changed

        self.scene = self.cam.readBGR()

        assert self.scene is not None,"Unable to load scene image - is the camera running?"

        # we use the feature edges to extract contours
        edges = self.cam.readEDGES()
        # self.showImage("Cam Edges", edges)

        # this finds all the robot outlines in edges but not the inner shapes
        # it helps to setup the bots first and doesn't take long
        # sometimes this returns more contoors than bots - probably
        # due to noise and non-closed contours
        botContours = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        botContours = botContours[0]

        # cv2.drawContours(self.scene,botContours,-1,(0,255,255),1) # debugging

        #print("Num Contours=", len(botContours))
        # scan for robots
        for c in botContours:
            self.addRobot(c)  # checks size and adds to botsFound list if ok

        #print("Num bots=", len(self.botsFound))
        # now search for dots and directorsq

        self.contours, self.hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        self.hierarchy = self.hierarchy[0]  # hierarchy is a list of arrays

        self.processContours()  # brute force approach since following heirarchy didn't work well

        # show cross hairs to show heading is correct
        # just two lines drawn through the centre of the image
        if self.showCrossHairs: self.addCrossHairs()
        if self.showMaskRect:   self.addMaskRectangle()
        if self.showScaleRect:  self.addScaleRect()

        if self.recording: video_writer.write(scene)

        return self.scene

    def getRobots(self):
        '''
        ArenaManager calls this to retrieve the bot information
        after the last call to update

        X,Y coordinates
        :return: dictionary allBots[botId]=(x,y),heading
        '''
        allBots={}
        for bot in self.botsFound:
            pos=bot.getLocation()
            # adjust for camera scale turns pixels into mm
            scaled_pos=(int(pos[0]*Params[PARAM_CAMERA_SCALE]),int(pos[1]*Params[PARAM_CAMERA_SCALE]))
            allBots[bot.getId()]=scaled_pos,bot.getHeading()

        return allBots

    def enableMaskDisplay(self, on=False):
        self.showMaskRect = on

    def enableScaleDisplay(self, on=False):
        self.showScaleRect = on

    def enableCrosshairDisplay(self, on=False):
        self.showCrosshair = on

    def setBotColors(self,colors):
        '''
        Sets the colours dictionary for the bots
        This allows bots to have seperate colours, if we want that

        Note the default is blue for bots 1-4 and red for 5-8

        :param colors: dict[botId]=color tuple (r,g,b)
        :return: nothing
        '''
        self.botColors=colors

    def setBotColor(self,botId,color):
        '''
        Set the color to use for one bot only
        :param botId: int bot number
        :param color: tuple (r,g,b) colour to use
        :return: Nothing
        '''
        if botId in self.botColors:
            self.botColors[botId]=color

    # dot sizes may need to be adjusted up
    def setDotSize(self,min,max):
        ratio = 1 / (Params[PARAM_FRAME_WIDTH] / 1920)
        self.minDotR=min*ratio
        self.maxDotR=max*ratio

    def setDirSize(self, min, max):
        '''
        Sets the colours dictionary for the bots
        This allows bots to have seperate colours, if we want that
        :param colors: dict[botId]=color tuple (r,g,b)
        :return: nothing
        '''
        ratio = 1 / (Params[PARAM_FRAME_WIDTH] / 1920)
        self.minDirR = min*ratio
        self.maxDirR = max*ratio

    def setBotSize(self,min,max):
        ratio = 1/(Params[PARAM_FRAME_WIDTH] / 1920)
        self.minBotR=min*ratio
        self.maxBotR=max*ratio

if __name__ == "__main__":
    # debugging only
    # allows this module to be run before plumbing it in to ArenaManager
    # get a video stream and pump frame into imgprocessor.update

    # all done at max resolution
    size=resolutions[1920]

    AP= ArenaProcessor(size)  # uses values from Settings.json

    print("Running")
    try:
        while True:
            outFrame = AP.update()
            robots=AP.getRobots()

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                AP.stop()
                break

            cv2.imshow("outFrame", outFrame)

    except Exception as e:
        PrintException()
        traceException(5)   # traceback depth 5
        AP.stop()
        cv2.destroyAllWindows()
