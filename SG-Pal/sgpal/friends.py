"""Small, authenticated social graph in the shared account database."""
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sgpal import accounts


def router(root, profile_model):
    api=APIRouter(prefix='/api/friends')

    @contextmanager
    def transaction():
        store=accounts.Sessions(root())
        with store.db() as db:
            identity=store.row(db)
            if not identity['subject']:raise HTTPException(401,'Sign in with email to use friends.')
            db.execute('CREATE TABLE IF NOT EXISTS friend_codes(owner TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL)')
            db.execute("CREATE TABLE IF NOT EXISTS friendships(a TEXT NOT NULL,b TEXT NOT NULL,requester TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('pending','accepted')),PRIMARY KEY(a,b),CHECK(a<b))")
            owner=identity['owner']
            if not db.execute('SELECT 1 FROM friend_codes WHERE owner=?',(owner,)).fetchone():
                while True:
                    code=secrets.token_hex(6).upper()
                    try:db.execute('INSERT INTO friend_codes VALUES(?,?)',(owner,code));break
                    except sqlite3.IntegrityError:pass
            yield db,owner

    def profile(owner):
        path=root()/'players'/owner/'profile.json'
        if not path.exists():return {'name':'New neighbour','species':'merlion','adopted':False}
        try:
            value=profile_model.model_validate(json.loads(path.read_text()))
            return {'name':value.name,'species':value.species,'adopted':value.adopted}
        except (ValueError,OSError):raise HTTPException(503,'This neighbour’s profile is unavailable.') from None

    def target(db,code):
        row=db.execute('SELECT owner FROM friend_codes WHERE code=?',(code,)).fetchone()
        if not row:raise HTTPException(404,'Friend code not found. Ask your friend to open Friends and check their code.')
        return row['owner']

    def pair(owner,other):
        if owner==other:raise HTTPException(400,'That is your own friend code.')
        return sorted((owner,other))

    class Action(BaseModel):
        model_config=ConfigDict(extra='forbid')
        code:str=Field(pattern=r'^[A-F0-9]{12}$')
        action:str=Field(pattern=r'^(request|accept|decline|remove)$')

    @api.get('')
    def list_friends():
        with transaction() as (db,owner):
            mine=db.execute('SELECT code FROM friend_codes WHERE owner=?',(owner,)).fetchone()['code']
            result={'code':mine,'incoming':[],'outgoing':[],'friends':[]}
            for edge in db.execute('SELECT * FROM friendships WHERE a=? OR b=?',(owner,owner)):
                other=edge['b'] if edge['a']==owner else edge['a']
                code=db.execute('SELECT code FROM friend_codes WHERE owner=?',(other,)).fetchone()['code']
                group='friends' if edge['status']=='accepted' else 'outgoing' if edge['requester']==owner else 'incoming'
                result[group].append({**profile(other),'code':code})
            return result

    @api.post('')
    def change(body:Action):
        # The rate-limit transaction commits even for invalid guesses/self requests.
        if body.action=='request':
            with transaction() as (db,owner):
                key='friend-request:'+owner
                prior=db.execute('SELECT next FROM limits WHERE key=?',(key,)).fetchone()
                if prior and prior['next']>time.time():raise HTTPException(429,'Wait three seconds before sending another request.')
                db.execute('INSERT OR REPLACE INTO limits VALUES(?,?)',(key,time.time()+3))
        with transaction() as (db,owner):
            other=target(db,body.code);a,b=pair(owner,other)
            edge=db.execute('SELECT * FROM friendships WHERE a=? AND b=?',(a,b)).fetchone()
            if body.action=='request':
                if edge:return {'message':'Already friends.' if edge['status']=='accepted' else 'Request already exists. Check incoming or sent requests.'}
                db.execute("INSERT INTO friendships VALUES(?,?,?,'pending')",(a,b,owner))
                return {'message':'Friend request sent.'}
            if body.action in ('accept','decline'):
                if not edge or edge['status']!='pending' or edge['requester']==owner:
                    raise HTTPException(409,'No incoming request to answer. Refresh Friends.')
                if body.action=='accept':db.execute("UPDATE friendships SET status='accepted' WHERE a=? AND b=?",(a,b))
                else:db.execute('DELETE FROM friendships WHERE a=? AND b=?',(a,b))
                return {'message':'Friend request accepted.' if body.action=='accept' else 'Friend request declined.'}
            if edge:db.execute('DELETE FROM friendships WHERE a=? AND b=?',(a,b))
            return {'message':'Friend removed. Room access revoked.'}

    @api.get('/{code}/room')
    def visit(code:str):
        with transaction() as (db,owner):
            other=target(db,code);a,b=pair(owner,other)
            edge=db.execute("SELECT 1 FROM friendships WHERE a=? AND b=? AND status='accepted'",(a,b)).fetchone()
            if not edge:raise HTTPException(403,'Only accepted friends can visit this room.')
            result=profile(other)
            if not result['adopted']:raise HTTPException(404,'Your friend has not adopted a Pal yet.')
            path=root()/'players'/other/'gameplay.sqlite3';room={}
            # Never initialise/migrate a friend's gameplay store during a visit.
            if path.exists():
                with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as game:
                    if game.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='room'").fetchone():
                        room=dict(game.execute('SELECT slot_id,item_id FROM room'))
            return {**result,'room':room,'code':code,'read_only':True}
    return api
