import os
import time
from picamera import PiCamera
from datetime import datetime
import tweepy, json
from random import choice


#import glob
# import pymysql
import RPi.GPIO as GPIO
#from time import strftime
#import send_email_breech as send
import requests

#os.system('modprobe w1-gpio')
#os.system('modprobe w1-therm')
#temp_sensor = '/sys/bus/w1/devices/28-0516a4c767ff/w1_slave'
#ldr_pin = 27 # Light-Dependent Resistor (LDR)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# variables for MySQL
#db = pymysql.connect(host='localhost',user='monitor',password='password',db='temp_database')
#cur = db.cursor()

# variables for temperature comparison and sending emails when thresholds are breeched
#high = 20
#veryhigh = 25
#low = 10
#verylow = 5
#freezing = 0
#heateron = 15

def getDateTime():
    dt = datetime.now().strftime("%Y-%m-%d,%H:%M:%S")
    return dt


def takePhoto():
    camera = PiCamera()
    directory = "/home/pi/motion/"
    dateTime = getDateTime()
    filename = "motion-{}.png".format(str(dateTime))
    camera.capture('{}{}'.format(directory, filename))
    camera.close()


def takeVideo(seconds):
    camera = PiCamera()
    directory = "/home/pi/motion/"
    dateTime = getDateTime()
    filename = "motion-{}.h264".format(str(dateTime))
    camera.resolution = (640, 480)
    camera.start_recording("{}{}".format(directory, filename))
    camera.wait_recording(seconds)
    camera.stop_recording()
    camera.close()


def lightOn():
    url = "https://eu-wap.tplinkcloud.com?token=dadc92e2-B25hib6hw7YpK1exxwa1L7l"
    payload = {
        "method":"passthrough",
        "params":{
            "deviceId":"8006DF15B34A28FD866A58D702140318198880A7",
            "requestData": "{\"system\":{\"set_relay_state\":{\"state\":1}}}"
            }
        }# state = 1 turns on the plug}
    headers = {'content-type':'application/json'}
    response = requests.post(url, headers=headers, json=payload)
    
    print()
    print(response.text)
    print()
    if response.text[:15] == '{"error_code":0':
        print("light turned on")
        lightStatus = 1
    else:
        print("light did not turn on")
        lightStatus = 0
    return lightStatus

def lightOff():
    url = "https://eu-wap.tplinkcloud.com?token=dadc92e2-B25hib6hw7YpK1exxwa1L7l"
    payload = {
        "method":"passthrough",
        "params":{
            "deviceId":"8006DF15B34A28FD866A58D702140318198880A7",
            "requestData": "{\"system\":{\"set_relay_state\":{\"state\":0}}}"
            }
        }# state = 0 turns off the plug
    headers = {'content-type':'application/json'}
    response = requests.post(url, headers=headers, json=payload)

    print()
    print(response.text)
    print()
    if response.text[:15] == '{"error_code":0':
        print("light turned off")
        blueLEDOff()
        lightStatus = 0
    else:
        print("light did not turn off")
        lightStatus = 1
    return lightStatus


def readLDR():
    ldrCount = 0 # Set the count to zero
    GPIO.setup(pinLDR, GPIO.OUT)
    GPIO.output(pinLDR, GPIO.LOW)
    time.sleep(0.1)  # Drains all charge from the capacitor
    GPIO.setup(pinLDR, GPIO.IN) # Set the LDR pin to be input, determining if voltage across capacitor is high (>~1.4V) or low
    # Whilethe input pin read Low, count
    while GPIO.input(pinLDR) == 0:
        ldrCount += 1 # Add one to the counter
    return ldrCount


def blueLEDOn(): # using blue LED to show user if light level means light should be on
    GPIO.setup(pinLEDBlue, GPIO.OUT)
    GPIO.output(pinLEDBlue, GPIO.HIGH)


def blueLEDOff():
    GPIO.setup(pinLEDBlue, GPIO.OUT)
    GPIO.output(pinLEDBlue, GPIO.LOW)


def redLEDOn(): # using red LED to show user if motion has been detected
    GPIO.setup(pinLEDRed, GPIO.OUT)
    GPIO.output(pinLEDRed, GPIO.HIGH)


def redLEDOff():
    GPIO.setup(pinLEDRed, GPIO.OUT)
    GPIO.output(pinLEDRed, GPIO.LOW)


def tweet(mediaName):
    with open("twitter_auth.json") as file:
        secrets = json.load(file)

    auth = tweepy.OAuthHandler(secrets["consumer_key"], secrets["consumer_secret"])
    auth.set_access_token(secrets["access_token"], secrets["access_token_secret"])

    twitter = tweepy.API(auth)

    # to send a status update
    #twitter.update_status("My first automated tweet!")

    # to send an image with a status update
    #twitter.update_with_media("/path/to/image.jpg", "your status update")

    # to create a list of phrases to send when motion is detected
    phrases = [
        "Ahoy burglar!",
        "What out, dodgy geezer about!",
        "Motion detected!",
        "Humphry's about!",
        "Oi, oi!",
        "Don't steal my security bot!"
    ]

    my_phrase = choice(phrases)

    twitter.update_with_media("/home/pi/motion/{}, {}"format(mediaName, my_phrase))


#######
homeOfficeLightToken = 'dadc92e2-B25hib6hw7YpK1exxwa1L7l'
appServerUrl = 'https://eu-wap.tplinkcloud.com'
deviceId = '8006DF15B34A28FD866A58D702140318198880A7'
lightOnTimeS = 15
pinPIR = 17 # set a pin value for the PIR
pinLDR = 27 # set a pin value for the Light Dependent Resistor
pinLEDBlue = 18 # set a pin value for the blue LED
pinLEDRed = 24 # set a pin value for the red LED
lastDetectionTime = time.time()
lightOnUntil = time.time()# lastDetectionTime + lightOnTimeS
LIGHTONTHRESHOLD = 500 # set a value above which the light should come on
currentMotion = 0 # Current status of motion detection
lightStatus = 0 # Current status of light
lightLevel = 0 # Current light level using readLRD() function
MINCAMERADELAY = 5 * 60 # Time in seconds between taking photo / video
VIDEODURATION = 3 # Duration in seconds for video recording
earliestCamera = time.time() # Earliest point next recording will take place (used to limit frequency of recording)
redLEDOnUntil = time.time()

def main():
    # Set up pinPIR as input
    GPIO.setup(pinPIR, GPIO.IN)

    try:
        # Turn light off to start
        lightStatus = lightOff()
        # Set current time as time for earliest recording
        earliestCamera = time.time()
        print("Waiting for PIR to settle...")
        # Loop until PIR output is 0
        while GPIO.input(pinPIR) ==1:
            currentMotion = 0

        print("...Ready")
        lightOnUntil = time.time()
        #Loop until user quits with CTRL-C
        while True:
            # Read PIR state
            currentMotion = GPIO.input(pinPIR)
            # If the PIR is triggered
            if currentMotion == 1:
                print("motion detected")
                redLEDOn()
                lastDetectionTime = time.time() ##### not very good around here - two variables with different time
                strfLastDetectionTime = datetime.now().strftime("%H:%M:%S")
                print("last detection time = {}".format(strfLastDetectionTime))
                lightOnUntil = lastDetectionTime + lightOnTimeS
                print("light stays on until {}".format(lightOnUntil))
                # Detect current light level
                lightLevel = readLDR()
                print("light reading is {}".format(lightLevel))
                # If current light level above threshold
                if lightLevel > LIGHTONTHRESHOLD:
                    if lightStatus == 0:
                        blueLEDOn()
                        print("blue light on")
                        lightStatus = lightOn()

                takeVideo(VIDEODURATION)
                tweet()
                
#                elif lightLevel <= LIGHTONTHRESHOLD:
#                    blueLEDOff()
                    # elif current light level above threshold
                # elif lightStatus == 1:
                # send instruction to turn off light
                    # set light status to 0

            if time.time() > lightOnUntil:
                if lightStatus == 1:
                    lightStatus = lightOff()
            time.sleep(1)
                
    #            lastDetectionTime = time.strftime("%H:%M:%S")
    #            print("...Motion Detected!")
    #            # Record previous state
    #            previousState = 1
    #        # If the PIR has returned to ready state
    #        elif currentState == 0 and previousState == 1:
    #            print("...Ready")
    #            previousState = 0
    #
    #        # Wait for 10 milliseconds
    #        time.sleep(0.01)

    except KeyboardInterrupt:
        print("Quitting...")
        lightOff()

        # Reset GPIO settings
        GPIO.cleanup()

    #def tempRead():
    #    t = open(temp_sensor, 'r')
    #    lines = t.readlines()
    #    t.close()
    #
    #    temp_output = lines[1].find('t=')
    #    if temp_output != -1:
    #        temp_string = lines[1].strip()[temp_output+2:]
    #        temp_c = float(temp_string)/1000.0
    #    return round(temp_c,1)
    #
    #while True:
    #    temp = tempRead()
    #    print(temp)
    #    datetimeWrite = (time.strftime("%Y-%m-%d ") + time.strftime("%H:%M:%S"))
    #    print(datetimeWrite)
    ##    sql = ("""INSERT INTO tempLogcron (datetime, temperature, light) VALUES (%s,%s,%s)""",(datetimeWrite,temp,light))
    ##    sql_max_id = ("""SELECT max(`id`) FROM `tempLogcron`""") #NEW
    ##    sql_temp_max_id = ("""SELECT `temperature` FROM `tempLogcron` WHERE `id` = (SELECT max(`id`) FROM `tempLogcron`)""") #NEW
    ##    sql_previous_temp_max_id = ("""SELECT `temperature` FROM `tempLogcron` WHERE `id` = (SELECT max(`id`) FROM `tempLogcron` WHERE 1)-1""") #NEW
    ##    
    #    try:
    #        date = time.strftime("%d/%m/%Y")
    #        print(date)
    #        sqldate = ("""SELECT `WFH` FROM `WFHDates` WHERE `Date`='2017-10-05'""")
    #
    #       
    #        cur.execute(sqldate)
    #        (wfh,) = cur.fetchone()
    #        print(wfh)
    #        if temp < heateron:
    #
    #        time.sleep(15)
    #
    #
    #    else:
    #        print("else")
    #        url = "https://eu-wap.tplinkcloud.com?token=dadc92e2-B1B8YgawmklZuao1HoFEfSO"
    #        payload = {
    #            "method":"passthrough",
    #            "params":{
    #                "deviceId":"8006DF15B34A28FD866A58D702140318198880A7",
    #                "requestData": "{\"system\":{\"set_relay_state\":{\"state\":0}}}"
    #                }
    #            }# state = 1 turns on the plug}
    #        headers = {'content-type':'application/json'}
    #        response = requests.post(url, headers=headers, json=payload)
    #
    #        print()
    #        print(response.text)
    #        print()
    #        if response.text[:15] == '{"error_code":0':
    #            print("light turned off")
    #        else:
    #            print("light did not turn off")
    #
    #    except:
    #        print("something failed")
    #    break

if __name__ == '__main__':
    main()
