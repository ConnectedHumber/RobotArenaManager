"""
CameraSetup.py

Small App to tweak camera settings and save them


"""
from Params import *
from tkinter import *
import time
import cv2
from Camera import *
from Decorators import *

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

        print("Setup called from",__name__)

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
        nxtRow=self.makePreviewSpinners(nxtRow)

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
        self.closing=True
        self.cam.release()
        self.window.destroy()

    def updateWindowLoop(self):
        '''
        Neverending update loop to keep tkinter happy and the opencv image windows
        open
        :return:
        '''
        while True:
            if self.closing: break
            self.window.update()
            self.showAllCameraImages()
            cv2.waitKey(1)      # keep openCV windows open


    def showAllCameraImages(self):
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

        h,w = image.shape[:2]

        #print("Image shape=",w,h)

        if w == res:
            # no scaling
            cv2.imshow(windowTitle, image)
            return

        # display the scaled image
        dim = resolutions[res]
        #print("Resizing displayed image to ",dim)
        # method can be INTER_NEAREST, INTER_LINEAR,INTER_AREA,INTER_CUBIC,INTER_LANCZO4
        # all of them screw up text readability when image is scaled
        cv2.imshow(windowTitle, cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR))

    def makeSpacer(self,Row):
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

        valueList=list(resolutions.keys())

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

        if self.cam.getCAP(cv2.CAP_PROP_BRIGHTNESS) == -1: return

        curValue=Params[PARAM_CAMERA_BRIGHTNESS]
        self.brightnessVar=IntVar()
        self.makeSpinner("Brightness", Row, self.brightnessChanged, 0, 100, 1,self.brightnessVar, curValue)
        return Row+1

    def makeISOSpinner(self, Row):

        if self.cam.getCAP(cv2.CAP_PROP_ISO_SPEED)==-1: return

        curValue = Params[PARAM_CAMERA_ISO_SPEED]
        self.ISO_Var = IntVar()
        self.ISO_Var.set(curValue)
        self.makeSpinner("ISO Speed", Row, self.ISOChanged, 0,3,1, self.ISO_Var, curValue)
        return Row+1

    def makeAutoExposureSpinner(self, Row):

        curValue = self.cam.getCAP(cv2.CAP_PROP_AUTO_EXPOSURE)
        if curValue == -1: return

        self.autoExposureVar = DoubleVar()
        self.makeSpinner("Auto Exposure", Row, self.autoExposureChanged, 0.1, 1.0, 0.01, self.autoExposureVar, curValue)
        return Row+1

    def makeExposureSpinner(self, Row):

        if self.cam.getCAP(cv2.CAP_PROP_EXPOSURE) == -1: return

        curValue = Params[PARAM_CAMERA_EXPOSURE]
        self.exposureVar = IntVar()
        self.makeSpinner("Exposure", Row, self.exposureChanged, 0, 5000,1, self.exposureVar, curValue)
        return Row+1

    def makeCannyMinSpinner(self, Row):
        curValue = Params[PARAM_CANNY_MIN]
        self.cannyMinVar = IntVar()
        self.makeSpinner("Canny Min", Row, self.cannyMinChanged, 0, 255, 1,self.cannyMinVar, curValue)
        return Row+1

    def makeCannyMaxSpinner(self, Row):
        curValue = Params[PARAM_CANNY_MAX]
        self.cannyMaxVar = IntVar()
        self.makeSpinner("Canny Max", Row, self.cannyMaxChanged, 0, 255, 1,self.cannyMaxVar, curValue)
        return Row+1

    def makeSaturationSpinner(self, Row):

        if self.cam.getCAP(cv2.CAP_PROP_SATURATION)==-1: return

        curValue = Params[PARAM_CAMERA_SATURATION]
        self.saturationVar = IntVar()
        self.makeSpinner("Camera Saturation", Row, self.saturationChanged, 0, 255,1, self.saturationVar, curValue)
        return Row+1

    def makeContrastSpinner(self, Row):

        if self.cam.getCAP(cv2.CAP_PROP_CONTRAST) == -1: return

        curValue = Params[PARAM_CAMERA_CONTRAST]
        self.contrastVar = IntVar()
        self.makeSpinner("Camera Contrast", Row, self.contrastChanged, 0, 255, 1,self.contrastVar, curValue)
        return Row+1

    def makeScaleSpinner(self, Row):
        curValue = Params[PARAM_CAMERA_SCALE]
        self.scaleVar = DoubleVar()
        self.makeSpinner("Camera Scale", Row, self.scaleChanged, 0.1, 3.0, 0.01,self.scaleVar, curValue)
        return Row+1

    def makeAutoExposureSpinner(self, Row):

        curValue = self.cam.getCAP(cv2.CAP_PROP_AUTO_EXPOSURE)
        if curValue==-1: return

        self.autoExposureVar = DoubleVar()
        self.makeSpinner("Auto-Exposure", Row, self.autoExposureChanged, 0.1, 1.0, 0.01, self.autoExposureVar, curValue)
        return Row+1

        #######################################################################
    def makeSpinner(self,LabelText,Row,Callback,From,To,Increment,Var,InitialValue):
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
        self.previewBGR=self.previewBGRVar.get()

    def previewGRAYSizeChanged(self):
        self.previewGRAY=self.previewGRAYVar.get()

    def previewTHRESHSizeChanged(self):
        self.previewTHRESH=self.previewTHRESHVar.get()

    def previewEDGESSizeChanged(self):
        self.previewEDGES=self.previewEDGESVar.get()


    def thresholdChanged(self):
        newThresh=self.thresholdVar.get()
        #print("Threshold changed",newThresh)
        self.cam.setThreshold(newThresh)
        Params[PARAM_THRESH_MIN]=newThresh

    def afterCannyThresholdChanged(self):
        newThresh=self.thresholdVar.get()
        #print("After Canny Threshold changed",newThresh)
        self.cam.setAfterCannyThreshold(newThresh)
        Params[PARAM_AFTER_CANNY_THRESH_MIN]=newThresh

    def autoExposureChanged(self):
        newAuto=self.autoExposureVar.get()
        self.cam.setCAP(cv2.CAP_PROP_AUTO_EXPOSURE,newAuto)
        Params[PARAM_CAMERA_AUTO_EXPOSURE]=newAuto

    def brightnessChanged(self):
        newBright=self.brightnessVar.get()
        self.cam.setCAP(cv2.CAP_PROP_BRIGHTNESS,newBright)
        #print("Brightness changed",newBright)
        Params[PARAM_CAMERA_BRIGHTNESS]=newBright

    def ISOChanged(self):
        newISO=self.ISO_Var.get()
        self.cam.setCAP(cv2.CAP_PROP_ISO_SPEED,newISO )
        #print("ISO changed",newISO)
        Params[PARAM_CAMERA_ISO_SPEED]=newISO

    def exposureChanged(self):
        newExp=self.exposureVar.get()
        self.cam.setCAP(cv2.CAP_PROP_EXPOSURE, newExp)
        #print("Exposure changed",newExp)
        Params[PARAM_CAMERA_EXPOSURE]=newExp

    def cannyMinChanged(self):
        newMin=self.cannyMinVar.get()
        self.cam.setCannyMin(newMin)
        #print("Canny Min changed",newMin)
        Params[PARAM_CANNY_MIN] = newMin

    def cannyMaxChanged(self):
        newMax=self.cannyMaxVar.get()
        self.cam.setCannyMax(newMax)
        Params[PARAM_CANNY_MAX]=newMax
        #print("Canny Max changed",newMax)

    def contrastChanged(self):
        newContrast=self.contrastVar.get()
        self.cam.setCAP(cv2.CAP_PROP_CONTRAST, newContrast)
        #print("Contrast changed", newContrast)
        Params[PARAM_CAMERA_CONTRAST]=newContrast

    def saturationChanged(self):
        newSat=self.saturationVar.get()
        self.cam.setCAP(cv2.CAP_PROP_CONTRAST, newSat)
        Params[PARAM_CAMERA_SATURATION]=newSat
        #print("Saturation changed", newSat)

    def scaleChanged(self):
        newScale=self.scaleVar.get()
        print("Scale changed", newScale)

        Params[PARAM_CAMERA_SCALE]=newScale
        pass

########################################
#
# button commands callbacks
#
    def btnSaveParams(self):
        fname = self.Filename.get()
        saveParams(fname)

    def btnReadParams(self):
        readParams(fname)

if __name__ == "__main__":

    imageSize=(Params[PARAM_FRAME_WIDTH],Params[PARAM_FRAME_HEIGHT])
    S=Setup(DataFile,imageSize) # never returns till quit