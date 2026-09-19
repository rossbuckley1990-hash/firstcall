# Programme A — Freeze 1.2.1: prospective host repair and machine registrations

Status: prospective package; binding only when committed, annotated-tagged
`programme-a-freeze-1.2.1-pre-reveal`, and pushed by the protocol custodian.
Parent: Freeze 1.2 commit `3def4227285453c253e2c6df969bb3eefc291fa8`.
This is additive. Historical frozen files remain byte-identical. No A1 retrieval
or gate transition is performed by this package. G1 is explicitly on HOLD.

## Authority, chronology and boundary

The protocol custodian's 2026-09-19 follow-up explicitly resolves the IDNA conflict
in favour of Freeze 1.1's IDNA2008 requirement. The reason is chronological and
structural: Freeze 1.1 explicitly required IDNA2008; Freeze 1.2 retained its URI
normalisation but introduced stdlib IDNA for structural RDGs; offline synthetic
strings proved disagreement. No observed A1 host motivated this choice.

Discovery order (exact wall-clock instants were not recorded and are not invented):

1. D8A: prior agent's pre-reveal offline registration tests found anchored E2
   accepting malformed DNS hosts and failing URI normalisation. The prior audit
   file records these synthetic triggers and the initial STOP recommendation.
2. Path defect: the interrupted implementation's D8 property test failed. Takeover
   reproduced `HTTPS://sub.x.com:8443/0//` → `/0/` → `/0`, before any code change.
3. D8B: the prior agent noticed the IDNA split; takeover confirmed the conflicting
   frozen clauses and `straße.de` → `strasse.de` (RDG) versus `xn--strae-oqa.de`
   (draft E2), then stopped. The custodian subsequently authorised this repair.
4. This amendment implements that explicit prospective decision on 2026-09-19.

At discovery and repair: A1 snapshot retrieved NO; membership observed NO;
candidate identities observed 0; A1 entropy NONE; permutation NONE; selected RDGs 0;
eligibility decisions 0; vendor API calls 0; autonomous runs 0; outcomes 0.
Repository counters and absence of output artifacts support this assertion; they
cannot prove activity outside recorded custody. Earlier disclosed source metadata
observations remain disclosed by Freeze 1.2. Dependency downloads occurred in the
previous task (cached IDNA/PyYAML evidence); this takeover downloaded nothing.

## Narrow supersession

| Defect | Frozen clause / implementation | Authoritative replacement | Consequence and regression |
| --- | --- | --- | --- |
| D8A | Freeze 1.2 §9, decision-protocol E2 DNS-only text versus `a1_evidence._norm_url`; Freeze 1.1 §2 URI rules retained by Freeze 1.2 §16 | `a1_e2_leads.normalise_lead`: absolute HTTP(S), shared valid DNS host, deterministic URI rules below | Malformed links can consume a finite page slot; equivalent links can consume duplicate slots. DNS/URI hostile tests prevent both. Field selection and default server-variable substitution remain frozen. |
| D8B | Freeze 1.2 §5 step 2, population unit.host_extraction and `a1_frame.to_alabel/key_host` stdlib-IDNA clause; consequentially §5 step 3 singleton tests (the shared validity check also makes malformed `xn--` A-labels and all-numeric final labels singletons; singleton bases `INVALID_IDN` and empty-label `NON_DNS_HOST` are recorded as `INVALID_DNS_LABEL`) | Freeze 1.1 IDNA2008 remains authoritative. `a1_host.canonical_host`, pinned idna 3.11, is shared by the operative RDG and E2 paths, including PSL label conversion | Unicode hosts must not split structural identity. Synthetic U-label/A-label, ß, NFC, ASCII, case and invalid-host tests cover both paths. The singleton mechanism itself is unchanged. |
| Path implementation defect (D8A) | Freeze 1.1 §2 “remove terminal / except root”; draft one-character slicing | After unreserved decoding and dot-segment resolution, remove the entire terminal ASCII slash run, retaining `/` if the result is empty | `/0//` becomes `/0` once. Internal repeated slashes remain. Corpus/property tests require N(N(x)) = N(x). No candidate-dependent exception. |

Freeze 1.2 RDG sampling design is otherwise unchanged: snapshot, PSL bytes, structural
key grammar, RDG/eTLD+1 grouping, primary key/entry, conservation, uniform permutation,
sequential screening, estimand, budgets, eligibility predicates and human independence.
Host validation rejects malformed IDNA A-labels and numeric-final-label/non-DNS hosts
consistently; a rejected structural host retains the frozen singleton mechanism.
No confusable merging, vendor identity resolution or server-based RDG construction.

## Exact URL and shared host rules

1. Non-string/empty input is dropped. Trim only ASCII whitespace at the two ends;
   apply NFC. Reject internal ASCII whitespace/control/DEL before URL parsing.
2. Remaining balanced templates are dropped. Relative and scheme-relative URLs,
   non-HTTP(S) schemes and missing hosts are dropped. Scheme is lower-case;
   HTTP and HTTPS remain distinct. Malformed authority/brackets/ports are dropped.
3. Validate userinfo syntax and percent escapes, then discard userinfo. Multiple
   `@`, empty userinfo and empty explicit ports are malformed. Validate fragment
   syntax/percent escapes, then discard it. No credential-bearing lead is emitted.
4. Shared host: NFC, lower-case, remove trailing ASCII dots; strict IDNA2008 through
   vendored idna 3.11 (`strict=True`, `uts46=False`, Unicode 16.0.0). No transitional
   or compatibility mapping. Validate A-labels including existing punycode; LDH,
   1–63 octets/label, no empty labels, total ≤253, at least two labels, nonnumeric
   final label. IP literals and localhost/single labels are rejected. PSL labels
   use the same IDNA conversion with the necessary single-label allowance.
5. Default ports 80/HTTP and 443/HTTPS disappear. Other valid integer ports remain.
6. Encode non-ASCII path/query UTF-8 octets as uppercase percent escapes. Reject
   malformed escapes, invalid Unicode scalars and characters outside URI syntax.
   Uppercase escape hex and decode only unreserved bytes; reserved escapes remain.
7. Resolve dot segments, then strip the terminal slash run once (root retained).
   Path case and internal repeated slashes remain unchanged.
8. Split query on `&`, discard empty segments, split each at the first `=`;
   retain duplicates; remove case-sensitive `utm_*`, `gclid`, `fbclid` keys after
   percent normalisation. Sort by key then value UTF-8 bytes, with absent `=`
   preceding present `=` only as a tie-break. Plus remains a literal plus.
9. Byte-sort and deduplicate E2 URLs. Existing candidate fields and server-variable
   default substitution are imported unchanged from the anchored E2 module.

## Operative files and dependency custody

Use `a1_frame_121.py` for R12 frame construction and `a1_e2_leads.py` for E2;
R17 version 1.2.1 calls those modules. Historical `a1_frame.py` and
`a1_evidence.py` remain archival frozen implementations, not operative entrypoints
under this amendment. An AST test proves all frame functions except the two host
adapters are unchanged. The additive manifest pins operative files and registrations;
old registered hashes remain checked against Freeze 1.2. R17 must be re-registered
for any future dependency change. Runtime registration pins the Python executable,
Unicode database and shared IDNA vectors. UTS46 is disabled.

IDNA provenance is offline: pre-existing source archive SHA256
`795dafcc9c04ed0c1fb032c2aa73654d8e8c5023a7df64a53f39190ada629902`, matching its
cached package-index release record; all ten vendored runtime/licence files match
archive members. `a1/provenance/idna-3.11.json` records evidence and limitations;
PKG-INFO is retained. Only package files and licence enter the import directory;
no build scripts, tests or caches. Local cache identity and byte pinning are the
registered supply-chain threat model, consistent with the existing vendored parser
approach. This is not independently signed upstream authentication and does not
protect against a malicious pre-existing cache or local administrator.

R17 parsing remains deterministic and offline: duplicate JSON/YAML mapping keys,
Python-equal YAML key collisions, NaN/Infinity/overflowed floats, cyclic aliases,
unsafe constructors, excessive aliases/depth/size, malformed documents and invalid
UTF-8 fail closed. They produce no leads; evidence-dependent predicates remain
UNRESOLVED. No remote references are loaded. Synthetic hostile fixtures only.

## Registrations and sealing

R07 is **NO_MACHINE_TRANSLATION / FAIL_CLOSED**, accepted by this explicit
prospective amendment. No translation or detector model runs. A required predicate
supported only by non-English evidence follows the frozen UNRESOLVED mechanism,
reason `TRANSLATION_NOT_AVAILABLE`; it is never silently negative. The English
first-party evidence route stays within the frozen navigation budget. Declared
language-related shrinkage remains reportable.

R08 remains conditional on actual installation attestations by each adjudicator.
No browser installation or candidate documentation inspection is claimed.
R16 is the unchanged anchored projector's byte-reproducible structural projection;
no historical outcome inspection or A1 comparison. Both approvals remain empty.

`registrations/record_seal.py` supplies custodian-owned offline persistence for two
preregistered human identities. Whole blocks are declared before intake. Each
record binds block, adjudicator, RDG, evidence digest, decision digest, UTC timestamp
and schema. A participant receipt contains only `sealed: true`. Reveal is refused
until both humans seal every required record in that block. Disagreement is retained.
SQL transactions serialize seal/reveal, reject duplicates/overwrite and recover
crashes; append-only triggers and hash chains detect corruption. Custodian-retained
external checkpoints detect rollback. No cryptographic identity authentication,
encryption, trusted timestamps or protection from a malicious custodian/admin is
claimed. Participants must have separate authenticated intake channels and no direct
store/interpreter/filesystem access; the trusted custodian enforces those controls.
No claim that a shared OS account provides participant isolation. Production requires
real signed roster records from a prospectively anchored commit; none exist here.
Only clearly labelled synthetic fixture IDs were used in tests, never registered as
humans. Actual human deployment/intake attestation is a G4 prerequisite.

R03, R04, R05, R06 and R16 human approvals remain UNFILLED. R09/R10 and Freeze-4
apparatus remain future execution blockers. Machine-package sealability does not
satisfy these human requirements or authorise crossing G1 in this task.

## Verification and scope

`a1/run_offline_121.py` runs all suites under an OS network deny sandbox, fixed
Python hash seed, early Python entropy/network guard inherited by subprocesses,
and synthetic inputs. Deterministic temporary names replace implicit Python random
seeding; each Python process claims its own empty scratch root (atomic `mkdir` on a
counter, removed at exit), because Python 3.14 tries only 20 names per `mkdtemp` call
and fixtures leaked by frozen `test_a1.py` exhausted the shared deterministic sequence
(takeover harness defect; test-only, no protocol effect). The takeover audit also made
non-finite YAML mapping keys fail closed (`NON_FINITE_NUMBER`) and added synthetic
B-first, wrong-block, malformed-decision and sealed-body tamper seal tests.
No experiment entropy is generated. OS/runtime internals may use randomness
for their own operation; the guard does not claim syscall-level prevention of that.
Tests do not contact a server to establish that the network sandbox works.
Validation includes frozen byte integrity, MULTI and helper hashes, JSON syntax,
R16 reproducibility, digest drift, D8/shared-host/path regressions, parser hostility,
sealing isolation/duplicates/tamper/crash/races and original A1/Freeze-1.1 suites.
The hostile review and generated report record actual results. Failure blocks sealing.
