import numpy as np

import cv2

import time

import picamera2
from picamera2 import Picamera2

import RPi.GPIO as GPIO

GPIO_LEFT = 12
GPIO_RIGHT = 13

camera = Picamera2()
camera.resolution = (640, 480)
camera.framerate = 60
config = camera.create_video_configuration(main={"format": 'XRGB8888',
                                                           "size": (640, 480)}, controls={"FrameDurationLimits": (0, 16666)})
camera.configure(config)
camera.start()

# allow the camera to warmup
time.sleep(1)

faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_LEFT, GPIO.OUT)
GPIO.setup(GPIO_RIGHT, GPIO.OUT)

t = time.time()
deltaTime = 0
averageTime = 0
while True:
    newTime = time.time()
    deltaTime = newTime - t
    averageTime = (averageTime + deltaTime)/2
    t = newTime
    print("FPS=" + str(1/deltaTime) + " AVG=" + str(1/averageTime))

    frame = camera.capture_array()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = faceCascade.detectMultiScale(

        gray,

        scaleFactor=1.2,

        minNeighbors=5,

        minSize=(20, 20)

    )

    for (x, y, w, h) in faces:

        #cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        #print("Face:" + str(x) + "," + str(y) + "\n")

        if x > 240:
            print("Left")
            GPIO.output(GPIO_LEFT,GPIO.HIGH)
            GPIO.output(GPIO_RIGHT, GPIO.LOW)

        elif x < 220:
            print("Right")
            GPIO.output(GPIO_RIGHT,GPIO.HIGH)
            GPIO.output(GPIO_LEFT,GPIO.LOW)