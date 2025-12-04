#!/bin/bash

echo "Starting in 5 seconds..."
echo "[.    ]"
sleep 1
echo "[..   ]"
sleep 1
echo "[...  ]"
sleep 1
echo "[.... ]"
sleep 1
echo "[.....]"
sleep 1

cp /home/arty/Clank/basic_pipelines/pose_estimation.py /home/arty/hailo-examples/basic_pipelines/
DISPLAY=:0 /home/arty/Clank/run.sh