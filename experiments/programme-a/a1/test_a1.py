#!/usr/bin/env python3
"""Offline tests for the Freeze-1.2 Population A1 amendment (registrable-domain-group correction).

All tests run under a socket ban and an os.urandom ban. Nothing here retrieves A1 membership,
generates entropy, orders real units, adjudicates vendors or calls any API. Synthetic git
trees are built with git plumbing (no filesystem case folding, colons allowed).
"""
import copy
import itertools
import json
import os
import random
import socket
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

import a1_evidence as ev  # noqa: E402
import a1_frame as fr  # noqa: E402
import a1_permutation as pm  # noqa: E402
import a1_screening as sc  # noqa: E402
import prior_firstcall_projector as pj  # noqa: E402
import validate_a1 as va  # noqa: E402

PINNED_PSL = fr.load_pinned_psl()          # vendored, hash-checked; no network


class NetworkBan(unittest.TestCase):
    def setUp(self):
        self._orig = (socket.socket.connect, socket.create_connection)

        def banned(*a, **k):
            raise AssertionError("network access attempted during offline test")
        socket.socket.connect = banned
        socket.create_connection = banned
        self._urandom = os.urandom

        def no_entropy(*a, **k):
            raise AssertionError("os.urandom called during offline test")
        os.urandom = no_entropy

    def tearDown(self):
        socket.socket.connect, socket.create_connection = self._orig
        os.urandom = self._urandom


def tree_repo(paths, date="2026-01-01T00:00:00Z", content=b"x"):
    """Synthetic snapshot built with git plumbing. `paths` may map path -> bytes content."""
    d = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    items = paths.items() if isinstance(paths, dict) else ((p, content) for p in paths)
    for path, data in items:
        blob = subprocess.run(["git", "-C", str(d), "hash-object", "-w", "--stdin"], input=data,
                              capture_output=True, check=True).stdout.decode().strip()
        subprocess.run(["git", "-C", str(d), "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}"],
                       check=True)
    env = dict(os.environ, GIT_COMMITTER_DATE=date, GIT_AUTHOR_DATE=date)
    subprocess.run(["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q",
                    "-m", "fixture"], check=True, env=env)
    c = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, check=True).stdout.decode().strip()
    return d, c


def frame_for(keys, psl=PINNED_PSL):
    d, c = tree_repo([f"APIs/{k}/1.0/openapi.yaml" for k in keys])
    return fr.build_frame(d, psl, commit=c, psl_sha256=fr.sha256(psl))[0]


def walk(order, status, n, block):
    return sc.screen(list(order), lambda bi, b: {g: status[g] for g in b}, n_target=n, block_size=block)


# ------------------------------------------------------------------ counterexamples A-E

def old_key_level_platform_probabilities(keys, platform_of, component_of, n, partition=None):
    """REFERENCE ONLY (withdrawn design): permute keys; designated key = byte-smallest key of each
    platform within its registrable-domain component; S = designated keys."""
    comps = {}
    for k in keys:
        comps.setdefault(component_of[k], []).append(k)
    designated = set()
    for c, members in comps.items():
        groups = partition.get(c) if partition and c in partition else None
        if groups is None:
            g = {}
            for k in members:
                g.setdefault(platform_of[k], []).append(k)
            groups = list(g.values())
        for grp in groups:
            designated.add(min(grp, key=str.encode))
    hits, total, twice = {p: 0 for p in set(platform_of.values())}, 0, 0
    for order in itertools.permutations(keys):
        sel = [k for k in order if k in designated][:n]
        ps = [platform_of[k] for k in sel]
        for p in set(ps):
            hits[p] += 1
        twice += len(ps) != len(set(ps))
        total += 1
    return {p: Fraction(h, total) for p, h in hits.items()}, Fraction(twice, total)


def rdg_probabilities(frame, n):
    G = frame["G"]
    status = {g: sc.IN_S for g in G}
    hits, total = {g: 0 for g in G}, 0
    for order in itertools.permutations(G):
        for g in walk(order, status, n, 1)["selected"]:
            hits[g] += 1
        total += 1
    return {g: Fraction(h, total) for g, h in hits.items()}


def registrable(k):
    return ".".join(k.split(":")[0].split(".")[-2:])


class CounterexampleTests(NetworkBan):
    def check(self, keys, platform_of, n, expect_old_equal, partition=None):
        M = len(set(platform_of.values()))
        old, twice = old_key_level_platform_probabilities(keys, platform_of, {k: registrable(k) for k in keys}, n, partition)
        required = Fraction(n, M)
        self.assertEqual(all(v == required for v in old.values()), expect_old_equal, old)
        frame = frame_for(keys)
        new = rdg_probabilities(frame, n)
        self.assertEqual(set(new.values()), {Fraction(min(n, len(frame["G"])), len(frame["G"]))})
        return old, twice, frame

    def test_A_same_domain_old_equal_new_equal(self):
        keys = ["a.com", "api.b.com", "b.com", "eu.b.com", "x.b.com", "y.b.com", "c.com"]
        p = {k: ("A" if k == "a.com" else "C" if k == "c.com" else "B") for k in keys}
        for n in (1, 2):
            _, _, frame = self.check(keys, p, n, True)
        self.assertEqual(frame["G"], ["a.com", "b.com", "c.com"])

    def test_A_split_domains_old_fails_new_equal_over_rdgs(self):
        keys = ["a.com", "b1.com", "b2.com", "b3.com", "b4.com", "b5.com", "c.com"]
        p = {k: ("A" if k == "a.com" else "C" if k == "c.com" else "B") for k in keys}
        old, twice, frame = self.check(keys, p, 1, False)
        self.assertEqual((old["B"], old["A"]), (Fraction(5, 7), Fraction(1, 7)))
        old, twice, frame = self.check(keys, p, 2, False)
        self.assertEqual((old["B"], old["A"], twice), (Fraction(20, 21), Fraction(2, 7), Fraction(10, 21)))
        self.assertEqual(len(frame["G"]), 7)      # vendor B contributes 5 RDGs: declared unit property

    def test_B_two_keys_one_domain(self):
        keys = ["x.com", "api.x.com", "a.com", "c.com"]
        p = {"x.com": "X", "api.x.com": "X", "a.com": "A", "c.com": "C"}
        for n in (1, 2):
            self.check(keys, p, n, True)

    def test_C_platform_on_two_domains_old_fails(self):
        keys = ["x.com", "xcloud.com", "a.com", "c.com"]
        p = {"x.com": "X", "xcloud.com": "X", "a.com": "A", "c.com": "C"}
        old, _, _ = self.check(keys, p, 1, False)
        self.assertEqual(old["X"], Fraction(1, 2))
        old, twice, _ = self.check(keys, p, 2, False)
        self.assertEqual((old["X"], twice), (Fraction(5, 6), Fraction(1, 6)))

    def test_D_shared_domain_distinct_platforms(self):
        keys = ["d.com", "partner.d.com", "a.com", "c.com"]
        p = {"d.com": "D1", "partner.d.com": "D2", "a.com": "A", "c.com": "C"}
        self.check(keys, p, 1, True)                                   # correct identity adjudication
        wrong = {"d.com": [["d.com", "partner.d.com"]]}
        old, _ = old_key_level_platform_probabilities(keys, p, {k: registrable(k) for k in keys}, 1, wrong)
        self.assertEqual((old["D2"], old["D1"]), (0, Fraction(1, 3)))  # identity error breaks equality
        frame = frame_for(keys)
        g = next(x for x in frame["groups"] if x["rdg"] == "d.com")
        self.assertEqual((g["primary_key"], g["primary_key_rule"]), ("d.com", "BARE_REGISTRABLE_DOMAIN"))

    def test_E_aliases_old_fails_new_equal(self):
        keys = ["y.com", "api.y.com", "yacq.com", "ybrand.com", "dev.ybrand.com", "z.com"]
        p = {k: ("Z" if k == "z.com" else "Y") for k in keys}
        old, _, frame = self.check(keys, p, 1, False)
        self.assertEqual((old["Y"], old["Z"]), (Fraction(3, 4), Fraction(1, 4)))
        self.assertEqual(frame["G"], ["y.com", "yacq.com", "ybrand.com", "z.com"])


# ------------------------------------------------------------------ SRS over G (exhaustive)

class SamplingProofTests(NetworkBan):
    G = ["g1", "g2", "g3", "g4", "g5", "g6"]
    STATUS = {"g1": sc.IN_S, "g2": sc.EXCLUDED, "g3": sc.IN_S, "g4": sc.UNRESOLVED_ELIGIBILITY,
              "g5": sc.IN_S, "g6": sc.EXCLUDED}

    def test_first_n_of_S_is_uniform_over_n_subsets(self):
        counts = {}
        for order in itertools.permutations(self.G):
            sel = frozenset(walk(order, self.STATUS, 2, 1)["selected"])
            counts[sel] = counts.get(sel, 0) + 1
        S = [g for g, v in self.STATUS.items() if v == sc.IN_S]
        self.assertEqual(set(counts), {frozenset(c) for c in itertools.combinations(S, 2)})
        self.assertEqual(set(counts.values()), {720 // comb(3, 2)})

    def test_inclusion_and_pairwise_probabilities(self):
        hits, pair = {g: 0 for g in self.G}, 0
        for order in itertools.permutations(self.G):
            sel = walk(order, self.STATUS, 2, 1)["selected"]
            for g in sel:
                hits[g] += 1
            pair += ("g1" in sel and "g3" in sel)
        for g in ("g1", "g3", "g5"):
            self.assertEqual(Fraction(hits[g], 720), Fraction(2, 3))
        for g in ("g2", "g4", "g6"):
            self.assertEqual(hits[g], 0)
        self.assertEqual(Fraction(pair, 720), Fraction(2 * 1, 3 * 2))

    def test_block_mechanics_do_not_change_the_selected_set(self):
        for order in itertools.permutations(self.G):
            base = walk(order, self.STATUS, 2, 1)["selected"]
            for b in (2, 4, 6):
                self.assertEqual(walk(order, self.STATUS, 2, b)["selected"], base)

    def test_position_dependent_status_breaks_uniformity(self):
        counts = {}
        for order in itertools.permutations(self.G):
            st = dict(self.STATUS)
            st["g5"] = sc.IN_S if order[0] == "g5" else sc.EXCLUDED
            sel = frozenset(walk(order, st, 1, 1)["selected"])
            counts[sel] = counts.get(sel, 0) + 1
        self.assertNotEqual(len(set(counts.values())), 1)

    def test_prevalence_estimator_unbiased_naive_biased(self):
        G = ["a", "b", "c", "d", "e", "f", "g"]
        st = {g: (sc.IN_S if g in ("a", "c", "f") else sc.EXCLUDED) for g in G}
        unbiased, naive, total = Fraction(0), Fraction(0), 0
        for order in itertools.permutations(G):
            T = walk(order, st, 2, 1)["T"]
            unbiased += Fraction(1, T - 1)
            naive += Fraction(2, T)
            total += 1
        self.assertEqual(unbiased / total, Fraction(3, 7))
        self.assertNotEqual(naive / total, Fraction(3, 7))

    def test_exhaustion_floor_stop_conservation(self):
        G = [f"g{i:02d}" for i in range(30)]
        r = walk(G[::-1], {g: (sc.IN_S if i < 20 else sc.EXCLUDED) for i, g in enumerate(G)}, 24, 6)
        self.assertTrue(r["exhausted"])
        self.assertEqual((r["n_selected"], r["underpowered"]), (20, False))
        r = walk(G, {g: (sc.IN_S if i < 10 else sc.EXCLUDED) for i, g in enumerate(G)}, 24, 6)
        self.assertEqual((r["n_selected"], r["underpowered"]), (10, True))
        st = {g: (sc.IN_S if i % 2 == 0 else sc.EXCLUDED) for i, g in enumerate(G)}
        r = walk(G, st, 5, 6)
        self.assertEqual(r["screened"], 12)
        self.assertEqual([e["role"] for e in r["ledger"] if e["status"] == sc.IN_S].count("S_OVERSHOOT_NOT_SELECTED"), 1)
        self.assertEqual(r["conservation"], {"EXCLUDED": 6, "RESOLVED_ELIGIBLE": 6, "UNSCREENED": 18})

    def test_old_identity_states_are_not_accepted(self):
        with self.assertRaises(sc.ScreeningHalt):
            sc.screen(["a"], lambda bi, b: {"a": "STRUCTURAL_DUPLICATE"}, n_target=1, block_size=1)
        with self.assertRaises(sc.ScreeningHalt):
            sc.screen(["a"], lambda bi, b: {"a": "UNRESOLVED_IDENTITY"}, n_target=1, block_size=1)
        with self.assertRaises(sc.ScreeningHalt):
            sc.screen(["a", "b"], lambda bi, b: {"a": sc.IN_S}, n_target=1, block_size=2)


# ------------------------------------------------------------------ adjudication of the primary entry

PE = "APIs/x.com/1.0/openapi.yaml"


def full(**over):
    p = {k: "TRUE" for k in sc.INCLUSIONS}
    p.update({k: "FALSE" for k in sc.EXCLUSIONS + sc.TERMS})
    p.update({c: "FALSE" for c in sc.CATEGORIES})
    p["C02"] = "TRUE"
    p.update(over)
    return {"rdg": "x.com", "primary_entry": PE, "predicates": p, "fatal_stop": None, "deviation": False,
            "observed_relationships": []}


def early(fatal):
    code = "FALSE" if fatal.startswith("INCLUSION_FALSE:") else "TRUE"
    pred = fatal.split(":", 1)[1] if fatal.startswith("INCLUSION_FALSE:") else fatal
    return {"rdg": "x.com", "primary_entry": PE, "predicates": {pred: code}, "fatal_stop": fatal, "deviation": False}


class CombinationTests(NetworkBan):
    def test_agreed_eligible_and_disagreement(self):
        self.assertEqual(sc.combine(full(), full(), PE)[0], sc.IN_S)
        st, why = sc.combine(full(), full(I0="UNRESOLVED"), PE)
        self.assertEqual(st, sc.UNRESOLVED_ELIGIBILITY)
        self.assertIn("I0:NOT_AGREED_TRUE", why)

    def test_no_adjudicator_choice_of_primary_entry(self):
        other = full()
        other["primary_entry"] = "APIs/x.com/2.0/openapi.yaml"      # an 'easier' entry of the same RDG
        st, why = sc.combine(other, full(), PE)
        self.assertEqual((st, why), (sc.UNRESOLVED_ELIGIBILITY, ["NOT_THE_PRIMARY_ENTRY"]))
        both = copy.deepcopy(other)
        self.assertEqual(sc.combine(both, other, PE)[0], sc.UNRESOLVED_ELIGIBILITY)

    def test_fatal_rules(self):
        self.assertEqual(sc.combine(early("E1"), early("E1"), PE), (sc.EXCLUDED, ["E1"]))
        self.assertEqual(sc.combine(early("INCLUSION_FALSE:I0"), early("INCLUSION_FALSE:I0"), PE)[0], sc.EXCLUDED)
        self.assertEqual(sc.combine(early("E1"), early("E3"), PE)[0], sc.UNRESOLVED_ELIGIBILITY)
        st, why = sc.combine(early("T2"), full(), PE)
        self.assertEqual(st, sc.UNRESOLVED_ELIGIBILITY)
        self.assertIn("UNILATERAL_FATAL_STOP", why)
        with self.assertRaises(sc.ScreeningHalt):
            sc.combine({"primary_entry": PE, "predicates": {"E1": "UNRESOLVED"}, "fatal_stop": "E1"}, full(), PE)

    def test_terms_scope_categories_deviation(self):
        self.assertEqual(sc.combine(full(T1="TRUE"), full(T1="TRUE"), PE)[0], sc.EXCLUDED)
        self.assertEqual(sc.combine(full(T3="UNRESOLVED"), full(T3="UNRESOLVED"), PE)[0], sc.UNRESOLVED_ELIGIBILITY)
        none = {c: "FALSE" for c in sc.CATEGORIES}
        self.assertEqual(sc.combine(full(**none), full(**none), PE), (sc.EXCLUDED, ["SCOPE_OUTSIDE"]))
        a = full(C05="UNRESOLVED")
        self.assertEqual(sc.combine(a, full(), PE)[0], sc.IN_S)
        self.assertEqual(sc.descriptive_categories(a, full())["vector"], "INCOMPLETE")
        d = full()
        d["deviation"] = True
        self.assertEqual(sc.combine(d, full(), PE), (sc.UNRESOLVED_ELIGIBILITY, ["PROTOCOL_DEVIATION"]))

    def test_fatal_stop_cannot_change_S_membership(self):
        rng = random.Random(20260919)
        states = ("TRUE", "FALSE", "UNRESOLVED")
        keys = sc.INCLUSIONS + sc.EXCLUSIONS + sc.TERMS + sc.CATEGORIES
        for _ in range(20000):
            f = rng.choice(sc.FATAL)
            pred = f.split(":", 1)[1] if f.startswith("INCLUSION_FALSE:") else f
            affirmed = "FALSE" if f.startswith("INCLUSION_FALSE:") else "TRUE"
            other = {"primary_entry": PE, "predicates": {k: rng.choice(states) for k in keys}}
            completion = {k: rng.choice(states) for k in keys}
            completion[pred] = rng.choice((affirmed, "UNRESOLVED"))
            self.assertNotEqual(sc.combine({"primary_entry": PE, "predicates": completion}, other, PE)[0], sc.IN_S)
            self.assertNotEqual(sc.combine(early(f), other, PE)[0], sc.IN_S)
            self.assertNotEqual(sc.combine(other, early(f), PE)[0], sc.IN_S)


class NoIdentityOperationTests(NetworkBan):
    def test_relationships_are_descriptive_only(self):
        a, b = full(), full()
        rel = {"rdg": "xcloud.com", "relation": "same control plane"}
        a2, b2 = copy.deepcopy(a), copy.deepcopy(b)
        a2["observed_relationships"] = [rel]
        b2["observed_relationships"] = [rel]
        self.assertEqual(sc.combine(a, b, PE), sc.combine(a2, b2, PE))
        self.assertEqual(sc.descriptive_relationships(a2, b2), [rel])

    def test_related_rdgs_both_kept_no_dedup_no_replacement(self):
        G = ["a.com", "x.com", "xcloud.com", "z.com"]
        st = {g: sc.IN_S for g in G}
        r = walk(["x.com", "xcloud.com", "a.com", "z.com"], st, 2, 1)
        self.assertEqual(r["selected"], ["x.com", "xcloud.com"])   # same vendor: both kept
        self.assertEqual(r["n_selected"], 2)

    def test_no_identity_merge_dedup_or_collapse_code(self):
        src = (HERE / "a1_screening.py").read_text().split('"""', 2)[2].lower()
        for token in ("resolve_component", "designated", "structural_duplicate", "unresolved_identity", "merge",
                      "dedup", "collapse", "replace", "reserve", "vendor"):
            self.assertNotIn(token, src, token)
        est = json.loads((HERE / "estimand.json").read_text())
        self.assertIn("No vendor-collapsed or vendor-level estimator is defined or permitted.", est["cross_domain_relationships"])


# ------------------------------------------------------------------ RDG frame and primary entry

class RDGFrameTests(NetworkBan):
    def group(self, frame, rdg):
        return next(g for g in frame["groups"] if g["rdg"] == rdg)

    def test_edge_cases_1_to_9_and_14_15(self):
        keys = ["vendor.com", "api.vendor.com", "vendor.com:payments",        # 1, 2, 4, 15
                "api.other.com", "eu.other.com",                               # 3
                "svc.com:alpha", "svc.com:beta",                               # 4 (no bare key)
                "ported.com:8443",                                             # 5
                "Case.COM.",                                                   # 6
                "bücher.de", "xn--bcher-kva.de",                               # 7
                "192.0.2.1", "[2001:db8::1]",                                  # 8
                "localhost", "co.uk", "a.github.io", "b.github.io",            # 9, public suffix, PSL private
                "bad_label.com"]
        paths = {f"APIs/{k}/1.0/openapi.yaml": b"servers: [{url: 'https://unrelated.example.net'}]" for k in keys}  # 14
        paths["APIs/vendor.com/0.9/swagger.json"] = b"{}"
        d, c = tree_repo(paths)
        frame, raw = fr.build_frame(d, PINNED_PSL, commit=c)
        g = self.group(frame, "vendor.com")
        self.assertEqual(g["keys"], ["api.vendor.com", "vendor.com", "vendor.com:payments"])
        self.assertEqual((g["primary_key"], g["primary_key_rule"]), ("vendor.com", "BARE_REGISTRABLE_DOMAIN"))
        self.assertEqual(g["primary_entry"], "APIs/vendor.com/0.9/swagger.json")
        self.assertEqual(self.group(frame, "other.com")["primary_key"], "api.other.com")
        g = self.group(frame, "svc.com")
        self.assertEqual((g["primary_key"], g["primary_key_rule"]), ("svc.com:alpha", "BYTE_SMALLEST_KEY"))
        self.assertEqual(self.group(frame, "ported.com")["primary_key"], "ported.com:8443")
        self.assertEqual(self.group(frame, "case.com")["keys"], ["case.com"])
        g = self.group(frame, "xn--bcher-kva.de")
        self.assertEqual(g["keys"], ["bücher.de", "xn--bcher-kva.de"])
        self.assertEqual(g["primary_key"], "bücher.de")
        for k, why in (("192.0.2.1", "IP_LITERAL"), ("[2001:db8::1]", "IP_LITERAL"), ("localhost", "NON_DNS_HOST"),
                       ("co.uk", "HOST_IS_PUBLIC_SUFFIX"), ("bad_label.com", "INVALID_DNS_LABEL")):
            g = self.group(frame, "singleton:" + k)
            self.assertEqual((g["basis"], g["primary_key_rule"]), ("SINGLETON_" + why, "SINGLETON"))
        self.assertIn("a.github.io", frame["G"])
        self.assertIn("b.github.io", frame["G"])
        self.assertNotIn("unrelated.example.net", json.dumps(frame))

    def test_conservation_and_exclusions(self):
        d, c = tree_repo(["APIs/a.com/1/openapi.yaml", "APIs/b.a.com/1/swagger.yaml", "APIs/empty.com/README.md",
                          "APIs/stray.txt", "README.md"])
        frame, raw = fr.build_frame(d, PINNED_PSL, commit=c)
        self.assertEqual(frame["G"], ["a.com"])
        self.assertEqual(frame["raw_entry_count"], 2)
        self.assertEqual({e["entry"]: e["rule"] for e in frame["structural_exclusions"]},
                         {"APIs/stray.txt": "XS1_NOT_A_PROVIDER_DIRECTORY", "APIs/empty.com": "XS2_NO_SPEC_FILE"})
        for mutate in (lambda f: f["groups"][0].update(raw_entries=9),
                       lambda f: f["groups"][0].update(primary_entry="APIs/b.a.com/1/swagger.yaml"),
                       lambda f: f["groups"][0].update(primary_key="zzz"),
                       lambda f: f.update(G=["b", "a"])):
            bad = copy.deepcopy(frame)
            mutate(bad)
            with self.assertRaises(fr.FrameHalt):
                fr.validate_frame(bad, raw)

    def test_primary_entry_deterministic_and_frame_reproducible(self):
        paths = ["APIs/b.com/2.0/openapi.yaml", "APIs/b.com/1.0/openapi.yaml", "APIs/api.b.com/1/openapi.json"]
        d1, c1 = tree_repo(paths)
        d2, c2 = tree_repo(list(reversed(paths)))
        f1, _ = fr.build_frame(d1, PINNED_PSL, commit=c1)
        f2, _ = fr.build_frame(d2, PINNED_PSL, commit=c2)
        self.assertEqual(c1, c2)
        self.assertEqual(fr.canonical(f1), fr.canonical(f2))
        self.assertEqual(f1["groups"][0]["primary_entry"], "APIs/b.com/1.0/openapi.yaml")
        self.assertTrue(fr.verify_frame(f1, d1, PINNED_PSL, commit=c1))

    def test_frame_fails_if_snapshot_or_psl_differs(self):
        d, c = tree_repo(["APIs/a.com/1/openapi.yaml"])
        frame, _ = fr.build_frame(d, PINNED_PSL, commit=c)
        d2, c2 = tree_repo(["APIs/a.com/1/openapi.yaml", "APIs/b.com/1/openapi.yaml"])
        with self.assertRaises(fr.FrameHalt):
            fr.verify_frame(frame, d2, PINNED_PSL, commit=c2)
        tampered = copy.deepcopy(frame)
        tampered["G"] = ["a.com", "b.com"]
        with self.assertRaises(fr.FrameHalt):
            fr.verify_frame(tampered, d, PINNED_PSL, commit=c)
        with self.assertRaises(fr.FrameHalt) as ctx:
            fr.build_frame(d, PINNED_PSL + b"\nevil.example\n", commit=c)
        self.assertEqual(ctx.exception.code, "PSL_MISMATCH")
        synthetic = b"com\n"
        f3, _ = fr.build_frame(d, synthetic, commit=c, psl_sha256=fr.sha256(synthetic))
        with self.assertRaises(fr.FrameHalt) as ctx:
            fr.verify_frame(f3, d, PINNED_PSL, commit=c)
        self.assertEqual(ctx.exception.code, "FRAME_INPUTS_MISMATCH")

    def test_fixed_psl_dependency(self):
        self.assertEqual(fr.sha256(PINNED_PSL), fr.PSL_SHA256)
        self.assertEqual(len(PINNED_PSL), 334040)
        with tempfile.NamedTemporaryFile(delete=False) as t:
            t.write(PINNED_PSL[:-1])
        with self.assertRaises(fr.FrameHalt):
            fr.load_pinned_psl(t.name)
        src = (HERE / "a1_frame.py").read_text()
        self.assertNotIn("psl_commit_at_t0", src)                      # no live PSL resolution
        self.assertNotIn("publicsuffix.org", src)

    def test_psl_rules_real(self):
        psl = fr.PublicSuffixList(PINNED_PSL.decode())
        self.assertEqual(psl.registrable_domain("a.b.example.co.uk"), "example.co.uk")
        self.assertEqual(psl.registrable_domain("x.y.github.io"), "y.github.io")
        self.assertIsNone(psl.registrable_domain("co.uk"))

    def test_snapshot_date_rule_and_retrieval_once(self):
        d, c = tree_repo(["APIs/a.com/1/openapi.yaml"])
        self.assertEqual(fr.verify_snapshot(d, commit=c)["commit"], c)
        d2, c2 = tree_repo(["APIs/a.com/1/openapi.yaml"], date="2026-09-17T00:00:01Z")
        with self.assertRaises(fr.FrameHalt):
            fr.verify_snapshot(d2, commit=c2)
        out = Path(tempfile.mkdtemp()) / "snap"
        out.mkdir()
        with self.assertRaises(FileExistsError):
            fr.retrieve(tempfile.mkdtemp(), out, source_repo="/nonexistent")

    def test_pinned_constants(self):
        self.assertEqual(fr.SNAPSHOT_COMMIT, "f04b8d0bcd39c52e1cf3ad7a5fe744709832ae49")
        self.assertEqual(fr.PSL_COMMIT, "3955e3ec29b94c3cca7bd4509c5f14a7c0959e26")
        self.assertEqual((sc.N_TARGET, sc.FLOOR, sc.RUNS_PER_PLATFORM, pm.BLOCK_SIZE), (24, 16, 5, 6))


class EvidenceLeadTests(NetworkBan):
    def test_server_url_edge_cases_10_to_13(self):
        doc = {"openapi": "3.0.0",
               "info": {"x-origin": [{"url": "https://Vendor.COM/openapi.yaml?utm_source=x&b=2&a=1#frag"}],
                        "termsOfService": "/terms", "contact": {"url": 5}},
               "externalDocs": {"url": "HTTPS://docs.vendor.com:443/guide/"},
               "servers": [{"url": "https://api.vendor.com/v1"}, {"url": "https://eu.vendor.com:8443/v1"},
                           {"url": "/relative"}, {"url": "https://{region}.vendor.com", "variables": {"region": {"default": "us"}}},
                           {"url": "https://{tenant}.vendor.com"}, {"url": "http://127.0.0.1:8080"},
                           {"url": "http://localhost/api"}, {"url": "ht!tp://bad"}, {"url": ""}, "not-a-dict"]}
        out = ev.e2_leads(doc)
        self.assertEqual(out["leads"], ["https://api.vendor.com/v1", "https://docs.vendor.com/guide",
                                        "https://eu.vendor.com:8443/v1", "https://us.vendor.com/",
                                        "https://vendor.com/openapi.yaml?a=1&b=2"])
        reasons = sorted(d["reason"] for d in out["dropped"])
        self.assertEqual(reasons, sorted(["RELATIVE_OR_NON_HTTP", "EMPTY_OR_NOT_STRING", "RELATIVE_OR_NON_HTTP",
                                          "UNRESOLVED_TEMPLATE", "IP_LITERAL_HOST", "NON_DNS_HOST",
                                          "RELATIVE_OR_NON_HTTP", "EMPTY_OR_NOT_STRING"]))

    def test_swagger2_and_missing(self):
        out = ev.e2_leads({"swagger": "2.0", "host": "api.v.com", "basePath": "/v2", "schemes": ["https", "http"]})
        self.assertEqual(out["leads"], ["http://api.v.com/v2", "https://api.v.com/v2"])
        self.assertEqual(ev.e2_leads({}), {"leads": [], "dropped": []})
        self.assertEqual(ev.e2_leads("not a dict"), {"leads": [], "dropped": []})

    def test_leads_never_influence_grouping(self):
        a = frame_for(["a.com"])
        d, c = tree_repo({"APIs/a.com/1.0/openapi.yaml": b"servers: [{url: 'https://z.org'}]"})
        b, _ = fr.build_frame(d, PINNED_PSL, commit=c)
        self.assertEqual((a["G"], a["groups"][0]["primary_entry"]), (b["G"], b["groups"][0]["primary_entry"]))


# ------------------------------------------------------------------ estimators and permutation

class EstimatorTests(NetworkBan):
    def test_half_widths_and_band(self):
        self.assertAlmostEqual(sc.half_width(24), 0.39205, places=4)
        r = sc.primary([(5, 5), (0, 5), (0, 0)])
        self.assertEqual((r["indeterminate"], r["estimate"]), (1, 0.5))
        e = sc.half_width(3)
        self.assertAlmostEqual(r["band"][1], min(1.0, 2 / 3 + e))

    def test_unknown_runs_excluded_not_failures(self):
        self.assertEqual(sc.rdg_rate(3, 4), 0.75)       # 5 attempts, 1 UNKNOWN: 3/4, not 3/5
        self.assertIsNone(sc.rdg_rate(0, 0))
        self.assertEqual(sc.prevalence_unbiased(24, 159), 23 / 158)


class PermutationTests(NetworkBan):
    def test_generator_single_call_exact_length(self):
        calls = []

        def fake(n):
            calls.append(n)
            return bytes(n)
        self.assertEqual(len(pm.generate_tape(10, entropy=fake)), 320)
        self.assertEqual(calls, [320])
        with self.assertRaises(pm.PermutationHalt):
            pm.generate_tape(10, entropy=lambda n: b"\0" * (n - 1))

    def test_mapping_ties_commitment(self):
        G = ["a", "b", "c"]
        tape = (3).to_bytes(32, "big") + (1).to_bytes(32, "big") + (2).to_bytes(32, "big")
        self.assertEqual(pm.permutation(G, tape, pm.tape_commitment(tape)), ["b", "c", "a"])
        tie = (7).to_bytes(32, "big") * 2
        for args in ((["a", "b"], tie, pm.tape_commitment(tie)), (["a", "b"], tape[:64], "0" * 64),
                     (["b", "a"], tape[:64], pm.tape_commitment(tape[:64])), (G, tape[:-1], pm.tape_commitment(tape[:-1]))):
            with self.assertRaises(pm.PermutationHalt):
                pm.permutation(*args)
        seen = set()
        for ranks in itertools.permutations(range(4)):
            t = b"".join(r.to_bytes(32, "big") for r in ranks)
            seen.add(tuple(pm.permutation(list("abcd"), t, pm.tape_commitment(t))))
        self.assertEqual(len(seen), 24)

    def test_permutation_is_over_rdgs_of_a_frame(self):
        frame = frame_for(["a.com", "api.a.com", "b.com"])
        G = frame["G"]
        tape = b"".join(r.to_bytes(32, "big") for r in (2, 1))
        self.assertEqual(pm.permutation(G, tape, pm.tape_commitment(tape)), ["b.com", "a.com"])
        with self.assertRaises(pm.PermutationHalt):                    # a key-level tape cannot be used
            pm.permutation(G, tape + (3).to_bytes(32, "big"), pm.tape_commitment(tape + (3).to_bytes(32, "big")))


# ------------------------------------------------------------------ hostile static and package

class HostileStaticTests(NetworkBan):
    OPERATIVE = ("a1_frame.py", "a1_permutation.py", "a1_screening.py", "a1_evidence.py", "prior_firstcall_projector.py")

    def test_no_search_engine_or_discovery_code(self):
        for name in self.OPERATIVE:
            src = (HERE / name).read_text().lower()
            for token in ("bing", "search/repositories", "api.github.com/search", "duckduckgo", "b_algo"):
                self.assertNotIn(token, src)

    def test_no_network_clients_in_pure_modules(self):
        for name in ("a1_permutation.py", "a1_screening.py", "a1_evidence.py"):
            src = (HERE / name).read_text()
            for token in ("urllib.request", "http.client", "requests", "socket"):
                self.assertNotIn(token, src)

    def test_entropy_only_in_registered_generator(self):
        for name in self.OPERATIVE:
            code = (HERE / name).read_text().split('"""', 2)[2]
            if name == "a1_permutation.py":
                self.assertEqual(code.count("urandom"), 1)
            else:
                self.assertNotIn("urandom", code)

    def test_frame_never_reads_definition_contents(self):
        src = (HERE / "a1_frame.py").read_text()
        self.assertNotIn("cat-file", src.replace('"cat-file", "-t"', ""))
        self.assertNotIn("json.loads(git", src)

    def test_no_a1_artifacts(self):
        for p in ("snapshot", "entropy", "permutation", "screening", "sample"):
            self.assertFalse((HERE / p).exists(), p)
        self.assertEqual([p.name for p in HERE.glob("*tape*")], [])


class PackageTests(NetworkBan):
    def test_supersession_rows_complete(self):
        doc = json.loads((HERE / "supersession.json").read_text())
        fields = {"id", "old_rule", "source_clause", "new_rule", "why_changed", "when_discovered",
                  "evidence_observed_before_change", "bias_risk", "status"}
        for row in doc["rows"]:
            self.assertTrue(fields <= set(row) <= fields | {"superseded_by"}, row["id"])
            self.assertTrue(all(row[f] for f in fields), row["id"])
            self.assertIn(row["status"], ("SUPERSEDED", "SUPERSEDED_NON_OPERATIVE", "RETAINED_MODIFIED", "NEW_RULE",
                                          "WITHDRAWN_PRE_SEAL"))
            if row["status"] == "WITHDRAWN_PRE_SEAL":
                self.assertIn(row["superseded_by"], {r["id"] for r in doc["rows"]})
        ids = {r["id"] for r in doc["rows"]}
        self.assertTrue({"SUP-38", "SUP-39", "SUP-40", "SUP-41", "SUP-42"} <= ids)
        sup38 = next(r for r in doc["rows"] if r["id"] == "SUP-38")
        for fact in ("5/7", "20/21", "5/6", "3/4", "P(D2)=0"):
            self.assertIn(fact, sup38["why_changed"])
        self.assertEqual(va.supersession_coverage_errors(doc), [])

    def test_roles_gates_fail_closed(self):
        roles = json.loads((HERE / "roles.json").read_text())
        self.assertTrue(all(v == "CLOSED" for v in va.gate_status(roles, anchored=False).values()))
        gates = va.gate_status(roles, anchored=True)
        self.assertEqual((gates["G0_ANCHOR"], gates["G1_SNAPSHOT"]), ("OPEN", "OPEN"))
        for g in ("G2_REGISTRY", "G3_ENTROPY", "G4_SCREENING", "G5_EXECUTION"):
            self.assertEqual(gates[g], "CLOSED")

    def test_role_conflicts_detected(self):
        roles = json.loads((HERE / "roles.json").read_text())
        r = {x["id"]: x for x in roles["roles"]}
        r["R03"].update(status="FILLED", holder="Ross Buckley")
        self.assertTrue(va.role_conflicts(roles))
        roles = json.loads((HERE / "roles.json").read_text())
        r = {x["id"]: x for x in roles["roles"]}
        r["R05"].update(status="FILLED", holder="A Person")
        r["R06"].update(status="FILLED", holder="a  person")
        self.assertTrue(va.role_conflicts(roles))

    def test_protocol_and_estimand_wording(self):
        p = json.loads((HERE / "decision-protocol.json").read_text())
        self.assertEqual(sorted(p["fatal_exclusion_stop"]["fatal_predicates"]), sorted(sc.FATAL))
        self.assertNotIn("identity_stage", p["navigation"])
        self.assertIn("no_substitution", p["evidence_hierarchy"])
        e = json.loads((HERE / "estimand.json").read_text())
        self.assertIn("registrable-domain groups", e["primary_estimand"])
        self.assertNotIn("vendor platform", e["primary_estimand"])
        self.assertIn("An RDG is a structural sampling unit, not a vendor.", e["unit_statement"])
        self.assertIn("correlation_limitation", e["uncertainty"])

def make_repo(files):
    d = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    for path, text in files.items():
        p = d / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    subprocess.run(["git", "-C", str(d), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                    "commit", "-q", "-m", "fixture"], check=True)
    return d, subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], check=True,
                             capture_output=True).stdout.decode().strip()


class ProjectorTests(unittest.TestCase):
    def test_grammar_and_exclusions(self):
        repo, commit = make_repo({
            "experiments/x/config.json": json.dumps({"experiment": "EXP-9", "vendor": "Alpha Mail",
                                                     "firstcall_operated": True,
                                                     "runner": "firstcall/run_alpha.py"}),
            "experiments/x/receipt.json": json.dumps({"experiment": "EXP-9", "vendor": "Leaky", "grade": "FAIL"}),
            "experiments/y/plain.json": json.dumps({"vendor_id": "Beta"}),
            "docs/design.md": "Experiment: EXP-10\n\n## 2. Targets\n\n| Vendor | Result |\n|---|---|\n| Gamma | SECRET |\n\n## Results\nVendor: NotThis\n",
            "docs/other.md": "# Target selection\ntext\n",
            "firstcall/run_alpha.py": "print('never executed')\n",
            "artifacts/z.json": json.dumps({"experiment": "E", "vendor": "Out"}),
        })
        r = pj.project(repo, commit)
        self.assertEqual([e["path"] for e in r["ledger"]], sorted((e["path"] for e in r["ledger"]), key=str.encode))
        pos = {(d["path"], d["identity"]) for d in r["positive_json_designations"]}
        self.assertEqual(pos, {("experiments/x/config.json", "Alpha Mail")})
        self.assertTrue(r["positive_json_designations"][0]["firstcall_operated"])
        md = r["positive_markdown_designations"]
        self.assertEqual([(d["path"], d["vendor_column_values"]) for d in md], [("docs/design.md", ["Gamma"])])
        dumped = json.dumps(r)
        for secret in ("SECRET", "Leaky", "NotThis", "FAIL", "Out"):
            self.assertNotIn(secret, dumped)
        reasons = {(u["path"], u["reason"]) for u in r["unrecognized_designations"]}
        self.assertIn(("experiments/y/plain.json", "IDENTITY_KEY_WITHOUT_SAME_LEVEL_EXPERIMENT"), reasons)
        self.assertIn(("docs/other.md", "NON_GRAMMAR_TARGET_HEADING"), reasons)
        self.assertEqual(r["status"], "BLOCKED_UNRECOGNIZED_DESIGNATION")
        cls = {e["path"]: e["class"] for e in r["ledger"]}
        self.assertEqual(cls["experiments/x/receipt.json"], "EXCLUDED_RESULT_OR_EVIDENCE_CONTEXT")
        self.assertEqual(cls["artifacts/z.json"], "OUT_OF_PROJECTION_SCOPE_S8_4")
        self.assertEqual(cls["firstcall/run_alpha.py"], "CODE_PATH_ONLY")
        cfg = next(e for e in r["ledger"] if e["path"] == "experiments/x/config.json")
        self.assertEqual(cfg["literal_code_path_references"], ["firstcall/run_alpha.py"])
        self.assertEqual(r["adjudicator_approvals"], {"ADJ-1": None, "ADJ-2": None})

    def test_hostile_designation_cases(self):
        repo, commit = make_repo({
            # incidental vendor mention in a config (not a target key)
            "experiments/a/config.json": json.dumps({"experiment": "A-1", "notes": "compared against VendorNotes"}),
            # policy field: boolean/null vendor-named keys cannot carry an identity
            "experiments/b/policy.json": json.dumps({"experiment": "B-1", "independent_vendor_verification_required": True,
                                                     "target_timeout_override": None}),
            # actual experiment target
            "experiments/c/manifest.json": json.dumps({"experiment_id": "C-1", "target_vendor": "RealTarget"}),
            # renamed experiment (id string records history) is still positive
            "experiments/d/manifest.json": json.dumps({"experiment": "D-2 (formerly D-1)", "vendor_id": "RenamedTarget"}),
            # nested experiment: identity below the experiment object is not grammar -> blocks
            "experiments/e/manifest.json": json.dumps({"experiment": "E-1", "runs": [{"vendor": "NestedTarget"}]}),
            # policy-like key holding an identity-capable value -> blocks
            "experiments/f/policy.json": json.dumps({"experiment": "F-1", "provider_under_test": "HiddenTarget"}),
            # documentation example in a fenced block and in an example path
            "docs/guide.md": "Intro.\n\n```\nExperiment: X-1\n## Targets\nVendor: FencedExample\n```\n",
            "experiments/examples/sample.json": json.dumps({"experiment": "X-2", "vendor": "ExampleVendor"}),
            # vendor appearing in prose only
            "docs/prose.md": "# Notes\nWe read about Vendor: ProseOnly in passing and ProseTwo elsewhere.\n",
            # historical artifact and receipt contexts
            "artifacts/old/manifest.json": json.dumps({"experiment": "H-1", "vendor": "ArtifactVendor"}),
            "experiments/h/receipt.json": json.dumps({"experiment": "H-2", "vendor": "ReceiptVendor"}),
        })
        r = pj.project(repo, commit)
        pos = {(d["path"], d["identity"]) for d in r["positive_json_designations"]}
        self.assertEqual(pos, {("experiments/c/manifest.json", "RealTarget"),
                               ("experiments/d/manifest.json", "RenamedTarget")})
        self.assertEqual(r["positive_markdown_designations"], [])
        reasons = {(u["path"], u["reason"]) for u in r["unrecognized_designations"]}
        self.assertEqual(reasons, {
            ("experiments/e/manifest.json", "IDENTITY_KEY_WITHOUT_SAME_LEVEL_EXPERIMENT"),
            ("experiments/f/policy.json", "EXPERIMENT_OBJECT_WITH_NON_GRAMMAR_TARGET_KEY"),
            ("experiments/examples/sample.json", "DESIGNATION_SHAPE_IN_EXAMPLE_PATH"),
        })
        b = next(e for e in r["ledger"] if e["path"] == "experiments/b/policy.json")
        self.assertEqual([f["key"] for f in b["projection"]["incidental_non_identity_fields"]],
                         ["independent_vendor_verification_required", "target_timeout_override"])
        dumped = json.dumps(r)
        for leaked in ("VendorNotes", "FencedExample", "ExampleVendor", "ProseOnly", "ProseTwo",
                       "ArtifactVendor", "ReceiptVendor", "NestedTarget", "HiddenTarget"):
            self.assertNotIn(leaked, dumped)

    def test_clean_repo_is_draft_not_approved(self):
        repo, commit = make_repo({"experiments/x/config.json": json.dumps({"experiment": "E", "vendor": "A"})})
        r = pj.project(repo, commit)
        self.assertEqual(r["status"], "DRAFT_REQUIRES_TWO_ADJUDICATOR_APPROVAL")

    def test_deterministic(self):
        repo, commit = make_repo({"docs/a.md": "x", "experiments/b.json": "{}"})
        self.assertEqual(pj.canonical(pj.project(repo, commit)), pj.canonical(pj.project(repo, commit)))



if __name__ == "__main__":
    unittest.main(verbosity=1)
