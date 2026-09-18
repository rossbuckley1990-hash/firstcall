# FIRSTCALL MULTI-001
## Natural Autonomous-Customer Failure Discovery

### Research question

Can FIRSTCALL discover naturally occurring machine-facing onboarding
failures in unrelated real software products, localise the first blocking
interface defect from independent evidence, prescribe one minimal repair,
and demonstrate causal AFCR improvement with fresh autonomous customers?

### Hypothesis

For at least one real product, fresh autonomous customers using the
product's ordinary developer-facing onboarding will fail to produce a
verified first product outcome.

FIRSTCALL will be able to:

1. observe the failure;
2. distinguish agent claim from external effect;
3. localise the earliest blocking machine-interface defect;
4. freeze that diagnosis before intervention;
5. make exactly one minimal repair;
6. replay entirely fresh customers;
7. measure whether AFCR changes.

### Products

Initial discovery cohort:

- Postmark
- Stripe
- Clerk

Products are intentionally from different functional categories where
possible.

No product is selected because we already know it fails.

### Discovery stage

Run products independently.

For each product:

- 3 fresh autonomous customers
- new temporary workspace per customer
- no conversational history
- no FIRSTCALL rescue
- ordinary official developer material only
- credentials scoped to test/sandbox/development environment
- unique experiment nonce
- unique run identity
- exact task frozen before first run
- apparatus frozen before first run
- independent vendor-side verification
- captured Codex exec journey evidence
- generated workspace evidence
- secret-safe persistence

### Success definition

Agent prose NEVER establishes success.

A run is PROVEN_SUCCESS only when FIRSTCALL independently verifies the
requested product-side effect.

Outcome enum:

- PROVEN_SUCCESS
- FALSE_SUCCESS
- EXECUTION_FAILED
- EFFECT_FAILED
- UNSAFE_SUCCESS
- UNKNOWN

### Discovery rule

A product becomes a repair candidate only if at least one fresh customer
does not achieve PROVEN_SUCCESS.

Do not modify onboarding during the discovery cohort.

### Localisation rule

After the complete 3-run discovery cohort, FIRSTCALL must identify the
earliest common blocking point supported by captured evidence.

The diagnosis must name an observable interface boundary, for example:

- undiscoverable base URL
- authentication ambiguity
- credential scope ambiguity
- missing required header
- undocumented object prerequisite
- confusing endpoint selection
- SDK/API mismatch
- environment ambiguity
- verification ambiguity
- machine-unreadable setup dependency

Do not diagnose model psychology.

Do not use statements such as:

"The model did not understand."

Prefer evidence-grounded statements such as:

"All failed customers reached authentication but selected an unsupported
authentication scheme because the supplied onboarding surface did not
specify the required header contract."

### Diagnosis freeze

Before intervention, persist:

- diagnosis
- evidence references
- failing stage
- proposed minimal repair
- predicted stage transition
- diagnosis SHA256
- apparatus commit

The diagnosis MUST be committed before the repair is tested.

### Intervention

Exactly ONE machine-facing change is permitted in P01.

Examples:

- one sentence
- one code example
- one explicit URL
- one authentication instruction
- one schema annotation
- one environment instruction

Do not rewrite the entire documentation.

### Counterfactual cohort

After P01:

- 3 entirely fresh autonomous customers
- same model configuration
- same product task
- same credential scope
- same verifier
- same outcome classifier
- same apparatus except the frozen intervention
- new workspaces
- new run identities

### Primary metric

AFCR =
PROVEN_SUCCESS /
eligible fresh autonomous-customer runs

UNKNOWN is excluded from AFCR denominator.

### Causal signal

Compare:

baseline AFCR

versus

P01 AFCR

Also record stage transition.

A useful result is NOT restricted to 0/3 -> 3/3.

Examples:

0/3 -> 3/3
1/3 -> 3/3
0/3 -> 2/3

must all be reported exactly as observed.

### Negative result

If all three products achieve 3/3 PROVEN_SUCCESS:

MULTI-001 has not discovered a natural onboarding defect.

Do NOT invent one.

Expand the product cohort prospectively.

### Stop conditions

Stop a run/product if:

- production/live side effects would occur
- billing could occur
- credential scope cannot be safely isolated
- independent verification is unavailable
- evidence cannot be safely persisted
- vendor terms prohibit the experiment

### Claim discipline

MULTI-001 may support:

"FIRSTCALL discovered and localised a naturally occurring autonomous
customer failure in product X, and a frozen minimal intervention was
associated with measured AFCR change in fresh counterfactual customers."

MULTI-001 alone does NOT support:

"FIRSTCALL works for all APIs."

"FIRSTCALL proves autonomous-agent observability is a new software
category."

"FIRSTCALL automatically repairs arbitrary software."

Those require broader replication.
