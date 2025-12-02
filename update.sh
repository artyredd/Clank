#!/bin/bash

git pull
cp -r basic_pipelines/. ../hailo-rpi5-examples/basic_pipelines/ 
/usr/bin/lxterminal -e /home/arty/Clank/startup.sh