
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

import random
import logging
#import tsl2561
# MQTT related imports
import paho.mqtt.client as mqtt
from libutils.rpi_utils import getmac


MQTT_SERVER="192.168.0.210"
MQTT_PORT=1883
MQTT_BASE_TOPIC = "1R1/014"
MQTT_TYPE_TOPIC = "temperature"
MQTT_PUB = "/".join([MQTT_BASE_TOPIC, MQTT_TYPE_TOPIC])


MQTT_SUB = MQTT_PUB


MQTT_QOS=0 # (default) no ACK from server


MQTT_USER="azerty"
MQTT_PASSWD="azerty"

measure_interleave = 5

client      = None
timer       = None
log         = None
__shutdown  = False



# #############################################################################
#
# Functions
#


#
# Function ctrlc_handler
def ctrlc_handler(signum, frame):
    global __shutdown
    log.info("<CTRL + C> action detected ...");
    __shutdown = True
    # Stop monitoring
    stopMonitoring()


#
# Function stoping the monitoring
def stopMonitoring():
    global client
    global timer
    log.info("[Shutdown] stop timer and MQTT operations ...");
    timer.cancel()
    timer.join()
    del timer
    client.unsubscribe(MQTT_SUB)
    client.disconnect()
    client.loop_stop()
    del client

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

def on_connect(sekf,client, userdata, flags, rc):
    log.info("Connected with result code : %d" % rc)

    if( rc == 0 ):
        log.info("subscribing to topic: %s" % MQTT_SUB)
        # Subscribe to topic
        client.subscribe(MQTT_SUB);
        do_every(self,publishSensors)



def on_message(client, userdata, msg):
    ''' process incoming message.
        WARNING: threaded environment! '''
    payload = json.loads(msg.payload.decode('utf-8'))
    log.debug("Received message '" + json.dumps(payload) + "' on topic '" + msg.topic + "' with QoS " + str(msg.qos))

    log.debug("Temperature is %s deg. %s" % (payload['value'],payload['value_units']))

    # TO BE CONTINUED
    log.warning("TODO: process incoming message!")


def on_publish(client, userdata, mid):
    log.debug("mid: " + str(mid)+ " published!")


def on_subscribe(mosq, obj, mid, granted_qos):
    log.debug("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mosq, obj, level, string):
    log.debug(string)


def temperature():
        bus = smbus.SMBus(1)

        config = [0x00, 0x00]
        bus.write_i2c_block_data(0x1f, 0x01, config)


        bus.write_byte_data(0x1f, 0x08, 0x03)

        time.sleep(0.5) # MCP9808 address, 0x18(24)

        data = bus.read_i2c_block_data(0x1f, 0x05, 2)
        ctemp = ((data[0] & 0x1F) * 256) + data[1]
        if ctemp > 4095 :

                ctemp -= 8192

        ctemp = ctemp * 0.0625
        return(ctemp)

def publishSensors():

    temp = temperature()

    temp = "{:.2f}".format(temp)
    log.debug("RPi temperature = " + temp)
    # generate json payload
    jsonFrame = { }
    jsonFrame['unitID'] = str(getmac())
    jsonFrame['value'] = json.loads(temp)
    jsonFrame['value_units'] = '%'
    # ... and publish it!
    client.publish(MQTT_PUB, json.dumps(jsonFrame), MQTT_QOS)

