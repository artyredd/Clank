#!/bin/bash

sudo apt-get update
sudo apt -y full-upgrade
sudo apt -y install firefox
sudo apt -y install git
sudo apt -y install gh
sudo apt -y install ripgrep
sudo apt -y install pip
sudo apt -y install pipx
echo "GitHub Token: is in drive/backup/passwords/github clank key"
sudo gh auth login
echo enable pcie3, and auto-login
sudo raspi-config
echo did u enable pcie3, and auto-login?
sudo reboot

# reboot
sudo apt update && sudo apt full-upgrade
sudo rpi-eeprom-update
sudo rpi-eeprom-update -a
sudo reboot

# reboot
sudo apt -y install dkms
sudo apt -y install hailo-all
sudo reboot

# reboot
sudo apt update && sudo apt install rpicam-apps
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
git checkout dev
git pull
# change version number to main on second line
echo "change version number to main on second line"
sudo nano /config/config.yaml
sudo ./install.sh

cd ~
sudo git clone https://github.com/artyredd/Clank.git
sudo chown -R arty Clank
sudo chmod 777 Clank
sudo cp -r /home/arty/Clank/. /home/arty/hailo-rpi5-examples
cd Clank
sudo chmod +x run.sh
sudo chmod +x startup.sh

cd ~
# add /usr/bin/lxterminal -e /home/arty/Clank/startup.sh to end of file
sudo nano /etc/xdg/labwc/autostart

#reboot

#(git add . && git commit -m"PC->RPI" && git push) | (ssh arty@192.168.0.154 "cd /home/arty/Clank && git pull && sudo reboot")