# FIRSTCALL A1: information for an adjudicator

You are being asked to be one of two independent adjudicators (seat R06). Please read all of this
before agreeing. You do not need to understand the code.

## 1. What this is

FIRSTCALL (Programme A) measures how often a fresh autonomous AI agent can complete, and independently
verify, a typical real-world task on a public software platform. Population A1 is a fixed public catalogue of API descriptions (APIs.guru). A computer
shuffles it once. Then two people read each platform's public documentation, 6 platforms at a
time, and decide whether it is eligible for the study. Your job is that reading and deciding.
The two adjudicators work separately, so that neither can influence the other.

## 2. Your role

For each platform you are given:
- its API description file;
- a short list of starting web links (from that file);
- the written checklist (the decision protocol).

Follow only visible links on the platform's own site. Answer each checklist question as YES, NO or
UNRESOLVED, and write a short evidence note for each page you used. You have a time and page budget:
eligibility and categories, 16 pages / 60 minutes; terms of use, 6 pages / 20 minutes; one retry.
Blocks arrive one at a time, and you have 48 hours per block. Expect up to 3 blocks a week, possibly
for several months. You also approve one list from earlier FIRSTCALL projects (§5) before the study starts.

## 3. What you must not do

- Do not use AI tools, translation tools or anyone else to decide or write your answers.
- Do not search the web, type or guess URLs, log in, create accounts, call APIs, or use scripts or extensions.
- Do not discuss any platform, block or answer with the other adjudicator, or anyone else, until the
  whole block has been sealed.
- Do not look for, ask for, or accept the shuffle order, the random numbers, other blocks, or the other
  adjudicator's answers.
- Do not translate non-English pages, whether yourself or with a tool. Use an English first-party page
  if the permitted links reach one. If the only relevant evidence is not in English, record the
  question as UNRESOLVED with the reason TRANSLATION_NOT_AVAILABLE. Never treat it as a NO.
- Do not bypass cookie walls, paywalls, logins or other access restrictions. Record what blocked you.
- Do not keep copies or screenshots of pages unless the checklist asks.

## 4. Independence, what you see, confidentiality

- **Independence** means your answers are only yours. They are formed from the same inputs the other
  adjudicator receives, with no contact about the work until sealing. You must not hold the entropy roles (R03/R04).
- **Candidate identities:** yes, you will see the names of the platforms in each released block of 6,
  in a scrambled order. You will not see the full order or which platforms are "next".
- **The other adjudicator's decisions:** no, not before you have both sealed that whole block.
- **Security:** you submit answers only through the private channel the seal custodian gives you.
  You get no direct access to the answer store. Keep any login details private. Do not share block
  contents or your answers outside the process until the study is published.
- **Browser:** Firefox ESR on a desktop computer, set up with the project's locked settings file
  (next section). Use a fresh private window per platform, restart the browser between platforms,
  stay logged out, use an en-GB language setting and a UK internet connection (no VPN or proxy).

### Browser attestation (R08), done by you shortly before your first block

1. Install Firefox ESR (desktop). Do not install extensions.
2. Copy `experiments/programme-a/a1/registrations/R08-firefox-policies.template.json` to the Firefox
   `distribution/policies.json` location for your operating system. Check it is unchanged: its SHA256
   must be `a64ea0938304bf7e129be2bd7e196670aadfdd53cd4bb148ffb2dc2230b400aa`.
3. Open `about:policies` and confirm it shows **Active**. Open `about:support` and note the exact **Version**.
4. Fill in `forms/R08-installation-attestation.form.json`: your seat, the ESR version, `Active`,
   the policies hash above, your operating-system timezone, egress country `GB`, and the UTC time.
   Sign it yourself (§6) before your first block. Do not change the version during a block. Record any
   update between blocks. Both adjudicators must use the same ESR major version.

Do not open any study platform's pages while setting up.

## 5. Approving the earlier-projects list (R16)

Before the study starts, each adjudicator separately checks a list of files from earlier FIRSTCALL
work: `experiments/programme-a/a1/registrations/R16-prior-firstcall-projection.json`. Confirm its
SHA256 is `799c9f0bd305842b6acbaee8546564b9370117179cf5cd61424b3b56323fe6b2`. The check asks whether
the list correctly identifies which platforms FIRSTCALL already targeted, so they are excluded.
Fixed exclusions: Postmark, Resend, CF-001/Acme fixtures and the MULTI-002 Stripe target.

- Review each ledger entry with `reviewer_confirmation_required: true` (152 of them), using only
  what the ledger shows (path, class and extracted fields).
- Never open files marked `EXCLUDED_RESULT_OR_EVIDENCE_CONTEXT`. They contain earlier results, and you must not see them.
- Look specifically at `experiments/multi-001/candidates.json`. Decide whether the ledger's
  handling of it is right.
- Fill in `forms/R16-registry-approval.form.json` with **APPROVE**, or **BLOCK** if anything is wrong or
  unclear. Do this without consulting the other adjudicator, and sign it (§6).

## 6. How you register and sign yourself

You create your own record. Nobody may do it for you.

1. Ross gives you write access to the project repository on GitHub.
2. In the GitHub web page for branch `v0.2-real-agent`, choose **Add file → Create new file** and
   name it `experiments/programme-a/a1/registrations/humans/R06-registration.json`.
3. Paste the record below, fill every `<...>`, and set each disclosure honestly. If any statement is not
   true for you, stop and tell Ross; do not register. For `registered_utc`, use the current UTC time
   just before you commit. It must not be later than your commit.
4. Commit it yourself with the message `programme-a: register R06 adjudicator (self-registration)`.
   The commit made from your own account, together with your typed signature, is your signature.
   Do not ask anyone, or any AI tool, to write or commit it for you. Ross then anchors it with an
   annotated tag and pushes it; nobody may edit the file afterwards. A mistake needs a new,
   separately reviewed procedure, never an edit.

```json
{
  "schema": "firstcall.programmeA.a1_human_registration.v1",
  "form": "A1 adjudicator registration (R05 ADJ-1 / R06 ADJ-2)",
  "id": "adj-r06",
  "role": "R06",
  "kind": "human",
  "status": "FILLED",
  "full_name": "<your full legal name>",
  "signature": "<type your full name again>",
  "independence_attestation": "I confirm that every statement in attestations_all_required_true is true for me.",
  "controlling_protocol": {"commit": "a436bf5d4bc5b4f8dfed8a80fdf8a557eb398e00", "tag": "programme-a-freeze-1.2.1-pre-reveal"},
  "fields": {
    "slot": "R06",
    "full_name": "<your full legal name>",
    "public_contact": "<an email address you will use for this study>",
    "registered_utc": "<YYYY-MM-DDTHH:MM:SSZ>",
    "languages_read": "<informational only>",
    "signature": "<type your full name again>",
    "signature_method": "annotated tag or signed commit made by the registrant personally"
  },
  "attestations_all_required_true": [
    "I am a natural person registering myself; this record was not created on my behalf by any model or other person",
    "I have read the anchored Freeze-1.2 A1 amendment (commit 3def4227285453c253e2c6df969bb3eefc291fa8) and the role's duties in roles.json",
    "I will code every predicate personally; no model-generated or third-party codes",
    "I will not communicate with the other adjudicator about any RDG until both records for its block are sealed by hash",
    "I have no access to Programme A outcomes, draw order, priorities or the other adjudicator's codes before sealing",
    "I will examine only the sealed primary entry of each released RDG; I will not substitute another entry",
    "I will use only the frozen E1/E2 leads, the R08 browser profile, the frozen vocabulary and budgets; no search, guessed URLs, login, API calls or automation",
    "I hold no entropy custodian (R03) or witness (R04) role and am not the other adjudicator",
    "I accept that no replacement is possible after any packet is opened"
  ],
  "attestations_confirmed": true,
  "disclosures_required": {
    "is_protocol_author": <true|false>,
    "is_capture_or_snapshot_custodian": <true|false>,
    "saw_quarantined_drafts_or_rejected_names": <true|false>,
    "knows_historical_firstcall_outcomes": <true|false>,
    "viewed_A1_frame_before_registration": <true|false>,
    "other_conflicts": []
  },
  "required_before": "G2_REGISTRY (registry approval) and G3_ENTROPY"
}
```

The R05 holder uses the same record with `"id": "adj-r05"`, `"role": "R05"`, `"slot": "R05"` and the
file name `R05-registration.json`. You may add `"supplementary_statements": ["..."]` for extra
disclosures. `experiments/programme-a/a1/registrations/validate_humans.py` checks the record against
the frozen form. It rejects anything incomplete, altered, unanchored, or conflicting with another role.
