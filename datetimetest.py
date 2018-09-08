from datetime import datetime, timedelta
from time import time, sleep

REDLEDONTIME = 2

redLEDOnTime = datetime.now()
strfRedLEDOnTime = redLEDOnTime.strftime("%H:%M:%S")
print('red LED on at {}'.format(datetime.now().strftime("%H:%M:%S")))
#print('red LED on at {}'.format(redLEDOnTime.strftime("%H:%M:%S")))
#print('red LED on at {}'.format(strfRedLEDOnTime))
redLEDOnUntil = redLEDOnTime + timedelta(seconds=REDLEDONTIME)
strfRedLEDOnUntil = redLEDOnUntil.strftime("%H:%M:%S")
print('red LED on until {}'.format(strfRedLEDOnUntil))
#strfLastDetectionTime = datetime.now().strftime("%H:%M:%S")
i = 1
while datetime.now() < redLEDOnUntil:
    sleep(0.5)
    print('waiting {} time'.format(i))
    i += 1
print('time now {}'.format(datetime.now().strftime("%H:%M:%S")))
print('quitting...')