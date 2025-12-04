import numpy as np

import cv2

import time

import picamera2
from picamera2 import Picamera2

import RPi.GPIO as GPIO
from threading import Thread, Lock, Condition

GPIO_LEFT = 16
GPIO_RIGHT = 26

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(GPIO_LEFT, GPIO.OUT)
GPIO.setup(GPIO_RIGHT, GPIO.OUT)

GPIO.output(GPIO_LEFT, GPIO.LOW)
GPIO.output(GPIO_RIGHT, GPIO.LOW)

pwmLeft = GPIO.PWM(GPIO_LEFT, 50)
pwmRight = GPIO.PWM(GPIO_RIGHT, 50)

pwmLeft.start(0)
pwmRight.start(0)

for freq in range(50,1000, 50):
    pwmLeft.ChangeFrequency(freq)
    print(f"Testing: {freq}\n")
    print(f"[", end='')
    for dc in range(0, 101, 1):
        print(".", end='')
        pwmLeft.ChangeDutyCycle(dc)
        #pwmRight.ChangeDutyCycle(dc)
        time.sleep(.1)
    print(f"]\n")

# for dc in range(100, -1, -1):
#     pwmLeft.ChangeDutyCycle(dc)
#     #pwmRight.ChangeDutyCycle(dc)
#     time.sleep(.1)


#pwmRight.stop()
GPIO.cleanup()