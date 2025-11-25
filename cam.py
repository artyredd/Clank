import numpy as np

import cv2

import time

import picamera2

import RPi.GPIO as GPIO

GPIO_LEFT = 12
GPIO_RIGHT = 13

# from PCA9685 import PCA9685

#pwm = PCA9685()

#pwm.setPWMFreq(50)

faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(0)

cap.set(3, 640)  # Set Width

cap.set(4, 480)  # Set Height

current_PAN = 90

current_TILT = 20

GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_LEFT, GPIO.OUT)
GPIO.setup(GPIO_RIGHT, GPIO.OUT)

#pwm.setRotationAngle(1, 180)  # PAN

#pwm.setRotationAngle(0, current_TILT)  # TILT

while True:

    ret, img = cap.read()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

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

    cv2.imshow("Face Tracking", img)

    if cv2.waitKey(30) & 0xFF == 27:  # Press ‘ESC’ to exit

        break

cap.release()

cv2.destroyAllWindows()
