# R05 registration: PROPOSED, NOT EFFECTIVE, for Ross Buckley's personal review

This is a proposal prepared by an AI assistant. It is **not a registration**. It has no typed signature,
no confirmation, no timestamp and no contact address. Only Ross may supply those, after reading every
statement. It becomes effective only when Ross personally does all of the following:
1. saves it as `experiments/programme-a/a1/registrations/humans/R05-registration.json`;
2. commits it;
3. creates his own annotated tag;
4. pushes it (README §3);
5. runs `validate_humans.py`, which must report R05 `REGISTERED`.

Do not keep any statement that is not true. If any required attestation is untrue, do not register.

## What Ross must personally do

1. Read the anchored Freeze 1.2 amendment (commit `3def4227…`), `roles.json` R05, and the frozen form
   `experiments/programme-a/a1/registrations/forms/R05-R06-adjudicator.form.json`.
2. Check every disclosure below, especially `saw_quarantined_drafts_or_rejected_names`. The
   repository's pre-reveal audit says you saw rejected drafts. Answer from your own memory.
3. Replace each `<<ROSS: ...>>` placeholder:
   - `signature` in two places: type your full name yourself;
   - `attestations_confirmed`: the JSON value `true` (no quotes), only if every attestation is true;
   - `registered_utc`: current UTC time, not later than your commit;
   - `public_contact`: the contact you choose to publish in the repository (it becomes public on GitHub);
   - `languages_read`: informational only.
4. Approve this typed attestation, which the record carries verbatim:

   > I confirm that every statement in attestations_all_required_true is true for me.

   The frozen form's `signature_method` is "annotated tag or signed commit made by the registrant
   personally". With no signing key, your typed signature plus your own annotated tag is the method.
   No signing key was created for you.

## Proposed record

```json
{
  "schema": "firstcall.programmeA.a1_human_registration.v1",
  "form": "A1 adjudicator registration (R05 ADJ-1 / R06 ADJ-2)",
  "id": "adj-r05",
  "role": "R05",
  "kind": "human",
  "status": "FILLED",
  "full_name": "Ross Buckley",
  "signature": "<<ROSS: type your full name>>",
  "independence_attestation": "I confirm that every statement in attestations_all_required_true is true for me.",
  "controlling_protocol": {"commit": "a436bf5d4bc5b4f8dfed8a80fdf8a557eb398e00", "tag": "programme-a-freeze-1.2.1-pre-reveal"},
  "fields": {
    "slot": "R05",
    "full_name": "Ross Buckley",
    "public_contact": "<<ROSS: contact to publish>>",
    "registered_utc": "<<ROSS: YYYY-MM-DDTHH:MM:SSZ>>",
    "languages_read": "<<ROSS: informational only>>",
    "signature": "<<ROSS: type your full name>>",
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
  "attestations_confirmed": "<<ROSS: replace with true only after reading each statement>>",
  "disclosures_required": {
    "is_protocol_author": true,
    "is_capture_or_snapshot_custodian": true,
    "saw_quarantined_drafts_or_rejected_names": "<<ROSS: true or false from your own knowledge>>",
    "knows_historical_firstcall_outcomes": true,
    "viewed_A1_frame_before_registration": false,
    "other_conflicts": [
      "Holds R01 protocol custodian and R02 source/snapshot custodian (roles.json); will perform the single A1 snapshot retrieval as R02 after registering."
    ]
  },
  "supplementary_statements": [
    "At registration I have not seen A1 membership, any A1 candidate identity, entropy, a permutation or any draw order.",
    "I accept the R05 independence restrictions of roles.json and the frozen R05/R06 form.",
    "I will not receive R03/R04 entropy material (tape, priorities, order) or the other adjudicator's decisions before the permitted reveal; as R01 I handle only published SHA256 commitments and post-reveal ledgers.",
    "I will not act as seal-store custodian or R09 operator while holding R05.",
    "I will complete my R08 browser installation attestation separately before my first block."
  ],
  "required_before": "G2_REGISTRY (registry approval) and G3_ENTROPY"
}
```

Two points need Ross's attention:

- **`viewed_A1_frame_before_registration: false`** is true only if the record is anchored before G1.
  If Ross retrieves the snapshot first, this must be `true`, and the first supplementary statement must
  be removed.
- **The last `other_conflicts` clause** assumes Ross will still perform the retrieval as R02. Frozen
  text permits that, and the validator requires R01/R02 holders to disclose both roles.
