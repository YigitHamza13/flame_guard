import json
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from src.database import sync_store
from src.evidence import ROOT, family, load_datasets, material_keys, sample_rows, summary, evidence_gaps
from src.screening import condition_comparison, evidence_export, csv_bytes, research_brief


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tests, cls.maps, cls.catalog, cls.sources, cls.errors = load_datasets()

    def test_import_totals(self):
        self.assertEqual((len(self.tests), summary(self.tests)["tests"], len(self.catalog)), (11, 39, 26))
        self.assertFalse(self.errors)

    def test_disputed_sibal_not_counted(self):
        result = summary(sample_rows(self.tests, "pamuklu kumaş"))
        self.assertEqual(result["tests"], 27)
        self.assertIsNone(result["ignited"])

    def test_no_evidence_is_unknown(self):
        self.assertEqual(summary(sample_rows(self.tests, "plastik (pmma)")), {"tests": None, "ignited": None, "ratio": None})

    def test_wif_pressure_restored_with_scope(self):
        rows = sample_rows(self.tests, "kablo kılıfı")
        self.assertTrue(rows.pressure_kpa.eq(101.325).all())
        self.assertTrue(rows.raw_pressure_kpa.isna().all())
        self.assertTrue(rows.pressure_scope.notna().all())
        self.assertEqual(summary(rows)["ignited"], 4)

    def test_saffire_does_not_imply_sustained_burning(self):
        rows = sample_rows(self.tests, "kauçuk")
        self.assertTrue(rows.ignition.eq("local_gas_flame").all())
        self.assertTrue(rows.sustained.eq("not_observed").all())
        self.assertTrue(rows.propagation.eq("not_observed").all())
        self.assertIsNone(summary(rows)["ignited"])

    def test_gradflex_separate(self):
        self.assertEqual(family({"acronym": "GRADFLEX"}), "GRADFLEX")
        self.assertEqual(family({"acronym": "FLEX-2"}), "FLEX")

    def test_fluid_physics_retained(self):
        for r in self.catalog:
            if r.get("acronym") in ("GRADFLEX", "PBRE"):
                self.assertEqual(r["research_area"], "Fluid Physics")

    def test_pmma_separate_from_evidence(self):
        self.assertNotIn("plastik (pmma)", material_keys(self.tests, self.maps))

    def test_sources_are_pdf_pages(self):
        self.assertEqual(len(self.sources), 10)
        for source in self.sources:
            self.assertIn("#page=", source["url"])
            self.assertEqual(source["human_approval"], "pending")
            self.assertGreater(len(source["text"]), 50)

    def test_gaps_preserve_dispute(self):
        frame = evidence_gaps(self.tests, ["pamuklu kumaş", "plastik (pmma)"])
        self.assertIn("Disputed", frame.Status.values)
        self.assertIn("Unknown", frame.Status.values)

    def test_moon_comparison_does_not_use_completeness(self):
        result = condition_comparison(self.tests, "Moon Base", {"oxygen": 21, "pressure": 101.325})
        self.assertTrue(result.gravity_match.eq("different").all())
        self.assertNotIn("three_fields_equal", result.comparison.values)

    def test_assumptions_change_comparison(self):
        rows = sample_rows(self.tests, "kablo kılıfı")
        a = condition_comparison(rows, "ISS", {"oxygen": 21, "pressure": 101.325})
        b = condition_comparison(rows, "ISS", {"oxygen": 30, "pressure": 101.325})
        self.assertTrue(a.comparison.eq("three_fields_equal").all())
        self.assertTrue(b.comparison.eq("different_conditions").all())

    def test_unknown_assumptions_not_equal(self):
        result = condition_comparison(self.tests, "Mars Mission", {})
        self.assertTrue(result.gravity_match.eq("unknown").all())
        self.assertTrue(result.oxygen_match.eq("unknown").all())

    def test_export_keeps_filtered_and_absent_selections(self):
        result = evidence_export(self.tests, ["plastik (pmma)", "kablo kılıfı"], "Moon Base", {"oxygen": 19},
                                 {"oxygen_enabled": True, "oxygen_range": [0, 5]}, self.tests.attrs["snapshot"])
        self.assertEqual(len(result), 2)
        self.assertTrue(result.test_count.isna().all())
        # PMMA has no compiled rows; the cable has tests, but none inside 0–5 % O2.
        self.assertEqual(dict(zip(result.material, result.evidence_status)),
                         {"plastik (pmma)": "no_matching_evidence", "kablo kılıfı": "outside_filter"})
        self.assertTrue(result.snapshot_sha256.eq(self.tests.attrs["snapshot"]).all())
        self.assertTrue(result.assumed_oxygen_pct.eq(19).all())

    def test_csv_formula_input_neutralized(self):
        output = csv_bytes(pd.DataFrame({"phase": ["=1+1", " @SUM(A1)", "safe"]})).decode("utf-8-sig")
        self.assertIn("'=1+1", output)
        self.assertIn("' @SUM", output)

    def test_brief_has_source_pages(self):
        export = evidence_export(self.tests, ["kablo kılıfı", "plastik (pmma)"], "ISS", {}, {}, self.tests.attrs["snapshot"])
        text = research_brief(export)
        self.assertIn("#page=", text)
        self.assertIn("No matching evidence", text)
        self.assertIn(self.tests.attrs["snapshot"], text)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "data", self.root / "data", ignore=shutil.ignore_patterns("*.sqlite3*"))
        shutil.copytree(ROOT / "sources", self.root / "sources")
        self.raw = pd.read_csv(self.root / "data/experiments.csv")
        self.maps = pd.read_csv(self.root / "data/materials.csv")
        self.catalog = json.loads((self.root / "data/psi_combustion_investigations.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def sync(self):
        return sync_store(self.root, self.raw, self.maps, self.catalog, [])

    def test_lossless_and_idempotent(self):
        one, two = self.sync(), self.sync()
        self.assertEqual(one[-1], two[-1])
        with closing(sqlite3.connect(self.root / "data/flameguard.sqlite3")) as db:
            rows = [json.loads(r[0]) for r in db.execute("SELECT raw_json FROM test_groups ORDER BY id")]
            self.assertEqual(rows, json.loads(self.raw.to_json(orient="records", force_ascii=False)))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0], 1)
            self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())

    def test_changed_csv_invalidates_review(self):
        first = self.sync()
        path = self.root / "data/experiments.csv"
        path.write_bytes(path.read_bytes() + b"\n")
        second = self.sync()
        self.assertNotEqual(first[-1], second[-1])
        self.assertTrue(all(r["review_status"] == "pending" for r in second[0]))
        self.assertTrue(second[3])

    def test_changed_pdf_excluded_from_search(self):
        path = self.root / "sources/originals/20150008962.pdf"
        path.write_bytes(b"changed")
        result = self.sync()
        self.assertFalse(any(s["source_id"] == "20150008962" for s in result[2]))
        self.assertTrue(result[3])

    def test_changed_passages_disable_source_search(self):
        path = self.root / "data/primary_passages.json"
        path.write_text("[]", encoding="utf-8")
        result = self.sync()
        self.assertFalse(result[2])
        self.assertTrue(result[3])

    def test_concurrent_imports(self):
        self.sync()
        with ThreadPoolExecutor(max_workers=3) as pool:
            outputs = list(pool.map(lambda _: self.sync(), range(3)))
        self.assertEqual(len({o[-1] for o in outputs}), 1)


if __name__ == "__main__":
    unittest.main()
