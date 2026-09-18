#!/usr/bin/env python3
"""Validate/apply the proposed protocol overlay. No frame, draw, network or writes.

Default: print validation summary. --emit: canonical effective protocol to stdout.
This is protocol composition, not executable sampling apparatus.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = "experiments/programme-a/"
HERE = BASE + "amendments/"
PARENT = "13ff44c37a96882553ffb9103a5596787555e0f3"
TAG = "programme-a-freeze-1-protocol"
PARENT_NAMES = (
    "README.md", "analysis-plan.json", "estimand.schema.json", "journey-standard.json",
    "outcome-taxonomy.json", "prereg-freeze-sequence.json", "receipt.v1.schema.json",
    "run-design.config.json", "sample-frame.config.json",
)
PARENT_PATHS = {BASE + p for p in PARENT_NAMES} | {"docs/programme-a-measurement-protocol.md"}
PATCH_TARGETS = {BASE + p for p in (
    "sample-frame.config.json", "estimand.schema.json", "analysis-plan.json",
    "prereg-freeze-sequence.json",
)}
QUARANTINE = BASE + "quarantine/INVALID_PRE_FREEZE_2_DRAFT/"
HELPERS = {
    "firstcall/cf001_baseline_b08.py", "firstcall/cf001_baseline_recovery.py",
    "firstcall/cf001_baseline_valid.py", "firstcall/cf001_p01_replay.py",
    "firstcall/cf001_p01_replay_finish.py",
}
NEW_PATHS = {
    "docs/programme-a-freeze-1.1-amendment.md",
    HERE + "freeze-1.1.json", HERE + "entry-integrity.json",
    HERE + "apply_protocol.py", HERE + "test_protocol.py",
    HERE + "hostile-review.md", HERE + "validation-report.json",
    QUARANTINE + "README.md", QUARANTINE + "provenance.json",
    QUARANTINE + "build_frame.py.txt",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads(data):
    def invalid_constant(value):
        raise ValueError(f"non-JSON numeric constant: {value}")
    return json.loads(data, object_pairs_hook=_unique, parse_constant=invalid_constant)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def apply_patches(original, operations):
    """Strict test/replace/add subset; replacements require adjacent old-value tests."""
    result = copy.deepcopy(original)
    prior = None
    for op in operations:
        require(set(op) == {"op", "path", "value"}, "bad patch fields")
        path = op["path"]
        require(path.startswith("/") and path != "/", "invalid pointer")
        tokens = [s.replace("~1", "/").replace("~0", "~") for s in path[1:].split("/")]
        node = result
        for token in tokens[:-1]:
            node = node[int(token)] if isinstance(node, list) else node[token]
        key = int(tokens[-1]) if isinstance(node, list) else tokens[-1]
        kind = op["op"]
        if kind == "test":
            require(canonical(node[key]) == canonical(op["value"]), f"patch test failed: {path}")
        elif kind == "replace":
            require(prior is not None and prior["op"] == "test" and prior["path"] == path,
                    f"unguarded replacement: {path}")
            node[key] = copy.deepcopy(op["value"])
        elif kind == "add":
            require(isinstance(node, dict) and key not in node, f"add would overwrite: {path}")
            node[key] = copy.deepcopy(op["value"])
        else:
            raise ValueError(f"unsupported patch operation: {kind}")
        prior = op
    return result


def validate_rules(a):
    require(a["status"] == "PROPOSED_NOT_FROZEN", "must remain an unsealed proposal")
    require(a["parent_commit"] == PARENT and a["parent_tag"] == TAG, "wrong parent")
    require(set(a["parent_file_sha256"]) == PARENT_PATHS, "incomplete parent manifest")
    require(set(a["json_patches"]) == PATCH_TARGETS, "unexpected patch scope")
    require(a["unrelated_freeze_1_provisions_unchanged"] is True, "unbounded scope")
    for counter in ("real_vendor_runs", "selected_vendors", "outcome_observations"):
        require(type(a[counter]) is int and a[counter] == 0, f"nonzero/noninteger {counter}")
    r = a["rules"]
    require([c["id"] for c in r["categories"]] == [f"C{i:02}" for i in range(1, 8)], "category IDs")
    require(len({c["label"] for c in r["categories"]}) == 7, "duplicate category labels")
    require(r["category_assignment"]["input"] ==
            ["FIRSTCALL-A-1.1-STRATUM", "canonical_id", "category_id"], "mutable category hash")
    for key in ("depends_on_category_counts", "depends_on_display_names", "random_seed_used", "overrides_or_rerolls"):
        require(r["category_assignment"][key] is False, f"category discretion: {key}")
    require(r["category_assignment"]["ledger_sealed_before_scoring"] is True
            and r["category_assignment"]["adjudicators_blind_to_scores"] is True,
            "category scores exposed before ledger lock")
    require(r["sampling_unit"]["identity_unresolved"] == "BLOCK_ENTIRE_FRAME", "identity leakage")
    e = r["eligibility"]
    require(e["terminal_states"] == ["ELIGIBLE", "EXCLUDED", "UNRESOLVED_ELIGIBILITY"], "terminal states")
    require(e["conservation"] == "TOTAL_CANONICAL_UNITS = ELIGIBLE + EXCLUDED + UNRESOLVED_ELIGIBILITY",
            "bad conservation")
    require(e["unresolved_draw"] is False and e["unresolved_reserve"] is False, "unresolved promotion")
    require("E5" not in e["exclusion_codes"], "duplicate aliases counted as units")
    s = r["source_universe"]
    require(s["actual_sources"] == [] and s["source_selection_status"] == "NOT_STARTED", "sources already chosen")
    require(s["take"] == "ALL_QUALIFYING_UPSTREAM_ENUMERATIONS", "source cherry-picking")
    require(s["min_independent_maintainers"] == 2 and s["organic_positions"] == [1, 20], "source bounds")
    require(len(s["queries"]) == 4 and len(set(s["queries"])) == 4, "source discovery queries")
    for flag in ("snowballing", "query_edits", "candidate_content_screening_for_source_choice", "popularity_truncation"):
        require(s[flag] is False, f"source discretion: {flag}")
    d = r["documentary_adjudication"]
    for key, value in {"capture_window_calendar_days": 7, "max_pages_per_unit": 16,
                       "max_link_depth": 2, "max_page_bytes": 2097152,
                       "request_timeout_seconds": 30, "retries_per_page": 1,
                       "retry_wait_seconds": 30, "redirect_limit": 3, "adjudicators": 2,
                       "max_review_minutes_per_unit_per_adjudicator": 60,
                       "max_source_review_minutes_per_adjudicator": 20}.items():
        require(type(d[key]) is int and d[key] == value, f"search-budget mismatch: {key}")
    require(d["disagreement"] == "UNRESOLVED" and d["extra_search_on_disagreement"] is False,
            "discretionary disagreement handling")
    require(d["post_lock_upgrades"] is False, "post-lock eligibility changes")
    p = r["prior_firstcall"]
    require(p["provenance_commit"] == PARENT, "moving provenance cutoff")
    require(p["explicit_parent_exclusions"] == ["Postmark", "Resend", "CF-001/Acme", "MULTI-002 Stripe"],
            "changed parent named exclusions")
    require(all(p[k] is False for k in ("outcome_lookup", "known_outcome_condition", "stripe_reentry_exception")),
            "prior-outcome leakage")
    require(r["allocation"]["N"] == 24 and r["allocation"]["modify_strata_sources_or_N_on_failure"] is False,
            "allocation discretion")
    draw = r["later_draw"]
    require(draw["status"] == "NOT_PERFORMED" and draw["seed_value"] is None,
            "draw or seed already exists")
    require(draw["selected_vendor_ids"] == [] and draw["replacement_order"] == [], "selection artifacts")
    require(draw["tape_bytes_per_unit"] == 32, "random priority width")
    require(r["replacement"]["within_same_stratum"] is True and r["replacement"]["outcome_based"] is False,
            "replacement manipulation")
    require(r["replacement"]["census_unresolved"] == "BLOCK_EXECUTION", "unknown census silently excluded")
    require(r["sampling_unit"]["anchor_difference_proves_distinct"] is False,
            "URL-based identity split")
    require("FIRSTCALL-A-1.1-ID" in r["sampling_unit"]["canonical_id"], "identity domain missing")
    require(r["category_assignment"]["probability_claim"].startswith("deterministic 0/1"),
            "unsupported random-category claim")
    require(r["category_assignment"]["malformed_or_duplicate_ids"] == "REJECT_NOT_DEDUPLICATE",
            "malformed IDs silently accepted")
    capture = s["capture"]
    require(capture["attempts"] == 1 and capture["researchers_use_same_archived_bytes"] is True,
            "alternative source capture")
    require(capture["query_offsets_seconds"] == [0, 60, 120, 180]
            and capture["maximum_start_lateness_seconds"] == 5, "capture timing discretion")
    require(p["code_paths_alone_qualify"] is False and p["fuzzy_name_matching"] is False,
            "path/name-based prior exclusion")
    grammar = p["positive_grammar"]
    require(grammar["json_experiment_keys"] == ["experiment", "experiment_id"]
            and grammar["json_identity_keys"] == ["vendor", "vendor_id", "target_vendor", "target_vendor_id"],
            "designation grammar discretion")
    require(grammar["unrecognized_layout"].startswith("UNRECOGNIZED_DESIGNATION => BLOCK_REGISTRY"),
            "unrecognized designation silently ignored")
    require(draw["repeat_invocation"] == "ABORT_COHORT_NO_REROLL"
            and draw["priority_access_before_census_seal"] == "CUSTODIAN_ONLY", "entropy custody failure")
    require(r["replacement"]["reveal_after_census_seal"] is True
            and r["replacement"]["repeat_eligibility_adjudication"] is False,
            "census may depend on revealed priorities")
    sequence = r["sequence"]
    stages = ["FREEZE_2A_FRAME_METHOD_SAP_SEAL", "FREEZE_2B_ENTROPY_COMMITMENT",
              "FREEZE_3_CUSTODIAL_BLIND_DRAW", "FREEZE_4_ALL_FRAME_APPARATUS_AND_GATE_SEAL",
              "FREEZE_5A_BLINDED_CENSUS_SEAL", "FREEZE_5B_REVEAL_VERIFY_MECHANICAL_REPLACEMENT",
              "EXECUTION"]
    require(len(sequence) == len(set(sequence)), "duplicate chronology stage")
    require(all(stage in sequence for stage in stages), "missing chronology stage")
    require([sequence.index(stage) for stage in stages] == sorted(sequence.index(stage) for stage in stages),
            "contradictory freeze order")
    analysis = r["analysis_consequence"]
    interval = analysis["primary_interval"]
    require(interval["method"] == "conservative two-stage bounded-cluster population band"
            and interval["alpha"] == 0.05 and interval["epsilon"] == "sqrt(C*ln(40))",
            "invalid primary confidence rule")
    require(analysis["support_changed_explicitly"] is True and "conditional" in analysis["parameter"],
            "silent estimand change")
    require(analysis["bootstrap"].startswith("SECONDARY_DESCRIPTIVE_ONLY"),
            "bootstrap promoted to guaranteed population CI")
    require(analysis["bootstrap_parameters"]["seed_value"] is None, "bootstrap seed already generated")


def compose(a, originals):
    validate_rules(a)
    result = copy.deepcopy(originals)
    for name, ops in a["json_patches"].items():
        result[name] = apply_patches(originals[name], ops)
    require(result[BASE + "sample-frame.config.json"]["freeze_1_1_rules"] == a["rules"],
            "embedded rules diverge from normative rules")
    sample = result[BASE + "sample-frame.config.json"]
    require(sample["frozen_snapshot"] == a["rules"]["source_universe"], "source overlay divergence")
    require(sample["replacements"] == a["rules"]["replacement"], "replacement overlay divergence")
    for name in ("estimand.schema.json", "analysis-plan.json"):
        require(result[BASE + name]["freeze_1_1_sampling_consequence"] == a["rules"]["analysis_consequence"],
                "analysis overlay divergence")
    sequence = result[BASE + "prereg-freeze-sequence.json"]
    require(sequence["freeze_1_1_sequence"] == a["rules"]["sequence"], "sequence overlay divergence")
    require([str(x["freeze"]) for x in sequence["freeze_sequence"]] ==
            ["1", "1.1", "2A", "2B", "3", "4", "5A", "5B"], "legacy reveal/census order remains")
    require(result[BASE + "analysis-plan.json"]["primary"]["interval"] ==
            a["rules"]["analysis_consequence"]["primary_interval"], "primary interval overlay divergence")
    require(result[BASE + "sample-frame.config.json"]["inclusion_rules"][4].startswith("not FIRSTCALL"),
            "prior-exclusion polarity reversed")
    for name in ("journey-standard.json", "outcome-taxonomy.json", "run-design.config.json", "receipt.v1.schema.json"):
        require(result[BASE + name] == originals[BASE + name], f"unrelated protocol modified: {name}")
    return result


def verify_repository(a):
    require(git("rev-parse", TAG + "^{commit}").decode().strip() == PARENT, "tag no longer matches parent")
    originals = {}
    for name, expected in a["parent_file_sha256"].items():
        frozen = git("show", f"{PARENT}:{name}")
        require(digest(frozen) == expected, f"parent hash mismatch: {name}")
        require((ROOT / name).read_bytes() == frozen, f"frozen file modified: {name}")
        if name.endswith(".json"):
            originals[name] = loads(frozen)
            require(originals[name]["real_vendor_runs"] == 0, "parent run counter")
    baseline = loads((ROOT / HERE / "entry-integrity.json").read_bytes())
    require(baseline["parent_commit"] == PARENT and baseline["captured_before_amendment_writes"] is True,
            "entry baseline provenance")
    q = loads((ROOT / a["quarantine_manifest"]).read_bytes())
    require(q["sha256"] == "a3e3af7045424c59b559ba34c4e7143ebfa00821bca9efc3284a85627846302b",
            "inherited draft identity changed")
    require(not (ROOT / q["original_path"]).exists(), "invalid builder still active")
    qpath = ROOT / q["preserved_path"]
    require(qpath.suffix == ".txt" and qpath.stat().st_mode & 0o111 == 0, "quarantine executable")
    require(digest(qpath.read_bytes()) == q["sha256"], "quarantine bytes changed")
    tracked = set(git("ls-files", "-z").decode().rstrip("\0").split("\0"))
    protected = {p for p in tracked if any(t in p.lower() for t in ("multi001", "multi002", "multi-001", "multi-002"))}
    require(PARENT_PATHS | protected | HELPERS <= set(baseline["sha256"]), "entry manifest omissions")
    for name, expected in baseline["sha256"].items():
        path = qpath if name == q["original_path"] else ROOT / name
        require(digest(path.read_bytes()) == expected, f"entry bytes changed: {name}")
        if name in protected:
            require(path.read_bytes() == git("show", f"{PARENT}:{name}"), f"historical file differs from parent: {name}")
    actual = {str(p.relative_to(ROOT)) for p in (ROOT / BASE).rglob("*") if p.is_file()}
    require(actual <= PARENT_PATHS | NEW_PATHS, f"unexpected Programme A artifacts: {actual - PARENT_PATHS - NEW_PATHS}")
    artifacts = ROOT / "artifacts/programme-a"
    require(not artifacts.exists() or not any(artifacts.rglob("*")), "Programme A run artifacts exist")
    untracked = set(filter(None, git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0")))
    require(untracked <= NEW_PATHS | HELPERS, f"unexpected untracked artifact: {untracked - NEW_PATHS - HELPERS}")
    changed = set(filter(None, git("diff", "--name-only", PARENT, "--").decode().splitlines()))
    require(changed <= NEW_PATHS, f"unrelated tracked changes from parent: {changed - NEW_PATHS}")
    git("diff", "--check")
    return originals, len(protected), len(actual)


def validate():
    a = loads((ROOT / HERE / "freeze-1.1.json").read_bytes())
    validate_rules(a)
    text = (ROOT / a["amendment_document"]).read_bytes()
    require(digest(text) == a["amendment_document_sha256"], "amendment text hash mismatch")
    originals, historical_count, file_count = verify_repository(a)
    effective = compose(a, originals)
    bundle = {
        "schema": "firstcall.programmeA.effective_protocol.v1_1.proposed",
        "status": "PROPOSED_NOT_FROZEN_NOT_A_FRAME",
        "parent_commit": PARENT, "parent_tag": TAG,
        "parent_protocol_text": (ROOT / "docs/programme-a-measurement-protocol.md").read_text(),
        "amendment_text": text.decode(), "amendment": a,
        "effective_json_documents": effective,
        "precedence": a["text_precedence"],
    }
    report = {
        "schema": "firstcall.programmeA.amendment_validation.v1",
        "status": "PASS_PROPOSAL_ONLY_NOT_FREEZE_2",
        "final_adversarial_review": "SEALABLE_PROSPECTIVE_RULES_WITH_EXPLICIT_ASSUMPTIONS_AND_STOP_GATES",
        "effective_protocol_sha256": digest(canonical(bundle)),
        "applicator_sha256": digest(Path(__file__).read_bytes()),
        "amendment_json_sha256": digest((ROOT / HERE / "freeze-1.1.json").read_bytes()),
        "amendment_document_sha256": digest(text),
        "entry_integrity_manifest_sha256": digest((ROOT / HERE / "entry-integrity.json").read_bytes()),
        "parent_files_byte_identical": len(PARENT_PATHS),
        "multi_001_002_files_byte_identical": historical_count,
        "historical_helpers_byte_identical": len(HELPERS),
        "quarantined_builder_byte_identical": True,
        "programme_a_file_inventory_count_at_validation": file_count,
        "selected_vendors": 0, "random_draw_performed": False,
        "random_seed_generated": False, "outcome_observations": 0, "real_vendor_runs": 0,
        "unrelated_parent_json_documents_unchanged": 4,
        "git_diff_check": "PASS",
        "limits": "Protocol and repository checks, not source feasibility, a constructed frame, or executed sampling. No claim of no prior exposure to rejected vendor names.",
    }
    return bundle, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit", action="store_true", help="emit canonical effective protocol JSON to stdout")
    args = parser.parse_args()
    bundle, report = validate()
    print(canonical(bundle).decode() if args.emit else json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
