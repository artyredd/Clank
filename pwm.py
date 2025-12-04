import numpy as np

import cv2

import time

import picamera2
from picamera2 import Picamera2

import RPi.GPIO as GPIO
from threading import Thread, Lock, Condition

GPIO_LEFT = 16
GPIO_RIGHT = 13

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(GPIO_LEFT, GPIO.OUT)
GPIO.setup(GPIO_RIGHT, GPIO.OUT)

GPIO.output(GPIO_LEFT, GPIO.LOW)
GPIO.output(GPIO_RIGHT, GPIO.LOW)

pwmLeft = GPIO.PWM(GPIO_LEFT, 200)
pwmRight = GPIO.PWM(GPIO_RIGHT, 200)

pwmLeft.start(0)
pwmRight.start(0)

# for freq in range(200,201, 1):
#     pwmLeft.ChangeFrequency(freq)
#     print(f"{freq}Hz [", end='', flush=True)
#     for dc in range(0, 101, 1):
#         print(".", end='', flush=True)
#         pwmLeft.ChangeDutyCycle(dc)
#         #pwmRight.ChangeDutyCycle(dc)
#         time.sleep(.025)
#     print(f"]\n")

# for dc in range(100, -1, -1):
#     pwmLeft.ChangeDutyCycle(dc)
#     #pwmRight.ChangeDutyCycle(dc)
#     time.sleep(.1)

try:
    while True:
        for dc in range(0, 101, 1):
                print(".", end='', flush=True)
                pwmLeft.ChangeDutyCycle(dc)
                #pwmRight.ChangeDutyCycle(dc)
                time.sleep(.025)

        pwmLeft.ChangeDutyCycle(0)

        for dc in range(0, 101, 1):
                print(".", end='', flush=True)
                pwmRight.ChangeDutyCycle(dc)
                #pwmRight.ChangeDutyCycle(dc)
                time.sleep(.025)
                
        pwmRight.ChangeDutyCycle(0)
except:
    print("Quitting")
    pwmRight.ChangeDutyCycle(0)

    pwmRight.stop()
    pwmLeft.stop()