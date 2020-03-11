"""
Camera.py
Purpose is to provide the most current video frame and to analyse it
to obtain the edges
Two threads are used. One collects the most recent BGR frame in an attempt to
ensure the caller has the latest BGR image and so reduce lag.
The second thread runs to process the BGR image creating a grayscale,
thesholded and edged version of the masked region of the BGR
Threading locks are used to ensure image updating/reading takes place on
a stable image at all times
typical usage:
    from FastCameraStream import CameraStream
    vs=CameraStream(path)           # defaults to first camera
    vs.setCAP(cv2.CAP...,value)     # set camera capabilities
    vs.setMask(w,h)                 # excludes regions outside the image
    vs.start()                      # starts the processBGR() method as a background task
    #grab the scene - we will draw contours on it later
    scene=vs.readBGR()
    # getting contours
    edges=vs.readEDGES()    # this could be several frames behind the BGR due to conversion time
    contours = cv2.findContours(edges,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # draw all the contours (-1 signifies this) in green 2 pixels wide
    cv2.drawContours(scene, contours, -1, (0, 255, 0), 2)
    cv2.imshow("scene",scene)
    cv2.waitKey(0)
    vs.stop() or vs.release()
    cv2.destroyAllWindows()
"""

import cv2
import time
import threading
from Decorators import timeit,traceit,tracecam
from Params import *
from CameraProperties import props
import numpy as np

readParams()

class CameraStream:

    maskROI=(0,0,0,0)   # use as [Y1:Y2,X1:X2]

    def __init__(self, size, index=0):
        '''
        initialise variables and start the BGR image collector
        :param size: tuple (w,h) of the captured camera video frame
        :param index: zero based camera index
        '''
        begin=time.time()

        print("Camera: Initialising")
        print("Camera: capture resolution=",size)

        (self.frame_w,self.frame_h)=size
        (self.mask_w,self.mask_h)=size

        self.stream = cv2.VideoCapture(index)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_w)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_h)

        self.stopped = False

        # images created during conversion
        self.BGRcam=None    # temp, current camera frame
        self.BGR=None       # copy of BGRcam
        self.GRAY=None      # gray scale
        self.THRESH=None    # thresholded gray scale
        self.EDGES=None     # canny edges

        self.BGRlock = threading.Lock()     # lock used with framme aquisition
        self.UPDATElock=threading.Lock()    # locak used to make sure user readable images are in sync

        self.threshold=Params[PARAM_THRESH_MIN]   # values to use for thresholding gray scale images
        self.thresholdAfterCanny=Params[PARAM_AFTER_CANNY_THRESH_MIN]
        self.brightness=Params[PARAM_CAMERA_BRIGHTNESS]
         # millisec?
        self.ISO=Params[PARAM_CAMERA_ISO_SPEED]
        self.AutoExposure=Params[PARAM_CAMERA_AUTO_EXPOSURE]    # must be before exposure in case disabled
        self.exposure = Params[PARAM_CAMERA_EXPOSURE]
        self.contrast=0
        self.gain=0.01

        self.cannyMin = Params[PARAM_CANNY_MIN]
        self.cannyMax = Params[PARAM_CANNY_MAX]


        self.startBGRCollector()
        while self.BGRcam is None: # normally takes 1.07s
            pass

        # chnages to camera settings needs to be done after the camera has captured
        # its first image

        if self.stream.get(cv2.CAP_PROP_BRIGHTNESS)!=-1:
            # camera supports brightness properties
            self.stream.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness)
        else:
            if self.setCAP(cv2.CAP_PROP_AUTO_EXPOSURE,0.25):    # turn it off 0.75 is on
                self.setCAP(cv2.CAP_PROP_EXPOSURE, self.exposure)

        print("Camera: first image obtained in {0:2.2f} seconds".format((time.time() - begin)))

        # set the mask to use from the saved mask size
        w,h=Params[PARAM_ARENA_MASK_SIZE] # dimensions in pixels
        #scale=Param[PARAM_ARENA_MASK_SCALE] is this needed?
        self.makeMask(int(w),int(h))

        self.convertBGR()   # create initial GRAY,THRESH and EDGES images

        print("Camera: __init__ finished")

    def __del__(self):
        '''
        called when the program terminates to protect against
        failing to call stop() or release()
        This ensures background threads are stopped.
        :return:
        '''
        if not self.stopped:
            self.stopped=True
            #print("Waiting for CameraStream thread to stop active=",threading.active_count())
            #while threading.active_count()>0:
            #    pass
            self.stream.release()
            time.sleep(1)
            #print("After sleep active=",threading.active_count())

    def collectBGR(self):
        '''
        Thread to ensure BGR is always the latest frame
        :return:
        '''
        while True:

            try:
                (grabbed,BGR) = self.stream.read()

                if grabbed:
                    with self.BGRlock:
                        self.BGRcam = BGR  # save till convertBGR() runs
                else:
                    print("Unable to read camera stream")
            except Exception as e:
                print("Exception in collectBGR()")
                print(e)

            if self.stopped: return

    def startBGRCollector(self):
        '''
        getting the next frame from the camera is done in a separate thread
        :return:
        '''
        self.stopped=False
        t = threading.Thread(target=self.collectBGR, args=())
        t.daemon = True
        t.start()


    def start(self):
        '''
        Start a thread to process the last BGR frame captured from the camera
        locks are used to prevent simultaneous access whilst the image is being written or read
        :return: None
        '''

        t = threading.Thread(target=self.processBGR, args=())
        t.daemon = True
        t.start()
        self.stopped=False

    def ready(self):
        '''
        Check if we have an EDGES image. If so processBGR() has
        converted the BGR image and it is then safe to call readBGR(), readGRAY(), readEDGES()
        or readTHRESH()
        :return: True or False
        '''
        with self.UPDATElock:   # conversion may be taking place
            if self.EDGES is None: return False
            return True

    ##################################
    #
    # methods intended for dynamic changing of parameters
    #
    ##################################

    #@traceit
    def setCAP(self,CAP,Value):
        '''
        Allow caller to set the camera capabilities
        Invalid values for Value can cause exceptions. These need to be trapped
        to stop the process dying with threads still active.
        :param CAP: an openCV property like cv2.CAP_PROP_FRAME_WIDTH
        :param Value: suitable value
        :return: True if set , False if not
        '''
        try:
            # supported?
            if self.stream.get(CAP)==-1:
                print("Camera capability",props[CAP],"is not suppoerted")
                return False
            #print("Camera setting",props[CAP],"to",Value)
            self.stream.set(CAP,Value)
            return True
        except Exception as e:
            print("Exception trying to set camera property",props[CAP],e)
            return False

    def getCAP(self,CAP):
        '''
        :param CAP: int openCV CAP_PROP value
        :return: the current setting (-1 signifies unsupported)
        '''
        return self.stream.get(CAP)

    def setThreshold(self,value):
        '''
        The gray level used to threshold the grayscale image
        :param value: int range 0-255
        :return: True if value ok, False otherwise
        '''
        threshold=int(value)
        #print("Camera Threshold ",threshold)
        if threshold>=0 and threshold<=255:
            self.threshold=threshold
            return True
        return False

    def setAfterCannyThreshold(self,value):
        '''
        The gray level used to threshold the grayscale image
        :param value: int range 0-255
        :return: True if value ok, False otherwise
        '''
        threshold=int(value)
        #print("Camera Threshold ",threshold)
        if threshold>=0 and threshold<=255:
            self.thresholdAfterCanny=threshold
            return True
        return False

    def setCannyMin(self,value):
        '''
        Set the min threshold for Canny edge detection
        :param value: int pixel grayscala  0-255, normally 100
        :return: Nothing
        '''
        self.cannyMin=value

    def setCannyMax(self,value):
        '''
        Set the max threshold for Canny edge detection
        :param value: nt pixel grayscala  0-255, normally 200
        :return: Nothing
        '''
        self.cannyMax=value

    def setResolution(self,size):
        '''
        Try to change the camera resolution
        :param size: tuple (w,h)
        :return: True if parameters changed ok, False otherwise
        '''
        (frame_w,frame_h)=size
        widthOk=self.setCAP(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
        heightOk=self.setCAP(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)
        if widthOk and HeightOk:
            self.frame_w,self.frame_h=frame_w,frame_h
            return True
        # restore previous settings
        self.setCAP(cv2.CAP_PROP_FRAME_WIDTH, self.frame_w)
        self.setCAP(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_h)
        return False


###########################################

    def processBGR(self):
        '''
        Background thread.
        Processes the most recent BGR image
        :return: None till stop() or release() are called
        '''

        while True:

            if self.stopped:
                self.stream.release()
                return

            self.convertBGR()

    def convertBGR(self):
        '''
        this is a lengthy process taking upto 400ms per frame
        Therefore the locks are acquired in stages to give the user
        and BGR collector chance to readBGR() and readEDGES() etc
        uses the latest BGR image (BGRcam) to create grayscale, thresholded and edged images
        Also called by __init__
        :return:
        '''
        (X1,X2,Y1,Y2)=self.maskROI

        with self.BGRlock:
            # lock required in case BGRcam is being written
            # by the BGR collector
            bgr=self.BGRcam

        # process the image
        gray = cv2.cvtColor(bgr[Y1:Y2,X1:X2], cv2.COLOR_BGR2GRAY)

        #print("Camera threshold=",self.threshold)

        th, thresh = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY)  # make it black & white
        edges = cv2.Canny(thresh, self.cannyMin, self.cannyMax)

        # enhance the edges to aid contour detection - experimental and doesn't appear
        # to improve anything
        if self.thresholdAfterCanny>0:
            th, edges = cv2.threshold(edges, self.thresholdAfterCanny, 255, cv2.THRESH_BINARY)

        # update the images used by the caller
        # this ensures that all the images correspond
        # to the BGR - otherwise there could
        # be a lag
        with self.UPDATElock:

            self.GRAY=gray
            self.BGR=bgr
            self.THRESH=thresh

            # EDGES is just a black image with edges drawn on it
            # todo - modify programs using this to accept the smaller edges
            # they can add offsets to the contours to get actual x/y back
            self.smallEDGES=edges
            self.EDGES=np.zeros((self.frame_h,self.frame_w,1),dtype=np.uint8)
            self.EDGES[Y1:Y2,X1:X2,0]=edges

    #@traceit
    def readBGR(self):
        '''
        gets the last BGR image from the camera
        :return: BGR image
        '''
        assert self.BGR is not None,"Attempt to call readBGR() no image available. Did you call start()"

        with self.UPDATElock:
            return self.BGR.copy()


    def readGRAY(self):
        '''
        Gets the gray scale image created from the BGR
        This is just the mask region

        :return: masked grayscale image
        '''
        assert self.GRAY is not None,"Attempt to call readGRAY() no image available. Did you call start()"
        with self.UPDATElock:
            return self.GRAY.copy()


    def readTHRESH(self):
        '''
        return the thresholded version of the last grayscale
        This is just the masked region
        :return: thresholded grayscale image
        '''
        assert self.THRESH is not None,"Attempt to call readTHRESH() no image available. Did you call start()"
        with self.UPDATElock:
            return self.THRESH.copy()


    #@timeit
    def readEDGES(self):
        '''
        return canny edges of the grayscale
        This image matches the dimensions of the camera image
        :return:
        '''
        assert self.EDGES is not None, "Attempt to call readEDGES() no image available. Did you call start()"
        with self.UPDATElock:
            return self.EDGES.copy()

    def readSmallEDGES(self):
        '''
        returns the edged mask region

        :return:  image
        '''
        assert self.smallEDGES is not None, "Attempt to call readSmallEDGES() no image available. Did you call start()"

        with self.UPDATElock:
            return self.smallEDGES.copy()

    #@traceit
    def makeMask(self,mask_w,mask_h):
        '''
        creates a mask region for the frame image
        used to exclude peripheral areas from the image processing
        :param mask_w: int mask width in pixels
        :param mask_h: int mask height in pixels
        :return:Nothing
        '''

        if mask_w>self.frame_w or mask_h>self.frame_h:
            # mask must not be larger than the video frame
            # so make it fit the whole image
            self.maskROI=(0,self.frame_w-1,0,self.frame_h-1)
            return

        # make sure the mask is centred
        y1 = (self.frame_h - mask_h) // 2
        y2=y1+mask_h
        x1 = (self.frame_w - mask_w) // 2
        x2=x1+mask_w
        self.maskROI=(x1,x2,y1,y2)


    def getMaskSize(self):
        '''
        return the current mask size (so we can draw the mask)
        :return: tuple w,h integers
        '''
        return self.mask_w,self.mask_h

    def getMaskOffsets(self):
        '''
        Returns the X1,Y1 components of the maskROI

        This allows the contour finding to work on the ROI only (faster)
        The ArenaProcessing simply adds these to the x/y cordinates
        of the contours

        :return: tuple (X1,Y1)
        '''
        X1,x,Y1,y=self.maskROI
        return (X1,Y1)

    def release(self):
        '''
        for compatability with openCV VideoCapture()
        :return:
        '''
        # indicate that the thread should be stopped
        self.stop()

    def stop(self):
        '''
        Tells the background threads to exit
        :return: None
        '''
        self.stopped = True

if __name__ == "__main__":

    cam=CameraStream((1920,1080))

    BGR=cam.readBGR()
    EDGES=cam.readEDGES()

    # prepare to draw mask rectangle
    imH,imW=BGR.shape[:2]
    maskw,maskh=cam.getMaskSize()

    # centre the mask rectangle
    x1=int((imW-maskw)/2)
    x2=x1+maskw
    y1=int((imH-maskh)/2)
    y2=y1+maskh


    # add mask rectangles
    # always centred

    cv2.rectangle(BGR,(x1,y1),(x2,y2),(0,255,255),2)    # colored image
    cv2.rectangle(EDGES,(x1,y1),(x2,y2),(255),2)        # edges is black & white

    cv2.imshow("BGR",BGR)
    cv2.imshow("EDGES",EDGES)

    print("Press any key to quit")
    cv2.waitKey(0)
    cam.release()
    cv2.destroyAllWindows()