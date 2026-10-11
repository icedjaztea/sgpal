"""Hardware-independent transport checks; physical validation is separate."""
import io
import json
import queue
from types import SimpleNamespace
import sys
import pytest
import pi_online
import hardware


def test_browser_commands_do_not_expose_error_payloads():
    messages=iter([{'method':'Page.fileChooserOpened','params':{'backendNodeId':7}}, {'id':1,'result':{'data':'frame'}}])
    wire=[]
    c=object.__new__(pi_online.CDP);c.sequence=0;c.events=[]
    c.ws=SimpleNamespace(send=wire.append,recv=lambda:json.dumps(next(messages)))
    assert c.call('Page.captureScreenshot')=={'data':'frame'}
    assert c.events==[{'backendNodeId':7}]
    c.ws.recv=lambda:json.dumps({'id':2,'error':{'message':'private information'}})
    with pytest.raises(RuntimeError,match='^Browser command failed$'):c.call('Runtime.evaluate')


def test_optional_buttons_never_claim_unwired_pins(monkeypatch):
    devices=[]
    class Device:
        def __init__(self,*pins,**options):self.pins=pins;self.options=options;devices.append(self)
        def close(self):pass
    monkeypatch.setitem(sys.modules,'gpiozero',SimpleNamespace(RotaryEncoder=Device,Button=Device))
    events=queue.Queue();controls=hardware.Controls({'rotary_a':5,'rotary_b':6,'rotary_press':13,'back_button':None,'scan_button':None},events)
    assert [d.pins for d in devices]==[(5,6),(13,)]
    devices[0].when_rotated_clockwise();devices[1].when_pressed()
    assert events.get()==('next',None) and events.get()==('select',None)
    assert devices[1].options['bounce_time']==.08
    controls.close()
