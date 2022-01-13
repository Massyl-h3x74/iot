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
from rpiutils import getmac

# Measurement related
# seconds between each measure.
measure_interleave = 10

client      = None
timer       = None
log         = None
__shutdown  = False
MQTT_TOPICS     =  "1R1/014/lux"


# #############################################################################
#
# Functions
#

class Luminosity(MqttComm):
    def __init__(self,unitID):
        super().__init__(self,unitID,MQTT_TOPICS)
        threading.Thread.__init__(self)
        self._frequence = measure_interleave
        self._unitId = str(getmac())
        self._lux = 0
        self._connection.on_connect = self.on_connect
        self._connection.on_disconnect = self.on_disconnect
        self._connection.on_subscribe = self.on_subscribe
        self._connection.on_publish = self.on_publish
        self._connection.on_message = self.on_message
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
        self._connection.subscribe(MQTT_TOPICS)
        do_every(self._frequence,publishSensors)
    # The callback for a received message from the server.

    def on_message(self,client, userdata, msg):
        ''' process incoming message.
            WARNING: threaded environment! '''
        payload = json.loads(msg.payload.decode('utf-8'))
        log.debug("Received message '" + json.dumps(payload) + "' on topic '" + msg.topic + "' with QoS " + str(msg.qos))
        if(payload["dest"] == self._unitId):
            print("command reçu", payload['value'])
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



