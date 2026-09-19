# A1 pre-reveal machine registrations — Freeze 1.2.1

Additive to Freeze 1.2 commit `3def4227285453c253e2c6df969bb3eefc291fa8`.
Binding on commit, annotated tag `programme-a-freeze-1.2.1-pre-reveal`, and push.
The custodian explicitly authorised the IDNA2008 and E2 repair. G1 stays on HOLD.

| Component | Registration | State |
| --- | --- | --- |
| Runtime | RT-A1-RUNTIME.json | Pinned Python/Unicode/IDNA2008 |
| R12 frame | ../a1_frame_121.py; ../../amendments/freeze-1.2.1.json | Operative additive host repair; historical frame file preserved |
| R17 parser | R17-spec-parser.json | Version 1.2.1, shared host and repaired E2 |
| R07 | R07-translation.json | NO_MACHINE_TRANSLATION / FAIL_CLOSED |
| R08 | R08-browser-profile.json | Conditional on actual installation attestations |
| R16 | R16-prior-firstcall-registry.json | Structural projection reproduced; two approvals unfilled |
| Sealing | SEAL-TOOL.json | Synthetic tests pass; real human intake/isolation attestation required before G4 |
| R03/R04/R05/R06 | forms/ | Unfilled human requirements |

`pre-reveal-audit.json` retains discovery history, including the original open-D8
finding; current readiness is `registrations-validation.json`. No prior draft
finding is represented as a current operative rule. The amendment describes the
precise supersession and dependency trust limits.

Run all offline validation from the repository root:

```sh
/usr/bin/sandbox-exec -p '(version 1) (allow default) (deny network*)' \
  /usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 \
  PYTHONPATH="$PWD/experiments/programme-a/a1/offline" \
  python3 -B experiments/programme-a/a1/run_offline_121.py
```

PyYAML 6.0.3 package and MIT licence are preserved from the cached source archive
(SHA256 `d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f`).
IDNA 3.11 provenance is registered in `../provenance/idna-3.11.json`. Vendored
upstream whitespace is intentionally part of the recorded hashes and is never
rewritten to satisfy whitespace checks.

The sealing library is a custodian-side interface, not a participant browser or
shared CLI. It accepts authenticated identities supplied by the custodian, never
publishes pre-reveal decision hashes, and forbids reveal until both full blocks
are sealed. SQLite files must remain private to that custodian. Synthetic fixture
IDs are not human registrations. Human record signatures/independence and intake
controls need real attestations; no deployed human isolation is claimed here.
