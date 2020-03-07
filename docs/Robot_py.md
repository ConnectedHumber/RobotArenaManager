# Robot.py

This is the robot class. When a robot is found by ArenaProcessing.py a new instance is created and added to the list of robots found.

Only the main methods are documented below - there are others some of which are depracated and others used internally.

## class robot.py(x,y,r)  
x: float is the x coordinate returned from openCVs' minEnclosingCircle()  
y: float is the y coordiate also returned from openCVs' minEnclosingCircle()  
r: float is the radius of the circle enclosing the robot, returned from openCVs' minEnclosingCircle()  

x/y give the centre of the robot hat which is also over the centre of the robot.  
r gives an indication of the size of contour and is used to quickly distinguish the robot from the other contour features.

### setSize(radius)  
radius: float minEnclosingCirle() radius  
redundant since the openCV boxPoints() are now used (see setContour())

### setContour(points)
point: list of coordinate pairs obtained from openCV boxPoints()  
Used to check if a dot or heading indicator belong to this robot.   

### setLocation(pos)  
pos: tuple (x,y) x & y are float  
returns True if the location was set.  
Identifies the current location of the robot in pixels. (openCV returns float values)  

### setDirector(pos)  
pos: tuple (x,y) x & y are float  
Returns True if set otherwise returns False.  
Checks if pos is within the countour.     

### addIdDot(pos)  
pos: tuple (x,y) x & y are float  
Returns True if successful otherwise False.  
Checks if pos is within the robot contour if so adds the id dot to the list of dots owned by the robot.  

### setColor(color)  
color: tuple (r,g,b)  
Sets the drawing color for this robot.  

### setTextColor(color)  
color: tuple (r,g,b)  
Sets the text drawing color for this robot. (normally white)  

### getPosAndHeading()  
Returns (botPos,heading) where botPos is a tuple (x,y)  
x and y are floats  
heading is an int since a heading accuracy better than 1 degree is unlikely.  

### drawId(image)  
Draws the current botId (number of dots) at the robot centre on the image. This provides visual identification on screen.

### drawOutline(image)  
Draws the robot outline using openCVs' polylines() method. Since the shapes are rotated rectangles then that's what we get.




