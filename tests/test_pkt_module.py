"""Checks that this repository is a valid module of PK Transport: manifest, plugin file, version bookkeeping."""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def manifest():
    with open(os.path.join(ROOT, "pkt_module.json"), encoding="utf-8") as f:
        return json.load(f)


class Manifest(unittest.TestCase):
    def test_fields(self):
        m = manifest()
        self.assertEqual((m["api"], m["id"], m["name"]), (1, "analyze", "PKT Analyze"))
        self.assertRegex(m["version"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(m["min_shell"], r"^\d+\.\d+\.\d+$")
        self.assertTrue(os.path.isfile(os.path.join(ROOT, m["plugin"])))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, m["requirements_file"])))

    def test_the_version_is_the_one_of_the_changelog(self):
        log = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
        rows = re.findall(r"(?m)^\| \*\*PKT-Analyze (\d+\.\d+\.\d+)\*\* \|", log)
        self.assertEqual(manifest()["version"], rows[-1])

    def test_the_plugin_file_has_the_api(self):
        src = open(os.path.join(ROOT, "pkt_plugin.py"), encoding="utf-8").read()
        self.assertRegex(src, r"(?m)^API = 1$")
        for fn in ("create", "summary", "recent", "texts"):
            self.assertRegex(src, rf"(?m)^def {fn}\(", fn)
        top = src.split("\n\nAPI = 1")[0] if "\n\nAPI = 1" in src else src
        heavy = re.findall(r"(?m)^(?:import|from)\s+(torch|ultralytics|cv2|numpy|matplotlib)\b", src)
        self.assertEqual(heavy, [], "pkt_plugin.py must stay light at the top (PK Transport imports it on its Home page)")


class Outputs(unittest.TestCase):
    """The results list of the Home card (find_analysis_outputs); the plugin is imported with a stand-in for the shell's theme module."""

    @classmethod
    def setUpClass(cls):
        import types
        for name in ("pkt", "pkt.ui", "pkt.ui.theme"):
            sys.modules.setdefault(name, types.ModuleType(name))
        sys.modules["pkt.ui.theme"].COLORS = {"bg": "#ffffff"}
        import importlib.util
        spec = importlib.util.spec_from_file_location("pkt_plugin_under_test", os.path.join(ROOT, "pkt_plugin.py"))
        cls.plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.plugin)

    def test_finds_result_folders_newest_first(self):
        import tempfile
        root = tempfile.mkdtemp(prefix="pkt_out_")
        old = os.path.join(root, "clipA", "run1")
        new = os.path.join(root, "clipB")
        for folder, video in ((old, "C:/x/clipA.mp4"), (new, "clipB.mp4")):
            os.makedirs(folder)
            with open(os.path.join(folder, "Run_Summary.json"), "w", encoding="utf-8") as f:
                json.dump({"video": video}, f)
        with open(os.path.join(new, "Summary.json"), "w", encoding="utf-8") as f:
            json.dump({"indicators": {"TTC": {"N": 4}, "PET": {"N": 2}}}, f)
        os.utime(os.path.join(old, "Run_Summary.json"), (1000, 1000))
        os.makedirs(os.path.join(root, "empty"))
        found = self.plugin.find_analysis_outputs(root)
        self.assertEqual([r["name"] for r in found], ["clipB", "run1"])
        self.assertEqual((found[0]["clip"], found[0]["ttc"], found[0]["pet"]), ("clipB.mp4", 4, 2))
        self.assertEqual((found[1]["clip"], found[1]["ttc"]), ("clipA.mp4", None))
        self.assertEqual(len(self.plugin.find_analysis_outputs(root, limit=1)), 1)
        self.assertEqual(self.plugin.find_analysis_outputs(os.path.join(root, "nope")), [])
        self.assertEqual(self.plugin.find_analysis_outputs(""), [])


class Lang(unittest.TestCase):
    def test_every_template_keeps_its_placeholders(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("pkt_analyze_lang", os.path.join(ROOT, "pkt_analyze_lang.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertGreater(len(mod.EXACT), 400)
        for src, dst in mod.TEMPLATES.items():
            self.assertEqual(sorted(re.findall(r"\{\d+\}", src)), sorted(re.findall(r"\{\d+\}", dst)), src)


if __name__ == "__main__":
    unittest.main()
