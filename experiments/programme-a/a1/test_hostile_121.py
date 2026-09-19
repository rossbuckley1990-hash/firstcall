#!/usr/bin/env python3
"""Hostile structural, dependency and translation tests, synthetic only."""
import ast
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / 'registrations')]
import a1_e2_leads as e2
import a1_frame_121 as frame
import a1_host as host
import a1_integrity_121 as integrity
import translation_policy as translation
import validate_registrations as registrations

class HostileTests(unittest.TestCase):
    def test_frame_ast_scope(self):
        self.assertEqual(registrations.check_frame_scope(), [])

    def test_actual_frame_grouping(self):
        # Reuse frozen synthetic Git builder; no real snapshot read.
        import test_a1 as old_tests
        original = old_tests.fr
        old_tests.fr = frame
        try:
            f = old_tests.frame_for(['straße.de', 'xn--strae-oqa.de', 'strasse.de'])
            self.assertEqual(f['G'], ['strasse.de', 'xn--strae-oqa.de'])
            g = next(x for x in f['groups'] if x['rdg'] == 'xn--strae-oqa.de')
            self.assertEqual(len(g['keys']), 2)
            self.assertEqual(set(g['hosts'].values()), {'xn--strae-oqa.de'})
        finally: old_tests.fr = original

    def test_full_pinned_psl(self):
        p = frame.PublicSuffixList(frame.load_pinned_psl().decode())
        self.assertEqual(p.registrable_domain(host.canonical_host('straße.de')), 'xn--strae-oqa.de')

    def test_query_order_and_percent_ambiguity(self):
        for raw, expected in [('https://x.com/?a=z&a=&a', 'https://x.com/?a&a=&a=z'),
                              ('https://x.com/a%252f', 'https://x.com/a%252f'),
                              ('https://x.com/a/%2e%2e/b///', 'https://x.com/b'),
                              ('https://x.com/?é=ü', 'https://x.com/?%C3%A9=%C3%BC')]:
            self.assertEqual(e2.normalise_lead(raw), (expected, None))
            self.assertEqual(e2.normalise_lead(expected), (expected, None))

    def test_manifest_tamper_rejected(self):
        original = integrity.MANIFEST
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'manifest.json'
            doc = json.loads(original.read_bytes())
            doc['registered_file_sha256']['experiments/programme-a/a1/a1_host.py'] = '0' * 64
            p.write_text(json.dumps(doc)); integrity.MANIFEST = p
            try:
                with self.assertRaises(RuntimeError): integrity.verify_package()
            finally: integrity.MANIFEST = original
        integrity.verify_package()

    def test_idna_pin_and_module_origin(self):
        host._verify_idna()
        self.assertEqual(host.idna.__version__, '3.11')
        self.assertEqual(host.idna.idnadata.__version__, '16.0.0')
        for name, module in list(sys.modules.items()):
            if name == 'idna' or name.startswith('idna.'):
                self.assertTrue(Path(module.__file__).resolve().is_relative_to(host.VENDOR_IDNA.resolve()))

    def test_translation_never_negative(self):
        self.assertEqual(translation.evidence_requirement(required_predicate_has_english_support=False),
                         {'translation': None, 'code': 'UNRESOLVED', 'reason': 'TRANSLATION_NOT_AVAILABLE'})
        self.assertIsNone(translation.evidence_requirement(required_predicate_has_english_support=True)['code'])
        with self.assertRaises(ValueError): translation.evidence_requirement(required_predicate_has_english_support='yes')

    def test_dns_octet_limits(self):
        maximum = '.'.join(['a'*63]*3 + ['a'*61])
        self.assertEqual(len(maximum), 253)
        self.assertEqual(host.canonical_host(maximum), maximum)
        for bad in (maximum + 'a', 'a'*64 + '.example', 'x..example', 'xn--.example'):
            with self.assertRaises(host.HostError): host.canonical_host(bad)

    def test_registration_schema_rejects_drift(self):
        schema = registrations.load('registration-record.schema.json')
        doc = registrations.load('R17-spec-parser.json')
        self.assertEqual(registrations.schema_errors(doc, schema), [])
        for key, bad in [('status', 'FILLED'), ('version', 121), ('digests', {'parser': 'not-a-digest'}), ('anchor_parent', {})]:
            broken = dict(doc, **{key: bad})
            self.assertTrue(registrations.schema_errors(broken, schema), key)

    def test_early_guard(self):
        self.assertEqual(os.environ.get('FIRSTCALL_OFFLINE_GUARD_ACTIVE'), '1')
        with self.assertRaises(RuntimeError): os.urandom(1)
        import random
        with self.assertRaises(RuntimeError): random.Random()

    def test_guard_scratch_survives_leaked_deterministic_names(self):
        # Regression: leaked fixtures holding all TMP_MAX guard names made mkdtemp fail.
        import subprocess
        base = Path(tempfile.mkdtemp())
        names = tempfile._RandomNameSequence()
        for _ in range(max(tempfile.TMP_MAX, 20)): (base / ('tmp' + next(names))).mkdir()
        child = ('import tempfile\nfor _ in range(30): tempfile.mkdtemp()\n'
                 'print(tempfile.gettempdir())')
        env = dict(os.environ, TMPDIR=str(base))
        p = subprocess.run([sys.executable, '-B', '-c', child], env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        root = Path(p.stdout.strip())
        self.assertEqual(root.parent.resolve(), base.resolve())
        self.assertNotEqual(root, Path(tempfile.gettempdir()))
        self.assertFalse(root.exists())

if __name__ == '__main__': unittest.main()
