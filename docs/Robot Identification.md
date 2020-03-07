# Robot Identification

During development I tried numerous ways to identify the robot and its heading.

This is a picture of the PixelBot designed by CrazyRobMiles. 

![PixelBot](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/DSC00910.JPG)

It has an ultrasonic range detector on the front, a 12 LED neo-pixel ring on the top and a speaker below the ring. It, currently, uses a WeMOS to enable WiFi connectivity.

I tried identifying the robot using the LEDs with red/blue as leading LED to identify the team and yellow/magenta/green/cyan to identify the team member. Unfortunately this proved too difficult to work with. The bare LEDs saturated the camera light sensors and when a filtered through a translucent cover they were too diffuse.

I tried putting a circular opaque cap on the top - you can see some I tried in this photo. 
![Caps](https://github.com/ConnectedHumber/RobotArenaManager/blob/master/images/DSC00912.JPG)

Initially I tried putting QR codes on the caps but, although the QR codes were found the images were too blurred after rotation for the openCV detector to read them. So I resorted to using dots on the caps.

Using a circular cap (diameter=54mm, same as the neo-pixel ring) proved to be too small. The small dots were not easily isolated in the contours. It also became difficult to identify the dots by color because I am using a grayscale image - perhaps if I used edge detection on each color channel separately I might have had some success, but I didn't try that. Working on a single channel image also meant the image processing should be quicker than working on three color channels and recombining later.

In the end I opted for a simple rectangular hat for the PixelBot with black and white features. The rectangles fit within the boundary of the robot. A big rectangle is easily detected. The size of the rectangle meant that the features could be bigger - though one has to be careful not to place them too close to the edges of the rectangle otherwise they get incorporated into the contour. You should preview the contour image using CameraSetup.py to check that all features are edged separately.

The ArenaProcessing.py code counts small dots within the boundary of the robot rectangle to identify the bot number.

A larger dot or rectangle on the forward side of the robot is used to identify the heading using the centre of the robot contour and the centre of the heading dot contour. 

There needs to be a measurable difference in size between the Id dots and the 'heading' shape
