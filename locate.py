#encoding=utf8  
import requests
import urllib
from urlparse import urljoin
import json
import pdb
import serial
import pynmea2
import logging
import time
import sys
import signal
import logging

### URLS ###
URL = "https://ms-shuttle-tlv-server.herokuapp.com"
BECOME = "/becomeBeacon"
REMOVE = "/removeBeacon"
SENDPOS = "/busLocation"
BEACONSTATUS = r"/beaconStatus"


### GENERAL CONSTS ###
DEVICE = "/dev/serial0"
NAME = "Shuttle Driver"
BEACONID = "8fc0537f-3fd3-4713-871f-5fa4b1850f97"
LOCATION_MSGS = ["GGA", "RMC"]
HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}
IGNORE = "ignore"
VALID_BEACON_STATUS = [set(dict()),set(["name","beaconId"])]
LOGPATH = "/var/log/gps.log"
#LOGPATH = r"c:\temp\gps\log.log"

def init_logger(logpath):
    logging.basicConfig(filename=logpath,filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s - ')
    logger = logging.getLogger(__name__)
    return logger

def sigterm_handler(_signo, _stack_frame):
    if _signo == signal.SIGTERM or _signo == signal.SIGINT:
        logging.info("shutting down signal recived")
        print "Sigterm_handler called"
        print "removing beacon"
        logging.info("removing beacon")
        remove_beacon(BEACONID)
    logging.info("exiting")
    sys.exit(0)
    
def validate_beacon_status(beacon_status_json):
    logging.info("validating beaconStatus message")
    if set(beacon_status_json.keys()) not in VALID_BEACON_STATUS:
        logging.error("invalid beaconStatus recived")
        print "Error: recived invalid beaconStatus"
        logging.info("exiting")
        sys.exit(0)
    logging.info("beaconStatus validation succeeded")
    return beacon_status_json

    
def beacon_status():
    logging.info("trying to get beaconStatus")
    r = None
    try:
        r = requests.get(urljoin(URL,BEACONSTATUS), headers=HEADERS)
    except:
        logging.exception("error while getting beaconStatus")
    if r and r.raise_for_status():
        logging.error("error while getting beaconStatus")
        return None
    return validate_beacon_status(json.loads(r.text))
    
def become_beacon(beaconid, name):
    data = {}
    data["beaconId"] = beaconid
    data["name"] = name
    try:
        logging.info("trying to beacome an active beacon")
        r = requests.post(urljoin(URL,BECOME), data=json.dumps(data), headers=HEADERS)    
    except:
        logging.exception("error during a try to beacome an active beacon")
        raise
    return r

def remove_beacon(beaconid):
# TODO: insert the try and except into while with some sleeping, because sometimes the server refuse the connection
# and we need to try harder to rem
    data = {}
    data["beaconId"] = beaconid
    try:
        logging.info("trying to remove beacon")
        r = requests.post(urljoin(URL,REMOVE), data=json.dumps(data), headers=HEADERS)    
    except:
        logging.exception("error during a try to remove the active beacon")
        raise
    return r

def get_location_msg():
  
    logging.info("trying to get location message from gps")
    try:
        logging.info("connecting to serial device: %s" % DEVICE)
        serial_device = serial.Serial(DEVICE)
    except:
        logging.exception("error in opening the serial device")
        print "something happend during serial connection"
        raise
        
    try:
        logging.info("opening NMEAStreamReader")
        streamreader = pynmea2.NMEAStreamReader(serial_device,errors=IGNORE)
    except:
        logging.exception("error in opening NMEAStreamReader")
        print "something happend during pynmea2 reader init"
        raise
    
    while True:
        # TODO: something is borken in this loop, constant ASCII exception
        try:
            for msg in streamreader.next():
                if msg.sentence_type in LOCATION_MSGS:
                    serial_device.close()
                    return msg
        except Exception as ex:
            print "something happend during get_location_msg while loop"
            logging.exception("error in handeling location message")
            #raise
            
def gps_calibrate():
    while True:
        msg = get_location_msg()    
        latitude = msg.latitude
        longitude = msg.longitude
        print latitude, longitude
        logging.info("latitude: %s, longitude: %s" % (latitude,longitude))
        if longitude != 0 and latitude != 0:
            print "valid location"
            logging.info("got a valid location, gps is calibrated")
            return True

def send_location():
    msg = get_location_msg()
    try:
        latitude = float("%07.6f" % msg.latitude)
        longitude = float("%07.6f" % msg.longitude)
    except:
        logging.exception("error in formatting following lat (%s) or\and long (%s)" %(msg.latitude, msg.longitude))
    data = {}
   
    print "location is: %s, %s" % (latitude, longitude)
    logging.info("location is: %s, %s" % (latitude, longitude))
    data["lat"] = latitude
    data["lon"] = longitude
    data["beaconKey"] = BEACONID
    try:
        r = requests.post(urljoin(URL,SENDPOS), data=json.dumps(data), headers=HEADERS)   
    except:
        logging.exception("error in sending location")
    print "return message of send_location: %s, %s" % (r.status if hasattr(r,"status") else "status N.A", r.text)
    logging.info("return message of send_location: %s, %s" % (r.status if hasattr(r,"status") else "status N.A", r.text))
    
def main():

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)
    
    try: 
        logger = init_logger(LOGPATH)
    except:
        print "failed to init logger"
    #is_beacon = False
    #send_location()
    try:
        print "calibrating the gps..."
        logging.info("gps calibration")
        gps_calibrate()
    except:
        logging.exception("gps calibration failed")
        print "gps calibration failed, exiting"
        sys.exit(0)
    
    tries = 0
    while True:
        try:
            cur_status = beacon_status()
            if not cur_status:
                logging.info("No beacon found, becoming one...")
                print "No beacon found, becoming one..."
                r = become_beacon(BEACONID,NAME)
            else:
                # if the beacon is not me, wait 20 sec
                if cur_status["beaconId"] != BEACONID:
                    logging.info("beacon is already taken by: %s, sleeping for 20 sec" % cur_status["beaconId"])
                    print "somone else is the beacon, waiting 20 sec"
                    time.sleep(20)
                    # to decide
                    continue
                logging.info("I'm already the beacon, continuing")
                print "I'm already the beacon, continuing"
            print "sending location"
            logging.info("trying to send location")
            send_location()
            
            logging.info("sleeping for 7 seconds")
            # TODO: change this number to CONST and format it into the logging message above
            time.sleep(7)
        except Exception, e:
            print e
            tries += 1
            logging.exception("got exception in main for the %d time" % tries)
            if tries == 4:
                print "maximum failed tries achived, exiting..."
                logging.error("maximum failed tries achived")
                logging.info("removing beacon")
                remove_beacon(BEACONID)
                logging.info("exiting")
                sys.exit(0)
            
                
            
        
if __name__ == "__main__":
        main()

     
        

#pdb.set_trace()
#t = send_location()
# get status to understand if beacon is available 
#x = become_beacon(BEACONID, NAME)
# check if I'm the beacon
#y = get_status()




#z = remove_beacon(BEACONID) 
#r = requests.post(url, data=json.dumps(dict), headers=headers)

#params = urllib.urlencode()
#conn.request("POST", "/becomeBeacon")
#conn.request("GET", "/beaconStatus")
#r1 = conn.getresponse()
#print r1.status, r1.reason

