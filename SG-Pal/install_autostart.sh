#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
project_dir="$(pwd)"
project_user="$(id -un)"
if [[ "$project_dir" == *" "* ]] || [[ "$project_dir" == *"%"* ]]; then echo 'Use a project folder with no spaces or percent signs.'; exit 1; fi
if [ ! -x "$project_dir/.venv/bin/python" ]; then echo 'Run install_pi.sh first.'; exit 1; fi
sudo tee /etc/systemd/system/sgpal.service >/dev/null <<EOF
[Unit]
Description=SG Pal cultural companion
After=network.target
[Service]
Type=simple
User=$project_user
WorkingDirectory=$project_dir
Environment=GPIOZERO_PIN_FACTORY=lgpio
ExecStart=$project_dir/.venv/bin/python $project_dir/app.py --pi
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now sgpal.service
echo 'Autostart enabled. Check: sudo systemctl status sgpal --no-pager'
