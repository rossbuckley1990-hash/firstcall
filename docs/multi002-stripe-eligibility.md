# MULTI-002 Stripe documentary eligibility gate — decision

**Decision: `NOT_ELIGIBLE`.**

Assessment date: 2026-09-18. Repository inspected at `e9be04017b52df81f65689e537f6e49b3a1d119c`.
Design under test: `docs/multi002-experiment-design.md`
(SHA256 `3c3e867d15ae7c74ee7f70cee5c0e769697012afcc54ce6f80bf64cc23179f99`).
Captured source corpus: 43 files under `experiments/multi-002/stripe/sources/web-extracts/`
(source manifest hash `6c13f1f315d32ad4aceb5864d9db83e288a1333508fb4d4f7bbb9ca4d7749791`
**after credential-example sanitization** — see "Sanitization provenance" below;
pre-sanitization manifest hash was `883e17a2a0e3d681c4601bbff4ff7aecd8f8ab80297e40ebbce5f9648d042443`;
per-file hashes in `experiments/multi-002/stripe/eligibility.json`).

This gate reuses the documentary evidence Codex already captured. **No broad crawl was
repeated and no supplemental docs.stripe.com page was fetched** — the captured corpus was
sufficient to decide. **Zero Stripe API requests, zero Checkout Sessions, zero MULTI-002
real runs.** No credentials or configuration values were inspected.

## The question this gate must answer

Given the frozen customer task (design §6A), current official Stripe documentation, ordinary
permitted local-runtime inspection, ordinary permitted read-only discovery, and a valid price
present in `STRIPE_PRICE_ID`: is `STRIPE_PRICE_ID` an **authentic operational-configuration
handoff whose existence/location is genuinely not machine-discoverable**? Or would withholding
knowledge of it **manufacture** the baseline failure?

The pre-registered gate (design §3 "Disqualifying alternative", §4 items 4–5) rejects the
candidate if either (a) the official flow / task / natural discovery already makes the intended
Price reasonably machine-discoverable, or (b) `STRIPE_PRICE_ID` as the hidden handoff is
researcher-created rather than vendor-supported. **Both conditions hold.** A generic
environment-variable pattern we invented is explicitly declared insufficient.

## Ground 1 — `STRIPE_PRICE_ID` is not a vendor-supported handoff

Stripe's onboarding treats environment variables as the store for **API keys only**. The
quickstart (S06, `docs.stripe.com/checkout/quickstart.md`) has a section titled *"Set your
environment variables"* whose entire content is:

> Add your publishable and secret keys to a `.env` file. Next.js automatically loads them into
> your application as environment variables. If you want to listen to webhooks, also include a
> webhook secret…

No captured official source defines, recommends, or uses `STRIPE_PRICE_ID` — or any
price-identifier environment variable — as an operational/deployment handoff.

Instead, the Price identifier appears in **every** official Checkout code sample as an **inline
template placeholder** `{{PRICE_ID}}`, annotated:

> // Provide the exact Price ID (for example, price_1234) of the product you want to sell

This annotation and placeholder recur six times across the JS/Ruby/Python/PHP/.NET/Go samples
in S06 and again in the curl samples of S10 (`accept-a-payment`, `line_items[0][price]={{PRICE_ID}}`).
Stripe's convention is a literal value the developer **looks up and pastes inline**, not a
handed-off environment variable.

Where Stripe *does* address the "which price at deploy time" problem, its documented, stable,
vendor-supported mechanism is the Price **`lookup_key`**, not an env var. S28
(`products-prices/manage-prices`) frames it exactly as the deployment-handoff case:

> …the process is often manual and requires you to deploy new code. To better manage these
> scenarios, you can use the `lookup_key` attribute on the Price object.

`lookup_key` is a queryable Price field (S20 `lookup_keys` list param; S33 price object; S35
prices/search). So the authentic vendor handoff for "reference this specific price stably" is a
lookup_key that is itself machine-resolvable — the opposite of an opaque hidden env var.

**Conclusion:** `STRIPE_PRICE_ID` as the hidden operational handoff is researcher-created. This
alone is disqualifying under design §4 item 4 ("If authentic handoff evidence does not support
this exact variable/task, reject") and the task's rule that a generic invented env-var pattern
is not sufficient.

## Ground 2 — the intended Price is unambiguously machine-discoverable

The frozen customer task (design §6A) **names the product**: *"one unit of the existing FIRSTCALL
Test Plan catalog price"*, supplies the valid test secret key in `STRIPE_SECRET_KEY` (named in
the task), and **explicitly permits** "Read-only API exploration and inspection of your local
runtime environment." Within that permitted, unmodified official surface, the named Price is
reachable by documented routes:

| Route | Captured docs | Mechanism |
| --- | --- | --- |
| A. Product name → price | S34 `products/search`, S20 `prices/list` | `POST /v1/products/search q="name:'FIRSTCALL Test Plan'"` → product id → `GET /v1/prices?product=prod_…`. S20 documents the `product` param: *"Only return prices for the given product."* |
| B. Search prices | S35 `prices/search` | Constrain by product/metadata → Price id. |
| C. Enumerate | S20 `prices/list` | A disposable test account holds few prices; the active intended price is directly enumerable. |
| D. Stable key | S20 `lookup_keys`, S28, S33 | If the fixture Price carries a `lookup_key`, `GET /v1/prices?lookup_keys[]=…` returns it — Stripe's documented deployment-stable reference. |
| E. Agent-native / live | S43 `skills` | Stripe Agent skills + Agent plugins **automatically configure the Stripe MCP server** (live account data), plus `stripe agent setup` and terminal `stripe docs`. A fresh agent has first-class routes to enumerate the account's real Prices. |

S43 (`docs.stripe.com/skills`) is explicit:

> Install the Stripe CLI with `npm install -g @stripe/cli` and run `stripe agent setup`. … Agent
> plugins for Stripe automatically configure the Stripe MCP server, install our skills, and make
> sure they're up-to-date.

The "Start here: Integrate with Stripe using skills and plugins" banner is also stamped on the
Product/Price API reference pages themselves (S34, S35), so an agent reading the official
onboarding is pointed at these agent-native discovery tools directly.

Because the task hands the agent the product **name** and permits read-only discovery, routes
A–E form an **explicit, unambiguous path from task to intended Price**. Design §3 ("If it makes
the necessary value unambiguously machine-discoverable, **reject**; do not suppress list
endpoints, strip examples, add decoy prices, or obscure variable names") and §4 item 5 ("An
explicit, unambiguous route from task to intended price disqualifies the candidate for this gap")
both require rejection.

## Why this is a "manufactured baseline", not a discoverability defect

To make the baseline fail, the experiment would have to rely on the agent **not** using the
documented, permitted catalog read/search/MCP routes that lead straight to the task-named Price.
That is precisely the confound this gate exists to reject: a baseline failure produced by
withholding an env-var mapping that Stripe never defined, in a workflow where the vendor supplies
multiple first-class, machine-native ways to resolve the exact price by its product name. Any
resulting 0/3 would measure "the agent didn't bother to enumerate the catalog," not a genuine
machine-discoverability defect in Stripe's operational configuration.

### Contrast with the MULTI-001 Postmark finding (why that one was legitimate)

Postmark's `POSTMARK_FROM` is a **verified sender identity** — an account-onboarding artifact
whose *operational role* (which verified sender the API requires) is not a routinely enumerable
first-class object the task can name and the agent can list/search its way to. Stripe's Price is
the opposite: a first-class, enumerable, searchable catalog object, named in the task, with a
documented stable key (`lookup_key`) and agent-native live discovery (MCP). The P01→P02 sender
gap does not transfer to a Stripe catalog Price.

## Evidence integrity

- 43 captured sources; each file's SHA256 and byte length are recorded in
  `experiments/multi-002/stripe/eligibility.json` under `captured_source_manifest`.
- Source manifest hash: `6c13f1f315d32ad4aceb5864d9db83e288a1333508fb4d4f7bbb9ca4d7749791`
  (sha256 over compact-canonical JSON of the sorted `[{id,file,url,bytes,sha256}]` manifest,
  computed over the sanitized repository files).
- Design SHA256: `3c3e867d15ae7c74ee7f70cee5c0e769697012afcc54ce6f80bf64cc23179f99`.
- Corpus coverage spans the intended official entry points (Checkout, Sessions
  create/list/retrieve/line_items/object, Prices list/retrieve/search/object, Products
  list/retrieve/search/object, authentication, keys, restricted keys, testing, sandboxes,
  pagination, idempotency, errors, versioning, libraries, agent skills), so the decision does not
  rest on missing pages.

## Sanitization provenance

GitHub push protection matched **Stripe Test API Secret Key** patterns in three captured
files. These are credential-shaped **example strings copied verbatim from public official
Stripe documentation** (the long-standing docs sample keys), not user or account credentials.
No local Stripe credential was inspected. To make the prospective documentary evidence safe to
store in Git **without using a push-protection bypass or allowlist**, the single example token
in each file was replaced with the deterministic marker `<REDACTED_PUBLIC_STRIPE_TEST_KEY>`;
all other bytes were preserved, so the semantic documentary content (authentication,
idempotency, and key-best-practices guidance) is intact.

| Source | Official URL | Original raw SHA256 | Sanitized repo SHA256 | Occurrences |
| --- | --- | --- | --- | --- |
| S13 | `https://docs.stripe.com/api/authentication` | `a793415c13e8d598f5431a593989170c67c6d72286392e3b8f710717fc6bec9c` | `4bdb62064b22f3d34abd23dd91872aae1f433bb2fbf95c52078178de107f6506` | 1 |
| S22 | `https://docs.stripe.com/api/idempotent_requests` | `d9b6e6c0537d86830ebdd078cf97a2e5f58f09303ad1e3e393160cec3bc5ddea` | `6213758fe18fc5e999fc189a881a0f8be0f8e0384b9bc38de41e662431493d96` | 1 |
| S30 | `https://docs.stripe.com/keys-best-practices` | `0f1d6bb6f9f8a81b231a36b4e5ec67a34fe966798ed38e47e99562994289faa2` | `2f29fe8bd53be3e806f4e8cc0778daa81325e873e2e549f9314cc2d50c81756d` | 1 |

Redaction marker: `<REDACTED_PUBLIC_STRIPE_TEST_KEY>`. Reason (each file): *public Stripe
documentation credential example removed for repository push-protection compatibility.* Semantic
documentary content otherwise preserved. Full machine-readable record is in the `sanitization`
block of `eligibility.json`, which retains both the pre- and post-sanitization source-manifest
hashes. The redaction changes the corpus bytes but **not the decision**: none of the five
grounds depends on the literal example key values.

## Reproducing the reasoning (for a hostile reviewer)

1. `python3` load each `experiments/multi-002/stripe/sources/web-extracts/S*.json`; the crawled
   text is in the `result` field.
2. Confirm Ground 1: grep S06 for `environment variable` (keys only) and `{{PRICE_ID}}` /
   "Provide the exact Price ID"; grep S10 for `{{PRICE_ID}}`; grep S28 for the `lookup_key`
   deploy-scenario framing. No source binds a price to an env var.
3. Confirm Ground 2: S34 products/search, S20 prices/list `product` + `lookup_keys` params, S35
   prices/search, S43 skills/plugins/MCP/`stripe agent setup`. The task names the product, so
   these yield an unambiguous route.
4. Recompute hashes with the algorithm above and compare to `eligibility.json`.

## Outcome

`NOT_ELIGIBLE` is a **successful experimental-design outcome**: the gate rejected Stripe before
any run because the intended `STRIPE_PRICE_ID` gap is researcher-created and the authentic Price
is machine-discoverable through official, permitted routes. Per the design (§4, §11), the correct
next step is to preregister a different prospectively documented candidate — **not** to make the
Stripe task harder, and **not** to select or implement another vendor within this task. No such
selection is performed here.

**Stripe API requests: 0. Checkout Sessions created: 0. Real MULTI-002 runs: 0.**
