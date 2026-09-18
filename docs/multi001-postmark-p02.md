# MULTI-001 Postmark P02 apparatus

P02 is mechanically derived from P01 commit
`9015c333080c4e192d680d6f88ce9360d74353c5`, apparatus tag
`multi-001-postmark-p01-apparatus`, diagnosis tag
`multi-001-postmark-p01-diagnosis`. Its canonical evidence is
`artifacts/multi-001/postmark/p01-counterfactual/ca116baa8519`.
All P01 source, frozen inputs, and historical evidence remain unchanged.

The sole additional customer-facing fact is:

> A concrete verified sender identity is available in the environment variable POSTMARK_FROM.

`experiments/multi-001-postmark-p02/get-started.html` preserves the exact P01
onboarding bytes, inserting only a newline and one HTML paragraph containing
that sentence immediately after the existing body opening tag. The workspace
filename remains `postmark-official-get-started.html`. No sender address is
added. P02 inputs live outside `experiments/multi-001` to preserve its frozen
tree hash and P01's existing tests. This document and the diagnosis/manifest
are harness records; customers receive only the onboarding and original task.

The frozen diagnosis in `experiments/multi-001-postmark-p02/diagnosis.json`
records this prediction before any real execution:

> Fresh autonomous customers should progress beyond MissingFromAddress. Making the already-supplied sender identity discoverable through POSTMARK_FROM is not predicted to guarantee a successful effect.

The diagnosis and prediction must remain immutable after execution. The runner
pins their content, checks the frozen manifest before preflight, before every
customer, and before the summary, and embeds the original diagnosis and its
hash in receipts and summary. Later findings require a separate record.

`firstcall.multi001_postmark_p02` retains P01's task, subject contract, model,
customer invocation, verifier, grading, fresh workspace and cleanup behavior,
evidence safety, and stop conditions. The three run IDs are `P02-R01`, `P02-R02`,
and `P02-R03`; the phase is `P02_COUNTERFACTUAL`. Output is restricted to
`artifacts/multi-001/postmark/p02-counterfactual/<nonce>/`, with redirected roots,
symlinks, and overwriting existing cohort directories rejected.

The sender continues to come only from the parent's `POSTMARK_FROM` at execution
time, without a default or value substitution. The customer experiment variables
remain exactly `POSTMARK_SERVER_TOKEN`, `POSTMARK_FROM`, and `FIRSTCALL_SUBJECT`.
The sender is excluded from inherited harness subprocess environments, restored
to the parent on exit, never placed in argv, and redacted from evidence. Only
its SHA256 fingerprint is persisted. As in P01, this environment-scoping runner
must remain sequential within its Python process.

DeliveryType=Sandbox preflight remains mandatory. PROVEN_SUCCESS requires an
independently verified matching sandboxed effect. UNKNOWN halts the cohort.
There is no FIRSTCALL rescue or customer retry after ambiguous failure; existing
read-only verifier attempts are unchanged. Nonces and evidence hashes retain
P01 behavior. Additional content pins reject edits to frozen inputs and shared
apparatus before vendor/customer work. The P02 onboarding is hash-checked again
at delivery, including its workspace copy.

Frozen SHA256 values:

| Record | SHA256 |
| --- | --- |
| P02 diagnosis | `7e7ce8952b5827107a030d51b7ea1bdfac0533fb98b7861ac87b092ce6f928f3` |
| P02 onboarding | `823dbea537294f9fd89a18ed779f50be4eeea423dac5da366c991fdf841555af` |
| P02 manifest | `040965f04a1649448c4036bfdd583f89e3d4fbe1c4b9cdb4de2a65a67bd15723` |
| Original P01 onboarding | `8410998e0f53c0d56b8804fab215dce9955dbcb6a81d70b2bd88a39cee2ca4cc` |
| P01 canonical evidence tree | `6a975b16d84227d7cd5c23372f02fe43e3d167f6c68ea2a262f696f7b7989e34` |
| Historical baseline evidence tree | `40289fdcf64dc5c8073ed90b22a698cd6897d9a7fc118fa51c6e5add8d9087f7` |

Tree hashes are SHA256 of UTF-8 JSON mapping every sorted relative file path
to its SHA256, with sorted keys and compact separators. The manifest pins the
original inputs and apparatus files individually, and identifies frozen baseline
commit `ce95ed52ec9b728d43d8247ef3f2df53fee61ab1`, baseline cohort `d0bd8c7ade2b`,
P01 provenance, and P02 phase. This is a content freeze; no new commit or tag is
created by this work.

Offline verification:

```sh
.venv/bin/python -m pytest -q tests/test_multi001_postmark_p02.py
.venv/bin/python -m pytest -q
.venv/bin/python -c 'from pathlib import Path; from firstcall.repo_security import scan_repository; hits = scan_repository(Path.cwd()); print(hits); raise SystemExit(bool(hits))'
git diff --check
git status --short
```

The dedicated tests are copied from P01 and adapted for P02, with additional
checks for the exact single-paragraph delta, immutable prediction, protected
evidence/source hashes, output isolation, and mechanical preservation of the
customer execution/grading flow. They block real subprocess and network work
and use synthetic sender values.

Future execution command, requiring both credentials already present in the
parent execution environment (not executed during implementation):

```sh
.venv/bin/python -m firstcall.multi001_postmark_p02 --execute
```

Omitting `--execute` fails before any cohort work. No real P02 cohort has been
executed as part of preparing this apparatus.
