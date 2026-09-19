# Programme A / A1: human registration phase (working pack, not a registration)

Prepared 2026-09-19 against the pre-reveal anchor `a436bf5d4bc5b4f8dfed8a80fdf8a557eb398e00`
(tag `programme-a-freeze-1.2.1-pre-reveal`). Nothing here amends Freezes 1, 1.1, 1.2 or 1.2.1,
fills a role, or signs anything for anyone. It only explains the frozen rules and gives each human
the steps they must carry out themselves.

Sources: `experiments/programme-a/a1/roles.json` (frozen conflicts, gates, registration mechanism),
enforced in code by `validate_a1.role_conflicts`; Freeze 1.1 §4, §5, §8.4, §8.5; Freeze 1.2 §6, §9, §15;
the Freeze 1.2.1 registration forms in `experiments/programme-a/a1/registrations/forms/`.

## 1. Conflict matrix (frozen rules only)

Frozen conflicts (`roles.json`): R01 and R02 may not be R03/R04. R03 is not R01, R02, R05, R06 or R10.
R04 is not R01, R02, R03, R05 or R06. R05 is not R03, R04 or R06. R06 is not R03, R04 or R05.
R09 operator is not R05/R06. R10 is not R03. R16 is an act by R05 and R06, not a separate seat.
R08 attestations are made per adjudicator about their own installation.

Pairwise, for one person holding both roles:

|      | R01/R02 (Ross) | R03 | R04 | R05 | R06 |
| --- | --- | --- | --- | --- | --- |
| R03  | PROHIBITED | — | PROHIBITED | PROHIBITED | PROHIBITED |
| R04  | PROHIBITED | PROHIBITED | — | PROHIBITED | PROHIBITED |
| R05  | CONDITIONAL | PROHIBITED | PROHIBITED | — | PROHIBITED |
| R06  | CONDITIONAL | PROHIBITED | PROHIBITED | PROHIBITED | — |

Ross (already R01 protocol custodian and R02 snapshot custodian):

| Role / act | Ross | Rule |
| --- | --- | --- |
| R03 entropy custodian | PROHIBITED | R03 conflicts with R01, R02 |
| R04 entropy witness | PROHIBITED | R04 conflicts with R01, R02 |
| R05 adjudicator 1 | CONDITIONAL | no frozen conflict with R01/R02; conditions below |
| R06 adjudicator 2 | CONDITIONAL | as R05; never both |
| R05 and R06 together | PROHIBITED | R05/R06 conflict |
| R16 approval | CONDITIONAL | only as the R05/R06 holder, one approval, his own |
| R08 attestation | CONDITIONAL | only for his own installation, only if an adjudicator |
| Seal-store custodian (Freeze 1.2.1 sealing intake) | PROHIBITED if adjudicator | an adjudicator with store access could read the other's codes before sealing; this breaks the R05/R06 attestation "no access to ... the other adjudicator's codes" |
| R09 operator (future) | PROHIBITED if adjudicator | R09 operator is not R05/R06 |
| R10 reviewer (future) | ALLOWED | conflicts only with R03 |

Conditions on Ross as an adjudicator (all come from the frozen R05/R06 form):
1. Complete the disclosures truthfully: protocol author (yes), snapshot custodian (yes), saw quarantined
   drafts or rejected names, knows historical FIRSTCALL outcomes, viewed the A1 frame before registration.
2. Never receive the tape, priorities, draw order or the other adjudicator's codes before a block is sealed.
   As R01 he commits only the published SHA256 commitments and post-reveal ledgers.
3. Do not act as seal-store custodian or R09 operator.

## 2. Minimum number of distinct humans: 4

Proof. R03, R04, R05 and R06 are pairwise in conflict:
R03–R04 (R04 is not R03), R03–R05, R03–R06, R04–R05, R04–R06 and R05–R06.
They form a 4-clique in the conflict graph, so four different people are needed.
All four seats are mandatory for G3 (`G3_ENTROPY requires R03, R04, R05, R06`), so no smaller set can
reach entropy. Two humans cannot suffice: Ross cannot take R03 or R04, so Human B would have to hold
both R03 and R04, which is prohibited, and would also have to hold both R05 and R06.

Sufficiency. The following allocation satisfies every frozen conflict:

| Human | Roles |
| --- | --- |
| A = Ross Buckley | R01, R02 (held); R05 adjudicator 1 (+ his R16 approval, his R08 attestation) |
| B = unidentified independent human | R06 adjudicator 2 (+ their R16 approval, their R08 attestation) |
| C = unidentified independent human | R03 entropy custodian |
| D = unidentified independent human | R04 entropy witness |

Seal-store custodian: must be neither R05 nor R06. The frozen protocol does not name it. The natural
holder is C (R03), who already holds block release and computes selection after each block seal.
Whether seal custody counts as an "apparatus" role under R03's conflict list is not settled by frozen
text. Treat it as CONDITIONAL, and have Ross (R01) record the choice before G4. D (R04) is an equally
permitted fallback. Future: the R09 operator may be D, never Ross or B. The R10 reviewer may be Ross,
B or D, never C. So four humans suffice through G5 as well.

A stronger-independence alternative: five humans, with Ross holding no adjudicator seat. The frozen
rules do not require it, but it removes the protocol author from coding. It is Ross's choice; it is
not recommended here only because it costs a fifth person.

## 3. Ross's assignment and exact registration action

Recommended: Ross = R05. Register before G1 if practical, so that the disclosure
`viewed_A1_frame_before_registration` is `false`. The frozen rules do not require this ordering.

Ross must personally review, create, sign and anchor his record. An agent must not do this.

1. Read Freeze 1.2 (`docs/programme-a-freeze-1.2-a1-amendment.md`), `roles.json` R05, and the form
   `experiments/programme-a/a1/registrations/forms/R05-R06-adjudicator.form.json`.
2. Review the proposed record in `R05-PROPOSED-FOR-ROSS-REVIEW.md`. Correct anything untrue, set
   `registered_utc` to the current UTC time, and save it as
   `experiments/programme-a/a1/registrations/humans/R05-registration.json`.
3. Sign and anchor it personally. Form `signature_method` is "annotated tag or signed commit made by the
   registrant personally". Without a signing key, the typed signature plus your own annotated tag is
   the method. Do not add AI co-author trailers; the validator rejects AI/model/tool authorship.

   ```sh
   git add experiments/programme-a/a1/registrations/humans/R05-registration.json
   git commit -m "programme-a: register R05 adjudicator (self-registration)"
   git tag -a programme-a-a1-R05-registration -m "R05 self-registration by the registrant"
   git push origin v0.2-real-agent refs/tags/programme-a-a1-R05-registration
   git fetch origin && python3 -B experiments/programme-a/a1/registrations/validate_humans.py
   ```

Validator: `experiments/programme-a/a1/registrations/validate_humans.py` (additive tooling). It
implements `roles.json` §registration_mechanism: a schema-valid record committed under an annotated
tag on origin fills the slot. It never rewrites `roles.json`. Verified records become an in-memory
overlay passed to the frozen `validate_a1.role_conflicts` and `validate_a1.gate_status`. Use
`--with-pre-reveal` to also run the Freeze 1.2.1 validator. That validator flags any `humans/` record
by design, and only that error is forgiven, and only when every record verifies. Not yet covered
(separate records, later): R16 approvals, R08 attestations, the sealing-intake attestation, and whether
a slot was anchored before its first gate was crossed.

## 4. R16 (prior-FIRSTCALL registry approval)

Who: exactly the R05 holder and the R06 holder, independently (`roles.json` R16 "act_by_R05_and_R06";
Freeze 1.2 §15). Nobody else, and neither may approve for the other. Both must approve; any BLOCK or
ambiguity keeps G2 closed (Freeze 1.1 §5, §8.4).

What: `experiments/programme-a/a1/registrations/R16-prior-firstcall-projection.json`
(SHA256 `799c9f0bd305842b6acbaee8546564b9370117179cf5cd61424b3b56323fe6b2`, 313 paths, 152 marked
`reviewer_confirmation_required`, including the flagged `experiments/multi-001/candidates.json`).
The procedure is in `ADJUDICATOR-PACK.md` §5. Review the ledger's projections only. Never open files classed
`EXCLUDED_RESULT_OR_EVIDENCE_CONTEXT` (Freeze 1.1 §5: never read receipts, outcomes, traces or results).
No comparison with A1 is possible or permitted. Approvals are anchored like registrations, before G2.

## 5. Gate order from now

Frozen gate requirements (`roles.json` gates), with status at the pre-reveal anchor:

**MUST HAPPEN BEFORE G1:** nothing further. G1 requires G0 (anchored), R02 (Ross, anchored), R12
(operative `a1_frame_121.py`, anchored in Freeze 1.2.1) and R18 (pinned PSL, anchored). No human
registration is a G1 prerequisite. G1 is legitimately crossable now; the HOLD is a task-level
choice, not a frozen rule. Recommended but not required: Ross registers R05 first (see §3).

**CAN HAPPEN BEFORE OR AFTER G1, BUT BEFORE G2** (G2 does not depend on G1):
R05 and R06 registrations anchored (their first gate is G2), then both R16 approvals anchored, then G2.

**MUST HAPPEN BEFORE G3:** G1 crossed and frame G sealed (R02, once). G2 open. R03 and R04
registrations anchored. R05/R06 already anchored ("adjudicators registered BEFORE any order exists").
R07 and R13 anchored (done). Then the one entropy call (`ENTROPY-CEREMONY.md`).

**MUST HAPPEN BEFORE G4 (first block release):**
- each adjudicator's R08 installation attestation, anchored before their first block;
- the R05/R06 roster for the seal tool: a roster file assembled from the two anchored R05/R06 records,
  which already carry the `human-roster.schema.json` fields;
- the seal-store custodian designated (not R05/R06);
- the sealing-intake attestation (separate authenticated intake, no participant store access,
  external checkpoint custody);
- R03 active. R11, R14 and R17 are already anchored.

**MUST HAPPEN BEFORE G5:** Freeze-4 apparatus sealed; R09 scheduler and operator (operator not R05/R06);
R10 reviewer (not R03).
