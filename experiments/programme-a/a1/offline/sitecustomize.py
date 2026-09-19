"""Test-only early guard, inherited by child Python processes via PYTHONPATH.
Run beneath sandbox-exec deny network*. Fixed fixtures only; never use for A1 entropy.
"""
import os
import sys

def banned(*args, **kwargs):
    raise RuntimeError('OFFLINE_GUARD: network/entropy forbidden')

os.urandom = banned
if hasattr(os, 'getrandom'): os.getrandom = banned
# Stop Python's module-global Random from implicitly requesting OS entropy.
import _random
_Base = _random.Random
class _DeterministicStartup(_Base):
    def seed(self, value=None):
        return super().seed(0 if value is None else value)
_random.Random = _DeterministicStartup
import random
_original_seed = random.Random.seed

def seeded_only(self, value=None, version=2):
    if value is None: banned()
    return _original_seed(self, value, version)
random.Random.seed = seeded_only
random.seed = banned
random._urandom = banned
# Scratch filenames are deterministic test plumbing, not sampling entropy.
import tempfile
class _ScratchRandom(random.Random):
    def __init__(self): super().__init__(0)
tempfile._Random = _ScratchRandom
# Every process draws the same name sequence and Python 3.14 tries only TMP_MAX (20)
# names per call, so fixtures leaked into a shared temp dir (frozen test_a1 never
# removes its mkdtemp dirs) exhaust it. Give each process its own empty root, claimed
# by atomic mkdir on a counter (no entropy), and remove it at exit.
import atexit
import shutil
_scratch_base = tempfile.gettempdir()
_n = 0
while True:
    _scratch_root = os.path.join(_scratch_base, 'firstcall-offline-%d' % _n)
    try:
        os.mkdir(_scratch_root, 0o700)
        break
    except FileExistsError:
        _n += 1
tempfile.tempdir = _scratch_root
_scratch_pid = os.getpid()
def _remove_scratch():
    if os.getpid() == _scratch_pid: shutil.rmtree(_scratch_root, True)
atexit.register(_remove_scratch)
import socket
for attr in ('create_connection', 'getaddrinfo', 'gethostbyname', 'gethostbyname_ex'):
    setattr(socket, attr, banned)
for attr in ('connect', 'connect_ex', 'sendto'):
    setattr(socket.socket, attr, banned)

def audit(event, args):
    if event.startswith('socket.') and event not in ('socket.__new__',): banned()
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path = os.fsdecode(args[0])
        if '/experiments/programme-a/a1/snapshot/' in path or '/artifacts/programme-a/' in path:
            raise RuntimeError('OFFLINE_GUARD: A1 data access forbidden')
sys.addaudithook(audit)
os.environ['FIRSTCALL_OFFLINE_GUARD_ACTIVE'] = '1'
