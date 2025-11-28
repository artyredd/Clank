import numpy as np

import cv2

import time

import picamera2
from picamera2 import Picamera2

import RPi.GPIO as GPIO
from threading import Thread, Lock, Condition

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

faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_LEFT, GPIO.OUT)
GPIO.setup(GPIO_RIGHT, GPIO.OUT)

GPIO.output(GPIO_LEFT, GPIO.LOW)
GPIO.output(GPIO_RIGHT, GPIO.LOW)

t = time.time()
deltaTime = 0
averageTime = 0

frameBuffer = []
frameBufferHasData = False
backupFrameBuffer = []
backupFrameBufferHasData = False
frameBufferLock = Lock()
backupFrameBufferLock = Lock()

def BackgroundWork():
    global frameBuffer
    global backupFrameBuffer
    global frameBufferLock
    global backupFrameBufferLock
    global frameBufferHasData
    global backupFrameBufferHasData
    
    # Read the next frame from the stream in a different thread
    print("Starting Camera Worker Thread")
    while True:
        if frameBufferHasData and backupFrameBufferLock.acquire(False) :
            backupFrameBuffer = camera.capture_array()
            backupFrameBufferLock.release()
            backupFrameBufferHasData = True
        elif frameBufferLock.acquire(False):
            frameBuffer = camera.capture_array()
            frameBufferLock.release()
            frameBufferHasData = True


grayScaleBufferHasData = False
grayscaleFramebuffer = []
grayscaleFrameLock = Lock()
faces = []
facesLock = Lock()
faceDataAvailable = False

def MLWorker():
    global facesLock
    global faces
    global grayscaleFramebuffer
    global faceDataAvailable
    
    print("Started ML Worker Thread")
    while True:
        if faceDataAvailable == False and grayScaleBufferHasData:
            if facesLock.acquire():
                if grayscaleFrameLock.acquire():
                    faces = faceCascade.detectMultiScale(
                        grayscaleFramebuffer,
                        scaleFactor=1.2,
                        minNeighbors=5,
                        minSize=(20, 20)
                    )
                    facesLock.release()
                    grayscaleFrameLock.release()
                    faceDataAvailable = True


thread = Thread(target=BackgroundWork, args=())
thread.daemon = True
thread.start()

thread = Thread(target=MLWorker, args=())
thread.daemon = True
thread.start()

print("Starting Main Thread")
while True:
    if faceDataAvailable == True:
        if facesLock.acquire():
            newTime = time.time()
            deltaTime = newTime - t
            averageTime = (averageTime + deltaTime)/2
            t = newTime
            print("FPS=" + str(1/deltaTime) + " AVG=" + str(1/averageTime))

            for (x, y, w, h) in faces:
                
                if grayscaleFrameLock.acquire(False):
                    cv2.rectangle(grayscaleFramebuffer, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    grayscaleFrameLock.release()
                
                if x > 240:
                    print("Left")
                    GPIO.output(GPIO_LEFT, GPIO.HIGH)
                    GPIO.output(GPIO_RIGHT, GPIO.LOW)
                elif x < 220:
                    print("Right")
                    GPIO.output(GPIO_RIGHT,GPIO.HIGH)
                    GPIO.output(GPIO_LEFT,GPIO.LOW)
                else:
                    print("Center Or No face")
                    GPIO.output(GPIO_RIGHT,GPIO.LOW)
                    GPIO.output(GPIO_LEFT,GPIO.LOW)

            facesLock.release()
            faceDataAvailable = False

    if frameBufferHasData and frameBufferLock.acquire(False):
        grayscaleFramebuffer = cv2.cvtColor(frameBuffer, cv2.COLOR_BGR2GRAY)
        frameBufferLock.release()
        frameBufferHasData = False
        grayScaleBufferHasData = True
    elif backupFrameBufferHasData and backupFrameBufferLock.acquire(False):
        grayscaleFramebuffer = cv2.cvtColor(backupFrameBuffer, cv2.COLOR_BGR2GRAY)
        backupFrameBufferLock.release()
        backupFrameBufferHasData = False
        grayScaleBufferHasData = True