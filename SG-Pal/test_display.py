from PIL import Image,ImageDraw
from core import CONFIG
from hardware import Display
im=Image.new('RGB',(320,240),'white'); d=ImageDraw.Draw(im)
for box,color in [((0,0,105,180),'red'),((106,0,212,180),'green'),((213,0,319,180),'blue')]: d.rectangle(box,fill=color)
d.text((20,198),'SG PAL - TOP IS ABOVE THE COLOURS',fill='black')
d.rectangle((0,0,319,239),outline='black',width=2)
lcd=Display(CONFIG)
try:
 lcd.show(im); input('Check red/green/blue, orientation and border. Press Enter to exit. ')
finally: lcd.close()
