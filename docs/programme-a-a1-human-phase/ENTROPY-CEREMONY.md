# FIRSTCALL A1: entropy ceremony (R03 custodian, R04 witness)

DO NOT PERFORM BEFORE G3. It requires: G1 crossed and frame G sealed and published; G2 open;
R03, R04, R05 and R06 registrations anchored. Frozen sources: Freeze 1.1 §8.5, Freeze 1.2 §6
steps 9–12, `roles.json` R03/R04, `a1_permutation.py` (R13), forms R03/R04.

## Who

- **C, entropy custodian (R03):** an independent person with no other study role. They must not
  be Ross (R01/R02), either adjudicator, or the apparatus reviewer (R10). They generate the random
  numbers once, keep them private, release blocks of 6 one at a time, and compute selection mechanically.
- **D, entropy witness (R04):** an independent person, not Ross, not C, not an adjudicator. They
  watch the single generation, check the inputs, and sign the log.

Both register themselves with forms `R03-entropy-custodian.form.json` and `R04-entropy-witness.form.json`.
They use the same record envelope and signing as adjudicators (`ADJUDICATOR-PACK.md` §6), with the
form's own fields and attestations and no `disclosures_required`. The files are
`humans/R03-registration.json` and `humans/R04-registration.json`. Adjudicators never
attend, and never receive the random numbers or the order.

## Script

1. **Check inputs (C and D together).** On the registered runtime (`RT-A1-RUNTIME.json`: interpreter
   path and SHA256 `b502cb4c…74a0bf`, Python 3.14.6, Unicode 16.0.0), D confirms:
   - the interpreter hash;
   - that the sealed `frame.json` published by R02 is on origin under its annotated tag;
   - `G_sha256` and `G_size` from that file.

   D writes both numbers into the log. Do not run under the offline test guard
   (`PYTHONPATH=.../offline`); it deliberately blocks `os.urandom`.
2. **One call (C, with D watching).** From the repository root, run exactly once, using the registered
   interpreter path from `RT-A1-RUNTIME.json` (shown here as `<registered-python>`):

   ```sh
   umask 077
   <registered-python> -B -c '
   import json, sys; sys.path.insert(0, "experiments/programme-a/a1")
   import a1_permutation as p
   frame = json.load(open(sys.argv[1]))
   tape = p.generate_tape(frame["G_size"])          # the single os.urandom(32*|G|) call
   open(sys.argv[2], "xb").write(tape)              # custody file; "x" refuses to overwrite
   print("G_sha256", frame["G_sha256"], "tape_sha256", p.tape_commitment(tape))' \
     <path-to-sealed-frame.json> <C-private-custody-path>
   ```

   The custody path must be outside the repository and readable only by C.
3. **Any error aborts the cohort.** An exception, a short tape, a failed write or a second invocation
   ends it. Do not retry and do not reroll (Freeze 1.1 §8.5). C and D record the failure in the log.
4. **Commit before interpretation.** C and D both sign a generation log: UTC time, interpreter hash,
   `G_sha256`, `G_size`, `tape_sha256`, "one call, no retries", both names. R01 (Ross) commits and pushes
   the log under an annotated tag. It contains only hashes, never the tape.
5. **Order and blocks (C alone, after step 4 is on origin).** C computes
   `p.permutation(G, tape, tape_sha256)`. A tie aborts the cohort. C then releases block 1 in
   `p.presentation_order(...)`, and releases each later block only after the previous one is sealed by
   both adjudicators. Selection is computed mechanically from the sealed statuses.
6. **Secrecy.** C tells nobody (Ross, adjudicators, D) the tape, priorities or order until the
   sample is sealed. Then the tape is revealed and anyone can check it against `tape_sha256`.

No hash can prove the operating system's randomness was honest. The witness and the prior commitment
make the one-call process auditable; they do not make it cryptographically fraud-proof.
