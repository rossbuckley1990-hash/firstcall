#!/usr/bin/env python3
"""FIRSTCALL Programme A prior-FIRSTCALL provenance projector (Freeze 1.2 registration).

Implements the Freeze-1.1 §5/§8.4 provenance-only designation projection mechanically.
It reads git blobs at the provenance cutoff commit and emits ONLY:
  * the full tracked path inventory with blob hashes and a projection class;
  * for JSON configuration/manifests: experiment id + the four identity keys + explicit
    firstcall_authored / firstcall_operated flags at the same object level, plus the
    sorted key-name skeleton (names only, never values) for reviewer plausibility checks;
  * for Markdown: `Experiment:` metadata values and Target/Targets/Experimental target(s)
    sections' `Vendor:` / `Target vendor:` lines or Vendor / Target vendor table columns;
  * for code: the path only, plus literal references from qualifying records.
Result/receipt/trace/outcome/retrospective/forensic/audit/diagnosis/evidence contexts are
classified by fixed path tokens and never parsed. No code is executed. Output is a DRAFT
that requires both registered adjudicators; any UNRECOGNIZED_DESIGNATION blocks it.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECTOR_VERSION = "1.2.1"
PROVENANCE_CUTOFF_COMMIT = "13ff44c37a96882553ffb9103a5596787555e0f3"
SCOPE_PREFIXES = ("docs/", "experiments/", "firstcall/")
IDENTITY_KEYS = ("vendor", "vendor_id", "target_vendor", "target_vendor_id")
EXPERIMENT_KEYS = ("experiment", "experiment_id")
AUTHORSHIP_KEYS = ("firstcall_authored", "firstcall_operated")
# Fixed result/evidence-context tokens (matched against lower-cased path segments' text).
RESULT_CONTEXT_TOKENS = (
    "receipt", "trace", "outcome", "result", "retrospective", "forensic", "transcript",
    "summary", "diagnos", "invalidation", "audit", "evidence", "web-extracts", "eligibility",
    "history-hashes",
)
CODE_SUFFIXES = (".py", ".sh", ".js", ".ts")
PLAUSIBILITY_KEY_RE = re.compile(r"vendor|target|provider", re.I)
MD_SECTION_LABEL_RE = re.compile(r"^(?:\d+(?:\.\d+)*\.?\s+)?(.*?)\s*$")
TARGET_HEADINGS = {"target", "targets", "experimental target", "experimental targets",
                   "experimental target(s)"}
MD_EXPERIMENT_RE = re.compile(r"^\s*experiment:\s*(\S.*?)\s*$", re.I)
MD_IDENTITY_LINE_RE = re.compile(r"^\s*(vendor|target vendor):\s*(\S.*?)\s*$", re.I)
MD_AUTHOR_RE = re.compile(r"^\s*(firstcall_authored|firstcall_operated):\s*true\s*$", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
# Path segments marking example/fixture material. A designation-shaped record there is
# neither admitted nor ignored: it is UNRECOGNIZED and blocks the registry.
EXAMPLE_SEGMENT_RE = re.compile(r"(^|[/_.-])(examples?|samples?|fixtures?|templates?|demos?)([/_.-]|$)", re.I)
NAMED_MANDATORY_EXCLUSIONS = (
    "Postmark", "Resend", "CF-001/Acme local fixtures", "MULTI-002 Stripe target",
)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def inventory(repo, commit):
    out = git(repo, "ls-tree", "-r", "-z", "--full-tree", commit).decode("utf-8")
    rows = []
    for entry in filter(None, out.split("\0")):
        meta, path = entry.split("\t", 1)
        mode, kind, obj = meta.split()
        if kind == "blob":
            rows.append((path, obj))
    rows.sort(key=lambda r: r[0].encode("utf-8"))
    return rows


def classify(path):
    if not path.startswith(SCOPE_PREFIXES):
        return "OUT_OF_PROJECTION_SCOPE_S8_4", None
    low = path.lower()
    if low.endswith(CODE_SUFFIXES):
        return "CODE_PATH_ONLY", None
    for token in RESULT_CONTEXT_TOKENS:
        if token in low:
            return "EXCLUDED_RESULT_OR_EVIDENCE_CONTEXT", token
    if low.endswith(".json"):
        return "JSON_PROJECTED", None
    if low.endswith(".md"):
        return "MARKDOWN_PROJECTED", None
    return "FORMAT_OUTSIDE_S8_4_GRAMMAR", None


def _nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


def _identity_capable(value):
    """Structural rule: only strings, non-boolean numbers, arrays or objects can carry an
    identity. Booleans and null (policy flags) cannot name a vendor."""
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return isinstance(value, (int, float, list, dict))


def project_json(data):
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"positive": [], "unrecognized": [{"pointer": "", "reason": f"UNPARSEABLE_JSON:{type(exc).__name__}"}],
                "key_skeleton": []}
    positive, unrecognized, keys, incidental = [], [], set(), []

    def walk(node, pointer, ancestor_has_experiment):
        if isinstance(node, dict):
            keys.update(node.keys())
            exp_keys = [k for k in EXPERIMENT_KEYS if _nonempty_str(node.get(k))]
            id_keys = [k for k in IDENTITY_KEYS if _nonempty_str(node.get(k))]
            auth = {k: node[k] for k in AUTHORSHIP_KEYS if k in node}
            if exp_keys and id_keys:
                for ik in id_keys:
                    positive.append({"pointer": pointer, "experiment_key": exp_keys[0],
                                     "experiment": node[exp_keys[0]], "identity_key": ik,
                                     "identity": node[ik],
                                     "firstcall_authored": node.get("firstcall_authored") is True,
                                     "firstcall_operated": node.get("firstcall_operated") is True})
            elif exp_keys and any(PLAUSIBILITY_KEY_RE.search(k) and _identity_capable(node[k]) for k in node):
                unrecognized.append({"pointer": pointer, "reason": "EXPERIMENT_OBJECT_WITH_NON_GRAMMAR_TARGET_KEY",
                                     "keys": sorted(k for k in node
                                                    if PLAUSIBILITY_KEY_RE.search(k) and _identity_capable(node[k]))})
            elif id_keys and not exp_keys:
                unrecognized.append({"pointer": pointer, "reason": "IDENTITY_KEY_WITHOUT_SAME_LEVEL_EXPERIMENT",
                                     "keys": id_keys, "ancestor_has_experiment": ancestor_has_experiment})
            if exp_keys:
                incidental.extend({"pointer": pointer, "key": k, "value_type": "null" if node[k] is None else "boolean"}
                                  for k in sorted(node)
                                  if PLAUSIBILITY_KEY_RE.search(k) and not _identity_capable(node[k]))
            if auth and not (exp_keys and id_keys):
                unrecognized.append({"pointer": pointer, "reason": "AUTHORSHIP_FLAG_WITHOUT_DESIGNATION",
                                     "keys": sorted(auth)})
            for k in sorted(node):
                walk(node[k], f"{pointer}/{_esc(k)}", ancestor_has_experiment or bool(exp_keys))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{pointer}/{i}", ancestor_has_experiment)

    walk(doc, "", False)
    return {"positive": positive, "unrecognized": unrecognized, "key_skeleton": sorted(keys),
            "incidental_non_identity_fields": incidental}


def _esc(key):
    return str(key).replace("~", "~0").replace("/", "~1")


def _label(text):
    return MD_SECTION_LABEL_RE.match(text.strip()).group(1).strip().casefold()


def _table_cells(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    return [c.strip() for c in s.strip("|").split("|")]


def project_markdown(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {"experiment_lines": [], "target_sections": [], "unrecognized": [{"reason": "UNDECODABLE_MARKDOWN"}]}
    lines, in_fence = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            lines.append("")
        else:
            lines.append("" if in_fence else line)
    experiments = [m.group(1) for m in (MD_EXPERIMENT_RE.match(l) for l in lines) if m]
    sections, unrecognized = [], []
    i = 0
    while i < len(lines):
        m = HEADING_RE.match(lines[i])
        if not m:
            i += 1
            continue
        level, label = len(m.group(1)), _label(m.group(2))
        mentions_target = re.search(r"\btargets?\b|\btarget\(s\)", label) is not None
        j = i + 1
        while j < len(lines):
            n = HEADING_RE.match(lines[j])
            if n and len(n.group(1)) <= level:
                break
            j += 1
        if label in TARGET_HEADINGS:
            body = lines[i + 1:j]
            ids = [mm.group(2) for mm in (MD_IDENTITY_LINE_RE.match(l) for l in body) if mm]
            authored = sorted({mm.group(1).lower() for mm in (MD_AUTHOR_RE.match(l) for l in body) if mm})
            column_values = []
            k = 0
            while k < len(body):
                header = _table_cells(body[k])
                if header is not None:
                    cols = [idx for idx, c in enumerate(header) if c.casefold() in ("vendor", "target vendor")]
                    k += 1
                    if k < len(body) and _table_cells(body[k]) is not None and set(body[k].replace("|", "").strip()) <= set("-: "):
                        k += 1
                    while k < len(body) and _table_cells(body[k]) is not None:
                        row = _table_cells(body[k])
                        for idx in cols:
                            if idx < len(row) and row[idx]:
                                column_values.append(row[idx])
                        k += 1
                    continue
                k += 1
            section = {"heading": label, "identity_lines": ids, "vendor_column_values": column_values,
                       "authorship_flags": authored}
            sections.append(section)
            if not ids and not column_values:
                unrecognized.append({"reason": "TARGET_HEADING_WITHOUT_GRAMMAR_IDENTITY", "heading": label})
            elif not experiments:
                unrecognized.append({"reason": "TARGET_SECTION_WITHOUT_EXPERIMENT_LINE", "heading": label})
        elif mentions_target:
            unrecognized.append({"reason": "NON_GRAMMAR_TARGET_HEADING", "heading": label})
        i = j if label in TARGET_HEADINGS else i + 1
    if experiments and not sections:
        unrecognized.append({"reason": "EXPERIMENT_LINE_WITHOUT_TARGET_SECTION"})
    return {"experiment_lines": experiments, "target_sections": sections, "unrecognized": unrecognized}


def project(repo, commit=PROVENANCE_CUTOFF_COMMIT):
    rows = inventory(repo, commit)
    ledger, code_paths = [], []
    for path, obj in rows:
        cls, token = classify(path)
        entry = {"path": path, "git_blob": obj, "class": cls}
        if token:
            entry["excluded_by_token"] = token
        if cls in ("JSON_PROJECTED", "MARKDOWN_PROJECTED", "CODE_PATH_ONLY", "FORMAT_OUTSIDE_S8_4_GRAMMAR"):
            data = git(repo, "cat-file", "blob", obj)
            entry["blob_sha256"] = hashlib.sha256(data).hexdigest()
            if cls == "JSON_PROJECTED":
                entry["projection"] = project_json(data)
            elif cls == "MARKDOWN_PROJECTED":
                entry["projection"] = project_markdown(data)
            proj = entry.get("projection")
            if proj and EXAMPLE_SEGMENT_RE.search(path):
                shaped = proj.get("positive") or any(s["identity_lines"] or s["vendor_column_values"]
                                                     for s in proj.get("target_sections", []))
                if shaped:
                    proj["unrecognized"].append({"reason": "DESIGNATION_SHAPE_IN_EXAMPLE_PATH"})
                    proj["positive"] = []
                    for sec in proj.get("target_sections", []):
                        sec["identity_lines"], sec["vendor_column_values"] = [], []
            elif cls == "CODE_PATH_ONLY":
                code_paths.append(path)
            entry["_data"] = data
        ledger.append(entry)
    for entry in ledger:
        data = entry.pop("_data", None)
        proj = entry.get("projection")
        qualifying = proj and (proj.get("positive") or any(s["identity_lines"] or s["vendor_column_values"]
                                                          for s in proj.get("target_sections", [])))
        if qualifying and data is not None:
            entry["literal_code_path_references"] = [p for p in code_paths if p.encode("utf-8") in data]
        entry["reviewer_confirmation_required"] = entry["class"] != "OUT_OF_PROJECTION_SCOPE_S8_4"
    positives = [(e["path"], p) for e in ledger for p in (e.get("projection") or {}).get("positive", [])]
    md_pos = [(e["path"], s) for e in ledger for s in (e.get("projection") or {}).get("target_sections", [])
              if s["identity_lines"] or s["vendor_column_values"]]
    unrecognized = [(e["path"], u) for e in ledger for u in (e.get("projection") or {}).get("unrecognized", [])]
    counts = {}
    for e in ledger:
        counts[e["class"]] = counts.get(e["class"], 0) + 1
    return {
        "schema": "firstcall.programmeA.prior_firstcall_projection.v1",
        "projector_version": PROJECTOR_VERSION,
        "provenance_cutoff_commit": commit,
        "status": "BLOCKED_UNRECOGNIZED_DESIGNATION" if unrecognized else "DRAFT_REQUIRES_TWO_ADJUDICATOR_APPROVAL",
        "named_mandatory_exclusions": list(NAMED_MANDATORY_EXCLUSIONS),
        "class_counts": dict(sorted(counts.items())),
        "path_count": len(ledger),
        "positive_json_designations": [{"path": p, **d} for p, d in positives],
        "positive_markdown_designations": [{"path": p, **s} for p, s in md_pos],
        "unrecognized_designations": [{"path": p, **u} for p, u in unrecognized],
        "ledger": ledger,
        "adjudicator_approvals": {"ADJ-1": None, "ADJ-2": None},
        "identity_mapping_to_canonical_units": "PENDING_IDENTITY_LEDGER",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[3]))
    ap.add_argument("--commit", default=PROVENANCE_CUTOFF_COMMIT)
    ap.add_argument("--summary", action="store_true",
                    help="print class counts and flagged paths only (no key skeletons or ledger)")
    args = ap.parse_args(argv)
    result = project(args.repo, args.commit)
    if args.summary:
        print(json.dumps({"status": result["status"], "path_count": result["path_count"],
                          "class_counts": result["class_counts"],
                          "positive_json_paths": sorted({d["path"] for d in result["positive_json_designations"]}),
                          "positive_markdown_paths": sorted({d["path"] for d in result["positive_markdown_designations"]}),
                          "unrecognized": [{"path": u["path"], "reason": u["reason"]}
                                           for u in result["unrecognized_designations"]]}, indent=2))
    else:
        sys.stdout.buffer.write(canonical(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
