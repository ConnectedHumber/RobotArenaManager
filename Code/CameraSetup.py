"""
CameraSetup.py

Small App to tweak camera settings and save them

Use it to explore the best settings for your lighting conditions


"""
from Params import *
from tkinter import *
import time
import cv2
from Camera import *
from Decorators import *

# read saved parameters from Settings.json (can be changed)

readParams()    # initial values. Can be re-read on button press

resolutions={
    # possible images sizes on screen
    1920:(1920,1080),
    1640:(1640,922),
    1440:(1440,810),
    1280:(1280,720),
    640:(640,480),
    480:(480,320)
}

print("DataFile=",DataFile)

class Setup:

    window=None
    cam=None

    # default preview image width
    previewBGR=640
    previewGRAY=640
    previewEDGES=640
    previewTHRESH=640

    def __init__(self,settingsFname,imageSize, cameraIndex=0):

        self.cam=CameraStream(imageSize,cameraIndex)
        self.cam.start()

        self.window = Tk()

        self.window.title("PixelBot Arena Camera Setup Utility")
        #self.window.geometry('360x430')


        nxtRow=0

        nxtRow = self.makeSpacer(nxtRow)
        nxtRow=self.makeFilenameEntry(nxtRow,settingsFname)
        nxtRow=self.makeSpacer(nxtRow)


        # unsupported camera options will not appear
        # as widgets
        nxtRow=self.makeThresholdSpinner(nxtRow)
        nxtRow=self.makeAfterCannyThresholdSpinner(nxtRow)

        nxtRow=self.makeBrightnessSpinner(nxtRow)
        nxtRow=self.makeSaturationSpinner(nxtRow)
        nxtRow=self.makeContrastSpinner(nxtRow)
        nxtRow=self.makeISOSpinner(nxtRow)
        nxtRow=self.makeAutoExposureSpinner(nxtRow)
        nxtRow=self.makeExposureSpinner(nxtRow)
        nxtRow=self.makeCannyMinSpinner(nxtRow)
        nxtRow=self.makeCannyMaxSpinner(nxtRow)
        nxtRow=self.makeScaleSpinner(nxtRow)

        Label(self.window, text="Preview Image Size").grid(row=nxtRow, column=0, sticky=N,padx=5, columnspan=3)

        nxtRow=self.makePreviewSpinners(nxtRow+1)

        nxtRow = self.makeSpacer(nxtRow)

        buttonFrame=Frame(self.window)
        # add buttons - next to each other in the middle
        loadButton = Button(buttonFrame, text="Load", fg="red", command=self.btnReadParams)
        loadButton.grid(column=0, row=nxtRow, sticky=W, padx=2)

        saveButton = Button(buttonFrame, text="Save", fg="red", command=self.btnSaveParams)
        saveButton.grid(column=1,row=nxtRow, sticky=N,padx=2)

        quitButton = Button(buttonFrame,text="Quit",fg="red",command=self.quit)
        quitButton.grid(column=2, row=nxtRow, sticky=E,padx=2)

        buttonFrame.grid(column=0,row=nxtRow,columnspan=3)

        nxtRow=nxtRow+1
        nxtRow = self.makeSpacer(nxtRow)


        self.showAllCameraImages()
        self.closing=False
        self.updateWindowLoop()     # can't use mainloop() because it never returns

    def quit(self):
        '''
        Called to tidy up on exit
        :return:
        '''
        self.closing=True
        self.cam.release()
        self.window.destroy()

    def updateWindowLoop(self):
        '''
        Neverending update loop to keep tkinter happy and the opencv image windows
        open
        :return: Nothing
        '''
        while True:
            if self.closing: break
            self.window.update()
            self.showAllCameraImages()
            cv2.waitKey(1)      # keep openCV windows open


    def showAllCameraImages(self):
        '''
        Opens a preview window for each image at the
        size requested

        :return: Nothing
        '''
        self.showImage("RAW BGR",self.cam.readBGR(),self.previewBGR)
        self.showImage("GRAY",self.cam.readGRAY(),self.previewGRAY)
        self.showImage("THRESH", self.cam.readTHRESH(), self.previewTHRESH)
        self.showImage("EDGES",self.cam.readEDGES(),self.previewEDGES)

    def showImage(self,windowTitle, image,res):
        '''
        Display the image at the requested width (res)

        :param windowTitle: window title text
        :param image: image to display
        :param res: image width for display
        :return: None
        '''
        assert image is not None, "showImage() requires an image. None was supplied."

        h,w = image.shape[:2]   # original image shape

        # do we bother scaling?
        if w == res:
            # no scaling
            cv2.imshow(windowTitle, image)
            return

        # maintain aspect ratio
        ratio=res/w
        newW=int(w*ratio)
        newH=int(h*ratio)
        # method can be INTER_NEAREST, INTER_LINEAR,INTER_AREA,INTER_CUBIC,INTER_LANCZO4
        # all of them screw up text readability when image is scaled
        cv2.imshow(windowTitle, cv2.resize(image, (newW,newH), interpolation=cv2.INTER_LINEAR))

    def makeSpacer(self,Row):
        '''
        Just a adds a space line
        :param Row: row to draw the empty line on
        :return: Row+1
        '''
        Label(self.window, text="").grid(row=Row, column=0,sticky=W)
        return Row+1

    def makePreviewSpinners(self, Row):
        '''
        Cannot use makeSpinner - that uses a range of value, these use a list

        :param Row: Label row
        :return: next row number (Row+4)
        '''
        Label(self.window, text="BGR Size").grid(row=Row, column=0, sticky=W,padx=5)
        Label(self.window, text="GRAY Size").grid(row=Row+1, column=0, sticky=W,padx=5)
        Label(self.window, text="THRESH Size").grid(row=Row+2, column=0, sticky=W,padx=5)
        Label(self.window, text="EDGES Size").grid(row=Row+3, column=0, sticky=W,padx=5)

        valueList=sorted(list(resolutions.keys()))

        self.previewBGRVar=IntVar()
        self.previewGRAYVar=IntVar()
        self.previewEDGESVar=IntVar()
        self.previewTHRESHVar=IntVar()

        BGRspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewBGRVar, command=self.previewBGRSizeChanged)
        BGRspin.grid(column=1, row=Row, sticky=W)

        GRAYspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewGRAYVar, command=self.previewGRAYSizeChanged)
        GRAYspin.grid(column=1, row=Row+1, sticky=W)

        THRESHspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewTHRESHVar, command=self.previewTHRESHSizeChanged)
        THRESHspin.grid(column=1, row=Row+2, sticky=W)

        EDGESspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewEDGESVar, command=self.previewEDGESSizeChanged)
        EDGESspin.grid(column=1, row=Row+3, sticky=W)

        self.previewBGRVar.set(self.previewBGR)
        self.previewGRAYVar.set(self.previewGRAY)
        self.previewEDGESVar.set(self.previewEDGES)
        self.previewTHRESHVar.set(self.previewTHRESH)
        return Row + 4

    def makeFilenameEntry(self,Row,fname):
        Label(self.window, text="Setting file").grid(row=Row, column=0,sticky=W,padx=5)

        self.Filename=Entry(self.window)
        self.Filename.grid(row=Row,column=1,padx=(0,5))
        self.Filename.insert(0,fname)
        return Row+1


    def makeThresholdSpinner(self,Row):
        curValue=Params[PARAM_THRESH_MIN]
        self.thresholdVar = IntVar()
        self.makeSpinner("Threshold ",Row,self.thresholdChanged,0,255,1,self.thresholdVar,curValue)
        return Row+1

    def makeAfterCannyThresholdSpinner(self,Row):
        curValue=Params[PARAM_AFTER_CANNY_THRESH_MIN]
        self.afterCannyThresholdVar = IntVar()
        self.makeSpinner("After Canny Threshold ",Row,self.afterCannyThresholdChanged,0,255,1,self.afterCannyThresholdVar,curValue)
        return Row+1

    def makeBrightnessSpinner(self,Row):
        '''
        Create a spinner for setting the camera brightness parameter
        The default setting appears to be 50 for the Pi Camera so the
        range is set 0->100 here

        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        if self.cam.getCAP(cv2.CAP_PROP_BRIGHTNESS) == -1: return

        curValue=Params[PARAM_CAMERA_BRIGHTNESS]
        self.brightnessVar=IntVar()
        self.makeSpinner("Brightness", Row, self.brightnessChanged, 0, 100, 1,self.brightnessVar, curValue)
        return Row+1

    def makeISOSpinner(self, Row):
        '''
        Create a spinner for setting the camera ISO SPEED parameter
        ISO takes only integer values in the range 0-3

        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        if self.cam.getCAP(cv2.CAP_PROP_ISO_SPEED)==-1: return

        curValue = Params[PARAM_CAMERA_ISO_SPEED]
        self.ISO_Var = IntVar()
        self.ISO_Var.set(curValue)
        self.makeSpinner("ISO Speed", Row, self.ISOChanged, 0,3,1, self.ISO_Var, curValue)
        return Row+1

    def makeAutoExposureSpinner(self, Row):
        '''
        Create a spinner for setting the camera auto exposure parameter
        Auto-exposure parameter ranges 0 to 1.0.

        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''

        curValue = self.cam.getCAP(cv2.CAP_PROP_AUTO_EXPOSURE)
        if curValue == -1: return

        self.autoExposureVar = DoubleVar()
        self.makeSpinner("Auto Exposure", Row, self.autoExposureChanged, 0, 1.0, 0.01, self.autoExposureVar, curValue)
        return Row+1

    def makeExposureSpinner(self, Row):
        '''
        Create a spinner for setting the camera exposure parameter.
        On the Pi Camera this appears to be set to 1000ms by default so
        range has been set here to be 0-5000
        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        if self.cam.getCAP(cv2.CAP_PROP_EXPOSURE) == -1: return

        curValue = Params[PARAM_CAMERA_EXPOSURE]
        self.exposureVar = IntVar()
        self.makeSpinner("Exposure", Row, self.exposureChanged, 0, 5000,1, self.exposureVar, curValue)
        return Row+1

    def makeCannyMinSpinner(self, Row):
        '''
        Create a spinner for setting the ccanny edge detector lower threshold parameter.
        The threshold corresponds to grayscale pixel values 0-255.
        Pixels below this value are not edge pixels.
        See https://docs.opencv.org/2.4/doc/tutorials/imgproc/imgtrans/canny_detector/canny_detector.html
        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        curValue = Params[PARAM_CANNY_MIN]
        self.cannyMinVar = IntVar()
        self.makeSpinner("Canny Min", Row, self.cannyMinChanged, 0, 255, 1,self.cannyMinVar, curValue)
        return Row+1

    def makeCannyMaxSpinner(self, Row):
        '''
        Create a spinner for setting the Canny edge detector upper threshold parameter.
        The threshold corresponds to grayscale pixel values 0-255.
        Pixels above this value are edge pixels.
        See https://docs.opencv.org/2.4/doc/tutorials/imgproc/imgtrans/canny_detector/canny_detector.html
        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        curValue = Params[PARAM_CANNY_MAX]
        self.cannyMaxVar = IntVar()
        self.makeSpinner("Canny Max", Row, self.cannyMaxChanged, 0, 255, 1,self.cannyMaxVar, curValue)
        return Row+1

    def makeSaturationSpinner(self, Row):
        '''
        Create a spinner for setting the camera saturation parameter.
        On the Pi Camera this appears to be set to 0 by default so
        range has been set here to be 0-255
        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        if self.cam.getCAP(cv2.CAP_PROP_SATURATION)==-1: return

        curValue = Params[PARAM_CAMERA_SATURATION]
        self.saturationVar = IntVar()
        self.makeSpinner("Camera Saturation", Row, self.saturationChanged, 0, 255,1, self.saturationVar, curValue)
        return Row+1

    def makeContrastSpinner(self, Row):
        '''
        Create a spinner for setting the camera contrast parameter.
        On the Pi Camera this appears to be set to 0 by default so
        range has been set here to be 0-255
        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        if self.cam.getCAP(cv2.CAP_PROP_CONTRAST) == -1: return

        curValue = Params[PARAM_CAMERA_CONTRAST]
        self.contrastVar = IntVar()
        self.makeSpinner("Camera Contrast", Row, self.contrastChanged, 0, 255, 1,self.contrastVar, curValue)
        return Row+1

    def makeScaleSpinner(self, Row):
        '''
        Create a spinner for setting the camera scaling parameter.
        Used to adjust the pixel to millimetre ratio see CameraScaling.py
        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        curValue = Params[PARAM_CAMERA_SCALE]
        self.scaleVar = DoubleVar()
        self.makeSpinner("Camera Scale", Row, self.scaleChanged, 0.1, 3.0, 0.01,self.scaleVar, curValue)
        return Row+1

    def makeAutoExposureSpinner(self, Row):
        '''
        Create a spinner for setting the camera auto-exposure parameter.
        On the Pi Camera this appears to be set to 0 by default so
        range has been set here to be 0-1.0 since, according to the internet
        a value of 0.25 turns off auto exposure and 0.75 turns it on.
        Not sure this works with the PiCamera

        :param Row: int row number for the spinner
        :return: Row+1 next row
        '''
        curValue = self.cam.getCAP(cv2.CAP_PROP_AUTO_EXPOSURE)
        if curValue==-1: return

        self.autoExposureVar = DoubleVar()
        self.makeSpinner("Auto-Exposure", Row, self.autoExposureChanged, 0, 1.0, 0.01, self.autoExposureVar, curValue)
        return Row+1

        #######################################################################
    def makeSpinner(self,LabelText,Row,Callback,From,To,Increment,Var,InitialValue):
        '''
        Method to create numerical spinners which has a defined range and step

        :param LabelText: string lable placed to the left of the spinner
        :param Row: int row to create the spinner on
        :param Callback: method to call when the spinner up/down control is clicked
        :param From: number lowest value
        :param To: number maximum value
        :param Increment: number the step size
        :param Var: the tkinter variable which will hold the value of the spinner
        :param InitialValue: value to start with
        :return: Nothing, the spinner is created
        '''
        Label(self.window, text=LabelText).grid(row=Row, sticky=W, padx=5)

        Var.set(InitialValue)
        spin = Spinbox(self.window, from_=From, to=To, width=5, textvariable=Var, command=Callback, increment=Increment)
        col=1
        spin.grid(column=col, row=Row, sticky=W)

    #####################################################
    #
    # Spinner callbacks
    #
    #####################################################

    def previewBGRSizeChanged(self):
        '''
        Use has changed the preview size for the BGR image
        sets the python variable used to store the value

        :return: Nothing
        '''
        self.previewBGR=self.previewBGRVar.get()

    def previewGRAYSizeChanged(self):
        '''
        Use has changed the preview size for the GRAY image
        sets the python variable used to store the value

        :return: Nothing
        '''
        self.previewGRAY=self.previewGRAYVar.get()

    def previewTHRESHSizeChanged(self):
        '''
        Use has changed the preview size for the THRESH image
        sets the python variable used to store the value

        :return: Nothing
        '''
        self.previewTHRESH=self.previewTHRESHVar.get()

    def previewEDGESSizeChanged(self):
        '''
        Use has changed the preview size for the EDGES image
        sets the python variable used to store the value

        :return: Nothing
        '''
        self.previewEDGES=self.previewEDGESVar.get()


    def thresholdChanged(self):
        '''
        Use has changed the Canny lower threshold used to create
        edges from the GRAY image

        sets the camera variable and the Param

        :return: Nothing
        '''
        newThresh=self.thresholdVar.get()
        #print("Threshold changed",newThresh)
        self.cam.setThreshold(newThresh)
        Params[PARAM_THRESH_MIN]=newThresh

    def afterCannyThresholdChanged(self):
        '''
        Use has changed the after Canny lower threshold used to
        further sharpen the EDGES image.

        sets the camera variable and the saved Param

        If this value is zero the afterCanny thresholding is turned off

        This is an experimental feature which may be removed since it doesn't
        appear to improve the edges.

        :return: Nothing
        '''
        newThresh=self.thresholdVar.get()
        #print("After Canny Threshold changed",newThresh)
        self.cam.setAfterCannyThreshold(newThresh)
        Params[PARAM_AFTER_CANNY_THRESH_MIN]=newThresh

    def autoExposureChanged(self):
        '''
        Use has changed the camera auto exposure setting

        sets the camera variable and the Param

        :return: Nothing
        '''
        newAuto=self.autoExposureVar.get()
        self.cam.setCAP(cv2.CAP_PROP_AUTO_EXPOSURE,newAuto)
        Params[PARAM_CAMERA_AUTO_EXPOSURE]=newAuto

    def brightnessChanged(self):
        '''
        Use has changed the camera brioghtness setting
        This needs to be called after the first image has been
        retrieved from the camera so that it can adjust
        its initial settings

        sets the camera variable and the Param

        :return: Nothing
        '''
        newBright=self.brightnessVar.get()
        self.cam.setCAP(cv2.CAP_PROP_BRIGHTNESS,newBright)
        #print("Brightness changed",newBright)
        Params[PARAM_CAMERA_BRIGHTNESS]=newBright

    def ISOChanged(self):
        '''
        Use has changed the camera ISO SPEED parameter

        sets the camera variable and the Param

        :return: Nothing
        '''
        newISO=self.ISO_Var.get()
        self.cam.setCAP(cv2.CAP_PROP_ISO_SPEED,newISO )
        #print("ISO changed",newISO)
        Params[PARAM_CAMERA_ISO_SPEED]=newISO

    def exposureChanged(self):
        '''
        Use has changed the camera exposure parameter

        sets the camera variable and the Param

        :return: Nothing
        '''
        newExp=self.exposureVar.get()
        self.cam.setCAP(cv2.CAP_PROP_EXPOSURE, newExp)
        #print("Exposure changed",newExp)
        Params[PARAM_CAMERA_EXPOSURE]=newExp

    def cannyMinChanged(self):
        '''
        User has changed the Canny min parameter

        sets the camera variable and the Param

        :return: Nothing
        '''
        newMin=self.cannyMinVar.get()
        self.cam.setCannyMin(newMin)
        #print("Canny Min changed",newMin)
        Params[PARAM_CANNY_MIN] = newMin

    def cannyMaxChanged(self):
        '''
        User has changed the Canny max parameter

        sets the camera variable and the Param

        :return: Nothing
        '''
        newMax=self.cannyMaxVar.get()
        self.cam.setCannyMax(newMax)
        Params[PARAM_CANNY_MAX]=newMax
        #print("Canny Max changed",newMax)

    def contrastChanged(self):
        '''
        User has changed the camera contrast parameter

        sets the camera variable and the Param

        :return: Nothing
        '''
        newContrast=self.contrastVar.get()
        self.cam.setCAP(cv2.CAP_PROP_CONTRAST, newContrast)
        #print("Contrast changed", newContrast)
        Params[PARAM_CAMERA_CONTRAST]=newContrast

    def saturationChanged(self):
        '''
        User has changed the camera saturation parameter

        sets the camera variable and the Param

        :return: Nothing
        '''
        newSat=self.saturationVar.get()
        self.cam.setCAP(cv2.CAP_PROP_CONTRAST, newSat)
        Params[PARAM_CAMERA_SATURATION]=newSat
        #print("Saturation changed", newSat)

    def scaleChanged(self):
        '''
        User has changed the camera scaling factor parameter

        currently unused in this app

        :return: Nothing
        '''
        newScale=self.scaleVar.get()
        #print("Scale changed", newScale)

        Params[PARAM_CAMERA_SCALE]=newScale


########################################
#
# button commands callbacks
#
    def btnSaveParams(self):
        '''
        Saves the current Param values to the specified settings file
        :return: Nothing
        '''
        fname = self.Filename.get()
        saveParams(fname)

    def btnReadParams(self):
        '''
        restores the last settings from the specified file
        :return: Params is repopulated
        '''
        readParams(fname)

if __name__ == "__main__":

    # start the program
    imageSize=(Params[PARAM_FRAME_WIDTH],Params[PARAM_FRAME_HEIGHT])
    S=Setup(DataFile,imageSize) # never returns till quit