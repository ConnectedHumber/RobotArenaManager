# ArenaManager.py

This program uses Flask to create a streamed video of the robot arena. Other devices may access the video using their web browsers pointed to port 8000 on the machine running ArenaManager.py.

ArenaManager.py calls the ArenaProcessing::update() interface. This returns the image of the arena with robot outlines and ID numbers overlaid. ArenaManager then scales this image down to a sensible size for streaming.

ArenaManager.py also calls the ArenaProcessing::getRobots() interface which returns a dictionary of all robtos discovered in this update cycle. The dictionary is json encoded and sent to an MQTT broker (using MqttManager.py)  with the topic 'pixelbot/location'.

The MQTT payload looks like this:-
```
{"robots": {"1": [1245, 841, 49], "2": [1069, 778, 108], "7": [867, 772, 129], "8": [1339, 713, 134], "6": [1040, 602, 15], "4": [1311, 536, 149], "5": [1189, 486, 230], "3": [951, 473, 18]}}
```

ArenaManager can subscribe to the broker but it is, currently, envisaged we just push the robot information to the MQTT broker.

The game controller program (being written by CrazyRobMiles) will be listening to the broker and will pass the coordinates to the robots. The robots, in turn, listen for messages from the game controller and act on them (CrazyRobMiles is in charge of the robot firmware.
