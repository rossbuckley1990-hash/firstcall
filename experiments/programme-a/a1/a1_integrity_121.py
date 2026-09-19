"""Read-only integrity check for additive Freeze 1.2.1 machinery."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'experiments/programme-a/amendments/freeze-1.2.1.json'

def verify_package():
    doc = json.loads(MANIFEST.read_bytes())
    for rel, expected in doc['registered_file_sha256'].items():
        p = ROOT / rel
        if not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Freeze 1.2.1 dependency drift: ' + rel)
    return True

# Importing operative code verifies all registered bytes before use.
VERIFIED = verify_package()
