# Programme A — Freeze 1.2: Population A1 consolidated amendment (prospective; RDG correction)

**Status: PROPOSED.** The amendment binds only once it is committed, tagged `programme-a-freeze-1.2-a1` and pushed
to `origin` by the protocol custodian. Design date: 2026-09-19.

**Parents:**
- Freeze 1: `13ff44c37a96882553ffb9103a5596787555e0f3` (`programme-a-freeze-1-protocol`)
- Freeze 1.1: `4eaa6493924256dbeb888ff992a769a6b9c6d56d` (`programme-a-freeze-1.1-protocol`)

This amendment supersedes **only** the rows of `experiments/programme-a/a1/supersession.json`
(§16). Every other Freeze-1 and Freeze-1.1 provision remains operative. If this text and the
machine-readable files disagree, the amendment may not be used.

## 1. Contamination boundary

| Item | Status |
| --- | --- |
| A1 membership retrieved | NO |
| A1 candidate identities observed | 0 |
| A1 frame constructed | NO |
| A1 entropy / permutation | NONE / NONE |
| A1 RDGs selected | 0 |
| A1 eligibility decisions | 0 |
| A1 vendor API calls | 0 |
| A1 autonomous runs | 0 |
| A1 outcomes | 0 |

**Pre-design observations, stated openly.**
- One GitHub contents-API listing of `APIs-guru/openapi-directory/APIs` was retrieved. The
  script reduced it to a count (701) before printing. No name was displayed, recorded or
  used.
- One commits-API response was reduced to commit dates.
- The metrics endpoint returned aggregates only.
- README criteria and licence were read through a summariser instructed to omit names.
- Other sources read: Wikidata aggregates; GitHub and Zenodo terms pages; UK statute text;
  `git ls-remote` (one SHA).
- The **Public Suffix List** was obtained from its own project on 2026-09-19. It contains no
  A1 membership.
- The counterexamples of §7.3 were computed only on synthetic keys.

## 2. History (not cleaned up)

1. The Freeze-2 attempt halted because registrations were missing.
2. Freeze-1.2 revision 1 (Bing capture) was withdrawn over terms uncertainty. No Bing
   request was ever made.
3. Freeze-1.2 revision 2 (GitHub search) was withdrawn because of coverage and ranking
   problems. No search request was ever made.
4. The metadata feasibility study proposed APIs.guru as the narrow population A1.
5. Hostile statistical review produced the sequential S0 design.
6. The documentary-access review replaced scraping with independent human reading.
7. **A key-level / designated-key A1 draft was found not sealable.** Its randomisation unit
   (structural keys) differed from its estimand unit (vendor platforms). Exact enumeration
   refuted equal platform inclusion (§7.3). The draft was replaced by the
   registrable-domain-group (RDG) unit before any A1 membership, entropy, permutation,
   adjudication or outcome existed.

All three withdrawn drafts are preserved read-only, with hashes, in
`experiments/programme-a/quarantine/`.

## 3. Population A1 and its unit

**The A1 primary sampling unit is the registrable-domain group (RDG).** The frame G is
the set of RDGs represented in the pinned APIs.guru OpenAPI Directory snapshot, computed
structurally with the pinned Public Suffix List and sealed before entropy.

- **An RDG is a structural sampling unit, not a vendor.**
- **One vendor or control plane may contribute several RDGs.**
- **One RDG may contain several products or platform surfaces.**
- **Only the mechanically chosen primary entry of an RDG is measured.**
- **A1 does not estimate a universal vendor, API or SaaS success rate.**

Programme A's measurement standard stays source-agnostic. A1 is the first registered
population in a multi-population programme (§14).

## 4. Source, snapshot and PSL (frozen before membership retrieval)

| Item | Frozen value |
| --- | --- |
| Repository | `https://github.com/APIs-guru/openapi-directory.git`. Independent community project; repository licence CC0-1.0; definitions acquired from public sources are held under fair use. Stated inclusion criteria: public, long-lived, useful beyond its owner. |
| Snapshot | Commit `f04b8d0bcd39c52e1cf3ad7a5fe744709832ae49`. At retrieval it must exist and have a committer date ≤ T0 (2026-09-17T00:00:00Z), otherwise HALT. No substitute is permitted. Vintage: the automated refresh ended 2024-03-01. |
| PSL | `publicsuffix/list` commit `3955e3ec29b94c3cca7bd4509c5f14a7c0959e26` (2026-09-08T12:18:25Z; the first first-parent commit ≤ T0, compared in timezone-aware UTC). `public_suffix_list.dat` SHA256 `a26f7d7e334778ed69216cedb5451ef82031feba6615c12039783cdd94e1fcae`, 334,040 bytes. Full ICANN and PRIVATE sections. Vendored at `experiments/programme-a/a1/psl/` with its MPL-2.0 licence. It is read only from that file after its hash is verified. It is **never fetched live**, and frame construction halts on any mismatch. |
| Retrieval | Exactly once, by the snapshot custodian after anchoring (`a1_frame.py --retrieve`). The output directory is exclusive. |
| Retained / published | Custody: a git bundle. Published: commit and tree SHAs, PSL commit and hash, `frame.json`, `raw-entries.json`, `retrieval.json`. Definition bodies are not republished. |
| Raw entry | Each `openapi.{json,yaml}` / `swagger.{json,yaml}` under `APIs/<provider>/…`. `source_record_id` = `["FIRSTCALL-A1", commit, null, path]`. |
| Structural exclusions | XS1: a file directly under `APIs/`. XS2: a provider directory with no spec file. |

## 5. RDG definition (purely structural, deterministic)

1. **Structural key** = the provider directory name, NFC-normalised, lower-cased, with
   trailing dots removed. Nothing else is merged.
2. **Host** = the key's text before its first `:`. A `:service` suffix or `:port` is
   ignored. Trailing dots are removed. Each label is converted to a lower-case A-label
   (stdlib IDNA codec of the registered runtime).
3. **Singletons.** A key whose host is any of the following forms its own RDG, with id
   `singleton:<key>` and its basis recorded:
   - an IPv4 or IPv6 literal (including bracketed forms);
   - a single label (e.g. `localhost`);
   - a host with an empty label;
   - a host that fails IDNA conversion;
   - a host with a non-LDH label;
   - a host longer than 253 characters;
   - a host that is itself a public suffix.
4. **Registrable domain** = the eTLD+1 under the pinned PSL (exceptions, wildcards, the
   implicit `*` rule). The **RDG id** is the registrable domain (as A-labels) or the
   singleton id.
5. **Primary key.** For a singleton, the key itself. Otherwise the key with no `:` suffix
   whose host equals the RDG id (the bare registrable domain), byte-smallest if there are
   several. Otherwise the byte-smallest key in the RDG.
6. **Primary entry** = the byte-smallest spec path (UTF-8 bytes) of the primary key.
7. **Server URLs inside definitions are never used for grouping or for choosing the
   primary entry.** The number of keys, hosts, services, versions or files in an RDG has
   no effect on its inclusion.
8. **Frame G** = the byte-sorted RDG ids. Each RDG carries its keys, hosts, basis, primary
   key, primary-key rule, primary entry and raw-entry count. G is sealed with `G_sha256`
   **before entropy**.
9. **Conservation and verification.** Every raw entry maps to exactly one key, and every
   key to exactly one RDG. Each RDG has exactly one primary entry, and it obeys rule 6.
   The frame must name the pinned snapshot and PSL and be reproduced byte-identically
   from them. Any other snapshot or PSL fails validation.

**Edge cases handled and tested:**
- several keys sharing one RDG;
- a bare-domain key present, and absent;
- `:service` suffixes;
- ports;
- case and trailing dots;
- internationalised domain names (U-label and A-label spellings merge);
- IPv4 and IPv6 hosts;
- `localhost` and other non-DNS hosts;
- a host that is itself a public suffix;
- PRIVATE-section hosting tenants (separate RDGs);
- non-LDH labels;
- server hosts in a definition that are unrelated to the key;
- multiple surfaces within one RDG.

Malformed, relative, templated or multi-host server URLs affect only the E2 leads (§9).

## 6. Order of operations

| Step | Action | Gate |
| --- | --- | --- |
| 0 | Anchor this amendment | G0 |
| 1 | Retrieve the snapshot once | G1 |
| 2 | Extract raw entries | — |
| 3 | Structural keys | — |
| 4 | Hosts and registrable domains (pinned PSL) | — |
| 5 | Primary key and primary entry for every RDG | — |
| 6 | **Seal the RDG frame G** | — |
| 7 | Prior-FIRSTCALL registry approved | G2 |
| 8 | Adjudicators, translation tool, browser profile and spec parser registered | — |
| 9 | One `os.urandom(32·\|G\|)` call by the entropy custodian and witness; commitment recorded | G3 |
| 10 | **One uniform permutation of G; sealed** | — |
| 11 | Blocks of 6 RDGs released one at a time; dual independent screening of each RDG's primary entry | G4 |
| 12 | Mechanically select the first 24 members of S_G, stopping at the end of that block | — |
| 13 | Handle exhaustion (see below) | — |
| 14 | Seal the sample; reveal the tape | — |
| 15 | Freeze-4 apparatus for the selected RDGs | — |
| 16 | Execution | G5 |

**Exhaustion.** If the permutation runs out with M_G < 24, select all RDGs in S_G. If
M_G < 16, report A1 as underpowered.

**There are no replacements, merges, de-duplications or substitutions at any step.**

## 7. Sampling theorem and the counterexamples that forced the correction

### 7.1 Theorem

*Let G be finite with |G| = N. Let S_G ⊆ G be fixed, with |S_G| = M_G ≥ n. Let π be a
uniformly random ordering of G, independent of S_G. Then the first n members of S_G in π
form a simple random sample without replacement from S_G. Each g ∈ S_G has
Pr(g selected) = n/M_G, and each pair g ≠ h has Pr(both selected) = n(n−1)/(M_G(M_G−1)).
If M_G < n, all of S_G is selected.*

*Proof.* Map π to π|S_G, the order π induces on S_G. Every ordering σ of S_G has exactly
N!/M_G! preimages: choose the positions S_G occupies (C(N, M_G) ways), place S_G in the
order σ, and arrange G∖S_G ((N−M_G)! ways). Since C(N, M_G)·(N−M_G)! = N!/M_G!,
π|S_G is uniform. The first n elements of a uniform ordering form a uniform ordered
n-tuple, and hence a uniform n-subset. ∎

### 7.2 Conditions

- The permutation is over the **same units the estimand averages over**: RDGs.
- **S_G is fixed.** Every status depends only on the RDG's own primary entry, its frozen
  evidence and the frozen procedure. It never depends on the RDG's position, the quota,
  the time or other units.
- No identity decision exists that could vary with the order of screening.
- The fatal-stop rule is monotone (§8), and the terms gate sits inside S_G (§11).
- Stopping at a block boundary and exhaustion do not change the selected set.

### 7.3 Counterexamples to the withdrawn key-level design

These are exact enumerations. In the withdrawn design, keys were randomised and a
designated key was chosen within each registrable-domain component. Each counterexample
is a regression test.

| Case | Setup | Withdrawn design | Required |
| --- | --- | --- | --- |
| A(i) | Vendor B has 5 keys on one registrable domain | equal (1/3; 2/3 for n = 2) | n/3 |
| A(ii) | B's 5 keys lie on 5 registrable domains | n=1: P(B) = 5/7, P(A) = 1/7. n=2: P(B) = 20/21, P(A) = 2/7, P(B twice) = 10/21 | n/3 |
| B | Two keys on one domain, one platform | equal | n/3 |
| C | One platform on 2 domains | n=1: P(X) = 1/2, P(A) = 1/4. n=2: P(X) = 5/6, P(A) = 1/2; P(X twice) = 1/6 | n/3 |
| D | Two platforms share a domain | equal only if the identity decision is correct. A wrong merge gives P(D2) = 0; UNRESOLVED gives 0 for both | n/4 |
| E | Aliases on 3 domains | n=1: P(Y) = 3/4, P(Z) = 1/4. n=2: P(Y) = 1, P(Z) = 1/2; P(Y twice) = 1/2 | n/2 |

**Under the RDG design** every RDG in each case has inclusion probability exactly
n/|G| (tested). The unequal *vendor*-level multiplicity in A(ii), C and E is now part of
the unit's definition, not a sampling error.

**Why complete vendor identity was rejected.** Establishing vendor identity for the whole
frame before randomisation would need about 470–1,400 person-hours for within-group
identity. On top of that there are 245,350 cross-group pairs, and completeness still
could not be guaranteed.

## 8. Fatal-exclusion early stop

**Fatal predicates:**
- INCLUSION_FALSE:I0–I4;
- E1–E4 and E6;
- T1–T3.

An adjudicator who affirms a fatal predicate seals the record and stops. If both
adjudicators affirm the same fatal predicate, the RDG is EXCLUDED. Any other combination
follows the normal rules. A stop by only one adjudicator can never produce
RESOLVED_ELIGIBLE, and this is recorded.

*Monotonicity proof.* Once an affirmative code exists, further reading can only keep it
or turn it into UNRESOLVED (on contradiction). Either way the RDG fails S_G. So stopping
never changes membership of S_G. This is checked with 20,000 randomised cases, I0
included.

## 9. Documentary eligibility — of the primary entry only

**Adjudicators.** Two distinct registered human adjudicators. No codes may be generated
by a model. Both receive identical inputs:
- the E1 primary-entry definition;
- the E2 leads from `a1_evidence.e2_leads(primary entry)`;
- the frozen protocol.

The leads are drawn from these fields:
- `x-origin` URL;
- `externalDocs` URL;
- `termsOfService`;
- `contact.url`;
- `servers` (variables filled only from their own defaults);
- the Swagger 2.0 host.

Only absolute http(s) URLs with a DNS host are kept. Relative, unresolved-template,
IP-literal, `localhost` and malformed values are dropped and recorded.

**Independent reading.** Each adjudicator reads independently, logged out, with no
search, no guessed URLs, no login, no vendor API calls, no scraping and no archive
creation. Budgets:
- eligibility and categories: 16 pages / 60 minutes;
- terms: 6 pages / 20 minutes;
- one retry.

Browser profile: pinned. Evidence records are minimal. No page copies or screenshots are
kept by default. Technical and explicit access restrictions are respected. Any commercial
publication goes through a separate legal-review gate.

**Predicates** (all apply to the surface of the primary entry):
- **I0:** the platform/journey surface documented by the primary entry is identifiable;
- **I1–I4:** unchanged from Freeze 1.1;
- **E1–E4, E6:** unchanged from Freeze 1.1;
- **T1–T3:** the terms predicates (§11);
- **C01–C07:** descriptive only, but scope requires at least one agreed TRUE.

**No substitution.** Adjudicators may not examine, adopt or switch to another entry, key,
product or service in the same RDG — not even when the primary entry is difficult,
inaccessible or ineligible. The normal EXCLUDED/UNRESOLVED rules apply instead. A record
about any other entry is a protocol deviation (UNRESOLVED).

**Relationships.** A relationship to another RDG may be recorded only when the ordinary
frozen evidence establishes it. It is descriptive only.

## 10. UNRESOLVED (fail-closed)

A predicate is UNRESOLVED when any of the following applies:
- evidence is insufficient within the budget;
- the required evidence is behind a login;
- authoritative documentation conflicts;
- the page is inaccessible after the frozen retry;
- the translation is uncertain;
- the adjudicators disagree;
- there is a protocol deviation or a record about a non-primary entry;
- the terms are ambiguous, or require login or acceptance to read.

UNRESOLVED is never treated as negative and never as eligible. The unresolved rate is
reported prominently, because this shrinkage favours well-documented surfaces.

## 11. Execution-stage terms gate — inside S_G

- **T1:** automated agents are prohibited.
- **T2:** benchmarking or testing of the required kind is prohibited.
- **T3:** publication of the derived result is prohibited.

An affirmed T predicate means EXCLUDED. Terms that are login-gated or ambiguous mean
UNRESOLVED. If the adjudicators read the terms and find no prohibition, the result is
reported neutrally as NO_EXPLICIT_RESTRICTION_OBSERVED.

The gate is applied *before* an RDG counts toward the 24. Applying it after selection
would force a replacement or produce a data-dependent subset. A fact that only surfaces
at signup, after selection, makes the RDG SELECTED_NOT_EXECUTABLE: it is indeterminate,
never replaced, and widens the band.

## 12. Screening campaign

- Blocks of 6 RDGs, released only after the previous block is sealed.
- Presentation within a block is hash-shuffled and shows no positions.
- Both readings must happen within 48 h of release.
- At most 3 blocks are released per week.
- Expected screening effort is n(|G|+1)/(M_G+1) RDGs. With |G| = 701, that is 80, 120,
  159 or 237 RDGs at 30%, 20%, 15% or 10% prevalence respectively (about 5–14 weeks).
- The planning bound is 26 weeks. Exceeding it is recorded as a deviation. It never
  truncates the sample.
- Drift diagnostics (a trend test and per-adjudicator rates) never alter the sample.

## 13. Estimand, estimator, uncertainty

**P_A1 is the equal-weight mean, over resolved-eligible registrable-domain groups
represented in the frozen APIs.guru snapshot, of the probability that a fresh autonomous
run PROVEN_SUCCEEDs on the platform/journey surface mechanically represented by that
group's primary entry, given a valid determinate run.** The frozen Freeze-1 natural
customer condition, journey, verifier and outcome taxonomy apply.

**Sample size.** n = 24 and k = 5, for 120 target runs.

**Estimator.**
- For each selected RDG g: r_g = PROVEN_SUCCESS runs / valid determinate runs.
- UNKNOWN and invalid runs are excluded from the denominator. They are never converted
  into failures.
- P̂_A1 = (1/n) Σ r_g over selected RDGs with at least one determinate run. RDGs with
  none are reported and bounded.

**Uncertainty.** The Freeze-1.1 bounded band with one stratum gives
e = √(ln 40 / 24) ≈ **0.392** before widening for indeterminate RDGs. **A1 does not
provide narrow population precision.**

**Correlation limitation.** SRS makes the selection exchangeable, not the outcomes
independent. RDGs that share a control plane or infrastructure may have correlated
outcomes. The band's run-noise stage assumes cluster independence and can therefore
under-cover. This is reported, with no adjustment.

**Cross-domain relationships.** If two selected RDGs share a vendor or control plane,
**both are kept** as distinct units. That is a property of the structural population.
The relationship may be reported descriptively only. It never alters inclusion,
weighting, the denominator, the estimate, replacement or eligibility. **No
vendor-collapsed or vendor-level estimator exists or is permitted.**

**Reported separately:**
- the UNKNOWN rate by sub-code;
- FALSE_SUCCESS;
- indeterminate and not-executable counts;
- the unresolved rate;
- exclusions by predicate;
- T, (n−1)/(T−1) and the overshoot;
- the category mix;
- key, host and file counts per selected RDG;
- descriptive relationships;
- |G| and singleton counts;
- snapshot age;
- OpenAPI-directory bias;
- diagnostics.

Prevalence is never combined with the success rate. RDGs are never described as vendors.

**Verification** follows Freeze 1 §2.3 and §6, unchanged: returned IDs are hints only;
independent observation; bounded schedule; pagination; nonce plus time boundary; stale
exclusion; exactly one effect; idempotency; ambiguity → UNKNOWN; acceptance plus
inconclusive non-observation → UNKNOWN; FALSE_SUCCESS only on an explicit claim with
complete, determinate contradiction.

## 14. Multi-population architecture

Future populations (A2, A3, …) may use other independently defined enumerations under the
same standard. Each must be registered prospectively. There is no automatic pooling: a
pooled estimand needs its own preregistered superpopulation. Consistency across
populations counts as replication evidence. It never licenses claims of universal
representativeness.

## 15. Roles, gates, prior-FIRSTCALL

Roles are listed in `roles.json`. A missing mandatory role keeps its gate **CLOSED**.

**Designated, binding on anchoring:**
- R01 protocol custodian — Ross Buckley;
- R02 snapshot custodian — Ross Buckley.

**Frozen:**
- R11 decision protocol;
- R12–R15 software;
- R18 pinned PSL.

**Unfilled:**
- R03 entropy custodian;
- R04 entropy witness;
- R05 and R06 adjudicators;
- R07 translation tool;
- R08 browser profile;
- R16 registry approval;
- R17 spec parser (no YAML parser is installed in the registered runtime).

**Future:** R09 execution scheduler; R10 apparatus reviewer.

Adjudicators, the translation tool and the spec parser must be registered before entropy
or screening, as the gates require.

**Prior-FIRSTCALL.** The structural projector v1.2.1 is carried forward unchanged, and
its hostile tests pass. The dry run found no unrecognised designations. Gate G2 stays
closed until both adjudicators approve the ledger, including
`experiments/multi-001/candidates.json`.

## 16. Supersession table

Machine-readable version: `experiments/programme-a/a1/supersession.json`. Withdrawn
rows are kept, with status `WITHDRAWN_PRE_SEAL` and a `superseded_by` pointer.

Discovery stages: **D0** 2026-09-18 ~20:00Z: Freeze-2 implementation attempt halted before any source request (missing registrations); **D1** 2026-09-18: external review of uncommitted Freeze-1.2 rev1 (Bing HTML terms uncertainty); **D2** 2026-09-18: reviewer rejection of uncommitted Freeze-1.2 rev2 (GitHub-only search discovery); **D3** 2026-09-18/19: source-metadata feasibility study; **D4** 2026-09-19: hostile statistical design review; **D5** 2026-09-19: documentary access-model review; **D6** 2026-09-19: consolidation (this amendment); **D7** 2026-09-19: hostile review of the sampling unit (key-level randomisation vs vendor-platform estimand), before any A1 membership retrieval.

Evidence classes: **EV0** protocol text and repository structure only; no source or vendor observation; **EV1** terms, robots.txt and API-documentation pages (GitHub, Zenodo); zero discovery requests; **EV2** APIs.guru repository metadata, commit dates, aggregate metrics, README criteria; one listing reduced to a count (701) without display; Wikidata aggregate counts; **EV3** offline calculations only; **EV4** UK statute text (CDPA ss.29A, 30); **EV5** prior-FIRSTCALL projector dry-run summaries at 13ff44c (statuses, paths, key names only; no outcome values); **EV6** git ls-remote of APIs.guru (ref names and one SHA); **EV7** exact finite enumeration of counterexamples A-E on synthetic keys (scratch computation using the then-current screening engine); no A1 membership; **EV8** Public Suffix List project repository: first-parent commit dates and public_suffix_list.dat at the pinned commit; contains no A1 membership.

| ID | Old rule | Source clause | New rule | Why changed | When | Evidence before change | Bias risk | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SUP-01 | Choose one public reproducible enumeration; alternates recorded but unused | Freeze 1 §4.1(1); sample-frame.config frozen_snapshot | A1 is defined by one named, pinned source: APIs.guru openapi-directory commit f04b8d0 (a1-population.json) | Freeze 1.1 had already replaced it with search discovery; that mechanism failed (SUP-02) | D3 | EV2, EV6 | source chosen by the researchers from metadata; OpenAPI-listing bias declared in the estimand | SUPERSEDED |
| SUP-02 | Discovery by public Bing web-search HTML: four queries, logged-out GB/English, top 20 organic | Freeze 1.1 §3 para 1; §8.2; rules.source_universe.engine/queries/capture | No discovery step. A1 membership is the pinned snapshot's structural entries | terms uncertainty over automated retrieval, parsing and archival of Bing HTML | D1 | EV0 | none introduced; removes search-ranking dependence | SUPERSEDED |
| SUP-03 | Use all qualifying enumerations; union; >=2 independently controlled maintainers | Freeze 1.1 §3 para 4 | Single-source population A1; other sources become separately registered populations A2, A3, ... (never pooled automatically) | no second licensed machine-readable enumeration with a compatible population definition was found from metadata; a heterogeneous union would not define a population | D3 | EV2 | single-source coverage; addressed by explicit A1-only claim and the multi-population architecture | SUPERSEDED |
| SUP-04 | Source screening of discovered results: four metadata pages, 20 min per source, SOURCE_ELIGIBLE/INELIGIBLE/UNRESOLVED, source lock | Freeze 1.1 §3 paras 2-3; §8.2 para 3 | Removed; the source is fixed by this amendment and its metadata recorded in a1-population.json | no discovery results exist to screen | D3 | EV2 | source suitability judged once, at design, by the researchers | SUPERSEDED |
| SUP-05 | Latest complete immutable version <= T0 of each qualifying source | Freeze 1.1 §3 para 5 | Pinned commit f04b8d0; at retrieval it must exist and have committer date <= T0 = 2026-09-17T00:00:00Z, else HALT; T0 unchanged | pinning removes any retrieval-time choice; T0 kept | D6 | EV2, EV6 | none; listing vintage (automated refresh stopped 2024-03-01) is a declared staleness limitation | RETAINED_MODIFIED |
| SUP-06 | Per-source parser locked from documented schema; source_record_id [source, version, native id, row address]; preserve every row | Freeze 1.1 §3 para 6 | Raw entry = spec file path under APIs/<provider>/ at the pinned commit; source_record_id [FIRSTCALL-A1, commit, null, path]; a1_frame.py frozen by digest | source is now a repository tree, not a tabular export | D6 | EV2 | structural definition could over- or under-count providers with unusual layouts; conservation checks and published ledger | RETAINED_MODIFIED |
| SUP-07 | Sampling unit = control plane; all pairwise identity relations recorded; any UNRESOLVED relation or missing anchor blocks the entire Freeze 2 | Freeze 1.1 §2 paras 1-4; §8.3 paras 2-4 | Randomisation unit = structural key; identity components by registrable domain computed mechanically; per-component identity adjudication only when a member is screened; designated key = byte-smallest key of each platform; UNRESOLVED_IDENTITY is a unit-level terminal state | all-pairs identity over the whole frame requires full-population adjudication before sampling, which the sequential design removes; the designated-key indicator is order-independent (proof §7) | D4 | EV3 | cross-registrable-domain duplicates of one platform get extra entry points (declared residual; flagged and sensitivity-tested if two selected units prove identical) | WITHDRAWN_PRE_SEAL → SUP-38 |
| SUP-08 | Identity capture per distinct lead group (16 pages, 60 min) before unit resolution | Freeze 1.1 §8.3 para 1 | Identity capture per component, only for components reached in the permutation; 16 pages / 60 min per adjudicator; input is the whole component | workload; keeps identity input independent of which member is reached first | D4 | EV3 | none beyond SUP-07 | WITHDRAWN_PRE_SEAL → SUP-38 |
| SUP-09 | Partition into >=6 categories; stratified selection | Freeze 1 §4.1(2); sample-frame.config categories_min, stratified | S0 unstratified primary sampling; C01-C07 descriptive only | stratum sizes of the eligible population are unknown without full screening; stratified sequential designs need estimated weights, invalidate the bounded band and let the rarest stratum drive workload | D4 | EV3 | category mix of the sample is random (reported), no category balance guarantee | SUPERSEDED |
| SUP-10 | Complete membership vector required; any UNRESOLVED membership => UNRESOLVED_ELIGIBILITY; hash assignment fixes the stratum | Freeze 1.1 §2 paras 6-7; §8.1 | Scope requires >=1 category agreed TRUE; all seven agreed FALSE => SCOPE_OUTSIDE; an incomplete vector is reported INCOMPLETE and does not block eligibility; the Freeze-1.1 hash assignment is computed only descriptively, after the sample is sealed | membership completeness only mattered for stratum assignment, which no longer controls inclusion; avoids unnecessary UNRESOLVED shrinkage | D6 | EV0 | reduces, not increases, documentation-quality shrinkage | RETAINED_MODIFIED |
| SUP-11 | Hamilton proportional allocation of N=24 across seven strata; Freeze 2 fails if any stratum lacks capacity | Freeze 1.1 §6 para 1 | Removed | no strata in the primary design | D4 | EV3 | none | SUPERSEDED |
| SUP-12 | Salted vendor-name hash ordering (Freeze 1); per-stratum permutation from a 32*M tape generated after the eligible frame is sealed (Freeze 1.1) | Freeze 1 §4.1(5); sample-frame.config ordering; Freeze 1.1 §6 paras 2-3; §8.5 paras 3-4 | ONE uniform permutation of sealed K from a 32*\|K\| os.urandom tape generated after K is sealed and BEFORE any eligibility adjudication; tie aborts; commitment before interpretation | eligibility is no longer known before ordering | D4 | EV3 | order becomes visible to screening (see SUP-15 mitigations) | WITHDRAWN_PRE_SEAL → SUP-38 |
| SUP-13 | INELIGIBLE_PRE_EXECUTION => replaced by next vendor in the same category's frozen ordering; Freeze-5A census of all eligible units; final pi = m_h/G_h | Freeze 1 §4.2; §6 table; §7.3; sample-frame.config replacements; Freeze 1.1 §6 paras 5-6; §8.5 paras 5-6 | No replacement of any kind. Documentary and terms gates are part of S and are applied BEFORE a unit is counted; post-selection non-executability => SELECTED_NOT_EXECUTABLE, indeterminate, never replaced | replacement after selection is outcome-adjacent discretion; gating inside S keeps the SRS proof exact | D4 | EV3 | post-selection failures widen the band rather than being hidden | SUPERSEDED |
| SUP-14 | Reserves >= 6; reserve budget 25% | Freeze 1 §4.4; sample-frame.config reserves_min, reserve_budget_fraction | Removed; the permutation remainder is the only candidate source | no reserve concept under sequential selection | D4 | EV3 | none | SUPERSEDED |
| SUP-15 | Draw hashed and blind; selection status and order withheld until Freeze 5B; census personnel blind to ordering | Freeze 1 §4.5; §9.2; Freeze 1.1 §8.5 para 4; §8.7 | Order held in custody by R03; one block of 6 released at a time in hash-shuffled presentation order without positions; statuses sealed before selection is computed mechanically | sequential screening necessarily exposes the current block | D4 | EV3 | screeners can guess that eligible units in early blocks are likely selected; mitigated by blocks, sealing, dual independent coding, drift and per-adjudicator diagnostics; residual declared | SUPERSEDED |
| SUP-16 | Single seven-calendar-day documentary capture window for the whole batch; missing it blocks the batch | Freeze 1.1 §4 para 2; §8.3 para 1 | Per-block 48-hour windows; at most 3 blocks/week; 26-week planning bound (exceeding it is a recorded deviation, never a truncation) | human reading of ~100-250 keys cannot fit seven days | D5 | EV3 | documentary drift over a longer campaign; position-drift diagnostic | SUPERSEDED |
| SUP-17 | Automated byte-ordered BFS frontier, 2 MiB/page, 30 s requests, one retry on timeout/429/5xx, automated archive | Freeze 1.1 §4 para 3 | Human logged-out browser reading from E2 leads via visible first-party links with the frozen vocabulary; 16 pages, depth 2, 60 min; frozen target order; one retry after >= 30 min | automated retrieval and archival of arbitrary vendor sites has no established access basis | D5 | EV4 | human navigation varies; disagreement becomes UNRESOLVED (shrinkage declared) | SUPERSEDED |
| SUP-18 | Two adjudicators receive identical captured packets | Freeze 1.1 §4 para 4 | Identical inputs (E1 material, E2 leads, protocol); independent reading and evidence records | no automated packet exists; a single collector would be an unregistered third adjudicator | D5 | EV0 | more UNRESOLVED from navigation differences (declared) | SUPERSEDED |
| SUP-19 | Collect the whole permitted frontier even after an exclusion is found | Freeze 1.1 §4 para 3 | Fatal-exclusion early stop: an adjudicator who affirms a fatal predicate seals and stops; both affirming the same fatal predicate => EXCLUDED | workload; proof §8 shows S-membership cannot change | D5 | EV3 | fewer co-occurring exclusion reasons recorded (reason reporting is per affirmed predicate) | SUPERSEDED |
| SUP-20 | Captured evidence with source URL/hash/excerpt, archived pages and error metadata | Freeze 1.1 §4 paras 1, 3 | Minimal evidence record (URL, UTC time, title, tier, proposition, predicate, code, reason, minimal excerpt, adjudicator, record SHA256, optional existing archive pointer); no page copies or screenshots by default | raw archival is not needed for decisions and its permission is not established | D5 | EV4 | observations are auditable but not re-observable; declared | SUPERSEDED |
| SUP-21 | Terminal states ELIGIBLE/EXCLUDED/UNRESOLVED_ELIGIBILITY over the canonical union; conservation TOTAL = E + X + U | Freeze 1.1 §4 paras 5-6; rules.eligibility.conservation | Terminal states over K: RESOLVED_ELIGIBLE, EXCLUDED, UNRESOLVED_ELIGIBILITY, UNRESOLVED_IDENTITY, STRUCTURAL_DUPLICATE, plus UNSCREENED; \|K\| = sum of all; SELECTED_NOT_EXECUTABLE recorded post-selection | sequential design leaves most of K unscreened by construction | D4 | EV3 | none; every key accounted | WITHDRAWN_PRE_SEAL → SUP-42 |
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
| SUP-38 | Randomisation unit = structural key; estimand unit = canonical vendor platform; equal platform inclusion claimed via designated-key identity within registrable-domain components (uncommitted A1 draft SUP-07/SUP-08/SUP-12) | Freeze 1.1 §2; §8.3; §6 (as modified by withdrawn A1 draft rows SUP-07, SUP-08, SUP-12) | Primary sampling unit = registrable-domain group (RDG), computed structurally from the pinned snapshot and pinned PSL and sealed as frame G before entropy; ONE uniform permutation of G; estimand is the equal-weight mean over resolved-eligible RDGs measured through each RDG's mechanically chosen primary entry; 'vendor platform' removed as sampling/estimand unit | Exact enumeration refuted equal vendor-platform inclusion under the key-level design: (A) B with 5 keys on 5 registrable domains: n=1 P(B)=5/7, P(A)=P(C)=1/7 vs required 1/3; n=2 P(B)=20/21, P(A)=2/7 vs 2/3, P(B twice)=10/21; (C) platform on 2 domains: n=1 1/2 vs 1/3, n=2 5/6 vs 2/3, twice 1/6; (D) shared-domain distinct platforms equal only if identity adjudication is correct (wrong merge: P(D2)=0; unresolved: both 0); (E) aliases on 3 domains: n=1 P(Y)=3/4, P(Z)=1/4 vs 1/2. Complete pre-randomisation vendor identity would need ~470-1,400 person-hours plus 245,350 cross-group pairs and still could not be guaranteed complete | D7 | EV7 | one vendor may contribute several RDGs and an RDG may bundle several surfaces; both are declared properties of the structural unit, not corrected by weighting | SUPERSEDED |
| SUP-39 | Public Suffix List taken at retrieval time as the latest first-parent commit <= T0 | withdrawn A1 draft (a1-population.json retrieval.psl; a1_frame.py psl_commit_at_t0) | PSL pinned and vendored before any membership retrieval: publicsuffix/list commit 3955e3ec29b94c3cca7bd4509c5f14a7c0959e26 (2026-09-08T12:18:25Z, latest first-parent commit <= T0 by timezone-aware UTC comparison), public_suffix_list.dat sha256 a26f7d7e334778ed69216cedb5451ef82031feba6615c12039783cdd94e1fcae, full ICANN+PRIVATE list; read only from the vendored file; frame construction halts on hash mismatch | a live PSL fetch at retrieval time would be a mutable input chosen after membership becomes visible | D7 | EV8 | none; PSL private-section suffixes (hosting platforms) make tenant subdomains separate RDGs (declared) | NEW_RULE |
| SUP-40 | Eligibility adjudicated for a designated key using the component's evidence | withdrawn A1 draft decision-protocol.json identity/eligibility stages | Primary key = bare registrable-domain key (byte-smallest if several) else byte-smallest key; primary entry = byte-smallest spec path of the primary key; E1/E2 from the primary entry only; new predicate I0 (surface identifiable); records about any other entry are protocol deviations; no substitution of an easier entry | within-RDG choice of what to measure must be mechanical to prevent outcome-informed selection | D7 | EV7 | the primary entry may be an older, narrower or less typical API of its RDG; ineligibility then excludes the RDG (declared) | NEW_RULE |
| SUP-41 | Identity resolution as a sampling operation; cross-domain duplicates flagged with a proposed collapse-to-vendor sensitivity analysis | withdrawn A1 draft (a1_screening.resolve_component; SUP-07 bias note; hostile review #4) | No identity resolution, merging, de-duplication or replacement after the permutation. Two selected RDGs later shown to share a vendor/control plane are both kept; relationships may be reported descriptively only and never affect inclusion, weighting, denominator, estimate, replacement or eligibility; no vendor-collapsed estimator | complete vendor identity cannot be constructed prospectively; any post-hoc collapse would be a data-dependent redefinition of the population | D7 | EV7 | shared control planes may correlate outcomes across RDGs; reported as a limitation of the uncertainty statement | NEW_RULE |
| SUP-42 | Terminal states RESOLVED_ELIGIBLE, EXCLUDED, UNRESOLVED_ELIGIBILITY, UNRESOLVED_IDENTITY, STRUCTURAL_DUPLICATE, UNSCREENED over K (withdrawn SUP-21) | withdrawn A1 draft SUP-21; Freeze 1.1 §4 paras 5-6 | Terminal states over G: RESOLVED_ELIGIBLE, EXCLUDED, UNRESOLVED_ELIGIBILITY, UNSCREENED; SELECTED_NOT_EXECUTABLE post-selection; conservation \|G\| = sum | identity states no longer exist as sampling states | D7 | EV7 | none | RETAINED_MODIFIED |

**Unchanged and operative:** Freeze-1 journey standard, effect requirements, natural customer condition, credentials policy (§2-§3); k = 5 runs per platform; model and run isolation (§5); outcome taxonomy, FALSE_SUCCESS minimum evidence, R02 generalisation, append-only later observation (§6); verifier hardening (§2.3), Wilson and serialisation rules (§7.2), UNKNOWN sub-codes (§7.3), sensitivity analyses a-f except the category-weighted secondary (§7.5); anti-bias controls not listed above (§8); Freeze-1.1 T0, canonical JSON, URI normalisation, UK-customer context, identity definitions of namespace/authority (§8.3 bullets), Freeze-1.1 prior-FIRSTCALL rules (§5, §8.4) as implemented by SUP-32, entropy custody and one-call generation (§8.5 para 2), conservative band derivation and assumptions (§8.6).
