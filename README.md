# FIRSTCALL

**Synthetic customer monitoring for autonomous agents.**

FIRSTCALL asks a fresh coding agent to integrate a product,
executes what it builds, and independently verifies whether the
required real-world effect occurred.

The agent does not grade itself.

## Core outcomes

- `PROVEN_SUCCESS`
- `FALSE_SUCCESS`
- `EXECUTION_FAILED`
- `EFFECT_FAILED`
- `UNSAFE_SUCCESS`
- `UNKNOWN`

## Core experiment

1. Snapshot the onboarding surface.
2. Give a fresh agent a customer task.
3. Execute its integration.
4. Verify the effect independently.
5. Localise failures.
6. Patch the onboarding surface.
7. Replay fresh agents.
8. Measure the causal improvement.

This is **Counterfactual Replay**.

## North-star metric

**Agent First-Call Rate (AFCR)**

The proportion of fresh agent runs that reach an independently
verified successful first product outcome.

## Principle

> Agent says success != proof of success.

## v0.4 benchmark integrity

RESEND-001 Phase 3 is implemented. Future executions write under
`artifacts/resend-001/executions/<execution_nonce>/<run_id>/`, with
content-addressed receipts and a cohort summary. Historical evidence is immutable.

Each run preserves captured Codex exec JSONL, stderr, completed command events,
a sorted workspace manifest, and safe copies of generated files before cleanup.
`candidate_execution_observed` means at least one completed `command_execution`
event was observed; it does not establish that the integration or vendor effect
succeeded. Agent prose and result claims cannot set this field.

Manifests record observed byte sizes and SHA256 hashes, plus separate hashes for
persisted copies. Caches, virtual environments, bytecode, internal metadata, and
all symlinks are excluded. Both run credentials and repository secret patterns
are checked before persistence; redactions and omitted unsafe paths are explicit
in `evidence_integrity`. Receipt proofs bind temporal identity, apparatus and
credential provenance, commands, and evidence hashes. Cohort summary proofs bind
the execution nonce, provenance, and ordered run proofs.
