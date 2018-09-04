import os
import time
from picamera import PiCamera
from datetime import datetime, timedelta
import tweepy
import json
from random import choice
import RPi.GPIO as GPIO
#import requests ##### THINK THIS IS FOR SENDING TEXTS?

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


def getDateTime():
    dt = datetime.now().strftime("%Y-%m-%d,%H:%M:%S")
    return dt


def takePhoto():
    camera = PiCamera()
    camera.rotation = 180
    directory = "/home/pi/motion/"
    dateTime = getDateTime()
    filename = "motion-{}.png".format(str(dateTime))
    camera.capture('{}{}'.format(directory, filename))
    camera.close()
    return filename


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
    return filename


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
        "Watch out, dodgy geezer about!",
        "Motion detected!",
        "Humphry's about!",
        "Oi, oi!",
        "Don't steal my security bot!"
    ]

    my_phrase = choice(phrases)

    twitter.update_with_media('/home/pi/motion/{}'.format(mediaName), '{}'.format(my_phrase))


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
REDLEDONTIME = 5 # Time (seconds) for red light to show when motion is detected
SCANFREQ = 5 # Time (seconds) between checks for motion

def main():
    # Set up pinPIR as input
    GPIO.setup(pinPIR, GPIO.IN)

    try:
        # Turn light off to start
        lightStatus = lightOff()
        # Set current time as time for earliest recording
        earliestCamera = datetime.now()
        # Set the time that red LED will turn off
        redLEDOnUntil = datetime.now()
        # Set the time that the light will turn off
        lightOnUntil = datetime.now()
        print("Waiting for PIR to settle...")
        # Loop until PIR output is 0
        while GPIO.input(pinPIR) ==1:
            currentMotion = 0

        print("...Ready")
        #Loop until user quits with CTRL-C
        while True:
            # Read PIR state
            currentMotion = GPIO.input(pinPIR)
            # If the PIR is triggered
            if currentMotion == 1:
                lastDetectionTime = datetime.now()
                print("motion detected")
                redLEDOn()
                redLEDOnUntil = datetime.now() + timedelta(seconds=REDLEDONTIME)
                print("last detection time = {}".format(lastDetectionTime.strftime("%H:%M:%S")))
                lightOnUntil = lastDetectionTime + timedelta(seconds=MINCAMERADELAY)
                print("light stays on until {}".format(lightOnUntil.strftime("%H:%M:%S")))
                # Detect current light level
                lightLevel = readLDR()
                print("light reading is {}".format(lightLevel))
                # If current light level above threshold
                if lightLevel > LIGHTONTHRESHOLD:
                    if lightStatus == 0:
                        blueLEDOn()
                        print("blue light on")
                        lightStatus = lightOn()

                if datetime.now() > earliestCamera:
                    filename = takePhoto() #Video(VIDEODURATION)
                    tweet(filename)
                    earliestCamera += timedelta(seconds=MINCAMERADELAY)

            if datetime.now() > redLEDOnUntil:
                redLEDOff()
                
            if datetime.now() > lightOnUntill:
                if lightStatus == 1:
                    lightStatus = lightOff()
            time.sleep(SCANFREQ)

if __name__ == '__main__':
    main()