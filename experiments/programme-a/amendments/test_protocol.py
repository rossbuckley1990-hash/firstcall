"""Offline adversarial protocol-composition tests; no frame construction or draw."""
import copy
import importlib.util
import hashlib
import math
import pathlib
import unittest
from fractions import Fraction

PATH = pathlib.Path(__file__).with_name("apply_protocol.py")
spec = importlib.util.spec_from_file_location("protocol_overlay", PATH)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.a = p.loads(PATH.with_name("freeze-1.1.json").read_bytes())
        self.originals = {name: p.loads((p.ROOT / name).read_bytes())
                          for name in p.PARENT_PATHS if name.endswith(".json")}

    def test_repeatable_composition_does_not_mutate_parent(self):
        before = copy.deepcopy(self.originals)
        first = p.compose(self.a, self.originals)
        self.assertEqual(p.canonical(first), p.canonical(p.compose(self.a, self.originals)))
        self.assertEqual(self.originals, before)

    def test_changed_parent_value_fails_patch_precondition(self):
        self.originals[p.BASE + "sample-frame.config.json"]["categories_min"] = 99
        with self.assertRaisesRegex(ValueError, "patch test failed"):
            p.compose(self.a, self.originals)

    def test_unguarded_or_overwriting_patch_rejected(self):
        for op in ({"op": "replace", "path": "/x", "value": 2},
                   {"op": "add", "path": "/x", "value": 2}):
            with self.assertRaises(ValueError):
                p.apply_patches({"x": 1}, [op])

    def test_duplicate_keys_and_non_json_numbers_rejected(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError):
                p.loads(value)

    def test_unknown_state_cannot_be_promoted_into_draw(self):
        self.a["rules"]["eligibility"]["unresolved_draw"] = True
        with self.assertRaisesRegex(ValueError, "unresolved promotion"):
            p.validate_rules(self.a)

    def test_category_count_and_source_selection_discretion_rejected(self):
        self.a["rules"]["category_assignment"]["depends_on_category_counts"] = True
        with self.assertRaisesRegex(ValueError, "category discretion"):
            p.validate_rules(self.a)
        self.setUp()
        self.a["rules"]["source_universe"]["take"] = "PREFERRED_SOURCE"
        with self.assertRaisesRegex(ValueError, "source cherry-picking"):
            p.validate_rules(self.a)

    def test_outcome_condition_and_seed_rejected(self):
        self.a["rules"]["prior_firstcall"]["known_outcome_condition"] = True
        with self.assertRaisesRegex(ValueError, "prior-outcome leakage"):
            p.validate_rules(self.a)
        self.setUp()
        self.a["rules"]["later_draw"]["seed_value"] = "FORBIDDEN_PLACEHOLDER"
        with self.assertRaisesRegex(ValueError, "draw or seed"):
            p.validate_rules(self.a)

    def test_embedded_rules_must_match_normative_rules(self):
        ops = self.a["json_patches"][p.BASE + "sample-frame.config.json"]
        for op in ops:
            if op["path"] == "/freeze_1_1_rules":
                op["value"]["eligibility"]["unresolved_draw"] = True
        with self.assertRaisesRegex(ValueError, "embedded rules diverge"):
            p.compose(self.a, self.originals)

    def test_reverse_exclusion_polarity_rejected(self):
        for op in self.a["json_patches"][p.BASE + "sample-frame.config.json"]:
            if op["op"] == "replace" and op["path"] == "/inclusion_rules/4":
                op["value"] = "FIRSTCALL-authored units are eligible"
        with self.assertRaisesRegex(ValueError, "polarity reversed"):
            p.compose(self.a, self.originals)

    def test_nonzero_activity_cannot_validate(self):
        self.a["outcome_observations"] = 1
        with self.assertRaisesRegex(ValueError, "outcome_observations"):
            p.validate_rules(self.a)

    def test_duplicate_or_malformed_category_ids_rejected(self):
        for bad in ("C01", "", "C08", "c02", None):
            self.setUp()
            self.a["rules"]["categories"][1]["id"] = bad
            with self.assertRaisesRegex(ValueError, "category IDs"):
                p.validate_rules(self.a)

    def test_abstract_category_argmin_is_order_independent(self):
        # Abstract digest preimage, not a candidate identity or constructed frame.
        domain = self.a["rules"]["category_assignment"]["input"][0]
        def choose(ids, digest=hashlib.sha256):
            return min(ids, key=lambda c: (digest(p.canonical([domain, "0" * 64, c])).digest(), c))
        ids = ["C01", "C02", "C07"]
        self.assertEqual(choose(ids), choose(list(reversed(ids))))
        class TiedDigest:
            def __init__(self, data):
                pass
            def digest(self):
                return b"\0" * 32
        self.assertEqual(choose(ids, TiedDigest), "C01")
        # Labels are absent from preimages; domains distinguish uses.
        self.assertNotEqual(p.canonical([domain, "0" * 64, "C01"]),
                            p.canonical(["FIRSTCALL-A-1.1-ID", "0" * 64, "C01"]))

    def test_source_capture_cannot_be_repeated_or_substituted(self):
        self.a["rules"]["source_universe"]["capture"]["attempts"] = 2
        with self.assertRaisesRegex(ValueError, "alternative source capture"):
            p.validate_rules(self.a)

    def test_census_must_precede_reveal(self):
        sequence = self.a["rules"]["sequence"]
        i = sequence.index("FREEZE_5A_BLINDED_CENSUS_SEAL")
        j = sequence.index("FREEZE_5B_REVEAL_VERIFY_MECHANICAL_REPLACEMENT")
        sequence[i], sequence[j] = sequence[j], sequence[i]
        with self.assertRaisesRegex(ValueError, "freeze order"):
            p.validate_rules(self.a)

    def test_prior_paths_and_identity_urls_cannot_alone_decide(self):
        self.a["rules"]["prior_firstcall"]["code_paths_alone_qualify"] = True
        with self.assertRaisesRegex(ValueError, "path/name-based"):
            p.validate_rules(self.a)
        self.setUp()
        self.a["rules"]["sampling_unit"]["anchor_difference_proves_distinct"] = True
        with self.assertRaisesRegex(ValueError, "URL-based"):
            p.validate_rules(self.a)

    def test_replacement_mirror_cannot_retain_old_reveal_order(self):
        for op in self.a["json_patches"][p.BASE + "sample-frame.config.json"]:
            if op["op"] == "replace" and op["path"] == "/replacements":
                op["value"]["reveal_after_census_seal"] = False
        with self.assertRaisesRegex(ValueError, "replacement overlay divergence"):
            p.compose(self.a, self.originals)

    def test_combinatorial_inclusion_identities_without_sampling(self):
        # Counts of hypothetical designs only: no RNG, permutations, vendors or draw.
        for population in range(2, 9):
            for seats in range(1, population + 1):
                total = math.comb(population, seats)
                self.assertEqual(Fraction(math.comb(population - 1, seats - 1), total),
                                 Fraction(seats, population))
                if seats >= 2:
                    self.assertEqual(Fraction(math.comb(population - 2, seats - 2), total),
                                     Fraction(seats * (seats - 1), population * (population - 1)))
            for retained in range(1, population + 1):
                extensions = math.comb(population, retained) * math.factorial(population - retained)
                self.assertEqual(extensions * math.factorial(retained), math.factorial(population))

    def test_priority_symmetry_by_counting_not_generating_priorities(self):
        alphabet, positions = 8, 3
        assignments_without_ties = math.prod(range(alphabet - positions + 1, alphabet + 1))
        assignments_per_order = math.comb(alphabet, positions)
        self.assertEqual(assignments_per_order * math.factorial(positions), assignments_without_ties)

    def test_primary_band_union_tail_and_singleton_do_not_degenerate(self):
        for C in (1.0, 1 / 24, 0.125):
            epsilon = math.sqrt(C * math.log(40))
            self.assertAlmostEqual(2 * math.exp(-epsilon * epsilon / C), 0.05)
            self.assertGreater(epsilon, 0)
        self.a["rules"]["analysis_consequence"]["bootstrap"] = "PRIMARY_95_PERCENT_CI"
        with self.assertRaisesRegex(ValueError, "bootstrap promoted"):
            p.validate_rules(self.a)

    def test_bootstrap_rejection_threshold_has_no_modulo_bias(self):
        # Small abstract word width suffices to test the counting identity.
        for bound in range(1, 25):
            limit = 256 - (256 % bound)
            counts = [sum(1 for x in range(limit) if x % bound == i) for i in range(bound)]
            self.assertEqual(len(set(counts)), 1)

    def test_no_stale_primary_interval_or_estimated_support(self):
        effective = p.compose(self.a, self.originals)
        self.assertIsInstance(effective[p.BASE + "analysis-plan.json"]["primary"]["interval"], dict)
        denominator = effective[p.BASE + "estimand.schema.json"]["primary_estimand"]["denominator"]
        self.assertIn("all G census-eligible", denominator)


if __name__ == "__main__":
    unittest.main()
