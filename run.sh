#!/bin/bash

echo "Starting"
cd /home/arty/hailo-rpi5-examples
. setup_env.sh
python3 /home/arty/hailo-rpi5-examples/basic_pipelines/pose_estimation.py --input rpi --video-width 640 --video-height 480