"""
Robot.py


"""

# contour x/y co-ords may differ by only a few pixels
# this is the max allowed amount

xyJitter=10  # coordinates within this distance are the same object

import math
import cv2
from Decorators import *


def getTeamColor(botId):
    if botId <= 4:
        return (255, 0, 0)  # blue team
    else:
        return (0, 0, 255)  # red team


class robot:

    def __init__(self,x=0,y=0,r=0):
        self.location=(x,y) # centre of the robot
        self.director=(0,0) # centre of the direction box
        self.botRadius=r    # overwritten later
        self.botId=None
        self.color=(255,255,0)
        self.textColor=(255,255,255)
        self.dotsFound={}    # x,y co-ords to eliminate duplicates
        self.contour=None

    def setSize(self,botRadius):
        self.botRadius=botRadius

    def getSize(self):
        return self.botRadius

    def setContour(self,points):
        '''
        The contour should be a list of 4 x/y points describing the four vertices of the robot
        :param points: [[x0,y0],.....[xn,yn]]
        :return: Nothing
        '''
        self.contour=points

    def getContour(self):
        '''
        Returns the bot contour
        :return: list of points
        '''
        return self.contour

    def contourContains(self,point):
        if self.contour is None:
            #print("WARNING: contourContains(",point,") - self contour is None")
            return False

        r=cv2.pointPolygonTest(self.contour,point,False)
        #print("polygonTest returns",r)
        if r>0: return True
        return False

    def distance(self,pos1,pos2):
        '''
        calculate the distance between two points using pythagorus

        :param pos1: tuple (x,y
        :param pos2: tuple (x,y)
        :return: distance between point
        '''
        x1,y1=pos1
        x2,y2=pos2
        diffX=abs(x1-x2)
        diffY=abs(y1-y2)
        return math.sqrt(diffX*diffX+diffY*diffY)

    def setLocation(self,pos):
        '''
        Set the co-ordinates of the robot
        :param pos: tupe (x,y) position
        :return: Nothing, location is set if not already set
        '''
        # has location already been set?
        if self.location!=(0,0): return False

        self.location=pos
        return True

    def getLocation(self):
        '''
        return the x/y pixel coordinates of the robot
        :return:tuple (x,y) current robot position
        '''
        return self.location


    def setDirector(self,pos):
        '''
        The robot has a rectangular direction indicator (could also be a circle)
        This method records the centre co-ords of that indicator.
        Used to calculate heading
        :param x: x position of direction indicator centre
        :param y: y position of direction indicator centre
        :return: True if added otherwise false
        '''

        # silently ignore , caller will be scanning all bots
        if not self.contourContains(pos): return False

        if self.director != (0, 0):
            # jitter
            dist=self.distance(pos, self.director)
            if dist<= xyJitter:
                #print("WARNNG: director jitter. Attempt to change director from ", self.director, "to", pos,"distance",dist)
                return False

        self.director=pos
        return True

    def getId(self):
        '''
        Returns the robot Id. See also addIdDot()

        :return: int Id
        '''
        return self.botId

    #@traceit
    def addIdDot(self,dotPos):
        '''
        called each time a new ID dot is found

        :param dotPos: tuple (x,y) location of the dot
        :return: True if added, False otherwise
        '''
        # silently ignore, caller may be scanning all bots
        if not self.contourContains(dotPos): return False

        for dot in self.dotsFound:
            dist=self.distance(dot,dotPos)
            if dist<=xyJitter:
                #print("WARNING: duplicate existing dot at",dot,"dup at=",dotPos,"distance=",dist)
                return False

        self.dotsFound[dotPos]=1
        self.botId = len(self.dotsFound.keys())

        return True

    def setColor(self,color):
        '''
        Set the color to use for drawing the bot outline
        :param color: tuple (r,g,b)
        :return:
        '''
        self.color=color

    def setTextColor(self,color):
        '''
        Set the color used to annotate the bot
        :param color: tuple (r,g,b)
        :return:
        '''
        self.textColor=color

    def getPosAndHeading(self):
        '''
        returns the current x/y position of this robot
        and calculated Nautical heading in degrees

        :return: (x,y),Heading
        '''
        heading=self.getHeading()
        return self.location,heading

    def getHeading(self):
        '''
        Attempts to calculate a robot heading where North=0 degrees

        uses self.location and self.director to figure out the heading
        :return: None
        '''
        heading = 0  # North or +90

        if self.director==(0,0):
            # director not found
            return None

        # atan expects y to increase bottom up
        (boxX,boxY)=self.director
        (botX,botY)=self.location

        angle = math.atan2(boxY - botY, botX - boxX)
        deg = int(math.degrees(angle))

        if deg < 0:  # clockwise angle from 0
           heading = (450 + deg) % 360
        else:
           heading = 90 + deg

        #print("getHeading() bot", self.botId, " bot x/y", self.location, "director at", self.director,"heading",int(heading))

        # print("heading x,y=",x,y,"cx/cy=",roi_cx,roi_cy,"deg",deg,"heading",heading)
        return int(heading)

    def annotate(self,image):

        # botId might not be available at the time of drawing

        # todo caller should set bot team color
        if self.botId is not None:
                self.color = getTeamColor(self.botId)

        cx,cy=self.location
        # ints required for drawing
        cx,cy=int(cx),int(cy)
        rad=int(self.botRadius)
        h,w,p=image.shape

        if cy-rad-5>0:  # 5 is just a small gap
            # place text above the shape
            textY=cy-rad-5
        else:
            # place text below the shape
            textY=cy+rad+5
        textX=cx-rad

        cv2.putText(image, str(self.botId) + " hdg:" + str(self.getHeading()), (textX, textY), cv2.FONT_HERSHEY_SIMPLEX,0.5,self.textColor, 1)

        self.drawOutline(image)

        # contours within the bot
        # the direction indicator
        cx,cy=self.director
        cv2.circle(image, (int(cx), int(cy)), 8, self.color, 1)  # out circle defining the director

        # the dots
        for pos in self.dotsFound.keys():
            cv2.circle(image, pos, 5, self.color, 1)  # out circle defining the dots

    def drawId(self,image):
        '''
        puts the ID number of the bot at the bot centre

        :param image: image to draw on
        :return: Nothing, the ID is drawn
        '''
        x,y=self.location
        x=int(x-20) # CENTRING
        y=int(y+10)
        cv2.putText(image, str(self.botId), (x,y), cv2.FONT_HERSHEY_SIMPLEX,2, self.textColor, 2)

    def drawOutline(self,image):
        #cv2.drawContours(image, self.contour, -1, self.color, 2)
        cv2.polylines(image, [self.contour], True, self.color,2)  # True = isClosed

    def showInfo(self):
        x,y=self.location
        print("showInfo() ID",self.botId,"x,y",int(x),int(y),"Direction",self.getHeading(),"size",int(self.botRadius),"contour",self.contour)