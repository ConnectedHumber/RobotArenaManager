# CameraSetup.py

This is a Tkinter app which provides a number of spinners to change camera parameters whilst observing the effects on the BGR, GRAY, THRESH and EDGES images.

![CameraSetup](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/CameraSetup.jpg)

Sorry if the image has suffered in resizing. Top left is the raw camera image/frame (RAW BGR). Bottom left is the resulting edges (EDGES). Top right is the grayscale image (GRAY) and bottom right is the thresholded grayscale (THRESH).

Looking at the THRESH image you can see the robots and their feature dots are all clearly visible - that means the openCV findContours() method has a fighting chance of extracting the information needed.

Although not clear in this screenshot the EDGES image, which can be zoomed in, shows that all features have been detected separately.

The utility is a bit simple - if you type a value into a spinbox you need to click up/down to send it to the camera - room for improvement there but I haven't researched tkinter to find out how to improve that.

When you are happy that your EDGES image has nice clean edges click the save button to update the Settings.json data file. 

