#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v raspi-config >/dev/null; then echo 'Run this on Raspberry Pi OS, not your Mac.'; exit 1; fi
sudo apt-get update
sudo apt-get install -y python3-venv python3-pil python3-numpy python3-gpiozero python3-lgpio python3-spidev python3-smbus2 rpicam-apps fonts-dejavu-core
python3 -m venv --system-site-packages .venv
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
sudo usermod -aG spi,i2c,gpio,video "$(id -un)"
echo 'Install complete. Run sudo reboot, wait, then reconnect using SSH.'
