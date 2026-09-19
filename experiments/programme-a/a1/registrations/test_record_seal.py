#!/usr/bin/env python3
"""Synthetic store tests. Fixture IDs are not human registrations."""
import concurrent.futures
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import record_seal as s

ROSTER = [{'role': 'R05', 'id': 'synthetic-one', 'kind': 'SYNTHETIC_TEST_ONLY'},
          {'role': 'R06', 'id': 'synthetic-two', 'kind': 'SYNTHETIC_TEST_ONLY'}]
T = '2026-09-19T00:00:00Z'

class SealTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'store'
        self.store = s.Store.create(self.path, ROSTER, synthetic=True)
        self.store.declare_block('synthetic-block', ['synthetic-rdg'])

    def seal(self, actor='synthetic-one', decision=None, rdg='synthetic-rdg'):
        return self.store.seal('synthetic-block', actor, rdg, 'a' * 64, decision or {'code': 'YES'}, T)

    def test_isolation_and_disagreement(self):
        with self.assertRaises(s.SealError): self.store.reveal('synthetic-block')
        self.assertEqual(self.seal(), {'sealed': True})
        with self.assertRaises(s.SealError): self.store.reveal('synthetic-block')
        self.seal('synthetic-two', {'code': 'UNRESOLVED'})
        out = self.store.reveal('synthetic-block')
        self.assertEqual(len(out['records']), 2)
        self.assertEqual(out['disagreements'], ['synthetic-rdg'])
        self.assertEqual(self.store.reveal('synthetic-block'), out)
        for e in out['records']:
            self.assertEqual(e['decision_digest'], s.sha(s.canonical(e['decision'])))
            for k in ('schema', 'block', 'adjudicator', 'rdg', 'evidence_digest', 'timestamp'): self.assertIn(k, e)

    def test_entire_block_required(self):
        self.store.declare_block('second', ['synthetic-a', 'synthetic-b'])
        for actor in ('synthetic-one', 'synthetic-two'):
            self.store.seal('second', actor, 'synthetic-a', 'a' * 64, {'code': 'YES'}, T)
        with self.assertRaises(s.SealError): self.store.reveal('second')

    def test_duplicate_overwrite_unknown_actor(self):
        self.seal()
        point = self.store.verify()
        for actor, rdg in [('synthetic-one', 'synthetic-rdg'), ('not-registered', 'synthetic-rdg'), ('synthetic-two', 'not-declared')]:
            with self.assertRaises(s.SealError): self.seal(actor, rdg=rdg)
        with self.assertRaises(FileExistsError): s.Store.create(self.path, ROSTER, synthetic=True)
        with self.assertRaises(s.SealError): self.store.declare_block('synthetic-block', ['other'])
        self.assertEqual(self.store.verify(), point)

    def test_append_only_sql_controls(self):
        con = sqlite3.connect(self.store.db)
        try:
            for sql in ('UPDATE events SET previous="x"', 'DELETE FROM events'):
                with self.assertRaises(sqlite3.IntegrityError): con.execute(sql)
        finally: con.close()

    def test_tamper_and_checkpoint(self):
        point = self.store.verify()
        with self.assertRaises(s.SealError): self.store.verify(dict(point, sha256='f' * 64))
        self.seal()
        self.store.verify(point)
        con = sqlite3.connect(self.store.db)
        con.execute('DROP TRIGGER no_update')
        con.execute('UPDATE events SET digest=? WHERE seq=3', ('f' * 64,))
        con.execute("CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'append-only'); END")
        con.commit(); con.close()
        with self.assertRaises(s.SealError): self.store.verify()
        with self.assertRaises(s.SealError): self.store.reveal('synthetic-block')

    def test_distinct_real_humans_required(self):
        for roster in ([], [ROSTER[0]], [ROSTER[0], ROSTER[0]]):
            with self.assertRaises(s.SealError): s.Store.create(Path(self.tmp.name) / 'other', roster, synthetic=True)
        with self.assertRaises(s.SealError): s.Store.create(Path(self.tmp.name) / 'other', ROSTER)
        with self.assertRaises(s.SealError): s.validate_roster([dict(r, kind='agent') for r in ROSTER], False)

    def test_permissions_and_bad_records(self):
        for stamp in ('2026-02-31T00:00:00Z', 'yesterday'):
            with self.assertRaises(s.SealError): self.store.seal('synthetic-block', 'synthetic-one', 'synthetic-rdg', 'a'*64, {'code':'YES'}, stamp)
        with self.assertRaises(s.SealError): self.store.seal('synthetic-block', 'synthetic-one', 'synthetic-rdg', 'bad', {'code':'YES'}, T)
        os.chmod(self.path, 0o755)
        with self.assertRaises(s.SealError): s.Store(self.path)
        os.chmod(self.path, 0o700)

    def test_crash_recovery_before_commit(self):
        point = self.store.verify()
        code = """import os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import record_seal as s
store=s.Store(sys.argv[2]); con=store._connect(); state=store._state(con)
store._append(con,state,{'type':'block','block':'crash-uncommitted','rdgs':['synthetic-rdg']})
os._exit(23)
"""
        proc = subprocess.run([sys.executable, '-B', '-c', code, str(Path(s.__file__).parent), str(self.path)])
        self.assertEqual(proc.returncode, 23)
        self.assertEqual(s.Store(self.path).verify(), point)
        self.seal(); self.seal('synthetic-two')
        self.assertEqual(len(self.store.reveal('synthetic-block')['records']), 2)

    def test_duplicate_race(self):
        def attempt(_):
            try: self.seal(); return 'OK'
            except s.SealError: return 'DUPLICATE'
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(attempt, range(2))), ['DUPLICATE', 'OK'])
        self.store.verify()

    def test_reveal_seal_race(self):
        self.seal()
        def reveal():
            try: return self.store.reveal('synthetic-block')
            except s.SealError: return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(reveal); b = pool.submit(self.seal, 'synthetic-two')
            out = a.result(); b.result()
        if out is not None: self.assertEqual(len(out['records']), 2)
        self.assertEqual(len(self.store.reveal('synthetic-block')['records']), 2)

    def test_crash_after_commit_duplicate_retry_rejected(self):
        code = "import sys,os; sys.path.insert(0,sys.argv[1]); import record_seal as s; s.Store(sys.argv[2]).seal('synthetic-block','synthetic-one','synthetic-rdg','a'*64,{'code':'YES'},'2026-09-19T00:00:00Z'); os._exit(24)"
        p = subprocess.run([sys.executable, '-B', '-c', code, str(Path(s.__file__).parent), str(self.path)])
        self.assertEqual(p.returncode, 24)
        with self.assertRaises(s.SealError): self.seal()
        self.store.verify()

    def test_trigger_tamper_without_payload_change(self):
        con = sqlite3.connect(self.store.db)
        con.execute('DROP TRIGGER no_update')
        con.execute('CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT 1; END')
        con.commit(); con.close()
        with self.assertRaises(s.SealError): self.store.verify()

    def test_rollback_against_retained_checkpoint(self):
        self.seal(); checkpoint = self.store.verify()
        con = sqlite3.connect(self.store.db)
        con.execute('DROP TRIGGER no_delete')
        con.execute('DELETE FROM events WHERE seq=3')
        con.execute("CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'append-only'); END")
        con.commit(); con.close()
        with self.assertRaises(s.SealError): self.store.verify(checkpoint)

    def test_b_first_wrong_block_malformed_and_body_tamper(self):
        self.assertEqual(self.seal('synthetic-two'), {'sealed': True})
        with self.assertRaises(s.SealError): self.store.reveal('synthetic-block')
        with self.assertRaises(s.SealError):
            self.store.seal('undeclared-block', 'synthetic-one', 'synthetic-rdg', 'a' * 64, {'code': 'YES'}, T)
        for decision in ({}, [], 'YES', None):
            with self.assertRaises(s.SealError):
                self.store.seal('synthetic-block', 'synthetic-one', 'synthetic-rdg', 'a' * 64, decision, T)
        with self.assertRaises(ValueError):
            self.store.seal('synthetic-block', 'synthetic-one', 'synthetic-rdg', 'a' * 64, {'p': float('nan')}, T)
        self.seal()
        for field, value in (('evidence_digest', 'b' * 64), ('decision', {'code': 'NO'})):
            copy = Path(self.tmp.name) / ('tamper-' + field)
            copy.mkdir(mode=0o700)
            (copy / 'sealed.sqlite3').write_bytes(self.store.db.read_bytes())
            os.chmod(copy / 'sealed.sqlite3', 0o600)
            con = sqlite3.connect(copy / 'sealed.sqlite3')
            con.execute('DROP TRIGGER no_update')
            body = json.loads(con.execute('SELECT body FROM events WHERE seq=3').fetchone()[0])
            body[field] = value
            con.execute('UPDATE events SET body=? WHERE seq=3', (s.canonical(body),))
            con.execute("CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'append-only'); END")
            con.commit(); con.close()
            with self.assertRaises(s.SealError): s.Store(copy).verify()
            with self.assertRaises(s.SealError): s.Store(copy).reveal('synthetic-block')
        self.assertEqual(len(self.store.reveal('synthetic-block')['records']), 2)

    def test_deterministic_verification(self):
        self.seal()
        self.assertEqual(self.store.verify(), s.Store(self.path).verify())

if __name__ == '__main__': unittest.main()
