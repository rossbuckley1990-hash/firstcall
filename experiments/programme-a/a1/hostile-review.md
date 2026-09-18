# Freeze 1.2 Population A1 — hostile review (RDG correction)

The key-level / designated-key draft failed this review. Exact enumeration
(supersession SUP-38) showed unequal vendor-platform inclusion. That draft is preserved
in `quarantine/NON_OPERATIVE_A1_KEY_DESIGNATED_DRAFT/`. This review attacks the corrected
design, in which the registrable-domain group (RDG) is the sampling unit.

**Verdict key.**
- **HELD**: the control is structural or tested.
- **RESIDUAL**: the control is partial; the remaining risk is stated.
- **OPEN**: a named gate stays closed.

## A. Attacks on the RDG correction

| # | Attack | Control | Verdict |
| --- | --- | --- | --- |
| 1 | RDG computation | Structural keys are derived from directory names only: NFC, lower-case, trailing dot removed. The host is the text before the first `:`, converted to A-labels with the stdlib IDNA codec. Hosts are checked for LDH form and length ≤ 253. The registrable domain comes from the full pinned PSL. Tests cover conservation, all 15 edge cases, determinism and byte-identical rebuilds. | HELD. RESIDUAL: the stdlib codec implements IDNA2003, not IDNA2008 (Freeze-1.1 §2). The two differ only on rare code points, and such hosts become INVALID_IDN singletons. The runtime is pinned by digest. |
| 2 | PSL ambiguity | Commit `3955e3ec` (the latest first-parent commit ≤ T0, compared in UTC) is vendored, and its SHA256 is checked before every use. The full ICANN and PRIVATE sections are used. The list is never fetched live, and frame verification fails on any other PSL. | HELD. The PRIVATE section splits hosting-platform tenants into separate RDGs. This is declared. |
| 3 | Primary-entry manipulation | Frozen rule: the bare registrable-domain key (byte-smallest if there are several), otherwise the byte-smallest key; the entry is the byte-smallest spec path of that key. Both are fixed in the sealed frame. A record about any other entry becomes `NOT_THE_PRIMARY_ENTRY`, i.e. UNRESOLVED. Covered by tests. | HELD. RESIDUAL: the rule may pick an older or narrower API. Declared, never corrected. |
| 4 | Multi-host OpenAPI definitions | Server URLs never affect grouping or the choice of primary entry (tested: an unrelated server host leaves the frame unchanged). They are E2 leads only. All valid servers become byte-sorted leads. Relative, template, IP, localhost and malformed values are dropped and recorded. | HELD |
| 5 | Cross-domain vendor multiplicity | Declared as a property of the unit: one vendor may contribute several RDGs. Inclusion is n/M_G per RDG. Nothing is merged, weighted or collapsed. | HELD by definition. RESIDUAL: the unit is not a vendor, and every report must say so. |
| 6 | Shared-domain, multi-platform RDGs | Only the primary entry's surface is measured. Other surfaces in the RDG have no inclusion. | HELD by definition. RESIDUAL: declared. |
| 7 | Eligibility substitution | The primary entry is fixed in the frame, and the protocol's `no_substitution` rule applies. The record's primary entry must match the frame. An ineligible or inaccessible primary entry gives EXCLUDED or UNRESOLVED; no switching is allowed. | HELD |
| 8 | Post-randomisation identity changes | There is no identity operation at all: no `resolve_component`, no merge, dedup or replace code (static test). Relationships are descriptive and cannot change `combine` or `screen` (tested). | HELD |
| 9 | Unequal inclusion | The permutation is over sealed G. Exhaustive tests give n/M_G for every RDG in each of counterexamples A–E, and exact pairwise probabilities. A key-level tape cannot be applied to G (length check). | HELD |
| 10 | Post-hoc vendor collapsing | Forbidden in `estimand.json` (no vendor-collapsed or vendor-level estimator; forbidden headlines). The earlier idea of a collapse sensitivity analysis is withdrawn (SUP-41). | HELD by rule. Enforcement lies in reporting. |
| 11 | Denominator manipulation | Every RDG is recorded as RESOLVED_ELIGIBLE, EXCLUDED, UNRESOLVED_ELIGIBILITY or UNSCREENED. The old identity states are rejected (tested). Conservation over G is tested. T and the overshoot are published. | HELD |
| 12 | Outcome leakage | Frame, entropy, permutation and screening all complete before Freeze 4 and any run. Relationships and categories are descriptive only. | HELD |

## B. The 25 earlier attacks, re-checked

| # | Attack | Verdict |
| --- | --- | --- |
| 1 | Source selection | RESIDUAL. The source was chosen from metadata; researcher familiarity is disclosed. |
| 2 | OpenAPI optimism | RESIDUAL. Declared in the estimand and in every report. |
| 3 | Snapshot staleness | RESIDUAL. The automated refresh ended 2024-03-01; declared. |
| 4 | Identity / canonicalisation manipulation | HELD. Identity is no longer a sampling operation (A.8). |
| 5 | Structural exclusions | HELD. Only XS1 and XS2 apply. |
| 6 | Entropy manipulation | RESIDUAL. Unchanged from Freeze 1.1 §8.5: one `os.urandom` call of 32·\|G\| bytes. |
| 7 | Permutation manipulation | HELD. |
| 8 | Screening-order leakage | RESIDUAL. Mitigated by blocks, sealing and diagnostics. |
| 9 | Differential effort | HELD by protocol; human diligence is monitored. |
| 10 | Fatal-exclusion manipulation | HELD for S-membership (20,000-case check, including I0). A single adjudicator can still force UNRESOLVED. |
| 11 | Unresolved shrinkage | RESIDUAL. Reported prominently. |
| 12 | Adjudicator collusion | RESIDUAL. Detectable, not prevented. |
| 13 | Evidence drift | RESIDUAL. The 48 h window and a drift test apply. |
| 14 | Terms gate after selection | HELD. T1–T3 are inside S. |
| 15 | Hidden replacement | HELD. |
| 16 | Candidate insertion | HELD. G is sealed with its hash before entropy. |
| 17 | Denominator manipulation | HELD (A.11). |
| 18 | Prior-FIRSTCALL leakage | HELD. The projector is structural. RESIDUAL: approval of `candidates.json` is still needed. |
| 19 | Verifier false negatives | HELD. Freeze-1 rules unchanged. |
| 20 | False-success misclassification | HELD. Freeze-1 rules unchanged. |
| 21 | Outcome leakage into eligibility | HELD. |
| 22 | Generalisation overclaim | HELD by rule. RDG ≠ vendor; A1 only. |
| 23 | Publication / legal overclaim | HELD. |
| 24 | Sample reconstruction | HELD once artefacts exist: public commit, vendored PSL, published frame, committed tape, sealed records. |
| 25 | Amendment reconstruction | HELD. Three drafts are quarantined; the supersession ledger covers D0–D7 with the withdrawn rows kept. |

## C. Statistical limitation (stated, not corrected)

SRS makes the selection of RDGs exchangeable. It does not make their outcomes
independent. Selected RDGs that share a control plane, vendor or infrastructure can have
correlated run outcomes. The run-noise stage of the Freeze-1.1 band assumes cluster
independence, so coverage can fall short where RDGs share a control plane.

At n = 24 the half-width is 0.392 before widening for indeterminate RDGs.

## D. OPEN

Every gate beyond anchoring and snapshot retrieval is closed. The following roles are
unfilled:
- R03 entropy custodian and R04 witness;
- R05 and R06 adjudicators;
- R07 translation tool;
- R08 browser profile;
- R16 registry approval;
- R17 spec parser (no YAML parser is installed);
- R09 and R10 execution and apparatus roles.
