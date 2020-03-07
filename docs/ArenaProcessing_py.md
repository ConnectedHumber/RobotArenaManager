# ArenaProcessing.py

This code takes the BGR and EDGES images from the Camera.py and tries to locate and identify the robots.

This is done,initially, by using openCVs' minEnclosingCircle() method which returns the coordinates of the features found and their approximate size (radius). The robot, id dots and direction indicator all need to be significantly different in size. The sizes can be adjusted using the ArenaSetup.py program.

Large object contours (robots?) are checked using minAreaRect() to get the four corners of the robot. This polygon is used to check if dots and direction indicators are actually inside the robot using openCVs' pointPolgonTest(). I tried using contour heirarchy using the openCV CV_RETR_TREE mode with findContours() but, although it found all the features this often produced orphaned contours so didn't gain anything for me. Possibly, this was caused by changes in lighting even though I kept the room blinds drawen and the 6000k LED light on. I have ordered LED lights from Aliexpress to try as arena illumination.

This program uses the centre of the robot combined with the centre of the direction indicator to work out the nautical heading of the robot. Pixel 0,0 is top left of the camera image.

The image from the camera is overlaid with the robot positions and their Id numbers and is returned to the ArenaManager.py for streaming as well as being displayed on the local screen.

ArenaManager.py also requests the discovered list of robots, their positions and headings to be published by the MQTTManager.py program once per second. The coordinates are pushed to each robot so it knows where it is.

ArenaProcessing.py can also record the labeled camera frames to output.avi - a live action recording. This, clearly, reduces the frame rate if used but the worst I saw with an arena populated by 8 robots was 3 fps (faster than the robot position update rate). At times, without video recording I saw upto 10fps. This was all with 1920x1080 video frames. Reducing the frame size to 1280x720 significantly improved the frame rate.

## class ArenaProcessor(size,camera,recording)
size: tuple (w,h) in pixels  
camera: int camera index default 0 (first camera)  
recording: boolean default False. True to record the arena to output.avi - the frame rate is set quite low. You may need to tweak that.

### update()
return: The arena image overlaid with robot ID and outlines  
This is called by ArenaManager.py to periodically update the streamed video.  
### getRobots()  
Returns the dictionary of robots robots[id]=x,y,heading. X and y are adjusted using the camera scale parameter so that they represent millimeters instead of pixels.
### SetBotColors(colors)  
colors: dict[botid]=tuple (r,g,b)
Used to set the colors of the robot outlines. By default robots with Id 1-4 are colored blue whilst those 5-8 are coloured red. This identifies members of each time. But, each robot could have a different color if the game was for individuals.  
### setBotColor(Id,color)  
id: int robot number
color: tuple (r,g,b)  
Sets the outline color of the specified robot.
