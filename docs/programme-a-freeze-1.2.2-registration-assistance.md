# Programme A — Freeze 1.2.2: disclosed clerical assistance in human registration records

Status: prospective amendment. It is binding only when committed, annotated-tagged
`programme-a-freeze-1.2.2-registration-assistance`, and pushed by the Protocol Custodian (R01).
Machine-readable form: `experiments/programme-a/amendments/freeze-1.2.2.json`.
Protocol anchor: Freeze 1.2.1 pre-reveal `a436bf5d4bc5b4f8dfed8a80fdf8a557eb398e00`.

## State at adoption

No human registration exists. A1 is wholly unrevealed:
- no snapshot has been retrieved and no membership observed;
- no candidate identities have been observed;
- there is no entropy, permutation or selection;
- there are no eligibility decisions, vendor API calls, autonomous runs or outcomes.

G1 has not been crossed. No A1 information motivated this amendment.

## Defect H1

The first attestation of every frozen human registration form reads:

> "I am a natural person registering myself; this record was not created on my behalf by any model or other person"

It appears in `R03-entropy-custodian.form.json`, `R04-entropy-witness.form.json` and
`R05-R06-adjudicator.form.json`. Read literally, it forbids any clerical help in drafting, formatting
or constructing the JSON. That is not the property the protocol needs. The protocol needs human origin
and human ownership of every personal fact, disclosure answer, conflict statement and independence
statement, together with a personal review, attestation, signature and anchoring by the registrant.
The same reading of "made and signed by the person" in
`experiments/programme-a/a1/registrations/pre-reveal-audit.json` (`human_roles.self_registration`)
is clarified here.

## Replacement (only change)

In each of the three forms, that single attestation is replaced by these four attestations, in its position:

1. "I am a natural person registering myself."
2. "I personally supplied or explicitly confirmed every personal fact, disclosure answer, conflict
   statement and independence statement in this record; no model or other person chose any of them for me."
3. "I personally reviewed this complete final record before attesting, and I make this attestation and
   signature personally."
4. "Any drafting, formatting or mechanical JSON assistance used in preparing this record is truthfully
   disclosed in drafting_assistance."

Records also carry a new required field, `drafting_assistance`, with keys `used`, `types` and `description`:
- If `used` is `false`, then `types` must be `[]` and `description` must be `""`.
- If `used` is `true`, then `types` must be a non-empty list of distinct values from `MODEL_DRAFTING`,
  `MODEL_FORMATTING`, `HUMAN_CLERICAL` and `OTHER_TOOL`, and `description` must be non-empty text
  saying who or what assisted and how.

Records made under this amendment set `controlling_protocol` to
`{"amendment": "freeze-1.2.2", "tag": "programme-a-freeze-1.2.2-registration-assistance"}`.

**Prohibited.** No model or other person may choose or decide any answer to a conflict, disclosure or
independence attestation. No model or other person may make the attestation, the typed signature, the
registration commit or the anchoring tag for the registrant. The registration commit and tag must not
carry AI authorship or co-authorship. Assistance is disclosed in the record, not in authorship metadata.

**Honest limit.** Code can check the form, the disclosure field and the anchoring. It cannot check who
decided an answer. That rests on the registrant's attestation.

## Unchanged

- The frozen forms stay byte-identical. The replacement is applied by the validator from this amendment.
- All other attestations, fields, disclosures and `required_before` are unchanged.
- The typed signature, the personal commit and annotated-tag anchoring on origin, and the append-only
  rules are unchanged.
- `roles.json` is unchanged, including roles, conflicts, independence requirements and gate prerequisites.
- Sampling, RDG construction, the estimand, eligibility, documentary adjudication, R07/R08/R16/R17,
  entropy, execution, the outcome taxonomy and the analysis are unchanged.

## Operative tooling and the prior draft

`experiments/programme-a/a1/registrations/validate_humans.py` accepts only records made under this
amendment. It checks four things about this amendment's tag:
- it is annotated;
- it is on origin;
- it is on top of the protocol anchor;
- it carries these exact amendment bytes.

It also requires the record commit to descend from it, and the registration timestamp to fall no
earlier than it. Records under the superseded attestation are rejected.

`docs/programme-a-a1-human-phase/R05-MODEL-DRAFT-NON-OPERATIVE.md` stays NON-OPERATIVE and must not be
used or copied.
