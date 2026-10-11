# SG Pal · Kopi Sunset browser integration

The approved 320 × 240 browser experience is now in `sgpal/web/`, served by
`sgpal/server.py` (FastAPI). The original Python/Pillow app, its scanning and
quest logic, culture catalogue, hardware adapters and tests are retained below.

## Run the new browser experience

On macOS you can double-click `Start SG Pal.command` in Finder. Keep its Terminal
window open while playing. If SG Pal is already running, the launcher opens the
kiosk URL. The local URLs require the server to be running on this Mac.

From the shared repository, create a local environment on first setup:

```bash
cd sgpal/SG-Pal
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-web.txt
SGPAL_DATA_DIR=./data/browser python -m uvicorn sgpal.server:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. The preview uses an ignored `data/browser/` save
folder. Browser acceptance tests use separate temporary folders.

For the exact handheld display, open **http://127.0.0.1:8000/?kiosk=1**.
The shared UI runs in a Pi browser, laptop browser or phone browser. Connecting
this renderer to the existing raw SPI display, GPIO and CSI camera is still
pending; the original `python app.py --pi` hardware runtime remains available.

For a phone on the same trusted LAN, replace `--host 127.0.0.1` with
`--host 0.0.0.0`, then visit `http://<computer-or-pi-IP>:8000`. All visitors to
that server share one device save. Phone camera access over ordinary LAN HTTP
may be unavailable; use the photo picker, or configure HTTPS.

Working: Merlion/Otter/Mynah adoption and saved BTO home, shared input,
photo capture/upload, real OpenAI recognition, catalogue correction/reassessment,
confirmation, saved CultureDex photos, assigned quests and Yes, I did it / Not yet answers
with exactly-once rewards. New discoveries earn 10 XP + 5 Kopi Coins; marking a
quest complete earns 25 XP + 10 coins. Completion is player-reported, with no photo
verification required. Uncertain/failed results earn nothing.

Use your existing Common Ground key. Check Settings or `/api/status` for credential
presence (this does not validate API billing/access). If missing, configure it
through the local hidden prompt, never through chat or browser code:

```bash
.venv/bin/python configure_key.py
```

The key is stored outside Git at `~/.config/sgpal/credentials.json`; requests read
it when needed, so no restart is required after configuration. Nothing creates a
new key. Click Analyse deliberately to send a photo to OpenAI. Real photos and
Singapore-time records save to the local gameplay database. Existing JSON progress
is imported once without altering it or granting retroactive coins.

A small shop, inventory and room placement now work with earned Kopi Coins.
Accounts/sync, pairing and friends remain deferred. The original
native `app.py --pi` runtime is retained; it does not yet render the new browser UI.
After migration, continue that save through FastAPI; changing its original JSON
with the old runtime creates a detected conflict rather than silently losing data.

See [KOPI_SUNSET.md](KOPI_SUNSET.md) for save compatibility, controls, validation,
architecture and remaining connections. The original hardware build instructions follow for compatibility. Both the
shared browser and native runtime now use honesty-based quest answers.

---

# SG Pal · Common Ground
## Start here — build dated 11 October 2026

A complete source package for your Raspberry Pi 3B+, Waveshare **2.8inch Capacitive Touch LCD (240×320)**, Camera Rev 1.3 and rotary controls. The interface renders at **320×240 landscape**. AI runs through your OpenAI API key named **Common Ground**, with `gpt-4.1-mini` configurable in `config.json`.

**Status:** software logic tests and rendered screen inspection completed. The integrated FastAPI flow also passed live OpenAI discovery recognition followed by self-reported quest completion using a synthetic menu and isolated test progress; see KOPI_SUNSET.md. Real-world photo accuracy, Pi GPIO, screen orientation/colours, touch, camera, audio and LED timing remain untested on your device. Your SSH connection is still unresolved. This is a build to install and test, not a claim that your hardware is already working.

### Included
- Same pixel interface on the Pi and in a Mac browser preview.
- Original animated Pocket Sprout, four home actions, XP, levels, scarf and sunhat unlocks.
- Capture a still photo → review → explicitly send to OpenAI → evidence-based cultural match.
- Ten curated cultural entries across Food, Language, Everyday life and Places.
- Saved culture log; an honesty-based quest with an explicit completion answer.
- 10 XP for each new category and 25 XP for each unique completed quest.
- Unknown/uncertain result handling; no points for low/medium-confidence classification.
- Local atomic progress saving, network/API errors, deliberate retries, no automatic paid retry loop.
- Explicit demo mode with separate saved progress; never masquerades as real recognition.
- Display, rotary/buttons, optional single-point touch, buzzer and WS2812 adapters.
- Private API key entry, diagnostics, component tests and optional boot service.

**MVP boundaries:** one creature, ten categories, still-photo review (not live viewfinder), English text, no audio speech, no accounts, no location tracking. Touch is supplementary: home/log selection and bottom-left Back; use the knob or preview controls for confirmation and paging. LED/buzzer are disabled until their electrical requirements are verified. Quests need no photos, AI verification or location proof; completion is self-reported.

## A. Try the frontend on your Mac immediately

1. Unzip `SG-Pal-Complete-Build.zip` in Downloads. The folder should be `~/Downloads/SG-Pal`.
2. Open Terminal. Run one line at a time:

```bash
cd ~/Downloads/SG-Pal
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py --demo
```

If Python is missing, install Python 3.11 or later from https://www.python.org/downloads/macos/ and reopen Terminal. No Homebrew is required.

3. Open **http://127.0.0.1:8765** in Safari/Chrome. Keep Terminal open.
4. Arrow keys = turn knob; Enter = press knob; Escape = Back; S = Scan. Buttons also work.
5. Select Explore & scan → Select to analyse → Select to accept quest → Select to answer → choose Yes, I did it or Not yet. Demo deliberately returns Chope and awards demo-only points. Its labelled sample picture is not analysed.
6. Ctrl+C in Terminal stops the app.

To try a real image on the Mac (optional), run `python configure_key.py`, enter the secret at the hidden prompt, then `python app.py` without `--demo`. Choose a photo in the browser, review it, then Select to send it. macOS HEIC is not supported: export as JPEG first. The key stays on this computer; configure it separately on the Pi later. A browser page never receives the key.

## B. Finish getting SSH working

The image on your card should be **Raspberry Pi OS Lite (64-bit)**, device Raspberry Pi 3, hostname `sgpal`, username `jaz`, SSH enabled with password authentication. Keep your own password private. If you chose different names, replace them in all commands.

On your iPhone enable Personal Hotspot → Allow Others to Join and Maximise Compatibility. Enter the exact hotspot name/password in Imager; don't reuse unrelated saved Wi-Fi. Connect your Mac to that hotspot. Boot with the card inserted and allow five minutes.

```bash
ssh -o ConnectTimeout=10 jaz@sgpal.local
```

Accept the first host-key prompt only when connecting to your own Pi. The login password is the Pi password, not the hotspot password. Terminal hides typing.

**If name resolution still fails after re-imaging, stop repeating the imaging step.** The hostname may not resolve, the Pi may not be on Wi-Fi, or hotspot clients may not be able to discover each other. Your earlier scan showed only the phone gateway and your Mac, not a confirmed Pi address. Do not assume the Mac address `172.20.10.4` belongs to the Pi.

Fastest reliable fallback if you have the equipment: connect the Pi's full-size HDMI to a monitor/TV and a USB keyboard. The SPI screen cannot show the boot console yet. Log in on that monitor and run:

```bash
hostname
hostname -I
nmcli device status
sudo nmtui
```

In nmtui choose Activate a connection, select your hotspot and enter its password. Exit and run `hostname -I` again. Then from Mac use `ssh jaz@PI_IP_ADDRESS` with the actual address shown. Alternatively attach Pi Ethernet to a router and connect your Mac to that router. Neither method needs re-imaging.

If SSH reports a changed host key after your own re-image, verify that the device/address really is your Pi, then remove the stale entry with `ssh-keygen -R sgpal.local` (or the actual IP used) and reconnect. Never dismiss a changed key for an unexplained reason.

## C. Copy the build from Mac to Pi

With working SSH, run these on the **Mac**, not inside an SSH session:

```bash
cd ~/Downloads/SG-Pal
ssh jaz@sgpal.local 'mkdir -p ~/SG-Pal'
scp app.py core.py ui.py hardware.py culture.json config.json requirements.txt configure_key.py install_pi.sh install_autostart.sh diagnose.sh test_display.py test_controls.py README.md WIRING.md jaz@sgpal.local:~/SG-Pal/
scp -r assets tests jaz@sgpal.local:~/SG-Pal/
```

If using an IP, replace every `sgpal.local` above. These explicit copies exclude your Mac's `.venv` and credentials. Do not copy a Mac virtual environment to Linux.

Now log in:

```bash
ssh jaz@sgpal.local
cd ~/SG-Pal
bash install_pi.sh
sudo reboot
```

The SSH session disconnects during reboot. Wait a minute, reconnect, then:

```bash
cd ~/SG-Pal
source .venv/bin/activate
export GPIOZERO_PIN_FACTORY=lgpio
ls /dev/spidev*
```

Expected SPI devices include `/dev/spidev0.0` and `/dev/spidev0.1`. Installation needs internet through the hotspot. If apt says a package cannot be found, save the exact output; don't force random old drivers or run `sudo pip`.

## D. Wire and test in stages

Read **WIRING.md** before connecting anything. Each time you change wiring:

```bash
sudo poweroff
```

Wait until shutdown activity has settled (about 30 seconds), unplug micro-USB power, then wire. The red LED can stay lit until unplugged. Never insert/remove the camera or GPIO connections while powered.

### D1. Display first
Connect only the eight LCD wires shown in WIRING.md; leave MISO and the four touch wires disconnected for this first test. Reconnect power, SSH in, then:

```bash
cd ~/SG-Pal
source .venv/bin/activate
export GPIOZERO_PIN_FACTORY=lgpio
python test_display.py
```

Confirm red, green, blue and the border. If upside down set `rotate_180` to `true` in `config.json`. If red and blue are reversed set `swap_red_blue` to `true`. If flickering, check connections and reduce `spi_hz` to `8000000`. Backlight with no image is not a successful test.

To show the UI before wiring controls:

```bash
python app.py --pi --demo --no-controls
```

Use the browser via the SSH tunnel below. Ctrl+C stops it. Do not run two applications using the display/GPIO at once.

### D2. Camera
Power down/unplug. Connect camera to **CAMERA**, not DISPLAY. On Pi 3B+, ribbon metal contacts face the HDMI side; blue stiffener faces the USB/Ethernet side. Gently lift the camera connector latch, insert the ribbon straight and evenly, then close it. Do not pull the latch off. Remove the protective lens film before photography.

Boot and reconnect, then:

```bash
rpicam-hello --list-cameras
rpicam-still --nopreview --timeout 1500 --width 1280 --height 960 --output ~/camera-test.jpg
```

The original Rev 1.3 camera typically identifies as OV5647. Copy the test photo using a separate **Mac** Terminal:

```bash
scp jaz@sgpal.local:~/camera-test.jpg ~/Downloads/
open ~/Downloads/camera-test.jpg
```

If no camera is detected, power off and check the ribbon seating/orientation first. Current Raspberry Pi camera software normally auto-detects it; do not enable obsolete legacy-camera tutorials. A manual `dtoverlay=ov5647` is a fallback only after checking detection/configuration, not part of this default install.

### D3. Rotary + buttons
Power down/unplug and wire by the actual printed pin labels in WIRING.md. The uploaded encoder photo did not clearly show all labels: do not guess its pin order. Send a close-up if its labels differ.

Boot, reconnect, then:

```bash
cd ~/SG-Pal
source .venv/bin/activate
export GPIOZERO_PIN_FACTORY=lgpio
python test_controls.py
```

Expected output: `next`, `prev`, `select`, `back`, `scan`. Ctrl+C exits. If rotation is reversed, exchange `rotary_a` and `rotary_b` in `config.json` (software change; no rewiring needed). Each button needs an actual switch contact pair, not two permanently joined legs.

## E. Enter Common Ground key privately on Pi

```bash
cd ~/SG-Pal
source .venv/bin/activate
python configure_key.py
```

Paste the **actual secret key**, not the display name Common Ground, at the hidden prompt. The script stores it at `~/.config/sgpal/credentials.json` with owner-only permissions. It is not stored in this project/ZIP, shown in the browser, or printed in logs. Do not paste it into chat/screenshots. The key's project needs model access and available API billing/quota; a key name alone does not activate billing.

## F. Run the complete core build

```bash
cd ~/SG-Pal
source .venv/bin/activate
export GPIOZERO_PIN_FACTORY=lgpio
python app.py --pi
```

1. Turn knob to Explore & scan and press.
2. Aim the camera; a still is captured. There is no live viewfinder in this version.
3. Review the image. Press to send to OpenAI; Back discards it. Scan can retake it.
4. A high-confidence match to our ten categories earns 10 XP once. Turn to read longer text.
5. Press to accept its quest. This replaces any currently active quest; completed quests cannot repeat for XP.
6. Open My quest, take a new photo, confirm analysis. A clear match to the quest criterion earns 25 XP once.
7. Back returns home; Culture log reopens facts. My pal shows levels/accessories.

Ambiguous matches do not earn points. Model confidence is a self-assessment, not a probability or guarantee. Cultural facts are from the curated JSON; the model supplies the match and a short observation. Empty network/API results never become invented discoveries. Without internet, the creature, saved log and progress still work; new AI scans show an error. Demo is a separate explicit launch mode.

### Watch/control the Pi screen from your Mac

In a second **Mac Terminal**:

```bash
ssh -L 8765:127.0.0.1:8765 jaz@sgpal.local
```

Keep this connection open, and open http://127.0.0.1:8765 on the Mac. Stop the Mac preview first if that port is already in use. The Pi web interface only listens on localhost; the SSH tunnel is intentional. Photo upload is enabled in desktop live preview only; Pi mode uses its camera.

## G. Start automatically on boot (after manual tests pass)

Stop the manually running app with Ctrl+C before installing the service:

```bash
cd ~/SG-Pal
bash install_autostart.sh
sudo systemctl status sgpal --no-pager
```

Useful commands:

```bash
sudo systemctl stop sgpal
sudo systemctl start sgpal
sudo systemctl restart sgpal
journalctl -u sgpal -n 50 --no-pager
sudo systemctl disable --now sgpal
```

The standard service runs as your user, not root, and launches real mode. Keep LED ring disabled for this standard service. Offline boot still opens the interface; a later Scan can work once Wi-Fi returns. To change config, stop the service, edit `config.json`, and restart.

## H. Optional touch, buzzer and ring

These are supplementary and untested on physical hardware. See WIRING.md for electrical prerequisites. Enable one at a time only after core works.

- Touch: connect TP wires, set `touch: true`. Test taps; if coordinates are wrong, leave it disabled and use the knob. It does not provide full gesture navigation.
- Buzzer: verify the module's 3.3V supply/logic compatibility, wire then set `buzzer: true`. This adapter is for the photographed low-level-trigger module. It emits a brief tone on scan/quest outcomes.
- LED ring: requires proper 5V power distribution and 3.3V-to-5V signal conversion. Do not power a 24-pixel ring from the Pi's 3.3V pin. It can be left out without any loss of the scan loop. With prerequisites met, install `rpi_ws281x` into the Pi venv and set `led_ring: true`. GPIO12 PWM on this backend may require root; this is a separate optional setup, not enabled by the standard boot service. For a manual test, stop the service and run:

```bash
cd ~/SG-Pal
.venv/bin/python -m pip install 'rpi_ws281x>=5,<6'
sudo env GPIOZERO_PIN_FACTORY=lgpio SGPAL_KEY_FILE="$HOME/.config/sgpal/credentials.json" "$PWD/.venv/bin/python" "$PWD/app.py" --pi --demo --data-dir /tmp/sgpal-led-demo
```

This optional command runs trusted local code as root to access PWM and uses temporary demo progress. Do not enable a privileged live service without reviewing permissions. Ring brightness starts at 12/255. The ring shows green/amber status, not a full animation system. A low software brightness setting is not a substitute for correct wiring/power design.

## I. Troubleshooting and testing

- Run `bash diagnose.sh` on Pi for model, OS, IP, power flags, SPI and camera status. It does not print passwords/keys.
- No display: check the exact model is the photographed 2.8inch Capacitive Touch LCD, all eight wires, SPI enabled, no competing service. This is not an HDMI/DSI screen and does not automatically show Linux desktop.
- Permission errors: reboot after installation/group changes. Use the supplied venv and `GPIOZERO_PIN_FACTORY=lgpio`.
- GPIO busy: stop the boot service before running test scripts or another app instance.
- API 401: configure the key again. 429: billing/quota/rate limit. 404: model access/name. Network error: hotspot/internet. No automatic fallback to fake results.
- Camera timeout: check ribbon, `--list-cameras`, and no other program using it. A blurry camera image can cause unknown results.
- Power trouble: `vcgencmd get_throttled`; `0x0` is the clean baseline. Use a stable supply suitable for Pi 3B+ (nominal recommendation 5V/2.5A for Pi, plus peripheral budget) and a good micro-USB cable. Disconnect optional loads while troubleshooting.
- Browser won't open on Mac: ensure app process is still running; on Pi use the tunnel. Check no other process is using 8765.

Tests (no hardware/API calls):

```bash
python -m unittest discover -s tests -v
```

Acceptance checklist before demo:
- [ ] SSH works; exact OS/model recorded.
- [ ] LCD test colours/border/orientation correct.
- [ ] Camera test photo clear.
- [ ] Knob and both buttons produce correct events.
- [ ] Demo whole flow works and says DEMO.
- [ ] Real scan uses key, shows suitable result or honest uncertainty.
- [ ] Wi-Fi failure shows error without XP reward or fabricated result.
- [ ] Repeated discovery/quest does not add duplicate points.
- [ ] App restart preserves real progress.
- [ ] Boot service opens interface without manual start.

Progress lives outside the code: `~/.local/share/sgpal/progress.json`, with separate `demo-progress.json`. Photos are held in memory during a scan; saved logs hold category, timestamp and photo hash, not photo files. Camera diagnostic photos are separate and remain until you remove them. OpenAI receives the photo only on confirmation, with `store:false`; that is not a promise of zero provider retention. Avoid sensitive imagery. API requests incur your project's charges. Treat culture content as a starter set for human review before broader public use.

## Sources and implementation notes

- Display model/pin mapping: https://www.waveshare.com/wiki/2.8inch_Capacitive_Touch_LCD
- Product: https://www.waveshare.com/2.8inch-capacitive-touch-lcd.htm
- Register reference downloaded: https://files.waveshare.com/wiki/2.8inch-Capacitive-Touch-LCD/2.8inch_Capacitive_Touch_LCD_RaspberryPi.zip
- Camera: https://www.raspberrypi.com/documentation/computers/camera_software.html
- Setup: https://www.raspberrypi.com/documentation/computers/getting-started.html
- Vision: https://developers.openai.com/api/docs/guides/images-vision
- Structured outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Model: https://developers.openai.com/api/docs/models/gpt-4.1-mini
- LED electrical guidance: https://learn.adafruit.com/neopixels-on-raspberry-pi/raspberry-pi-wiring

Hardware adapters were written for this package using the vendor's register values as reference. Display transfer uses RGB565 with explicit inclusive address bounds. DejaVu Sans is bundled with its licence. Pixel creature is original code-drawn artwork. No API keys or uploaded personal photographs are bundled.
