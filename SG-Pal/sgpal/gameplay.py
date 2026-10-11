"""Transactional local gameplay. Photos, operations and rewards share one SQLite commit.

Legacy JSON is imported once, without altering its contents or awarding retroactive
coins. UI profile remains in profile.json. No model call happens inside a DB lock.
"""
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from core import BY_ID, Store, digest
from sgpal.commerce import BY_ITEM, BY_SLOT

DISCOVERY_XP, DISCOVERY_COINS = 10, 5
QUEST_XP, QUEST_COINS = 25, 10
LEASE_SECONDS = 90


class GameError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)


def singapore_time(epoch):
    return datetime.fromtimestamp(epoch, ZoneInfo('Asia/Singapore')).isoformat(timespec='seconds')


def legacy_progress(directory):
    progress = Store(Path(directory) / 'progress.json').data
    if type(progress['xp']) is not int or progress['xp'] < 0:
        raise ValueError('Invalid XP')
    for cid, record in progress['log'].items():
        if cid not in BY_ID or not isinstance(record, dict):
            raise ValueError('Invalid discovery')
        if type(record.get('time')) not in (int, float) or not isinstance(record.get('hash'), str):
            raise ValueError('Invalid discovery record')
        singapore_time(record['time'])
    if any(cid not in progress['log'] for cid in progress['completed']):
        raise ValueError('Invalid completion')
    if progress['active'] and progress['active'] not in progress['log']:
        raise ValueError('Invalid active quest')
    return progress


class GameStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / 'gameplay.sqlite3'

    @contextmanager
    def connection(self):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(self.path, timeout=10)
        self.path.chmod(0o600)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def initialise(self):
        # Validate the original before creating any migration state.
        with self.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            version = db.execute("SELECT value FROM meta WHERE key='version'").fetchone()
            if version:
                if version['value'] not in ('1', '2', '3'):
                    raise GameError(503, 'Unsupported gameplay save version. Save preserved.')
                snapshot = db.execute("SELECT value FROM meta WHERE key='legacy_snapshot'").fetchone()
                if snapshot and json.loads(snapshot['value']) != legacy_progress(self.directory):
                    raise GameError(503, 'Original progress changed after migration. Both saves are preserved; reconcile them before continuing.')
                if version['value'] == '1':
                    self.migrate_quest_answers(db)
                if version['value'] in ('1', '2'):
                    self.migrate_commerce(db)
                return
            old = legacy_progress(self.directory)
            statements = [
                'CREATE TABLE wallet (id INTEGER PRIMARY KEY CHECK(id=1), xp INTEGER NOT NULL CHECK(xp>=0), coins INTEGER NOT NULL CHECK(coins>=0), active TEXT)',
                'CREATE TABLE photos (id TEXT PRIMARY KEY, hash TEXT NOT NULL, jpeg BLOB NOT NULL, received REAL NOT NULL, received_sgt TEXT NOT NULL)',
                'CREATE TABLE discoveries (culture_id TEXT PRIMARY KEY, photo_id TEXT REFERENCES photos(id), hash TEXT NOT NULL, discovered REAL NOT NULL, discovered_sgt TEXT NOT NULL, xp INTEGER NOT NULL, coins INTEGER NOT NULL)',
                'CREATE TABLE quests (culture_id TEXT PRIMARY KEY REFERENCES discoveries(culture_id), completed INTEGER NOT NULL DEFAULT 0, evidence_id TEXT REFERENCES photos(id), completed_sgt TEXT)',
                'CREATE TABLE operations (id TEXT PRIMARY KEY, kind TEXT NOT NULL, fingerprint TEXT NOT NULL, photo_id TEXT NOT NULL REFERENCES photos(id), target TEXT, source TEXT, status TEXT NOT NULL, result TEXT, started REAL NOT NULL, lease TEXT NOT NULL)',
                'CREATE TABLE rewards (event TEXT PRIMARY KEY, xp INTEGER NOT NULL, coins INTEGER NOT NULL, created_sgt TEXT NOT NULL)',
            ]
            for statement in statements:
                db.execute(statement)
            db.execute('INSERT INTO wallet VALUES(1,?,?,?)', (old['xp'], 0, old['active']))
            for cid, record in old['log'].items():
                db.execute('INSERT INTO discoveries VALUES(?,?,?,?,?,?,?)', (cid, None, record['hash'], record['time'], singapore_time(record['time']), DISCOVERY_XP, 0))
                db.execute('INSERT INTO quests(culture_id,completed) VALUES(?,?)', (cid, int(cid in old['completed'])))
                db.execute('INSERT INTO rewards VALUES(?,?,?,?)', ('discovery:'+cid, 0, 0, singapore_time(record['time'])))
                if cid in old['completed']:
                    db.execute('INSERT INTO rewards VALUES(?,?,?,?)', ('quest:'+cid, 0, 0, singapore_time(record['time'])))
            db.execute("INSERT INTO meta VALUES('legacy_snapshot',?)", (json.dumps(old),))
            db.execute("INSERT INTO meta VALUES('version','1')")
            self.migrate_quest_answers(db)
            self.migrate_commerce(db)

    @staticmethod
    def migrate_quest_answers(db):
        # Additive migration: preserve every balance, photo and prior completion.
        db.execute('CREATE TABLE quest_answers (id TEXT PRIMARY KEY, culture_id TEXT NOT NULL REFERENCES quests(culture_id), done INTEGER NOT NULL, result TEXT NOT NULL)')
        db.execute("UPDATE meta SET value='2' WHERE key='version'")

    @staticmethod
    def migrate_commerce(db):
        db.execute('CREATE TABLE inventory (item_id TEXT PRIMARY KEY, purchased_sgt TEXT NOT NULL, price INTEGER NOT NULL CHECK(price>=0))')
        db.execute('CREATE TABLE room (slot_id TEXT PRIMARY KEY, item_id TEXT NOT NULL UNIQUE REFERENCES inventory(item_id))')
        db.execute('CREATE TABLE commerce_operations (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result TEXT NOT NULL)')
        db.execute("UPDATE meta SET value='3' WHERE key='version'")

    def commerce(self, oid, kind, item_id, slot_id=None):
        if kind not in ('purchase', 'place') or item_id not in BY_ITEM:
            raise GameError(422, 'Choose an available shop item.')
        item = BY_ITEM[item_id]
        if kind == 'place' and (slot_id not in BY_SLOT or slot_id not in item['slots']):
            raise GameError(422, 'Choose a compatible room slot.')
        fingerprint = json.dumps([kind, item_id, slot_id])
        self.initialise()
        with self.connection() as db:
            old = db.execute('SELECT * FROM commerce_operations WHERE id=?', (oid,)).fetchone()
            if old:
                if old['fingerprint'] != fingerprint:
                    raise GameError(409, 'Request ID was already used for another action.')
                return json.loads(old['result'])
            for table in ('operations', 'quest_answers'):
                if db.execute(f'SELECT 1 FROM {table} WHERE id=?', (oid,)).fetchone():
                    raise GameError(409, 'Request ID was already used for another action.')
            owned = db.execute('SELECT 1 FROM inventory WHERE item_id=?', (item_id,)).fetchone()
            result = {'operation_id': oid, 'kind': kind, 'item_id': item_id, 'charged': 0}
            if kind == 'purchase':
                price = item['price']
                balance = db.execute('SELECT coins FROM wallet WHERE id=1').fetchone()['coins']
                if owned:
                    result['status'] = 'owned'
                elif balance < price:
                    result.update(status='insufficient', needed=price-balance)
                else:
                    db.execute('UPDATE wallet SET coins=coins-? WHERE id=1', (price,))
                    db.execute('INSERT INTO inventory VALUES(?,?,?)', (item_id, singapore_time(time.time()), price))
                    result.update(status='purchased', charged=price)
            else:
                if not owned:
                    raise GameError(409, 'Buy this decoration before placing it.')
                # Move a single owned item; replacing another decoration keeps both owned.
                db.execute('DELETE FROM room WHERE item_id=?', (item_id,))
                db.execute('INSERT INTO room VALUES(?,?) ON CONFLICT(slot_id) DO UPDATE SET item_id=excluded.item_id', (slot_id, item_id))
                result.update(status='placed', slot_id=slot_id)
            db.execute('INSERT INTO commerce_operations VALUES(?,?,?)', (oid, fingerprint, json.dumps(result)))
            return result

    def answer_quest(self, oid, cid, done):
        if cid not in BY_ID or type(done) is not bool:
            raise GameError(422, 'Choose a catalogue quest and Done or Not yet.')
        self.initialise()
        with self.connection() as db:
            if db.execute('SELECT 1 FROM commerce_operations WHERE id=?', (oid,)).fetchone():
                raise GameError(409, 'Request ID was already used for a decoration action.')
            previous = db.execute('SELECT * FROM quest_answers WHERE id=?', (oid,)).fetchone()
            if previous:
                if previous['culture_id'] != cid or bool(previous['done']) != done:
                    raise GameError(409, 'Request ID was already used for another answer.')
                return json.loads(previous['result'])
            if db.execute('SELECT 1 FROM operations WHERE id=?', (oid,)).fetchone():
                raise GameError(409, 'Request ID was already used for a photo operation.')
            quest = db.execute('SELECT * FROM quests WHERE culture_id=?', (cid,)).fetchone()
            if not quest:
                raise GameError(409, 'Discover this culture before completing its quest.')
            result = {'operation_id': oid, 'kind': 'complete', 'culture_id': cid,
                      'quest_id': cid, 'status': 'duplicate' if quest['completed'] else 'not_done',
                      'reward': {'xp': 0, 'coins': 0}, 'completion_method': 'self_reported'}
            if done and not quest['completed']:
                timestamp = singapore_time(time.time())
                db.execute('UPDATE quests SET completed=1,completed_sgt=? WHERE culture_id=?', (timestamp, cid))
                self.reward(db, 'quest:'+cid, QUEST_XP, QUEST_COINS)
                db.execute('UPDATE wallet SET active=CASE WHEN active=? THEN NULL ELSE active END WHERE id=1', (cid,))
                result.update(status='completed', completed_sgt=timestamp,
                              reward={'xp': QUEST_XP, 'coins': QUEST_COINS})
            db.execute('INSERT INTO quest_answers VALUES(?,?,?,?)', (oid, cid, int(done), json.dumps(result)))
            return result

    def state(self):
        self.initialise()
        with self.connection() as db:
            wallet = db.execute('SELECT * FROM wallet WHERE id=1').fetchone()
            rows = db.execute('SELECT * FROM discoveries ORDER BY discovered,culture_id').fetchall()
            quests = db.execute('SELECT * FROM quests').fetchall()
            log = {r['culture_id']: {'time': r['discovered'], 'timestamp_sgt': r['discovered_sgt'], 'hash': r['hash'], 'photo_url': '/api/photos/'+r['photo_id'] if r['photo_id'] else None, 'xp': r['xp'], 'coins': r['coins']} for r in rows}
            details = {r['culture_id']: {'completed': bool(r['completed']), 'completed_sgt': r['completed_sgt'], 'evidence_url': '/api/photos/'+r['evidence_id'] if r['evidence_id'] else None} for r in quests}
            reported = {r['culture_id'] for r in db.execute("SELECT culture_id FROM quest_answers WHERE done=1 AND json_extract(result, '$.status')='completed'")}
            for cid, detail in details.items():
                detail['completion_method'] = ('self_reported' if cid in reported else 'photo_verified' if detail['evidence_url'] else 'legacy') if detail['completed'] else None
            return {'xp': wallet['xp'], 'coins': wallet['coins'], 'active': wallet['active'], 'log': log, 'completed': [r['culture_id'] for r in quests if r['completed']], 'quest_details': details,
                    'inventory': [r['item_id'] for r in db.execute('SELECT item_id FROM inventory ORDER BY purchased_sgt,item_id')],
                    'room': {r['slot_id']: r['item_id'] for r in db.execute('SELECT * FROM room')}}

    @staticmethod
    def operation_result(row):
        result = json.loads(row['result']) if row['result'] else {}
        return {**result, 'operation_id': row['id'], 'status': row['status'], 'kind': row['kind'], 'quest_id': row['target'] if row['kind']=='verify' else None, 'photo_url': '/api/photos/'+row['photo_id']}

    def operation(self, oid):
        if not self.path.exists():
            raise GameError(404, 'Request not found. Choose the photo again.')
        self.initialise()
        with self.connection() as db:
            commerce = db.execute('SELECT result FROM commerce_operations WHERE id=?', (oid,)).fetchone()
            if commerce:
                return json.loads(commerce['result'])
            answer = db.execute('SELECT result FROM quest_answers WHERE id=?', (oid,)).fetchone()
            if answer:
                return json.loads(answer['result'])
            row = db.execute('SELECT * FROM operations WHERE id=?', (oid,)).fetchone()
            if not row:
                raise GameError(404, 'Request not found. You can retry it.')
            result = self.operation_result(row)
            result['retryable'] = row['status'] == 'failed' or (row['status'] == 'pending' and time.time()-row['started'] > LEASE_SECONDS)
            return result

    def begin(self, oid, kind, photo, target=None, source=None):
        self.initialise()
        now, lease = time.time(), str(uuid.uuid4())
        fingerprint = digest(photo) + ':' + kind + ':' + str(target) + ':' + str(source)
        with self.connection() as db:
            if db.execute('SELECT 1 FROM commerce_operations WHERE id=?', (oid,)).fetchone():
                raise GameError(409, 'Request ID was already used for a decoration action.')
            if db.execute('SELECT 1 FROM quest_answers WHERE id=?', (oid,)).fetchone():
                raise GameError(409, 'Request ID was already used for a quest answer.')
            row = db.execute('SELECT * FROM operations WHERE id=?', (oid,)).fetchone()
            if row:
                if row['fingerprint'] != fingerprint:
                    raise GameError(409, 'Request ID was already used for a different photo or quest.')
                if row['status'] != 'failed' and not (row['status'] == 'pending' and now-row['started'] > LEASE_SECONDS):
                    return self.operation_result(row), None
                db.execute("UPDATE operations SET status='pending',result=NULL,started=?,lease=? WHERE id=?", (now, lease, oid))
                return None, lease
            if kind == 'verify':
                quest = db.execute('SELECT * FROM quests WHERE culture_id=?', (target,)).fetchone()
                if not quest:
                    raise GameError(409, 'Discover this culture before verifying its quest.')
                if quest['completed']:
                    return {'operation_id': oid, 'kind': kind, 'status': 'duplicate', 'culture_id': target, 'reward': {'xp': 0, 'coins': 0}}, None
                discovery = db.execute('SELECT hash FROM discoveries WHERE culture_id=?', (target,)).fetchone()
                if discovery['hash'] == digest(photo):
                    raise GameError(409, 'Take a new evidence photo; this is the discovery photo again.')
            if source:
                previous = db.execute('SELECT * FROM operations WHERE id=?', (source,)).fetchone()
                if not previous or previous['kind'] != 'scan' or previous['status'] not in ('candidate', 'uncertain', 'rejected'):
                    raise GameError(409, 'This suggestion can no longer be corrected. Take a new photo.')
                db.execute("UPDATE operations SET status='rejected' WHERE id=?", (source,))
            pid = str(uuid.uuid4())
            db.execute('INSERT INTO photos VALUES(?,?,?,?,?)', (pid, digest(photo), photo, now, singapore_time(now)))
            db.execute('INSERT INTO operations VALUES(?,?,?,?,?,?,?,?,?,?)', (oid, kind, fingerprint, pid, target, source, 'pending', None, now, lease))
            return None, lease

    def retry_request(self, oid):
        self.initialise()
        with self.connection() as db:
            row = db.execute('SELECT o.*,p.jpeg FROM operations o JOIN photos p ON o.photo_id=p.id WHERE o.id=?', (oid,)).fetchone()
            if not row:
                raise GameError(404, 'Request not found. Choose the photo again.')
            return row['kind'], bytes(row['jpeg']), row['target'], row['source']

    def source_photo(self, oid):
        self.initialise()
        with self.connection() as db:
            row = db.execute('SELECT p.jpeg FROM photos p JOIN operations o ON p.id=o.photo_id WHERE o.id=?', (oid,)).fetchone()
            if not row:
                raise GameError(404, 'Original photo not found.')
            return bytes(row['jpeg'])

    def finish(self, oid, lease, result):
        with self.connection() as db:
            row = db.execute('SELECT * FROM operations WHERE id=?', (oid,)).fetchone()
            if row['lease'] != lease or row['status'] != 'pending':
                return self.operation_result(row)
            cid = result.get('culture_id')
            if cid not in [*BY_ID, 'unknown'] or result.get('confidence') not in ('high', 'medium', 'low') or type(result.get('verified')) is not bool or not isinstance(result.get('observation'), str):
                raise GameError(502, 'AI response was invalid. Retry with no reward claimed.')
            high = result['confidence'] == 'high' and cid in BY_ID
            payload = {'culture_id': cid, 'confidence': result['confidence'], 'observation': result['observation'][:500], 'reward': {'xp': 0, 'coins': 0}}
            if row['kind'] == 'scan':
                status = 'candidate' if high and (not row['target'] or row['target'] == cid) else 'uncertain'
            else:
                status = 'rejected'
                if high and result['verified'] and cid == row['target']:
                    changed = db.execute('UPDATE quests SET completed=1,evidence_id=?,completed_sgt=? WHERE culture_id=? AND completed=0', (row['photo_id'], singapore_time(time.time()), cid)).rowcount
                    status = 'verified' if changed else 'duplicate'
                    if changed:
                        self.reward(db, 'quest:'+cid, QUEST_XP, QUEST_COINS)
                        payload['reward'] = {'xp': QUEST_XP, 'coins': QUEST_COINS}
                        db.execute('UPDATE wallet SET active=CASE WHEN active=? THEN NULL ELSE active END WHERE id=1', (cid,))
            db.execute('UPDATE operations SET status=?,result=? WHERE id=?', (status, json.dumps(payload), oid))
            return {**payload, 'operation_id': oid, 'status': status, 'kind': row['kind']}

    def fail(self, oid, lease, message):
        with self.connection() as db:
            db.execute("UPDATE operations SET status='failed',result=? WHERE id=? AND lease=? AND status='pending'", (json.dumps({'message': message}), oid, lease))

    @staticmethod
    def reward(db, event, xp, coins):
        # A unique event plus the balance update lives in the same transaction.
        db.execute('INSERT INTO rewards VALUES(?,?,?,?)', (event, xp, coins, singapore_time(time.time())))
        db.execute('UPDATE wallet SET xp=xp+?,coins=coins+? WHERE id=1', (xp, coins))

    def confirm(self, oid):
        self.initialise()
        with self.connection() as db:
            row = db.execute('SELECT * FROM operations WHERE id=?', (oid,)).fetchone()
            if not row or row['kind'] != 'scan':
                raise GameError(404, 'Suggestion not found.')
            if row['status'] in ('confirmed', 'duplicate'):
                return self.operation_result(row)
            if row['status'] != 'candidate':
                raise GameError(409, 'Only a confident, recognised suggestion can be confirmed.')
            payload = json.loads(row['result'])
            cid = payload['culture_id']
            if cid not in BY_ID:
                raise GameError(409, 'Culture is not in the catalogue.')
            photo = db.execute('SELECT * FROM photos WHERE id=?', (row['photo_id'],)).fetchone()
            fresh = db.execute('INSERT OR IGNORE INTO discoveries VALUES(?,?,?,?,?,?,?)', (cid, photo['id'], photo['hash'], photo['received'], photo['received_sgt'], DISCOVERY_XP, DISCOVERY_COINS)).rowcount
            status = 'confirmed' if fresh else 'duplicate'
            payload['reward'] = {'xp': DISCOVERY_XP if fresh else 0, 'coins': DISCOVERY_COINS if fresh else 0}
            if fresh:
                db.execute('INSERT INTO quests(culture_id) VALUES(?)', (cid,))
                db.execute('UPDATE wallet SET active=? WHERE id=1', (cid,))
                self.reward(db, 'discovery:'+cid, DISCOVERY_XP, DISCOVERY_COINS)
            db.execute('UPDATE operations SET status=?,result=? WHERE id=?', (status, json.dumps(payload), oid))
            return {**payload, 'operation_id': oid, 'status': status, 'kind': 'scan'}

    def activate(self, cid):
        self.initialise()
        with self.connection() as db:
            row = db.execute('SELECT completed FROM quests WHERE culture_id=?', (cid,)).fetchone()
            if not row or row['completed']:
                raise GameError(409, 'Quest is unavailable or already completed.')
            db.execute('UPDATE wallet SET active=? WHERE id=1', (cid,))

    def photo(self, pid):
        self.initialise()
        with self.connection() as db:
            row = db.execute('SELECT jpeg FROM photos WHERE id=?', (pid,)).fetchone()
            if not row:
                raise GameError(404, 'Photo not found.')
            return bytes(row['jpeg'])
