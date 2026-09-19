#!/usr/bin/env python3
"""Offline D8 regression tests (Freeze 1.2.1). Synthetic URLs only; socket and os.urandom banned."""
import os
import random
import socket
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))

import a1_e2_leads as n  # noqa: E402
import a1_evidence as old  # noqa: E402  (anchored, superseded normaliser)

RNG_SEED = 20260919


class Offline(unittest.TestCase):
    def setUp(self):
        self._o = (socket.socket.connect, socket.create_connection, os.urandom)

        def banned(*a, **k):
            raise AssertionError("network or entropy use in offline test")
        socket.socket.connect = socket.create_connection = os.urandom = banned

    def tearDown(self):
        socket.socket.connect, socket.create_connection, os.urandom = self._o


def norm(u):
    return n.normalise_lead(u)


class D8RuleTests(Offline):
    def ok(self, raw, expected):
        self.assertEqual(norm(raw), (expected, None), raw)

    def drop(self, raw, reason):
        self.assertEqual(norm(raw), (None, reason), raw)

    def test_non_dns_hosts_cannot_survive(self):
        for raw in ("https://{x.com", "https://-x.com", "https://x-.com", "https://exa_mple.com", "https://x..com",
                    "https://1.2.3", "https://127.1", "https://0x7f.1", "https://xn--zz.com", "https://a" * 1 + "b" * 64 + ".com",
                    "https://" + ".".join(["a" * 60] * 5) + ".com", "https://ex%61mple.com"):
            self.assertEqual(norm(raw)[0], None, raw)
            self.assertEqual(norm(raw)[1], "INVALID_DNS_HOST", raw)
        for raw, why in (("http://localhost", "NON_DNS_HOST"), ("https://x．com", "NON_DNS_HOST"),
                         ("http://192.0.2.1", "IP_LITERAL_HOST"), ("https://[2001:db8::1]/", "IP_LITERAL_HOST"),
                         ("https://ex ample.com", "MALFORMED_URI"), ("https://x.com/a\tb", "MALFORMED_URI"),
                         ("https://x.com/a\nb", "MALFORMED_URI"), ("https://[zz/", "MALFORMED")):
            self.drop(raw, why)

    def test_anchored_code_accepted_these_new_rule_rejects(self):
        for raw in ("https://{x.com", "https://ex ample.com", "https://-x.com", "https://exa_mple.com", "https://1.2.3"):
            self.assertIsNotNone(old._norm_url(raw)[0], raw)       # the D8 defect, preserved in the anchored module
            self.assertIsNone(norm(raw)[0], raw)

    def test_scheme_case_trailing_dot_ports_userinfo_fragment(self):
        self.ok("HTTPS://Docs.Vendor.COM.:443/Guide#top", "https://docs.vendor.com/Guide")   # path case preserved
        self.ok("http://x.com:80", "http://x.com/")
        self.ok("https://x.com:8443/a", "https://x.com:8443/a")
        self.ok("http://x.com:443/", "http://x.com:443/")                                     # 443 is not http's default
        self.ok("https://user:pw@x.com/a", "https://x.com/a")
        self.drop("https://x.com:99999", "MALFORMED_PORT")
        self.drop("ftp://x.com", "RELATIVE_OR_NON_HTTP")
        self.assertNotEqual(norm("http://x.com/")[0], norm("https://x.com/")[0])              # http/https distinct

    def test_query_rules(self):
        self.ok("https://x.com/?b=2&utm_source=x&a=1&a=0&&c&gclid=9&fbclid=8&utm_medium=y",
                "https://x.com/?a=0&a=1&b=2&c")
        self.ok("https://x.com/?a=&a", "https://x.com/?a&a=")
        self.ok("https://x.com/?q=%7e%2f", "https://x.com/?q=~%2F")
        self.ok("https://x.com/?UTM_SOURCE=1", "https://x.com/?UTM_SOURCE=1")                  # tracking match is case-sensitive

    def test_path_dot_segments_percent_and_terminal_slash(self):
        self.ok("https://x.com/a/b/c/./../../g", "https://x.com/a/g")
        self.ok("https://x.com/a/%2E%2E/b", "https://x.com/b")                                 # decode unreserved first
        self.ok("https://x.com/%7euser/", "https://x.com/~user")
        self.ok("https://x.com/a%2fb", "https://x.com/a%2Fb")                                  # reserved stays encoded
        self.ok("https://x.com/a//", "https://x.com/a")                                       # entire terminal slash run removed once
        self.ok("https://x.com", "https://x.com/")
        self.ok("https://x.com/über", "https://x.com/%C3%BCber")
        self.drop("https://x.com/a%zz", "MALFORMED_URI")
        self.drop("https://x.com/a%4", "MALFORMED_URI")
        self.drop('https://x.com/a"b', "MALFORMED_URI")
        self.drop("https://x.com/a|b", "MALFORMED_URI")

    def test_idn_and_punycode(self):
        self.ok("https://Bücher.de", "https://xn--bcher-kva.de/")
        self.ok("https://xn--bcher-kva.de", "https://xn--bcher-kva.de/")
        self.ok("https://bücher.de", "https://xn--bcher-kva.de/")                       # NFD input, NFC applied
        self.ok("https://straße.de", "https://xn--strae-oqa.de/")                             # IDNA2008 (not 'strasse')

    def test_templates_relative_and_empty(self):
        self.drop("https://{region}.x.com", "UNRESOLVED_TEMPLATE")
        self.drop("https://x.com/{version}/docs", "UNRESOLVED_TEMPLATE")
        self.drop("https://x.com/{v", "MALFORMED_URI")
        self.drop("/v1", "RELATIVE_OR_NON_HTTP")
        self.drop("//cdn.x.com/a", "RELATIVE_OR_NON_HTTP")
        self.drop("   ", "EMPTY_OR_NOT_STRING")
        self.drop(5, "EMPTY_OR_NOT_STRING")
        self.ok("  https://x.com/a  ", "https://x.com/a")

    def test_e2_leads_fields_unchanged_and_output_sorted(self):
        doc = {"openapi": "3.0.0", "info": {"x-origin": [{"url": "https://B.com/o"}], "termsOfService": "/t",
                                            "contact": {"url": "https://{x.com"}},
               "externalDocs": {"url": "https://a.com/d/"}, "servers": [{"url": "https://{r}.c.com", "variables": {"r": {"default": "eu"}}},
                                                                          {"url": "http://127.0.0.1"}]}
        out = n.e2_leads(doc)
        self.assertEqual(out["leads"], ["https://a.com/d", "https://b.com/o", "https://eu.c.com/"])
        self.assertEqual(sorted(d["reason"] for d in out["dropped"]), ["INVALID_DNS_HOST", "IP_LITERAL_HOST", "RELATIVE_OR_NON_HTTP"])
        self.assertEqual([f for f, _ in old.candidate_links(doc)], [f for f, _ in n.a1_evidence.candidate_links(doc)])
        self.assertIs(n.a1_evidence, old)

    def test_actual_idempotence_regression(self):
        self.ok("HTTPS://sub.x.com:8443/0//", "https://sub.x.com:8443/0")
        for path in ("/", "//", "///", "/a///", "/a//b///", "/a/%2e%2e///", "/.//", "/a//../b/"):
            first = norm("https://x.com" + path)
            self.assertEqual(norm(first[0]), first)
        self.ok("https://x.com/a//b///", "https://x.com/a//b")

    def test_shared_hosts(self):
        import a1_frame_121 as frame
        from a1_host import canonical_host
        self.assertIs(frame.canonical_host, n.canonical_host)
        for host in ("straße.de", "STRASSE.de", "Bücher.DE.", "bücher.de", "xn--bcher-kva.de", "xn--strae-oqa.de", "a-b.example", "例え.テスト"):
            expected = canonical_host(host)
            self.assertEqual(frame.key_host(frame.normalise_key(host))[0], expected)
            self.assertEqual(norm("https://" + host)[0], "https://" + expected + "/")
        for host in ("-x.com", "x-.com", "x..com", "xn--zz.com", "exa_mple.com", "{x.com", "ex ample.com", "192.0.2.1", "[2001:db8::1]", "localhost", "1.2.3", "ex%61mple.com"):
            self.assertIsNone(frame.key_host(host)[0], host)
            self.assertIsNone(norm("https://" + host)[0], host)
        self.assertNotEqual(canonical_host("а.example"), canonical_host("a.example"))  # Cyrillic is not Latin
        self.assertEqual(frame.key_host("straße.de")[0], "xn--strae-oqa.de")

    def test_malformed_authority_and_discarded_components(self):
        for u in ("https://x.com:", "https://a@b@x.com", "https://@x.com", "https://u%xx@x.com", "https://x.com/#%xx", "https://x.com/\ud800"):
            self.assertIsNone(norm(u)[0], repr(u))


class D8PropertyTests(Offline):
    ALPH = list("abcXYZ09-_.%/?&=#:@ {}~ü") + ["%2e", "%7E", "%2F", "..", "./", "//"]

    def gen(self, rng):
        host = rng.choice(["x.com", "X.COM.", "bücher.de", "a-b.example", "sub.x.com", "x..com", "-bad.com", "1.2.3"])
        path = "".join(rng.choice(self.ALPH) for _ in range(rng.randint(0, 12)))
        scheme = rng.choice(["http", "https", "HTTPS", "ftp", ""])
        port = rng.choice(["", ":80", ":443", ":8443"])
        return f"{scheme}://{host}{port}/{path}" if scheme else f"//{host}/{path}"

    def test_deterministic_idempotent_and_only_dns_hosts(self):
        rng = random.Random(RNG_SEED)
        for _ in range(5000):
            raw = self.gen(rng)
            a, b = norm(raw), norm(raw)
            self.assertEqual(a, b)
            if a[0] is not None:
                self.assertEqual(norm(a[0]), a, raw)                               # idempotent
                host = a[0].split("://", 1)[1].split("/", 1)[0].split(":")[0]
                self.assertIsNotNone(n.LDH.match(host.split(".")[0]))
                self.assertEqual(n.dns_host(host), host)
                self.assertNotIn("#", a[0])
                self.assertFalse(any(c in a[0] for c in " {}|\"<>\\^`"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
