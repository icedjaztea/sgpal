"""320x240 interface shared pixel-for-pixel by LCD and localhost preview."""
import math, time
from PIL import Image, ImageDraw, ImageFont, ImageOps
from core import ROOT, BY_ID
BG='#F6F1DE'; INK='#233F3B'; MINT='#C7E9CA'; ORANGE='#EF9861'; MUTED='#60766B'
FONTS={s:ImageFont.truetype(str(ROOT/'assets/DejaVuSans.ttf'),s) for s in (10,11,12,13,15,18,22)}

def wrapped(text,width,font=13):
    lines=[]; line=''; f=FONTS[font]
    for word in text.split():
        candidate=(line+' '+word).strip()
        if f.getlength(candidate)<=width: line=candidate
        else:
            if line: lines.append(line)
            line=word
            while f.getlength(line)>width:
                cut=len(line)-1
                while cut>1 and f.getlength(line[:cut])>width: cut-=1
                lines.append(line[:cut]); line=line[cut:]
    if line: lines.append(line)
    return lines


def pal(draw,x,y,level,tick):
    # Original code-drawn pixel creature: a small sprout with a satchel.
    y+=int(math.sin(tick*2)*2)
    draw.rectangle((x+9,y+51,x+69,y+54),fill='#D8DFC5')
    draw.rectangle((x+18,y+6,x+61,y+43),fill=INK)
    draw.rectangle((x+10,y+15,x+69,y+36),fill=INK)
    draw.rectangle((x+15,y+16,x+64,y+35),fill=MINT)
    draw.rectangle((x+22,y+10,x+57,y+42),fill=MINT)
    draw.rectangle((x+24,y+43,x+32,y+49),fill=INK)
    draw.rectangle((x+49,y+43,x+57,y+49),fill=INK)
    blink=int(tick*2)%13==0
    for ex in (27,49): draw.rectangle((x+ex,y+21,x+ex+4,y+(22 if blink else 27)),fill=INK)
    draw.rectangle((x+36,y+31,x+43,y+33),fill=INK)
    draw.rectangle((x+18,y+30,x+24,y+33),fill=ORANGE)
    draw.rectangle((x+54,y+30,x+60,y+33),fill=ORANGE)
    draw.rectangle((x+39,y-4,x+42,y+7),fill=INK)
    draw.rectangle((x+25,y-9,x+39,y-3),fill='#76AE7C')
    draw.rectangle((x+43,y-12,x+55,y-5),fill='#76AE7C')
    if level>=2: draw.rectangle((x+14,y+37,x+65,y+42),fill=ORANGE)
    if level>=3:
        draw.rectangle((x+17,y+3,x+63,y+8),fill='#E9BE59')
        draw.rectangle((x+28,y-2,x+54,y+3),fill='#E9BE59')


def render(app):
    im=Image.new('RGB',(320,240),BG); d=ImageDraw.Draw(im)
    def text(x,y,t,size=13,color=INK): d.text((x,y),t,font=FONTS[size],fill=color)
    d.rectangle((0,0,319,27),fill=INK)
    text(12,5,'SG PAL',13,BG)
    text(186,7,'DEMO' if app.demo else 'OPENAI SCAN',10,'#C7E9CA')
    xp=app.store.data['xp']; level=1+xp//50
    app.hits=[]
    if app.screen=='home':
        text(14,36,'A little local adventure.',15)
        pal(d,219,83,level,time.monotonic())
        text(220,154,f'LEVEL {level}',11)
        for idx,label in enumerate(['Explore & scan','Culture log','My quest','My pal']):
            y=66+idx*32; selected=idx==app.index
            d.rounded_rectangle((10,y,202,y+27),radius=7,fill=MINT if selected else '#EAE8D6')
            text(20,y+5,('> ' if selected else '  ')+label,13)
            app.hits.append(((10,y,202,y+27),('menu',idx)))
        d.rectangle((219,177,302,183),fill='#DEDCC6')
        d.rectangle((219,177,219+int(83*(xp%50)/50),183),fill='#76AE7C')
        text(220,188,f'{xp} XP',11)
        footer='Turn to browse  /  Press to choose'
    elif app.screen=='photo':
        if app.photo:
            import io
            with Image.open(io.BytesIO(app.photo)) as photo: im.paste(ImageOps.fit(photo,(300,145)),(10,36))
        text(12,185,'Send this photo to OpenAI?' if not app.demo else 'Demo photo - no AI request',12)
        footer='Press: analyse  /  Back: discard'
    elif app.screen=='busy':
        pal(d,120,92,level,time.monotonic())
        text(55,162,app.busy_label,13)
        footer='Please wait - controls paused'
    elif app.screen=='pal':
        text(16,39,'Your Pocket Sprout',18)
        pal(d,119,88,level,time.monotonic())
        text(18,157,f'Level {level}  /  {xp} XP',15)
        text(18,181,'Scarf: Lv 2    Sunhat: Lv 3',12)
        footer='Back: home'
    elif app.screen=='log':
        text(14,36,'Culture log',18)
        ids=list(app.store.data['log'])
        if not ids: text(14,87,'Your first discovery awaits.',13)
        else:
            app.index%=len(ids)
            start=max(0,app.index-3)
            for idx in range(start,min(start+4,len(ids))):
                y=67+(idx-start)*33
                d.rounded_rectangle((10,y,308,y+28),radius=6,fill=MINT if idx==app.index else '#EAE8D6')
                text(19,y+5,BY_ID[ids[idx]]['title'],13)
                app.hits.append(((10,y,308,y+28),('logitem',idx)))
        footer='Turn: browse  /  Press: read  /  Back'
    else:
        title,body,footer=app.content()
        text(12,37,title[:28],18)
        lines=wrapped(body,292,13)
        page_size=7; pages=max(1,math.ceil(len(lines)/page_size)); app.page%=pages
        for i,line in enumerate(lines[app.page*page_size:(app.page+1)*page_size]): text(14,70+i*18,line,13)
        if pages>1: text(261,202,f'{app.page+1}/{pages}',10,MUTED)
    d.rectangle((0,219,319,239),fill=INK)
    text(8,224,footer,10,BG)
    app.hits.append(((0,219,95,239),('back',None)))
    return im
