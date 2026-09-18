# Postmark verifier measurement audit — 2026-09-18

VERDICT: the old verifier had a plausible eventual-consistency false-negative
window. This is a source-level finding, not a retrospective correction to P02.
P02 remains 2/3 AFCR; P02-R02 remains its recorded FALSE_SUCCESS. No live cohort,
Postmark request, send, or other network request was performed during this audit.
No P03, commit, tag, or push was performed.

## Evidence and old instrument

Inspected the old `firstcall/verifiers/postmark.py` (SHA256
`7ac6b91fc78190e566e887e7bfaf6e105b049f676919c77e4b81eaa350ef9cf6`), all eight
original verifier tests, Postmark preflight tests, baseline/P01/P02 verifier
call sites and associated mock tests, P02 frozen manifest, all three P02
receipts, summary, completed-command records, final customer results, and
stored evidence-file hashes. Each P02 receipt's eight evidence-file hashes
matched the files on disk.

Canonical P02 evidence is under
`artifacts/multi-001/postmark/p02-counterfactual/9906c79fc405`:

| Run | Started at (UTC) | Candidate ID | Historical independent result |
| --- | --- | --- | --- |
| P02-R01 | 13:32:29.694426 | d2367896-2347-4a2b-abb6-2cfe328ed777 | observed=true; PROVEN_SUCCESS |
| P02-R02 | 13:33:27.596628 | 74fdbaad-6b97-4d24-b16f-6d3e2b6990e6 | observed=false; vendor effect not observed; FALSE_SUCCESS |
| P02-R03 | 13:34:34.003050 | 82e2db86-7b0a-4da0-aed4-1192ec3f6c7e | observed=true; PROVEN_SUCCESS |

R02's stored completed send command has a one-request guard and outputs
`http_status=200`, `error_code=0`, and the above effect ID. Its final customer
message repeats the ID. These are candidate-side evidence of acceptance;
they are not the independent verifier's list response. No raw per-attempt list
responses or observation timestamps are retained in these receipts. Therefore
this evidence cannot establish when the message became independently visible,
or demonstrate that eventual consistency actually caused R02's result.

Exact old behavior:

1. `attempts=3` by default. Baseline, P01, and P02 supply no override.
2. No sleep, wait, backoff, or jitter, after either empty successful responses or
   RuntimeError. Only subprocess/request latency separates observations. No curl
   maximum time or Python subprocess timeout; three attempts were not a wall-clock
   bound.
3. `_list()` invokes curl's default GET of
   `https://api.postmarkapp.com/messages/outbound?count=100&offset=0`, using
   `-sS --fail-with-body` and the `X-Postmark-Server-Token` header. There are no
   server-side subject, recipient, time, sandbox, stream, or ID query filters.
   There is no pagination or TotalCount check.
4. No MessageID input exists. The only inputs are token, subject, recipient,
   created_after, and attempts. The candidate's effect_id is not passed by any
   of those three call sites. MessageID is copied from the sole matching list
   row without validating it.
5. Filtering is exact Subject, recipient membership in a Recipients list (or
   exact To fallback), ReceivedAt (or SentAt) at/after created_after, then literal
   `Sandboxed is True`. Two eligible rows fail verification.

All old paths returning `observed=false`:

- Immediately when `Messages` is absent or not a list:
  `malformed Postmark message list`.
- Immediately when an otherwise matching current row lacks literal sandbox true:
  `matching vendor-side message was not sandboxed`.
- Immediately on the second current sandboxed subject/recipient match:
  `multiple matching vendor-side messages observed`.
- After attempt exhaustion with no accepted match:
  `vendor effect not observed`, unless a RuntimeError has set `last_reason`.
  Empty lists, non-dictionary rows, wrong subjects/recipients, missing or invalid
  timestamps, and pre-boundary timestamps can all lead here. Zero/negative
  attempts also produced this result without observation.
- Exhaustion after `_list()` RuntimeError reports the last such error:
  `Postmark verification request failed` for nonzero curl exit,
  `Postmark verifier received invalid JSON`, or
  `Postmark verifier received malformed response` for non-object JSON.
  A later successful empty response did not reset the earlier error reason.

Invalid boundary parsing, timezone-naive/aware comparison TypeError, and
subprocess OSError could raise instead of returning false. P01/P02 catch those
exceptions as independent verification unavailable (observed=None/UNKNOWN),
and convert the four known malformed/transport reason strings to UNKNOWN.
Successful empty-list exhaustion remains determinate false in those runners.

A valid effect becoming visible after the third quick GET is a plausible false
negative. An effect omitted from the first 100 rows can also be missed. Missing
sandbox/time fields can cause rejection despite synchronous send acceptance.
The original tests lacked delayed-visibility, wait, transport-recovery, and
candidate-ID coverage. They also allowed malformed rows to be skipped, potentially
hiding an extra effect, and did not establish complete list cardinality.

## Repair and scope

The repaired verifier retains three default attempts and the same read-only GET.
It observes immediately, then waits exactly five seconds before each subsequent
attempt. An empty observation or transport error consumes one attempt. There is
no wait before the first request or after the last, and no retry of a send.
With fast responses the observation times are approximately 0, 5, and 10 seconds.
Curl `--max-time 10` and subprocess `timeout=10` bound each request; the default
budget is at most 30 seconds of requests plus 10 seconds of waits, excluding
process creation/cleanup, scheduling, and local processing overhead. This is a
chosen finite observation policy, not a measured Postmark consistency SLA.
`retry_delay` and the `wait` callable can be supplied explicitly; attempts must
be a positive integer and delay must be finite and positive.

`expected_message_id` optionally accepts a canonical UUID-shaped string and
compares case-insensitively. Invalid supplied IDs fail before observation.
A caller can pass the syntactically validated candidate ID via that keyword.
The verifier still requires independent matching subject/recipient, current time,
and sandbox evidence. It counts the full subject/recipient set BEFORE checking
the ID. A different ID, duplicate rows (including repeated IDs), or a matching
live row fails closed. A claimed ID absent throughout the window cannot prove
success. Historical runner call sites are intentionally unchanged; they do not
supply the new optional parameter.

Malformed list/row evidence fails closed immediately; candidate-matching times
must have a timezone and MessageID must be a nonempty string. Transport errors
can recover on a subsequent valid observation. Returned transport reasons are
fixed strings, never exception text, argv, token, or response body. The verifier
writes no credentials or vendor payloads to disk. Existing EvidenceSafety,
sandbox preflight, grading, and customer execution remain unchanged.

To avoid proving uniqueness from an incomplete page, an explicit TotalCount
must be an integer equal to the returned row count; a full 100-row page is also
rejected. Missing TotalCount remains supported for existing short-list inputs.
Incomplete/invalid lists use the existing malformed-list reason, preserving
historical runner UNKNOWN handling. This conservative policy can reject busy
accounts; pagination is not added by this repair.

Success still returns on the first valid observation. This establishes exactly
one eligible effect in that observation; neither the old nor repaired verifier
can rule out an additional effect becoming visible later. The bounded window
can also expire before a slow effect appears. No retrospective proof is claimed.

Changing wait or correlation semantics changes the measurement protocol. The
actual P02 manifest and production pin constants are untouched and now reject
the changed shared verifier before live work. Baseline/P01 do not have the same
strict source validation; they must not be rerun as an equivalent historical
instrument. No runner was executed with a real customer or vendor during this
audit. Mock-only runner tests use temporary directories and mocked transports.

Tests formerly asserting that the *current* verifier equals the historical hash
now assert the immutable receipts/manifests retain that old hash. Other apparatus
pins remain checked. P02 mock flow tests use a temporary copied test manifest
updated only for the changed verifier and P01 test source; no production pin is
relaxed. A separate test checks the real P02 manifest rejects the repair, and
another checks the stored 2/3 AFCR and R02 outcome remain unchanged.

## Validation

- Focused verifier and preflight: 71 passed.
- P02 focused mock tests: 90 passed.
- Full regression: 365 passed.
- Test waiting is mocked; sequence tests explicitly assert observation/wait order.
- The final three runs used an offline Python audit guard rejecting network/DNS
  and external processes except the suite's two exact local Python fixture scripts.
  All three runs recorded zero attempted forbidden operations.
- Repository secret scan: PASS, zero matches; scanner scope is the
  existing `firstcall.repo_security.scan_repository`, which excludes artifacts
  and checks its two configured key patterns. It is not a universal secret detector.
- `git diff --check`: PASS, no output (exit 0).

The new hostile cases cover first visibility, second/last observation visibility,
entire-window absence, transport error/timeout then visibility, permanent
transport failure, invalid JSON/list/row/time/recipient evidence, wrong supplied
and observed IDs, duplicate/live rows in either order, stale effects, fabricated
claims, invalid retry configuration, incomplete pages, read-only request/timeout
arguments, and sanitized transport diagnostics. Tests also check that a claim
without independent observation cannot grade as PROVEN_SUCCESS.

## Historical byte preservation

`postmark-verifier-history-hashes.json` contains complete before/after per-file
SHA256 manifests and tree digests. The before snapshot was taken before edits.
All 103 historical files, their relative names, and their hashes match afterward.
A tree digest hashes the concatenation of file SHA256, two spaces, relative path,
and newline for each file in sorted pathlib enumeration order.

| Historical tree | Files | Before SHA256 = after SHA256 |
| --- | ---: | --- |
| baseline | 43 | 0be41458ff43dcdbef36b68060b100a954601fbf44a554ac7714d8685dcaab24 |
| p01-counterfactual | 31 | cba1ce90e1ee4562ae2d1887fdc7280a3d32dafcfd0ffef1a16ffd47ac07f568 |
| p02-counterfactual | 29 | bd49ba2a51f237313306688d7c5e7a389d8a4c36a6e7003825f311c9fac2fc40 |

These digests use the explicitly recorded line-manifest algorithm; older tests
use a different JSON-manifest digest algorithm. Both checks pass. No historical
baseline, P01, P02, receipt, prediction, manifest, or AFCR was rewritten.


Files changed by this audit: `firstcall/verifiers/postmark.py`,
`tests/conftest.py`, `tests/test_postmark_verifier.py`,
`tests/test_multi001_postmark_p01.py`, and the already-untracked
`tests/test_multi001_postmark_p02.py`. New records:
`docs/postmark-verifier-audit.md` and
`docs/postmark-verifier-history-hashes.json`. Other pre-existing untracked work
was left untouched.
