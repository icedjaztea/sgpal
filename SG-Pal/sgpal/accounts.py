"""Opaque browser sessions + Supabase-managed email authentication.

No provider tokens or credentials are returned to browsers. Per-player stores
remain authoritative on one persistent FastAPI host; there is no client balance sync.
"""
import hashlib
import os
import secrets
import shutil
import sqlite3
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

CURRENT = ContextVar('sgpal_identity', default=None)
COOKIE = 'sgpal_session'
TTL = 7 * 86400

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Provider:
    @property
    def ready(self):
        return bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_PUBLISHABLE_KEY') and os.getenv('SGPAL_PUBLIC_URL'))

    def call(self, path, body):
        if not self.ready:
            raise HTTPException(503, 'Email sign-in is not configured. Guest play is available; see ACCOUNTS.md for setup.')
        base=os.environ['SUPABASE_URL'].rstrip('/')
        public=os.environ['SGPAL_PUBLIC_URL'].rstrip('/')
        parsed=urlparse(public)
        if not base.startswith('https://') or not (parsed.scheme=='https' or parsed.scheme=='http' and parsed.hostname in ('localhost','127.0.0.1')):
            raise HTTPException(503, 'Authentication requires a configured HTTPS origin (localhost is allowed for development).')
        try:
            r=httpx.post(base+'/auth/v1/'+path, json=body, headers={'apikey':os.environ['SUPABASE_PUBLISHABLE_KEY']}, timeout=15, follow_redirects=False)
            if r.status_code==429: raise HTTPException(429, 'Too many email requests. Wait a minute and try again.')
            if r.status_code>=400: raise HTTPException(400, 'Email sign-in could not finish. Request a fresh link and try again.')
            return r.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(503, 'Authentication service unavailable. Your progress is unchanged; try again later.') from None

    def send(self,email):
        self.call('otp', {'email':email,'create_user':True})

    def verify(self,token):
        result=self.call('verify',{'token_hash':token,'type':'email'})
        try:
            if not isinstance(result,dict): raise ValueError('Invalid provider response')
            user=result.get('user') or {}
            if not isinstance(user,dict) or not isinstance(user.get('email'),str): raise ValueError('Invalid user')
            subject=str(uuid.UUID(user['id']))
            email=user['email'].strip().lower()
            assert user.get('email_confirmed_at')
        except (ValueError,KeyError,TypeError,AssertionError):
            raise HTTPException(401,'The email link could not be verified.') from None
        return subject,email


provider=Provider()


class Sessions:
    def __init__(self,root):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.path=self.root/'accounts.sqlite3'
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS sessions (hash TEXT PRIMARY KEY, owner TEXT NOT NULL, subject TEXT, email TEXT, csrf TEXT NOT NULL, expires REAL NOT NULL, pending_email TEXT, deadline REAL, verified_subject TEXT, verified_email TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS accounts (subject TEXT PRIMARY KEY, owner TEXT NOT NULL UNIQUE, email TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS limits (key TEXT PRIMARY KEY, next REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS claims (hash TEXT PRIMARY KEY, owner TEXT NOT NULL)')

    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=15);db.row_factory=sqlite3.Row
        self.path.chmod(0o600)
        try:
            db.execute('BEGIN IMMEDIATE');yield db;db.commit()
        except BaseException:
            db.rollback();raise
        finally: db.close()

    def issue(self,db,owner=None,subject=None,email=None):
        token=secrets.token_urlsafe(32)
        db.execute('INSERT INTO sessions(hash,owner,subject,email,csrf,expires) VALUES(?,?,?,?,?,?)',
                   (digest(token),owner or str(uuid.uuid4()),subject,email,secrets.token_urlsafe(32),time.time()+TTL))
        return token

    def resolve(self,token):
        with self.db() as db:
            row=db.execute('SELECT * FROM sessions WHERE hash=? AND expires>?',(digest(token or ''),time.time())).fetchone()
            if row:return dict(row),None
            fresh=self.issue(db)
            return dict(db.execute('SELECT * FROM sessions WHERE hash=?',(digest(fresh),)).fetchone()),fresh

    def row(self,db):
        row=db.execute('SELECT * FROM sessions WHERE hash=? AND expires>?',(CURRENT.get()['hash'],time.time())).fetchone()
        if not row: raise HTTPException(401,'Session changed. Reload before continuing.')
        return row

    def request_email(self,email,ip):
        with self.db() as db:
            row=self.row(db)
            if row['subject']: raise HTTPException(409,'Sign out before switching accounts.')
            for key,delay in [('email:'+digest(email),60),('ip:'+digest(ip),10)]:
                prior=db.execute('SELECT next FROM limits WHERE key=?',(key,)).fetchone()
                if prior and prior['next']>time.time():raise HTTPException(429,'Please wait before requesting another link.')
                db.execute('INSERT OR REPLACE INTO limits VALUES(?,?)',(key,time.time()+delay))
            db.execute('UPDATE sessions SET pending_email=?,deadline=?,verified_subject=NULL,verified_email=NULL WHERE hash=?',(email,time.time()+900,row['hash']))
        provider.send(email)

    def complete(self,token):
        with self.db() as db:
            row=self.row(db)
            if not row['pending_email'] or (row['deadline'] or 0)<time.time():raise HTTPException(409,'Request a new email link in this browser first.')
            email=row['pending_email']
        subject,verified_email=provider.verify(token)
        if verified_email!=email:raise HTTPException(401,'This link belongs to another email request. Request a new link in this browser.')
        with self.db() as db:
            row=self.row(db)
            if row['pending_email']!=email or (row['deadline'] or 0)<time.time():raise HTTPException(409,'Email request changed. Request a new link.')
            account=db.execute('SELECT * FROM accounts WHERE subject=?',(subject,)).fetchone()
            if account:
                db.execute('UPDATE sessions SET verified_subject=?,verified_email=? WHERE hash=?',(subject,email,row['hash']))
                return None # Explicit conflict decision, even for an empty guest.
            db.execute('INSERT INTO accounts VALUES(?,?,?)',(subject,row['owner'],email))
            db.execute('DELETE FROM sessions WHERE owner=? AND subject IS NULL',(row['owner'],))
            return self.issue(db,row['owner'],subject,email)

    def decide(self,choice):
        with self.db() as db:
            row=self.row(db)
            if not row['verified_subject'] or (row['deadline'] or 0)<time.time():raise HTTPException(409,'Sign-in confirmation expired. Request a new link.')
            if choice=='guest':
                db.execute('UPDATE sessions SET pending_email=NULL,deadline=NULL,verified_subject=NULL,verified_email=NULL WHERE hash=?',(row['hash'],))
                return None
            account=db.execute('SELECT * FROM accounts WHERE subject=?',(row['verified_subject'],)).fetchone()
            # Keep the guest files untouched. Never merge balances or replace a save.
            db.execute('DELETE FROM sessions WHERE hash=?',(row['hash'],))
            return self.issue(db,account['owner'],account['subject'],account['email'])

    def logout(self):
        with self.db() as db:
            row=self.row(db);db.execute('DELETE FROM sessions WHERE hash=?',(row['hash'],))
            return self.issue(db)

    def claim(self,token):
        with self.db() as db:
            row=self.row(db)
            claim=db.execute('SELECT owner FROM claims WHERE hash=?',(digest(token),)).fetchone()
            if not claim:raise HTTPException(404,'Import key is invalid or already used.')
            if row['subject']:raise HTTPException(409,'Import into a fresh guest, then sign in. Your account is unchanged.')
            folder=self.root/'players'/row['owner']
            if any((folder/name).exists() for name in ('profile.json','gameplay.sqlite3','progress.json')):
                raise HTTPException(409,'This guest already has progress. Use a fresh browser session to import; no saves were changed.')
            db.execute('DELETE FROM claims WHERE hash=?',(digest(token),));db.execute('DELETE FROM sessions WHERE hash=?',(row['hash'],))
            return self.issue(db,claim['owner'])


def cookie(response,token,request):
    secure=request.url.scheme=='https' or os.getenv('SGPAL_PUBLIC_URL','').startswith('https://')
    response.set_cookie(COOKIE,token,max_age=TTL,httponly=True,secure=secure,samesite='lax',path='/')


def router(root):
    api=APIRouter(prefix='/api/auth')
    class EmailBody(BaseModel):
        model_config=ConfigDict(extra='forbid')
        email:str=Field(min_length=3,max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    class TokenBody(BaseModel):
        model_config=ConfigDict(extra='forbid')
        token_hash:str=Field(min_length=20,max_length=256,pattern=r'^[A-Za-z0-9_-]+$')
    class Decision(BaseModel):
        model_config=ConfigDict(extra='forbid')
        choice:str=Field(pattern=r'^(account|guest)$')
    class Claim(BaseModel):
        model_config=ConfigDict(extra='forbid')
        key:str=Field(min_length=32,max_length=128)

    @api.get('/session')
    def session():
        row=CURRENT.get()
        return {'owner_id':row['owner'],'csrf':row['csrf'],'signed_in':bool(row['subject']),'email':row['email'],
                'configured':provider.ready,'conflict':bool(row['verified_subject']),'pending_email':row['pending_email']}

    @api.post('/email')
    def email(body:EmailBody,request:Request):
        Sessions(root()).request_email(body.email.strip().lower(),request.client.host if request.client else 'unknown')
        return {'message':'Request accepted. Check your email and open the link in this browser within 15 minutes. No sign-in is confirmed yet.'}

    @api.post('/complete')
    def complete(body:TokenBody,request:Request,response:Response):
        token=Sessions(root()).complete(body.token_hash)
        if token:cookie(response,token,request)
        return {'signed_in':bool(token),'conflict':not bool(token)}

    @api.post('/decision')
    def decide(body:Decision,request:Request,response:Response):
        token=Sessions(root()).decide(body.choice)
        if token:cookie(response,token,request)
        return {'signed_in':bool(token),'conflict':False}

    @api.post('/logout')
    def logout(request:Request,response:Response):
        cookie(response,Sessions(root()).logout(),request)
        response.headers['Clear-Site-Data']='"cache"'
        return {'signed_in':False}

    @api.post('/import')
    def claim(body:Claim,request:Request,response:Response):
        cookie(response,Sessions(root()).claim(body.key.strip()),request)
        return {'imported':True}
    return api


def prepare_legacy(root,output):
    """Operator-only copy. Source is never reset and no secret is printed."""
    store=Sessions(root);owner=str(uuid.uuid4());target=store.root/'players'/owner
    if not any((store.root/n).exists() for n in ('profile.json','progress.json','gameplay.sqlite3')):
        raise RuntimeError('No legacy save found.')
    target.mkdir(parents=True,mode=0o700)
    for name in ('profile.json','progress.json'):
        if (store.root/name).exists():shutil.copy2(store.root/name,target/name);(target/name).chmod(0o600)
    if (store.root/'gameplay.sqlite3').exists():
        with sqlite3.connect(store.root/'gameplay.sqlite3') as src,sqlite3.connect(target/'gameplay.sqlite3') as dst:src.backup(dst)
        (target/'gameplay.sqlite3').chmod(0o600)
    key=secrets.token_urlsafe(32)
    path=Path(output)
    with open(path,'x',opener=lambda p,flags:os.open(p,flags,0o600)) as handle:handle.write(key)
    with store.db() as db:db.execute('INSERT INTO claims VALUES(?,?)',(digest(key),owner))
    print('Legacy save copied; source preserved. Import key file:',path)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Prepare a private one-time legacy save import. Stop the server first.')
    parser.add_argument('--data',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();prepare_legacy(args.data,args.output)
