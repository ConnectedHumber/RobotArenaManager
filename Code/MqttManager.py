"""
MqttManager.py

a class to encapsulate MQTT handling

mqttc=MqttManager()

mqttc.setCallback(which,target_function)

mqttc.publish(topic,payload

"""

import paho.mqtt.client as paho
import sys
import time
import logging


# todo - allow access to connected humber broker
mqttBroker = 'localhost'    # mqtt.connectedhumber.org
mqttClientUser = None       #
mqttClientPassword = None   #

mqttConnectTimeout=20	    # only checked on startup
mqttKeepAlive=60		    # client pings server if no messages have been sent in this time period.
MAX_MESSAGE_NUMBER=9999
MAX_JOBS=200                # job backlog


class MQTT():

    topic='#'
    mqttc=paho.Client()

    om_message_callback=None    # function to call

    def __init__(self,on_message_callback=None):

        self.on_message_callback=on_message_callback

        # connect to the mqtt broker or bust
        # the following method logs any errors
        self.connectToBroker()

    def __del__(self):
        self.mqttc.loop_stop()

    #####################################
    #
    # on_connect() callback from MQTT broker
    #
    def on_connect(self,mqttc, obj, flags, rc):

        if rc==0:
            self.brokerConnected=True
            logging.info("on_connect(): callback ok, subscribing to Topic: %s",self.topic)
            mqttc.subscribe(self.topic, 0)
        else:
            self.brokerConnected=False
            logging.info("on_connect(): callback error rc=%s",str(rc))

    #####################################
    #
    def set_on_message_callback(self,callback):
        self.on_message_callback=callback

    #####################################
    #
    # subscribe(topic,callback)
    #
    # subscribes to the topic and sets the callback
    # function
    def subscribe(self,topic,on_message_callback):
        if not self.brokerConnected: self.connectToBroker()
        if not self.brokerConnected:
            logging.error("subscribe(): Unable to connect to broker")
            return False
        self.mqttc.subscribe(topic, 0)
        self.on_message_callback=on_message_callback
        return True


    def publishPayload(self,topic,payload):
        '''
        meant to be called from outside
        :param topic:
        :param payload:
        :return:
        '''

        #print("MqttManager: Publish to ",topic,payload)
        self.mqttc.publish(topic,payload)

    ################################
    #
    # on_message() MQTT broker callback
    #
    # redirects to any method set by users
    #
    def on_message(self,mqttc, obj, msg):
        if self.on_message_callback:
            self.on_message_callback(mqttc,obj,msg)

    ################################
    #
    # on_subscribe() MQTT Broker callback
    #
    # information only
    #
    def on_subscribe(self,mqttc,obj,mid,granted_qos):
        global logging
        logging.info("on_subscribe(): Subscribed with mid=%s",str(mid))


    ################################
    #
    # connectToBroker
    #
    #
    def connectToBroker(self):

        self.brokerConnected=False

        logging.info("connectToBroker(): Trying to connect to the MQTT broker")

        # calls may be redirected
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_subscribe = self.on_subscribe
        self.mqttc.on_message = self.on_message

        # use authentication?
        if mqttClientUser is not None:
            logging.info("connectToBroker(): using MQTT authentication")
            self.mqttc.username_pw_set(username=mqttClientUser, password=mqttClientPassword)
        else:
            logging.info("main(): not using MQTT autentication")

        # terminate if the connection takes too long
        # on_connect sets a global flag brokerConnected
        startConnect = time.time()
        self.mqttc.loop_start()	# runs in the background, reconnects if needed
        self.mqttc.connect(mqttBroker, keepalive=mqttKeepAlive)

        while not self.brokerConnected:
            if (time.time() - startConnect) > mqttConnectTimeout:
                logging.error("connectToBroker(): broker on_connect time out (%ss)", mqttConnectTimeout)
                return False

        logging.info("connectToBroker(): Connected to MQTT broker after %s s", int(time.time() - startConnect))
        return True


