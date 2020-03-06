'''
CameraScaling.py

Utility to determine the camera image scale. (i.e. mm per pixel

Place an A4 sheet on the arena then adjust the on screen rectangle
till it fits. An A4 sheet has dimesions 297x210mm (landscape)
therefore we can deduce the distance represented by 1 pixel

This should be done before ArenaManager.py runs

Stores the PARAM_CAMERA_SCALE parameter in Settings.json for use by ArenaManager.py
'''

import cv2
from Params import *

# load the current parameters

getParams()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,Params[PARAM_FRAME_WIDTH])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,Params[PARAM_FRAME_HEIGHT])

A4=(295,210) # landscape

# wait for the camera to deliver the video frames
scene=None
while scene is None:
    ret,scene = cap.read()


print("Focus the camera and adjust the rectangle with '+' or '-' till an A4 sheet of paper fits the rectangle")

while True:
    ret,scene=cap.read()
    if scene is not None:
        H,W=scene.shape[:2]
        CX=W/2
        CY=H/2
        rw,rh=A4[0]*Params[PARAM_CAMERA_SCALE],A4[1]*Params[PARAM_CAMERA_SCALE]

        # target rectangle points
        TL=(int(CX-rw/2),int(CY-rh/2))
        BR = (int(CX + rw / 2), int(CY + rh / 2))

        # draw the scaled recangle
        cv2.rectangle(scene,TL,BR,(0,255,0),1)
        cv2.imshow("scene ",scene)

    key=cv2.waitKey(1) & 0xFF

    #print("key=",key)

    if key==ord('q'):
        break
    elif key == ord('s'):
        saveParams()
        break
    elif key==ord("=") or key==ord('+'): # same key as + (shift =) or numeric keypad +
        Params[PARAM_CAMERA_SCALE]=Params[PARAM_CAMERA_SCALE]+0.01
    elif key==ord("-"): # same as numeric keypad -
        Params[PARAM_CAMERA_SCALE]=Params[PARAM_CAMERA_SCALE]-0.01

cv2.destroyAllWindows()