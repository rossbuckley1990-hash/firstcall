# Programme A — Measurement / Rate Protocol

Status: **FREEZE-1 CANDIDATE — PROTOCOL ONLY. PROSPECTIVE. FROZEN BEFORE ANY VENDOR OUTCOME IS
OBSERVED. NOT EXECUTABLE.**
Design date: 2026-09-18. Hostile-reviewed for Freeze 1 at `65395d5a76caaed85a972a0902a9957777fac371`.
Zero real vendor runs, zero vendor API requests, zero credentials used in producing this design.

**Freeze-1 boundary (see Section 9.3).** Freeze 1 fixes *this protocol and the machine-readable
schemas only*. It occurs strictly **before** the sample-frame snapshot, the deterministic vendor
draw, the selected vendor list, any per-vendor journey mapping, any vendor-specific apparatus, and
any real vendor run. Nothing downstream of Freeze 1 exists yet.

**R02 grounding fact (incorporated, not a special case).** MULTI-001 Postmark P02-R02 was
historically graded `FALSE_SUCCESS` by verifier V1. Retrospective vendor-side forensics
(`docs/multi001-postmark-p02-r02-retrospective.md`;
`artifacts/multi-001/postmark/retrospective-forensics/p02-r02/forensics.json`; tag
`multi-001-postmark-p02-r02-forensics`, commit `65395d5`) conclusively observed the exact effect
— MessageID `74fdbaad-6b97-4d24-b16f-6d3e2b6990e6`, subject
`FIRSTCALL MULTI-001 POSTMARK 9906c79fc405 P02-R02`, Processed + Delivered,
`smtp;250 2.0.0 OK (sandbox blackhole)` — in Postmark's retained Activity. The historical
non-observation was a **verifier false negative**, i.e. the historical FALSE_SUCCESS was itself
wrong. Historical P02 remains immutably 2/3 under V1 and is **not** rewritten. Programme A
generalises this as a first-class evidentiary rule (Section 6.2–6.3), **not** as an exception.

## 0. Scope and separation from Programme B

FIRSTCALL is permanently split into two distinct programmes.

- **Programme A (this document) — RATE / MEASUREMENT.** *How often* can a fresh autonomous
  agent complete and independently verify a canonical real-world software journey under natural
  customer conditions? Programme A estimates a **rate over a defined population of vendors**. It
  makes no causal claim and runs no interventions.
- **Programme B — MECHANISM.** *Why* a journey fails and whether a controlled intervention
  causally changes the outcome. The Postmark P01/P02 counterfactual work and the Stripe
  `NOT_ELIGIBLE` documentary eligibility gate are Programme B methodology and are **out of scope
  here**.

Hard firewall between programmes:

1. Programme A must **never** select vendors because they look difficult, because an agent was
   observed to fail, or using any FIRSTCALL failure record. Vendor selection is by a public,
   pre-registered sample frame (Section 4) frozen before outcomes are visible.
2. Programme A must **never** apply the Programme B intervention sentence, documentary ablation,
   or counterfactual doc edits. Every Programme A run uses the *unmodified natural customer
   condition* (Section 3).
3. No Programme A artefact may modify MULTI-001, MULTI-002, or the five untracked `cf001` helper
   scripts. This document creates only new `docs/` and `experiments/programme-a/` files.

A Programme A result feeds Programme B only as a **hypothesis generator** *after* Programme A
outcomes are frozen — never the reverse, and never within a single frozen cohort.

---

## 1. Estimand

### 1.1 Unit of analysis

The **unit of analysis is the vendor**, not the run. A vendor contributes one **vendor-level
operability estimate** built from its `k` fresh independent runs (Section 5). Runs are the unit
of *observation*; the vendor is the unit of *inference*. Repeated runs against one vendor are
**never** treated as independent vendors: run-to-run correlation within a vendor is modelled as
clustering (Section 7). The population being generalised to is "vendors in the frozen sample
frame," not "all APIs."

### 1.2 Primary estimand

> **P_v = the population mean, over vendors in the frozen sample frame, of the vendor's
> probability that a single fresh autonomous agent run PROVEN_SUCCEEDs the canonical journey on
> its first integration attempt under the natural customer condition.**

Operationally we estimate `P_v` by the vendor-mean of the per-vendor PROVEN_SUCCESS rate
`r_v = PROVEN_SUCCESS_v / eligible_runs_v`, with vendor-clustered uncertainty. This is the
headline "how often does it work" number. It is a **run-level AFCR aggregated to a vendor mean**,
deliberately kept distinct from the quantities below.

### 1.3 Explicitly distinguished quantities (all reported; none conflated)

| Symbol | Name | Definition | Denominator |
| --- | --- | --- | --- |
| `P_v` | **Vendor-level pass rate (PRIMARY)** | Vendor-mean of per-vendor PROVEN_SUCCESS rate | vendors (eligible) |
| `AFCR_run` | **Run-level AFCR** | Pooled PROVEN_SUCCESS / eligible runs across all vendors | eligible runs |
| `FA` | **First-attempt success** | PROVEN_SUCCESS achieved within the one permitted effect-creating request, no rescue | eligible runs |
| `IVER` | **Independently verified effect rate** | Runs where the verifier independently confirms exactly one correct effect | eligible runs |
| `UNK` | **Ambiguity / UNKNOWN rate** | Runs graded UNKNOWN (transport, timing, pagination, identity ambiguity) | started runs |
| `FS` | **False-success rate** | Runs graded FALSE_SUCCESS under the strict evidence bar of Section 6 | started runs |
| `TTE` | **Time-to-effect** | Wall-clock from run start to first verifier-confirmed effect (successes only) | proven runs |
| `ACT` | **Agent actions / tool calls** | Count of model tool calls and shell/command events per run (distribution) | all runs |
| `RESQ` | **Rescue / intervention rate** | Runs in which any human/harness intervention beyond the frozen policy occurred | all runs — **must be 0** |

`RESQ > 0` invalidates the affected run (recorded, excluded from `P_v`, counted separately).
`AFCR` here means *verified first product outcome within one autonomous attempt*, not "first HTTP
request returned 200." Read-only exploration is unlimited; exactly one effect-creating request is
permitted (Section 2).

### 1.4 Denominator discipline

- `eligible_runs` = launched valid runs with a determinate PROVEN_SUCCESS / EFFECT_FAILED /
  FALSE_SUCCESS outcome. UNKNOWN and INELIGIBLE_PRE_EXECUTION are **excluded from success
  denominators and counted separately** (Section 7).
- A vendor with zero eligible runs has an **undefined** `r_v` (never 0); it is reported as
  "no estimate" and handled by the sensitivity analysis, not silently dropped.
- All denominators are frozen in Section 9 before the first run. No post-hoc denominator change.

---

## 2. Journey standard (vendor-neutral canonical journey)

Every vendor is mapped to the same six-stage journey. The concrete object differs; the
**epistemic standard is identical**. The mapping for each vendor is frozen (Section 9) before its
runs.

| Stage | Operational definition | Passing evidence |
| --- | --- | --- |
| **DISCOVER** | Agent locates the correct endpoint/object and the operational inputs it needs, from the natural condition surface (Section 3). | Trace shows identification of the target operation and required parameters. |
| **AUTHENTICATE** | Agent authenticates using supplied credentials without leaking them. | An authenticated read succeeds; no secret written to argv/files/logs. |
| **CONSTRUCT** | Agent assembles a valid single effect-creating request (correct object, params, mode, nonce). | Request captured pre-send with correct fields. |
| **EFFECT** | Agent issues **exactly one** effect-creating request that creates one sandbox-safe, reversible test object carrying the run nonce. | ≤1 create submission observed; SDK auto-retry disabled. |
| **VERIFY** | The **independent verifier** (separate credential) confirms the effect vendor-side within the bounded window. | Verifier predicates all pass (below). |
| **RECEIPT** | A canonical, hashed evidence receipt binds identity, journey, verification, and integrity. | `firstcall.programmeA.receipt.v1` produced and hash-sealed. |

### 2.1 What counts as an effect

An **effect** is a durable, vendor-side state change independently observable by a second,
read-scoped credential — e.g. one created test object (message, checkout session, record, file,
row) that the verifier can enumerate and retrieve. A 2xx HTTP response, an SDK return value, or
an agent claim is **not** an effect; it is at most a retrieval hint.

### 2.2 Effect requirements (frozen, identical across vendors)

- **Exactly one effect.** The journey requires precisely one created object. Zero = EFFECT_FAILED;
  two or more distinct objects = duplicate failure (FALSE if claimed success, else EFFECT_FAILED).
- **Reversible / sandbox-safe.** Test/sandbox mode only; no real money, no real recipient, no
  irreversible or externally-visible side effect. Objects persist through the verification window,
  then optional logged cleanup (never automatic deletion that destroys evidence before grading).
- **Independent vendor-side verification.** The verifier uses a **separate read-only credential**
  in the same account/sandbox and reads the vendor's own state. The agent's environment never
  contains the verifier credential.
- **IDs are hints, not proof.** A syntactically valid candidate-returned ID is a *retrieval hint*
  only. The verifier must **independently discover** candidate effects by enumeration even when
  the agent returns no ID, and must not let a claimed ID select the single row checked.

### 2.3 Verifier hardening (Postmark V2 lessons applied prospectively)

Carried forward from the Postmark verifier V2 audit and the MULTI-002 verifier design so we do
not re-learn them on live data:

- **Bounded observation window with a fixed schedule.** Observe at offsets **0, 5, 15, 30, 60 s
  after agent termination**. Never return success on the first match; schedule each round at the
  later of its offset or completion of the prior round. Per-request timeout 10 s; hard verifier
  deadline 120 s; ≤100 read requests/run. Exhaustion before complete terminal coverage ⇒ UNKNOWN.
- **Duplicate detection through the whole window.** Two complete terminal sweeps (≥30 s and ≥60 s)
  must agree on the single effect. Distinguish *repeated pagination rows* (same ID across pages =
  observation artefact) from *distinct duplicates* (two IDs = duplicate failure). Never collapse
  distinct effects while deduplicating.
- **Eventual consistency / stale exclusion.** An early empty response is **not** proof of absence.
  Require creation time within the run's temporal boundary; exclude pre-existing/stale objects by
  timestamp and nonce. A pre-run inventory snapshot defines "new."
- **Temporal boundary.** Capture server-time↔local-time relationship at run start; record run
  start and agent-termination times; only objects created within `[start, termination + window]`
  with the correct nonce are in scope.
- **Nonce / correlation strategy.** Each run receives a fresh unpredictable `RUN_NONCE`
  (≥128-bit) embedded in a vendor-appropriate correlation field (e.g. reference/metadata/subject).
  The verifier matches on nonce, not on agent-supplied IDs. If the vendor object has no writable
  correlation field, the mapping is frozen to use a deterministic unique attribute (amount+time
  window+account) and the ambiguity is pre-declared.
- **Transport ambiguity / idempotency.** Accepted-but-unobserved after the full window ⇒
  **UNKNOWN**, never automatic FALSE_SUCCESS. Where the vendor supports idempotency keys, the
  frozen effect request carries one so a transport retry cannot manufacture a duplicate; SDK
  automatic write-retries are disabled and a second create attempt halts the run (recorded).
- **Pagination.** Follow **every** page; count all new in-window objects including wrong-nonce
  ones; incomplete/looping/reordered pagination ⇒ UNKNOWN.
- **Synchronous acceptance is recorded as positive evidence.** The agent's own effect request and
  the vendor's *synchronous* response (HTTP status, vendor error/ok code, any vendor-assigned
  object id) are captured from the journey trace and stored as a distinct evidence field
  (`synchronous_vendor_acceptance`). A 2xx + vendor-accepted code + vendor-assigned id is
  **positive evidence that an effect was attempted and accepted by the vendor**. It is not by
  itself PROVEN_SUCCESS (independent read still required), but it materially constrains grading:
  it forbids an absence-based FALSE_SUCCESS (Section 6). This is the R02 correction made
  prospective — the synchronous acceptance in R02 was true; the verifier read was wrong.
- **Two independent observation paths where the vendor offers an authoritative audit surface.**
  The R02 effect was ultimately confirmed on Postmark's *Activity* log, a surface distinct from
  the enumeration API the historical verifier used. Prospectively: where a vendor exposes an
  authoritative delivery/audit/activity surface in addition to a primary enumeration/list API, the
  verifier mapping **must** query **both** paths for the nonce. This guards against a single-path
  false negative. Disagreement between paths (one observes the effect, the other does not) is
  **UNKNOWN + `verifier_path_disagreement`**, never a failure grade, and — because at least one
  authenticated authoritative path observed the effect — never FALSE_SUCCESS. Vendors with only
  one usable observation path are pre-declared as single-path in the mapping and carry a higher
  UNKNOWN risk by design, not a penalty.
- **Persist provenance.** For every observation store time, latency, HTTP status, safe request id,
  endpoint/params, cursors/counts, sanitized response projection, response digest, and decision
  reason. Hashing is tamper-evidence, not truth; the authenticated independent read is the source.

---

## 3. Natural customer condition

Programme A measures **realistic customer operability**, not a minimal-doc benchmark. The agent
receives what a competent developer would already have on day one, and nothing that leaks the
answer.

### 3.1 Five separated surfaces (frozen definitions)

| Surface | What it is | Programme A policy |
| --- | --- | --- |
| **VENDOR SURFACE** | Public docs, vendor-provided agent docs/skills, CLIs, MCP servers, SDKs, read-only API discovery. | **Permitted in full** (see 3.2). This is the realism we are measuring. |
| **CUSTOMER / ACCOUNT STATE** | The sandbox account and its pre-provisioned fixtures + supplied credentials/config that a real customer would have set up *before* the task. | Pre-provisioned identically per vendor mapping; frozen (Section 9). We do **not** penalise a vendor for setup that normally precedes the task. |
| **HARNESS STATE** | Workspace, network policy, timeouts, evidence capture, isolation. | Identical across all vendors/runs; frozen. |
| **AGENT BEHAVIOUR** | The model's autonomous actions/tool calls. | Observed, never coached. |
| **VERIFIER BEHAVIOUR** | Independent read-only vendor-side confirmation. | Isolated from agent; credentials never shared. |

### 3.2 What the agent MAY do (all permitted — this is the "natural" condition)

Browse public web documentation; use vendor-provided agent docs/skills; inspect environment
variables; inspect installed SDKs; use vendor CLIs; use vendor MCP servers; use web search;
follow documentation links; perform **safe read-only API discovery**; and read account metadata
available under the supplied credentials. These are enabled *uniformly for every vendor*. We are
measuring operability given the tools a real integrator has — not a stripped benchmark.

Constraints that keep it a measurement, not an intervention: read-only exploration is unlimited;
exactly **one** effect-creating request is allowed; automatic write-retry disabled; the agent
never sees FIRSTCALL records, other runs, this protocol, the verifier credential, or any
Programme B material; no human help; the agent must not print secrets.

### 3.3 Credentials / configuration supplied (anti-penalty rule)

To avoid confounding operability with account bootstrapping (which normally happens before the
task), each vendor mapping supplies, identically across that vendor's runs:

- A **customer credential** scoped to test/sandbox with the minimum capability to perform the
  journey and ordinary read discovery.
- A **separate read-only verifier credential**, held only by the harness.
- Any **pre-provisioned fixture** a normal customer would already own (e.g. an existing catalog
  object, a verified sender, a bucket) — provisioned outside measured runs, recorded with
  provenance, **identical across runs**.
- The **run nonce** and minimal identical runtime allowlist, isolated HOME/config, no unrelated
  credentials.

Setup that a real customer would have completed pre-task is provided as CUSTOMER/ACCOUNT STATE so
the run measures *first-call operability*, not *account creation*. What the agent must still do
autonomously is DISCOVER→RECEIPT. Which items are "normal pre-existing setup" versus "part of the
journey" is frozen per vendor in the mapping and justified from that vendor's own onboarding — not
chosen to make any vendor pass or fail.

---

## 4. Sample frame

The vendor-selection rule is **public, deterministic, and independent of any suspected agent
operability**. It is designed so FIRSTCALL cannot exercise discretion after outcomes are visible.

### 4.1 Frame construction (frozen snapshot)

1. **Frozen snapshot.** Choose one public, reproducible enumeration of software vendors/APIs with
   a datable snapshot — candidate frames to be fixed at freeze time, e.g. a public API directory
   (e.g. a programmable-web-style catalog), an open ecosystem index, or a category-tagged public
   registry. Record the source, exact snapshot date, retrieval method, and a SHA256 of the frozen
   snapshot file. Only one frame is chosen; alternates are recorded but unused.
2. **Category coverage.** Partition the frame into **≥6 software categories** (e.g. messaging/email,
   payments, storage/object, identity/auth, scheduling/calendar, docs/e-sign, data/CRM). Selection
   is **stratified** across categories to prevent a single-category result masquerading as a
   universal rate.
3. **Deterministic inclusion rules (all objective, applied to snapshot metadata only):**
   - Has public documentation.
   - Advertises a **test/sandbox mode** OR a free self-serve tier that supports a reversible
     effect. (Verified from *public docs only*, not by calling the API.)
   - Self-serve signup **without an enterprise sales contract**.
   - Supports at least one journey object meeting the effect requirements (Section 2.2) per its
     *public* docs.
   - Not FIRSTCALL-authored, not a prior FIRSTCALL experimental target where the outcome is known
     (Postmark, Resend, the local CF-001/Acme fixtures, and the MULTI-002 Stripe target are
     **excluded** to prevent outcome leakage; Stripe may only re-enter via the blind frame if the
     protocol is frozen and its Programme B outcome is not used to select it — default: exclude).
4. **Deterministic exclusion rules:** enterprise-contract-only; no safe test/sandbox capability
   per public docs; requires real money/PII/irreversible effect with no sandbox; region-locked or
   KYC-gated beyond a sandbox; duplicate of an already-included vendor (same platform).
5. **Ordering / draw.** Within each category, sort candidates by a **frozen deterministic key**
   (e.g. hash of vendor name salted with the pre-registered `RANDOMISATION_SEED`), then take the
   top `m` per category to reach the target `N`. This removes post-hoc discretion: the seed and
   algorithm are frozen before the draw and the draw is reproducible.

### 4.2 Enterprise-only and no-sandbox vendors

Vendors that inclusion-screen as enterprise-only or lacking safe sandbox are **excluded at the
frame stage by rule** (not after seeing an agent fail). If such a vendor is nonetheless drawn due
to ambiguous public metadata, it is marked **INELIGIBLE_PRE_EXECUTION** at the pre-execution
eligibility check (Section 6) and replaced by the **next vendor in the same category's frozen
ordering** — a replacement rule fixed *before* the draw. Replacements are logged with reason;
their ordering position is pre-determined so replacement cannot be steered by outcomes.

### 4.3 Anti-cherry-pick guarantees

- The frame, seed, algorithm, and full ordered draw (including reserves) are hashed and frozen
  (Section 9) **before** any run.
- Vendors are **never** added, removed, or reordered after outcomes are visible.
- No vendor is selected because a failure is already documented; prior-failure vendors are
  excluded, not sought.

### 4.4 How many vendors?

Twenty is a reasonable floor but chosen here on statistical, not convenience, grounds. With a
vendor-clustered proportion, the half-width of the Wilson interval on `P_v` is driven by the
number of **vendors**, and stratification needs enough per category. Recommendation:

- **Target N = 24 vendors** (≥6 categories × ~4 vendors/category), which gives balanced strata and
  a Wilson half-width on a mid-range `P_v` of roughly ±0.10–0.12 at the vendor level — adequate for
  a first defensible rate while staying cheap.
- Plus a **frozen reserve list** (next-in-order per category) sized to the expected
  INELIGIBLE_PRE_EXECUTION rate (budget ~25% ⇒ ≥6 reserves).

`N=20` is acceptable if cost-constrained; `N<16` is discouraged (strata too thin). The final `N`
is fixed at freeze; it is **not** changed after outcomes.

### 4.5 Blind-selection safeguard

The vendor list may be **drawn and hashed** now, but this document does **not** enumerate selected
vendors, and no operability inspection of any drawn vendor occurs until the full protocol
(Sections 1–9) is frozen. The draw artefact is committed as a hash first; the plaintext list is
revealed only inside the frozen pre-registration bundle. This prevents exposure to outcome
information before the protocol freeze.

---

## 5. Run design

### 5.1 Runs per vendor

**k = 5 fresh runs per vendor** is assessed as **adequate and near-optimal for a rate study** and
retained, because inference is at the **vendor** level: precision comes from `N` vendors, and
per-vendor runs mainly estimate within-vendor run variance and catch UNKNOWN/duplication. More
than 5/vendor spends budget on within-vendor precision that the clustered estimator barely uses;
fewer than 3 cannot separate a flaky vendor from a hard one. `k=5` gives per-vendor rates in
{0,.2,.4,.6,.8,1} and a usable within-vendor variance estimate. **Decision: N≈24 vendors × k=5
runs = ~120 eligible-target runs** — the cheapest design yielding a defensible clustered estimate.

### 5.2 Fixed vs varied agent/model

- **Model fixed and frozen** for the primary estimand (one model id + version), because Programme
  A estimates operability under a *held-fixed capable agent*, not a model comparison. The exact
  served model identity is captured per run; a drift/identity change **halts** comparison for
  affected runs (counted, excluded).
- **Temperature/settings frozen** (low/deterministic sampling where supported; exact settings in
  the config). A single **secondary** model may be run as a pre-registered sensitivity arm only if
  budget allows, analysed separately, never pooled into `P_v`.

### 5.3 Isolation and contamination controls

- **Fresh context** every run: no conversation history, no shared memory, no prior-run files.
- **Workspace reset:** a new ephemeral workspace per run; isolated HOME/config; no inherited
  credentials beyond the frozen allowlist.
- **Order randomisation:** run order is randomised across the full `N×k` matrix using the frozen
  seed, interleaving vendors and categories so time-of-day/rate-limit drift does not align with any
  vendor. No "all of vendor X, then vendor Y."
- **Time-of-day effects:** spread runs across ≥2 dayparts per the randomised schedule; record
  timestamps; include daypart as a covariate in sensitivity analysis.
- **Rate-limit effects:** per-vendor minimum spacing between that vendor's runs; back-off on 429 is
  a *harness* wait (not a rescue) and is logged; a run blocked purely by rate limits after
  exhausting the frozen wait budget ⇒ UNKNOWN, not EFFECT_FAILED.
- **Cross-run contamination:** nonces are unique per run; verifier scopes each run to its temporal
  boundary + nonce; a pre-run inventory snapshot per vendor separates new from prior effects.
- **Credential / account isolation:** one dedicated sandbox account per vendor is acceptable **iff**
  (a) test objects are cheap/reversible, (b) the nonce+temporal boundary make runs independently
  verifiable, (c) no run can observe another run's objects as its own, and (d) rate/quota supports
  `k` runs. If a vendor cannot support repeated safe trials in one account, the mapping either
  provisions `k` isolated sub-accounts or the vendor is INELIGIBLE_PRE_EXECUTION and replaced.

### 5.4 Cheapest defensible experiment

`~24×5` runs, one frozen model, sandbox-only reversible effects, one account per vendor where
safe, evidence captured once per run. No redundant re-runs, no pilots folded into results, no
optional stopping.

---

## 6. Grading — outcome taxonomy

Grades are assigned by the independent verifier + a frozen classifier, from evidence, **before**
any human sees the agent's self-report as decisive. Outcome, claim, execution status, and safety
are stored as **separate fields** so enum precedence cannot hide a material fact.

| Outcome | Definition | Enters `P_v` numerator? |
| --- | --- | --- |
| **PROVEN_SUCCESS** | Verifier independently confirms exactly one correct in-window effect satisfying all journey predicates; safety and evidence integrity pass; autonomous first-attempt establishment. | **Yes** |
| **EFFECT_FAILED** | Determinate wrong effect or determinate absence (trustworthy request/audit coverage), no success claim, no safety breach. | No |
| **FALSE_SUCCESS** | Explicit agent success claim **contradicted by determinate independent evidence** (see 6.1). | No (numerator); counted in `FS` |
| **UNKNOWN** | Transport exhaustion, incomplete pagination, ambiguous timing/identity, conflicting sweeps, possible delayed effect, missing integrity evidence. | No; excluded from success denominator; counted in `UNK` |
| **INELIGIBLE_PRE_EXECUTION** | Vendor fails the pre-execution eligibility check (no safe sandbox, enterprise-gated, missing fixture, unverifiable) **before** an agent runs. | No; excluded; triggers frozen replacement (Section 4.2) |
| *(reserved)* **UNSAFE_SUCCESS** | A verified effect accompanied by a safety violation. | **Never** in numerator; halts; recorded regardless of enum |

### 6.1 General evidentiary rule for effect claims (the R02 generalisation)

The R02 forensics prove a verifier can complete its full schedule and still **false-negative** a
genuine, vendor-delivered effect. Therefore *"the verifier looked and saw nothing"* is **not**, on
its own, determinate proof of non-existence, and must never by itself convict an agent of
fabrication. Programme A adopts these rules for **every** vendor and run (not as an R02 exception):

1. **Synchronous vendor acceptance is positive evidence.** A vendor's synchronous 2xx +
   accepted/ok code + vendor-assigned object id is positive evidence that an effect was *attempted
   and accepted*. It raises the floor on grading.
2. **Verifier non-observation is not fabrication evidence.** Failure of the independent read to
   observe an effect can arise from eventual consistency, verifier coverage limits, a single
   observation-path defect, or a genuine miss. None of these is evidence that the agent fabricated
   success.
3. **Incomplete or non-conclusive vendor observation resolves to UNKNOWN.** Any transport
   exhaustion, incomplete pagination, path disagreement, timing/identity ambiguity, or open
   eventual-consistency explanation ⇒ **UNKNOWN**, with a reason sub-code (Section 7.3).
4. **FALSE_SUCCESS requires determinate independent evidence contradicting an explicit success
   claim.** See the exact minimum in Section 6.3. Absence alone is never determinate when
   synchronous acceptance exists.
5. **Candidate-returned IDs aid correlation but are never sufficient alone.** A claimed id is a
   retrieval hint; grading requires independent nonce-based discovery on an authenticated vendor
   path.
6. **Later conclusive observation may establish verifier measurement error — append-only.** If a
   pre-registered later/authoritative observation (Section 6.4) conclusively observes the exact
   nonce-bearing effect, it establishes that an earlier non-observation was a verifier false
   negative. Such a correction may reclassify an **UNKNOWN** to PROVEN_SUCCESS as *append-only
   supplemental evidence*; it **cannot** rewrite a sealed primary receipt, and it never converts a
   FALSE_SUCCESS retroactively because FALSE_SUCCESS can only have been reached on determinate
   contradicting evidence in the first place.

### 6.2 FALSE_SUCCESS — minimum evidence (exact, exhaustive)

FIRSTCALL may grade a run **FALSE_SUCCESS only if the agent made an explicit success claim, the
independent verifier completed the full schedule and pagination on every configured observation
path with no exhaustion, AND at least one of the following determinate contradictions is
independently observed** — *never* by absence alone when synchronous acceptance is present:

- **(C-DENY) Synchronous denial contradicts the claim.** The vendor's own synchronous response to
  the agent's single effect request was a **rejection** (non-2xx, or a vendor error code / no
  object id) — i.e. the vendor never accepted an effect — **and** no in-window nonce-bearing
  object exists on any authenticated path. (Here absence *is* determinate because acceptance was
  affirmatively denied by the vendor.)
- **(C-PRED) An observed object contradicts a required predicate.** A nonce-correlated object is
  independently observed but violates a frozen predicate: wrong account, live mode when sandbox
  required, wrong nonce, wrong amount/quantity/mode, or completed/paid when forbidden.
- **(C-DUP) A determinate duplicate contradicts exactly-one.** Two or more distinct in-window
  nonce-bearing objects are independently observed (not repeated pagination rows), contradicting
  the exactly-one success claim.
- **(C-AUDIT) An authoritative vendor audit surface determinately shows non-existence.** A vendor
  whose authoritative audit/activity log is *complete and authoritative for the account/window*
  shows **no** such effect, this surface is distinct from and stronger than the enumeration path,
  and there is **no** synchronous acceptance to the contrary. Absent such an authoritative
  negative surface, non-observation is UNKNOWN.

If none of C-DENY / C-PRED / C-DUP / C-AUDIT is determinately met, the grade is **UNKNOWN**, not
FALSE_SUCCESS. **An agent self-report alone never determines FALSE_SUCCESS. Synchronous acceptance
followed only by verifier non-observation is UNKNOWN (the exact R02 situation).**

### 6.3 Worked application to R02 (illustration, not re-grading)

Under this rule R02 would grade **UNKNOWN** at primary window close (synchronous acceptance
present; enumeration path non-observed; no authoritative negative), then **PROVEN_SUCCESS** on the
append-only authoritative Activity observation. It would **never** be FALSE_SUCCESS. The historical
V1 FALSE_SUCCESS is preserved immutably as a Programme B artefact; this section changes only
Programme A's *prospective* behaviour, not the historical record.

### 6.4 Pre-registered later/authoritative observation (append-only)

Beyond the bounded primary window (0–60 s, Section 2.3), the verifier mapping **may** pre-register
one later authoritative observation (e.g. an authoritative audit/activity query at a fixed larger
offset, ≤ a frozen cap). It is **append-only supplemental evidence**: it may upgrade UNKNOWN→
PROVEN_SUCCESS when conclusive, is recorded in a separate supplemental receipt bound to the sealed
primary receipt by hash, and never mutates the primary receipt, the primary window grade
distribution, or any other run. Whether a vendor has such a surface is frozen at Freeze 4 from
public docs, identically across that vendor's runs.

---

## 7. Statistical analysis plan (frozen before data)

### 7.1 Primary

- **Primary estimand `P_v`** (Section 1.2): vendor-mean PROVEN_SUCCESS rate.
- **Estimator:** mean of per-vendor rates `r_v` (equal weight per vendor — the unit of inference),
  reported with a **vendor-clustered 95% CI**. Primary interval: **cluster bootstrap over
  vendors** (resample vendors with replacement, recompute the vendor-mean), ≥10,000 resamples,
  fixed bootstrap seed.
- **Wilson score interval** reported for the pooled run-level `AFCR_run` and for each per-vendor
  `r_v`. Wilson is the reference binomial interval because it behaves near 0 and 1 where
  Wald fails.

### 7.2 Wilson implementation notes (frozen)

- Compute `p̂ = s/n`, `z = 1.959964` (95%). Center `= (p̂ + z²/2n)/(1+z²/n)`;
  half `= z·sqrt(p̂(1-p̂)/n + z²/4n²)/(1+z²/n)`; interval `= center ± half`, clamped to `[0,1]`.
- **Near-zero serialization fix:** round interval bounds and any derived rate to a fixed decimal
  precision (e.g. 6 dp) *and* snap magnitudes `< 1e-9` to exactly `0.0` before serialization, so
  artefacts like `5.55e-17` never appear. Store as decimal strings with fixed precision, not raw
  floats. `n=0` ⇒ interval is `null` ("undefined"), never `[0,0]`.
- **Variance guard:** clamp the variance term `max(p̂(1-p̂), 0)` before `sqrt` so float error at
  `p̂∈{0,1}` cannot yield a NaN/negative root; clamp final bounds to `[0,1]`.

### 7.3 Handling UNKNOWN, missing data, and INELIGIBLE

- **UNKNOWN is sub-coded**, never a featureless dump: `{transport_exhaustion, incomplete_pagination,
  timing_ambiguity, identity_ambiguity, accepted_but_unobserved, verifier_path_disagreement,
  missing_integrity_evidence, rate_limited_after_wait_budget}`. The `UNK` rate is reported by
  sub-code so "measurement was hard" is itself an analysable finding.
- Primary analysis: UNKNOWN and INELIGIBLE_PRE_EXECUTION are **excluded** from success
  denominators and reported as their own rates (`UNK`, and a pre-execution ineligibility rate).
- **Attempted vs eligible (missing-data discipline).** `k=5` is the number of *attempted* runs per
  vendor; attrition to UNKNOWN can make eligible runs `< 5`. Per-vendor `r_v` uses that vendor's
  **eligible** runs. A vendor with **zero eligible runs** has `r_v = undefined` and is reported as
  an **indeterminate vendor** — it is **excluded from the `P_v` vendor-mean but its count and
  fraction are reported as a headline number**, never silently dropped and never scored 0.
- **Assignment bounds** reported alongside every rate: at run level, lower `= S/started`, upper
  `= (S + UNKNOWN)/started`; at vendor level, the vendor-mean is recomputed under
  "all-UNKNOWN-as-failure" and "all-UNKNOWN-as-success" (Section 7.5) so exclusions cannot
  manufacture apparent lift. No causal or complete-cohort claim unless the bounds are tight.
- INELIGIBLE vendors are handled by frozen replacement (Section 4.2); both the original and
  replacement are recorded. The ineligibility rate is itself a reported finding (it measures how
  many "listed" vendors are actually first-call-operable/safely-testable at all).
- **Every denominator is frozen at Freeze 1**; none is redefined after seeing outcomes.

### 7.4 Secondary estimands

`AFCR_run`, `FA`, `IVER`, `FS`, `UNK`, `TTE` (distribution + median), `ACT` (distribution),
`RESQ` (must be 0). Each with the same denominator discipline and, where a proportion, a Wilson
interval.

### 7.5 Stratification & sensitivity

- **Category stratification:** report `P_v` per software category; a category-weighted overall
  `P_v` is a pre-registered secondary (weights = equal per category) to check that the headline is
  not driven by one category.
- **Sensitivity analyses (all pre-registered):** (a) treat all UNKNOWN as failures (lower bound);
  (b) treat all UNKNOWN as successes (upper bound); (c) exclude vendors requiring rate-limit
  waits; (d) daypart covariate; (e) secondary-model arm if run; (f) leave-one-vendor-out on `P_v`.
- **No post-hoc denominator changes**, no optional stopping, no test swapped after seeing data.

### 7.6 No scoring/ranking product

Programme A produces a **measurement**, not a marketing leaderboard. Per-vendor rates are reported
for transparency and stratification only; no composite "vendor score," rank ordering, or
pass/fail badge is produced. Ranking is explicitly out of scope until valid measurement exists and
a separate, justified question demands it.

### 7.7 Informativeness under every outcome regime (design guarantee)

The design is **not** optimised toward finding failures and remains informative in all four corner
regimes; each is a valid, reportable result, not a study failure:

- **Every vendor passes** → `P_v ≈ 1` with a tight upper Wilson/bootstrap interval: a high measured
  first-call operability rate over the frame (still bounded to the frame, not "all APIs").
- **Every vendor fails** → `P_v ≈ 0`: a low operability rate; `EFFECT_FAILED` reason-codes and
  journey-stage attribution characterise *where* journeys break.
- **Most results UNKNOWN** → the `UNK` rate (by sub-code) and the **indeterminate-vendor fraction**
  become the headline: the finding is that *independent verifiability under natural conditions is
  the bottleneck*. `P_v` is reported only over the eligible subset with explicit assignment
  bounds; it is never inflated by treating UNKNOWN as failure or success.
- **Many vendors pre-execution ineligible** → the **pre-execution ineligibility rate** is the
  headline finding: most "listed" vendors are not safely first-call-testable; frozen replacement
  keeps the eligible cohort at target `N` while the ineligibility rate is reported in full.

No regime is treated as spoilage; each is pre-committed to publication (Section 8, 9.3).

---

## 8. Anti-bias controls (threat model → prospective control)

| Threat | Prospective control |
| --- | --- |
| **Vendor-selection bias** | Public frozen sample frame, deterministic seeded draw, hashed before any run (Section 4, 9); no discretionary additions. |
| **Survivorship bias** | Include vendors that turn out INELIGIBLE/hard; report the pre-execution ineligibility rate; frozen replacement, not silent dropping. |
| **Documentation-quality confounding** | Not controlled *away* — it is part of realistic operability and reported; but held constant *within* a vendor's runs (same natural surface each run). Category stratification separates it from vendor identity. |
| **Account-setup confounding** | Normal pre-task setup supplied identically as CUSTOMER/ACCOUNT STATE (Section 3.3); what counts as pre-existing is frozen per vendor from that vendor's own onboarding, not tuned to outcomes. |
| **Credential-scope confounding** | Customer credential scoped to the minimum for the journey + ordinary read discovery, identical across that vendor's runs; verifier credential separate and read-only; scopes recorded. |
| **Verifier false negatives (R02 class)** | Two independent observation paths where an authoritative audit surface exists; synchronous acceptance recorded as positive evidence; non-observation ⇒ UNKNOWN not failure; absence-based FALSE_SUCCESS forbidden when synchronous acceptance present (Section 6.1–6.2); append-only later authoritative observation can correct UNKNOWN→PROVEN; full schedule + pagination + two agreeing sweeps; verifier tested against hostile offline fixtures (incl. a synthetic R02 false-negative fixture) before any run. |
| **Vendor tool / SDK / CLI / MCP version drift** | Tool and SDK/CLI/MCP versions pinned in HARNESS/CUSTOMER state, identical across a vendor's `k` runs; a mid-cohort version change halts and is recorded, never silently mixed. |
| **Journey heterogeneity across vendors** | `P_v` is explicitly a rate over *heterogeneous* journeys of differing intrinsic difficulty, not a difficulty-normalised score; category stratification (7.5) and per-stage failure attribution separate journey difficulty from vendor identity; reported as a stated limitation, not corrected away. |
| **Browsing/search non-determinism** | Web content varies by time; the estimate is explicitly *conditional on the natural browsing surface at run time*; what was fetched is captured as provenance; interleaved randomisation prevents time-varying content aligning with any one vendor. |
| **Eventual consistency** | Bounded window with late sweeps; early empty ≠ absence; possible-delayed-effect ⇒ UNKNOWN. |
| **Agent prior-knowledge contamination** | Fresh context per run; nonce unpredictable; agent never sees FIRSTCALL records/other runs/this protocol; prior-knowledge is acknowledged as part of "natural" operability and not falsely attributed to docs. |
| **Model-provider bias** | Primary model fixed and disclosed; optional secondary model analysed separately, never pooled; served-model identity verified per run. |
| **Researcher rescue** | `RESQ` must be 0; any intervention beyond frozen policy invalidates the run (recorded, excluded); no coaching, no retry-after-ambiguous-write, no doc edits. |
| **Outcome-dependent exclusions** | Exclusion/replacement rules frozen before the draw; UNKNOWN/INELIGIBLE handled by pre-registered rule; assignment bounds reported. |
| **Repeated-run dependence** | Vendor is the unit of inference; within-vendor correlation modelled via cluster bootstrap; runs never counted as independent vendors. |
| **Publication bias** | Pre-registration (Section 9) commits to reporting **all** vendors, all outcomes, null and low rates, and the ineligibility rate, regardless of result. |
| **Time-of-day / rate-limit drift** | Randomised interleaved schedule, per-vendor spacing, daypart sensitivity, rate-limit waits logged as harness (not rescue). |

---

## 9. Pre-registration — freeze artefacts and sequence

### 9.1 Artefacts to freeze (each hashed; bundle hash sealed)

1. **Sample-frame snapshot** file + source + date + retrieval method + SHA256.
2. **Selection algorithm** (code) + parameters + SHA256.
3. **Randomisation seed** (`RANDOMISATION_SEED`) — committed as a hash first.
4. **Selected vendor list + full ordered draw + reserves** — committed as a **hash** first,
   plaintext revealed only inside the sealed bundle.
5. **Journey mapping** per vendor (object, effect, nonce field, fixtures, pre-existing setup).
6. **Agent configuration** (model id+version, temperature/settings, tool policy, timeout, network
   policy) + SHA256.
7. **Credential / configuration policy** (scopes, what is supplied vs must be discovered) — no
   secret values; keyed fingerprints only.
8. **Verifier specifications** (schedule, predicates, pagination, duplicate/UNKNOWN logic) + code
   hash + passing hostile-offline-test hashes.
9. **Outcome taxonomy** + classifier (Section 6) + code hash.
10. **Statistical analysis plan** (Section 7), including Wilson params, bootstrap seed, sensitivity
    list — frozen before data.
11. **Exclusion / replacement rules** (Section 4.2).
12. **Run IDs / run matrix** (N×k) with randomised order derived from the seed.
13. **Evidence schema** `firstcall.programmeA.receipt.v1` + canonical-JSON hashing algorithm.
14. **Code / test hashes** for runner, verifier, classifier, analysis.

### 9.2 Freeze sequence (so selection cannot follow outcomes)

1. **Freeze 1 — Protocol.** Sections 1–3, 5–8 and the schemas frozen and hashed (this document +
   `experiments/programme-a/*`).
2. **Freeze 2 — Frame & method.** Sample-frame snapshot, selection algorithm, `RANDOMISATION_SEED`
   **as a hash**, and the SAP frozen. No vendor plaintext yet.
3. **Freeze 3 — Blind draw.** Run the deterministic draw; commit the **hash** of the ordered vendor
   list + reserves. Still no operability inspection.
4. **Freeze 4 — Apparatus.** Runner/verifier/classifier/analysis code + hostile offline tests pass;
   hashes frozen. Per-vendor journey mappings frozen (built from *public* docs only, no runs).
5. **Freeze 5 — Seal & reveal.** Reveal seed + vendor-list plaintext *inside* the sealed
   pre-registration bundle; verify it matches the Freeze-3 hash. Only now may pre-execution
   eligibility checks and, subsequently, real runs begin.
6. **Execution.** Runs proceed in the frozen randomised order. Any change to Sections 1–9 after
   Freeze 5 invalidates the cohort and requires a new pre-registration; vendor selection can never
   be edited after outcomes are visible.

No real run occurs before Freeze 5. This document performs only design (pre-Freeze-1 content) and
creates no vendor apparatus.

### 9.3 Freeze-1 boundary (explicit chronology)

**Freeze 1 = protocol only.** It seals *this document* and *`experiments/programme-a/*.json`* (the
estimand, journey standard, outcome taxonomy, run design, sample-frame **rules** — not any list,
analysis plan, freeze sequence, and receipt schema). Freeze 1 fixes the science by which later
selection is bound. At Freeze 1 the following **do not yet exist and must not exist**:

1. sample-frame snapshot;
2. deterministic vendor draw / `RANDOMISATION_SEED` value (only its future commitment is defined);
3. selected vendor list (plaintext or hashed);
4. per-vendor journey mappings;
5. vendor-specific apparatus (runner/verifier/fixtures);
6. any real vendor run, credential use, or outcome datum.

Chronology is strictly ordered and one-directional: **Freeze 1 (protocol) → Freeze 2 (frame &
method) → Freeze 3 (blind draw, hashed) → Freeze 4 (apparatus & mappings from public docs) →
Freeze 5 (seal & reveal) → execution.** Because selection (Freeze 2–3) happens *after* the science
is sealed (Freeze 1) and the vendor list is hash-committed *before* reveal, vendor selection can
never be steered by, or altered after, any outcome. Editing Freeze-1 content after Freeze 2
reopens the whole sequence and voids any dependent selection.

---

## 10. Completion boundary

This turn creates `docs/programme-a-measurement-protocol.md` and machine-readable prospective
schemas/config under `experiments/programme-a/`. **No vendor-specific execution apparatus, no
sample-frame snapshot, no vendor draw, no credentials, and no runs were produced.** Zero real
vendor runs have occurred. MULTI-001, MULTI-002, and the five `cf001` helper scripts are
untouched. Nothing was committed, tagged, or pushed.
