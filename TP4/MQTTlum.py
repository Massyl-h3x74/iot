# #############################################################################
#
# Import zone
#
import errno
import os
import signal
import syslog
import sys

import time
from MQTTtemp import ctrlc_handler
from TP4.MQTTtemp import do_every
import smbus

import time
import threading
import json
from threading import Thread
import random
import logging
#import tsl2561
# MQTT related imports
import paho.mqtt.client as mqtt
from connexion import MqttComm

'''
# To extend python librayrt search path
_path2add='./libutils'
if (os.path.exists(_path2add) and not os.path.abspath(_path2add) in sys.path):
    sys.path.append(os.path.abspath(_path2add))
# Raspberry Pi related imports
from rpi_utils import *
'''
from libutils.rpi_utils import getmac



# #############################################################################
#
# Global Variables
#
MQTT_SERVER="192.168.0.210"
MQTT_PORT=1883
# Full MQTT_topic = MQTT_BASE + MQTT_TYPE
MQTT_BASE_TOPIC = "1R1/014"
MQTT_TYPE_TOPIC = "luminosity"
MQTT_PUB = "/".join([MQTT_BASE_TOPIC, MQTT_TYPE_TOPIC])
MQTT_COMMAND = "command"
# First subscription to same topic (for tests)
MQTT_SUB = "/".join([MQTT_BASE_TOPIC, MQTT_TYPE_TOPIC,MQTT_COMMAND])
# ... then subscribe to <topic>/command to receive orders
#MQTT_SUB = "/".join([MQTT_PUB, "command"])

MQTT_QOS=0 # (default) no ACK from server
#MQTT_QOS=1 # server will ack every message
MQTT_USER="azerty"
MQTT_PASSWD="azerty"

# Measurement related
# seconds between each measure.
measure_interleave = 10

client      = None
timer       = None
log         = None
__shutdown  = False



# #############################################################################
#
# Functions
#

class Luminosity(MqttComm):
    def __init__(self):
        threading.Thread.__init__(self)
        self._frequence = measure_interleave
        self._unitId = str(getmac())
        self._lux = 0
        self._connection = mqtt.Client()
        self._connection.on_connect = self.on_connect
        self._connection.on_disconnect = self.on_disconnect
        self._connection.on_subscribe = self.on_subscribe
        self._connection.on_publish = self.on_publish
        self._connection.on_message = self.on_message
        if len(MQTT_USER)!=0 and len(MQTT_PASSWD)!=0:
            client.username_pw_set(MQTT_USER,MQTT_PASSWD); # set username / password
    #

    #
    # threading.timer helper function
    def do_every (interval, worker_func, iterations = 0):
        global timer
        # launch new timer
        if ( iterations != 1):
            timer = threading.Timer (
                  interval,
                  do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1])
            timer.start();
        # launch worker function
        worker_func();


    # --- MQTT related functions --------------------------------------------------
    # The callback for when the client receives a CONNACK response from the server.


    def on_connect(self,client,userdata,flags,rc):
        if(rc != mqtt.MQTT_ERR_SUCCESS):
            print("connexion failed %s " %(mqtt.error_string(rc)))
        self._connected = True
        self._connection.subscribe(MQTT_SUB)
        do_every(self._frequence,publishSensors)
    # The callback for a received message from the server.


    def on_message(self,client, userdata, msg):
        ''' process incoming message.
            WARNING: threaded environment! '''
        payload = json.loads(msg.payload.decode('utf-8'))
        log.debug("Received message '" + json.dumps(payload) + "' on topic '" + msg.topic + "' with QoS " + str(msg.qos))
        if(payload["dest"] == self._unitId):
            print("command reçu", payload['value'])

        # First test: subscribe to your own publish topic
        # ... then remove later
        #log.debug("Temperature is %s deg. %s" % (payload['value'],payload['value_units']))

        # TO BE CONTINUED
        #log.warning("TODO: process incoming message!")


    # The callback to tell that the message has been sent (QoS0) or has gone
    # through all of the handshake (QoS1 and 2)
    def on_publish(client, userdata, mid):
        log.debug("mid: " + str(mid)+ " published!")

    def on_subscribe(mosq, obj, mid, granted_qos):
        log.debug("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(mosq, obj, level, string):
        log.debug(string)

    # ----- Lumiere -----
    def publishSensors(self):
        # get CPU temperature (string)
        lum = lumiere()
        # add some randomisation to the temperature (float)
        #_fcputemp = float(lum) + random.uniform(-10,10)
        # reconvert to string with quantization
        lum = "{:.2f}".format(lum)
        log.debug("RPi temperature = " + lum)
        # generate json payload
        jsonFrame = { }
        jsonFrame['unitID'] = self._unitId
        frequence = self._frequence
        jsonFrame['value'] = json.loads(lum)
        jsonFrame['value_units'] = 'lux'
        # ... and publish it!
        client.publish(MQTT_PUB, json.dumps(jsonFrame), MQTT_QOS)

    def lumiere(self):
        bus = smbus.SMBus(1)
        bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
        bus.write_byte_data(0x39, 0x01 | 0x80, 0x02)

        data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)
        data1 = bus.read_i2c_block_data(0x39, 0x0E | 0x80, 2)

        ch0 = data[1] * 256 + data[0]
        ch1 = data1[1] * 256 + data1[0]
        print ("Full Spectrum(IR + Visible) :%d lux" %ch0)
        return(ch0)



