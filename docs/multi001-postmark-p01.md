# MULTI-001 Postmark P01 apparatus

`firstcall.multi001_postmark_p01` is a distinct, opt-in counterfactual runner.
Implementation and offline validation do not execute a customer or send email.
The baseline runner, evidence, frozen inputs, verifier, classifier, and Codex
configuration remain unchanged.

The sole customer-facing intervention is `POSTMARK_FROM`, read from the parent
environment when execution is explicitly requested. Both `POSTMARK_SERVER_TOKEN`
and `POSTMARK_FROM` are required before any preflight, workspace, or customer
work. There is no default sender and no sender-validation email.

The existing Sandbox preflight must succeed before any customer starts. The
sequential runner temporarily removes `POSTMARK_FROM` from the harness environment
so inherited preflight, verifier, and Git subprocess environments cannot receive
it. It restores the parent's value on success or failure. Only the explicit
customer environment receives the sender, alongside the existing server token
and `FIRSTCALL_SUBJECT`. Do not run this environment-scoping runner concurrently
in the same Python process.

Three planned runs, `P01-R01`, `P01-R02`, and `P01-R03`, share one newly generated
cohort nonce. Each gets a fresh workspace containing the byte-identical official
onboarding snapshot, with its SHA256 checked before Codex starts. The original
task is substituted only with that run's subject:
`FIRSTCALL MULTI-001 POSTMARK <nonce> <P01-run-id>`. It still requires exactly one
Sandbox email to `test@blackhole.postmarkapp.com`, with subject and plain body
equal to this unique subject, and prohibits retry after an ambiguous response.
There is no additional sender instruction in the prompt or onboarding.

Independent vendor verification, exact cardinality, `started_at` binding,
classification, and safety halts retain baseline behavior. Read-only verifier
attempts are unchanged; the apparatus never retries a customer execution.
Completed command events alone establish `candidate_execution_observed`.

Evidence is written exclusively beneath
`artifacts/multi-001/postmark/p01-counterfactual/<nonce>/`. It includes raw Codex
JSONL, stderr, completed commands, workspace manifest and files, receipts,
summary, and integrity hashes. All capture and persistence paths redact the
server token and sender, including escaped values and unsafe filenames. A leak
halts the cohort and cannot count as proven success. Sender provenance contains
only its full SHA256 fingerprint. Workspaces are cleaned after evidence capture.

Summary and receipts bind the apparatus commit and source hashes, P01 phase,
baseline cohort `d0bd8c7ade2b` and AFCR `0/3`, execution nonce, and frozen inputs.
The summary records eligible runs, proven successes, and AFCR with counts.

- Diagnosis commit: `530351d120bac32b066aa70cbf8646387668cdac`
- Diagnosis tag: `multi-001-postmark-p01-diagnosis`
- Diagnosis SHA256: `8e3669969f77db0fbb39d51d3e38e05748a7576b8194ef8c2e6d5479b4543df3`
- Onboarding SHA256: `8410998e0f53c0d56b8804fab215dce9955dbcb6a81d70b2bd88a39cee2ca4cc`

Offline validation:

```sh
.venv/bin/python -m pytest -q tests/test_multi001_postmark_p01.py tests/test_multi001_postmark.py tests/test_postmark_preflight.py tests/test_postmark_verifier.py
.venv/bin/python -m pytest -q
```

P01 tests block actual subprocess and network work, simulate customers and
vendor responses, and pin frozen input and historical baseline tree hashes.
No counterfactual cohort has been executed as part of this implementation.
