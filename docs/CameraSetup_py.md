# CameraSetup.py

This is a Tkinter app which provides a number of spinners to change camera parameters whilst observing the effects on the BGR, GRAY, THRESH and EDGES images.

![CameraSetup](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/CameraSetup.jpg)


Looking at the THRESH image you can see the robots and their feature dots are all clearly visible - that means the openCV findContours() method has a fighting chance of extracting the information needed.

Zoom in the EDGES preview to check that all edges are clean like in this screenshot.

![Edges](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/Edges.jpg)

The utility is a bit simple - if you type a value into a spinbox you need to click up/down to send it to the camera - room for improvement there but I haven't researched tkinter to find out how to improve that.

When you are happy that your EDGES image has nice clean edges click the save button to update the Settings.json data file. 

