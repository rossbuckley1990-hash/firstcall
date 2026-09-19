#!/usr/bin/env python3
"""Hostile tests for validate_humans. Synthetic people and throwaway git repositories only."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_humans as vh  # noqa: E402

REAL = HERE.parents[3]
ORIGIN = "refs/remotes/origin/main"
BASE_T, REG_T, COMMIT_T = "2026-09-20T00:00:00Z", "2026-09-20T00:30:00Z", "2026-09-20T01:00:00Z"
PEOPLE = {"R03": ("Synthetic Carol Person", "carol@example.invalid"), "R04": ("Synthetic Dan Person", "dan@example.invalid"),
          "R05": ("Synthetic Alice Person", "alice@example.invalid"), "R06": ("Synthetic Bob Person", "bob@example.invalid")}


class Repo:
    def __init__(self, tmp):
        self.root = Path(tmp) / "repo"
        forms = self.root / vh.A1_REL / "registrations/forms"
        forms.mkdir(parents=True)
        shutil.copy(REAL / vh.A1_REL / "roles.json", self.root / vh.A1_REL / "roles.json")
        for f in set(vh.FORMS.values()):
            shutil.copy(REAL / vh.A1_REL / "registrations/forms" / f, forms / f)
        self.git("init", "-q", "-b", "main")
        self.commit("base", BASE_T)
        self.ctl = self.git("rev-parse", "HEAD").strip()
        self.tag("ctl"); self.tag("programme-a-freeze-1.2-a1")
        self.push()
        self.controlling = {"commit": self.ctl, "tag": "ctl"}

    def git(self, *args, when=COMMIT_T, name="Synthetic Fixture", email="fixture@example.invalid"):
        env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when, GIT_AUTHOR_NAME=name,
                   GIT_AUTHOR_EMAIL=email, GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email,
                   GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
        return subprocess.run(["git", "-C", str(self.root), *args], env=env, check=True, capture_output=True,
                              text=True).stdout

    def commit(self, message, when=COMMIT_T, **who):
        self.git("add", "-A", when=when, **who)
        self.git("commit", "-q", "--allow-empty", "-m", message, when=when, **who)

    def tag(self, tagname, annotated=True, **who):
        if annotated:
            self.git("tag", "-a", tagname, "-m", "synthetic anchor " + tagname, **who)
        else:
            self.git("tag", tagname)

    def push(self):
        self.git("update-ref", ORIGIN, "HEAD")

    def write(self, name, data):
        p = self.root / vh.HUMANS_REL / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode())
        return p

    def register(self, doc, filename=None, tag=True, push=True, message="register synthetic human", who=None):
        who = who or {}
        self.write(filename or f"{doc['role']}-registration.json", doc)
        self.commit(message, **who)
        if tag:
            self.tag(f"reg-{doc['role']}-{self.git('rev-parse', '--short', 'HEAD').strip()}", **who)
        if push:
            self.push()

    def validate(self):
        return vh.validate_humans(self.root, controlling=self.controlling, origin_ref=ORIGIN)


def record(role, controlling, name=None, contact=None):
    form = json.loads((REAL / vh.A1_REL / "registrations/forms" / vh.FORMS[role]).read_bytes())
    person, mail = PEOPLE[role]
    name, contact = name or person, contact or mail
    fields = dict(form["fields"], full_name=name, public_contact=contact, registered_utc=REG_T, signature=name)
    if "slot" in fields:
        fields["slot"] = role
        fields["languages_read"] = "English"
    doc = {"schema": vh.SCHEMA, "form": form["form"], "id": "syn-" + role.lower(), "role": role, "kind": "human",
           "status": "FILLED", "full_name": name, "signature": name, "independence_attestation": vh.INDEPENDENCE,
           "controlling_protocol": controlling, "fields": fields,
           "attestations_all_required_true": list(form["attestations_all_required_true"]),
           "attestations_confirmed": True, "required_before": form["required_before"]}
    if "disclosures_required" in form:
        doc["disclosures_required"] = {k: ([] if k == "other_conflicts" else False) for k in form["disclosures_required"]}
    return doc


class HumanValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repo(self.tmp.name)
        self.ctl = self.repo.controlling

    def rec(self, role="R05", **kw):
        return record(role, self.ctl, **kw)

    def rejected(self, doc=None, contains="", **kw):
        if doc is not None:
            self.repo.register(doc, **kw)
        r = self.repo.validate()
        self.assertEqual(r["decision"], "HUMAN_RECORDS_INVALID", r)
        self.assertEqual(set(r["roles"].values()), {"UNFILLED"}, "fail closed: nothing registered")
        self.assertTrue(any(contains in e for e in r["errors"]), r["errors"])
        return r

    # -- baseline ---------------------------------------------------------------------------------
    def test_no_records_all_unfilled(self):
        r = self.repo.validate()
        self.assertEqual((r["errors"], set(r["roles"].values())), ([], {"UNFILLED"}))
        self.assertEqual(r["gates"]["G3_ENTROPY"], "CLOSED")

    def test_valid_four_distinct_humans_registered(self):
        for role in ("R05", "R06", "R03", "R04"):
            self.repo.register(self.rec(role))
        r = self.repo.validate()
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["roles"], dict.fromkeys(("R03", "R04", "R05", "R06"), "REGISTERED"))
        self.assertEqual(r["gates"]["G2_REGISTRY"], "CLOSED")   # R16 approvals still unfilled (frozen gate)
        self.assertEqual(r["gates"]["G3_ENTROPY"], "CLOSED")

    def test_registered_distinguished_from_unfilled(self):
        self.repo.register(self.rec("R05"))
        r = self.repo.validate()
        self.assertEqual(r["roles"], {"R03": "UNFILLED", "R04": "UNFILLED", "R05": "REGISTERED", "R06": "UNFILLED"})

    # -- schema, role, identity, disclosures, attestations, timestamp, protocol ------------------
    def test_schema_and_envelope(self):
        for mutate, why in ((lambda d: d.update(schema="other"), "wrong schema"),
                            (lambda d: d.pop("signature"), "envelope"),
                            (lambda d: d.update(extra=1), "envelope"),
                            (lambda d: d.update(form="another form"), "frozen form")):
            with self.subTest(why=why):
                self.setUp()
                d = self.rec(); mutate(d)
                self.rejected(d, why)

    def test_role_id_and_slot(self):
        for mutate, why in ((lambda d: d.update(role="R07"), "R03-R06"),
                            (lambda d: d["fields"].update(slot="R06"), "slot"),
                            (lambda d: d.update(id="Bad ID!"), "invalid id")):
            with self.subTest(why=why):
                self.setUp()
                d = self.rec(); mutate(d)
                self.rejected(d, why, filename="R05-registration.json")

    def test_identity_fields(self):
        for mutate, why in ((lambda d: d.update(full_name=""), "full_name: nonempty"),
                            (lambda d: d.update(full_name=" Padded Name"), "full_name: nonempty"),
                            (lambda d: d.update(full_name="A (B)", signature="A (B)"), "plain personal name"),
                            (lambda d: d["fields"].update(full_name="Someone Else"), "fields.full_name/signature differ"),
                            (lambda d: d["fields"].update(public_contact=None), "fields.public_contact")):
            with self.subTest(why=why):
                self.setUp()
                d = self.rec(); mutate(d)
                self.rejected(d, why)

    def test_disclosures_and_attestations(self):
        for mutate, why in ((lambda d: d["disclosures_required"].update(knows_historical_firstcall_outcomes=None), "true or false"),
                            (lambda d: d["disclosures_required"].pop("viewed_A1_frame_before_registration"), "disclosures"),
                            (lambda d: d["disclosures_required"].update(other_conflicts="none"), "list"),
                            (lambda d: d["attestations_all_required_true"].pop(), "attestations differ"),
                            (lambda d: d["attestations_all_required_true"].__setitem__(2, "I may use a model"), "attestations differ"),
                            (lambda d: d.update(attestations_confirmed="yes"), "not confirmed"),
                            (lambda d: d.update(independence_attestation="ok"), "independence"),
                            (lambda d: d.update(required_before="G5"), "required_before")):
            with self.subTest(why=why):
                self.setUp()
                d = self.rec(); mutate(d)
                self.rejected(d, why)

    def test_timestamps(self):
        for value, why in (("2026-09-20 00:30", "UTC timestamp"), ("2026-02-31T00:00:00Z", "impossible"),
                           ("2026-09-20T02:00:00Z", "outside"), ("2026-09-19T23:00:00Z", "outside")):
            with self.subTest(value=value):
                self.setUp()
                d = self.rec(); d["fields"]["registered_utc"] = value
                self.rejected(d, why)

    def test_controlling_protocol(self):
        d = self.rec(); d["controlling_protocol"] = {"commit": "0" * 40, "tag": "ctl"}
        self.rejected(d, "controlling protocol")

    def test_record_not_on_controlling_protocol(self):
        self.repo.git("checkout", "-q", "--orphan", "stray")
        self.repo.register(self.rec(), message="stray root")
        self.rejected(None, "controlling protocol commit")

    # -- conflicts and duplicates ----------------------------------------------------------------
    def test_one_human_in_conflicting_roles(self):
        for a, b in (("R05", "R06"), ("R03", "R04"), ("R03", "R05"), ("R04", "R06")):
            with self.subTest(pair=(a, b)):
                self.setUp()
                name, contact = PEOPLE[a]
                self.repo.register(self.rec(a))
                self.repo.register(self.rec(b, name=name.upper(), contact="other-" + contact))  # case variant
                self.rejected(None, "role conflict")

    def test_designated_custodian_cannot_hold_entropy_roles(self):
        for role in ("R03", "R04"):
            with self.subTest(role=role):
                self.setUp()
                self.rejected(self.rec(role, name="Ross Buckley"), "role conflict")

    def test_designated_custodian_must_disclose_as_adjudicator(self):
        d = self.rec("R05", name="Ross Buckley")
        self.rejected(d, "must disclose")
        self.setUp()
        d = self.rec("R05", name="Ross Buckley")
        d["disclosures_required"].update(is_protocol_author=True, is_capture_or_snapshot_custodian=True,
                                         other_conflicts=["Holds R01 protocol custodian and R02 source/snapshot custodian"])
        self.repo.register(d)
        self.assertEqual(self.repo.validate()["roles"]["R05"], "REGISTERED")

    def test_duplicates(self):
        self.repo.register(self.rec("R05"))
        self.repo.register(self.rec("R06") | {"id": "syn-r05"})
        self.rejected(None, "duplicate registration id")
        self.setUp()
        self.repo.register(self.rec("R05"))
        self.repo.register(self.rec("R06", contact=PEOPLE["R05"][1]))
        self.rejected(None, "one contact")

    def test_second_record_for_same_role_by_other_name(self):
        self.repo.register(self.rec("R05"))
        self.repo.register(self.rec("R05", name="Synthetic Eve Person", contact="eve@example.invalid"),
                           filename="R06-registration.json")
        self.rejected(None, "filename disagrees")

    # -- append-only ----------------------------------------------------------------------------
    def test_overwrite_replacement_and_deletion(self):
        self.repo.register(self.rec("R05"))
        d = self.rec("R05"); d["fields"]["languages_read"] = "English, French"
        self.repo.register(d)
        self.rejected(None, "overwrite")
        self.setUp()
        self.repo.register(self.rec("R05"))
        edited = self.rec("R05"); edited["fields"]["languages_read"] = "English, German"
        self.repo.write("R05-registration.json", edited)        # uncommitted, still schema-valid
        self.rejected(None, "working-tree bytes differ")
        self.setUp()
        self.repo.register(self.rec("R05"))
        (self.repo.root / vh.HUMANS_REL / "R05-registration.json").unlink()
        self.repo.commit("remove"); self.repo.push()
        self.rejected(None, "removed")

    # -- signature / anchoring --------------------------------------------------------------------
    def test_unsigned_or_unanchored(self):
        cases = [("typed", lambda: self.repo.register(self.rec() | {"signature": "Someone"}), "typed signature"),
                 ("working tree", lambda: self.repo.write("R05-registration.json", self.rec()), "not committed"),
                 ("no tag", lambda: self.repo.register(self.rec(), tag=False), "annotated tag"),
                 ("not pushed", lambda: self.repo.register(self.rec(), push=False), "origin"),
                 ("lightweight", None, "annotated tag")]
        for label, act, why in cases:
            with self.subTest(label=label):
                self.setUp()
                if act is None:
                    self.repo.register(self.rec(), tag=False)
                    self.repo.tag("light", annotated=False)
                else:
                    act()
                self.rejected(None, why)

    def test_anchor_tag_must_itself_be_on_origin(self):
        self.repo.register(self.rec(), tag=False)                  # record commit pushed, untagged
        self.repo.commit("later local work"); self.repo.tag("local-only")   # annotated, not pushed
        self.rejected(None, "no annotated tag on origin")

    # -- filename is never the source of truth ---------------------------------------------------
    def test_filename_never_implies_registration(self):
        for name, data, why in (("R05-registration.json", b"{}", "role"),
                                ("R05-registration.json", b"not json", "malformed"),
                                ("R07-registration.json", b"{}", "unexpected entry"),
                                ("notes.json", b"{}", "unexpected entry")):
            with self.subTest(name=name, data=data):
                self.setUp()
                self.repo.write(name, data); self.repo.commit("c"); self.repo.tag("t"); self.repo.push()
                self.rejected(None, why)

    def test_malformed_json(self):
        for data, why in ((b'{"a":1,"a":2}', "duplicate JSON key"), (b'{"a":NaN}', "non-finite"),
                          (b"\xff", "malformed JSON"), (b"[]", "role")):
            with self.subTest(data=data):
                self.setUp()
                self.repo.write("R05-registration.json", data); self.repo.commit("c"); self.repo.tag("t"); self.repo.push()
                self.rejected(None, why)

    def test_symlink_rejected(self):
        target = self.repo.write("R05-registration.json", self.rec())
        target.rename(self.repo.root / "elsewhere.json")
        os.symlink(self.repo.root / "elsewhere.json", self.repo.root / vh.HUMANS_REL / "R05-registration.json")
        self.rejected(None, "unexpected entry")

    # -- non-human ------------------------------------------------------------------------------
    def test_ai_model_tool_rejected(self):
        ai = "AI/model/tool"
        for mutate, who, message, why in (
                (lambda d: d.update(kind="model"), {}, "m", "kind must be 'human'"),
                (lambda d: d.update(kind="agent"), {}, "m", "kind must be 'human'"),
                (lambda d: d.update(full_name="Claude", signature="Claude") or
                 d["fields"].update(full_name="Claude", signature="Claude"), {}, "m", ai),
                (lambda d: d["fields"].update(public_contact="noreply@anthropic.com"), {}, "m", ai),
                (lambda d: None, {"name": "Codex"}, "m", "commit shows " + ai),
                (lambda d: None, {}, "register\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>", "commit shows " + ai)):
            with self.subTest(why=why, who=who):
                self.setUp()
                d = self.rec(); mutate(d)
                self.rejected(d, why, message=message, who=who)

    def test_ai_tagger_rejected(self):
        self.repo.register(self.rec(), tag=False)
        self.repo.tag("reg-by-bot", name="Codex", email="codex@example.invalid")
        self.rejected(None, "tag shows AI/model/tool")

    def test_fail_closed_one_bad_record_voids_all(self):
        self.repo.register(self.rec("R05"))
        self.repo.register(self.rec("R06") | {"signature": "Nobody"})
        r = self.rejected(None, "typed signature")
        self.assertEqual(r["records"], {})

    def test_combine_forgives_only_the_humans_present_error_when_valid(self):
        pre = {"errors": [vh.PRE_REVEAL_HUMANS_ERROR + ": ['R05-registration.json']", "R17 parser digest mismatch"]}
        ok, bad = {"decision": "HUMAN_RECORDS_VALID", "errors": []}, {"decision": "HUMAN_RECORDS_INVALID", "errors": ["x"]}
        self.assertEqual(vh.combine(pre, ok)["pre_reveal_errors"], ["R17 parser digest mismatch"])
        self.assertFalse(vh.combine(pre, ok)["pass"])
        self.assertEqual(len(vh.combine(pre, bad)["pre_reveal_errors"]), 2)
        self.assertTrue(vh.combine({"errors": [vh.PRE_REVEAL_HUMANS_ERROR + ": [...]"]}, ok)["pass"])

    def test_real_repository_has_no_records_and_is_unchanged(self):
        r = vh.validate_humans(REAL)
        self.assertEqual((r["errors"], set(r["roles"].values())), ([], {"UNFILLED"}))
        self.assertEqual(r["gates"]["G1_SNAPSHOT"], "OPEN")        # frozen semantics, unchanged by this tool
        self.assertEqual(r["gates"]["G2_REGISTRY"], "CLOSED")


if __name__ == "__main__":
    unittest.main()
