"""
ArenaSetup.py

Small App to tweak feature sizes to help identify the robots
and their features (direction marker and id dots)

"""
from Params import *
from tkinter import *
import time
import cv2
from Camera import *
from Decorators import *
from ArenaProcessing import ArenaProcessor

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
    AP=None
    outframe=None

    # default preview image width
    previewOUTFRAME=640
    #previewBGR=640
    #previewGRAY=640
    #previewEDGES=640
    #previewTHRESH=640

    def __init__(self,settingsFname,imageSize, cameraIndex=0):

        print("Setup called from",__name__)

        self.AP=ArenaProcessor(imageSize)

        self.window = Tk()

        self.window.title("PixelBot Arena Bot Setup Utility")
        #self.window.geometry('360x430')


        nxtRow=0
        nxtRow = self.makeSpacer(nxtRow)
        nxtRow=self.makeFilenameEntry(nxtRow,settingsFname)
        nxtRow=self.makeSpacer(nxtRow)


        # unsupported camera options will not appear
        # as widgets
        nxtRow=self.makeDotMinSpinner(nxtRow)
        nxtRow=self.makeDotMaxSpinner(nxtRow)
        nxtRow=self.makeDirMinSpinner(nxtRow)
        nxtRow=self.makeDirMaxSpinner(nxtRow)
        nxtRow=self.makeBotMinSpinner(nxtRow)
        nxtRow=self.makeBotMaxSpinner(nxtRow)
        #nxtRow=self.makeScaleSpinner(nxtRow)
        nxtRow=self.makeOutframeSpinner(nxtRow)

        nxtRow = self.makeSpacer(nxtRow)

        buttonFrame=Frame(self.window)
        # add buttons - next to each other in the middle
        loadButton = Button(buttonFrame, text="Load", fg="red", command=self.btnReadParams)
        loadButton.grid(column=0, row=nxtRow, sticky=W,padx=5)

        saveButton = Button(buttonFrame, text="Save", fg="red", command=self.btnSaveParams)
        saveButton.grid(column=1,row=nxtRow, sticky=N,padx=5)

        quitButton = Button(buttonFrame,text="Quit",fg="red",command=self.quit)
        quitButton.grid(column=2, row=nxtRow, sticky=E,padx=5)

        buttonFrame.grid(column=0,row=nxtRow,columnspan=3)

        nxtRow=nxtRow+1
        nxtRow = self.makeSpacer(nxtRow)


        self.showAllCameraImages()
        self.closing=False
        self.updateWindowLoop()     # can't use mainloop() because it never returns

    def quit(self):
        self.closing=True
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
            self.outframe=self.AP.update()
            self.displayRobotInfo()
            self.showAllCameraImages()

            cv2.waitKey(1)      # keep openCV windows open


    def displayRobotInfo(self):
        robots=self.AP.getRobots()
        #print("robots",type(robots),"ROBOTS",robots)
        row=50
        for bot in robots:
            botId=bot() # bound method
            (posX,posY),heading=robots[bot] # heading is int already
            posX=int(posX)
            posY=int(posY)
            info="Bot: {0} pos {1:4d},{2:4d} hdg: {3:3d}".format(botId,posX,posY,heading)

            cv2.putText(self.outframe,info, (5, row), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            row=row+50


    def showAllCameraImages(self):
        if self.outframe is None: return
        self.showImage("OUTFRAME",self.outframe,self.previewOUTFRAME)
        #self.showImage("RAW BGR",self.cam.readBGR(),self.previewBGR)
        #self.showImage("GRAY",self.cam.readGRAY(),self.previewGRAY)
        #self.showImage("THRESH", self.cam.readTHRESH(), self.previewTHRESH)
        #self.showImage("EDGES",self.cam.readEDGES(),self.previewEDGES)

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

    def makePreviewSpinners_Unused(self, Row):
        '''
        Cannot use makeSpinner - that uses a range of value, these use a list

        :param Row: Label row
        :return: next row number (Row+4)
        '''
        Label(self.window, text="OUTFRAME Size").grid(row=Row, column=0, sticky=W,padx=5)
        Label(self.window, text="BGR Size").grid(row=Row, column=0, sticky=W,padx=5)
        Label(self.window, text="GRAY Size").grid(row=Row+1, column=0, sticky=W,padx=5)
        Label(self.window, text="THRESH Size").grid(row=Row+2, column=0, sticky=W,padx=5)
        Label(self.window, text="EDGES Size").grid(row=Row+3, column=0, sticky=W,padx=5)

        valueList=list(resolutions.keys())

        self.previewOUTFRAME=IntVar()
        self.previewBGRVar=IntVar()
        self.previewGRAYVar=IntVar()
        self.previewEDGESVar=IntVar()
        self.previewTHRESHVar=IntVar()

        OUTFRAMEspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewBGRVar, command=self.previewBGRSizeChanged)
        OUTFRAMEspin.grid(column=1, row=Row, sticky=W)

        BGRspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewBGRVar, command=self.previewBGRSizeChanged)
        BGRspin.grid(column=1, row=Row+1, sticky=W)

        GRAYspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewGRAYVar, command=self.previewGRAYSizeChanged)
        GRAYspin.grid(column=1, row=Row+2, sticky=W)

        THRESHspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewTHRESHVar, command=self.previewTHRESHSizeChanged)
        THRESHspin.grid(column=1, row=Row+3, sticky=W)

        EDGESspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewEDGESVar, command=self.previewEDGESSizeChanged)
        EDGESspin.grid(column=1, row=Row+4, sticky=W)

        self.previewOUTFRAMEVar.set(self.previewOUTFRAME)
        self.previewBGRVar.set(self.previewBGR)
        self.previewGRAYVar.set(self.previewGRAY)
        self.previewEDGESVar.set(self.previewEDGES)
        self.previewTHRESHVar.set(self.previewTHRESH)
        return Row + 5

    def makeOutframeSpinner(self, Row):
        '''
        Cannot use makeSpinner - that uses a range of value, these use a list

        :param Row: Label row
        :return: next row number
        '''
        Label(self.window, text="OUTFRAME Size").grid(row=Row, column=0, sticky=W,padx=5)

        valueList=list(resolutions.keys())
        #valueList=valueList.sort()
        self.previewOUTFRAMEVar=IntVar()

        OUTFRAMEspin = Spinbox(self.window, values=valueList, width=6, textvariable=self.previewOUTFRAMEVar, command=self.previewOUTFRAMESizeChanged)
        OUTFRAMEspin.grid(column=1, row=Row, sticky=W)

        self.previewOUTFRAMEVar.set(self.previewOUTFRAME)
        return Row + 1

    def makeFilenameEntry(self,Row,fname):
        Label(self.window, text="Setting file").grid(row=Row, column=0,sticky=W,padx=5)

        self.Filename=Entry(self.window)
        self.Filename.grid(row=Row,column=1,padx=(0,5))
        self.Filename.insert(0,fname)
        return Row+1


    def makeDotMinSpinner(self,Row):
        curValue=Params[PARAM_MIN_DOT_R]
        self.dotMinVar = IntVar()
        self.makeSpinner("ID Dot min size",Row,self.minDotChanged,0,255,1,self.dotMinVar,curValue)
        return Row+1

    def makeDotMaxSpinner(self, Row):
        curValue = Params[PARAM_MAX_DOT_R]
        self.dotMaxVar = IntVar()
        self.makeSpinner("ID Dot max size", Row, self.maxDotChanged, 0, 255, 1, self.dotMaxVar, curValue)
        return Row + 1

    def makeDirMinSpinner(self,Row):
        curValue=Params[PARAM_MIN_DIRECTOR_R]
        self.dirMinVar = IntVar()
        self.makeSpinner("Director min size",Row,self.minDirChanged,0,255,1,self.dirMinVar,curValue)
        return Row+1

    def makeDirMaxSpinner(self, Row):
        curValue = Params[PARAM_MAX_DIRECTOR_R]
        self.dirMaxVar = IntVar()
        self.makeSpinner("Director max size", Row, self.maxDirChanged, 0, 255, 1, self.dirMaxVar, curValue)
        return Row + 1

    def makeBotMinSpinner(self, Row):
        curValue = Params[PARAM_MIN_BOT_R]
        self.botMinVar = IntVar()
        self.makeSpinner("Bot min size", Row, self.minBotChanged, 0, 255, 1, self.botMinVar, curValue)
        return Row + 1


    def makeBotMaxSpinner(self, Row):
        curValue = Params[PARAM_MAX_BOT_R]
        self.botMaxVar = IntVar()
        self.makeSpinner("Bot max size", Row, self.maxBotChanged, 0, 255, 1, self.botMaxVar, curValue)
        return Row + 1



    def makeScaleSpinner(self, Row):
        curValue = Params[PARAM_CAMERA_SCALE]
        self.scaleVar = DoubleVar()
        self.makeSpinner("Camera Scale", Row, self.scaleChanged, 0.1, 3.0, 0.01,self.scaleVar, curValue)
        return Row+1


        #######################################################################
    def makeSpinner(self,LabelText,Row,Callback,From,To,Increment,Var,InitialValue):
        Label(self.window, text=LabelText).grid(row=Row, sticky=W,padx=5)

        Var.set(InitialValue)
        spin = Spinbox(self.window, from_=From, to=To, width=5, textvariable=Var, command=Callback, increment=Increment)
        col=1
        spin.grid(column=col, row=Row, sticky=W)

    #####################################################
    #
    # Spinner callbacks
    #
    #####################################################

    def previewOUTFRAMESizeChanged(self):
        self.previewOUTFRAME=self.previewOUTFRAMEVar.get()

    def previewBGRSizeChanged(self):
        self.previewBGR=self.previewBGRVar.get()

    def previewGRAYSizeChanged(self):
        self.previewGRAY=self.previewGRAYVar.get()

    def previewTHRESHSizeChanged(self):
        self.previewTHRESH=self.previewTHRESHVar.get()

    def previewEDGESSizeChanged(self):
        self.previewEDGES=self.previewEDGESVar.get()


    def minDotChanged(self):
        newMin=self.dotMinVar.get()
        # todo - feed through to Arena
        self.AP.setDotSize(newMin,self.dotMaxVar.get())
        Params[PARAM_MIN_DOT_R]=newMin

    def maxDotChanged(self):
        newMax=self.dotMaxVar.get()
        # todo - feed through to Arena
        self.AP.setDotSize(self.dotMinVar.get(),newMax)
        Params[PARAM_MAX_DOT_R]=newMax

    def minDirChanged(self):
        newMin = self.dirMinVar.get()
        # todo - feed through to Arena
        self.AP.setDotSize(newMin, self.dirMaxVar.get())
        Params[PARAM_MIN_DIRECTOR_R] = newMin

    def maxDirChanged(self):
        newMax = self.dirMaxVar.get()
        # todo - feed through to Arena
        self.AP.setDotSize(self.dirMinVar.get(), newMax)
        Params[PARAM_MAX_DIRECTOR_R] = newMax

    def minBotChanged(self):
        newMin = self.botMinVar.get()
        # todo - feed through to Arena
        self.AP.setBotSize(newMin, self.botMaxVar.get())
        Params[PARAM_MIN_BOT_R] = newMin

    def maxBotChanged(self):
        newMax = self.botMaxVar.get()
        # todo - feed through to Arena
        self.AP.setBotSize(self.botMinVar.get(), newMax)
        Params[PARAM_MAX_BOT_R] = newMax

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