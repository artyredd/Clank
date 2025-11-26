import numpy as np

import cv2

import time

import picamera2
from picamera2 import Picamera2

import RPi.GPIO as GPIO
from threading import Thread

GPIO_LEFT = 16
GPIO_RIGHT = 26

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

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_LEFT, GPIO.OUT)
GPIO.setup(GPIO_RIGHT, GPIO.OUT)

GPIO.output(GPIO_LEFT, GPIO.LOW)
GPIO.output(GPIO_RIGHT, GPIO.LOW)

t = time.time()
deltaTime = 0
averageTime = 0

global frameBuffer
global frameBufferHasData
global backupFrameBuffer
global backupFrameBufferHasData
global mainReadingFrameBuffer
global mainReadingBackupFrameBuffer
global workerWritingFrameBuffer
global workerWritingBackupFrameBuffer

frameBuffer = []
frameBufferHasData = False
backupFrameBuffer = []
backupFrameBufferHasData = False
mainReadingFrameBuffer = False
mainReadingBackupFrameBuffer = False
workerWritingFrameBuffer = False
workerWritingBackupFrameBuffer = False

def BackgroundWork():
    global frameBuffer
    global frameBufferHasData
    global backupFrameBuffer
    global backupFrameBufferHasData
    global mainReadingFrameBuffer
    global mainReadingBackupFrameBuffer
    global workerWritingFrameBuffer
    global workerWritingBackupFrameBuffer
    
    # Read the next frame from the stream in a different thread
    print("Starting Worker Thread")
    while True:
        if mainReadingFrameBuffer or frameBufferHasData:
            workerWritingBackupFrameBuffer = True
            backupFrameBuffer = camera.capture_array()
            workerWritingBackupFrameBuffer = False
            backupFrameBufferHasData = True
        else:
            workerWritingFrameBuffer = True
            frameBuffer = camera.capture_array()
            workerWritingFrameBuffer = False
            frameBufferHasData = True
            
        time.sleep(.001)

thread = Thread(target=BackgroundWork, args=())
thread.daemon = True
thread.start()

faces = []
faceDataAvailable = False

def MLWorker(gray):
    global faceDataAvailable
    global faces
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(20, 20)
    )
    faceDataAvailable = True

print("Starting Main Thread")
while True:
    if faceDataAvailable == True:
        newTime = time.time()
        deltaTime = newTime - t
        averageTime = (averageTime + deltaTime)/2
        t = newTime
        print("FPS=" + str(1/deltaTime) + " AVG=" + str(1/averageTime))

        for (x, y, w, h) in faces:
            cv2.rectangle(gray, (x, y), (x + w, y + h), (255, 0, 0), 2)

            if x > 240:
                print("Left")
                GPIO.output(GPIO_LEFT, GPIO.HIGH)
                GPIO.output(GPIO_RIGHT, GPIO.LOW)

            elif x < 220:
                print("Right")
                GPIO.output(GPIO_RIGHT,GPIO.HIGH)
                GPIO.output(GPIO_LEFT,GPIO.LOW)

    if frameBufferHasData == False and backupFrameBufferHasData == False:
        time.sleep(0.001)
        continue

    gray = []
    if frameBufferHasData and workerWritingFrameBuffer == False:
        mainReadingFrameBuffer = True
        gray = cv2.cvtColor(frameBuffer, cv2.COLOR_BGR2GRAY)
        mainReadingFrameBuffer = False
        frameBufferHasData = False
    elif backupFrameBufferHasData and workerWritingBackupFrameBuffer == False:
        mainReadingBackupFrameBuffer = True
        gray = cv2.cvtColor(backupFrameBuffer, cv2.COLOR_BGR2GRAY)
        mainReadingBackupFrameBuffer = False
        backupFrameBufferHasData = False

    Thread(target=MLWorker, args=(gray)).run()