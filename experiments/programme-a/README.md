# experiments/programme-a — PROSPECTIVE DESIGN ONLY

Programme A (RATE / MEASUREMENT). See `docs/programme-a-measurement-protocol.md` for the frozen
protocol. This directory holds **machine-readable prospective schemas and configuration
templates** only.

**NOT EXECUTABLE.** No vendor-specific runner or verifier exists here. No sample-frame snapshot,
no vendor list, no credentials, and no run outputs are present. REAL VENDOR RUNS = 0.

Files:
- `estimand.schema.json` — the quantities Programme A estimates and their denominators.
- `outcome-taxonomy.json` — the frozen grading outcomes and the strict FALSE_SUCCESS bar.
- `journey-standard.json` — the vendor-neutral DISCOVER→RECEIPT standard and verifier policy.
- `sample-frame.config.json` — deterministic vendor-selection rules (no vendors selected yet).
- `run-design.config.json` — N, k, isolation, randomisation policy.
- `analysis-plan.json` — Wilson/bootstrap params and sensitivity analyses.
- `prereg-freeze-sequence.json` — the ordered freeze artefacts and sequence.
- `receipt.v1.schema.json` — the per-run evidence receipt schema.

Nothing here selects a vendor or exposes outcome information. Vendor plaintext is only revealed
inside the sealed pre-registration bundle at Freeze 5.
