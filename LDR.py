import time, RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pinLDR = 27 # set a value for the LDR GPIO pin

def readLDR():
    ldrCount = 0 # Set the count to zero
    GPIO.setup(pinLDR, GPIO.OUT)
    GPIO.output(pinLDR, GPIO.LOW)
    time.sleep(0.1)  # Drains all charge from the capacitor
    GPIO.setup(pinLDR, GPIO.IN) # Set the LDR pin to be input, determining if voltage across capacitor is high (>~1.4V) or low
    # Whilethe input pin read Low, count
    while GPIO.input(pinLDR) == GPIO.LOW:
        ldrCount += 1 # Add one to the counter
    return ldrCount

while True:
    print(readLDR())
    time.sleep(1) # Wait for one second