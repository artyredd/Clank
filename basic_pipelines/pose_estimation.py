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
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import SOURCE_PIPELINE
from hailo_apps.hailo_app_python.apps.pose_estimation.pose_estimation_pipeline import GStreamerPoseEstimationApp
from hailo_apps.hailo_app_python.core.common.core import get_default_parser

import RPi.GPIO as GPIO
from threading import Thread, Lock, Condition
import time

PIN_LEFT = 16
PIN_RIGHT = 13
PWM_FREQ = 200
PWM_DUTY = 10
DETECTION_MARGIN = 45
PREVIOUS_ID = -1
CURRENT_ID = -1
TIME_AT_LAST_ID_CHANGE = 0
MAX_TIME_PER_ID = 10
ID_IN_LIST = False
PWM_RIGHT = None
PWM_LEFT = None

LAST_DUTY = 10

def stop_motor():
    global LAST_DUTY
    PWM_LEFT.ChangeDutyCycle(0)
    PWM_RIGHT.ChangeDutyCycle(0)
    LAST_DUTY = PWM_DUTY

def turn_left():
    global LAST_DUTY
    LAST_DUTY += 1
    PWM_LEFT.ChangeDutyCycle(PWM_DUTY)
    PWM_RIGHT.ChangeDutyCycle(LAST_DUTY)
def turn_right():
    global LAST_DUTY
    LAST_DUTY += 1
    PWM_LEFT.ChangeDutyCycle(0)
    PWM_RIGHT.ChangeDutyCycle(LAST_DUTY)

# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()

class MyGstreamer(GStreamerPoseEstimationApp):
    def __init__(self, arg1, arg2):
        self.batch_size = 1
        self.video_width = 1280    # Modify this value
        self.video_height = 720    # Modify this value
        self.video_format = "RGB"
        super().__init__(arg1, arg2)

    def get_pipeline_string(self):
        width = 1280
        height = 720
        framerate = 60
        return f"appsrc name=app_source is-live=true leaky-type=downstream max-buffers=3 ! videoflip name=videoflip video-direction=horiz ! video/x-raw, format=RGB, width={width}, height={height} !  queue name=source_scale_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! videoscale name=source_videoscale n-threads=2 ! queue name=source_convert_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! videoconvert n-threads=3 name=source_convert qos=false ! video/x-raw, pixel-aspect-ratio=1/1, format=RGB, width={width}, height={height} ! videorate name=source_videorate ! capsfilter name=source_fps_caps caps=\"video/x-raw, framerate={framerate}/1\"  ! queue name=inference_wrapper_input_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! hailocropper name=inference_wrapper_crop so-path=/usr/lib/aarch64-linux-gnu/hailo/tappas/post_processes/cropping_algorithms/libwhole_buffer.so function-name=create_crops use-letterbox=true resize-method=inter-area internal-offset=true hailoaggregator name=inference_wrapper_agg inference_wrapper_crop. ! queue name=inference_wrapper_bypass_q leaky=no max-size-buffers=20 max-size-bytes=0 max-size-time=0  ! inference_wrapper_agg.sink_0 inference_wrapper_crop. ! queue name=inference_scale_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! videoscale name=inference_videoscale n-threads=2 qos=false ! queue name=inference_convert_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! video/x-raw, pixel-aspect-ratio=1/1 ! videoconvert name=inference_videoconvert n-threads=2 ! queue name=inference_hailonet_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! hailonet name=inference_hailonet hef-path=/usr/local/hailo/resources/models/hailo8l/yolov8s_pose.hef batch-size=2  vdevice-group-id=1  force-writable=true  ! queue name=inference_hailofilter_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! hailofilter name=inference_hailofilter so-path=/usr/local/hailo/resources/so/libyolov8pose_postprocess.so   function-name=filter_letterbox  qos=false ! queue name=inference_output_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0   ! inference_wrapper_agg.sink_1 inference_wrapper_agg. ! queue name=inference_wrapper_output_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0   ! hailotracker name=hailo_tracker class-id=0 kalman-dist-thr=0.8 iou-thr=0.9 init-iou-thr=0.7 keep-new-frames=2 keep-tracked-frames=15 keep-lost-frames=2 keep-past-metadata=False qos=False ! queue name=hailo_tracker_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0   ! queue name=identity_callback_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! identity name=identity_callback  ! queue name=hailo_display_overlay_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! hailooverlay name=hailo_display_overlay  ! queue name=hailo_display_videoconvert_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! videoconvert name=hailo_display_videoconvert n-threads=2 qos=false ! queue name=hailo_display_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0  ! fpsdisplaysink name=hailo_display video-sink=autovideosink sync=false text-overlay=True signal-fps-measurements=true"
        
# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------

# This is the callback function that will be called when data is available from the pipeline
def app_callback(pad, info, user_data):
    
    global PREVIOUS_ID
    global CURRENT_ID
    global TIME_AT_LAST_ID_CHANGE
    global MAX_TIME_PER_ID
    global ID_IN_LIST
    global MOTOR_SPIN_LENGTH

    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()
    # Check if the buffer is valid
    if buffer is None:
        CURRENT_ID = -1
        ID_IN_LIST = False
        print("Tracking lost\n")
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

    if len(detections) == 0:
        stop_motor()

    idFound = False
    # Parse the detections
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        
        supportedTypes = ["person", "teddy bear", "animal", "dog"]
        
        timeSinceLastIdChange = time.time() - TIME_AT_LAST_ID_CHANGE

        if label in supportedTypes:
            # Get track ID
            track_id = 0
            track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            if len(track) == 1:
                track_id = track[0].get_id()
                # initialize if we haven't had a value yet
                if CURRENT_ID == -1 or ID_IN_LIST == False:
                    string_to_print += (f"Defaulting tracking to first object found\n")
                    CURRENT_ID = track_id
                    TIME_AT_LAST_ID_CHANGE = time.time()
                # check to see if the tracked object is still in the array
                if track_id == CURRENT_ID:
                    idFound = True
                # check to see if we should look at someone else
                if track_id != CURRENT_ID and timeSinceLastIdChange >= MAX_TIME_PER_ID:
                    string_to_print += (f"Looked too long at {CURRENT_ID} looking at {track_id} instead\n")
                    CURRENT_ID = track_id
                    TIME_AT_LAST_ID_CHANGE = time.time()
                    

            string_to_print += (f"Detection: ID: {track_id} Label: {label} Confidence: {confidence:.2f}\n")

            # Pose estimation landmarks from detection (if available)
            landmarks = detection.get_objects_typed(hailo.HAILO_LANDMARKS)

            # only do stuff if the person we're supposed to be tracking
            # is the same person we were looking at last time
            if len(landmarks) != 0 and CURRENT_ID == track_id:
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
                #cv2.circle(frame, (centerX, centerY), 5, (0, 255, 0), -1)
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
                    
    ID_IN_LIST = idFound

    if user_data.use_frame:
        # Convert the frame to BGR
        #frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)

    #print(string_to_print)
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
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_LEFT, GPIO.OUT)
        GPIO.setup(PIN_RIGHT, GPIO.OUT)

        GPIO.output(PIN_LEFT, GPIO.LOW)
        GPIO.output(PIN_RIGHT, GPIO.LOW)

        
        PWM_LEFT = GPIO.PWM(PIN_LEFT, PWM_FREQ)
        PWM_RIGHT = GPIO.PWM(PIN_RIGHT, PWM_FREQ)
        PWM_LEFT.start(0)
        PWM_RIGHT.start(0)

        # Create parser with default options
        parser = get_default_parser()

        # Set default frame rate for better performance
        parser.set_defaults(frame_rate=60)

        project_root = Path(__file__).resolve().parent.parent
        env_file     = project_root / ".env"
        env_path_str = str(env_file)
        os.environ["HAILO_ENV_FILE"] = env_path_str
        # Create an instance of the user app callback class
        user_data = user_app_callback_class()
        
        app = MyGstreamer(app_callback, user_data)
        app.run()
    except KeyboardInterrupt:
        stop_motor()
    except:
        stop_motor()