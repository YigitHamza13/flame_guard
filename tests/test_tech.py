"""Wilson intervals, NTRS parsing, ingestion pipeline and fuzzy retrieval."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StatsTests(unittest.TestCase):
    def test_wilson_known_values(self):
        from src.stats import wilson
        for k, n, lo, hi in ((4, 4, 51, 100), (15, 17, 66, 97), (0, 1, 0, 79)):
            a, b = wilson(k, n)
            self.assertEqual((round(a * 100), round(b * 100)), (lo, hi))
        self.assertIsNone(wilson(0, 0))


class NtrsTests(unittest.TestCase):
    def test_parse_is_robust(self):
        from src.ntrs import parse
        payload = {"results": [
            {"id": 20010073996, "title": "SIBAL", "publications": [{"publicationDate": "2001-05-01T00:00"}],
             "downloads": [{"links": {"pdf": "/api/citations/20010073996/downloads/20010073996.pdf"}}]},
            {"id": "20170008805", "title": "Saffire-II"},
            {"title": "no id"}]}
        rows = parse(payload)
        self.assertEqual([r["id"] for r in rows], ["20010073996", "20170008805"])
        self.assertTrue(rows[0]["pdf"].startswith("https://ntrs.nasa.gov/"))
        self.assertEqual(rows[0]["date"], "2001-05-01")
        self.assertTrue(rows[1]["known"])
        self.assertEqual(parse({}), [])


@unittest.skipUnless(importlib.util.find_spec("pypdf"), "pypdf is a development dependency")
class IngestionTests(unittest.TestCase):
    def test_local_pdf_becomes_pending_candidates_with_matching_hash(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import ingest_ntrs
        with tempfile.TemporaryDirectory() as out:
            ingest_ntrs.main(["20170008805", "--pdf", str(ROOT / "sources/originals/20170008805.pdf"), "--out", out])
            rec = json.loads((Path(out) / "20170008805.json").read_text(encoding="utf-8"))
        review = json.loads((ROOT / "data/source_review.json").read_text(encoding="utf-8"))
        known = next(s["sha256"] for s in review["sources"] if s["id"] == "20170008805")
        self.assertEqual(rec["pdf_sha256"], known)
        self.assertTrue(rec["candidates"])
        self.assertTrue(all(c["human_approval"] == "pending" and c["page"] >= 1 for c in rec["candidates"]))


class RetrievalTests(unittest.TestCase):
    def test_word_forms_match(self):
        from src.research import _fuzzy
        self.assertEqual(_fuzzy({"flammable"}, {"flammability"}), 1.0)
        self.assertEqual(_fuzzy({"ignite"}, {"ignition"}), 1.0)
        self.assertEqual(_fuzzy({"neutrino"}, {"pressure", "flame", "ignition"}), 0.0)
