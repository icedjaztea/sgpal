# SG Pal wiring — Pi 3B+ / 2.8in Waveshare SPI LCD

## Read first

Shut down with `sudo poweroff`, wait about 30 seconds, then unplug ALL power before changing wires or ribbons. Never feed 5V into a GPIO signal pin. Use the supplied 13-wire screen harness; follow the PCB labels, not wire colours. Its flat FPC ribbon is NOT a cable for the Pi's DSI or CSI connectors.

For the first build, use direct female jumper connections to the Pi header. The GPIO extension board and 40-way ribbon are optional. Using the extension later requires confirming pin-1 orientation at BOTH ends and correct alignment. A reversed/offset ribbon can connect power to signal pins. Don't infer pin 1 from a rainbow wire colour.

**Physical pin numbering** counts the 40 header positions. **BCM/GPIO numbering** names the signal. Example: GPIO25 is physical pin 22. The code uses BCM; the physical column below tells you where to connect.

Locate physical pin 1 before wiring: hold the Pi with USB/Ethernet ports at the bottom and GPIO header along the right edge, as in your supplied Pi photo. Pin 1 is the upper pin in the inner column (toward the board centre); pin 2 is beside it toward the outside edge. The inner column is 1,3,5...39 top-to-bottom; the outside column is 2,4,6...40. Check against the board's pin-1 marker before powering. If unsure, send a clear photo of the proposed connections first.

## 1. LCD core — wire these eight connections first

| Screen PCB label | Raspberry Pi signal | Physical pin | Extension-board label |
|---|---|---:|---|
| VCC | 3.3V | 1 | 3V3 |
| GND | Ground | 6 | GND |
| MOSI | GPIO10 / SPI MOSI | 19 | SPIMOSI / SPIMOS |
| SCLK | GPIO11 / SPI clock | 23 | SPISCLK / SPISCL |
| LCD_CS | GPIO8 / CE0 | 24 | SPICE0 |
| LCD_DC | GPIO25 | 22 | GPIO25 |
| LCD_RST | GPIO27 | 13 | GPIO27 |
| LCD_BL | GPIO18 | 12 | GPIO18 |

**MISO: leave disconnected** (vendor's Pi mapping says NC). Secure unused harness ends so they cannot touch pins. Do not substitute 5V for 3.3V in this build.

## 2. Touch — optional, four extra wires

| Screen PCB label | Pi signal | Physical pin |
|---|---|---:|
| TP_SDA | GPIO2 / I²C SDA | 3 |
| TP_SCL | GPIO3 / I²C SCL | 5 |
| TP_INT | GPIO4 | 7 |
| TP_RST | GPIO17 | 11 |

Leave these four ends insulated/disconnected when touch is disabled. `config.json` defaults to `touch: false`. It is fine to make the device knob-only.

## 3. Rotary encoder — confirm labels before wiring

The photo shows a small breakout with a five-pin header, but its full printed labels are not legible. The following mapping applies **only when those actual labels are present**; do not interpret this table as left-to-right pin order.

| Encoder label (common alternatives) | Pi signal | Physical pin |
|---|---|---:|
| GND / - | Ground | 9 |
| VCC / + (3.3V-compatible module only) | 3.3V | 17 |
| CLK / A | GPIO5 | 29 |
| DT / B | GPIO6 | 31 |
| SW / push | GPIO13 | 33 |

If it instead has bare switch labels A/B/C plus two switch contacts, get its pinout first; don't attach power based on this powered-breakout mapping. Encoder is optional until identified: run with `--no-controls` and use the browser tunnel. External knob is a press-fit accessory; washer/nut are for mounting in the case panel, not electrical parts.

## 4. Two buttons

| Button | One contact | Other contact |
|---|---|---|
| Back | GPIO19, physical 35 | GND, physical 14 |
| Scan | GPIO26, physical 37 | GND, physical 20 |

The code enables internal pull-ups. The switch joins GPIO to ground when pressed; no 3.3V/5V wire goes to a button. Four-leg tactile switches usually contain two internally joined pairs. Confirm with a continuity meter or the actual switch datasheet; use one leg from each pair. Place it across the breadboard's centre gap when its dimensions allow. If a button reads permanently pressed, likely the wrong leg pair is connected. Don't force wide legs into incompatible breadboard spacing.

## 5. Camera Rev 1.3

Use the existing 15-pin camera ribbon in the Pi connector labelled **CAMERA**, between HDMI and audio connector area. It does not use the 40-pin GPIO header. Power must be disconnected. At the Pi end, contacts face HDMI and the blue tab faces USB/Ethernet. At the camera end follow its existing connector orientation. Open latches gently, insert squarely, then lock. Remove lens protection film.

## 6. Buzzer — optional, do not enable before checking module rating

Photo identifies a low-level-trigger passive module marked GND / I/O / VCC. Verify seller's 3.3V supply and logic rating before using:

| Module label | Pi connection |
|---|---|
| I/O | GPIO16, physical 36 |
| GND | GND, physical 30 |
| VCC | 3.3V distribution rail, only if module supports it |

Share the 3.3V rail from Pi through the breadboard; never stuff two wire sockets on one header pin. If this module needs 5V power, verify input circuitry or add an appropriate driver/level interface before connecting to Pi. Do not connect an unknown 5V input circuit directly to GPIO. The provided adapter assumes low-level activation as printed on your module. It is disabled by default.

## 7. WS2812 24-LED ring — optional hardware prerequisites

The photos do not establish the ring's backside pad order, and no suitable level shifter, power distribution or protection components were shown. **Leave the ring disconnected for the initial core demo.** The code adapter exists, but you need an electrically complete wiring setup before enabling it.

Target wiring once the module labels and power budget are confirmed:

| Connection | Target |
|---|---|
| Pi GPIO12, physical 32 | Input of a 3.3V-compatible-to-5V logic level shifter (e.g. suitable 74AHCT125 breakout) |
| Shifter 5V output | Ring **DIN** via an appropriate series resistor (typically 330–470Ω) |
| Ring 5V | Suitable regulated 5V supply/distribution, not a GPIO signal or 3.3V rail |
| Ring GND | Supply ground and Pi ground (physical 34) connected together |
| Bulk capacitor | Across ring supply at ring; typically 500–1000µF, voltage rating above supply, correct polarity |

DOUT is not DIN. Verify the shifter's enable pins and supply against its own pinout. Use a ready-made solderless-compatible level-shifter board if preserving no-solder assembly. Do not tie independent positive power supplies together or backfeed the Pi through the header. Ground sharing is required. Traditional worst-case sizing is up to roughly 60mA per pixel at full white, so 24 LEDs can represent approximately 1.44A additional load; exact variants differ. That is why a Pi-sized supply alone is not automatically sufficient for a full-brightness ring. Default brightness is low, but software cannot guarantee all fault states.

GPIO12 is deliberately reserved for the optional ring; GPIO18 is already the LCD backlight. Do not follow generic LED guides that also put the ring on GPIO18.

## Pin allocation audit

LCD: 8,10,11,18,25,27. Touch: 2,3,4,17. Encoder: 5,6,13. Buttons: 19,26. Optional buzzer: 16. Optional ring: 12. These are all **BCM** numbers, with no overlap. Camera uses CSI.

Reference: https://www.waveshare.com/wiki/2.8inch_Capacitive_Touch_LCD
