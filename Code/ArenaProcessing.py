"""
ArenaProcessing_V1.py

Responsible for detecting robots in a camera image (Arena) then recording their
position and nautical heading

Uses Settings.py and Params.py

Setup Tools:

Used to to record/read user adjustable parameters which control the robot detection
and identification

CameraScaling.py    adust the scale factor to match an A4 shape
                    this gives us the pixel to millimetre ratio
                    so that the physical position of a robot can
                    be determined

CameraSetup.py      allows you to adjust parameters which affect the
                    edge detection

CameraMask.py       allows you to setup a mask to exclude objects
                    on the periphery of the arena - should speed up processing

ArenaSetup.py       allows you to adjust feature sizes which determine if a
                    shape is robot, ID dot or direction indicator.


"""

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

TEAM_A_COLOR=(255,0,0)
TEAM_B_COLOR=(0,0,255)
NUM_ROBOTS=8

readParams() # load parameters from Settings.json (See Params.py)

###################################################################
class ArenaProcessor:
    '''
    ArenaProcessor processe camera images to locate robots.

    Takes Full size color video frames from the camera and the EDGES imaage.
    The contours are then found in the EDGES image and used to identify the
    robots and their positions.

    The color image is then overlaid with robot identification information
    and passed back to the ArenaManager for streaming.

    Records the robot information for the ArenaManager to use.

    '''

    botsFound=[]
    cameraScale=1.0
    showCrossHairs=False
    showMaskRect=False
    useingSmallEDGES=False

    showScaleRect=False
    cam=None
    recording=False

    contours=None
    hierarchy=None
    video_writer=None
    recordingFps=0      # higher values cause recording to take place
    scene=None
    botColors={}    # botColors[id]=tuple (R,G,B)
    maskOffsets=(0,0)    # x,y position of smallEDGES image mnsk

    def __init__(self,size,useSmallEDGES=False, cameraIndex=0,recordingFps=0):
        '''
        Initialise the ArenaProcessor

        Sets the frame size and camera to use.

        If useSmallEDGES is True uses the camera's small EDGES (ROI) image which is determined by the
        arena mask size. If the mask is smaller than the frame size this could improve the
        frame processing rate.

        :param size: tuple (w,h) of the video frame
        :param useSmallEDGES: boolean True to use the masked EDGES frame
        :param cameraIndex: int default 0, camera to use (see openCV VideoCapture())
        :param recordingFPS: int recording frame rate Turns on video recording if >0
        '''
        self.usingSmallEDGES=useSmallEDGES

        self.recordingFps=recordingFps
        self.cam=CameraStream(size,cameraIndex)
        self.cam.start()

        # setup the image mask
        maskW,maskH=Params[PARAM_ARENA_MASK_SIZE]
        self.cam.makeMask(maskW,maskH)
        self.maskOffsets=self.cam.getMaskOffsets()

        self.botsFound=[]
        self.scale=Params[PARAM_CAMERA_SCALE]

        # temp - init bot colors
        for b in range(1,NUM_ROBOTS+1): # range stops one short
            if b<=4:
                self.botColors[b]=TEAM_A_COLOR
            else:
                self.botColors[b]=TEAM_B_COLOR

        # Video recording?
        if recordingFps>0:
            try:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter("output.avi", fourcc, recordingFps,size)
                assert self.video_writer.isOpened(), "Unable to open the VideoWriter."
                print("Recording to output.avi at",recordingFps,"fps")
            except Exception as e:
                print("Video Writer problem",e)
                exit()

    def __del__(self):
        """
        Close the camera and exit

        Destroys all cv2.imshow() windows - if any
        The windows are used for debugging.

        :return: nothing
        """
        if self.video_writer is not None:
            self.video_writer.release()
        self.cam.release()
        cv2.destroyAllWindows()

    def stop(self):
        '''
        Exit in a tidy manner.

        See also __del__()

        :return: Nothing
        '''
        if self.video_writer is not None:
            self.video_writer.release()
        self.cam.release()
        cv2.destroyAllWindows()

    def setCameraProps(self):
        '''
        set camera properties using the stored settings file.

        :return: Nothing
        '''

        for PROP in [CV2_CAMERA_BRIGHTNESS, CV2_CAMERA_CONTRAST, CV2_CAMERA_SATURATION, CV2_CAMERA_EXPOSURE,
                     CV2_CAMERA_ISO_SPEED]:
            prop, option = PROP
            self.cam.setCAP(prop, Params[option])

    def setDefaultCameraProps(self):
        '''
        Set the camera default properties
        :return: Nothing
        '''

        for PROP in [CV2_CAMERA_BRIGHTNESS, CV2_CAMERA_CONTRAST, CV2_CAMERA_SATURATION, CV2_CAMERA_EXPOSURE,
                     CV2_CAMERA_ISO_SPEED]:
            prop, option = PROP
            self.cam.set(prop, DefaultParams[option])

    def showImage(self,windowTitle, image, res=None):
        '''
        Display the image at the requested width (res)

        :param windowTitle: window title text
        :param image: image to display
        :param res: image width for display or -1/None for no scaling
        :return: Nothing
        '''
        assert image is not None, "showImage() requires an image. None was supplied."

        h,w = image.shape[:2]

        if res is None or w == res:
            # no scaling
            cv2.imshow(windowTitle, image)
            return

        # display the scaled image
        # maintaining aspect ratio
        aspect=res/w
        newW=int(w*aspect)
        newH=int(h*aspect)
        # method can be INTER_NEAREST, INTER_LINEAR,INTER_AREA,INTER_CUBIC,INTER_LANCZO4
        # all of them screw up text readability when image is scaled
        cv2.imshow(windowTitle, cv2.resize(image, (newW,newH), interpolation=cv2.INTER_LINEAR))

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

        # NOTE: if the system is using the smallEDGES x and y will
        # have been compensated already

        for bot in self.botsFound:
            # try to add a directory location

            if bot.setDirector((x, y)):
                return True
        #cv2.circle(self.scene,(int(x),int(y)),12,(255,255,0),2)
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
        # NOTE: if the system is using the smallEDGES x and y will
        # have been compensated already

        # scan known bots and try to add the dor
        for bot in self.botsFound:
            # try to add a directory location
            if bot.addIdDot((x, y)):
                return True
            #print("Unable to add dot @",x,y,"to robot @",bot.getLocation(),"contour",bot.getContour())
            #cv2.circle(self.scene,(x,y),5,(0,255,255),2)
            #exit()
        return False

    def distance(self, pos1, pos2):
        '''
        calculate the distance between two points using pythagorus

        Mainly used to work out the aspect ratio of the rectangular
        bot hat

        :param pos1: tuple (x,y)
        :param pos2: tuple (x,y)
        :return: float pixel distance between points
        '''
        x1, y1 = pos1
        x2, y2 = pos2
        diffX = abs(x1 - x2)
        diffY = abs(y1 - y2)
        return math.sqrt(diffX * diffX + diffY * diffY)

    def getAreaAndAspect(self,box):
        '''
        Calculate the aspect ratio and area of a rectangle

        Used to validate a shape as a probable robot

        :param box: list of corner co-ordinates [[x0 y0]...[x4 y4]]
        :return float,float: the area and aspect ratio between adjacent sides
        '''
        # calc length of side adjacent sides
        x0,y0=box[0]
        x1,y1=box[1]
        x2,y2=box[2]

        side1=self.distance(box[0],box[1])
        side2=self.distance(box[1],box[2])

        area=side1*side2

        # normalise so that ratio is <1.0
        # fudge to avoid division by zero
        if side1==0 or side2==0:
            return area,1.0

        if side1>side2: return area,side2/(side1)
        return area,side1/(side2)


    def addRobot(self,contour):
        '''
        Identifies this contour as a robot and adds it to the botsFound dict

        checks the contour is of an appropriate size (area), aspect ratio and
        that the robot isn't already in the list.

        :return: True if added, False if not
        '''

        # check rectangular aspect
        rect = cv2.minAreaRect(contour)  # allows for rotation
        box = cv2.boxPoints(rect)

        area,aspect = self.getAreaAndAspect(box)

        max_aspect = Params[PARAM_MAX_BOT_ASPECT_RATIO]
        min_aspect = Params[PARAM_MIN_BOT_ASPECT_RATIO]
        if aspect < min_aspect or aspect > max_aspect:
            # not a robot
            #print("- Apect ratio out of allowed range ", min_aspect, max_aspect, "was", aspect)
            return False

        # adjust XY coordinates if using the ROI mask
        if self.usingSmallEDGES:
            maskX, maskY = self.maskOffsets
            for pt in range(len(box)):
                bx, by = box[pt]
                box[pt] = (bx + maskX, by + maskY)

        # make a proper contour
        box = np.int0(box)

        # check the contour area the current robot is between 6000 and 9000 sq pixels
        # a contour could have a valid aspect ratio but be the wrong size

        #print("Contour area ",area ,"expecting min",Params[PARAM_MIN_BOT_AREA],"max",Params[PARAM_MAX_BOT_AREA])
        if area<Params[PARAM_MIN_BOT_AREA] or area>Params[PARAM_MAX_BOT_AREA]:
            #cv2.drawContours(self.scene,contour,-1,(0,0,255),2)
            #print("- bot area out of range",area)
            if area<Params[PARAM_MIN_BOT_AREA]:
                #print("Bot area below allowed range was",area)
                pass
            elif area>Params[PARAM_MAX_BOT_AREA]:
                # print this so we can manually adjust if necessary
                print("- Bot area above allowed range was",area)
            return False

        (botX, botY), botR = cv2.minEnclosingCircle(contour)
        # allow for a mask offset
        botX, botY = self.compensateXY(botX, botY)

        for prevBot in self.botsFound:
            result = cv2.pointPolygonTest(prevBot.getContour(), (botX, botY), False)
            if result >= 0:
                # bot already exists
                #print("- Bot @",botX,botY,"already seen")
                return False

        thisBot = robot()
        thisBot.setLocation((botX, botY))
        thisBot.setSize(botR)   # depracated
        thisBot.setContour(box) # now use contour instead
        self.botsFound.append(thisBot)

        #print("- addRobot() OK @",botX,botY,"contour",box)
        #cv2.circle(self.scene, (botX, botY), int(botR), (0, 255, 255), 2)
        return True

    def drawScaleRect(self):
        '''
        Draws a scaled A4 rectangle on self.scene to allow the camera scale to be shown/set..

        This gives us the pixel/mm ratio since we know the size of an A4
        shape.


        :return: nothing, the rectangle is drawn
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
        Draws a rectangle on self.scene showing the masked area

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
        Add a white cross to the scene.

        The cross passes through the centre of the scene
        horizontally and vertically - mostly for checking the heading values are correct
        :return: None
        '''
        H, W = self.scene.shape[:2]
        halfW = int(W / 2)
        halfH = int(H / 2)

        cv2.line(self.scene, (0, halfH), (W, halfH), (255, 255, 255), 1)
        cv2.line(self.scene, (halfW, 0), (halfW, H), (255, 255, 255), 1)

    def compensateXY(self,x,y):
        '''
        adds the mask offset to x and y if a mask is being used

        :param x: pixel point x pos
        :param y: pixel point y pos
        :return: tuple (x,y) integer values
        '''
        if self.usingSmallEDGES:
            maskX,maskY=self.maskOffsets
            x=x+maskX
            y=y+maskY
        return int(x),int(y)    # whole pixels

    def processContours(self):
        '''
        Locate ID dots and director shapes (used for heading)

        ID dots and directors are identified by using cv2.minEnclosingCircle().
        A bit clutzy - scans all contours for dots then scans
        all contours again for direction indicators
        TODO remove used contours to speed up following pass??

        :return: Nothing
        '''

        # scan for the direction dots first
        # this stops ID dots being classed as Direction indicators
        for c in self.contours:
            (x, y), r = cv2.minEnclosingCircle(c)
            if r>=Params[PARAM_MIN_DIRECTOR_R]and r<=Params[PARAM_MAX_DIRECTOR_R]:
                x,y=self.compensateXY(x,y)
                self.addRobotDirector(x, y)


        # now scan for ID dots
        for c in self.contours:
            (x, y), r = cv2.minEnclosingCircle(c)
            if r>=Params[PARAM_MIN_DOT_R] and r<=Params[PARAM_MAX_DOT_R]:
                x, y = self.compensateXY(x, y)
                self.addRobotIdDot(x, y)

        for bot in self.botsFound:
            # draw the bot outline and put its number in the middle so
            # people can see where their bots are
            botId=bot.getId()
            if botId is None:
                print("No bot id for bot @",bot.getLocation())
            # bot outline colour default is cyan
            if botId in self.botColors:
                bot.setColor(self.botColors[botId])
            bot.drawOutline(self.scene)
            #bot.drawScaledOutline(self.scene)

            # debugging
            avgDotR=(Params[PARAM_MIN_DOT_R]+Params[PARAM_MAX_DOT_R])//2
            bot.drawDots(self.scene,avgDotR)

            avgDirR=(Params[PARAM_MIN_DIRECTOR_R]+Params[PARAM_MAX_DIRECTOR_R])//2
            bot.drawDirector(self.scene,avgDirR)

            bot.drawId(self.scene)
            # bot.annotate(self.scene)

    def updateArenaMask(self):
        '''
        tell the camera the size of mask to use during image processing

        :return: Nothing
        '''
        w,h=Params[PARAM_ARENA_MASK_SIZE]
        self.cam.makeMask(int(w),int(h))

    ##############################################################################
    #
    # Main methods meant to be called by ArenaManager
    #
    ##############################################################################
    @FPS
    def update(self):
        '''
        Called from ArenaManager to update the scene image and bot information

        :return: numpy array updated scene image
        '''
        print("\nUPDATE Pass\n")

        self.botsFound = []
        self.setCameraProps()    # incase changed`dynamically
        self.updateArenaMask()   # incase the mask has been dynamically changed
        self.maskOffsets=self.cam.getMaskOffsets()
        self.scene = self.cam.readBGR()

        assert self.scene is not None,"Unable to load scene image - is the camera running?"

        # we use the feature edges to extract contours
        # if the arena mask is smaller than the video frame size
        # using the smallEDGES image should be quicker
        # when there is no mask the images are the same
        if self.usingSmallEDGES:
            edges=self.cam.readSmallEDGES()
        else:
            edges = self.cam.readEDGES()

        # temprary whilst debugging
        #cv2.imshow("EDGES",edges)

        # this SHOULD find all the robot outlines in edges but not the inner shapes
        # it helps to setup the bots first and doesn't take long with 8 bots.
        # sometimes this returns more contoors than bots - probably
        # due to noise and non-closed contours. Size is checked before acceptance

        # botContours are not used outside here
        # hierarchy isn't used
        # RETR_EXTERNAL is used to locate the outer shape of the contours
        botContours,hierarchy= cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #print("RETR_EXTERNAL Num Contours=",len(botContours))
        #print("Hierarchy",hierarchy[0])
        # scan for robots
        for c in botContours:
            self.addRobot(c)  # checks size and adds to botsFound list if ok
        #print("BotsFound=",len(self.botsFound))
        #print("FINISHED SCANNING FOR BOTS\n")
        # now search for dots and direction indicators
        # these are a lot smaller than the robot

        # hierarchy is not used
        self.contours,self.hierarchy= cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #if self.hierarchy is not None: self.hierarchy=self.hierarchy[0]    # not used
        if self.contours is not None:
            self.processContours()  # looking for dots and direction indicators

        # show cross hairs to show heading is correct
        # just two lines drawn through the centre of the image
        if self.showCrossHairs: self.addCrossHairs()
        if self.showMaskRect:   self.addMaskRectangle()

        if self.showScaleRect:  self.addScaleRect()

        if self.recordingFps>0:
            self.video_writer.write(self.scene)

        return self.scene.copy()

    def getRobots(self):
        '''
        Retrieve the current bot position and heading.

        Called by ArenaManager after the last call to update()
        :return: dict allBots[botId]=(x,y),heading
        '''
        allBots={}
        for bot in self.botsFound:
            pos=bot.getLocation()
            # adjust locations for camera scale turns pixels into mm
            scaled_pos=(int(pos[0]*Params[PARAM_CAMERA_SCALE]),int(pos[1]*Params[PARAM_CAMERA_SCALE]))
            allBots[bot.getId()]=scaled_pos,bot.getHeading()

        return allBots

    def enableMaskDisplay(self, on=False):
        '''
        Draw a mask rectangle over the image to show the boundaries of the arena mask

        The mask (if smaller than the video frame size) limits the image processing
        to that rectangular area. Used to exclude anything that isn't part of the arena
        hence remove unwanted edges/contours.

        :param on: True means add the mask rectangle
        :return: Nothing
        '''
        self.showMaskRect = on

    def enableScaleDisplay(self, on=False):
        '''
        An A4 landcape shape is used to scale the camera x,y coords
        into millimetres instead of pixels.

        This enables drawing of that scaled shape (rectangle) on the output image

        :param on: True means add the scale rectangle
        :return: Nothing
        '''
        self.showScaleRect = on

    def enableCrosshairDisplay(self, on=False):
        '''
        The croshair display is two lines drawn vertically and horizontally through
        the centre of the output image. Useful for checking calculated bot headings
        and centering of the arena elow the camera.

        :param on: True means add the crosshairs
        :return: Nothing
        '''
        self.showCrosshair = on

    ###############################################################################
    #
    # methods used by ArenaSetup.py for tuning the bot detection parameters
    # ArenaSetup.py will save these values is so required
    #

    def setBotColors(self,colors):
        '''
        Sets the colours dictionary for the bots

        This allows bots to have seperate colours, if we want that.
        The default is a red team and blue team each with 4 bots.
        bots 1-4 are blue and 5-8 are red

        :param colors: dict[botId]=color tuple (r,g,b)
        :return: nothing
        '''
        self.botColors=colors

    def setBotColor(self,botId,color):
        '''
        Set the color to use for one bot only

        Useful to visually flag a bot as dead etc.
        :param botId: int bot number
        :param color: tuple (r,g,b) colour to use
        :return: Nothing
        '''
        if botId in self.botColors:
            self.botColors[botId]=color

    def setDotSize(self,min,max):
        '''
        Set the min and max ID dot size

        Used by ArenaSetup to 'tune' the ID dot size

        :param min: int min id dot pixel radius
        :param max: int max id dot pixel radius
        :return: Nothing
        '''
        Params[PARAM_MIN_DOT_R]=min
        Params[PARAM_MAX_DOT_R]=max

    def setDirSize(self, min, max):
        '''
        Set the director min and max pixel radii

        Used by ArenaSetup to tune the direction indicator size

        :param min: int min pixel radius
        :param max: int max pixel radius
        :return: Nothing
        '''
        Params[PARAM_MIN_DIR_R] = min
        Params[PARAM_MAX_DIR_R]= max

    def setBotAreaSize(self,min,max):
        '''
        Set the min and max area used for bot detection

        :param min: int min area (pixels^2)
        :param max: int max area
        :return: Nothing
        '''
        Params[PARAM_MIN_BOT_AREA]=min
        Params[PARAM_MAX_BOT_AREA]=max

    def setBotAspectSize(self,min,max):
        '''
        Set the min and max aspect ratio for bot detection

        :param min: float min aspec ratio
        :param max: float max aspect raio
        :return: Nothing
        '''
        Params[PARAM_MIN_BOT_ASPECT_RATIO]=min
        Params[PARAM_MAX_BOT_ASPECT_RATIO]=max
########################################################################
#
# Manual Testing
#

if __name__ == "__main__":
    # for debugging only
    # allows this module to be run before plumbing it in to ArenaManager
    # get a video stream and pump frame into imgprocessor.update

    # all done at max resolution
    size=(1920,1080)

    FPS=0   # zero turns off video recording
    CAM=0
    USE_SMALL_EDGES=True

    AP= ArenaProcessor(size,USE_SMALL_EDGES,CAM,FPS)  # uses values from Settings.json

    print("Test Running")
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
        traceException(5)   # traceback depth 5
        AP.stop()
        cv2.destroyAllWindows()
