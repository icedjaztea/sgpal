"""Kopi Sunset browser entry point, alongside the original app.py Pi runtime.

Adoption/preferences have their own file. Existing progress is read through the
shared Store and is never rewritten by UI operations or design previews.
"""
import json
import base64
import binascii
import sqlite3
from uuid import UUID
import os
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from core import CULTURE, BY_ID, atomic_json, api_key, normalise, recognise
from sgpal.gameplay import GameStore, GameError, legacy_progress

ROOT = Path(__file__).parent
DATA = Path(os.environ.get("SGPAL_DATA_DIR", Path.home() / ".local/share/sgpal"))
LOCK = Lock()
app = FastAPI(title="SG Pal · Kopi Sunset", docs_url=None, redoc_url=None)


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    species: Literal["merlion", "otter", "mynah"]
    name: str = Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9 -]+$")

    @field_validator("name")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Name cannot be blank")
        return value.strip()


class SavedProfile(Profile):
    version: Literal[1] = 1
    adopted: bool = False
    sound: bool = False


class Sound(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    enabled: bool


def read_profile():
    path = DATA / "profile.json"
    if not path.exists():
        return SavedProfile(species="merlion", name="Kopi")
    try:
        return SavedProfile.model_validate(json.loads(path.read_text()))
    except (ValueError, OSError, ValidationError) as exc:
        raise HTTPException(503, "Profile could not be read. Existing file preserved.") from exc


def read_state():
    profile = read_profile()
    try:
        game = GameStore(DATA)
        progress = game.state() if game.path.exists() else legacy_progress(DATA)
    except (RuntimeError, OSError, ValueError, TypeError, sqlite3.Error, OverflowError) as exc:
        raise HTTPException(503, "Progress could not be read. Existing file preserved.") from exc
    return {**profile.model_dump(), "xp": progress["xp"], "coins": progress.get("coins", 0),
            "level": 1 + progress["xp"] // 50,
            "discoveries": list(progress["log"]), "log": progress["log"],
            "quests": list(progress["log"]), "completed": progress["completed"],
            "active": progress["active"], "quest_details": progress.get("quest_details", {}), "inventory": [], "room": {}}


def save_profile(profile):
    try:
        atomic_json(DATA / "profile.json", profile.model_dump())
    except OSError as exc:
        raise HTTPException(503, "Save failed. Retry after checking device storage.") from exc


@app.middleware("http")
async def same_origin_writes(request: Request, call_next):
    if request.method == "POST":
        try:
            if int(request.headers.get("content-length", "0")) > 9 * 1024 * 1024:
                return JSONResponse({"detail": "Photo request too large. Use a photo under 6 MB."}, status_code=413)
        except ValueError:
            return JSONResponse({"detail": "Invalid request size."}, status_code=400)
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            return JSONResponse({"detail": "Cross-origin writes are not allowed."}, status_code=403)
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/status")
def status():
    return {"mode": "local-browser", "ai_ready": credential_present(), "pi_camera_ready": False,
            "cloud_sync_ready": False, "progress_source": "gameplay.sqlite3" if GameStore(DATA).path.exists() else "progress.json"}


@app.get("/api/catalogue")
def catalogue():
    return CULTURE


@app.get("/api/state")
def state():
    with LOCK:
        return read_state()


@app.post("/api/adopt")
def adopt(body: Profile):
    with LOCK:
        before = read_state()
        if before["adopted"]:
            raise HTTPException(409, "A Pal is already adopted on this device.")
        profile = read_profile().model_copy(update={**body.model_dump(), "adopted": True})
        save_profile(profile)
        return {**before, **profile.model_dump()}


@app.post("/api/sound")
def sound(body: Sound):
    with LOCK:
        before = read_state()
        profile = read_profile().model_copy(update={"sound": body.enabled})
        save_profile(profile)
        return {**before, **profile.model_dump()}


def credential_present():
    try:
        return bool(api_key())
    except (RuntimeError, OSError, ValueError):
        return False


class OperationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID


class ScanBody(OperationBody):
    image: str = Field(min_length=1, max_length=8 * 1024 * 1024)


class VerifyBody(ScanBody):
    quest_id: str


class CorrectionBody(OperationBody):
    source_operation_id: UUID
    culture_id: str


class QuestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    culture_id: str


class QuestAnswerBody(OperationBody):
    culture_id: str
    done: bool = Field(strict=True)


@app.exception_handler(GameError)
async def game_error(request, exc):
    return JSONResponse({"detail": exc.message}, status_code=exc.status)


@app.exception_handler(sqlite3.Error)
async def database_error(request, exc):
    return JSONResponse({"detail": "Save unavailable. Check device storage and retry; no new reward is confirmed."}, status_code=503)


def game_store():
    if not read_profile().adopted:
        raise HTTPException(409, "Adopt your Pal first.")
    read_state()  # Validate existing progress before migration or any AI work.
    return GameStore(DATA)


def photo_bytes(encoded):
    try:
        raw = base64.b64decode(encoded, validate=True)
        return normalise(raw)
    except Exception:
        # Never return image bytes or a provider payload in an error.
        raise HTTPException(422, "Use a readable JPEG, PNG or WebP under 6 MB and 24 megapixels.") from None


def assess(store, oid, kind, photo, target=None, source=None):
    # A retry first consults the existing operation. Missing credentials must not
    # hide an already committed result, or trigger a duplicate provider request.
    if store.path.exists():
        try:
            prior = store.operation(oid)
            if prior['status'] not in ('failed', 'pending'):
                cached, _ = store.begin(oid, kind, photo, target, source)
                return {**cached, 'state': read_state()}
        except GameError as exc:
            if exc.status != 404: raise
    if not credential_present():
        raise HTTPException(503, "Common Ground key is not configured. Run python configure_key.py in Terminal, then Retry.")
    cached, lease = store.begin(oid, kind, photo, target, source)
    if cached:
        return {**cached, 'state': read_state()}
    try:
        result = recognise(photo, BY_ID[target] if kind == 'verify' else None,
                           BY_ID[target] if kind == 'scan' and target else None)
        store.finish(oid, lease, result)
        outcome = store.operation(oid)
    except (sqlite3.Error, OSError):
        # The provider may have finished, but no success is reported unless the
        # transaction committed. A retry reconciles this operation's identity.
        raise HTTPException(503, "Could not finish saving. Check request status before retrying.") from None
    except Exception as exc:
        message = str(exc) if isinstance(exc, RuntimeError) else 'AI could not assess the image. Retry with no reward claimed.'
        store.fail(oid, lease, message)
        raise HTTPException(502, message) from None
    return {**outcome, 'state': read_state()}


@app.post('/api/scan')
def scan(body: ScanBody):
    return assess(game_store(), str(body.operation_id), 'scan', photo_bytes(body.image))


@app.post('/api/correct')
def correct(body: CorrectionBody):
    if body.culture_id not in BY_ID:
        raise HTTPException(422, 'Unknown culture catalogue item.')
    store = game_store()
    return assess(store, str(body.operation_id), 'scan', store.source_photo(str(body.source_operation_id)), body.culture_id, str(body.source_operation_id))


@app.post('/api/retry')
def retry(body: OperationBody):
    store = game_store()
    prior = store.operation(str(body.operation_id))
    if prior['kind'] == 'complete':
        return {**prior, 'state': read_state()}
    kind, photo, target, source = store.retry_request(str(body.operation_id))
    return assess(store, str(body.operation_id), kind, photo, target, source)


@app.post('/api/confirm')
def confirm(body: OperationBody):
    store = game_store()
    store.confirm(str(body.operation_id))
    outcome = store.operation(str(body.operation_id))
    return {**outcome, 'state': read_state()}


@app.post('/api/verify')
def verify(body: VerifyBody):
    if body.quest_id not in BY_ID:
        raise HTTPException(422, 'Unknown quest.')
    return assess(game_store(), str(body.operation_id), 'verify', photo_bytes(body.image), body.quest_id)


@app.post('/api/quests/activate')
def activate(body: QuestBody):
    game_store().activate(body.culture_id)
    return read_state()


@app.post('/api/quests/answer')
def answer_quest(body: QuestAnswerBody):
    outcome = game_store().answer_quest(str(body.operation_id), body.culture_id, body.done)
    return {**outcome, 'state': read_state()}


@app.get('/api/operations/{operation_id}')
def operation(operation_id: UUID):
    result = game_store().operation(str(operation_id))
    return {**result, 'state': read_state()}


@app.get('/api/photos/{photo_id}')
def photo(photo_id: UUID):
    return Response(game_store().photo(str(photo_id)), media_type='image/jpeg', headers={'Cache-Control': 'private, no-store'})


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
