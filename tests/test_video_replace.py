"""replace_with_retry: a video that a player still holds is tried again before giving up (no `._ttc_tmp.mp4` left behind)."""
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(os.path.dirname(HERE), "PKStudio.py"), encoding="utf-8").read()
NS = {}
exec(SRC[SRC.index("# ==== CORE-BEGIN"):SRC.index("# ==== CORE-END")], NS)
retry = NS["replace_with_retry"]


class ReplaceWithRetry(unittest.TestCase):
    def test_succeeds_after_the_file_is_released(self):
        calls, waits = [], []

        def replace(a, b):
            calls.append((a, b))
            if len(calls) < 3:
                raise PermissionError("in use")
        self.assertTrue(retry("tmp", "dst", tries=6, delay_s=0.5, replace=replace, sleep=waits.append))
        self.assertEqual(len(calls), 3)
        self.assertEqual(waits, [0.5, 0.5])                    # it waited between the tries, not after the last one

    def test_gives_up_after_the_last_try(self):
        waits = []

        def replace(a, b):
            raise PermissionError("in use")
        self.assertFalse(retry("tmp", "dst", tries=4, delay_s=1.0, replace=replace, sleep=waits.append))
        self.assertEqual(waits, [1.0, 1.0, 1.0])

    def test_single_try_does_not_wait(self):
        waits = []
        self.assertFalse(retry("a", "b", tries=1, replace=lambda a, b: (_ for _ in ()).throw(OSError("x")), sleep=waits.append))
        self.assertEqual(waits, [])

    def test_really_replaces_a_file(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "a.tmp"), os.path.join(d, "b.mp4")
            open(src, "w").write("new")
            open(dst, "w").write("old")
            self.assertTrue(retry(src, dst))
            self.assertEqual(open(dst).read(), "new")
            self.assertFalse(os.path.exists(src))


if __name__ == "__main__":
    unittest.main()
