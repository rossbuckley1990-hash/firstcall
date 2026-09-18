# Freeze 1.1 hostile review — proposal, not frame certification

Reviewed 2026-09-18 against parent commit
`13ff44c37a96882553ffb9103a5596787555e0f3`. This is a self-review, not an
independent scientific review or a claim that future documentary adjudication occurred.
No sources/vendors were researched and no frame/draw was constructed for this review.

| Attack | Prospective control / result | Residual limitation or stop gate |
| --- | --- | --- |
| Pick a source because it contains preferred vendors | Fixed four-query discovery; fixed positions; metadata criteria; all qualifying upstream lists; source lock before rows | Search engine ranking, language, country and index date influence coverage. Reconstruct from archived search pages, not a claim that today's search will replay. Source uncertainty blocks lock. |
| Preview source counts, then choose a different date/export | T0 tied to sealing; latest complete version ≤T0; no content-based screen or date shift | Feasibility is deliberately untested here. Lack of a qualifying archived export stops. |
| Hand-pick a union of known catalogs | Actual sources absent; discovery outputs include all accepted/rejected/unresolved results and criterion evidence | Bounded discovery is not an exhaustive census of catalogs. English/GB discovery and 365-day history favor established sources; report this explicitly. |
| Use several mirrors as independent corroboration | Upstream/owner deduplication; ≥2 independent maintainers | Independence uncertainty stops; source overlap is descriptive, not a population coverage estimator. |
| Prefer famous vendors or highly ranked entries | Complete exports and every row; no rank/star threshold; source-exclusive and overlap counts published | Editorial inclusion and search visibility can retain popularity bias. Outside-union inclusion probabilities are unknown. |
| Discard geographically inconvenient vendors | Worldwide extraction; fixed ordinary UK-customer context; only affirmative documentary restriction supports exclusion | UK accessibility is a narrower target; headquarters is not an access proxy. Language/translation limitations remain missingness. |
| Rename a category or tweak a salt to shift a platform | Stable category IDs and fixed domain-separated hash; display labels irrelevant; identity/membership ledger sealed before scoring | Hash assignment is deterministic, not claimed random. No reroll when category sizes are unattractive. |
| Call one company three platforms to obtain three chances | Documented control-plane boundary; common parent alone neither merges nor splits; alias-row accounting | Any unresolved identity or contradictory equivalence blocks the whole frame. Parent attribution can remain unknown if unit identity is independently established. |
| Choose a canonical URL that produces a preferred category | Fixed URL normalization and byte-minimum documented equivalent anchor; namespace discriminant; blind ledger lock | Novel ambiguous account architectures are a STOP, not permission to choose the desired interpretation. |
| Fail to prove membership in an inconvenient category | Complete seven-predicate vector; explicit FALSE requires documented full scope/negative statement | Strict evidence may create many unresolved units. That is reported attrition, never permission to redefine categories. |
| Search harder for a preferred vendor | Fixed frontier, 16-page/depth-2 cap, retries and seven-day batch; two fixed adjudicators, 60 active minutes each; no extra search | Link topology and finite budget can favor discoverable documentation. Report budgets, gaps and unresolved fractions; never label this outcome-neutral coverage as unbiased. |
| Stop searching as soon as an exclusion is convenient | Complete permitted capture frontier even after an affirmative exclusion; all reasons published | Same maximal evidence access does not guarantee identical cognitive effort; reviewer/time logs expose differences. |
| Turn dead links into no-sandbox exclusions | Missing/inaccessible evidence is UNRESOLVED; affirmative violation needed for EXCLUDED | No all-vendor rate can be claimed; unresolved-state rate is a headline population-construction result. |
| Reviewers disagree, then recruit a favorable third vote | Two independent reviews; disagreement unresolved; no third reviewer or extension | Identity disagreement blocks the build; excessive unresolved eligibility can fail capacity. |
| Revive an unresolved candidate when a reserve is needed | Unresolved units never enter ordering; no post-lock upgrades in this cohort | New evidence requires a later separately preregistered frame. |
| Use historical success/failure to define prior targets | Parent-cutoff designation/authorship registry; projected provenance only; named exclusions retained; no outcome condition | Historical designations constrain support even when never executed. Mixed documents must be safely projected; ambiguous provenance blocks the registry. |
| Pretend the rejected draft never existed | Byte-identical text quarantine, original path/hash, explicit disclosure of named-draft exposure | The process cannot claim ignorance of proposed vendor names. No remembered claims may become frame evidence. |
| Change quotas to rescue sparse categories | Fixed Hamilton apportionment and reserve capacity gate; no source, stratum or N tuning | A failed capacity gate stops the study; no guarantee this protocol will yield 24 vendors. |
| Claim equal inclusion probabilities for unequal strata | Initial probability m_h/M_h; final probability m_h/G_h with complete blinded census; explicit design weights | These are conditional design probabilities under the stated entropy/census model, not universal inclusion chances. |
| Replace selectively until a preferred vendor appears | Full frozen order; census gates applied to every eligible platform before execution, blinded to ordering; log every skip | Whole-frame apparatus/mapping/census work is expensive. Unresolved census status or G_h<m_h stops execution. |
| Call a pseudorandom hash sort mathematically uniform | Future independent uniform 32-byte priority per unit; collision halts, no reroll; randomness tape commitment | Uniformity assumes the registered entropy source supplies independent uniform bytes; no such tape exists here. |
| Hide excluded/unresolved vendors or undefined rates in denominators | Three-state canonical conservation; separate raw-row equation; weighted estimable ratio explicitly labelled; zero denominator null | Informative nonresponse is not cured by weighting. Indeterminate rates, assignment bounds and frame/census attrition remain required. |
| Silently change the SAP while fixing sampling | Crosswalk explicitly amends population support, vendor weights and within-stratum bootstrap | This is a substantive, bounded amendment requiring separate sealing. It is not an interpretation claimed to exist in Freeze 1. |

The review tightened three points before delivery: identity/membership must be sealed
before hashing; review time is bounded as well as network effort; and randomization
uses an explicitly defined later randomness tape rather than leaving an unspecified
seed-stream algorithm to future discretion. None was selected using candidate counts.
It also distinguishes affirmative source ineligibility from source uncertainty, preserves
duplicate native source IDs as separate raw occurrences, and specifies the later entropy
interface and raw-byte commitment. No entropy call was made.

No remaining substantive sampling decision was identified as deferred to Freeze 2.
Future source retrieval/parser implementation, adjudicator registration, runtime-version
capture and apparatus code must implement the frozen rules without changing support,
thresholds or probabilities. Source availability, identity resolvability, documentary
coverage, reviewer feasibility, stratum capacity and census feasibility remain **untested
stop gates**, not completed validations. A newly discovered gap requires stopping and a
new prospective amendment; do not improvise during Freeze 2.

The applicator's checks prove parent byte integrity, guarded overlay composition and
repository boundaries. They cannot prove that public evidence supports a future candidate,
that an entropy provider is unbiased, or that human adjudicators obey the protocol.

Validation commands (offline; no vendor work):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/programme-a/amendments/test_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/programme-a/amendments/apply_protocol.py
git diff --check
```

For a consolidated prospective protocol, the same applicator's `--emit` option writes
canonical JSON to stdout only. It includes parent text, amendment text, original parent
hashes, operations and effective machine documents; it never alters Freeze-1 files.

## Final adversarial review (supersedes the earlier sealability assessment)

Initial decision: **NOT SEALABLE**. The earlier review was too permissive. No edits
were made until the requested files and immutable protocol had been read. Pre-correction
file hashes are retained in the amendment JSON's `final_review` record.

| Substantive counterexample | Minimum operative correction |
| --- | --- |
| Two compliant live searches on the same day produce different source lists | One preregistered, first-attempt authoritative capture; raw-response commitment before screening; reconstruction from that capture, not repeated live searches (§8.2). |
| A reviewer assumes two brands are one unit, pooling links to buy more evidence before identity is settled | Fixed raw-lead identity stage, then separately capped unit eligibility stage; all alias evidence and budgets retained (§8.3). |
| Two URLs for the same administrative platform cause a provisional DISTINCT decision | URI difference is no identity evidence; explicit account-scope/permission-authority pair rule and ambiguity halt (§8.3). |
| A name in a helper filename causes exclusion of an unrelated platform | Path is a lead only; explicit experiment-role grammar, exact identity evidence and complete provenance projection ledger required (§8.4). |
| An operator previews private entropy, discards it and publishes a more attractive tape | Independent witnessed one-call custodian; attempt log; abort on rerun/failure; frame digest bound before interpretation. A hash alone cannot prove honesty (§8.5). |
| Census follows reveal, so a near-boundary eligibility judgment removes an inconvenient selected platform | All-frame gates sealed blind; census completed/sealed at 5A before tape/order disclosure at 5B; no second pass or post-census replacements (§8.5–8.7). |
| Alias evidence after priorities changes a canonical ID, membership or selection probability | Invalidate the cohort, never mutate the ledger or reroll (§8.1). |
| Treating a deterministic public category hash as a fair random category draw | Assignment has only deterministic 0/1 probabilities; no 1/k or balance guarantee. Stable-ID argmin is order/label independent; tie rule explicit (§8.1). |
| Single-seat or equal-observed-rate strata produce a zero-width empirical bootstrap interval | Primary interval replaced by explicit conservative two-stage concentration band; bootstrap retained only as descriptive sensitivity (§8.6). |
| Rate excludes UNKNOWN but is described as unconditional success probability over the original frame | Conditional success parameter and its positivity assumption explicit; support changes and M→G restriction disclosed; indeterminate units never redefine G (§8.6). |
| JSON chronology and duplicated parameters still carry the earlier reveal-first instructions | Update all relevant guarded patches and verify repeated rule objects plus stage order in the applicator (§8.7). |

**Category proof.** For a fixed ID and applicable set, the minimum of (digest, stable
ID) is unique, independent of iteration order, and unchanged by display labels. It
offers no random assignment probability. Under a hypothetical iid-hash model 1/k holds
conditional on distinct scores; stable-ID tie-breaking prevents an unconditional exact
claim. Input validation rejects malformed/duplicate IDs. Public hashing cannot prevent
private clandestine score inspection; the protocol makes that a halt, not a mathematical
impossibility. Alias/membership changes after lock invalidate the cohort.

**Randomization proof.** M is known only after canonical eligibility and stratum assignment
are sealed. Exactly 32M bytes map one-to-one to sorted IDs. Under iid uniform bytes,
every within-stratum permutation has identical probability conditional on no ties. Each
stratum uses disjoint byte blocks; conditioning on independent no-tie events preserves
independence between strata. OS randomness is a stated model with witnessed custody,
not proven honest by its SHA256. A public beacon could strengthen provenance auditing;
it is not required to repair the mathematical design and was not substituted.

**Inclusion proof.** For a fixed initial stratum of M_h units, each occupies m_h of M_h
selected positions: pi_i=m_h/M_h. Every ordering of a fixed census subset has
choose(M_h,G_h)*(M_h-G_h)! extensions, so restriction to its G_h members is uniform and
pi_i=m_h/G_h. Same-stratum joint pi_ij=m_h(m_h-1)/(G_h(G_h-1)); cross-stratum products
follow independence. These are conditional on successful draw gates and the fixed census.
They are not probabilities of surviving source, documentary or census eligibility, and
they do not include aborted cohorts. Final census-ineligible units have pi=0.

**Replacement counterexample and repair.** With one initial seat among three abstract
units, an assessor who sees the top-ranked unit can mark it ineligible and repeat until
a preferred unit is next. Then G depends on the ordering and m/G is false. Sealing all
census statuses before reveal, with no repeat adjudication, removes that permitted path.
A post-seal safety or apparatus issue halts the cohort; it cannot trigger another vendor.

**Uncertainty proof.** For frozen G, W_h=G_h/G and C=sum(W_h²/m_h), let l_i=E[L_i] and
u_i=E[U_i]. Under the declared conditional-mean and positivity model, l_i≤p_i≤u_i.
Sampling fixed bounded l_i without replacement contributes mgf at most exp(t²C/8);
independent bounded cluster noise conditional on selection contributes the same bound.
Multiplying gives exp(t²C/4); Chernoff gives exp(-epsilon²/C) for each one-sided tail.
Taking epsilon=sqrt(C ln40) and a union bound yields at least 95% coverage. The method
uses no unobserved variance or joint-probability estimator. If positivity, cluster
independence or conditional-mean assumptions fail, there is no calibrated coverage claim.
The bound can be wide and does not repair source coverage or informative missingness.

**Modulo audit.** Category scoring and priority sorting perform no modulo reduction.
Hamilton remainders are deterministic apportionment, not randomization. The secondary
bootstrap's bounded-index mapping uses rejection above 2^64-(2^64 mod m_h); accepted
residue counts are equal. Its deterministic SHAKE stream is not called genuine entropy.

**Identity attacks.** Multiple APIs/brands and API versions sharing tenant scope and
permission authority collapse. Shared corporate ownership or SSO alone does not collapse
subsidiaries. Separate regional enrollment scopes or white-label administrative scopes
are distinct only on affirmative evidence. Acquisitions count as identity changes only
on documented effective integration by T0. Unknown historical architecture or conflicting
pair evidence stops the frame. A canonical anchor labels an identity already resolved;
it does not supply evidence of identity. There is no allowed post-hoc alias repair.

**Residual limitations, not hidden implementation choices.** The target is conditional
on the authoritative capture, complete documentary decisions and order-blind census;
two new live searches need not match. Documentary semantics still require the registered
reviewers; disagreement and unrecognized designation grammar fail closed. Outcome-based
judgment, concealed entropy rerolls and collusion are prohibited and auditable, not
cryptographically impossible. Coverage, source availability, documentary sufficiency,
whole-frame census cost and statistical precision have not been empirically verified.

Reassessment after these corrections: **SEALABLE as a prospective protocol**, subject
to its explicit registration, custody, capture, feasibility and model-assumption gates.
This is not a seal, an executed frame, or a claim that future inputs will pass those gates.
No new substantive sampling choice is delegated to seeing vendors or outcomes.
