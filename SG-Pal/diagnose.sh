#!/usr/bin/env bash
# Read-only diagnostics; does not print Wi-Fi passwords or API keys.
printf '\nMODEL\n'
cat /proc/device-tree/model
printf '\nOS\n'
cat /etc/os-release
printf '\nNETWORK\n'
hostname -I
nmcli -t -f DEVICE,STATE device status
printf '\nPOWER FLAGS\n'
vcgencmd get_throttled
printf '\nSPI\n'
ls /dev/spidev* 2>/dev/null
printf '\nCAMERA\n'
rpicam-hello --list-cameras
