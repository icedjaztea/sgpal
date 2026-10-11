#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
flags=''
for arg in "$@"; do
  case "$arg" in --controls|--camera|--touch) flags+=" $arg";; *) echo 'Use only verified --controls, --camera or --touch'; exit 2;; esac
done
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/sgpal-online.service" <<EOF
[Unit]
Description=SG Pal hosted game on the verified SPI LCD
StartLimitIntervalSec=60
StartLimitBurst=3
[Service]
Type=simple
WorkingDirectory=$PWD
Environment=GPIOZERO_PIN_FACTORY=lgpio
ExecStart=/usr/bin/python3 "$PWD/pi_online.py" run$flags
Restart=on-failure
RestartSec=5
TimeoutStopSec=40
UMask=0077
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable sgpal-online.service
printf '%s\n' 'Installed, not started. Stop any manual bridge before: systemctl --user start sgpal-online'
printf '%s\n' 'For boot without SSH login, run once: sudo loginctl enable-linger "$USER"'
