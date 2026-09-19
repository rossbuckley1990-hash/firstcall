#!/usr/bin/env python3
"""Offline hostile tests for the A1 pre-reveal registrations (R17 parser first).

Socket connections and os.urandom are banned. Every document is synthetic; nothing reads A1.
"""
import copy
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))

import a1_spec_parser as sp  # noqa: E402
import validate_registrations as vr  # noqa: E402

PSL = sp.a1_frame.load_pinned_psl()


class Offline(unittest.TestCase):
    def setUp(self):
        self._orig = (socket.socket.connect, socket.create_connection, os.urandom)

        def banned(*a, **k):
            raise AssertionError("network or entropy use during offline test")
        socket.socket.connect = socket.create_connection = os.urandom = banned

    def tearDown(self):
        socket.socket.connect, socket.create_connection, os.urandom = self._orig


def rec(doc_bytes, path="APIs/vendor.com/1.0/openapi.json"):
    return json.loads(sp.structural_record(path, doc_bytes, PSL))


def js(obj):
    return json.dumps(obj).encode()


def semantic(r):
    return {k: r[k] for k in ("status", "reason", "family", "e2", "d8_flags", "structure", "ignored_nonroot_servers")}


BASE = {"openapi": "3.0.3", "info": {"title": "t", "version": "1", "termsOfService": "https://vendor.com/terms",
                                     "x-origin": [{"url": "https://vendor.com/openapi.json"}]},
        "externalDocs": {"url": "https://docs.vendor.com/"}, "servers": [{"url": "https://api.vendor.com/v1"}],
        "paths": {}}


class ParserEquivalenceTests(Offline):
    def test_same_bytes_byte_identical_and_fresh_process(self):
        b = js(BASE)
        a1 = sp.structural_record("APIs/vendor.com/1.0/openapi.json", b, PSL)
        a2 = sp.structural_record("APIs/vendor.com/1.0/openapi.json", b, PSL)
        self.assertEqual(a1, a2)
        repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        blob = subprocess.run(["git", "-C", str(repo), "hash-object", "-w", "--stdin"], input=b, capture_output=True,
                              check=True).stdout.decode().strip()
        subprocess.run(["git", "-C", str(repo), "update-index", "--add", "--cacheinfo",
                        f"100644,{blob},APIs/vendor.com/1.0/openapi.json"], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit",
                        "-q", "-m", "f"], check=True)
        c = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, check=True).stdout.decode().strip()
        out = subprocess.run([sys.executable, "-B", str(HERE / "a1_spec_parser.py"), "--repo", str(repo), "--commit", c,
                              "--path", "APIs/vendor.com/1.0/openapi.json"], capture_output=True, check=True,
                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1")).stdout
        self.assertEqual(out.rstrip(b"\n"), a1)

    def test_reordered_json_and_yaml_equivalents(self):
        reordered = {"paths": {}, "servers": BASE["servers"], "externalDocs": BASE["externalDocs"],
                     "info": dict(reversed(list(BASE["info"].items()))), "openapi": "3.0.3"}
        yaml_doc = b"""openapi: '3.0.3'
servers:
  - url: https://api.vendor.com/v1
externalDocs: {url: 'https://docs.vendor.com/'}
info:
  x-origin: [{url: 'https://vendor.com/openapi.json'}]
  termsOfService: https://vendor.com/terms
  version: '1'
  title: t
paths: {}
"""
        a = semantic(rec(js(BASE)))
        self.assertEqual(a, semantic(rec(js(reordered))))
        y = semantic(rec(yaml_doc, "APIs/vendor.com/1.0/openapi.yaml"))
        self.assertEqual(a["e2"], y["e2"])
        self.assertEqual(a["family"], y["family"])

    def test_duplicate_looking_servers_unicode_case_trailing_dot_default_port(self):
        doc = copy.deepcopy(BASE)
        doc["servers"] = [{"url": u} for u in ("https://API.Vendor.com/v1", "https://api.vendor.com.:443/v1/",
                                               "https://api.vendor.com/v1", "https://bücher.de/", "https://xn--bcher-kva.de")]
        leads = rec(js(doc))["e2"]["leads"]
        self.assertEqual(leads.count("https://api.vendor.com/v1"), 1)
        self.assertEqual([u for u in leads if "bcher" in u], ["https://xn--bcher-kva.de/"])

    def test_server_variables_and_templates(self):
        doc = copy.deepcopy(BASE)
        doc["servers"] = [{"url": "https://{region}.vendor.com/{v}", "variables": {"region": {"default": "eu"}, "v": {"default": "v2"}}},
                          {"url": "https://{tenant}.vendor.com", "variables": {"tenant": {"enum": ["a", "b"]}}},
                          {"url": "https://{x.vendor.com"}]
        r = rec(js(doc))
        self.assertIn("https://eu.vendor.com/v2", r["e2"]["leads"])
        self.assertIn("UNRESOLVED_TEMPLATE", [d["reason"] for d in r["e2"]["dropped"]])
        self.assertNotIn("https://{x.vendor.com/", r["e2"]["leads"])
        self.assertIn("INVALID_DNS_HOST", [d["reason"] for d in r["e2"]["dropped"]])
        self.assertEqual(r["d8_flags"], {})

    def test_swagger_combinations(self):
        r = rec(b"swagger: 2.0\nhost: API.v.com:8443\nbasePath: /v2\ninfo: {title: t, version: '1'}\npaths: {}\n",
                "APIs/v.com/1/swagger.yaml")
        self.assertEqual(r["family"], "OAS2")                                         # unquoted YAML float 2.0
        self.assertEqual(r["e2"]["leads"], ["https://api.v.com:8443/v2"])              # anchored default scheme https
        r = rec(js({"swagger": "2.0", "host": "v.com", "schemes": ["http", "https"], "paths": {}}), "APIs/v.com/1/swagger.json")
        self.assertEqual(r["e2"]["leads"], ["http://v.com/", "https://v.com/"])
        r = rec(js({"swagger": "2.0", "paths": {}}), "APIs/v.com/1/swagger.json")
        self.assertEqual(r["e2"]["leads"], [])
        r = rec(js({"swagger": "2.0", "openapi": "3.0.0", "paths": {}}), "APIs/v.com/1/swagger.json")
        self.assertEqual(r["family"], "AMBIGUOUS_OPENAPI_AND_SWAGGER")

    def test_dropped_candidates_order_independent(self):
        a, b = copy.deepcopy(BASE), copy.deepcopy(BASE)
        a["servers"] = [{"url": "/v1"}, {"url": "http://192.0.2.1"}, {"url": "https://{t}.v.com"}]
        b["servers"] = list(reversed(a["servers"]))
        self.assertEqual(rec(js(a))["e2"], rec(js(b))["e2"])

    def test_oas3_server_precedence_root_only(self):
        doc = copy.deepcopy(BASE)
        doc["paths"] = {"/a": {"servers": [{"url": "https://path.vendor.com"}],
                               "get": {"servers": [{"url": "https://op.vendor.com"}]}}}
        r = rec(js(doc))
        self.assertEqual(r["ignored_nonroot_servers"], 2)
        self.assertFalse(any("path.vendor" in u or "op.vendor" in u for u in r["e2"]["leads"]))

    def test_relative_no_servers_ip_literals(self):
        doc = copy.deepcopy(BASE)
        doc["servers"] = [{"url": "/v1"}, {"url": "//cdn.vendor.com"}, {"url": "http://192.0.2.1"}, {"url": "https://[2001:db8::1]"},
                          {"url": "http://localhost:8080"}]
        r = rec(js(doc))
        self.assertEqual(sorted(d["reason"] for d in r["e2"]["dropped"]),
                         ["IP_LITERAL_HOST", "IP_LITERAL_HOST", "NON_DNS_HOST", "RELATIVE_OR_NON_HTTP", "RELATIVE_OR_NON_HTTP"])
        doc.pop("servers")
        self.assertEqual(rec(js(doc))["e2"]["leads"], ["https://docs.vendor.com/", "https://vendor.com/openapi.json",
                                                       "https://vendor.com/terms"])

    def test_path_keys_rdg_and_public_suffix_edges(self):
        b = js(BASE)
        s = lambda p: rec(b, p)["structure"]
        self.assertEqual(s("APIs/Bücher.DE./1/openapi.json")["rdg"], s("APIs/xn--bcher-kva.de/1/openapi.json")["rdg"])
        self.assertEqual(s("APIs/api.vendor.com:payments/1/openapi.json")["rdg"], "vendor.com")
        self.assertEqual(s("APIs/co.uk/1/openapi.json")["rdg"], "singleton:co.uk")
        self.assertEqual(s("APIs/a.github.io/1/openapi.json")["rdg"], "a.github.io")
        self.assertEqual(s("APIs/192.0.2.1/1/openapi.json")["host_reason"], "IP_LITERAL")
        self.assertEqual(s("APIs/localhost/1/openapi.json")["rdg"], "singleton:localhost")
        with self.assertRaises(sp.ParseFailure):
            sp.structural_record("not/an/entry.json", b, PSL)

    def test_leads_do_not_affect_rdg(self):
        doc = copy.deepcopy(BASE)
        doc["servers"] = [{"url": "https://totally-different.org"}]
        self.assertEqual(rec(js(doc))["structure"], rec(js(BASE))["structure"])


class ParserFailClosedTests(Offline):
    def failed(self, data, path="APIs/v.com/1/openapi.json"):
        r = rec(data, path)
        self.assertEqual((r["status"], r["e2"]), ("PARSE_FAILED", {"leads": [], "dropped": []}))
        return r["reason"]

    def test_malformed_documents(self):
        y = "APIs/v.com/1/openapi.yaml"
        self.assertEqual(self.failed(b"{not json"), "JSON_INVALID")
        self.assertEqual(self.failed(b'{"a":1,"a":2}'), "DUPLICATE_KEY")
        self.assertEqual(self.failed(b'{"a":NaN}'), "NON_FINITE_NUMBER")
        self.assertEqual(self.failed(b"[1,2]"), "ROOT_NOT_MAPPING")
        self.assertEqual(self.failed(b"\xff\xfe"), "INVALID_UTF8")
        self.assertEqual(self.failed(b"a: [1, 2\n", y), "YAML_INVALID")
        self.assertEqual(self.failed(b"a: 1\na: 2\n", y), "DUPLICATE_KEY")
        self.assertEqual(self.failed(b"a: 1\n---\nb: 2\n", y), "NOT_EXACTLY_ONE_DOCUMENT")
        self.assertEqual(self.failed(b"", y), "NOT_EXACTLY_ONE_DOCUMENT")
        self.assertEqual(self.failed(b"x: !!python/object:os.system {}\n", y), "YAML_CONSTRUCTOR_ERROR")
        with self.assertRaises(sp.ParseFailure) as ctx:
            sp.structural_record("APIs/v.com/1/openapi.txt", b"{}", PSL)
        self.assertEqual(ctx.exception.reason, "NOT_AN_A1_RAW_ENTRY_PATH")
        with self.assertRaises(sp.ParseFailure) as ctx:
            sp.parse_document(b"{}", "x.txt")
        self.assertEqual(ctx.exception.reason, "UNSUPPORTED_FILE_TYPE")
        self.assertEqual(self.failed(b'{"a":' * 1001 + b"1" + b"}" * 1001), "TOO_DEEP")
        self.assertEqual(rec(b'{"a":' * 999 + b"1" + b"}" * 999)["status"], "PARSED")
        self.assertEqual(self.failed(b"a: " + b"[" * 1200 + b"1" + b"]" * 1200 + b"\n", y), "TOO_DEEP")

    def test_alias_bomb_and_size_limits(self):
        bomb = b"a: &a [x]\nb: [" + b", ".join([b"*a"] * (sp.MAX_ALIASES + 1)) + b"]\n"
        self.assertEqual(self.failed(bomb, "APIs/v.com/1/openapi.yaml"), "ALIAS_LIMIT")
        old = sp.MAX_INPUT_BYTES
        sp.MAX_INPUT_BYTES = 10
        try:
            self.assertEqual(self.failed(js(BASE)), "INPUT_TOO_LARGE")
        finally:
            sp.MAX_INPUT_BYTES = old

    def test_cycles_nonfinite_and_equal_mapping_keys(self):
        for data, reason in ((b"x: &x [*x]", "DOCUMENT_INVALID"), (b"x: .nan", "NON_FINITE_NUMBER"),
                             (b"1: one\ntrue: yes", "DUPLICATE_KEY"), (b".nan: x", "NON_FINITE_NUMBER"),
                             (b"a: {-.inf: x}", "NON_FINITE_NUMBER")):
            self.assertEqual(self.failed(data, "APIs/v.com/1/openapi.yaml"), reason)
        self.assertEqual(self.failed(b'{"x":1e999}'), "NON_FINITE_NUMBER")

    def test_shared_idna_through_complete_parser(self):
        doc = {"openapi": "3.0.0", "servers": [{"url": "https://straße.de/0//"}]}
        r = rec(js(doc), "APIs/straße.de/1/openapi.json")
        self.assertEqual(r["structure"]["host"], "xn--strae-oqa.de")
        self.assertEqual(r["e2"]["leads"], ["https://xn--strae-oqa.de/0"])

    def test_accepted_edge_syntax(self):
        r = rec(b"\xef\xbb\xbf" + js(BASE))
        self.assertEqual(r["status"], "PARSED")                                      # one BOM stripped
        y = b"base: &b {url: 'https://docs.v.com/'}\nexternalDocs:\n  <<: *b\nopenapi: 3.1.0\n1: one\n"
        r = rec(y, "APIs/v.com/1/openapi.yaml")
        self.assertEqual((r["status"], r["family"]), ("PARSED", "OAS3"))              # merge key preserved
        self.assertEqual(r["e2"]["leads"], ["https://docs.v.com/"])


class D8Tests(Offline):
    def test_anchored_code_contradicts_anchored_text(self):
        norm = sp.a1_evidence._norm_url
        for bad in ("https://{x.com", "https://ex ample.com", "https://-x.com", "https://exa_mple.com"):
            url, why = norm(bad)
            self.assertIsNotNone(url, bad)                                             # anchored code keeps it
            self.assertTrue(any(f.startswith("TEXT_RULE_NON_DNS_HOST") for f in sp.text_rule_flags(url)), bad)
        self.assertIn("TEXT_RULE_DOT_SEGMENTS_UNRESOLVED", sp.text_rule_flags(norm("https://x.com/a/../b")[0]))
        self.assertIn("TEXT_RULE_PERCENT_ENCODING_UNNORMALISED", sp.text_rule_flags(norm("https://x.com/%7Euser")[0]))
        self.assertEqual(sp.text_rule_flags(norm("https://x.com/a%2Fb")[0]), [])     # reserved escape stays
        self.assertEqual(sp.remove_dot_segments("/a/b/c/./../../g"), "/a/g")


class IntegrityTests(Offline):
    def test_vendor_tamper_fails_closed(self):
        tmp = Path(tempfile.mkdtemp()) / "v"
        shutil.copytree(sp.VENDOR, tmp)
        self.assertTrue(sp.verify_integrity(vendor_dir=tmp))
        p = tmp / "yaml" / "loader.py"
        os.chmod(p, 0o644)
        p.write_bytes(p.read_bytes() + b"\n# tampered\n")
        with self.assertRaises(sp.ParserIntegrityError):
            sp.verify_integrity(vendor_dir=tmp)
        (tmp / "yaml" / "extra.py").write_text("x = 1\n")
        with self.assertRaises(sp.ParserIntegrityError):
            sp.verify_integrity(vendor_dir=tmp)

    def test_anchored_dependency_tamper_fails_closed(self):
        fake = Path(tempfile.mkdtemp()) / "a.json"
        doc = json.loads(sp.AMENDMENT_JSON.read_bytes())
        doc["registered_file_sha256"]["experiments/programme-a/a1/a1_evidence.py"] = "0" * 64
        fake.write_text(json.dumps(doc))
        old = sp.AMENDMENT_JSON
        sp.AMENDMENT_JSON = fake
        try:
            with self.assertRaises(sp.ParserIntegrityError):
                sp.verify_integrity()
        finally:
            sp.AMENDMENT_JSON = old

    def test_pinned_psl_required_and_no_libyaml(self):
        with self.assertRaises(sp.ParserIntegrityError):
            sp.structural_record("APIs/v.com/1/openapi.json", js(BASE), b"com\n")
        self.assertFalse(sp.yaml.__with_libyaml__)
        self.assertEqual(Path(sp.yaml.__file__).resolve().parent, (sp.VENDOR / "yaml").resolve())

    def test_parser_has_no_network_or_entropy_code(self):
        code = (HERE / "a1_spec_parser.py").read_text().split('"""', 2)[2]
        for token in ("urllib.request", "http.client", "socket", "requests", "urandom", "random"):
            self.assertNotIn(token, code)


class RegistrationTests(Offline):
    def test_records_complete_and_digests(self):
        errors, recs = vr.check_records()
        self.assertEqual(errors, [])
        self.assertEqual(recs["R17"]["status"], "REGISTERED_PENDING_ANCHOR")
        self.assertEqual(recs["R07"]["artifact"]["mechanism"], "NO_MACHINE_TRANSLATION (fail-closed null translator)")
        self.assertEqual(recs["R16"]["approvals"], {"ADJ-1": None, "ADJ-2": None})

    def test_no_fabricated_humans(self):
        self.assertEqual(vr.check_humans(), [])
        audit = json.loads((HERE / "pre-reveal-audit.json").read_text())
        self.assertFalse(audit["human_roles"]["R03"]["ross_permitted"])
        self.assertFalse(audit["human_roles"]["R04"]["ross_permitted"])
        self.assertTrue(audit["human_roles"]["R05"]["ross_permitted"])
        for r in ("R03", "R04", "R05", "R06"):
            self.assertEqual(audit["human_roles"][r]["status"], "UNFILLED")

    def test_zero_information(self):
        self.assertEqual(vr.check_zero_information(), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
