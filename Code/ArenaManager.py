# import the necessary packages
#from pyimagesearch.motion_detection import SingleMotionDetector
import MqttManager
import json
from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import cv2
from ArenaProcessing import ArenaProcessor
from Params import *
import time


frameSize=(Params[PARAM_FRAME_WIDTH],Params[PARAM_FRAME_HEIGHT])
AP= ArenaProcessor(frameSize)

Robots={} # populated during update

class StringDefs:
    ' used to make changes /capitalisation easier'
    cmd="cmd"
    mainTopic="pixelbot/"
    arenaTopic=mainTopic+"arena"
    location="location"
    loc="loc"
    botId="botId"
    heading="heading"
    color="color"
    setColor="setColor"
    enableCrosshairs="enableCrosshairs"
    state="state"
    on="on"
    off="off"
    replyTo="replyTo"   # sub topic
    getAllRobots="getAllRobots"
    robots="robots"
    x="x"
    y="y"

Strings=StringDefs()

def on_message_callback(mqttc,obj,msg):
    """
    The callback used by the MQTT manager when messages are heard
    NOTE: The MQTT manager listens for everything

    :param mqttc: mqtt client instance
    :param obj:
    :param msg: mqtt message
    :return:
    """
    global MQTT,AP,Robots
    # decode the msg payload
    msgDic = json.loads(msg.payload)


    # todo make text constants

    if msg.topic!=Strings.arenaTopic: return  # not for me
    if Strings.cmd not in msgDic:         return  # don't know what to do

    # commands aimed at specific bots
    if msgDic[Strings.cmd]==Strings.loc:
        # request for the location of 1 bot
        if Strings.botId not in msgDic:   return   # give me a clue!
        botId=msgDic[Strings.botId]
        if not botId in Robots:     return  # don't know him

        reply = {
            Strings.loc:Robots[botId]
          }
        payload = json.dumps(reply)
        MQTT.publish(Strings.mainTopic + str(botId), payload)
        return

    if msgDic[Strings.cmd]==Strings.setColor:
        if Strings.BotId not in msgDic:   return
        botId = msgDic[Strings.botId]
        if not botId in Robots:     return  # don't know him
        if Strings.color not in msgDic:   return
        AP.setBotColor(botId,mgsDic[Strings.color])


    #-----------------------------------------
    elif msgDic[Strings.cmd]==Strings.enableCroshairs:
        if Strings.state in msgDic:
            state=msgDic[Strings.state]
            if state==Strings.on:
                AP.enableCrosshairDisplay(True)
            else:
                AP.enableCrosshairDisplay(False)
            return
    #-------------------------------------------
    elif msgDic[Strings.cmd]==Strings.getAllRobots:
        # which topic to publish to
        if Strings.replyto not in msgDic: return

        reply=  {
            Strings.robots:Robots
            }

        payload = json.dumps(reply)
        MQTT.publishPayload(Strings.mainTopic + Strings.replyTo, payload)
        return

# initialise the MQTT manager and tell it where to send message callbacks
MQTT=MqttManager.MQTT(on_message_callback)

def publishAllLocations():
    # use
    pass

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None  # obtained from ArenaProcessing
lock = threading.Lock()
 
# initialize a flask object
app = Flask(__name__)

@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")

# image processing 
def updateOutputFrame():
    # grab global references to the video stream, output frame, and
    # lock variables
    global outputFrame, lock, ipd,Robots

    lastPush=time.time()-1  # force a push on first pass
    while True:
        with lock:
            # order is important
            outputFrame = AP.update()

            if time.time()-lastPush>=1:
                # push robot info to game controller
                R=AP.getRobots()
                Robots={}
                for bot in R:
                    #botId=bot() # bound method
                    (x,y),pos=R[bot]
                    x=int(x)
                    y=int(y)
                    Robots[bot]=(x,y,pos)

                reply = {
                    Strings.robots: Robots
                }

                payload = json.dumps(reply)
                MQTT.publishPayload(Strings.mainTopic + Strings.location, payload)
                lastPush=time.time()

        # scale down maintaining aspect ratio
        # just making a 640 pixel wide image for streaming
        h,w=outputFrame.shape[:2]
        aspect=640/w
        newHeight=int(aspect*h)

        outputFrame=cv2.resize(outputFrame, (640,newHeight), interpolation=cv2.INTER_LINEAR)

        cv2.imshow("output", outputFrame)

        if cv2.waitKey(1) & 0xFF == ord('q'):

            cv2.destroyAllWindows()
            break

def generate():
    '''
    Generate the video stream
    :return: Nothing
    '''

    global outputFrame, lock
 
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue
 
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
 
            # ensure the frame was successfully encoded
            if not flag:
                continue
 
        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
            bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == '__main__':

    # start a thread that will perform bot detection
    t = threading.Thread(target=updateOutputFrame)
    t.daemon = True
    t.start()
 
    # start the flask app
    app.run(host="0.0.0.0", port=8000, debug=True,threaded=True, use_reloader=False)
 
