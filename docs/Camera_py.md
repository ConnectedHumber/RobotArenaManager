# Camera.py

This Library is used to capture and process images from a camera using the openCV VideoCapture() API. processing is done using openCV methods cvtColor(), threshold() and Canny()

It provides the caller with access to a color image (BGR), GrayScale (GRAY), a thresholded grayscale (THRESH) and a Canny edge image (EDGES)

It uses two threads. 
1. Thread 1 collects images from the camera in a continuous loop. The captured image is stored temporarily. 
2. Thread 2 picks up the stored image, copies it to BGR then creates the grayscale from the BGR etc till all four images (BGR ,GRAY,THRESH and EDGES) have been processed. When the user reads the BGR,GRAY,THRESH and EDGES images they all belong to the same frame. 

Image processing takes around 300ms to convert a 1920x1080 image on my Pi4 to a Canny edges image. This would introduce a pipeline delay which means the displayed image would be very out of sync with reality. By capturing the camera images in a separate thread the processing is always done on the latest image and displays using the processed images were running at an acceptable rate. I was able to achieve upto 10fps with this. In pratice we only want to send out robot position information about once per second so this frame rate was acceptable and the robot motion was fairly good.

## Dependencies
1. openCv
2. threading
3. Decorators.py  
This is just a couple of decorators I use for debugging
4. props.py  
This is just a list of openCV camera properties - used for debugging. It is used to convert an openCV constant to human readable form.
5. Params.py  
This is a library to read/save the contents of the *Settings.json* file which contains a load of variables such as threhold values used by the camera image processing

## Class

### CameraStream(size,index)
Size: tuple (w,h) is the image capture size required.
Index: int default 0 is the openCV camera index which defaults to zero (First camera on the system) but it can be changed
### readBGR()  
Returns the color image from the last frame processed
### readGRAY()  
Returns the grayscale created from the BGR
### readTHRESH()  
Returns the thresholded image created from the GRAY image
### readEDGES()  
Returns the edged version of the thresholded image.  
### start()  
Starts the image capture and conversion  
### release()  
Stops the threads. Although the __del__() method also does that in case you forget.  
### ready()  
Returns True if the image processing has completed (All the images will be available)  
### setCAP(CAP,Value)  
CAP: int openCv capability property constant e.g. CAP_PROP_FRAME_HEIGHT  
Value: number - the required capability setting value.  
This method is used to change camera settings whilst running (See CameraSetup.py) so that you can work out the best settings for detecting robots in the arena.  
### setThreshold(Value)  
Value: int 0->255. Sets the lower threshold for the thresholding method. It turns the gray scale image into a black and white image. The threshold value should be adjusted till you get a clear B&W image of the arena with all robot features clearly visible and separate.  
### setAfterCannyThreshold(Value)
Experimental - thresholds the edges image. Not sure it actually does much but setting it to zero turns it off.
### setCannyMin(value)  setCannyMax(Value)
Value: int 0-255. Canny uses two thresholds for edge detection. OpenCV documentation suggests these should be in the ratio of 1:2 or 1:3. A min value of 100 and max of 200 is a normal setting and works well. You need to read the openCV documentation but it might be worth lowering the max value to see if the edges are more consistently found.  
### setResolution(size)  
size: tuple (w,h) Change the size of the captured image.
## Usage  
In general use the user would only require the BGR and EDGES images  
'''
from Camera import *
from Params import *
import cv2

size=(Params(PARAM_CAMERA_FRAME_WIDTH],Params(PARAM_CAMERA_FRAME_WIDTH])

CS=CameraStream(size)  # open the first camera by default
CS.start()

while True:
  BGR=CS.readBGR()
  EDGES=CS.readEDGES()

  contours=cv2.findContours(EDGES)
  
  cv2.drawContours(BGR,contours,-1,(255,255,255),1)
  cv2.imshow("contoured BGR",BGR)
  
CS.release()
'''






