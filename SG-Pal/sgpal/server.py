"""Kopi Sunset browser entry point, alongside the original app.py Pi runtime.

Adoption/preferences have their own file. Existing progress is read through the
shared Store and is never rewritten by UI operations or design previews.
"""
import json
import asyncio
import time
import hashlib
import secrets
import base64
import binascii
import sqlite3
from uuid import UUID
import os
from pathlib import Path
from threading import Lock
from typing import Literal
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from filelock import FileLock, Timeout
from sgpal import accounts, friends
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from core import CULTURE, BY_ID, atomic_json, api_key, normalise, recognise
from sgpal.gameplay import GameStore, GameError, legacy_progress
from sgpal.commerce import ITEMS, SLOTS

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


def data_dir():
    identity=accounts.CURRENT.get()
    if identity is None: raise RuntimeError("Player context required")
    return DATA / "players" / identity["owner"]


def read_profile():
    path = data_dir() / "profile.json"
    if not path.exists():
        return SavedProfile(species="merlion", name="Kopi")
    try:
        return SavedProfile.model_validate(json.loads(path.read_text()))
    except (ValueError, OSError, ValidationError) as exc:
        raise HTTPException(503, "Profile could not be read. Existing file preserved.") from exc


def read_state():
    profile = read_profile()
    try:
        game = GameStore(data_dir())
        progress = game.state() if game.path.exists() else legacy_progress(data_dir())
    except (RuntimeError, OSError, ValueError, TypeError, sqlite3.Error, OverflowError) as exc:
        raise HTTPException(503, "Progress could not be read. Existing file preserved.") from exc
    result = {**profile.model_dump(), "xp": progress["xp"], "coins": progress.get("coins", 0),
            "level": 1 + progress["xp"] // 50,
            "local_finds": progress.get("local_finds", []), "discoveries": list(progress["log"]), "log": progress["log"],
            "quests": list(progress["log"]), "completed": progress["completed"],
            "active": progress["active"], "quest_details": progress.get("quest_details", {}), "inventory": progress.get("inventory", []), "room": progress.get("room", {})}
    result['revision']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    identity=accounts.CURRENT.get()
    result['owner_id']=identity['owner'] if identity else None
    return result


def save_profile(profile):
    try:
        atomic_json(data_dir() / "profile.json", profile.model_dump())
    except OSError as exc:
        raise HTTPException(503, "Save failed. Retry after checking device storage.") from exc


@app.middleware("http")
async def private_sessions(request: Request, call_next):
    # Canonical HTTPS origin works behind Render TLS termination without trusting
    # client-controlled forwarded headers. All browser APIs use relative URLs.
    public=os.getenv('SGPAL_PUBLIC_URL','').rstrip('/')
    if public and request.url.path!='/healthz':
        parsed=urlparse(public)
        if parsed.scheme not in ('http','https') or request.headers.get('host')!=parsed.netloc:
            return JSONResponse({'detail':'Invalid application host.'},status_code=400)
    # No URL/body owner ID grants access. Even photo UUIDs require this session.
    if not request.url.path.startswith('/api/'):
        response=await call_next(request)
        response.headers['Referrer-Policy']='no-referrer'
        return response
    context=None;lock=None
    try:
        store=accounts.Sessions(DATA)
        identity,fresh=store.resolve(request.cookies.get(accounts.COOKIE))
        context=accounts.CURRENT.set(identity)
        if request.method=='POST':
            if int(request.headers.get('content-length','0'))>9*1024*1024:
                raise HTTPException(413,'Photo request too large. Use a photo under 6 MB.')
            origin=request.headers.get('origin')
            if origin and origin!=(public or str(request.base_url).rstrip('/')):
                raise HTTPException(403,'Cross-origin writes are not allowed.')
            if fresh or not secrets.compare_digest(request.headers.get('x-sgpal-csrf','').encode(),identity['csrf'].encode()):
                raise HTTPException(403,'Session check failed. Reload before saving.')
            if request.headers.get('x-sgpal-owner')!=identity['owner']:
                raise HTTPException(409,'Player session changed. Reload before saving.')
            if request.url.path not in ('/api/scan','/api/correct','/api/retry'):
                directory=data_dir();directory.mkdir(parents=True,exist_ok=True,mode=0o700)
                lock=FileLock(str(directory/'.write.lock'),thread_local=False)
                deadline=time.monotonic()+20
                while True:
                    try:
                        lock.acquire(timeout=0)
                        break
                    except Timeout:
                        if time.monotonic()>deadline: raise HTTPException(503,'Another save is still running. Retry shortly.')
                        await asyncio.sleep(.025)
                with store.db() as db: store.row(db)
            if request.url.path in ('/api/adopt','/api/sound','/api/room/place','/api/quests/activate'):
                replay=False
                if request.url.path=='/api/room/place':
                    body=await request.json()
                    if not isinstance(body,dict): raise HTTPException(422,'Expected a placement object.')
                    if GameStore(directory).path.exists():
                        try:replay=GameStore(directory).operation(str(body.get('operation_id')))['kind']=='place'
                        except GameError:pass
                if not replay and request.headers.get('if-match')!=read_state()['revision']:
                    raise HTTPException(409,'Progress changed in another tab or device. Refresh progress, then review your choice again.')
        response=await call_next(request)
        if fresh:accounts.cookie(response,fresh,request)
    except HTTPException as exc:
        response=JSONResponse({'detail':exc.detail},status_code=exc.status_code)
    except (sqlite3.Error,OSError,ValueError):
        response=JSONResponse({'detail':'Session or save unavailable. No new success is confirmed; reload and retry.'},status_code=503)
    finally:
        if lock:lock.release()
        if context is not None:accounts.CURRENT.reset(context)
    response.headers['Cache-Control']='private, no-store'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Content-Type-Options']='nosniff'
    return response


@app.get('/healthz')
def healthz():
    # Opening the persistent session DB checks the mount is writable.
    accounts.Sessions(DATA)
    return {'ok':True}


app.include_router(accounts.router(lambda:DATA))
app.include_router(friends.router(lambda:DATA, SavedProfile))


@app.get("/api/status")
def status():
    return {"mode": "local-browser", "ai_ready": credential_present(), "pi_camera_ready": False,
            "cloud_sync_ready": False, "account_sync_configured": accounts.provider.ready, "progress_source": "gameplay.sqlite3" if GameStore(data_dir()).path.exists() else "progress.json"}


@app.get("/api/catalogue")
def catalogue():
    return CULTURE


@app.get('/api/shop')
def shop():
    return {'items': ITEMS, 'slots': SLOTS}


@app.get("/api/state")
def state():
    with LOCK:
        return read_state()


@app.post("/api/adopt")
def adopt(body: Profile):
    with LOCK:
        before = read_state()
        if before["adopted"]:
            raise HTTPException(409, "A Pal is already adopted in this save.")
        profile = read_profile().model_copy(update={**body.model_dump(), "adopted": True})
        save_profile(profile)
        return read_state()


@app.post("/api/sound")
def sound(body: Sound):
    with LOCK:
        before = read_state()
        profile = read_profile().model_copy(update={"sound": body.enabled})
        save_profile(profile)
        return read_state()


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
    return GameStore(data_dir())


def photo_bytes(encoded):
    try:
        raw = base64.b64decode(encoded, validate=True)
        return normalise(raw)
    except Exception:
        # Never return image bytes or a provider payload in an error.
        raise HTTPException(422, "Use a readable JPEG, PNG or WebP under 6 MB and 24 megapixels.") from None


def assess(store, oid, kind, photo, target=None, source=None):
    if kind != 'scan':
        raise HTTPException(410, 'Quests are honesty-based. Open your quest and answer Yes, I did it or Not yet.')
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
        result = recognise(photo, None, BY_ID[target] if target else None)
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
    if prior['kind'] in ('complete', 'purchase', 'place'):
        return {**prior, 'state': read_state()}
    if prior['kind'] == 'verify':
        if prior['status'] in ('verified', 'duplicate'):
            return {**prior, 'state': read_state()}
        raise HTTPException(410, 'Photo checks are retired. Open the quest and answer Yes, I did it or Not yet.')
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
    raise HTTPException(410, 'Quests are honesty-based. Use the quest answer screen; no evidence photo is required.')


@app.post('/api/quests/activate')
def activate(body: QuestBody):
    game_store().activate(body.culture_id)
    return read_state()


@app.post('/api/quests/answer')
def answer_quest(body: QuestAnswerBody):
    outcome = game_store().answer_quest(str(body.operation_id), body.culture_id, body.done)
    return {**outcome, 'state': read_state()}


class PurchaseBody(OperationBody):
    item_id: str


class PlacementBody(PurchaseBody):
    slot_id: str


@app.post('/api/shop/purchase')
def purchase(body: PurchaseBody):
    outcome = game_store().commerce(str(body.operation_id), 'purchase', body.item_id)
    return {**outcome, 'state': read_state()}


@app.post('/api/room/place')
def place(body: PlacementBody):
    outcome = game_store().commerce(str(body.operation_id), 'place', body.item_id, body.slot_id)
    return {**outcome, 'state': read_state()}


@app.get('/api/operations/{operation_id}')
def operation(operation_id: UUID):
    result = game_store().operation(str(operation_id))
    return {**result, 'state': read_state()}


@app.get('/api/photos/{photo_id}')
def photo(photo_id: UUID):
    return Response(game_store().photo(str(photo_id)), media_type='image/jpeg', headers={
        'Cache-Control': 'private, no-store', 'Cross-Origin-Resource-Policy': 'same-origin',
        'X-Content-Type-Options': 'nosniff'})


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
