# Freeze 1.2 Population A1 — hostile review

Verdict key:
- **HELD**: the control is structural or tested.
- **RESIDUAL**: the control is partial, and the remaining risk is stated.
- **OPEN**: unresolved, and a named gate stays closed.

| # | Attack | Control | Verdict |
| --- | --- | --- | --- |
| 1 | Source-selection bias | The source was named from metadata only (licence, criteria, format, history, aggregates). No membership was viewed or compared. The one listing response was reduced to a count without display. Alternatives are recorded in the supersession ledger. | RESIDUAL: the researchers chose the source, and their general prior familiarity with public API directories is disclosed. |
| 2 | OpenAPI-directory optimism | A1 is defined as OpenAPI-directory-listed platforms. Listing plausibly correlates with machine-readable, agent-friendly documentation. Headline wording is restricted, and "all API vendors" claims are forbidden (estimand.json). | RESIDUAL by design; stated in every report. |
| 3 | Snapshot staleness | The commit is pinned, and the vintage is disclosed (automated refresh ended 2024-03-01). Defunct listings become EXCLUDED or UNRESOLVED and are counted; they are never scored as failures. | RESIDUAL: A1 over-represents platforms listed by early 2024. |
| 4 | Identity/canonicalisation manipulation | Structural keys come from mechanical rules only (NFC, lower-case, trailing dot). Components come from the PSL pinned at T0. Identity is adjudicated per whole component, independently by both adjudicators, with agreement required. The designated key is the byte-smallest. Tests show entry-order independence. | HELD for within-domain aliases. RESIDUAL: a platform spread across different registrable domains gets extra entry points; a duplicate discovered among selected units is flagged, and a sensitivity analysis drops the higher key. |
| 5 | Structural-exclusion manipulation | Only two mechanical exclusions exist (XS1 file under `APIs/`, XS2 no spec file). All are published, and conservation is tested. | HELD |
| 6 | Entropy manipulation | A registered independent custodian and witness perform one `os.urandom` call. The commitment is recorded before interpretation. There is no fallback source and no reroll, and a tie aborts. Adjudicators and translation are registered before entropy. | RESIDUAL: honest OS entropy cannot be proved by a hash (Freeze 1.1 §8.5, unchanged). |
| 7 | Permutation manipulation | The mapping is deterministic from the committed tape and byte-sorted K. Tests cover length, commitment, tie and uniform mapping. K is sealed before entropy. | HELD |
| 8 | Screening-order leakage | The custodian releases one block of 6 at a time. Presentation within a block is hash-shuffled with no positions shown. Statuses are sealed before selection is computed mechanically. | RESIDUAL: screeners know an early eligible unit is likely to be selected. Mitigated by independent dual coding, and by drift and per-adjudicator diagnostics. |
| 9 | Differential adjudication effort | Identical page and time budgets, target order and vocabulary for every key. Licensing changes retention only. | HELD by protocol. RESIDUAL: human diligence varies (monitored through diagnostics). |
| 10 | Fatal-exclusion manipulation | A stop requires an affirmative code with evidence. A unilateral stop can never produce ELIGIBLE. Only the same fatal predicate from both adjudicators yields EXCLUDED. Monotonicity holds: contrary evidence produces UNRESOLVED, never the opposite code. The fuzz proof check passes (20,000 cases). | HELD for S-membership. RESIDUAL: one adjudicator can still veto a unit into UNRESOLVED, just as under Freeze 1.1. |
| 11 | Unresolved shrinkage | UNRESOLVED is never selectable and never silently counted as negative. Rates are reported prominently. Freeing category completeness removes one source of shrinkage. | RESIDUAL: S is biased toward well-documented, readable platforms. This is a declared limitation. |
| 12 | Adjudicator collusion | Adjudicators are distinct registered persons. Records are sealed before exchange. The validator detects role conflicts. | RESIDUAL: covert collusion can be detected through disagreement patterns, not prevented. |
| 13 | Evidence drift | Each key is read within 48 hours by both adjudicators. A position-drift trend test is run. Nothing is re-adjudicated after sealing. | RESIDUAL: documentation changes over a campaign of about 5–14 weeks. |
| 14 | Terms-gate post-selection bias | T1–T3 are inside S, before counting. A post-selection gate would break the SRS proof or force replacement, so neither is used. Signup-time surprises produce SELECTED_NOT_EXECUTABLE, which is indeterminate and widens the band. | HELD |
| 15 | Hidden replacement | No replacement function exists (static test). Reserves are removed. There is a single permutation. | HELD |
| 16 | Candidate insertion | K is sealed with its hash before entropy. Retrieval is exactly once. The permutation covers exactly K. | HELD |
| 17 | Denominator manipulation | Every key's terminal status or UNSCREENED is recorded. Conservation over K is tested. T and the overshoot are published. | HELD |
| 18 | Prior-FIRSTCALL leakage | Projector v1.2.1 is structural; hostile tests cover incidental mentions, examples, policy fields, targets, renamed and nested experiments, artifacts, receipts and prose. The dry run shows no unrecognised designations. Approval by both adjudicators is required before entropy. | HELD. RESIDUAL: `candidates.json` must be confirmed by the adjudicators. |
| 19 | Verifier false negatives | Freeze-1 §2.3 and §6 are unchanged: two observation paths, synchronous acceptance counted as positive evidence, and non-observation → UNKNOWN. | HELD (unchanged); apparatus not yet built. |
| 20 | False-success misclassification | The Freeze-1 §6.2 minimum evidence (C-DENY, C-PRED, C-DUP, C-AUDIT) is unchanged. | HELD (unchanged) |
| 21 | Outcome leakage into eligibility | No outcome exists until the sample is sealed. Screening precedes Freeze 4, and runs follow the sample seal. | HELD |
| 22 | Population-generalisation overclaim | The A1-only estimand. Forbidden headlines. No pooling without a separate preregistration. | HELD by rule; enforcement lies in reporting. |
| 23 | Publication/legal overclaim | The protocol makes no legal conclusion. Technical controls are respected. Commercial publication has a separate legal-review gate. | HELD |
| 24 | Inability to reconstruct the sample | The public commit, published frame, tape commitment (tape revealed after the sample seal), sealed block records and deterministic engines are all available. Every step is re-runnable offline. | HELD, once artefacts exist. |
| 25 | Inability to reconstruct every amendment | Git history is preserved. Both withdrawn drafts are quarantined byte-identically with provenance. The supersession ledger records discovery stage, evidence seen and bias per change. | HELD. RESIDUAL: the uncommitted drafts are anchored only when the quarantine is committed. |

## Additional findings

- **Precision:** at n = 24, the conservative band half-width is 0.392 before
  indeterminate-vendor widening. This is a design choice, stated honestly.
- **Workload:** the expected number of keys screened is
  - 80 at 30% S-prevalence;
  - 120 at 20%;
  - 159 at 15%;
  - 237 at 10%.

  Exhaustion occurs if S-prevalence falls below about 3.4% (M < 24).
- **OPEN gates:** every gate beyond anchoring and snapshot retrieval is closed. The
  unfilled roles are the entropy custodian and witness, two adjudicators, the
  translation tool, the browser profile, the registry approval, and the execution and
  apparatus roles.
