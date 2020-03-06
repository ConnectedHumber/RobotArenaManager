
"""
Purpose is to provide the most current video frame and to analyse it
to obtain the edges

Two threads are used. One collects the most recent BGR frame in an attempt to
ensure the caller has the latest BGR image and so reduce lag.

The second thread runs to process the BGR image creating a grayscale,
thesholded and edged version of the masked region of the BGR

Threading locks are used to ensure image updating/reading takes place on
a stable image at all times

usage:
    from FastCameraStream import CameraStream

    vs=CameraStream(path,queuesize
    vs.setCAP(cv2.CAP...,value)     # set camera capabilities
    vs.setMask(w,h)                 # excludes regions outside the image
    vs.start()                      # starts the processBGR() method as a background task

    #grab the scene - we will draw contours on it later
    scene=vs.readBGR()

    # getting contours
    edges=vs.readEDGES()    # this could be several frames behind the BGR due to conversion time
    contours, hierarchy = cv2.findContours(edges,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # hierarchy is optional but useful for picking out parts of the contours
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

readParams()

class CameraStream:

    def __init__(self, size, index=0):
        '''
        initialise variables and start the BGR image collector

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

        print("Camera: first image obtained in", time.time() - begin, "seconds")

        self.makeMask(int(self.frame_w/2),int(self.frame_h/2))  # temporary, will be called by the user to set proper mask

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
            print("Waiting for CameraStream thread to stop active=",threading.active_count())
            #while threading.active_count()>0:
            #    pass
            self.stream.release()
            time.sleep(1)
            print("After sleep active=",threading.active_count())

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
        self.cannyMin=value

    def setCannyMax(self,value):
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

        with self.BGRlock:
            # lock required in case BGRcam is being written
            # by the BGR collector
            bgr=self.BGRcam

        # process the image
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        #print("Camera threshold=",self.threshold)

        if self.frame_h!=self.mask_h:
            masked_gray = cv2.bitwise_and(gray, self.gray_mask)
            th, thresh = cv2.threshold(masked_gray, self.threshold, 255,cv2.THRESH_BINARY)  # make it black & white
            edges=cv2.Canny(thresh, self.cannyMin,self.cannyMax)
        else:
            th, thresh = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY)  # make it black & white
            edges = cv2.Canny(thresh, self.cannyMin, self.cannyMax)

        # enhance the edges to aid contour detection
        if self.thresholdAfterCanny>0:
            th, edges = cv2.threshold(edges, self.thresholdAfterCanny, 255, cv2.THRESH_BINARY)  # make it black & white

        # update the images used by the caller
        # this ensures that all the images correspond
        # to the BGR - otherwise there could
        # be a lag
        with self.UPDATElock:
            if self.frame_h != self.mask_h:
                self.GRAY = masked_gray
            else:
                self.GRAY=gray

            self.BGR=bgr
            self.THRESH=thresh
            self.EDGES=edges

    #@traceit
    def readBGR(self):
        '''
        gets the last BGR image from the camera
        :return: BGR image
        '''
        assert self.BGR is not None,"Attempt to call readBGR() no image available. Did you call start()"

        with self.UPDATElock:
            return self.BGR.copy()
        return None


    def readGRAY(self):
        '''
        Gets the gray scale image created from the BGR
        :return: masked grayscale image
        '''
        assert self.GRAY is not None,"Attempt to call readGRAY() no image available. Did you call start()"
        with self.UPDATElock:
            return self.GRAY.copy()
        return None

    def readTHRESH(self):
        '''
        return the thresholded version of the last grayscale
        :return: thresholded grayscale image
        '''
        assert self.THRESH is not None,"Attempt to call readTHRESH() no image available. Did you call start()"
        with self.UPDATElock:
            return self.THRESH.copy()
        return None

    #@timeit
    def readEDGES(self):
        '''
        return canny edges of the grascale
        :return:
        '''
        assert self.EDGES is not None, "Attempt to call readEDGES() no image available. Did you call start()"
        with self.UPDATElock:
            return self.EDGES.copy()
        return None

    #@traceit
    def makeMask(self,mask_w,mask_h):
        '''
        creates a mask for the frame image
        used to exclude peripheral areas from the image

        :param size: (w,h)
        :return:
        '''
        self.mask_w,self.mask_h=mask_w,mask_h

        assert self.BGRcam is not None,"Check camera is ready before calling makeMask()"

        # todo only mask if mask size is less than the image
        # in proper use there will not be a mask as the whole field of
        # view will be the whole image

        # do we need a mask?
        if int(self.frame_h)==int(self.mask_h): return

        with self.BGRlock:
            self.bgr_mask = self.BGRcam.copy()  # mask must be a separate image

        # make the image black
        self.bgr_mask[0:self.frame_h, 0:self.frame_w] = (0, 0, 0)

        # make sure the mask is centred
        y = int((self.frame_h - mask_h) / 2)
        x = int((self.frame_w - mask_w) / 2)

        # fill the ROI with white to create a hole in the mask
        self.bgr_mask[y:y + mask_h, x:x + mask_w] = (255, 255, 255)
        self.gray_mask=cv2.cvtColor(self.bgr_mask, cv2.COLOR_BGR2GRAY)


    def release(self):
        '''
        for compatability with openCV VideoCapture()
        :return:
        '''
        # indicate that the thread should be stopped
        self.stop()

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
