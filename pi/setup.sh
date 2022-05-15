#!/bin/bash

sudo apt update

sudo apt install cmake build-essential pkg-config -y

sudo apt-get install espeak -y
sudo apt install python3-pip -y
sudo apt install libopencv-dev python3-opencv -y
sudo apt-get install libatlas-base-dev -y

pip3 install -r requirements.txt

python3 main.py
