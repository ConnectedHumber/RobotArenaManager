"""
Params.py

Methods to access the parameter settings

Use : 'from Params import *'

"""

import json
import cv2

DataFile="Settings.json"    # todo allow for different 'profiles'

# parameter names

PARAM_CAMERA_SCALE="CAMERA_SCALE"
PARAM_CAMERA_BRIGHTNESS="CAMERA_BRIGHTNESS"
PARAM_CAMERA_SATURATION="CAMERA_SATURATION"
PARAM_CAMERA_CONTRAST="CAMERA_CONTRAST"
PARAM_CAMERA_AUTO_EXPOSURE="CAMERA_AUTO_EXPOSURE"
PARAM_CAMERA_EXPOSURE="CAMERA_EXPOSURE"
PARAM_CAMERA_ISO_SPEED="CAMERA_ISO_SPEED"
PARAM_BLUR_SIZE="BLUR_SIZE"
PARAM_USE_THRESHOLDING="THRESHHOLDING"
PARAM_THRESH_MIN="THRESH_MIN"
PARAM_THRESH_MAX="THRESH_MAX"
PARAM_CANNY_MIN="CANNY_MIN"
PARAM_CANNY_MAX="CANNY_MAX"
PARAM_AFTER_CANNY_THRESH_MIN="AFTER_CANNY_THRESH_MIN"

# min max radius of robot - used to detect robot
PARAM_MIN_BOT_R="MIN_BOT_R"
PARAM_MAX_BOT_R="MAX_BOT_R"
# min max size of ID dots -  used to detect them
PARAM_MIN_DOT_R="MIN_DOT_R"
PARAM_MAX_DOT_R="MAX_DOT_R"
# min max radius of direction dot/square - used to detect them
PARAM_MIN_DIRECTOR_R="MIN_DIRECTOR_R"
PARAM_MAX_DIRECTOR_R="MAX_DIRECTOR_R"



PARAM_FRAME_WIDTH="FRAME_WIDTH"
PARAM_FRAME_HEIGHT="FRAME_HEIGHT"
PARAM_EPSILON="POLYDP_EPSILON"
PARAM_ARENA_MASK_SCALE="ARENA_MASK_SCALE"
PARAM_ARENA_MASK_SIZE="ARENA_MASK_SIZE"
PARAM_SCALE_RECT_SIZE="SCALE_RECT_SIZE"
PARAM_MIN_RAD_BOT="MIN_RAD_BOT"

CV2_CAMERA_BRIGHTNESS=(cv2.CAP_PROP_BRIGHTNESS,PARAM_CAMERA_BRIGHTNESS)
CV2_CAMERA_CONTRAST=(cv2.CAP_PROP_CONTRAST,PARAM_CAMERA_CONTRAST)
CV2_CAMERA_SATURATION=(cv2.CAP_PROP_SATURATION,PARAM_CAMERA_SATURATION)
CV2_CAMERA_EXPOSURE=(cv2.CAP_PROP_EXPOSURE,PARAM_CAMERA_EXPOSURE)
CV2_CAMERA_AUTO_EXPOSURE=(cv2.CAP_PROP_AUTO_EXPOSURE,PARAM_CAMERA_AUTO_EXPOSURE)
CV2_CAMERA_ISO_SPEED=(cv2.CAP_PROP_ISO_SPEED,PARAM_CAMERA_ISO_SPEED)


# Params - read in from Settings.py
# these can be accessed with Params[parameter] but is unsafe
# todo find a way to make the dictionary global using __builtins_ ???_
#
Params = {}

def getParam(param):
    '''
    Safe way to access parameters
    :param param: string parameter name
    :return: parameter value
    '''
    if param in Params: return Params[param]
    # return default value, if it exists
    assert param in DefaultParams,"Attempt to access unknown parameter "+param

    return DefaultParams[param]


# Default values - all based on image resolution of 1920x1080
# radii will need scaling if a different screen resolution is used
# for example the bot radius would be smaller

DefaultParams = {
    PARAM_CAMERA_SCALE: 1.32,
    PARAM_CAMERA_BRIGHTNESS: 4,
    PARAM_CAMERA_CONTRAST: 100,
    PARAM_CAMERA_SATURATION: 16,
    PARAM_CAMERA_EXPOSURE: 32,
    PARAM_CAMERA_AUTO_EXPOSURE: 0,
    PARAM_CAMERA_ISO_SPEED: 2,
    PARAM_BLUR_SIZE: 5,
    PARAM_THRESH_MIN: 100,
    PARAM_CANNY_MIN: 100,
    PARAM_CANNY_MAX: 200,
    PARAM_AFTER_CANNY_THRESH_MIN:100,
    PARAM_MIN_BOT_R: 30,
    PARAM_MAX_BOT_R: 75,
    PARAM_MIN_DOT_R: 1,
    PARAM_MAX_DOT_R: 10,
    PARAM_MIN_DIRECTOR_R: 6,
    PARAM_MAX_DIRECTOR_R: 10,
    PARAM_FRAME_WIDTH: 1920,
    PARAM_FRAME_HEIGHT: 1080,
    PARAM_EPSILON: 0.05,
    PARAM_ARENA_MASK_SCALE: 1,
    PARAM_ARENA_MASK_SIZE: (597, 420),  # W,H
    PARAM_SCALE_RECT_SIZE:(297,210) # A4 target for camera scaling
}



def RestoreDefaults():
    '''
    Overwrites Params with default values

    :return: Params is re-populated
    '''
    global Params
    for k in DefaultParams.keys():
        Params[k]=DefaultParams[k]

def readParams(fname=DataFile):
    '''
    Read parameters from the DataFile
    Populates the Params dictionary
    Currently has to be included in every module

    :return: Params dictionary is populated
    '''
    getParams(fname)

def getParams(fname=DataFile):
    '''
    DEPRACATED

    Read parameters from the DataFile
    Populates the Params dictionary
    Currently has to be included in every module


    :return: Params is populated
    '''
    global Params
    try:
        f=open(fname,"r")
        P=json.loads(f.read())
        f.close()
        print("Parameters read ok from file.")
        for k in P.keys():
            Params[k] = P[k]

    except Exception as e:
        print("Exception loading parameters from ",DataFile,e)
        print("Using default parameters instead")
        for k in DefaultParams.keys():
            Params[k] = DefaultParams[k]


def saveParams(fname=DataFile):
    print("Saving parameters")
    f=open(fname,"w")
    f.write(json.dumps(Params))
    f.close()
