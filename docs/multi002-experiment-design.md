# MULTI-002: operational-configuration discoverability across APIs

Design date: 2026-09-18. Repository inspected at `e9be04017b52df81f65689e537f6e49b3a1d119c`.
Status: **DESIGN ONLY; TARGET ELIGIBILITY NOT YET ESTABLISHED; NOT EXECUTABLE.**

Selected target **for documentary eligibility review**: **Stripe Checkout, creating one test-mode Checkout Session for an existing catalog price, without completing checkout**. This is a provisional selection, not a finding that Stripe has a discoverability defect. No non-email target can yet be certified against all the requested criteria from this repository alone. The scientifically strongest next step is the eligibility review below, followed by the six-run experiment only if it passes.

This audit used local files and local Git metadata only. No documentation was fetched, credentials inspected or used, vendor contacted, preflight performed, or autonomous customer launched. Vendor capabilities discussed below are design assumptions requiring primary-source confirmation, not current verified product claims. **Zero MULTI-002 real runs have occurred.** No implementation, P03, commit, tag, or push was created.

## 1. The MULTI-001 finding being replicated

| Frozen record | Historical result | Interpretation |
| --- | --- | --- |
| `multi-001-postmark-valid-baseline` | 0/3 | Required sender identity was not supplied. |
| `multi-001-postmark-p01-apparatus` | 0/3 | `POSTMARK_FROM` existed in the customer environment, but customers did not discover/use it. |
| `multi-001-postmark-p02-evidence`, commit `0da15acc2328775969fab2a7a8a0866a3f8b5fd5` | 2/3 PROVEN_SUCCESS; 1/3 FALSE_SUCCESS; AFCR 66.67% | One sentence identified the existing variable and its semantic role. |
| `postmark-verifier-v2`, commit `e9be04017b52df81f65689e537f6e49b3a1d119c` | Subsequent measurement repair | Not the instrument used for historical P02. |

The P02 sentence was exactly:

> A concrete verified sender identity is available in the environment variable POSTMARK_FROM.

The relevant discoverability contrast is **P01 → P02**, not the original baseline → P02. Original baseline → P01 changed availability. P01 → P02 changed information about availability, location, and semantic role while retaining the value.

**Configuration availability** means the required valid value actually exists in the customer's process environment. **Configuration discoverability** means the customer has enough information to identify its existence, location, and role in the API operation. An environment variable can be readable without its intended use being evident. Conversely, a customer may discover it unaided; that is a valid baseline success.

Sources: [P01 diagnosis](../experiments/multi-001/postmark/diagnoses/p01.json), [P01 apparatus](multi001-postmark-p01.md), [P02 apparatus](multi001-postmark-p02.md), and canonical summaries under `artifacts/multi-001/postmark/baseline/d0bd8c7ade2b`, `p01-counterfactual/ca116baa8519`, and `p02-counterfactual/9906c79fc405`. These records and their verdicts remain untouched.

## 2. Repository audit and threats to validity

### Existing apparatus and candidates

| Repository evidence | What exists | Relevance to MULTI-002 |
| --- | --- | --- |
| `experiments/multi-001/candidates.json`, `protocol.md` | Postmark, Stripe, Clerk listed prospectively; Stripe priority 2, Clerk priority 3 | Evidence of prior candidate selection, not vendor readiness or validated API behavior. |
| `firstcall/multi001_postmark*.py`, `postmark_preflight.py`, `verifiers/postmark.py` | Vendor-specific runners, sandbox preflight, read-only effect verifier, frozen official HTML, hostile fixtures/tests | Evidence architecture and measurement lessons; no Postmark execution or modification authorized. |
| `firstcall/resend001.py`, `live002.py` through `live005.py`, `verifiers/resend.py`, `resend2.py` | Real email integration apparatus, delivery/readback logic, pagination, official machine-doc capture | Useful infrastructure reference; poor independent-category replication. |
| `firstcall/agents/codex_live.py`, `runtime/workspace.py`, `journey_evidence.py`, `benchmark_evidence.py`, `receipt_verify.py`, `experiment_manifest.py` | Explicit experiment environment, temporary workspaces, command events, file manifests, receipts and hashes | Reusable concepts after review. No generic Stripe/Clerk adapter or verifier exists. |
| `firstcall/cf001_service.py`, `verifiers/cf001.py`, `experiments/cf-001` | Local synthetic event API and independent exact-cardinality readback | Offline apparatus fixtures only; cannot establish independent real-vendor replication. |
| `experiments/live-001/acme_service.py`, `verifiers/file_effect.py` | Local counter/file effects | Offline verifier/runner controls only. |
| `firstcall/simulator.py`, `demo.py`, `tests/test_kernel.py` | Synthetic `stripe:t1` task label and synthetic key-pattern fixture | **Not** a Stripe implementation, docs capture, credential, or successful Stripe experiment. |
| `experiments/resend-001/docs.md` | Links mentioning Supabase email integrations | Not Supabase Storage onboarding or a second-category adapter. |

Search scope included tracked source, tests, docs, experiments, and artifact inventories. There are no captured Stripe or Clerk official onboarding bytes, nor fixtures establishing their API response contracts. No additional viable real-vendor adapters were found. The five existing untracked `cf001` helper scripts are outside this change and were preserved byte-for-byte.

### Validity threats carried forward

1. **Availability confounding:** historical baseline lacked a sender. MULTI-002 must supply the same operational value in both arms from the outset.
2. **Apparatus masquerading as onboarding failure:** [the invalidated initial cohort](../experiments/multi-001/postmark/invalidations/d631d6344557.json) received no promised onboarding bytes. Assert and hash actual workspace delivery before every customer starts.
3. **Observation latency and coverage:** [the verifier audit](postmark-verifier-audit.md) found three quick observations without deliberate waits, incomplete list/cardinality coverage, and no stored observation timestamps/responses. P02-R02 has candidate-side acceptance evidence, but that cannot retrospectively prove a vendor effect or establish the cause of the miss. Preserve its FALSE_SUCCESS.
4. **Instrument drift:** verifier-v2 came after P02. Freeze the MULTI-002 verifier, classifier, observation budget, and hostile tests before either arm; never compare arms measured with different instruments.
5. **Small, sequential cohorts and post-observation selection:** three runs per arm provide coarse estimates; time/model changes, selection of a failed product, and reuse of information can exaggerate a contrast. Predeclare the candidate, intervention, exclusions, and randomized run order before outcomes. Retain all negative findings and all starts.
6. **Prior knowledge and leakage:** official-doc use does not prove a model learned from those docs. Fresh workspace alone does not isolate inherited HOME/configuration, memories, network access, or other credentials. Audit those surfaces explicitly. Customers must not see FIRSTCALL diagnosis, other runs, this design, or experiment arm names.
7. **Outcome versus claim:** `grade.py` uses stdout keywords and lacks a native tri-state observation type; callers special-case UNKNOWN. Do not assume it is an adequate MULTI-002 classifier. A completed shell command does not establish an API request. Preserve commands, actual request evidence, independent effects, and claims separately.
8. **Stale matching and incomplete journey evidence:** [RESEND-001's audit](../experiments/resend-001/audit/post-experiment.md) illustrates missing execution artifacts and insufficient temporal identity. Bind fresh nonces, time bounds, account identity, command events, generated files, and vendor evidence.
9. **Bounded uniqueness:** even verifier-v2 can return on the first match, before a later duplicate appears. MULTI-002 must observe through its declared window. No finite window proves permanent absence or uniqueness.
10. **Scope:** two vendors cannot justify “all APIs”; a Stripe result concerns a particular model, workflow, configuration handoff, and test environment. Discoverability may be an integration-handoff issue without any factual defect in vendor documentation.

## 3. Candidate APIs considered and rejection reasons

Evidence tiers: **local** = established from repository files; **proposed** = plausible workflow requiring official-source review; **unknown** = cannot establish offline. All non-email details below are proposed/unknown, including current pricing, permissions, test-mode guarantees, and endpoint response contracts.

### Stripe: create a simple test Product or Customer

- **Task/effect:** one test-mode object carrying a unique marker. This is consistent with the broad local candidate entry, which does not specify a particular object.
- **Onboarding/configuration:** proposed ordinary API introduction plus create/retrieve/list references; test secret credential and caller-provided attributes. Candidate hidden value: none established beyond authentication.
- **Availability/discoverability:** hiding the API-key variable when the task/docs normally identify authentication would manufacture a blocker. An extra price/account parameter is not necessary for this simple task.
- **Verification/grading:** proposed independent list and retrieve, exact marker, account, test mode, time, and count. Objective if the contracts are confirmed.
- **Safety/credentials/cost:** test-only write credential plus separate read-only verifier credential; duplicate test records possible; billing and quota terms unknown until reviewed. No need for actual payment or personal data.
- **Contamination/independence:** familiar API and model prior knowledge; strong category independence from email but no established configuration treatment.
- **Disposition:** **reject this task** for the hypothesis. Ease of implementing a create/read verifier does not supply a natural operational-config gap.

### Stripe: Checkout Session for an existing catalog price

- **Task/effect:** create exactly one test Checkout Session referencing a merchant's already-configured price; stop before payment. Existing-price reuse is a normal integration requirement, but its authenticity for this fixture must be documented before selection.
- **Onboarding/configuration:** proposed official hosted Checkout integration with existing Prices, Session create/retrieve/list and line-item readback, Price retrieval/listing, authentication, testing, and idempotency references. Necessary values include test credential, existing price identifier, quantity, mode, and return URLs.
- **Candidate variable:** `STRIPE_PRICE_ID`, already populated with the intended test price. Credential location and return URLs are explicit in both tasks. Only the price's environment mapping is the proposed discoverability treatment.
- **Natural blocker:** a customer knows the API needs the intended existing price but does not connect that requirement to the value already in its environment. This is a prediction, **not an observed or established blocker**.
- **Disqualifying alternative:** the official flow may already explain an environment mapping, provide a lookup key, or enable the customer to identify the intended price through ordinary catalog reads. If it makes the necessary value unambiguously machine-discoverable, **reject**; do not suppress list endpoints, strip examples, add decoy prices, or obscure variable names.
- **Verification/grading:** independently enumerate Sessions, retrieve the candidate effect and line items, and match the known fixture price; test-mode, count, account, timing, and marker checks. A Session URL or agent claim alone cannot pass.
- **Safety/duplicates:** persistent test Sessions, never a completed payment. One allowed create, no automatic retry, independent duplicate checks. Disable external callbacks and notifications. Test-mode availability and isolation must be confirmed, not inferred solely from a key prefix.
- **Credentials/cost:** equivalent test-scoped customer credentials, separate read-only verifier identity in the same sandbox. No keys in files or argv. Confirm restricted-key capabilities, fees, quotas, and billing isolation; do not assume “free.” Model execution also has a separately bounded cost.
- **Contamination/similarity/independence:** common Checkout recipes and `STRIPE_PRICE_ID` conventions may make baseline success likely. Analogous account-specific configured object; independent payments/catalog semantics with no sender verification, recipient, or email-delivery measurement.
- **Disposition:** **provisional first choice for eligibility review**, supported by the pre-existing cross-category shortlist and an objective proposed effect. No local evidence yet proves the crucial gap.

### Clerk: test identity or organization membership

- **Task/effect:** proposed creation of a development user; alternatively membership in an existing organization.
- **Onboarding/configuration:** ordinary backend SDK/API plus development-instance guidance. User creation needs a credential and permitted user fields; organization membership additionally needs an organization identifier and user identity.
- **Candidate variable/availability:** `CLERK_ORGANIZATION_ID` could exist in an environment, but neither a real handoff nor a need for it is established locally. Simple user creation does not establish this gap; adding organization membership solely to create it would select the task backwards.
- **Verification/grading:** proposed independent user/membership retrieval and list/cardinality checks; objectively gradable if supported.
- **Safety/credentials/cost/effects:** development-only credentials and read-only verifier access; duplicate users/memberships, hooks, emails, and plan/seat charges require containment and current verification. Use no real identity. Development mode must not be assumed to suppress every notification or charge.
- **Contamination/independence:** identity SDK defaults and prior knowledge; functionally distinct from email, but an email-verified signup task would reintroduce the original semantics.
- **Disposition:** **defer organization workflow; reject simple user creation for this hypothesis**. Local evidence is only the candidate entry. It is less well justified than the proposed catalog handoff and has unresolved notification/identity confounds.

### Supabase Storage: upload one inert object to an existing private bucket

- **Task/effect:** proposed tiny text object at a unique path in a private test bucket.
- **Onboarding/configuration:** proposed Storage upload and project/auth/bucket setup docs; project URL, scoped credential, bucket name, object path, and policy permissions.
- **Candidate variable/availability:** an existing deployment might supply `SUPABASE_STORAGE_BUCKET`; no such deployment convention or capture exists here. Official setup may already specify the bucket explicitly or make it listable.
- **Verification/grading:** separate read identity lists the prefix and retrieves object bytes to compare a digest; exact object version/write count needs more than a successful final GET. Same-key overwrites can hide duplicate mutations.
- **Safety/credentials/cost/effects:** private disposable project, no public URL, non-sensitive bytes, restricted write scope; storage/egress/quota charges unknown. Persistent object and possible hooks; a local emulator would be an apparatus test, not remote vendor replication.
- **Contamination/independence:** project credentials or broad service keys can confound permission failure with discoverability; strong storage-category independence from email. Do not remove ordinary bucket-discovery permissions to induce failure.
- **Disposition:** **reserve, not selected**. Lacks local Storage docs/adapter/fixture; remote sandbox, cost, and overwrite/cardinality guarantees are unresolved. Resend's Supabase links are insufficient evidence.

### Resend and local Acme/CF-001 controls

- **Resend task/onboarding/configuration:** send one test email, using locally captured official machine-doc material, key, sender, recipient, subject. Sender-variable discovery could resemble Postmark, but the existing task already supplies a sender. Removing it would be an artificial ablation.
- **Resend verification/safety/cost:** existing independent list/readback with delivery fields; keys, test recipients, duplicate sends, external email effects, quotas, and current costs require controls. Existing apparatus is evidence of implementability, not evidence of independence.
- **Resend contamination/independence:** extensive prior repository experiments and nearly identical email semantics. **Reject as MULTI-002's principal replication**, irrespective of convenience.
- **Acme/CF-001:** local event/counter/file creation with supplied synthetic docs/configuration; independently count/read effects, no vendor credential, no external cost or effect. Duplicate local events can be tested objectively. **Reject as scientific replication** because a planted fixture cannot establish a naturally occurring second-vendor onboarding gap. Retain only as offline apparatus controls.

Any candidate requiring subjective success, self-report-only verification, uncontrolled live effects, exposed credentials, deliberately incomplete docs, or newly granted capability in the intervention is rejected without running customers.

## 4. Selection gate: evidence required before freezing execution

The selection is provisional because the requested zero-network audit cannot fill the missing official-doc evidence. The following future review is a prerequisite, not work performed in this turn:

1. Capture the genuine official existing-price Checkout workflow, including linked material necessary to finish the task. Preserve original bytes, source URLs, redirects, capture time, media type, complete link inventory, and raw/content hashes. Identify official revisions when available. Do not substitute a researcher-authored tutorial.
2. Intended official entry points, **not fetched or validated here**, are `https://docs.stripe.com/payments/checkout`, `https://docs.stripe.com/api/checkout/sessions/create`, `https://docs.stripe.com/api/checkout/sessions/list`, `https://docs.stripe.com/api/prices`, and `https://docs.stripe.com/testing`. Follow genuine official links to retrieval, line items, restricted keys, idempotency, and sandbox guidance; freeze the resulting source manifest before runs.
3. Produce a requirement-to-source table for authentication, existing-price semantics, required request fields, mode, test guarantees, readback, pagination, and errors. Each entry must cite captured file/hash and exact section. No failed customer runs may be used to choose which pages to omit.
4. Independently document the deployment handoff: why an existing catalog price must be reused and why its identifier is supplied as `STRIPE_PRICE_ID`. Prefer an established application configuration convention rather than naming a variable to induce the desired result. No opaque name, dummy variable, irrelevant environment noise, or missing-value baseline. If authentic handoff evidence does not support this exact variable/task, reject this frozen proposal and record a new prospective design before any run.
5. Review every natural discovery route: official environment examples, API list/read operations, lookup keys, product metadata, SDK configuration, linked setup instructions, and deployment config files. An explicit, unambiguous route from task to intended price disqualifies the candidate for this gap; an unaided environment inspection remains permitted. Do not interpret a generic placeholder alone as proof of a defect.
6. Confirm the necessary independent verifier and safety contracts from primary sources. Document all remaining uncertainty and its resolution. Missing evidence means **NOT ELIGIBLE**, not “probably eligible.”

Rejecting Stripe at this gate is a useful scientific result. Move to another prospectively documented candidate without changing this baseline into a harder task. If no candidate passes, report “no supported replication target yet”; do not manufacture a positive experiment. No frozen official onboarding artifact or its hash is claimed to exist today.

## 5. Exact frozen hypothesis and estimand

**Conditional on the eligibility gate passing**, preregister this hypothesis verbatim:

> For fresh autonomous customers performing the specified Stripe test Checkout task with the intended existing price already available as STRIPE_PRICE_ID, adding only the sentence identifying that variable and its semantic role will increase independently verified first-outcome success relative to the complete unmodified official onboarding, by reducing failures at resolution of the existing price identifier.

Primary estimand: the difference in PROVEN_SUCCESS proportions between assignment to the one-sentence treatment and assignment to unmodified official onboarding, for this frozen task, model, environment, and observation policy. Directional prediction: AFCR(intervention) > AFCR(baseline). No promised effect size and no presumption of baseline failure.

Secondary mechanistic outcome: the trace establishes resolution and use of the intended price, followed by an attempted Session create. Distinguish discovering the variable from independently discovering the same identifier through another permitted route. Trace absence is not proof that an agent never read a value; mark unobservable steps unknown.

## 6. Baseline and counterfactual protocol (A–H)

### A. Frozen baseline customer task

Use these exact task bytes if the eligibility review validates the scenario. Substitute only `{RUN_MARKER}` with a fresh opaque marker; give neither arm its arm label.

```text
You are a fresh autonomous developer integrating Stripe Checkout for an existing catalog.

Using the supplied official Stripe onboarding and API documentation, create and
execute the smallest integration that creates exactly one test-mode hosted
Checkout Session for one unit of the existing FIRSTCALL Test Plan catalog price.
Reuse that existing price; do not create or alter products or prices.

Use the test API credential in STRIPE_SECRET_KEY. Use payment mode and these
return URLs: https://example.com/success and https://example.com/cancel.
Set the Session client_reference_id to {RUN_MARKER}.

Do not open or complete checkout, collect payment details, create a subscription,
send a notification, or access live-mode resources. Read-only API exploration and
inspection of your local runtime environment are allowed. Do not print secrets.
Make at most one Session-creation request. Disable automatic SDK write retries.
If a write response is ambiguous, stop; do not retry or create a replacement.
Do not ask for help. Stop when done or blocked.

Report whether you believe the requested Session was created, its identifier if
available, and the reason if blocked. Your report is not the success verifier.
```

The existing-catalog requirement must reflect the authentic use case established at the gate. It must not be added merely to disallow an otherwise sufficient official inline-price recipe. The product name and URLs are fixed task constants, not hidden parameters. If that product name plus normal listing identifies the intended price, the gate rejects the candidate rather than adding misleading products or removing listing rights.

### B. Frozen official onboarding material

Both arms receive the same complete official-source bundle selected by the documentary gate, at the same neutral workspace paths. Original bytes and all dependencies remain intact. Preserve HTML and any official machine-readable version; any navigation index or rendering must be identical across arms and must not summarize away configuration instructions. Missing pages/assets necessary to use the official workflow are apparatus defects.

For reproducibility, use the frozen official corpus as the documentation surface in both arms. Freeze the same offline navigation mechanism and API network policy. If the corpus does not contain an ordinary required linked path, stop before execution and complete it; do not create failure by blocking that path. Freeze API version and preinstalled client/runtime versions so package installation is unnecessary. Neither arm can read experiment records or earlier runs.

**Pending freeze fields:** source bundle, exact document/section chosen for insertion, hashes, official API version, runtime/client versions, and model identity. They cannot honestly be filled in from current local evidence. Execution is prohibited until recorded in a prospective manifest.

### C. Environment/configuration supplied to every customer

| Input | Baseline and intervention |
| --- | --- |
| `STRIPE_SECRET_KEY` | Valid test-only customer credential; same capabilities and sandbox account in every run. Explicitly named in both tasks. |
| `STRIPE_PRICE_ID` | The same nonempty, valid existing one-time test price identifier in both arms; not printed into prompts or examples. Correctness preflighted before all runs. |
| `{RUN_MARKER}` | Unique unpredictable execution/run marker inserted into the task. Independent of arm. |
| Runtime variables | Minimal identical allowlist, with isolated customer home/configuration and no unrelated credentials. |
| Verifier credential | Separate read-only credential, retained only by harness; never in customer environment, workspace, prompt, or logs. |

Record secret-safe credential identity/scope provenance and equality of price/account across arms. The fixture's currency, amount, product identity, active status, type, and price ID are frozen in a harness-only manifest. No new value, privilege, network destination, SDK helper, or account setup is introduced for treatment. Customers may enumerate environment names and read values in either arm. Do not prevent natural discovery.

### D. Exact expected natural blocker

The predicted boundary is **mapping the documented existing-price requirement to the supplied STRIPE_PRICE_ID value before constructing the Session's line item**. Eligible baseline traces might explicitly stop for lack of a known existing price or use a documented placeholder and receive a corresponding rejection. Neither behavior is guaranteed. Authentication, bad fixture, permission denial, missing docs, or invalid mode is a different failure, not evidence for this hypothesis.

### E. Exact minimal discoverability intervention

Add exactly one paragraph at the start of the selected official entry document, preserving every original byte apart from the single insertion:

> The existing catalog price identifier is available in the environment variable STRIPE_PRICE_ID.

This is a clearly recorded experimental annotation, never represented in provenance as vendor-authored text. It supplies no identifier, code, extra capability, permissions, endpoint, or fallback. Same document filename and delivery mechanism in both arms; no separate help prompt. Freeze the exact insertion anchor and verify a one-paragraph byte diff before execution. If genuine official material already supplies this information, reject the candidate.

### F. Required invariants

Task template, fixture and operational values, credential capabilities, account/test mode, documentation bundle/navigation, prompt except the inserted docs paragraph, model/version/reasoning settings, tool set, runtime/client/API versions, timeout (300 seconds), retry policy, independent verifier and classifier, observation schedule, evidence capture/redaction, and safety controls remain identical. Differences allowed only for fresh run identity/workspace, arm assignment, and the single paragraph. Credential rotation, if necessary, must preserve scope and be predeclared identically; no post-failure adjustments.

### G–H. Three fresh baseline and three fresh counterfactual runs

Allocate `B01–B03` and `I01–I03` to three time-adjacent blocks, one baseline and one intervention per block. Independently randomize order within each block before the first customer, and save seed, algorithm, assignments, and hash. This yields exactly three customers per arm with less time-order confounding than running all baselines first. Customer-visible run markers do not encode assignment.

Every invocation has a new workspace and isolated session/configuration, no conversational history, no shared generated files, no feedback, and no rescue. Capture the actual served model identity; an unresolved or changed identity halts comparison. Freeze all hypotheses and treatment bytes before any invocation: do not tune the sentence after baseline results. No discarded pilots, replacement runs, retries after ambiguous writes, or optional stopping for favorable AFCR. Safety/measurement halts override completing six runs; report the incomplete allocation explicitly. Negative baseline outcomes never authorize repairing the apparatus mid-cohort.

## 7. Independent verification, AFCR, and ambiguity (I–M)

### I. Independent verifier contract

Build a new Stripe verifier; do not repurpose or change the frozen Postmark runners. Its proposed read paths are Session list, Session retrieval, Session line-item retrieval, and Price retrieval; confirm exact API contracts at the documentary gate.

1. Before customer launch, independently confirm sandbox/account and fixture, capture server-time relationship, and snapshot existing Sessions. No concurrent actor may write in the dedicated test account. Save run start and customer-execution end times. Isolate each customer's access after termination so background writes cannot continue.
2. Independently list **all** potentially relevant new Sessions, following every page. Count all new Sessions in the isolated account's run interval, including wrong-marker Sessions; do not let missing metadata hide duplicate effects. Independently discover candidates even if the agent provides no ID.
3. Treat a syntactically valid claimed ID only as a retrieval hint. It does not select the only row checked or exclude other effects. Retrieve the independently discovered Session and its complete line items.
4. Require correct account, literal test-mode evidence, fresh creation time within the run boundary (with a frozen precision/clock tolerance), exact `client_reference_id`, intended existing price ID, quantity one, payment mode, configured return URLs, and an uncompleted/unpaid Session. Confirm expected product/currency/amount from the frozen fixture where the official contract permits. No live or completed payment is a valid success.
5. Require exactly one new Session and no forbidden mutations. Use independent sandbox inventory/request-audit evidence plus the enforced operation policy; an untrusted customer log alone cannot prove no extra writes. If supported vendor readback/audit cannot resolve this, the gate fails or the outcome is UNKNOWN.
6. Observe at offsets **0, 5, 15, 30, and 60 seconds after customer termination**, never return success early. Schedule each round at the later of its offset or completion of the prior round. Requests time out after 10 seconds; verification has a hard 120-second deadline and maximum 100 read requests per run. Exhaustion before complete terminal coverage yields UNKNOWN. This chosen policy is not a vendor consistency SLA.
7. Persist each attempt's time, latency, HTTP status, safe request identifier, endpoint/parameters, pagination cursors/counts, sanitized response, response digest, and decision reason. Two complete terminal sweeps at/after 30 and 60 seconds must agree on the single effect; known duplicate IDs across conflicting pages are observation ambiguity, not proof of two unique effects. Two distinct created Sessions are a duplicate failure. Never collapse distinct effects while deduplicating repeated pagination rows.

### J. AFCR calculation

For each arm, `AFCR = PROVEN_SUCCESS / eligible fresh customer runs`, where eligible means a launched valid run with a determinate outcome; UNKNOWN and apparatus-invalid runs are excluded and separately counted. Report exact counts, assigned/started/eligible totals, all outcomes, and percentage. With three eligible runs, possible rates are 0%, 33.33%, 66.67%, 100%. Report `delta = AFCR_I - AFCR_B` in percentage points.

Also report assignment-based bounds `[S/3, (S+U+M)/3]`, where S is proven successes, U is unknown/invalid started allocations and M is unstarted allocations. This prevents exclusions/halts from creating apparent lift. No complete-cohort causal claim unless all six allocations are valid and determinate. AFCR with zero eligible runs is undefined, never zero. Freeze this denominator rule before either arm.

AFCR here means verified first product outcome within one autonomous integration attempt, not “the first HTTP request succeeds”: read-only exploration is allowed, one effect-creating request is permitted.

### K–L. Halt conditions and ambiguity handling

- Halt before launch for missing/invalid operational value, inadequate docs delivery, failed eligibility, unverified sandbox/billing isolation, insufficient verifier access, changed frozen hashes, invalid credentials/scopes, shared-state contamination, or unsafe evidence persistence. These are apparatus failures, not evidence of an onboarding defect.
- Halt the cohort on live-mode evidence, attempted forbidden external effect, secret leakage, duplicate mutation, unknown verification, incomplete pagination, model drift, or inability to stop background work. Preserve every started run and all available evidence. No replacement to restore 3/3.
- `PROVEN_SUCCESS`: independent, complete, bounded-window proof satisfies all predicates, safety and evidence integrity pass, and autonomous execution is established. A contradictory final agent claim does not erase a proven effect; record it separately.
- `FALSE_SUCCESS`: an explicit success claim contradicted by determinate independent evidence. A request accepted but still unobserved after the window is **UNKNOWN**, not automatically FALSE_SUCCESS.
- `EXECUTION_FAILED`: established execution failure with determinate absence/wrong outcome and no safety breach. A process timeout after possible submission requires verification, not automatic failure.
- `EFFECT_FAILED`: determinate wrong effect or absence without a success claim. No-write absence requires trustworthy request/audit coverage; repeated empty listings alone cannot establish absence after an ambiguous accepted write.
- `UNSAFE_SUCCESS`: a verified effect accompanied by a safety violation; never in the numerator. Record safety violations even when no successful effect exists and halt; the safety field must not depend on this enum name.
- `UNKNOWN`: transport exhaustion, malformed relevant evidence, incomplete lists, ambiguous timing/identity, conflicting observations, possible delayed effect, or missing integrity evidence. Keep outcome, claim, execution status, and safety as separate fields so enum precedence cannot hide a material fact.
- Read-only retries follow only the frozen schedule; no write retry or model rescue. Late observations, if separately authorized, are append-only supplemental evidence and cannot rewrite the original window's grade.

### M. Evidence schema and provenance requirements

Proposed schema `firstcall.multi002.receipt.v1` (design only):

| Group | Required fields |
| --- | --- |
| Identity | experiment, run_id, execution_nonce, opaque marker, arm, randomized block/order, start/end UTC and monotonic duration |
| Preregistration | design/eligibility/task/source/intervention manifests and SHA256; original official source URLs, capture times and hashes; exact patch hash |
| Apparatus | source-file hashes, Git commit and dirty-state manifest, runner/verifier/classifier versions, policy and fixture hashes, runtime/client/API versions |
| Customer | requested and observed model/version/settings, invocation hash, isolated workspace/config proof, timeout, tool/network policy hash |
| Configuration | allowed variable names, presence assertions, equality assertions across arms, account/test-mode proof, customer/verifier credential-scope identities; no secret values |
| Journey | safe JSONL and stderr, completed command events, candidate_execution_observed, operation-level request evidence, final structured claim, generated-file manifest/copies and hashes |
| Mechanism | first supported blocking boundary, evidence references, price-discovery route, correct-price-used state, actual create-attempt state; unknown allowed |
| Verification | immutable schedule, all attempt records, full pagination coverage, safe vendor response projections, claimed/discovered IDs, complete matching/new-effect sets, final observation coverage and bounded predicates |
| Result | outcome, explicit reason code, claim/effect agreement, eligibility, unsafe flags, halt reason, exclusion reason |
| Integrity | redactions/omissions, safe observed/persisted byte sizes and digests, evidence-file hashes, canonical receipt proof hash |

Use a versioned canonical JSON algorithm for manifest/receipt/cohort hashes. Cohort summary binds the ordered run proofs, full allocation including unstarted runs, outcomes, denominators, bounds, AFCR/delta, and limitations. Keep original histories immutable; prospective records belong under new `experiments/multi-002/` and nonce-specific `artifacts/multi-002/` paths only when implementation is separately authorized.

Credentials never enter argv, repository files, prompts, or retained unredacted traces. Prefer opaque secret-manager identity or keyed fingerprint for credentials and low-entropy configuration rather than exposing reversible values or guessable plain hashes. Keep the fingerprint key out of evidence. Response projections must preserve all grading fields while removing credentials, session URLs/tokens, and unnecessary account identifiers. Scan in memory before persistence; if safe sanitization cannot retain verifiability, halt. Hashing is tamper evidence, not proof that the data are true; independent authenticated vendor reads establish the observation source.

## 8. Safety and sandbox preflight (N)

**All steps here are future requirements. None ran during this design turn.**

1. Verify current official test/sandbox behavior, terms, pricing, quotas, and restricted permissions. Use a dedicated disposable sandbox with no real customers, payment methods, subscriptions, live credentials, outbound webhooks, connected applications, notification automations, or unrelated writers. Do not infer isolation from environment names alone.
2. Provision the fixture outside measured runs: existing product and one-time price representing the authentic application catalog. Both arms receive identical configuration. Record fixture provenance, scopes, mode, amount/currency, and immutable identity without leaking credentials. Do not create decoys or deliberately remove discovery permissions.
3. Independently read back the fixture using the verifier credential and establish that customer credential scope supports the intended operation and ordinary discovery paths. Do not execute the customer solution during preflight or add help based on a rehearsal. If a capability can only be tested by a write, it requires a separately authorized, recorded apparatus canary, never an unreported MULTI-002 customer pilot.
4. Validate in offline fixtures that sandbox/account guards fail closed; freeze a method/path egress policy permitting official read exploration and only the requested Session creation. The policy must not suppress ordinary reads to manufacture the blocker. Block completion, payments, subscriptions, catalog mutation, notification endpoints, arbitrary destinations, and checkout URL navigation. Allow no more than one create submission per run and disable SDK automatic retries; a second attempt halts and is recorded even if blocked.
5. Ensure customer and verifier credentials are distinct, scoped and isolated, with equivalently scoped customer credentials across arms. Check launch environment presence without exposing values. No credentials or actual configuration were inspected in this audit.
6. Bound effects to at most six intended test Sessions, one per allocation, plus separately recorded fixture resources. No financial charge, email, external callback, or actual purchase is part of the task. Confirm vendor costs before authorization; stop if zero-billing containment cannot be established. Freeze model budget separately.
7. Keep created objects for the verification window and evidence capture. Any later cleanup is separately authorized and logged after grading; no automatic deletion obscures evidence. Do not open Session URLs. Domain return URLs are request parameters, not destinations to visit.

## 9. Incorporating verifier-v2 lessons before execution (O)

Freeze meaningful offline tests for: delayed visibility at every observation; empty then visible; accepted write never visible; transport failure then recovery; permanent timeout; malformed payloads; incomplete/looping/reordered pagination; repeated row versus distinct duplicate; duplicate appearing after first success; missing/wrong marker; correct marker with wrong price or account; absent/false test-mode flag; stale effect and timestamp precision; fabricated claimed ID; claim-free genuine effect; wrong amount/quantity/mode; terminal disagreement; zero-budget configuration; secret-safe error paths; and read-only verifier behavior.

Exercise the entire runner with mocked customer and vendor transports: exact environment equality, actual docs delivery and hashes, one-paragraph delta, isolation from parent credentials/history, no FIRSTCALL execution of customer code, no write retry/rescue, ordinal/randomization preservation, UNKNOWN halts, and no secret persistence. Offline tests must reject outbound network/process execution except explicitly allowed local fixtures.

Unlike historical P02, retain each observation's provenance and do not treat an early empty response as absence. Unlike the remaining first-match limitation in Postmark v2, continue through terminal cardinality observations. Freeze the measurement protocol before both arms; prospective verifier changes invalidate comparability and require a separately recorded future experiment. No retrospective regrading of MULTI-001.

## 10. Success, falsification, and information gain (P–Q)

**Supports the narrow generalization:** the candidate passes documentary eligibility; all six runs are valid and determinate; intervention AFCR exceeds baseline; and trace evidence supports the predicted price-resolution transition. For example, 0/3 → 2/3 is a +66.67 percentage-point directional replication across email and payments, not proof of a universal law. A 0/3 → 3/3 contrast is stronger evidence but still tiny: with six independent runs, an unblocked two-sided Fisher exact test gives p=0.10 for that extreme table. The planned three-block randomization has only eight possible within-block assignments; even three favorable discordant blocks give one-sided randomization p=1/8. Do not claim conventional statistical significance or adequate power. Report exact counts and an exact test appropriate to the actual allocation, without changing tests after seeing outcomes.

**Weakens or fails to support the specified hypothesis:**

- Baseline 3/3: no observed need for the treatment in this setting. Preserve it; do not make the task harder.
- Equal AFCR or lower intervention AFCR: no positive first-outcome effect in this experiment. With n=3, this does not establish a universal null.
- Both arms resolve the price but fail elsewhere: predicted bottleneck not supported; no discoverability-lift claim.
- Treatment improves price resolution but not verified outcome: mechanistic progress only, not support for the primary AFCR hypothesis.
- AFCR increases without evidence of the predicted resolution change: association with the annotation, mechanism unestablished.
- Complete official onboarding already makes the value discoverable: candidate falsified at eligibility, no customer experiment warranted for this gap.
- Missing values, changed permissions, damaged docs, leakage, inconsistent verification, or unknown outcomes: invalid/inconclusive experiment, not a negative vendor result and not positive support.

Expected information gain is separating a cross-category operational-handoff effect from email-specific sender-verification behavior. A successful baseline or failed eligibility review is informative: the hypothesis does not apply to every first-call API workflow. No outcome here changes Postmark's historical 2/3.

## 11. Implementation plan and present completion boundary

Future work, **not implemented or authorized for execution by this document**:

1. Complete the documentary and authentic-handoff eligibility review without autonomous customer pilots. Record acceptance or rejection and primary-source evidence. If rejected, stop this target and preregister another candidate rather than modify its task to force failure.
2. If eligible, freeze missing source bytes, insertion anchor, concrete fixture provenance, versions/model, response contracts, safety budget, and randomization manifest. These are mandatory unresolved inputs, not assumed facts.
3. Implement isolated MULTI-002 runner, Stripe verifier, safe preflight, tri-state outcome handling, and evidence schema in new files; reuse audited generic evidence helpers where appropriate. Do not alter the frozen Postmark apparatus/history or existing untracked helpers.
4. Complete offline hostile verifier/runner tests and security checks; inspect exact baseline/intervention delta. Review sandbox and ordinary discovery permissions before authorization for external actions.
5. Only under later explicit execution authorization, provision/preflight safely and run the fixed six assignments with no rescue. Record every started run and halt exactly as specified. Report all results, including failed eligibility or null findings.

This turn creates only `docs/multi002-experiment-design.md`. No runnable MULTI-002 adapter, verifier, fixtures, captured external docs, experiment manifest, or execution artifacts were created. **Zero MULTI-002 real runs have occurred. Network requests during this audit: zero.**
