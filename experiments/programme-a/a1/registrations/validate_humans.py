#!/usr/bin/env python3
"""Additive, fail-closed validator for A1 human registration records (R03-R06).

Tooling only. The frozen roles.json is never rewritten. roles.json's registration_mechanism fills a
slot with "a schema-valid record committed under an annotated tag whose peeled commit is on origin".
This module verifies such records and builds an in-memory overlay of roles.json: each verified slot
becomes status FILLED with the registrant as holder. The overlay is passed unchanged to the frozen
validate_a1.role_conflicts and validate_a1.gate_status, so the conflict pairs and gate prerequisites
are the frozen ones. Any error anywhere means no slot is overlaid.

Record location: experiments/programme-a/a1/registrations/humans/<ROLE>-registration.json.
The role is read from the record's content. The filename must merely agree with it.

A record counts as REGISTERED only when all of these hold:
- it validates against its frozen form (forms/*.form.json) and the envelope below;
- exactly one commit in the whole repository ever touched its path, and that commit added it;
- the working-tree bytes equal that commit's bytes (append-only: no overwrite, replacement or deletion);
- the adding commit descends from the controlling pre-reveal commit;
- an annotated tag's peeled commit contains those bytes and is on the origin branch.

Signature: the frozen forms allow "annotated tag or signed commit made by the registrant personally".
Here that means a typed signature equal to the full name, plus the annotated-tag anchor. This is not
cryptographic identity proof. That a real, distinct natural person made the record rests on the
registrant's attestation and custody, which no code can establish. Offline; no network; no entropy.
"""
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
A1_REL = "experiments/programme-a/a1"
HUMANS_REL = A1_REL + "/registrations/humans"
sys.path.insert(0, str(HERE.parent))
import validate_a1  # noqa: E402  (anchored; pure role_conflicts / gate_status / norm)

SCHEMA = "firstcall.programmeA.a1_human_registration.v1"
PRE_REVEAL_COMMIT = "a436bf5d4bc5b4f8dfed8a80fdf8a557eb398e00"
PRE_REVEAL_TAG = "programme-a-freeze-1.2.1-pre-reveal"
ORIGIN_REF = "refs/remotes/origin/v0.2-real-agent"
FORMS = {"R03": "R03-entropy-custodian.form.json", "R04": "R04-entropy-witness.form.json",
         "R05": "R05-R06-adjudicator.form.json", "R06": "R05-R06-adjudicator.form.json"}
FILENAME = re.compile(r"^(R0[3-6])-registration\.json$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
INDEPENDENCE = "I confirm that every statement in attestations_all_required_true is true for me."
# Heuristic, fail-closed screen. The binding safeguard is kind == "human" plus the personal attestation.
NON_HUMAN = re.compile(r"\b(claude|anthropic|openai|chatgpt|gpt(-?\d[\w.]*)?|codex|gemini|copilot|llama|"
                       r"mistral|bard|bot|assistant|agent|model|llm)\b|\[bot\]|noreply@anthropic\.com", re.I)
ENVELOPE = {"schema", "form", "id", "role", "kind", "status", "full_name", "signature", "independence_attestation",
            "controlling_protocol", "fields", "attestations_all_required_true", "attestations_confirmed",
            "required_before"}
OPTIONAL = {"supplementary_statements"}
# The frozen form leaves every disclosure null and untyped. Only this one may truthfully be uncertain:
# Freeze 1.1 disclaims pristine ignorance of rejected names. Exact string only; other disclosures stay boolean.
UNSURE_ALLOWED = frozenset({"saw_quarantined_drafts_or_rejected_names"})


class Invalid(Exception):
    pass


def _git(root, *args, check=True):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if check and p.returncode:
        raise Invalid("git " + " ".join(args[:2]) + " failed")
    return p


def _strict_json(data):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise Invalid("duplicate JSON key " + repr(k))
            out[k] = v
        return out

    def constant(name):
        raise Invalid("non-finite JSON number")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Invalid("malformed JSON: " + type(exc).__name__) from None


def _utc(value, what):
    if not isinstance(value, str) or not UTC.fullmatch(value):
        raise Invalid(what + ": UTC timestamp YYYY-MM-DDTHH:MM:SSZ required")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise Invalid(what + ": impossible date") from None


def _text(value, what):
    if not isinstance(value, str) or not value.strip() or value != value.strip() \
            or unicodedata.normalize("NFC", value) != value or any(unicodedata.category(c)[0] == "C" for c in value):
        raise Invalid(what + ": nonempty trimmed NFC text without control characters required")
    return value


def _designated(roles_doc):
    """Normalised holders of the designated human roles R01/R02 (frozen roles.json)."""
    return {r["id"]: validate_a1.norm(r["holder"]).split(" (")[0]
            for r in roles_doc["roles"] if r["id"] in ("R01", "R02") and r.get("holder")}


def check_record(doc, form, roles_doc, controlling):
    """Content validation against the frozen form. Returns the role. Raises Invalid."""
    if not isinstance(doc, dict):
        raise Invalid("record must be a JSON object")
    keys = set(doc)
    adjudicator = "disclosures_required" in form
    required = ENVELOPE | ({"disclosures_required"} if adjudicator else set())
    if not required <= keys or not keys <= required | OPTIONAL:
        raise Invalid(f"envelope keys: missing {sorted(required - keys)} unexpected {sorted(keys - required - OPTIONAL)}")
    if doc["schema"] != SCHEMA:
        raise Invalid("wrong schema")
    if doc["form"] != form["form"]:
        raise Invalid("record is not for this frozen form")
    role = doc["role"]
    allowed = ("R05", "R06") if adjudicator else (form["form"].split("(")[-1].split(")")[0],)
    if role not in allowed:
        raise Invalid(f"role {role!r} not permitted by form")
    if doc["kind"] != "human" or doc["status"] != "FILLED":
        raise Invalid("kind must be 'human' and status 'FILLED'")
    if not isinstance(doc["id"], str) or not ID.fullmatch(doc["id"]):
        raise Invalid("invalid id")
    name = _text(doc["full_name"], "full_name")
    if "(" in name or len(validate_a1.norm(name)) < 2:
        raise Invalid("full_name must be a plain personal name")
    for value in (name, doc["id"], doc.get("fields", {}).get("public_contact") or ""):
        if NON_HUMAN.search(str(value)):
            raise Invalid("AI/model/tool identity cannot register as a human")
    if validate_a1.norm(_text(doc["signature"], "signature")) != validate_a1.norm(name):
        raise Invalid("typed signature must equal full_name")
    if doc["independence_attestation"] != INDEPENDENCE:
        raise Invalid("independence attestation text differs")
    if doc["controlling_protocol"] != controlling:
        raise Invalid("controlling protocol version differs")
    fields = doc["fields"]
    if not isinstance(fields, dict) or set(fields) != set(form["fields"]):
        raise Invalid("fields must match the frozen form exactly")
    for k, v in fields.items():
        if k == "slot":
            if v != role:
                raise Invalid("fields.slot differs from role")
        elif k == "signature_method":
            if v != form["fields"][k]:
                raise Invalid("signature_method differs from form")
        elif k == "registered_utc":
            _utc(v, "fields.registered_utc")
        else:
            _text(v, "fields." + k)
    if fields["full_name"] != name or fields["signature"] != doc["signature"]:
        raise Invalid("fields.full_name/signature differ from record")
    if doc["attestations_all_required_true"] != form["attestations_all_required_true"]:
        raise Invalid("attestations differ from the frozen form")
    if doc["attestations_confirmed"] is not True:
        raise Invalid("attestations not confirmed")
    if doc["required_before"] != form["required_before"]:
        raise Invalid("required_before differs from form")
    if "supplementary_statements" in doc:
        s = doc["supplementary_statements"]
        if not isinstance(s, list) or not s:
            raise Invalid("supplementary_statements must be a nonempty list")
        for x in s:
            _text(x, "supplementary_statements")
    if adjudicator:
        d = doc["disclosures_required"]
        if not isinstance(d, dict) or set(d) != set(form["disclosures_required"]):
            raise Invalid("disclosures must match the frozen form exactly")
        for k, v in d.items():
            if k == "other_conflicts":
                if not isinstance(v, list):
                    raise Invalid("other_conflicts must be a list")
                for x in v:
                    _text(x, "other_conflicts")
            elif k in UNSURE_ALLOWED and v == "UNSURE":
                continue
            elif type(v) is not bool:
                raise Invalid(f"disclosure {k} must be answered true or false"
                              + (' or "UNSURE"' if k in UNSURE_ALLOWED else ""))
        held = [rid for rid, holder in _designated(roles_doc).items() if holder == validate_a1.norm(name)]
        if held:
            text = " ".join(d["other_conflicts"])
            if not (d["is_protocol_author"] and d["is_capture_or_snapshot_custodian"]) or \
                    any(rid not in text for rid in held):
                raise Invalid(f"holder of {held} must disclose protocol authorship, snapshot custody and {held}")
    return role


def _commit_time(root, commit):
    return datetime.fromtimestamp(int(_git(root, "show", "-s", "--format=%ct", commit).stdout), timezone.utc)


def _ancestor(root, a, b):
    return _git(root, "merge-base", "--is-ancestor", a, b, check=False).returncode == 0


def check_anchor(root, rel, data, doc, controlling, origin_ref):
    """Append-only git anchoring. Returns evidence. Raises Invalid."""
    touching = _git(root, "log", "--all", "--format=%H", "--", rel).stdout.decode().split()
    if not touching:
        raise Invalid("not committed: a working-tree file is not a registration")
    if len(touching) != 1:
        raise Invalid("overwrite/replacement: path touched by more than one commit")
    commit = touching[0]
    added = _git(root, "log", "--all", "--diff-filter=A", "--format=%H", "--", rel).stdout.decode().split()
    if added != [commit]:
        raise Invalid("record path was not added exactly once")
    if _git(root, "show", f"{commit}:{rel}").stdout != data:
        raise Invalid("working-tree bytes differ from the anchored record")
    if _git(root, "rev-parse", controlling["tag"] + "^{commit}", check=False).stdout.decode().strip() != controlling["commit"]:
        raise Invalid("controlling tag does not resolve to the controlling commit")
    if not _ancestor(root, controlling["commit"], commit):
        raise Invalid("record not committed on top of the controlling protocol commit")
    if _git(root, "rev-parse", "--verify", "--quiet", origin_ref, check=False).returncode:
        raise Invalid("origin branch ref missing")
    if not _ancestor(root, commit, origin_ref):
        raise Invalid("record commit is not on the origin branch")
    registered = _utc(doc["fields"]["registered_utc"], "fields.registered_utc")
    if registered > _commit_time(root, commit) or registered < _commit_time(root, controlling["commit"]):
        raise Invalid("registered_utc outside [controlling commit, record commit]")
    ident = _git(root, "show", "-s", "--format=%an <%ae>%n%cn <%ce>%n%B", commit).stdout.decode("utf-8", "replace")
    if NON_HUMAN.search(ident):
        raise Invalid("record commit shows AI/model/tool authorship")
    tags = []
    for line in _git(root, "for-each-ref", "--format=%(objecttype) %(refname:short)", "refs/tags").stdout.decode().splitlines():
        kind, name = line.split(" ", 1)
        if kind != "tag":
            continue  # lightweight tags are not anchors
        peeled = _git(root, "rev-parse", name + "^{commit}").stdout.decode().strip()
        if _ancestor(root, commit, peeled) and _ancestor(root, peeled, origin_ref) and \
                _git(root, "show", f"{peeled}:{rel}", check=False).stdout == data:
            tagger = _git(root, "for-each-ref", "--format=%(taggername) <%(taggeremail)>%0a%(contents)",
                          "refs/tags/" + name).stdout.decode("utf-8", "replace")
            if NON_HUMAN.search(tagger):
                raise Invalid("anchoring tag shows AI/model/tool authorship")
            tags.append({"tag": name, "peeled": peeled})
    if not tags:
        raise Invalid("no annotated tag on origin anchors this record")
    return {"commit": commit, "anchors": sorted(tags, key=lambda t: t["tag"])}


def validate_humans(root=ROOT, *, controlling=None, origin_ref=ORIGIN_REF):
    root = Path(root)
    controlling = controlling or {"commit": PRE_REVEAL_COMMIT, "tag": PRE_REVEAL_TAG}
    roles_doc = json.loads((root / A1_REL / "roles.json").read_bytes())
    forms = {r: json.loads((root / A1_REL / "registrations/forms" / f).read_bytes()) for r, f in FORMS.items()}
    errors, records, humans = [], {}, root / HUMANS_REL
    present = []
    if humans.is_symlink() or (humans.exists() and not humans.is_dir()):
        errors.append("humans: must be a real directory")
    elif humans.is_dir():
        for p in sorted(humans.iterdir()):
            rel = f"{HUMANS_REL}/{p.name}"
            if p.is_symlink() or not p.is_file() or not FILENAME.fullmatch(p.name):
                errors.append(f"{rel}: unexpected entry (only regular R03-R06 registration files)")
                continue
            present.append(rel)
            try:
                data = p.read_bytes()
                doc = _strict_json(data)
                if not isinstance(doc, dict) or doc.get("role") not in FORMS:
                    raise Invalid("record role must be one of R03-R06")
                role = check_record(doc, forms[doc["role"]], roles_doc, controlling)
                if FILENAME.fullmatch(p.name).group(1) != role:
                    raise Invalid("filename disagrees with the record's role")
                evidence = check_anchor(root, rel, data, doc, controlling, origin_ref)
            except Invalid as exc:
                errors.append(f"{rel}: {exc}")
                continue
            if role in records:
                errors.append(f"{rel}: duplicate registration for {role}")
                continue
            records[role] = {"id": doc["id"], "name": doc["full_name"], "contact": doc["fields"]["public_contact"],
                             "path": rel, **evidence}
    # Every record ever added must still be present (append-only; no deletion).
    ever = set(_git(root, "log", "--all", "--diff-filter=A", "--name-only", "--format=", "--", HUMANS_REL).stdout.decode().split())
    for rel in sorted(ever - set(present)):
        errors.append(f"{rel}: anchored registration removed or renamed")
    ids = [r["id"] for r in records.values()]
    if len(ids) != len(set(ids)):
        errors.append("duplicate registration id")
    contacts = {}
    for role, r in records.items():
        contacts.setdefault(r["contact"].casefold(), set()).add(validate_a1.norm(r["name"]))
    if any(len(names) > 1 for names in contacts.values()):
        errors.append("one contact used by differently named registrants")
    overlay = json.loads(json.dumps(roles_doc))
    for r in overlay["roles"]:
        if r["id"] in records:
            r["status"], r["holder"] = "FILLED", records[r["id"]]["name"]
    errors += validate_a1.role_conflicts(overlay)   # frozen conflict pairs, including R01/R02 holder
    if errors:                                      # fail closed: nothing is registered
        records, overlay = {}, json.loads(json.dumps(roles_doc))
    return {"schema": "firstcall.programmeA.a1_human_registrations_validation.v1",
            "decision": "HUMAN_RECORDS_INVALID" if errors else "HUMAN_RECORDS_VALID",
            "errors": errors,
            "roles": {rid: ("REGISTERED" if rid in records else "UNFILLED") for rid in ("R03", "R04", "R05", "R06")},
            "records": records,
            "gates": validate_a1.gate_status(overlay, validate_a1.anchored(root)),
            "not_covered": "R16 approvals, R08 attestations, sealing intake, gate-crossing chronology: remain as recorded"}


PRE_REVEAL_HUMANS_ERROR = "unexpected human registration records present"


def combine(pre_reveal, humans):
    """The frozen 1.2.1 pre-reveal validator flags any humans/ record by design. Forgive exactly that
    error, and only when every human record verified. All other pre-reveal checks stay binding."""
    kept = [e for e in pre_reveal["errors"]
            if not (e.startswith(PRE_REVEAL_HUMANS_ERROR) and humans["decision"] == "HUMAN_RECORDS_VALID")]
    return {"pre_reveal_errors": kept, "human_errors": humans["errors"], "humans": humans,
            "pass": not kept and not humans["errors"]}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--with-pre-reveal", action="store_true",
                    help="also run the frozen Freeze-1.2.1 pre-reveal validator (slow; clean-clone Freeze-1.1 tests)")
    args = ap.parse_args(argv)
    report = validate_humans()
    if args.with_pre_reveal:
        import validate_registrations
        report = combine(validate_registrations.validate(), report)
        ok = report["pass"]
    else:
        ok = not report["errors"]
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
