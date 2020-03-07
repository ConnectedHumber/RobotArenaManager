# MqttManager.py 

This program provides a simplified interface to PAHO MQTT. Essentially, all the ArenaManager needs to do is publish commands to the topic 'pixelbot/location'

MqttManager.py is configured (at the top) to talk to an MQTT broker on the local network - in my case Mosquittto running on the same Pi as the ArenaManager.py program. 

Because this is behind enemy lines on my private network I haven't set a username or password but the code will use them if supplied.

You need to edit these values at the top of MqttManager.py

```
mqttBroker = 'localhost'    
mqttClientUser = None       
mqttClientPassword = None   
```
