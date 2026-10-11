"""Single-device local save server. No AI calls, cloud sync or fake rewards."""
import json
import os
import tempfile
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
DATA = Path(os.environ.get("SGPAL_DATA_DIR", str(Path.home() / ".local/share/sgpal")))
LOCK = Lock()
app = FastAPI(title="SG Pal UI prototype", docs_url=None, redoc_url=None)


def default_save():
    return {"version": 1, "adopted": False, "species": "merlion", "name": "Kopi",
            "xp": 0, "coins": 0, "discoveries": [], "quests": [], "inventory": [],
            "room": {}, "sound": False}


def read_save():
    path = DATA / "save.json"
    if not path.exists():
        return default_save()
    try:
        state = json.loads(path.read_text())
        if not isinstance(state, dict) or state.get("version") != 1:
            raise ValueError("Invalid save")
        return {**default_save(), **state}
    except (ValueError, OSError) as exc:
        raise HTTPException(503, "Save could not be read. Existing file was preserved.") from exc


def write_save(state):
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=DATA, delete=False) as out:
            tmp = out.name
            json.dump(state, out)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, DATA / "save.json")
    finally:
        if tmp and Path(tmp).exists():
            Path(tmp).unlink()


class Profile(BaseModel):
    species: str
    name: str = Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9 -]+$")


class Sound(BaseModel):
    enabled: bool


@app.get("/api/status")
def status():
    return {"mode": "local-ui-prototype", "ai_ready": False,
            "pi_camera_ready": False, "cloud_sync_ready": False}


@app.get("/api/state")
def state():
    with LOCK:
        return read_save()


@app.post("/api/adopt")
def adopt(profile: Profile):
    if profile.species not in ("merlion", "otter", "mynah"):
        raise HTTPException(422, "Unknown Pal")
    with LOCK:
        state = read_save()
        if state["adopted"]:
            raise HTTPException(409, "A Pal is already adopted on this device.")
        state.update(adopted=True, species=profile.species, name=profile.name.strip())
        if not state["name"]:
            raise HTTPException(422, "Name cannot be blank")
        write_save(state)
        return state


@app.post("/api/sound")
def sound(body: Sound):
    with LOCK:
        state = read_save()
        state["sound"] = body.enabled
        write_save(state)
        return state


@app.post("/api/scan")
@app.post("/api/verify")
def not_connected():
    raise HTTPException(501, "AI integration is not connected. No rewards were added.")


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
