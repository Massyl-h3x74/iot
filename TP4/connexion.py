
import os
import sys
import time
import json
from threading import Thread, Event
import paho.mqtt.client as mqtt



# MQTT settings
MQTT_SERVER     = "192.168.0.210"
MQTT_PORT       = 1883

MQTT_KEEP_ALIVE         = 60    # set accordingly to the mosquitto server setup
MQTT_RECONNECT_DELAY    = 7     # minimum delay before retrying to connect (max. is 120 ---paho-mq  defaults)

MQTT_USER       = 'azerty'
MQTT_PASSWD     = 'azerty'

# input topics
#MQTT_TOPICS     = [ "#" ]           # allowed to subscribe to all ... but carefull filters required ;)


class MqttComm(Thread):
    # class attributes ( __class__.<attr_name> )

    # objects attributes
    _connection     = None  # mqtt client
    _connected      = False
    _mqtt_user      = None
    _mqtt_server    = None
    _mqtt_port      = None
    _mqtt_passwd    = None
    _mqtt_topics    = None  # list of topics to subscribe to
    _unitID         = None
    _addons         = None  # additional parameters

    _shutdownEvent = None

    def __init__(self, unitID, mqtt_topics, shutdownEvent, *args, **kwargs ):
        ''' Initialize object '''
        super().__init__()
        self._unitID = unitID
        self._mqtt_user = "azerty"
        self._mqtt_server = "192.168.0.210"
        self._mqtt_port = 1883
        self._mqtt_passwd = "azerty"
        self._mqtt_topics = mqtt_topics
        self._addons        = kwargs

        if( self._shutdownEvent is None ):
            print("unspecified global shutdown ... thus locally specified ...")
            #self._shutdownEvent = Event()

        # setup MQTT connection
        self._connection = mqtt.Client(self._unitID)
        self._connection.username_pw_set(self._mqtt_user, self._mqtt_passwd)
        self._connection.on_connect = self.on_connect
        self._connection.on_disconnect = self.on_disconnect
        self._connection.on_subscribe = self.on_subscribe
        self._connection.on_publish = self.on_publish
        self._connection.on_message = self.on_message
        self._connection.on_unsubscribe = self.on_unsubscribe
        #self._connection.on_log = self.on_log

        print("initialization done")



    def run(self):
        self._connection.connect(self._mqtt_server ,self._mqtt_port)
        print("Connected to server %s on port %s" % (MQTT_SERVER, MQTT_PORT))
        counter = 0
        #self._connection.subscribe(self._mqtt_topics)
        try:
            while not self._shutdownEvent.is_set() or counter == 100:
                if self._connection.loop(timeout=2.0) != mqtt.MQTT_ERR_SUCCESS:
                    print("loop failed, sleeping a bit before retrying")
                    time.sleep(2)
                #self._connection.publish("1R1","{ \"dest\":" + str( self._unitID) + " }")
                counter = counter + 1
        except Exception as ex:
            print("Exception : " + str(ex))

        #self._connection.disconnect()


    def on_disconnect(self,client,userdata,rc):
        self._connected = False
        print("Unit %s <<< disconnected with message  : %s " % (self._unitID, mqtt.error_string(rc)))


    def on_subscribe(self,client,userdata,mid,granted_ops):
        print("Unit " + str(self._unitID) + " >>> Successfully subscribed to topic " + self._mqtt_topics)


    def on_publish(self, client,userdata,mid):
        pass
        #print("Unit " + str(self._unitID) + " >>> Successfully published to topic")


    def on_unsubscribe(self,client,userdata,mid):
        print("Unsubscriped to topic")

    ''' handles pre-validated MQTT messages, to be implemented by subclasses '''
    def handle_message(self, payload):
        print("mqtt comm handle message")
        pass


    def do_every(interval, function):
        pass


    def on_message(self,client,userdata,message):
        try:
            payload = json.loads(message.payload.decode('utf-8'))
        except Exception as ex:
            print("exception handling json payload from topic '%s': " % str(message.topic) + str(ex))
            return
        if( self._unitID is not None and payload['dest'] != "all" and str(payload['dest']) != str(self._unitID) ):
            #print("msg received on topic '%s' features destID='%s' != self._unitID='%s'" % (str(message.topic),payload['dest'],self._unitID) )
            return
        else:
            self.handle_message(payload)

    def on_log(self,client,userdata,level,buf):
        if( level == mqtt.MQTT_LOG_ERR or level == mqtt.MQTT_LOG_WARNING ):
            print("[log][%s] %s" % (str(level),str(buf)))
