import time
from picamera import PiCamera
from datetime import datetime


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


def main():
    takePhoto()


if __name__ == '__main__':
    main()
