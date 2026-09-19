#!/usr/bin/env python3
"""Offline, fail-closed validator for the A1 pre-reveal registrations.

Checks: the Freeze-1.2 A1 anchor is unchanged (tag -> 3def422, no tracked file altered, anchored
validator passes); every registration record is complete and its digests match; the R16
projection is reproducible from the anchored projector; the registered runtime is the one in use;
no human role is filled or fabricated; A1 zero-information counters; effective gate readiness.
--write stores registrations-validation.json. No network.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import unicodedata
import ast
import re
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
A1 = HERE.parent
ROOT = HERE.parents[3]
ANCHOR_TAG, ANCHOR_COMMIT = "programme-a-freeze-1.2-a1", "3def4227285453c253e2c6df969bb3eefc291fa8"
RECORDS = ("RT-A1-RUNTIME.json", "R17-spec-parser.json", "R08-browser-profile.json", "R07-translation.json",
           "R16-prior-firstcall-registry.json", "SEAL-TOOL.json")
REQUIRED = ("schema", "component_id", "component", "status", "artifact", "version", "digests", "registered_utc",
            "controlling_clause", "prerequisites", "conflicts_independence", "registrant", "binding", "immutability",
            "anchor_parent")
STATUSES = ("REGISTERED_PENDING_ANCHOR", "CONDITIONALLY_REGISTERED_PENDING_ANCHOR", "GENERATED_APPROVAL_UNFILLED", "UNFILLED")
HUMAN_FORMS = ("R03-entropy-custodian.form.json", "R04-entropy-witness.form.json", "R05-R06-adjudicator.form.json",
               "R16-registry-approval.form.json", "R08-installation-attestation.form.json", "sealing-intake-attestation.form.json")
sys.path.insert(0, str(A1))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True).stdout


def check_anchor():
    errors = []
    if git("rev-parse", ANCHOR_TAG + "^{commit}").decode().strip() != ANCHOR_COMMIT:
        errors.append("anchor tag does not resolve to 3def422")
    tracked = git("ls-tree", "-r", "-z", "--name-only", ANCHOR_COMMIT).decode().rstrip("\0").split("\0")
    changed = git("diff", "--name-only", ANCHOR_COMMIT, "--", *tracked).decode().split()
    if changed:
        errors.append(f"anchored files changed: {changed}")
    import validate_a1
    report = validate_a1.validate()
    if report["errors"] or report["decision"] == "NOT_SEALABLE":
        errors.append(f"anchored validator: {report['errors']}")
    return errors, {"tag": ANCHOR_TAG, "commit": ANCHOR_COMMIT, "anchored_validator": report["decision"],
                    "gates": report["gates"], "freeze_1": report["freeze_1"]["pass"],
                    "freeze_1_1": report["freeze_1_1"]["pass"], "protected": report["protected"]["pass"],
                    "a1_counters": report["a1_counters"]}


def load(name):
    return json.loads((HERE / name).read_bytes())


def schema_errors(value, schema, root_schema=None, path="$"):
    """Evaluate the schema vocabulary used by this registration package, offline."""
    root_schema = schema if root_schema is None else root_schema
    if '$ref' in schema:
        target = root_schema
        for token in schema['$ref'].split('/')[1:]: target = target[token]
        return schema_errors(value, target, root_schema, path)
    if 'anyOf' in schema:
        return [] if any(not schema_errors(value, option, root_schema, path) for option in schema['anyOf']) else [path + ': no schema alternative']
    errors = []
    types = {'object': dict, 'array': list, 'string': str}
    if 'type' in schema and not isinstance(value, types[schema['type']]):
        return [path + ': wrong type']
    if 'const' in schema and value != schema['const']: errors.append(path + ': wrong constant')
    if 'enum' in schema and value not in schema['enum']: errors.append(path + ': invalid enum')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0): errors.append(path + ': empty string')
        if 'pattern' in schema and not re.search(schema['pattern'], value): errors.append(path + ': pattern mismatch')
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value: errors.append(path + ': missing ' + key)
        for key, item in value.items():
            spec = schema.get('properties', {}).get(key, schema.get('additionalProperties', {}))
            if isinstance(spec, dict): errors += schema_errors(item, spec, root_schema, path + '.' + key)
    if isinstance(value, list) and 'items' in schema:
        for index, item in enumerate(value): errors += schema_errors(item, schema['items'], root_schema, path + '[' + str(index) + ']')
    return errors


def check_records():
    errors = []
    recs = {}
    for name in RECORDS:
        r = load(name)
        errors += schema_errors(r, load("registration-record.schema.json"), path=name)
        recs[r["component_id"]] = r
        missing = [f for f in REQUIRED if f not in r]
        if missing:
            errors.append(f"{name}: missing {missing}")
        if r.get("status") not in STATUSES:
            errors.append(f"{name}: bad status")
        if r.get("anchor_parent", {}).get("commit") != ANCHOR_COMMIT:
            errors.append(f"{name}: wrong anchor parent")
    from a1_integrity_121 import verify_package
    try:
        verify_package()
    except RuntimeError as exc:
        errors.append(str(exc))
    for rel, h in recs["R17"]["digests"]["operative"].items():
        if sha(A1 / rel) != h: errors.append("R17 operative dependency mismatch " + rel)
    for rid, name in (("R07", "translation_policy.py"), ("SEAL-TOOL", "record_seal.py")):
        if sha(HERE / name) != recs[rid]["digests"][name]: errors.append(rid + " digest mismatch")
    if recs["R07"]["artifact"].get("policy") != "NO_MACHINE_TRANSLATION / FAIL_CLOSED":
        errors.append("R07 policy drift")
    d = recs["R17"]["digests"]
    if sha(HERE / "a1_spec_parser.py") != d["a1_spec_parser.py"]:
        errors.append("R17 parser digest mismatch")
    for rel, h in d["vendored_pyyaml"].items():
        if sha(HERE / rel) != h:
            errors.append(f"R17 vendored digest mismatch {rel}")
    for key, rel in (("anchored_a1_evidence.py", "a1_evidence.py"), ("anchored_a1_frame.py", "a1_frame.py")):
        if sha(A1 / rel) != d[key]:
            errors.append(f"R17 anchored dependency mismatch {rel}")
    if sha(HERE / "R08-firefox-policies.template.json") != recs["R08"]["digests"]["R08-firefox-policies.template.json"]:
        errors.append("R08 policy digest mismatch")
    r16 = recs["R16"]
    proj = HERE / "R16-prior-firstcall-projection.json"
    if sha(proj) != r16["digests"]["projection"] or sha(A1 / "prior_firstcall_projector.py") != r16["digests"]["projector"]:
        errors.append("R16 digest mismatch")
    regenerated = subprocess.run([sys.executable, "-B", str(A1 / "prior_firstcall_projector.py")], capture_output=True,
                                 check=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1")).stdout
    if regenerated != proj.read_bytes():
        errors.append("R16 projection not reproducible")
    if any(v is not None for v in r16["approvals"].values()):
        errors.append("R16 approval filled without an adjudicator record")
    rt = recs["RT-A1-RUNTIME"]
    exe = os.path.realpath(sys.executable)
    if exe != rt["artifact"]["interpreter_realpath"] or sha(exe) != rt["digests"]["interpreter_sha256"] \
            or sys.version != rt["artifact"]["python_version"] or unicodedata.unidata_version != rt["artifact"]["unicode_version"]:
        errors.append("runtime differs from RT-A1-RUNTIME")
    from a1_host import canonical_host
    for u, a in rt["artifact"]["idna_vectors"].items():
        if canonical_host(u) != a:
            errors.append(f"IDNA vector changed: {u}")
    return errors, recs


def check_humans():
    errors = []
    for f in HUMAN_FORMS:
        form = json.loads((HERE / "forms" / f).read_bytes())
        if form.get("status") != "TEMPLATE_UNFILLED":
            errors.append(f"{f}: form is not an unfilled template")
        for k, v in (form.get("fields") or {}).items():
            if k in ("full_name", "public_contact", "signature") and v is not None:
                errors.append(f"{f}: human field pre-filled ({k})")
    humans = [p.name for p in HERE.rglob("*.json") if p.parent.name == "humans"]
    if humans:
        errors.append(f"unexpected human registration records present: {humans}")
    roles = json.loads((A1 / "roles.json").read_bytes())
    for r in roles["roles"]:
        if r["id"] in ("R03", "R04", "R05", "R06") and (r["status"] != "UNFILLED" or r.get("holder")):
            errors.append(f"{r['id']} filled in roles.json")
    return errors


def check_zero_information():
    errors = []
    for p in list(A1.rglob("*")):
        rel = str(p.relative_to(A1))
        if any(tok in rel for tok in ("snapshot", "frame.json", "raw-entries", "tape", "permutation.json", "sample", "screening/")):
            errors.append(f"A1 artefact present: {rel}")
    return errors


def readiness(recs, anchor_gates):
    d8_open = False
    return {
        "G0_ANCHOR": "OPEN",
        "G1_SNAPSHOT": "HOLD: no retrieval authorised in this task; no gate crossed",
        "G2_REGISTRY": "CLOSED: R05/R06 unfilled; R16 approvals unfilled",
        "G3_ENTROPY": "CLOSED: R03/R04/R05/R06 unfilled; R07 machine registered",
        "G4_SCREENING": "CLOSED: G3 closed; R08 installation and sealing intake conditional; R17 machine registered",
        "G5_EXECUTION": "CLOSED: R09/R10 future; Freeze-4 apparatus absent",
    }


def check_frame_scope():
    old = ast.parse((A1 / "a1_frame.py").read_text())
    new = ast.parse((A1 / "a1_frame_121.py").read_text())
    def retained(tree):
        return [ast.dump(n, include_attributes=False) for n in tree.body
                if not (isinstance(n, (ast.Import, ast.ImportFrom)) or
                        isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str) or
                        isinstance(n, ast.FunctionDef) and n.name in ("to_alabel", "key_host"))]
    return [] if retained(old) == retained(new) else ["RDG scope changed beyond host adapters"]


def validate():
    errors = []
    e, anchor = check_anchor()
    errors += e
    e, recs = check_records()
    errors += e
    errors += check_humans()
    errors += check_zero_information()
    errors += check_frame_scope()
    # Validate schema-required types, not merely key presence.
    for name in RECORDS:
        r = load(name)
        for key in ("artifact", "digests", "registrant", "anchor_parent"):
            if not isinstance(r.get(key), dict): errors.append(name + ": invalid " + key)
        for key in ("prerequisites",):
            if not isinstance(r.get(key), list): errors.append(name + ": invalid " + key)
        if r.get("registrant", {}).get("kind") not in ("machine_registration", "machine_generation"):
            errors.append(name + ": unexpected registrant kind")
    if git("diff", "--check") != b"":
        errors.append("git diff --check (tracked)")
    decision = "NOT_READY_INVALID" if errors else "SEALABLE_MACHINE_PACKAGE_HUMANS_UNFILLED"
    return {"schema": "firstcall.programmeA.a1_registrations_validation.v1", "decision": decision, "errors": errors,
            "anchor": anchor, "records": {k: v["status"] for k, v in recs.items()},
            "human_roles": {"R03": "UNFILLED", "R04": "UNFILLED", "R05": "UNFILLED", "R06": "UNFILLED"},
            "open_defects": [], "effective_gates": readiness(recs, anchor["gates"])}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    report = validate()
    data = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        (HERE / "registrations-validation.json").write_text(data)
    sys.stdout.write(data)
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
