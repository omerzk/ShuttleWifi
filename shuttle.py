import RPi.GPIO as GPIO 
import time
import subprocess
import os
import signal
import datetime
import sys
import threading

PYTHON_PATH = "python"
SHUTTLE_LOCATION_SCRIPT = "/home/pi/locate.py"
SHUTTLE_LOCATION_CMDLINE = r"%s %s" % (PYTHON_PATH, SHUTTLE_LOCATION_SCRIPT)

START_ACTIVITY_HOURS = 0
END_ACTIVITY_HOURS = 24

GPIO.setmode(GPIO.BCM) 
GPIO.setup(18, GPIO.IN)
GPIO.setup(23, GPIO.OUT)
 
GPIO.add_event_detect(18, GPIO.RISING)  # add rising edge detection on a channel

EVENT_TIMEOUT = 1

WORKING_HOURS_ERROR = 3
LOCATE_PROCESS_ERROR = 5

               
def blinkGreenLed():
    GPIO.output(23, GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(23, GPIO.LOW)
    time.sleep(0.25)
    
def setGreenLedOn():
    GPIO.output(23, True);

def setGreenLedOff():
    GPIO.output(23, False);
    
def flashGreenLed(event, sleeptime, blinkCount):
    while not event.isSet():
        eventIsSet = event.wait(sleeptime)
        if eventIsSet:
            break
        else:

            for i in range(blinkCount):
                if event.isSet():
                    break
                blinkGreenLed()
 
    print "Event signaled"
    setGreenLedOff()

def startLocationApplication():
    # return subprocess.Popen([PYTHON_PATH, "test.py"], stdout=subprocess.PIPE, preexec_fn=os.setsid)     
    return subprocess.Popen([PYTHON_PATH, SHUTTLE_LOCATION_SCRIPT], stdout=subprocess.PIPE, preexec_fn=os.setsid) 

def stopLocationApplication(location_process):
    if location_process is None:
        print "Invalid location process"
        return None
        
    print "Killing location process" 
    os.killpg(os.getpgid(location_process.pid), signal.SIGTERM)

    print "Waiting for location process to die" 
    location_process.wait()

    print "Location process output:" 
    for line in location_process.stdout:
        print line.rstrip()
    

def SwitchOnState(): 
    print "Switch turned on" 
    try:
    
      location_process = startLocationApplication()
      if location_process:
        print "Location application started"
        
      return location_process
      
    except Exception:
    
        print "Failed to start location application"
        return None
    
 
def SwitchOffState(location_process): 
    print "Switch turned off" 
    stopLocationApplication(location_process)

def InWorkingHours():
    now = datetime.datetime.now()
    return now.hour > START_ACTIVITY_HOURS and now.hour < END_ACTIVITY_HOURS
    
location_process = None
thread = None


try:
    setGreenLedOff()
    event = threading.Event()
    print "Waiting for switch toggle" 
    while True:
        
        # Test that we are still in working hours
        if not InWorkingHours():
            if GPIO.input(18) == 1 and not thread:
                print "Not in working hours"
                thread = threading.Thread(name='non-block', target=flashGreenLed, args=(event, EVENT_TIMEOUT, WORKING_HOURS_ERROR))
                event.clear()
                thread.start()  
                
            if GPIO.input(18) == 0 and thread:
                event.set()   
                thread.join()
                thread = None  
            continue
                
                        
        # Pulling on events for Pin 18
        if GPIO.event_detected(18):
            print "Detected event on switch"
            # Event - Switch on     
            if GPIO.input(18) == 1:
                print "Switch is on"
                if location_process is None:
                    location_process = SwitchOnState()
                    if not location_process:
                        thread = threading.Thread(name='non-block', target=flashGreenLed, args=(event, EVENT_TIMEOUT, LOCATE_PROCESS_ERROR))
                        event.clear()
                        thread.start()                        
                    else:
                        setGreenLedOn()
                else:
                    continue
            
            # Event - Switch 0ff
            elif GPIO.input(18) == 0:
                print "Switch is off"
                if location_process is not None:
                    SwitchOffState(location_process)                
                    location_process = None
                    
                if thread and not event.isSet():
                    event.set()   
                    thread.join()
                    thread = None  

                setGreenLedOff()
            else:
                print('Invalid switch state')
            
        time.sleep(1)

except KeyboardInterrupt: 
  if location_process is not None:
    stopLocationApplication(location_process)
GPIO.cleanup()      # clean up GPIO on normal exit 
