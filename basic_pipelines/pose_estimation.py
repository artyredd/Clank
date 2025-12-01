from pathlib import Path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import numpy as np
import cv2
import hailo

from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.apps.pose_estimation.pose_estimation_pipeline import GStreamerPoseEstimationApp

import RPi.GPIO as GPIO
from threading import Thread, Lock, Condition

PIN_LEFT = 16
PIN_RIGHT = 23
DETECTION_MARGIN = 100

def user_Main():
    print("Starting GPIO thread\n")
    while(True):
          x = 1
          
# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()

# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------

def stop_motor():
    GPIO.output(PIN_LEFT, GPIO.LOW)
    GPIO.output(PIN_RIGHT, GPIO.LOW)
def turn_left():
    GPIO.output(PIN_LEFT, GPIO.HIGH)
    GPIO.output(PIN_RIGHT, GPIO.LOW)
def turn_right():
    GPIO.output(PIN_LEFT, GPIO.LOW)
    GPIO.output(PIN_RIGHT, GPIO.HIGH)

# This is the callback function that will be called when data is available from the pipeline
def app_callback(pad, info, user_data):
    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()
    # Check if the buffer is valid
    if buffer is None:
        stop_motor()
        return Gst.PadProbeReturn.OK

    # Using the user_data to count the number of frames
    user_data.increment()
    string_to_print = f"Frame count: {user_data.get_count()}\n"

    # Get the caps from the pad
    format, width, height = get_caps_from_pad(pad)

    # If the user_data.use_frame is set to True, we can get the video frame from the buffer
    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        # Get video frame
        frame = get_numpy_from_buffer(buffer, format, width, height)

    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # Get the keypoints
    keypoints = get_keypoints()

    if len(detections) is 0:
        stop_motor()

    # Parse the detections
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        
        supportedTypes = ["person", "teddy bear", "animal", "dog"]
        
        if label in supportedTypes:
            # Get track ID
            track_id = 0
            track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            if len(track) == 1:
                track_id = track[0].get_id()
            string_to_print += (f"Detection: ID: {track_id} Label: {label} Confidence: {confidence:.2f}\n")

            # Pose estimation landmarks from detection (if available)
            landmarks = detection.get_objects_typed(hailo.HAILO_LANDMARKS)
            if len(landmarks) != 0:
                points = landmarks[0].get_points()
                leftShoulderIndex = keypoints["left_shoulder"]
                rightShoulderIndex = keypoints["right_shoulder"]
                leftShoulderPoint = points[leftShoulderIndex]
                rightShoulderPoint = points[rightShoulderIndex]
                leftX = int((leftShoulderPoint.x() * bbox.width() + bbox.xmin()) * width)
                leftY = int((leftShoulderPoint.y() * bbox.height() + bbox.ymin()) * height)
                rightX = int((rightShoulderPoint.x() * bbox.width() + bbox.xmin()) * width)
                rightY = int((rightShoulderPoint.y() * bbox.height() + bbox.ymin()) * height)
                centerX = int((leftX+rightX)/2)
                centerY = int((leftY+rightY)/2)
                string_to_print += f"Center: x: {centerX:.2f} y: {centerY:.2f}\n"
                cv2.circle(frame, (centerX, centerY), 5, (0, 255, 0), -1)
                global DETECTION_MARGIN
                centerScreen = int(width/2)
                if centerX < (centerScreen - DETECTION_MARGIN):
                    turn_left()
                    string_to_print += "Left\n"
                elif centerX > (centerScreen + DETECTION_MARGIN):
                    turn_right()
                    string_to_print += "Right\n"
                else:
                    stop_motor()
                    string_to_print += "Center\n"
                    

    if user_data.use_frame:
        # Convert the frame to BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)

    print(string_to_print)
    return Gst.PadProbeReturn.OK

# This function can be used to get the COCO keypoints coorespondence map
def get_keypoints():
    """Get the COCO keypoints and their left/right flip coorespondence map."""
    keypoints = {
        'nose': 0,
        'left_eye': 1,
        'right_eye': 2,
        'left_ear': 3,
        'right_ear': 4,
        'left_shoulder': 5,
        'right_shoulder': 6,
        'left_elbow': 7,
        'right_elbow': 8,
        'left_wrist': 9,
        'right_wrist': 10,
        'left_hip': 11,
        'right_hip': 12,
        'left_knee': 13,
        'right_knee': 14,
        'left_ankle': 15,
        'right_ankle': 16,
    }

    return keypoints

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_LEFT, GPIO.OUT)
    GPIO.setup(PIN_RIGHT, GPIO.OUT)

    GPIO.output(PIN_LEFT, GPIO.LOW)
    GPIO.output(PIN_RIGHT, GPIO.LOW)
    project_root = Path(__file__).resolve().parent.parent
    env_file     = project_root / ".env"
    env_path_str = str(env_file)
    os.environ["HAILO_ENV_FILE"] = env_path_str
    # Create an instance of the user app callback class
    user_data = user_app_callback_class()
    app = GStreamerPoseEstimationApp(app_callback, user_data)
    app.run()
