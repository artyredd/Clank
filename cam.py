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
camera.configure(camera.create_video_configuration(main={"format": 'XRGB8888',
                                                           "size": (640, 480)}))
camera.start()

# allow the camera to warmup
time.sleep(1)

faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

current_PAN = 90

current_TILT = 20

GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_LEFT, GPIO.OUT)
GPIO.setup(GPIO_RIGHT, GPIO.OUT)

while True:
    frame = camera.capture_array()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = faceCascade.detectMultiScale(

        gray,

        scaleFactor=1.2,

        minNeighbors=5,

        minSize=(20, 20)

    )

    for (x, y, w, h) in faces:

        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

        if x > 240:

            #pwm.setRotationAngle(1, current_PAN)  # PAN
            GPIO.output(GPIO_LEFT,GPIO.HIGH)
            GPIO.output(GPIO_RIGHT, GPIO.LOW)
            current_PAN -= 2

        elif x < 220:
            #pwm.setRotationAngle(1, current_PAN)  # PAN
            GPIO.output(GPIO_RIGHT,GPIO.HIGH)
            GPIO.output(GPIO_LEFT,GPIO.LOW)
            current_PAN += 2

        if y > 140:

            #pwm.setRotationAngle(0, current_TILT)  # TILT

            current_TILT += 2

        elif y < 60:

            #pwm.setRotationAngle(0, current_TILT)  # TILT

            current_TILT -= 2

    cv2.imshow('f', frame)
    
    if cv2.waitKey(30) & 0xFF == 27:  # Press ‘ESC’ to exit
        break

cap.release()

cv2.destroyAllWindows()
