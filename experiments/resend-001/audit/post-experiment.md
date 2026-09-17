# RESEND-001 Post-Experiment Audit

## Status

The original receipts and verdicts are preserved.

RESEND-001 proves the narrow claim that three fresh Codex agent runs caused
three distinct Resend vendor-side email effects which were independently
observed as delivered.

It does not yet establish that the supplied documentation caused those
outcomes or preserve sufficient raw execution evidence to reconstruct the
integration journey.

## Verified

- Three distinct vendor email IDs.
- Each observed with last_event=delivered.
- Receipt proof hashes reproduce.
- Summary proof reproduces.
- No detected credential leakage.
- Frozen apparatus remained unchanged during the experiment.

## Evidence gaps

- Raw Codex JSONL was not persisted in the pushed evidence.
- Agent command execution was not preserved in the receipts.
- Generated integration artifacts were not preserved.
- candidate_execution_observed=false.
- candidate_commands is empty.

## Integrity defect

Vendor verification was bound to deterministic subject and recipient but not
to a unique experiment execution nonce and temporal lower bound.

A later replay could therefore match a historical vendor object.

This must be corrected prospectively before counterfactual replay.

## Required v0.4 controls

1. Per-execution nonce.
2. started_at temporal effect binding.
3. apparatus commit and dirty-state provenance.
4. Separate credential fingerprints with inequality assertion.
5. Raw Codex journey evidence preservation.
6. Evidence manifests covering raw trace artifacts.
7. Hostile stale-effect rejection test.

## Causal control

RESEND-002 will test documentation ablation.

RESEND-001 must not be interpreted as evidence of documentation lift until a
valid ablation control has been performed.

The ablation must prevent retrieval of Resend documentation while preserving
the ability to reach the Resend API required by the task.
