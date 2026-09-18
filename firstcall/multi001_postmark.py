"""MULTI-001 baseline; explicit invocation: python -m firstcall.multi001_postmark --execute.

Each fresh workspace receives the exact pinned official onboarding snapshot.
Importing this module does no live work.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re

from firstcall.agents.codex_events import extract_codex_evidence, extract_completed_commands
from firstcall.agents.codex_live import AgentResult, CodexLiveRunner
from firstcall.grade import grade
from firstcall.journey_evidence import EvidenceSafety, capture_journey
from firstcall.model import Execution, HygieneFinding, Outcome, Verification
from firstcall.postmark_preflight import inspect_server
from firstcall.resend001 import (
    digest, file_sha256, git_output, new_execution_nonce, tracked_repo_dirty, utc_now,
)
from firstcall.runtime.workspace import create_workspace
from firstcall.stats import afcr
from firstcall.verifiers.postmark import PostmarkVerifier

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / 'experiments/multi-001'
OUT = ROOT / 'artifacts/multi-001/postmark/baseline'
RUN_IDS = ('R01', 'R02', 'R03')
ONBOARDING_SHA256 = '8410998e0f53c0d56b8804fab215dce9955dbcb6a81d70b2bd88a39cee2ca4cc'
ONBOARDING_FILENAME = 'postmark-official-get-started.html'


def frozen_inputs():
    """Read once, validate the frozen manifests, and bind every frozen file."""
    snapshots = {p.relative_to(EXP).as_posix(): p.read_bytes()
                 for p in sorted(EXP.rglob('*')) if p.is_file()}
    for name, base in [('intent-manifest.json', EXP),
                       ('postmark/apparatus-manifest.json', EXP / 'postmark')]:
        manifest = json.loads(snapshots[name])
        for relative, expected in manifest.items():
            if not isinstance(expected, dict):
                continue
            # The frozen manifest predates the existing sandbox verifier check.
            # Preserve its hash as provenance; bind the actual apparatus below.
            if relative.startswith('firstcall/'):
                continue
            path = base / relative
            if path.stat().st_size != expected['bytes'] or file_sha256(path) != expected['sha256']:
                raise RuntimeError('frozen provenance mismatch')
    contract = json.loads(snapshots['postmark/subject-contract.json'])
    policy = json.loads(snapshots['postmark/policy.json'])
    if contract['run_ids'] != list(RUN_IDS) or policy['planned_runs'] != 3:
        raise RuntimeError('invalid frozen cohort cardinality')
    provenance = {
        'apparatus_commit': git_output('rev-parse', 'HEAD'),
        'apparatus_dirty': tracked_repo_dirty(),
        'runner_sha256': file_sha256(Path(__file__)),
        'apparatus_files': {name: file_sha256(ROOT / name) for name in (
            'firstcall/agents/codex_live.py', 'firstcall/agents/codex_events.py',
            'firstcall/journey_evidence.py', 'firstcall/verifiers/postmark.py',
            'firstcall/postmark_preflight.py', 'firstcall/grade.py',
        )},
        'frozen_provenance': {name: {'bytes': len(data), 'sha256': digest(data.decode())}
                              for name, data in snapshots.items()},
    }
    return snapshots['postmark/task.txt'].decode(), contract, provenance


def persist(path: Path, value: dict, safety: EvidenceSafety) -> dict:
    value = safety.object(value, path.name)
    value['evidence_integrity'] = safety.integrity()
    value['content_sha256'] = digest(json.dumps(value, sort_keys=True, separators=(',', ':')))
    data = json.dumps(value, indent=2, sort_keys=True).encode()
    safety.check(data)
    with path.open('xb') as stream:
        stream.write(data)
    return value


def customer_claim(agent: AgentResult) -> bool | None:
    try:
        evidence = extract_codex_evidence(agent.stdout)
    except (AttributeError, TypeError, ValueError):
        return None
    if evidence.claim.found:
        return evidence.claim.ok
    # The frozen MULTI-001 task uses a colon/block result, unlike RESEND-001.
    # Only completed assistant messages qualify, never arbitrary prose.
    for event in reversed(agent.events):
        item = event.get('item', {})
        if (event.get('type') != 'item.completed' or not isinstance(item, dict)
                or item.get('type') != 'agent_message'):
            continue
        text = item.get('text', '')
        if not isinstance(text, str):
            continue
        match = re.search(r'^FIRSTCALL_RESULT:\s*\nclaim_success: (true|false)\s*$', text, re.M)
        if match:
            return match[1] == 'true'
    return None


def run_one(*, run_id, nonce, token, task, contract, provenance, directory, runner):
    subject = f'FIRSTCALL MULTI-001 POSTMARK {nonce} {run_id}'
    prompt = task.replace('{SUBJECT}', subject)
    safety = EvidenceSafety(token)
    workspace = create_workspace()
    try:
        onboarding = (EXP / 'postmark/official-onboarding/get-started.html').read_bytes()
        if sha256(onboarding).hexdigest() != ONBOARDING_SHA256:
            raise RuntimeError('official onboarding source SHA256 mismatch')
        supplied = workspace.path / ONBOARDING_FILENAME
        supplied.write_bytes(onboarding)
        if file_sha256(supplied) != ONBOARDING_SHA256:
            raise RuntimeError('official onboarding workspace SHA256 mismatch')
        started_at = utc_now()
        try:
            agent = runner.run(cwd=workspace.path, prompt=prompt, experiment_env={
                'POSTMARK_SERVER_TOKEN': token, 'FIRSTCALL_SUBJECT': subject,
            })
        except (OSError, RuntimeError):
            # Exception text can contain a credential; never persist it.
            agent = AgentResult(1, '', 'customer execution unavailable', 0, ())
        commands = extract_completed_commands(agent.events)
        journey, _, forbidden, _ = capture_journey(
            workspace.path, directory / run_id, agent, commands, safety,
        )
        journey['base_path'] = run_id
        try:
            observation = PostmarkVerifier(
                server_token=token, subject=subject, recipient=contract['recipient'],
                created_after=started_at,
            ).verify()
            verification = safety.object(asdict(observation), 'verification')
        except (OSError, RuntimeError, ValueError, TypeError):
            verification = {'observed': None, 'reason': 'independent verification unavailable'}
        # The existing verifier returns False for transport/malformed responses.
        # These do not establish absence of an effect and are ineligible for AFCR.
        if verification['reason'] in {
            'Postmark verification request failed', 'Postmark verifier received invalid JSON',
            'Postmark verifier received malformed response', 'malformed Postmark message list',
        }:
            verification['observed'] = None
        claim = customer_claim(agent)
        receipt = safety.object({
            **provenance, 'experiment': 'MULTI-001', 'product': 'POSTMARK',
            'stage': 'BASELINE_DISCOVERY', 'execution_nonce': nonce, 'run_id': run_id,
            'subject': subject, 'recipient': contract['recipient'], 'started_at': started_at,
            'prompt_sha256': digest(prompt), 'journey_evidence': journey,
            'candidate_commands': [asdict(c) for c in commands],
            'candidate_execution_observed': bool(commands),
            'agent': {'exit_code': agent.exit_code, 'duration_ms': agent.duration_ms,
                      'claim_ok': claim},
            'verification': verification,
            'controls': {'fresh_workspace': True, 'firstcall_rescue': False,
                         'intervention': False, 'sandboxed_effect_required': True},
        }, 'receipt')
        unsafe = bool(safety.redacted or forbidden)
        if verification['observed'] is None:
            verdict = Outcome.UNKNOWN
        else:
            verdict = grade(
                Execution(agent.exit_code, 'success' if claim is True else '', '', {}),
                Verification(verification['observed'], verification),
                (HygieneFinding('evidence_integrity', 'high', 'unsafe evidence'),) if unsafe else (),
            )
        receipt['verdict'] = verdict.value
        receipt['integrity'] = {'secret_leaked': bool(safety.redacted), 'forbidden_files': forbidden}
        receipt['journey_evidence']['evidence_integrity'] = safety.integrity()
        # Protocol stop conditions are safety halts, never an intervention/retry.
        receipt['halt_cohort'] = (unsafe or verdict == Outcome.UNKNOWN or
                                 verification['reason'] == 'matching vendor-side message was not sandboxed')
        return persist(directory / run_id / 'receipt.json', receipt, safety)
    finally:
        workspace.cleanup()


def run_cohort() -> dict:
    token = os.environ.get('POSTMARK_SERVER_TOKEN', '')
    if not token:
        raise RuntimeError('POSTMARK_SERVER_TOKEN is required')
    task, contract, provenance = frozen_inputs()
    safety = EvidenceSafety(token)
    # Validate supplied bytes before any customer or vendor work.
    safety.check(json.dumps([task, contract, provenance]).encode())
    preflight = safety.object(asdict(inspect_server(token)), 'preflight')
    if safety.redacted or preflight['safe'] is not True or preflight['delivery_type'] != 'Sandbox':
        raise RuntimeError('Postmark preflight requires DeliveryType=Sandbox')
    nonce = new_execution_nonce()
    if not re.fullmatch(r'[0-9a-f]{12}', nonce):
        raise ValueError('invalid execution nonce')
    directory = OUT / nonce
    directory.mkdir(parents=True, exist_ok=False)
    preflight = persist(directory / 'preflight.json', preflight, safety)
    runner = CodexLiveRunner(timeout=300)
    results = []
    for run_id in RUN_IDS:
        receipt = run_one(run_id=run_id, nonce=nonce, token=token, task=task,
                          contract=contract, provenance=provenance,
                          directory=directory, runner=runner)
        results.append(receipt)
        safety.redacted.update(
            f'{run_id}/{location}'
            for location in receipt['evidence_integrity']['redacted_locations']
        )
        if receipt['halt_cohort']:
            break
    eligible = [r['run_id'] for r in results if r['verdict'] != Outcome.UNKNOWN.value]
    proven = sum(r['verdict'] == Outcome.PROVEN_SUCCESS.value for r in results)
    metric = afcr(proven, len(eligible), len(results) - len(eligible))
    summary = {
        **provenance, 'experiment': 'MULTI-001', 'product': 'POSTMARK',
        'stage': 'BASELINE_DISCOVERY', 'execution_nonce': nonce,
        'status': 'halted' if results[-1]['halt_cohort'] else 'complete',
        'planned_runs': list(RUN_IDS), 'runs': len(results), 'eligible_runs': eligible,
        'proven_successes': proven, 'afcr': metric.rate, 'metric': asdict(metric),
        'preflight_content_sha256': preflight['content_sha256'],
        'outcomes': {r['run_id']: r['verdict'] for r in results},
        'verification_results': {r['run_id']: r['verification'] for r in results},
        'evidence_hashes': {r['run_id']: {
            'receipt_content_sha256': r['content_sha256'],
            'files': r['journey_evidence']['files'],
        } for r in results},
    }
    return persist(directory / 'summary.json', summary, safety)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='execute the real three-customer cohort')
    args = parser.parse_args()
    if not args.execute:
        parser.error('explicit --execute is required')
    run_cohort()


if __name__ == '__main__':
    main()
