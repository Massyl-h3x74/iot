from MQTTlum import Luminosity

def driver():

    # Global variables
    global client, timer, log
    # Function ctrlc_handler
    def ctrlc_handler(signum, frame):
        global __shutdown
        log.info("<CTRL + C> action detected ...");
        __shutdown = True
        # Stop monitoring
        stopMonitoring()

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

    signal.signal(signal.SIGINT, ctrlc_handler)

    lum = Luminosity()
    lum.start()


# Execution or import
if __name__ == "__main__":

    # Logging setup
    logging.basicConfig(format="[%(asctime)s][%(module)s:%(funcName)s:%(lineno)d][%(levelname)s] %(message)s", stream=sys.stdout)
    log = logging.getLogger()

    print("\n[DBG] DEBUG mode activated ... ")
    log.setLevel(logging.DEBUG)
    #log.setLevel(logging.INFO)

    # Start executing
    driver()


# The END - Jim Morrison 1943 - 1971
#sys.exit(0)



# The END - Jim Morrison 1943 - 1971
#sys.exit(0)