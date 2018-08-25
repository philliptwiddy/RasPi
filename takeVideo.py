import time
from picamera import PiCamera
from datetime import datetime


def getDateTime():
    dt = datetime.now().strftime("%Y-%m-%d,%H:%M:%S")
    return dt


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


def main():
    takeVideo(2)


if __name__ == '__main__':
    main()
