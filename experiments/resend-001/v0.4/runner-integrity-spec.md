# FIRSTCALL v0.4 Runner Integrity

## Purpose

Bind independently observed vendor effects to the exact autonomous customer,
experiment execution and frozen apparatus that produced them.

## Required controls

### Cohort identity

Generate one cryptographically random execution_nonce per complete experiment
invocation.

R01, R02 and R03 share the same execution_nonce.

Subjects:

FIRSTCALL RESEND-001 <execution_nonce> R01
FIRSTCALL RESEND-001 <execution_nonce> R02
FIRSTCALL RESEND-001 <execution_nonce> R03

### Temporal binding

Capture started_at in UTC immediately before each autonomous customer launch.

Pass that exact value to:

ResendVerifier(created_after=started_at)

Persist started_at in the receipt.

### Apparatus provenance

Capture before any customer run:

- apparatus_commit
- apparatus_dirty for tracked repository state
- docs_sha256
- task_sha256
- policy_sha256

Deliberately untracked historical cf001 helper scripts do not constitute
tracked apparatus dirtiness.

### Credential separation

Customer credential:

RESEND_API_KEY

Independent verifier credential:

FIRSTCALL_RESEND_VERIFIER_KEY

Before launch:

- both must exist
- full values must differ
- SHA256 each
- persist only first 12 lowercase hex characters
- credential_separation must equal true

The verifier credential must never enter the autonomous customer's
environment.

### Journey evidence

Before temporary workspace cleanup preserve safe evidence for each run:

- captured Codex exec JSONL
- captured Codex stderr
- generated workspace manifest
- safe generated integration artifacts where possible
- completed command_execution evidence
- command
- exit_code
- status

Do not describe Codex exec JSONL as a complete internal model transcript.

### Secret handling

No credential may be persisted.

Evidence containing credential material must not be persisted verbatim.

Persistent evidence must pass FIRSTCALL repository secret scanning.

### Receipt

Each prospective receipt must include:

- execution_nonce
- run_id
- started_at
- apparatus_commit
- apparatus_dirty
- docs_sha256
- task_sha256
- policy_sha256
- agent_credential_fingerprint
- verifier_credential_fingerprint
- credential_separation
- journey evidence paths
- journey evidence hashes
- candidate_commands
- candidate_execution_observed

candidate_execution_observed must derive from captured execution evidence,
never agent prose.

proof_sha256 must cover these fields.

### Summary

Summary must include:

- execution_nonce
- apparatus provenance
- run proofs
- content-addressed summary proof

### Required hostile tests

Prove:

1. All cohort runs share one execution nonce.
2. Run subjects contain nonce and distinct run IDs.
3. Exact started_at is passed to verifier as created_after.
4. Equal customer/verifier credentials fail before launch.
5. Credential fingerprints are deterministic 12-char lowercase hex.
6. Fingerprints do not reveal credentials.
7. Tracked dirty apparatus is recorded.
8. Raw Codex evidence is captured before workspace cleanup.
9. command_execution events populate candidate_commands.
10. No command evidence means candidate_execution_observed=false.
11. Secret-containing raw evidence is not persisted plaintext.
12. Historical RESEND-001 evidence is never rewritten.

## Existing verifier invariants

The v0.4 verifier already proves:

- historical matching effects are rejected
- exactly one current matching effect is accepted
- duplicate current effects are rejected
- duplicates hidden on later pages are rejected
- repeated pagination cursors fail closed

## Experimental next step

Do not run another external experiment until these controls pass.

After v0.4 freezes, run RESEND-002 as a documentation-ablation control before
claiming documentation lift from RESEND-001.
