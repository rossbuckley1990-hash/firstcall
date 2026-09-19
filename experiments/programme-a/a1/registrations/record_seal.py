#!/usr/bin/env python3
"""Custodian-owned dual-human seal store, v1.0.0. Offline; no entropy.

Participants never receive filesystem/SQL/Python access to the custodian store.
The trusted custodian authenticates each human outside this library and passes that
identity; ID strings are NOT authentication. Neither participant receives verification
checkpoints, payloads or decision hashes until the WHOLE declared block is sealed.
SQLite FULL synchronous transactions serialize seal/reveal and recover interrupted
writes. Hash chaining and append-only SQL triggers detect accidental tamper; retained
external checkpoints detect rollback. A malicious custodian/admin can read/rewrite
plaintext and is outside the guarantee. No encryption, signatures or trusted clock.
"""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

SCHEMA = 'firstcall.dual_human_seals.v1'
HEX = re.compile(r'^[0-9a-f]{64}$')
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}$')
ZERO = '0' * 64

class SealError(ValueError):
    pass

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')

def sha(value):
    return hashlib.sha256(value).hexdigest()

def check_id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise SealError('invalid ID')

def check_time(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        raise SealError('UTC timestamp required')
    try:
        datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError as exc:
        raise SealError('invalid timestamp') from exc

def roster_from_anchor(repo, commit, path):
    """Load a real, prospectively anchored roster; only local Git objects are read.
    A separate signed human registration is needed for each role. This verifies
    the anchored attestations, not whether a person lied or a signature is genuine.
    """
    if not re.fullmatch(r'[0-9a-f]{40}', commit) or path.startswith('-') or '..' in Path(path).parts:
        raise SealError('invalid registration reference')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args])
    # Registered anchor must already be in the locally attested origin branch.
    if subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', commit, 'refs/remotes/origin/v0.2-real-agent'], capture_output=True).returncode:
        raise SealError('registration not on attested origin branch')
    tags = git('tag', '--points-at', commit).decode().splitlines()
    if not any(git('cat-file', '-t', 'refs/tags/' + tag).strip() == b'tag' for tag in tags):
        raise SealError('annotated registration anchor required')
    raw = git('show', commit + ':' + path)
    roster = json.loads(raw)
    validate_roster(roster, synthetic=False)
    return {'roster': roster, 'anchor_commit': commit, 'anchor_path': path, 'registration_sha256': sha(raw)}

def validate_roster(roster, synthetic):
    if not isinstance(roster, list) or len(roster) != 2:
        raise SealError('exactly two preregistered adjudicators required')
    if {r.get('role') for r in roster} != {'R05', 'R06'}:
        raise SealError('R05 and R06 required')
    for r in roster:
        check_id(r.get('id'))
        if synthetic:
            if r.get('kind') != 'SYNTHETIC_TEST_ONLY' or not r['id'].startswith('synthetic-'):
                raise SealError('synthetic fixtures only')
        elif r.get('kind') != 'human' or r.get('status') != 'FILLED' or not all(isinstance(r.get(k), str) and r[k].strip() for k in ('full_name', 'signature', 'independence_attestation')):
            raise SealError('signed human registrations required')
    if len({r['id'] for r in roster}) != 2:
        raise SealError('distinct adjudicators required')
    if not synthetic and len({' '.join(r['full_name'].casefold().split()) for r in roster}) != 2:
        raise SealError('distinct humans required')

class Store:
    @classmethod
    def create(cls, directory, roster, *, synthetic=False, registration=None):
        validate_roster(roster, synthetic)
        if not synthetic:
            if not registration or registration.get('roster') != roster:
                raise SealError('use create_from_anchor for human registrations')
            # Caller cannot fabricate a dictionary as proof of an anchor.
            raise SealError('use create_from_anchor for human registrations')
        return cls._create(directory, roster, {'synthetic': True})

    @classmethod
    def create_from_anchor(cls, directory, repo, commit, path):
        registration = roster_from_anchor(repo, commit, path)
        return cls._create(directory, registration['roster'], registration)

    @classmethod
    def _create(cls, directory, roster, registration):
        directory = Path(directory)
        directory.mkdir(mode=0o700, parents=False, exist_ok=False)
        db = directory / 'sealed.sqlite3'
        fd = os.open(db, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        con = sqlite3.connect(db, isolation_level=None)
        try:
            con.execute('PRAGMA journal_mode=WAL')
            con.execute('PRAGMA synchronous=FULL')
            con.executescript("""
            BEGIN IMMEDIATE;
            CREATE TABLE events (seq INTEGER PRIMARY KEY, body BLOB NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL);
            CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'append-only'); END;
            CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'append-only'); END;
            """)
            body = canonical({'schema': SCHEMA, 'type': 'init', 'roster': roster, 'registration': registration})
            con.execute('INSERT INTO events VALUES (1, ?, ?, ?)', (body, ZERO, sha(ZERO.encode() + body)))
            con.execute('COMMIT')
        finally:
            con.close()
        # Persist directory entries as well as SQLite's transaction.
        fd = os.open(directory, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
        fd = os.open(directory.parent, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
        return cls(directory)

    def __init__(self, directory):
        self.directory = Path(directory)
        self.db = self.directory / 'sealed.sqlite3'
        if not self.db.is_file() or self.db.is_symlink() or self.directory.is_symlink():
            raise SealError('missing or unsafe store')
        if self.directory.stat().st_mode & 0o077 or self.db.stat().st_mode & 0o077:
            raise SealError('custodian-only permissions required')

    def _connect(self):
        con = sqlite3.connect('file:' + str(self.db.resolve()) + '?mode=rw', uri=True, isolation_level=None, timeout=10)
        con.execute('PRAGMA synchronous=FULL')
        con.execute('BEGIN IMMEDIATE')
        return con

    def _state(self, con):
        if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise SealError('database corruption')
        triggers = {r[0]: ' '.join(r[1].split()).rstrip(';') for r in con.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")}
        expected = {f'no_{op}': f"CREATE TRIGGER no_{op} BEFORE {op.upper()} ON events BEGIN SELECT RAISE(ABORT, 'append-only'); END" for op in ('update', 'delete')}
        if triggers != expected:
            raise SealError('append-only controls changed')
        previous, count, init, blocks = ZERO, 0, None, {}
        for seq, body, prev, digest in con.execute('SELECT seq, body, previous, digest FROM events ORDER BY seq'):
            count += 1
            if seq != count or prev != previous or sha(prev.encode() + body) != digest:
                raise SealError('tampered event chain')
            e = json.loads(body)
            if canonical(e) != body or e.get('schema') != SCHEMA:
                raise SealError('noncanonical event')
            previous = digest
            if count == 1:
                if e.get('type') != 'init': raise SealError('missing registration')
                init = e
                validate_roster(e['roster'], e['registration'].get('synthetic', False))
                actors = {r['id'] for r in e['roster']}
                continue
            typ, block = e.get('type'), e.get('block')
            check_id(block)
            if typ == 'block':
                if block in blocks or not e['rdgs'] or len(set(e['rdgs'])) != len(e['rdgs']):
                    raise SealError('duplicate or empty block')
                for rdg in e['rdgs']: check_id(rdg)
                blocks[block] = {'rdgs': e['rdgs'], 'records': {}, 'revealed': False}
            elif typ in ('seal', 'reveal'):
                if block not in blocks: raise SealError('unknown block')
                b = blocks[block]
                if typ == 'seal':
                    actor, rdg = e['adjudicator'], e['rdg']
                    if actor not in actors or rdg not in b['rdgs'] or (actor, rdg) in b['records'] or b['revealed']:
                        raise SealError('invalid or duplicate seal')
                    check_time(e['timestamp'])
                    if not HEX.fullmatch(e['evidence_digest']) or e['decision_digest'] != sha(canonical(e['decision'])):
                        raise SealError('record digest mismatch')
                    b['records'][actor, rdg] = e
                else:
                    if b['revealed'] or len(b['records']) != 2 * len(b['rdgs']):
                        raise SealError('premature or duplicate reveal')
                    b['revealed'] = True
            else:
                raise SealError('unexpected event')
        if init is None: raise SealError('uninitialised store')
        return {'init': init, 'blocks': blocks, 'count': count, 'digest': previous}

    def _append(self, con, state, event):
        body = canonical(dict(event, schema=SCHEMA))
        con.execute('INSERT INTO events VALUES (?, ?, ?, ?)',
                    (state['count'] + 1, body, state['digest'], sha(state['digest'].encode() + body)))

    def _transaction(self, operation):
        con = self._connect()
        try:
            result = operation(con, self._state(con))
            self._state(con)  # validate proposed event before committing
            con.execute('COMMIT')
            return result
        except BaseException:
            con.execute('ROLLBACK')
            raise
        finally:
            con.close()

    def declare_block(self, block, rdgs):
        def op(con, state):
            self._append(con, state, {'type': 'block', 'block': block, 'rdgs': sorted(rdgs)})
        return self._transaction(op)

    def seal(self, block, adjudicator, rdg, evidence_digest, decision, timestamp):
        if not isinstance(decision, dict) or not decision:
            raise SealError('decision object required')
        def op(con, state):
            self._append(con, state, {'type': 'seal', 'block': block, 'adjudicator': adjudicator, 'rdg': rdg,
                                     'evidence_digest': evidence_digest, 'decision': decision,
                                     'decision_digest': sha(canonical(decision)), 'timestamp': timestamp})
            return {'sealed': True}  # no decision or hash leakage
        return self._transaction(op)

    def reveal(self, block):
        def op(con, state):
            if block not in state['blocks']: raise SealError('unknown block')
            b = state['blocks'][block]
            if len(b['records']) != 2 * len(b['rdgs']): raise SealError('both complete blocks must be sealed')
            if not b['revealed']:
                self._append(con, state, {'type': 'reveal', 'block': block})
            return {'schema': SCHEMA, 'block': block, 'records': [b['records'][k] for k in sorted(b['records'])],
                    'disagreements': [r for r in b['rdgs'] if len({canonical(e['decision']) for (a, x), e in b['records'].items() if x == r}) > 1]}
        return self._transaction(op)

    def verify(self, expected_checkpoint=None):
        """Custodian/auditor only. Do not give checkpoints to blinded participants."""
        def op(con, state):
            checkpoint = {'events': state['count'], 'sha256': state['digest']}
            if expected_checkpoint is not None:
                seq = expected_checkpoint['events']
                row = con.execute('SELECT digest FROM events WHERE seq=?', (seq,)).fetchone()
                if not row or row[0] != expected_checkpoint['sha256']:
                    raise SealError('rollback or checkpoint mismatch')
            return checkpoint
        return self._transaction(op)
