"""Unit tests for the pure-logic CORE region of PKStudio.py.

Run from the Run folder:   python -m unittest discover -s tests -v
(or: python -m pytest tests)

PKStudio.py starts a GUI/CUDA bootstrap when imported, so the tests exec only
the region between the CORE-BEGIN / CORE-END markers.
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "PKStudio.py")


def load_core():
    with open(SRC, encoding="utf-8") as f:
        text = f.read()
    begin = text.index("# ==== CORE-BEGIN")
    end = text.index("# ==== CORE-END ====")
    ns = {}
    exec(compile(text[begin:end], "PKStudio.py[CORE]", "exec"), ns)
    return ns


CORE = load_core()
clean = CORE["clean_zone_visits"]
seq_from = CORE["zone_sequence_from_samples"]
classify = CORE["classify_movement"]
PATTERNS = CORE["MOVEMENT_PATTERNS"]


class CleanZoneVisits(unittest.TestCase):
    def test_aba_flicker_removed(self):
        self.assertEqual(clean([("A", 0, 1), ("B", 1.02, 1.05), ("A", 1.07, 2)]), [("A", 0, 2)])

    def test_brief_exit_merged(self):
        self.assertEqual(clean([("A", 0, 1), ("A", 1.05, 2)]), [("A", 0, 2)])

    def test_real_reentry_kept(self):
        v = [("A", 0, 1), ("A", 1.5, 2)]
        self.assertEqual(clean(v), v)

    def test_real_transit_kept(self):
        v = [("1", 0, 1), ("6", 1.02, 1.04), ("5", 1.06, 2)]
        self.assertEqual(clean(v), v)

    def test_long_middle_kept(self):
        v = [("A", 0, 1), ("B", 1.02, 3), ("A", 3.02, 4)]
        self.assertEqual(clean(v), v)


class Patterns(unittest.TestCase):
    def test_six_movements(self):
        self.assertEqual(
            set(PATTERNS),
            {"1-3-4", "2-3-1", "1-3-6-7", "5-6-3-1", "2-3-4", "5-6-7"},
        )

    def test_id_matches_sequence(self):
        for mid, info in PATTERNS.items():
            self.assertEqual(mid, "-".join(str(z) for z in info["sequence"]))

    def test_no_pattern_inside_another(self):
        # otherwise an Exact match could also be read as a Partial of another pattern
        for a, ia in PATTERNS.items():
            for b, ib in PATTERNS.items():
                if a == b:
                    continue
                n = len(ia["sequence"])
                frags = [ib["sequence"][i:i + n] for i in range(len(ib["sequence"]) - n + 1)]
                self.assertNotIn(ia["sequence"], frags, (a, b))

    def test_main_road_flags(self):
        self.assertEqual({m for m, i in PATTERNS.items() if i["main_road"]}, {"2-3-4", "5-6-7"})
        self.assertEqual(PATTERNS["2-3-4"]["side"], "entry")
        self.assertEqual(PATTERNS["5-6-7"]["side"], "opposite")


class Classify(unittest.TestCase):
    def test_exact(self):
        for mid, info in PATTERNS.items():
            self.assertEqual(classify(info["sequence"]), (mid, "Exact"))

    def test_consecutive_duplicates_ignored(self):
        self.assertEqual(classify([2, 2, 3, 3, 4]), ("2-3-4", "Exact"))

    def test_partial_unique(self):
        self.assertEqual(classify([1, 3, 6]), ("1-3-6-7", "Partial"))
        self.assertEqual(classify([6, 3, 1]), ("5-6-3-1", "Partial"))
        self.assertEqual(classify([3, 6, 7]), ("1-3-6-7", "Partial"))

    def test_partial_ambiguous_never_guessed(self):
        for frag in ([3, 4], [2, 3], [1, 3], [6, 7], [5, 6], [3, 1]):
            self.assertEqual(classify(frag), ("", "Ambiguous"), frag)

    def test_unclassified(self):
        self.assertEqual(classify([4, 3]), ("", "Unclassified"))
        self.assertEqual(classify([2, 3, 6, 7]), ("", "Unclassified"))

    def test_insufficient(self):
        self.assertEqual(classify([3]), ("", "Insufficient"))
        self.assertEqual(classify([]), ("", "Insufficient"))


class SequenceFromSamples(unittest.TestCase):
    @staticmethod
    def run_samples(zones, dt=1 / 60):
        return [(i * dt, z) for i, z in enumerate(zones)]

    def test_simple_through(self):
        z = [2] * 30 + [3] * 30 + [4] * 30
        self.assertEqual(seq_from(self.run_samples(z)), [2, 3, 4])

    def test_boundary_flicker_removed(self):
        # 3 -> 2 -> 3 for one frame at the 2/3 border
        z = [2] * 30 + [3] * 5 + [2] + [3] * 30 + [4] * 30
        self.assertEqual(seq_from(self.run_samples(z)), [2, 3, 4])

    def test_brief_gap_outside_zones_merged(self):
        z = [1] * 20 + [None] * 2 + [1] * 20 + [3] * 20 + [4] * 20
        self.assertEqual(seq_from(self.run_samples(z)), [1, 3, 4])

    def test_long_gap_outside_zones_kept_as_reentry_then_deduped(self):
        z = [3] * 20 + [None] * 30 + [3] * 20
        self.assertEqual(seq_from(self.run_samples(z)), [3])

    def test_right_turn_through_conflict_zones(self):
        z = [1] * 40 + [3] * 20 + [6] * 20 + [7] * 40
        self.assertEqual(classify(seq_from(self.run_samples(z))), ("1-3-6-7", "Exact"))


if __name__ == "__main__":
    unittest.main()
