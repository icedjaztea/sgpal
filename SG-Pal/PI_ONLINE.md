# Pi: hosted SG Pal on the existing SPI screen

This replaces the independent `app.py --pi` runtime for online play. It does not run FastAPI, a local game database or an AI key on the Pi. Production remains https://sgpal.onrender.com/?kiosk=1 . Recovery accounts and friends share the hosted backend with laptops/phones.

## Observed hardware

Pi 3B+ / Debian 13 (64-bit), no graphical desktop or browser initially. HDMI disconnected. The teammate's `/home/jaz/sgpal-hardware-tests/screen_test.py` drives a raw SPI 240×320 controller as a 320×240 landscape panel: SPI0 CE0, 8 MHz, DC BCM25, reset27, backlight18, ROTATE_90 and RGB565. The bridge reuses the repository's matching register sequence and preserves the original test file and boot configuration. `rpicam-hello --list-cameras` detects OV5647 CSI. Rotary wiring still requires confirmation on the actual device before enabling controls.

A normal desktop Chromium window cannot appear on this raw panel. The bridge uses sandboxed headless Chromium, renders the real production page at 320×240, and transfers frames to the existing SPI driver. It sends normal arrow/Enter/Escape keys through the browser's loopback-only debugging interface. No browser security is disabled and no camera HTTP endpoint is exposed. At Pi 3 speeds this is a low-frame-rate UI, not a video stream.

## Manual operation first

Install only the missing browser/transport dependencies:

```sh
sudo apt-get update
sudo apt-get install -y chromium python3-websocket
cd ~/sgpal-online/SG-Pal
GPIOZERO_PIN_FACTORY=lgpio python3 pi_online.py run
```

Do not run `screen_test.py`, old `app.py --pi`, GPIO tests or another camera process alongside the bridge. Ctrl+C closes only this bridge and its own Chromium child. A process lock prevents duplicate bridges.

After confirming the physical rotary pins, create `~/.config/sgpal-online.json` (outside Git) with the **actual** BCM `rotary_a`, `rotary_b`, `rotary_press`; include `back_button` and `scan_button` only if those switches are physically wired. Then run with `--controls`. The existing gpiozero quadrature decoder is reused with 3 ms rotation and 80 ms press debounce. Check five detents produce five selections. If reversed, swap A/B in this private configuration, not the wires while powered. Back is also an explicit game action; no long press is needed.

Remote keyboard equivalents, without taking GPIO:

```sh
python3 pi_online.py key ArrowRight
python3 pi_online.py key Enter
python3 pi_online.py key Escape
python3 pi_online.py status
```

## Restore privately

With the bridge running, use an interactive SSH Terminal:

```sh
cd ~/sgpal-online/SG-Pal
python3 pi_online.py restore
```

Type the private recovery code at the hidden prompt, never as a command argument, environment variable, chat message or URL. The helper invokes the same HTTPS recovery endpoint in the authenticated browser, with CSRF/owner checks. Unsaved guest progress blocks switching: save that guest or cancel. Public friend codes cannot restore. Browser session files live at `~/.local/share/sgpal-online/chromium` with private permissions, outside Git. Do not copy or commit that profile. The code itself is not saved by the helper. Account is also reachable from the compact welcome screen and Settings → save status.

## CSI photo

Only after confirming the camera is free, add `--camera`. In Scan, choose **Upload**: the Pi intercepts that deliberate file-selection action, captures once with `rpicam-still`, and passes the temporary private JPEG into the existing file input. The normal photo preview → Analyse → confirmation flow runs on the hosted game. There is no success or reward on capture. Temporary files are deleted after the page reads them. This CSI adapter uses Upload because CSI/libcamera is not a normal browser webcam. Laptop/phone uploads remain the fallback. Never run another camera capture simultaneously.

## Startup after physical checks pass

Stop the manual bridge first, then:

```sh
bash install_online_service.sh --controls --camera # omit any hardware not yet verified
sudo loginctl enable-linger "$USER"              # once, for boot without SSH
systemctl --user start sgpal-online
```

Start/stop/restart and logs:

```sh
systemctl --user start sgpal-online
systemctl --user stop sgpal-online
systemctl --user restart sgpal-online
journalctl --user -u sgpal-online -n 60 --no-pager
```

Safe update, only if this dedicated checkout is clean:

```sh
cd ~/sgpal-online
if [ -z "$(git status --porcelain)" ]; then
  git fetch origin && git merge --ff-only origin/main && systemctl --user restart sgpal-online
else
  echo 'Local changes found: preserve/review them before updating.'
fi
```

No display driver replacement, forced Git update, secret transfer, local player database or reboot is required. Physical screen orientation, each detent/press, real camera results and the user's private account restoration require on-device confirmation; remote screenshot delivery alone is not proof of those physical checks.
