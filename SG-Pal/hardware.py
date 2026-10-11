"""Pi hardware adapters. Register values checked against Waveshare's 2.8in sample.
No GPIO imports occur in desktop preview. All pin numbers below are BCM.
"""
import time, subprocess, tempfile
from pathlib import Path

class Display:
    def __init__(self, config):
        import spidev
        from gpiozero import DigitalOutputDevice
        self.config = config
        self.reset = DigitalOutputDevice(27, initial_value=True)
        self.dc = DigitalOutputDevice(25, initial_value=False)
        self.bl = DigitalOutputDevice(18, initial_value=False)
        self.spi = spidev.SpiDev(); self.spi.open(0, 0)
        self.spi.max_speed_hz = config['spi_hz']; self.spi.mode = 0
        self.reset.off(); time.sleep(.02); self.reset.on(); time.sleep(.12)
        regs = [(0x36,[0x00]), (0x3A,[0x05]), (0xB2,[0x0B,0x0B,0,0x33,0x35]),
                (0xB7,[0x11]), (0xBB,[0x35]), (0xC0,[0x2C]), (0xC2,[1]),
                (0xC3,[0x0D]), (0xC4,[0x20]), (0xC6,[0x13]), (0xD0,[0xA4,0xA1]),
                (0xD6,[0xA1]), (0xE0,[0xF0,6,11,10,9,0x26,0x29,0x33,0x41,0x18,0x16,0x15,0x29,0x2D]),
                (0xE1,[0xF0,4,8,8,7,3,0x28,0x32,0x40,0x3B,0x19,0x18,0x2A,0x2E])]
        for cmd, data in regs: self.command(cmd, data)
        self.command(0x21); self.command(0x11); time.sleep(.12); self.command(0x29)
        self.bl.on()

    def command(self, cmd, data=()):
        self.dc.off(); self.spi.writebytes([cmd])
        if data: self.dc.on(); self.spi.writebytes(list(data))

    def show(self, image):
        import numpy as np
        from PIL import Image
        if self.config['rotate_180']: image = image.transpose(Image.Transpose.ROTATE_180)
        # Render portrait controller memory from our landscape canvas.
        image = image.transpose(Image.Transpose.ROTATE_90)
        pixels = np.asarray(image.convert('RGB'), dtype=np.uint16)
        if self.config['swap_red_blue']: pixels = pixels[..., ::-1]
        words = ((pixels[:,:,0] >> 3) << 11) | ((pixels[:,:,1] >> 2) << 5) | (pixels[:,:,2] >> 3)
        data = words.astype('>u2').tobytes()
        self.command(0x2A,[0,0,0,239]); self.command(0x2B,[0,0,1,63]); self.command(0x2C)
        self.dc.on()
        for start in range(0,len(data),4096): self.spi.writebytes(data[start:start+4096])

    def close(self):
        self.bl.off(); self.spi.close()
        for pin in (self.reset,self.dc,self.bl): pin.close()


class Controls:
    def __init__(self, config, queue):
        from gpiozero import RotaryEncoder, Button
        self.devices = []
        rotary = RotaryEncoder(config['rotary_a'],config['rotary_b'],max_steps=0,bounce_time=.003)
        rotary.when_rotated_clockwise = lambda: queue.put(('next',None))
        rotary.when_rotated_counter_clockwise = lambda: queue.put(('prev',None))
        self.devices.append(rotary)
        for pin, action in [(config['rotary_press'],'select'),(config['back_button'],'back'),(config['scan_button'],'scan')]:
            if pin is None: continue  # Unwired optional Back/Scan buttons.
            button = Button(pin,pull_up=True,bounce_time=.08)
            button.when_pressed = lambda a=action: queue.put((a,None))
            self.devices.append(button)
    def close(self):
        for device in self.devices: device.close()


def capture():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)/'capture.jpg'
        try:
            subprocess.run(['rpicam-still','--nopreview','--timeout','1000','--width','1280',
                            '--height','960','--encoding','jpg','--output',str(path)],
                           check=True, capture_output=True, timeout=15)
            return path.read_bytes()
        except FileNotFoundError: raise RuntimeError('Install rpicam-apps first.') from None
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
            raise RuntimeError('Camera capture failed. Run rpicam-hello --list-cameras over SSH.') from None


class Touch:
    """Optional single-point polling; verify rotation on the actual panel."""
    def __init__(self, config, queue):
        from smbus2 import SMBus, i2c_msg
        from gpiozero import DigitalOutputDevice, DigitalInputDevice
        self.bus = SMBus(1); self.msg = i2c_msg; self.config=config; self.queue=queue
        self.rst=DigitalOutputDevice(17); self.interrupt=DigitalInputDevice(4,pull_up=True)
        self.rst.off(); time.sleep(.01); self.rst.on(); time.sleep(.05)
        self.last=0
    def read(self,reg,n):
        w=self.msg.write(0x1A,[reg>>8,reg&255]); r=self.msg.read(0x1A,n)
        self.bus.i2c_rdwr(w,r); return list(r)
    def poll(self):
        if self.interrupt.value: return
        count=self.read(0xD005,1)[0]&15
        data=self.read(0xD000,5) if 0<count<=5 else None
        self.bus.i2c_rdwr(self.msg.write(0x1A,[0xD0,0x05,0]))
        if data and time.monotonic()-self.last>.3:
            x=(data[1]<<4)|(data[3]>>4); y=(data[2]<<4)|(data[3]&15)
            x,y=319-y,x
            if self.config['rotate_180']: x,y=319-x,239-y
            if 0<=x<320 and 0<=y<240: self.queue.put(('tap',(x,y))); self.last=time.monotonic()
    def close(self): self.bus.close(); self.rst.close(); self.interrupt.close()


class Effects:
    def __init__(self, config):
        self.buzzer=None; self.ring=None
        if config['buzzer']:
            from gpiozero import PWMOutputDevice
            self.buzzer=PWMOutputDevice(config['buzzer_pin'],active_high=False,initial_value=0,frequency=1200)
        if config['led_ring']:
            from rpi_ws281x import PixelStrip
            self.ring=PixelStrip(config['led_count'],config['led_pin'],brightness=config['led_brightness'],channel=0)
            self.ring.begin()
    def signal(self, success):
        if self.ring:
            from rpi_ws281x import Color
            color=Color(20,100,50) if success else Color(80,35,0)
            for i in range(self.ring.numPixels()): self.ring.setPixelColor(i,color)
            self.ring.show()
        if self.buzzer:
            self.buzzer.frequency=1600 if success else 700; self.buzzer.value=.5
            time.sleep(.06); self.buzzer.off()
    def close(self):
        if self.buzzer: self.buzzer.close()
        if self.ring:
            for i in range(self.ring.numPixels()): self.ring.setPixelColor(i,0)
            self.ring.show()
