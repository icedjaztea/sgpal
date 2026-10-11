"""TEST ONLY: injected AI responses, temporary data, no OpenAI calls.
Used by test_gameplay_browser.py; never part of the normal server startup.
"""
import io
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from PIL import Image
from sgpal import server

if not os.environ.get('SGPAL_BROWSER_FIXTURE') or not Path(server.DATA).name.startswith('sgpal-game-test-'):
    raise RuntimeError('This fixture requires a dedicated temporary test directory.')


def recognise(photo, quest=None, correction=None):
    color = Image.open(io.BytesIO(photo)).getpixel((0,0))
    uncertain = color[1] > color[0] + 20 and color[1] > color[2] + 20
    return {'culture_id': quest['id'] if quest else correction['id'] if correction else 'kopi',
            'confidence': 'low' if uncertain else 'high',
            'verified': bool(quest) and not uncertain,
            'observation': 'TEST FIXTURE: simulated photo assessment, not a live AI result.'}


server.recognise = recognise
server.credential_present = lambda: True
app = FastAPI()


@app.get('/')
def index():
    html=(server.ROOT/'web/index.html').read_text()
    return HTMLResponse(html.replace('<body>', '<body><p style="margin:0;background:#29334a;color:#f7e8ca;text-align:center">TEST FIXTURE — simulated AI, temporary progress</p>'))


app.mount('/',server.app)
