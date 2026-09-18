# Programme A — Freeze 1.2: Population A1 consolidated amendment (prospective)

**Status: PROPOSED. Binding only when committed, tagged `programme-a-freeze-1.2-a1` and
pushed to `origin` by the protocol custodian.** Design date: 2026-09-19.

**Parents:**
- Freeze 1: `13ff44c37a96882553ffb9103a5596787555e0f3` (`programme-a-freeze-1-protocol`);
- Freeze 1.1: `4eaa6493924256dbeb888ff992a769a6b9c6d56d` (`programme-a-freeze-1.1-protocol`).

This amendment supersedes **only** the provisions listed in §15 and in
`experiments/programme-a/a1/supersession.json`. Everything else in Freeze 1 and
Freeze 1.1 remains operative. Where this text and the machine files disagree, use is
blocked.

## 1. Contamination boundary (as of this amendment)

| Item | Status |
| --- | --- |
| A1 membership retrieved | NO |
| A1 candidate identities observed | 0 |
| A1 frame constructed | NO |
| A1 entropy / permutation | NONE / NONE |
| A1 vendors selected | 0 |
| A1 eligibility decisions | 0 |
| A1 vendor API calls | 0 |
| A1 autonomous runs | 0 |
| A1 outcomes | 0 |

**Pre-design observations, recorded transparently.** During source-metadata review, one
request returned more than aggregates: the GitHub contents-API response for
`APIs-guru/openapi-directory/APIs` (a directory listing). The script reduced it to a
count (701 entries) before printing. No name was displayed, recorded or used.

A GitHub commits-API response was reduced to committer dates. Everything else observed
was metadata or aggregates:
- repository licence, creation date, last push and top-level layout;
- `metrics.json` counts (677 providers, 2,529 APIs, 3,992 specs, 166 unreachable, 688
  invalid, 25 unofficial);
- README inclusion criteria and licence text (summarised with names excluded);
- Wikidata aggregate counts;
- terms, robots.txt and API-documentation pages for GitHub and Zenodo;
- UK statute text;
- `git ls-remote` of the APIs.guru repository, which returned one SHA.

The prior-FIRSTCALL projector dry runs printed only statuses, paths and key names. The
researchers' general prior familiarity with public API directories is disclosed.

## 2. Why this amendment exists (history, not cleaned up)

1. **2026-09-18, about 20:00Z.** Freeze 2 was attempted and halted before any source
   request. Freeze 1.1 required a sealing certificate registering the capture roles; it
   was never issued.
2. **Freeze-1.2 rev1 (uncommitted).** It proposed automated Bing capture. It was withdrawn
   after external review found terms uncertainty. No Bing request was ever made.
3. **Freeze-1.2 rev2 (uncommitted).** It proposed GitHub repository search. It was
   rejected because GitHub-only discovery shifts coverage toward developer/open-source
   ecosystems, and because undocumented ranking and top-20 truncation weaken
   reproducibility. No search request was ever made.
4. **Metadata feasibility review.** No licensed search-free enumeration with a vendor-wide
   population definition was found. APIs.guru can define a narrower, honest population
   (A1).
5. **Hostile statistical review.** It established the S0 sequential design (§7).
6. **Documentary-access review.** It replaced automated capture with independent human
   reading (§9).

Both drafts are preserved read-only in `experiments/programme-a/quarantine/`, with
hashes and provenance.

## 3. Population A1

**A1 is the prospectively frozen population of canonical vendor platforms represented by
structural entries in the immutable APIs.guru OpenAPI Directory snapshot below, after
the frozen canonicalisation and designated-key rules.** It is not "all API vendors",
SaaS or software. Programme A's measurement standard stays source-agnostic, and A1 is
the first registered population of a multi-population programme (§13).

## 4. Source (frozen before membership retrieval)

| Item | Frozen value |
| --- | --- |
| Repository | `https://github.com/APIs-guru/openapi-directory.git`: community-maintained, independent of FIRSTCALL. Repository licence CC0-1.0; definitions acquired from public sources are held by APIs.guru under fair use. Stated criteria: public, long-lived, useful beyond owner. |
| Snapshot | **commit `f04b8d0bcd39c52e1cf3ad7a5fe744709832ae49`** (the value of `refs/heads/main` from `ls-remote` on 2026-09-18). At retrieval it must exist and have committer date ≤ T0 = 2026-09-17T00:00:00Z, otherwise HALT. No other commit, mirror or date may be substituted. Declared vintage: the automated refresh ended 2024-03-01. |
| Retrieval | Once, by the snapshot custodian after anchoring: `a1_frame.py --retrieve`. `git fetch` of the pinned commit, plus the Public Suffix List at its latest first-parent commit ≤ T0. The output directory is exclusive, so a second retrieval is refused. |
| Retained representation | Custody: git bundle (hash recorded). Published: commit/tree SHA, PSL commit/hash, `frame.json`, `raw-entries.json`, `retrieval.json`. Definition bodies are not republished. |
| Extraction | Raw entry = each `openapi.{json,yaml}` or `swagger.{json,yaml}` under `APIs/<provider>/…`. `source_record_id` = canonical JSON `["FIRSTCALL-A1", commit, null, path]`. |
| Canonicalisation | Structural key = NFC, lower-case, trailing-dot-stripped provider directory name; nothing else merges. Identity components = keys sharing a PSL registrable domain (non-DNS keys are singletons), computed mechanically. |
| Structural exclusions | XS1 (a file directly under `APIs/`) and XS2 (a provider directory with no spec file). Nothing else. |
| Conservation | Every raw entry maps to exactly one key; every key has ≥1 entry; components partition K; IDs are unique; K is unique and byte-sorted (`validate_frame`). |

## 5. Order of operations (A1 chronology)

| Step | Action | Gate |
| --- | --- | --- |
| 0 | Anchor this amendment | G0 |
| 1 | Retrieve the snapshot once | G1 |
| 2 | Extract raw entries | |
| 3 | Structural keys | |
| 4 | Identity components | |
| 5 | Structural exclusions | |
| 6 | **Seal K** (K_sha256) | |
| 7 | Prior-FIRSTCALL registry approved by both adjudicators | G2 |
| 8 | Adjudicators, translation tool and browser profile registered | |
| 9 | Entropy custodian and witness: one `os.urandom(32·|K|)` call; commitment recorded | G3 |
| 10 | **One uniform permutation of K; sealed** | |
| 11 | Blocks of 6 released one at a time; dual independent human screening; records sealed | G4 |
| 12 | Mechanical selection of the first 24 members of S | |
| 13 | Stop at the end of the block that holds the 24th member, or at exhaustion (M < 24: select all M; M < 16: A1 reported underpowered/uninformative; no substitute population) | |
| 14 | Seal the sample; reveal the tape | |
| 15 | Freeze-4 apparatus and mappings for the selected platforms | |
| 16 | Execution | G5 |

**There are no replacements. The frozen permutation is the only source of candidates.**

## 6. S — the resolved-eligible set

A key k ∈ K is in **S** if and only if all of the following hold:
- **(a)** its component's identity is resolved by agreement and k is the byte-smallest key
  of its platform (the designated key);
- **(b)** I1–I4 are agreed TRUE;
- **(c)** E1–E4, E6 (prior-FIRSTCALL) and the terms predicates T1–T3 are agreed FALSE;
- **(d)** at least one of C01–C07 is agreed TRUE;
- **(e)** there is no fatal stop by either adjudicator and no protocol deviation.

Everything else takes one of these terminal states:
- EXCLUDED (an agreed fatal predicate, or SCOPE_OUTSIDE);
- UNRESOLVED_ELIGIBILITY;
- UNRESOLVED_IDENTITY;
- STRUCTURAL_DUPLICATE;
- UNSCREENED (beyond the stopping point).

All of these are recorded, never selectable and never scored as failures. A C01–C07
vector that is incomplete is reported as INCOMPLETE and does not block eligibility.

## 7. Theorem (simple random sample from S)

*Let K be finite with |K| = N. Let S ⊆ K be fixed, with |S| = M ≥ n. Let π be a uniformly
random ordering of K, independent of S. Then the set of the first n members of S in π is
uniformly distributed over the C(M, n) subsets of S. For i, j ∈ S with i ≠ j,
Pr(i selected) = n/M and Pr(i and j selected) = n(n−1)/(M(M−1)).*

*Proof.* Write π|S for the order π induces on S. The map π ↦ π|S sends the N! orderings
of K onto the M! orderings of S, and every ordering σ of S has exactly N!/M! preimages:
choose the positions S occupies (C(N, M) ways), place S in order σ, then arrange K∖S
((N−M)! ways); C(N, M)·(N−M)! = N!/M!. So π|S is uniform. The first n elements of a
uniform ordering of S form a uniform ordered n-tuple, and hence a uniform n-subset. ∎

**Conditions of validity:**
- **Fixed S.** Every key's terminal status is a function only of its frozen evidence
  and the frozen procedure, never of its position, the quota state or the time.
  Mechanisms that enforce this: identical inputs; sealing before selection is computed;
  no re-adjudication; a component-level identity decision (§7.1); fatal-stop
  monotonicity (§8); terms and all documentary gates inside S (§11).
- **Blocks and stopping.** They do not change the selected set, because the first n
  members of S are defined whenever screening reaches the n-th one.
- **Exhaustion.** If M < n, the selection is all of S.

**§7.1 Designated key is order-independent.** Each adjudicator codes identity for the
**whole component**, from the union of all members' E1/E2 material. The input is the
same whichever member is reached first, so the designated key (the byte-smallest key of
each platform) is a fixed function of the component.

*Counterexamples showing the conditions are necessary* (both are offline tests):
- If a unit's status depends on its position (for example, leniency early on), uniformity
  fails.
- The naive prevalence estimate n/T is biased under stopping. The unbiased estimator of
  M/N is (n−1)/(T−1): E[(n−1)/(T−1)] = Σ_t C(t−2, n−2)·C(N−t, M−n)/C(N, M)
  = C(N−1, M−1)/C(N, M) = M/N.

## 8. Fatal-exclusion early stop

**Fatal predicates:**
- INCLUSION_FALSE:I1–I4;
- E1–E4 and E6;
- T1–T3.

**Rule.** An adjudicator who affirmatively establishes a fatal predicate seals a record
with `fatal_stop` set to it and stops reading that key. Once both records are sealed:
- if both affirm the **same** fatal predicate, the key is **EXCLUDED**, and no further
  budget is spent;
- otherwise the normal combination applies.

**Proposition: an early stop never changes S-membership.**
- A key is in S only if every inclusion is agreed TRUE, every exclusion and terms
  predicate is agreed FALSE, and neither adjudicator stopped.
- If adjudicator A affirmed fatal predicate f, the frozen monotonicity rule says any
  continued reading leaves A's code for f affirmed, or makes it UNRESOLVED on
  contradiction. It never becomes the opposite affirmative code.
- In both cases the key fails the requirement for S. So whether A stops or continues,
  the key is not in S.
- The stop can change only the label (EXCLUDED rather than UNRESOLVED) and the number of
  co-occurring reasons recorded. ∎

This is checked by a 20,000-case randomized test and by direct cases.

## 9. Documentary eligibility model (dual independent human adjudication)

**Adjudicators.** Two distinct registered natural persons. No model- or
third-party-generated codes.

**Inputs.** Both receive the same E1 material (the pinned snapshot's definitions for the
component), the same E2 starting links and the same frozen protocol
(`decision-protocol.json`). Each reads independently. Neither sees the other's evidence
or codes until both records for the block are sealed.

**Evidence hierarchy:**
- **E1** (snapshot) gives leads and hints only.
- **E2** starting links are only:
  - `x-origin` URL;
  - `externalDocs` URL;
  - `termsOfService`;
  - `contact.url`;
  - `servers`.
- **E3** is explicitly licensed documentation. Its licence changes only what may be
  retained.
- **E4** is logged-out human browser reading of public first-party pages via visible
  links.
- **E5** (vendor APIs) is excluded.
- **E6** (search engines, guessed URLs, reviews, model memory, mirrors, drafts, prior
  outcomes) is excluded.

**Navigation:**
- links whose path contains a frozen vocabulary term (the Freeze-1.1 list);
- a fixed target order;
- depth ≤ 2;
- identity: 16 pages / 60 minutes per component;
- eligibility and categories: 16 pages / 60 minutes;
- terms: 6 pages / 20 minutes;
- one retry after ≥ 30 minutes.

**Browser.** A registered pinned clean profile with UK egress, never logged in.

**Prohibited:**
- search engines;
- guessed URLs;
- login;
- vendor API calls;
- automated scraping or bulk download;
- creating archive copies.

**Evidence record** (schema `evidence-record.schema.json`): URL, UTC timestamp, page
title, tier, factual proposition, predicate, code, reason, a minimal excerpt only where
appropriate, adjudicator id, record SHA256, and an optional pointer to an existing public
archive.

**Not retained by default:** full HTML/PDF/page copies and screenshots.

**Access controls.** Technical access controls and explicit access restrictions are
respected, never circumvented. The protocol draws no legal conclusion. Any commercial or
non-research publication of the records requires a separate legal-review gate.

## 10. UNRESOLVED (fail-closed)

A predicate is UNRESOLVED, never silently negative or eligible, when:
- evidence is insufficient within budget;
- required evidence is login-gated;
- authoritative documentation conflicts;
- evidence is inaccessible after the frozen retry;
- the translation is uncertain;
- the adjudicators disagree;
- there is a protocol deviation;
- terms relevant to execution are ambiguous, or require login or acceptance to read.

A login wall on every documentation lead is an affirmative observation (I1 = FALSE).
Because UNRESOLVED shrinkage can favour unusually well-documented platforms, the
unresolved rate (identity and eligibility, with hypergeometric CIs) is reported
prominently as a limitation.

## 11. Execution-stage terms gate — inside S

**Predicates (applicable first-party terms):**
- **T1:** explicit prohibition of the automated agents the journey requires.
- **T2:** explicit prohibition of benchmarking or testing of that kind.
- **T3:** explicit prohibition of publishing the derived result or evidence.

An affirmed T1–T3 is EXCLUDED, recorded as documentary pre-execution ineligibility.
Terms that need login or acceptance to review, and materially ambiguous restrictions,
are UNRESOLVED. FALSE means the applicable terms were located and read within budget and
no explicit prohibition was observed. It is reported neutrally as
NO_EXPLICIT_RESTRICTION_OBSERVED, never as permission.

**Hostile finding.** Applying this gate *after* a platform enters the first 24 would
either force a replacement (next member of S∖gate, which is outcome-adjacent discretion)
or make the analysed set a data-dependent subset. So T1–T3 are part of S and are applied
before a key counts. Only facts impossible to observe before signup — terms or KYC
surfaced at account creation — can arise after selection. Such a platform is sealed
SELECTED_NOT_EXECUTABLE: it is indeterminate (n_i = 0), widens the band through
L_i = 0, U_i = 1, and is never replaced.

## 12. Screening campaign

**Blocks and release:**
- blocks of 6 keys;
- the custodian releases block b only after block b−1 is sealed;
- keys within a block are presented in a hash-shuffled order with no positions shown;
- both readings of every key in the block happen within **48 hours** of release;
- at most 3 blocks per week.

**Expected screening for n = 24 over |K| ≈ 701:**

| S-prevalence | Keys screened | Blocks | Weeks (at 3 blocks/week) |
| --- | --- | --- | --- |
| 30% | 80 | 14 | ~5 |
| 20% | 120 | 20 | ~7 |
| 15% | 159 | 27 | ~9 |
| 10% | 237 | 40 | ~14 |

**Planning bound: 26 weeks.** Exceeding it is a recorded deviation. It never truncates
the sample, because a time cut-off could depend on how hard units are to adjudicate.

**Diagnostics** (they never alter the sample):
- a Cochran–Armitage trend test of the S indicator and the UNRESOLVED indicator against
  block index;
- per-adjudicator UNRESOLVED, fatal-stop and disagreement rates.

## 13. Verification, estimand, precision, multi-population

**Verification (Freeze 1 §2.3 and §6, unchanged).**
- Returned IDs are hints, never proof on their own.
- Independent vendor-side observation.
- A bounded schedule.
- Complete pagination.
- Nonce plus temporal boundary.
- Stale-effect exclusion.
- Exactly one effect.
- Idempotency where available.
- Transport or observation ambiguity → UNKNOWN.
- Synchronous acceptance followed by inconclusive non-observation → UNKNOWN.
- FALSE_SUCCESS only on an explicit claim, with complete, determinate, contradictory
  evidence and no unresolved observation ambiguity.

**Estimand.** P_A1 = mean over platforms i ∈ S of p_i, where p_i is the probability of
PROVEN_SUCCESS given a valid determinate run, under the frozen Freeze-1 condition.
- Equal-platform weighting: each selected platform contributes r_i = S_i / n_i over its
  k = 5 runs.
- The primary estimate is the mean of r_i over selected platforms with n_i > 0.
- **n = 24, k = 5, target runs = 120.**

**Precision.** Freeze-1.1 §8.6 band with one stratum: e = √(ln 40 / 24) ≈ **0.392**,
before indeterminate-vendor widening. **A1 does not give narrow population precision.**
The secondary descriptive bootstrap resamples the selected platforms.

**Reported separately:**
- the primary estimate and band;
- the UNKNOWN rate by sub-code;
- the FALSE_SUCCESS rate;
- the indeterminate and SELECTED_NOT_EXECUTABLE counts;
- the unresolved screening rate;
- exclusion counts by predicate;
- structural duplicates;
- T, (n−1)/(T−1) and the overshoot;
- the descriptive category mix;
- snapshot age and coverage;
- OpenAPI-directory selection bias;
- the diagnostics.

Eligibility prevalence is **never** multiplied into, or combined with, the success rate.
No claim is made about all API vendors, SaaS or software. No rankings are produced.

**Multi-population.**
- Future populations (A2, A3, …) may use other independently defined enumerations under
  the same standard, each registered prospectively.
- There is no automatic pooling. A pooled estimand needs its own preregistered
  superpopulation, with identity and multiplicity across populations.
- Consistency across populations is replication and generalisation evidence, not a
  licence to claim universal representativeness.

## 14. Roles, gates, prior-FIRSTCALL

See `experiments/programme-a/a1/roles.json`. Any missing mandatory role keeps its gate
**CLOSED**.

**Designated, binding on anchoring:**
- R01 protocol custodian: Ross Buckley;
- R02 source/snapshot custodian: Ross Buckley.

**Unfilled:**
- R03 entropy custodian;
- R04 entropy witness;
- R05/R06 adjudicators;
- R07 translation tool;
- R08 browser profile;
- R16 registry approval.

**Future stage:**
- R09 execution scheduler;
- R10 verifier/apparatus reviewer.

**Registered software and documents:** R11–R15.

Adjudicators and translation must be registered **before entropy**, so no adjudicator is
chosen with knowledge of the order.

**Prior-FIRSTCALL.** Projector v1.2.1 is carried forward byte-identically from the rev2
draft. Its structural rule separates actual experimental targets from incidental,
example, policy-field and prose mentions without reading outcome values (hostile tests
pass). Its dry run at `13ff44c` reports no unrecognised designations. The four named
mandatory exclusions still apply. The registry gate G2 stays closed until both
adjudicators approve the full ledger, including the path-flagged
`experiments/multi-001/candidates.json`.

## 15. Supersession table

Machine-readable: `experiments/programme-a/a1/supersession.json` (rows plus discovery
stages plus evidence classes plus the list of unchanged operative provisions).

Discovery stages: **D0** 2026-09-18 ~20:00Z: Freeze-2 implementation attempt halted before any source request (missing registrations); **D1** 2026-09-18: external review of uncommitted Freeze-1.2 rev1 (Bing HTML terms uncertainty); **D2** 2026-09-18: reviewer rejection of uncommitted Freeze-1.2 rev2 (GitHub-only search discovery); **D3** 2026-09-18/19: source-metadata feasibility study; **D4** 2026-09-19: hostile statistical design review; **D5** 2026-09-19: documentary access-model review; **D6** 2026-09-19: consolidation (this amendment).

Evidence classes: **EV0** protocol text and repository structure only; no source or vendor observation; **EV1** terms, robots.txt and API-documentation pages (GitHub, Zenodo); zero discovery requests; **EV2** APIs.guru repository metadata, commit dates, aggregate metrics, README criteria; one listing reduced to a count (701) without display; Wikidata aggregate counts; **EV3** offline calculations only; **EV4** UK statute text (CDPA ss.29A, 30); **EV5** prior-FIRSTCALL projector dry-run summaries at 13ff44c (statuses, paths, key names only; no outcome values); **EV6** git ls-remote of APIs.guru (ref names and one SHA).

| ID | Old rule | Source clause | New rule | Why changed | When discovered | Evidence observed before change | Bias risk | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SUP-01 | Choose one public reproducible enumeration; alternates recorded but unused | Freeze 1 §4.1(1); sample-frame.config frozen_snapshot | A1 is defined by one named, pinned source: APIs.guru openapi-directory commit f04b8d0 (a1-population.json) | Freeze 1.1 had already replaced it with search discovery; that mechanism failed (SUP-02) | D3 | EV2, EV6 | source chosen by the researchers from metadata; OpenAPI-listing bias declared in the estimand | SUPERSEDED |
| SUP-02 | Discovery by public Bing web-search HTML: four queries, logged-out GB/English, top 20 organic | Freeze 1.1 §3 para 1; §8.2; rules.source_universe.engine/queries/capture | No discovery step. A1 membership is the pinned snapshot's structural entries | terms uncertainty over automated retrieval, parsing and archival of Bing HTML | D1 | EV0 | none introduced; removes search-ranking dependence | SUPERSEDED |
| SUP-03 | Use all qualifying enumerations; union; >=2 independently controlled maintainers | Freeze 1.1 §3 para 4 | Single-source population A1; other sources become separately registered populations A2, A3, ... (never pooled automatically) | no second licensed machine-readable enumeration with a compatible population definition was found from metadata; a heterogeneous union would not define a population | D3 | EV2 | single-source coverage; addressed by explicit A1-only claim and the multi-population architecture | SUPERSEDED |
| SUP-04 | Source screening of discovered results: four metadata pages, 20 min per source, SOURCE_ELIGIBLE/INELIGIBLE/UNRESOLVED, source lock | Freeze 1.1 §3 paras 2-3; §8.2 para 3 | Removed; the source is fixed by this amendment and its metadata recorded in a1-population.json | no discovery results exist to screen | D3 | EV2 | source suitability judged once, at design, by the researchers | SUPERSEDED |
| SUP-05 | Latest complete immutable version <= T0 of each qualifying source | Freeze 1.1 §3 para 5 | Pinned commit f04b8d0; at retrieval it must exist and have committer date <= T0 = 2026-09-17T00:00:00Z, else HALT; T0 unchanged | pinning removes any retrieval-time choice; T0 kept | D6 | EV2, EV6 | none; listing vintage (automated refresh stopped 2024-03-01) is a declared staleness limitation | RETAINED_MODIFIED |
| SUP-06 | Per-source parser locked from documented schema; source_record_id [source, version, native id, row address]; preserve every row | Freeze 1.1 §3 para 6 | Raw entry = spec file path under APIs/<provider>/ at the pinned commit; source_record_id [FIRSTCALL-A1, commit, null, path]; a1_frame.py frozen by digest | source is now a repository tree, not a tabular export | D6 | EV2 | structural definition could over- or under-count providers with unusual layouts; conservation checks and published ledger | RETAINED_MODIFIED |
| SUP-07 | Sampling unit = control plane; all pairwise identity relations recorded; any UNRESOLVED relation or missing anchor blocks the entire Freeze 2 | Freeze 1.1 §2 paras 1-4; §8.3 paras 2-4 | Randomisation unit = structural key; identity components by registrable domain computed mechanically; per-component identity adjudication only when a member is screened; designated key = byte-smallest key of each platform; UNRESOLVED_IDENTITY is a unit-level terminal state | all-pairs identity over the whole frame requires full-population adjudication before sampling, which the sequential design removes; the designated-key indicator is order-independent (proof §7) | D4 | EV3 | cross-registrable-domain duplicates of one platform get extra entry points (declared residual; flagged and sensitivity-tested if two selected units prove identical) | SUPERSEDED |
| SUP-08 | Identity capture per distinct lead group (16 pages, 60 min) before unit resolution | Freeze 1.1 §8.3 para 1 | Identity capture per component, only for components reached in the permutation; 16 pages / 60 min per adjudicator; input is the whole component | workload; keeps identity input independent of which member is reached first | D4 | EV3 | none beyond SUP-07 | SUPERSEDED |
| SUP-09 | Partition into >=6 categories; stratified selection | Freeze 1 §4.1(2); sample-frame.config categories_min, stratified | S0 unstratified primary sampling; C01-C07 descriptive only | stratum sizes of the eligible population are unknown without full screening; stratified sequential designs need estimated weights, invalidate the bounded band and let the rarest stratum drive workload | D4 | EV3 | category mix of the sample is random (reported), no category balance guarantee | SUPERSEDED |
| SUP-10 | Complete membership vector required; any UNRESOLVED membership => UNRESOLVED_ELIGIBILITY; hash assignment fixes the stratum | Freeze 1.1 §2 paras 6-7; §8.1 | Scope requires >=1 category agreed TRUE; all seven agreed FALSE => SCOPE_OUTSIDE; an incomplete vector is reported INCOMPLETE and does not block eligibility; the Freeze-1.1 hash assignment is computed only descriptively, after the sample is sealed | membership completeness only mattered for stratum assignment, which no longer controls inclusion; avoids unnecessary UNRESOLVED shrinkage | D6 | EV0 | reduces, not increases, documentation-quality shrinkage | RETAINED_MODIFIED |
| SUP-11 | Hamilton proportional allocation of N=24 across seven strata; Freeze 2 fails if any stratum lacks capacity | Freeze 1.1 §6 para 1 | Removed | no strata in the primary design | D4 | EV3 | none | SUPERSEDED |
| SUP-12 | Salted vendor-name hash ordering (Freeze 1); per-stratum permutation from a 32*M tape generated after the eligible frame is sealed (Freeze 1.1) | Freeze 1 §4.1(5); sample-frame.config ordering; Freeze 1.1 §6 paras 2-3; §8.5 paras 3-4 | ONE uniform permutation of sealed K from a 32*\|K\| os.urandom tape generated after K is sealed and BEFORE any eligibility adjudication; tie aborts; commitment before interpretation | eligibility is no longer known before ordering | D4 | EV3 | order becomes visible to screening (see SUP-15 mitigations) | SUPERSEDED |
| SUP-13 | INELIGIBLE_PRE_EXECUTION => replaced by next vendor in the same category's frozen ordering; Freeze-5A census of all eligible units; final pi = m_h/G_h | Freeze 1 §4.2; §6 table; §7.3; sample-frame.config replacements; Freeze 1.1 §6 paras 5-6; §8.5 paras 5-6 | No replacement of any kind. Documentary and terms gates are part of S and are applied BEFORE a unit is counted; post-selection non-executability => SELECTED_NOT_EXECUTABLE, indeterminate, never replaced | replacement after selection is outcome-adjacent discretion; gating inside S keeps the SRS proof exact | D4 | EV3 | post-selection failures widen the band rather than being hidden | SUPERSEDED |
| SUP-14 | Reserves >= 6; reserve budget 25% | Freeze 1 §4.4; sample-frame.config reserves_min, reserve_budget_fraction | Removed; the permutation remainder is the only candidate source | no reserve concept under sequential selection | D4 | EV3 | none | SUPERSEDED |
| SUP-15 | Draw hashed and blind; selection status and order withheld until Freeze 5B; census personnel blind to ordering | Freeze 1 §4.5; §9.2; Freeze 1.1 §8.5 para 4; §8.7 | Order held in custody by R03; one block of 6 released at a time in hash-shuffled presentation order without positions; statuses sealed before selection is computed mechanically | sequential screening necessarily exposes the current block | D4 | EV3 | screeners can guess that eligible units in early blocks are likely selected; mitigated by blocks, sealing, dual independent coding, drift and per-adjudicator diagnostics; residual declared | SUPERSEDED |
| SUP-16 | Single seven-calendar-day documentary capture window for the whole batch; missing it blocks the batch | Freeze 1.1 §4 para 2; §8.3 para 1 | Per-block 48-hour windows; at most 3 blocks/week; 26-week planning bound (exceeding it is a recorded deviation, never a truncation) | human reading of ~100-250 keys cannot fit seven days | D5 | EV3 | documentary drift over a longer campaign; position-drift diagnostic | SUPERSEDED |
| SUP-17 | Automated byte-ordered BFS frontier, 2 MiB/page, 30 s requests, one retry on timeout/429/5xx, automated archive | Freeze 1.1 §4 para 3 | Human logged-out browser reading from E2 leads via visible first-party links with the frozen vocabulary; 16 pages, depth 2, 60 min; frozen target order; one retry after >= 30 min | automated retrieval and archival of arbitrary vendor sites has no established access basis | D5 | EV4 | human navigation varies; disagreement becomes UNRESOLVED (shrinkage declared) | SUPERSEDED |
| SUP-18 | Two adjudicators receive identical captured packets | Freeze 1.1 §4 para 4 | Identical inputs (E1 material, E2 leads, protocol); independent reading and evidence records | no automated packet exists; a single collector would be an unregistered third adjudicator | D5 | EV0 | more UNRESOLVED from navigation differences (declared) | SUPERSEDED |
| SUP-19 | Collect the whole permitted frontier even after an exclusion is found | Freeze 1.1 §4 para 3 | Fatal-exclusion early stop: an adjudicator who affirms a fatal predicate seals and stops; both affirming the same fatal predicate => EXCLUDED | workload; proof §8 shows S-membership cannot change | D5 | EV3 | fewer co-occurring exclusion reasons recorded (reason reporting is per affirmed predicate) | SUPERSEDED |
| SUP-20 | Captured evidence with source URL/hash/excerpt, archived pages and error metadata | Freeze 1.1 §4 paras 1, 3 | Minimal evidence record (URL, UTC time, title, tier, proposition, predicate, code, reason, minimal excerpt, adjudicator, record SHA256, optional existing archive pointer); no page copies or screenshots by default | raw archival is not needed for decisions and its permission is not established | D5 | EV4 | observations are auditable but not re-observable; declared | SUPERSEDED |
| SUP-21 | Terminal states ELIGIBLE/EXCLUDED/UNRESOLVED_ELIGIBILITY over the canonical union; conservation TOTAL = E + X + U | Freeze 1.1 §4 paras 5-6; rules.eligibility.conservation | Terminal states over K: RESOLVED_ELIGIBLE, EXCLUDED, UNRESOLVED_ELIGIBILITY, UNRESOLVED_IDENTITY, STRUCTURAL_DUPLICATE, plus UNSCREENED; \|K\| = sum of all; SELECTED_NOT_EXECUTABLE recorded post-selection | sequential design leaves most of K unscreened by construction | D4 | EV3 | none; every key accounted | RETAINED_MODIFIED |
| SUP-22 | (none) no explicit terms-of-use predicates | Freeze 1 §4.1(3)-(4); Freeze 1.1 rules.eligibility | New predicates T1-T3 (automated-agent, benchmarking/testing, publication prohibitions) inside S; login-gated or ambiguous terms => UNRESOLVED; absence => NO_EXPLICIT_RESTRICTION_OBSERVED (neutral) | a post-selection terms gate would require replacement or break the SRS proof | D5 | EV0 | excludes platforms with restrictive or unreadable terms from S (declared population restriction) | NEW_RULE |
| SUP-23 | 60 active minutes per unit per adjudicator for eligibility/category | Freeze 1.1 §4 para 4 | Eligibility and category 60 min / 16 pages; terms 20 min / 6 pages; identity 60 min / 16 pages per component | terms gate added; identity stage restructured | D6 | EV0 | identical budgets for every key | RETAINED_MODIFIED |
| SUP-24 | P_v over census-eligible G; W_h = G_h/G; band C = sum W_h^2/m_h; within-stratum bootstrap | Freeze 1.1 §8.6 | P_A1 over S; band with W = 1, C = 1/n_selected; bootstrap over selected platforms; post-selection non-executable = indeterminate | census and strata removed | D4 | EV3 | none; the band remains conservative (half-width ~0.39 at n = 24) | RETAINED_MODIFIED |
| SUP-25 | Category-weighted overall P_v as a preregistered secondary | Freeze 1 §7.5 | Removed; per-category rates of selected platforms are descriptive only | category sizes in S are unknown; weights would be estimated from a small sample | D4 | EV3 | none | SUPERSEDED |
| SUP-26 | Design weights w_i = G_h/m_h; weighted complete-case ratio | Freeze 1.1 §6 para 7 | Equal weights (SRS from S): plain complete-case mean | SRS makes the Hajek estimator the plain mean | D4 | EV3 | none | SUPERSEDED |
| SUP-27 | Freeze sequence 1 -> 2 -> 3 -> 4 -> 5 and the Freeze-1.1 §8.7 chronology | Freeze 1 §9.2-9.3; prereg-freeze-sequence.json; Freeze 1.1 §7, §8.7 | A1 chronology (amendment §5): anchor -> snapshot/K seal -> registry approval -> adjudicator/translation registration -> entropy -> permutation seal -> block screening -> sample seal -> Freeze-4 apparatus -> execution | ordering now precedes eligibility | D4 | EV3 | none | SUPERSEDED |
| SUP-28 | N = 24 justified as >=6 categories x ~4 vendors | Freeze 1 §4.4; §5.1 | n = 24 resolved-eligible platforms, k = 5, 120 target runs; justification is cost, not category balance; precision stated honestly | stratification removed; n = 60 was considered and not adopted | D6 | EV3 | wide primary band; no narrow-precision claim | RETAINED_MODIFIED |
| SUP-29 | INELIGIBLE_PRE_EXECUTION as a pre-run grade that triggers replacement | Freeze 1 §6 table; outcome-taxonomy INELIGIBLE_PRE_EXECUTION | Documentary pre-execution ineligibility is an EXCLUDED reason inside S (T1-T3, E1-E4); post-selection non-executability is SELECTED_NOT_EXECUTABLE (indeterminate), never replaced | see SUP-13 | D4 | EV3 | none | RETAINED_MODIFIED |
| SUP-30 | Exhaustion: G_h < m_h stops the cohort | Freeze 1.1 §6 para 5; §8.5 | Permutation exhausted with M < 24 => select all M; M < 16 => reported underpowered/uninformative; no substitute population | no strata; M is a population fact, not an outcome | D4 | EV3 | none | SUPERSEDED |
| SUP-31 | Source-level coverage reporting (overlap matrix, union size, source-exclusive units) | Freeze 1.1 §3 para 9 | A1 reporting list (estimand.json reported_separately) | single source | D6 | EV0 | none | SUPERSEDED |
| SUP-32 | Prior-FIRSTCALL designation projection (rev1 trigger: any vendor\|target\|provider-named key) | Freeze 1.1 §5; §8.4 (projector first implemented in uncommitted Freeze-1.2 rev1) | Projector v1.2.1: value-type structural trigger, fenced Markdown ignored, example paths block; approval by both adjudicators before entropy | rev1 trigger false-positive on a boolean policy field (experiments/resend-001/policy.json) | D2 | EV5 | structural rule tuned after one false positive; hostile tests cover true targets, nesting and examples | RETAINED_MODIFIED |
| SUP-33 | Freeze-1.1 sealing certificate names capture custodian and runner; registration of roles implicit | Freeze 1.1 §8.2 para 2; §4 para 4; §8.5 | A1 roles and gates (roles.json); registration records anchored before each gate; adjudicators and translation registered before entropy | certificate never issued; no mechanism existed | D0 | EV0 | none | SUPERSEDED |
| SUP-34 | Freeze-1.2 rev1 draft: Bing capture runner, 2026-09-19T09:00Z schedule, capture registration | uncommitted Freeze-1.2 rev1 | NON-OPERATIVE; preserved in quarantine/NON_OPERATIVE_BING_CAPTURE_DRAFT | see SUP-02 | D1 | EV0 | none (never run; no Bing request) | SUPERSEDED_NON_OPERATIVE |
| SUP-35 | Freeze-1.2 rev2 draft: GitHub REST search runner, 2026-09-23 schedule, S-LIC/S-ACCESS, custody model | uncommitted Freeze-1.2 rev2 | NON-OPERATIVE; preserved in quarantine/NON_OPERATIVE_FREEZE_1_2_REV2_DRAFT | coverage change toward GitHub-hosted/developer ecosystems; undocumented ranking; top-20 truncation | D2 | EV1 | none (never run; no search request) | SUPERSEDED_NON_OPERATIVE |
| SUP-36 | Programme A estimates one rate over one frozen frame | Freeze 1 §1.1-1.2; §4 | Multi-population programme; A1 first; no automatic pooling; cross-population consistency = replication evidence only | avoid presenting one source's population as the vendor universe | D4 | EV3 | none | NEW_RULE |
| SUP-37 | Pre-execution ineligibility rate reported as headline in the 'many ineligible' regime | Freeze 1 §7.7 | S-prevalence (n-1)/(T-1) and unresolved rates reported beside, never multiplied into, the success estimate | stopping biases naive prevalence; combined metrics overstate | D4 | EV3 | none | RETAINED_MODIFIED |

**Unchanged and operative:** Freeze-1 journey standard, effect requirements, natural customer condition, credentials policy (§2-§3); k = 5 runs per platform; model and run isolation (§5); outcome taxonomy, FALSE_SUCCESS minimum evidence, R02 generalisation, append-only later observation (§6); verifier hardening (§2.3), Wilson and serialisation rules (§7.2), UNKNOWN sub-codes (§7.3), sensitivity analyses a-f except the category-weighted secondary (§7.5); anti-bias controls not listed above (§8); Freeze-1.1 T0, canonical JSON, URI normalisation, UK-customer context, identity definitions of namespace/authority (§8.3 bullets), Freeze-1.1 prior-FIRSTCALL rules (§5, §8.4) as implemented by SUP-32, entropy custody and one-call generation (§8.5 para 2), conservative band derivation and assumptions (§8.6).
