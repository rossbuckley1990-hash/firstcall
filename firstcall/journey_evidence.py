"""Secret-safe captured Codex exec JSONL and customer workspace evidence."""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import stat

from firstcall.agents.codex_live import AgentResult
from firstcall.agents.codex_events import CommandEvidence
from firstcall.repo_security import SECRET_PATTERNS


EXCLUDED_PARTS = {
    '.git', '.cache', '__pycache__', '.pytest_cache', '.mypy_cache',
    '.ruff_cache', '.tox', '.nox', '.venv', 'venv', 'env',
    'node_modules', '.firstcall',
}


class EvidenceSafety:
    """Sanitize before persistence, including JSON-escaped credentials."""

    def __init__(self, *credentials: str):
        self.secrets = sorted({
            encoded
            for value in credentials if value
            for encoded in (
                value.encode(), json.dumps(value)[1:-1].encode(),
                json.dumps(value, ensure_ascii=False)[1:-1].encode(),
            )
        }, key=len, reverse=True)
        self.redacted: set[str] = set()

    def clean(self, data: bytes, location: str) -> bytes:
        original = data
        for secret in self.secrets:
            data = data.replace(secret, b'[REDACTED]')
        # Reuse the repository scanner's patterns directly: its directory
        # exclusions intentionally skip artifacts, so scan_repository alone
        # cannot protect journey evidence.
        for pattern in SECRET_PATTERNS:
            data = pattern.sub(b'[REDACTED_CREDENTIAL]', data)
        self.check(data)
        if data != original:
            self.redacted.add(location)
        return data

    def check(self, data: bytes) -> None:
        if any(value in data for value in self.secrets) or any(
            pattern.search(data) for pattern in SECRET_PATTERNS
        ):
            raise RuntimeError('evidence_integrity: blocked unsafe credential material')

    def object(self, value, location: str):
        if isinstance(value, str):
            return self.clean(value.encode(), location).decode()
        if isinstance(value, dict):
            result = {}
            for key, child in value.items():
                safe_key = self.object(key, location)
                if safe_key in result:
                    raise RuntimeError('evidence_integrity: redacted key collision')
                result[safe_key] = self.object(child, location)
            return result
        if isinstance(value, (list, tuple)):
            return [self.object(child, location) for child in value]
        return value

    def integrity(self) -> dict:
        return {
            'status': 'redacted' if self.redacted else 'clean',
            'redacted_locations': sorted(self.redacted),
            'checks': ['exact_agent_credential', 'exact_verifier_credential',
                       'repository_secret_patterns'],
        }


def workspace_files(root: Path):
    """Yield sorted regular files only; never traverse or read symlinks."""
    paths = []
    for parent, directories, files in os.walk(root, followlinks=False):
        base = Path(parent)
        directories[:] = sorted(
            name for name in directories
            if name not in EXCLUDED_PARTS
            and not (base / name).is_symlink()
            and not (base / name / 'pyvenv.cfg').exists()
        )
        for name in files:
            path = base / name
            if name in EXCLUDED_PARTS or path.suffix in {'.pyc', '.pyo'}:
                continue
            if not stat.S_ISREG(path.lstat().st_mode):
                continue
            paths.append(path)
    for path in sorted(paths, key=lambda p: p.relative_to(root).as_posix()):
        # Codex has returned before inspection. O_NOFOLLOW additionally
        # prevents opening a file symlink if the entry changes meanwhile.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            yield path.relative_to(root).as_posix(), stream.read()


def capture_journey(
    root: Path,
    destination: Path,
    agent: AgentResult,
    commands: tuple[CommandEvidence, ...],
    safety: EvidenceSafety,
) -> tuple[dict, dict[str, str], list[str], list[dict]]:
    """Persist safe evidence before the caller cleans up the workspace.

    Manifest size/hash describe observed bytes; persisted_size/sha256
    describe the safe copy. These can differ when redaction is necessary.
    All symlinks (including internal ones) are excluded deliberately.
    """
    destination.mkdir(parents=True, exist_ok=False)
    files = []

    def write(relative: str, data: bytes):
        safe = safety.clean(data, relative)
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(safe)
        files.append({'path': relative, 'sha256': sha256(safe).hexdigest(),
                      'bytes': len(safe),
                      'evidence_integrity': 'redacted' if relative in safety.redacted else 'clean'})
        return safe

    write('codex.stdout.jsonl', agent.stdout.encode())
    write('codex.stderr.txt', agent.stderr.encode())
    safe_commands = safety.object([asdict(c) for c in commands], 'candidate-commands.json')
    write('candidate-commands.json', json.dumps(safe_commands, indent=2, sort_keys=True).encode())
    manifest = []
    generated = {}
    forbidden = []
    for name, data in workspace_files(root):
        safe_name = safety.clean(name.encode(), 'workspace_paths').decode()
        entry = {'path': safe_name, 'bytes': len(data), 'sha256': sha256(data).hexdigest()}
        # Do not let a credential-bearing filename create unsafe paths or
        # ambiguous collisions. Its contents remain observed in the manifest.
        if safe_name != name:
            entry['evidence_integrity'] = 'omitted_unsafe_path'
            manifest.append(entry)
            continue
        relative = 'workspace/' + name
        safe = write(relative, data)
        entry.update(persisted_path=relative, persisted_bytes=len(safe),
                     persisted_sha256=sha256(safe).hexdigest(),
                     evidence_integrity='redacted' if safe != data else 'clean')
        manifest.append(entry)
        if any(part == '.env' or part.startswith('.env.') for part in Path(name).parts):
            forbidden.append(name)
        try:
            generated[name] = safe.decode('utf-8')
        except UnicodeDecodeError:
            pass
    manifest.sort(key=lambda entry: entry['path'])
    write('workspace-manifest.json', json.dumps(manifest, indent=2, sort_keys=True).encode())
    # Preserve the capture outcome even if vendor verification later fails.
    write('evidence-integrity.json', json.dumps(safety.integrity(), indent=2, sort_keys=True).encode())
    journey = {
        'description': 'captured Codex exec JSONL',
        'files': sorted(files, key=lambda entry: entry['path']),
        'workspace_exclusions': sorted(EXCLUDED_PARTS | {'*.pyc', '*.pyo', 'symlinks', 'virtual environments'}),
        'evidence_integrity': safety.integrity(),
    }
    return journey, generated, forbidden, manifest
