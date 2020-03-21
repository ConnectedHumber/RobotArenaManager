# WARNING WORK IN PROGRESS
This repository is currently being populated. When I have finished this notice will be removed.

# RobotArenaManager
Python code to track Pixelbots (CrazyRobMiles design https://github.com/HullPixelbot) for educational gaming/coding sessions. In particular to support the concept of a Robot Rugby game.

![Pixelbot](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/PixelBot.jpg)

## In a nutshell
The code takes input from a PiCamera looking down on a game arena in which there are a number of identifiable robots.The scene is analysed using openCV contour detection to determine where the robots are and what direction they are heading. No, it's not that simple - read on.

The ArenaManager talks to an MQTT broker and publishes the co-ordinates and nautical heading of all the robots once per second.

The Arena can be viewed on the ArenaManager machine or on another local machine. A lower resolution image is locally streamed and can be picked up using a web browser.

A game controller, possibly on another machine, contains the game control logic. It subscribes to the broker listening for the information published and handles the messages accordingly. It publishes commands back to the robots via the MQTT broker.

The game controller also issues other commands to tell the robots where to go next.The robots subscribe to their own sub-topic to listen for commands aimed at themselves.

The robots can be remotely programmed and this is where the hands on educational bit come in. The 'owner' of the robot writes code which directs the robot to move from its current location to the target location. The code must include obstacle avoidance to circumnavigate other robots/obstacles on the way to the target location.

## Disclaimer

I don't purport to be the worlds best Python programmer. There may be better ways to code this stuff. You are welcome to take a copy and improve it. Please share back.

## Technical Stuff

The code uses Flask, openCV, numpy and Tkinter and was developed using Pycharm. 

*Flask* is used for the web streaming bit  
*openCV* for the video image capture, contour analysis and previews  
*tkinter* is used for a couple of 'Setup' utilities but not the main code   
*paho mqtt* is used to subscribe and publish robot position data to an MQTT broker  
*numpy* is used for some image processing  

Deveopment was done on a Raspberry Pi4 with 4GB RAM running Buster. Mosquitto was installed on the Pi for debugging the published messages.

CrazyRobMiles loaned me a couple of PixelBots to work with.

## Robot labelling

I tried a number of 'caps' on the robots. In the end a plain white rectangle with black dots to identify the bot number and a rectangle to help determine the heading worked best. The caps measured 73x83mm - the short edge being at front and rear as seen here:-

![caps](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/DSC00912.JPG)

Circular black dots (11mm dia) identify the robot number and a 15mm black square/circle, in conjunction with the robot centre, is used to determine the heading. Those worked best for me. As long as the dots and black square are sufficiently different in size the dots will be identified as ID dots and the square as a heading aid. The size ranges can all be tweaked using the ArenaSetup.py utility.

Note. To ensure consistent identification of a robot the arena needs even steady illumination (clouds passing in front of the sun are a problem.) and mask any highly reflective parts. I used a matt black sticky tape.

## Arena Illumination

My development room is a spare bedroom. The overhead light is a 6000K 75W bulb. With the (south facing) blinds open the lighting varied a lot as the clouds crossed the sun. Also, the illumination in the C4DI building was,also, significantly different.

Consequently, you need to consider illuminating the arena in a way which minimises the effect of other lighting not under your control. I checked Ebay and Amazon for photography LED lights but they were a bit expensive - especially as I was unsure if I needed one, two or four to subdue shadows.

So, Aliexpress to the rescue. I bought 4x 8W square White (6000-7000K) LED ceiling panels (220vAC). These had the advantage of not requiring a separate power supply - only amains extension lead.

https://www.aliexpress.com/item/4000015794425.html?spm=a2g0s.9042311.0.0.7ac94c4dF5w5aW

So far so good, I have only used two. You need to make a holder which can be hung over the arena with a square hole. This is a bit crude (prototype) but it works for me.  
![LED Panels](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/LED%20Panel%20Mounting.JPG)

Here you can see two panels with the Pi Camera in between.

![Led Panels 2](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/Arena%20Lighting.JPG)

## Configuration in a nutshell

It is a good idea to do the initial configuration at 1920x1080 camera resolution. 

Firstly you need to edit MqttManager.py and put your broker information in at the top. For testing I just used the mosquitto broker which I installed on the same Pi. I didn't bother with username or passwords - the MqttManager will connect with usernames and passwords if you specify them for your broker.

Next you need to run CameraScaling.py to determine the pixel to millimetre ratio. This will be stored in Settings.json and is used to convert image pixel co-ordinates to real world millimetres. The robots don't know about pixels. To use the CameraScaling.py utility place an A4 sheet of paper in the centre of the arena then adjust the on screen rectangle till it fits around the paper. Press s to save the scaling factor. Now, you need to find a way to guarantee your camera is always the same height above the arena otherwise you will need to do this again. And again... 

Please be aware that the next steps are easily influenced by ambient light conditions.

Next run the CameraSetup.py utility. This will allow you to tune parameters used by openCV for producing clean edges which can be used by openCv's findContour(). You will see 4 images - the raw camera image, the gray scale, the threshold image and the edges image. Adjust the parameters till you get a clean looking threshold image. Inspect the Edges image to make sure you are seeing closed contours around the robots and the features on the cap. You can zoom in to check them.

Finally, run the ArenaSetup.py utility and adjust the min/max values for the dots etc. The utility lists the bots identified and their headings. If you have X robots and X are found then that is a good start. If the dots aren't counted correctly adjust the min/max dot size. I found that min=1 seems to work well. If the heading isn't determined play with the min/max director settings. The settings should not overlap - for obvious reasons, I hope.

Now you can run the ArenaManager.py - let the game commence

Further details can be found in the individual documents.















