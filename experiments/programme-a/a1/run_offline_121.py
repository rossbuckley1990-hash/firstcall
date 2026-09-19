#!/usr/bin/env python3
"""Run inside sandbox-exec network deny with offline/sitecustomize on PYTHONPATH.
No --retrieve, live inputs or generated sampling entropy. Reports only; no freeze edits.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
A1 = ROOT / 'experiments/programme-a/a1'

def main():
    if os.environ.get('FIRSTCALL_OFFLINE_GUARD_ACTIVE') != '1':
        raise SystemExit('early offline guard required')
    suites = ['test_d8.py', 'test_hostile_121.py', 'registrations/test_registrations.py',
              'registrations/test_record_seal.py', 'test_a1.py']
    results = []
    for suite in suites:
        p = subprocess.run([sys.executable, '-B', str(A1 / suite)], cwd=ROOT, capture_output=True, text=True)
        print(suite + ':\n' + p.stdout + p.stderr, flush=True)
        results.append({'suite': suite, 'returncode': p.returncode, 'output': p.stdout + p.stderr})
    # The frozen validator runs Freeze-1.1 tests/applicator in an unchanged local clone,
    # copies only the five registered helpers, and verifies every historical digest.
    p = subprocess.run([sys.executable, '-B', str(A1 / 'registrations/validate_registrations.py'), '--write'],
                       cwd=ROOT, capture_output=True, text=True)
    print('registration/integrity validation:\n' + p.stdout + p.stderr, flush=True)
    results.append({'suite': 'registration/integrity validation (includes Freeze-1.1 tests)', 'returncode': p.returncode, 'output': p.stdout + p.stderr})
    # All repository JSON, including historical files, syntax only: do not display values.
    paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    invalid, count = [], 0
    for name in sorted(set(paths)):
        if name.endswith('.json'):
            count += 1
            try: json.loads((ROOT / name).read_bytes())
            except Exception as exc: invalid.append({'path': name, 'error': str(exc)})
    report = {'schema': 'firstcall.freeze121.offline_validation.v1', 'network': 'OS sandbox deny network*; no network probes',
              'entropy': 'experiment entropy forbidden; fixed synthetic seeds and scratch names; runtime internals not claimed entropy-free',
              'suites': results, 'json_files': count, 'invalid_json': invalid,
              'pass': not invalid and all(x['returncode'] == 0 for x in results)}
    (A1 / 'offline-validation-121.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['pass'] else 1

if __name__ == '__main__': sys.exit(main())
