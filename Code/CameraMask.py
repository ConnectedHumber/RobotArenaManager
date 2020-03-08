"""
CameraMaskSetup.py

Small App to tweak  the Arena mask used to exclude unwanted regions from
image processing by Camera.py


"""
from Params import *
from tkinter import *
import time
import cv2
from Camera import *
from Decorators import *

readParams()    # initial values. Can be re-read on button press

class Setup:

    window=None
    cam=None
    BGR=None

    # default preview image width
    BGRwidth=640

    def __init__(self,settingsFname,imageSize, cameraIndex=0):

        print("Setup called from",__name__)

        self.cam=CameraStream(imageSize)
        self.cam.start()
        time.sleep(1.2) # takes just over a second to get a frame from the camera

        self.window = Tk()

        self.window.title("Camera Mask Setup Utility")

        nxtRow=0
        nxtRow = self.makeSpacer(nxtRow)
        nxtRow=self.makeFilenameEntry(nxtRow,settingsFname)
        nxtRow=self.makeSpacer(nxtRow)


        # unsupported camera options will not appear
        # as widgets
        nxtRow=self.makeWidthSpinner(nxtRow)
        nxtRow=self.makeHeightSpinner(nxtRow)

        nxtRow=self.makeBGRSpinner(nxtRow)

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


        self.showImage("BGR", self.BGR, self.BGRwidth)
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
            self.BGR=self.cam.readBGR()

            # draw the current maskl region
            maskW,maskH=Params[PARAM_ARENA_MASK_SIZE]

            imH,imW=self.BGR.shape[:2]

            # center the mask
            x1=int((imW-maskW)/2)
            x2 = x1+maskW
            y1 = int((imH - maskH) / 2)
            y2 = y1+maskH

            cv2.rectangle(self.BGR,(x1,y1),(x2,y2),(255,255,0),2)

            self.showImage("BGR", self.BGR, self.BGRwidth)

            cv2.waitKey(1)      # keep openCV windows open



    def showImage(self,windowTitle, image,res):
        '''
        Display the image at the requested width (res)

        :param windowTitle: window title text
        :param image: image to display
        :param res: image width for display
        :return: None
        '''
        if image is None:
            print("Waiting for an image")
            return
        #assert image is not None, "showImage() requires an image. None was supplied."

        h,w = image.shape[:2]

        #print("Image shape=",w,h)

        if w == res:
            # no scaling
            cv2.imshow(windowTitle, image)
            return

        # display the scaled image
        #dim = resolutions[res]
        # maintain aspect ratio
        ratio=res/w
        newW=int(w*ratio)
        newH=int(h*ratio)

        #print("Resizing displayed image to ",dim)
        # method can be INTER_NEAREST, INTER_LINEAR,INTER_AREA,INTER_CUBIC,INTER_LANCZO4
        # all of them screw up text readability when image is scaled
        cv2.imshow(windowTitle, cv2.resize(image, (newW,newH), interpolation=cv2.INTER_LINEAR))

    def makeSpacer(self,Row):
        Label(self.window, text="").grid(row=Row, column=0,sticky=W)
        return Row+1

    def makeBGRSpinner(self, Row):
        '''
        Cannot use makeSpinner - that uses a range of value, these use a list

        :param Row: Label row
        :return: next row number (Row+4)
        '''
        Label(self.window, text="BGR width").grid(row=Row, column=0, sticky=W,padx=5)

        self.BGRVar=IntVar()

        spin = Spinbox(self.window, values=(480,640,1280,1920),width=6, textvariable=self.BGRVar, command=self.BGRSizeChanged)
        spin.grid(column=1, row=Row, sticky=W)

        self.BGRVar.set(self.BGRwidth)
        return Row + 1



    def makeFilenameEntry(self,Row,fname):
        Label(self.window, text="Setting file").grid(row=Row, column=0,sticky=W,padx=5)

        self.Filename=Entry(self.window)
        self.Filename.grid(row=Row,column=1,padx=(0,5))
        self.Filename.insert(0,fname)
        return Row+1


    def makeWidthSpinner(self,Row):
        w,h=Params[PARAM_ARENA_MASK_SIZE]
        curValue=w
        self.widthVar = IntVar()
        self.makeSpinner("Mask width",Row,self.widthChanged,0,1920,1,self.widthVar,curValue)
        return Row+1

    def makeHeightSpinner(self,Row):
        w,h=Params[PARAM_ARENA_MASK_SIZE]
        curValue=h
        self.heightVar = IntVar()
        self.makeSpinner("Mask height",Row,self.heightChanged,0,1080,1,self.heightVar,curValue)
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

    def widthChanged(self):
        w,h=Params[PARAM_ARENA_MASK_SIZE]

        newW=self.widthVar.get()

        Params[PARAM_ARENA_MASK_SIZE]=(newW,h)

    def heightChanged(self):
        w, h = Params[PARAM_ARENA_MASK_SIZE]

        newH = self.heightVar.get()

        Params[PARAM_ARENA_MASK_SIZE] = (w, newH)

    def BGRSizeChanged(self):
        self.BGRwidth=self.BGRVar.get()


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