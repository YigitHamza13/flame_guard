import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.evidence import load_datasets
from src.research import (ask_nasa_gemini, is_lunar, parse_model_response, relevant_passage,
                          setting, source_index, validated_selections)


class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, cls.catalog, cls.sources, _ = load_datasets()

    def test_lunar_variants(self):
        for question in ["Ayda yanma", "Ay’da malzeme", "Ay'da deney", "Moon?", "lunar habitat", "Ay yüzeyi"]:
            with self.subTest(question=question):
                self.assertTrue(is_lunar(question))
        self.assertFalse(is_lunar("layer and airway"))

    def test_future_manifest_unanswered(self):
        result = ask_nasa_gemini("Which material will go to Mars in 2030?", self.catalog, self.sources)
        self.assertFalse(result["answered"])
        self.assertFalse(result["excerpts"])
        self.assertEqual(result["notice"], "future_unanswered")

    def test_no_matching_source(self):
        result = ask_nasa_gemini("quantum neutrino oscillations", self.catalog, self.sources)
        self.assertEqual(result["notice"], "unanswered")

    def test_catalog_not_used_as_measured_findings(self):
        self.assertEqual(source_index(self.catalog, []), [])
        self.assertEqual(source_index([], [{"id": "summary", "text": "unsupported", "review_status": "pending"}]), [])

    def test_malformed_selection_shapes(self):
        for payload in [None, [], "oops", 4, {"excerpts": None}, {"excerpts": {}}, {"excerpts": ["bad", 2, None]},
                        {"excerpts": [{"id": [], "quote": {}}, {"id": "x", "quote": []}]}]:
            with self.subTest(payload=payload):
                self.assertEqual(validated_selections(payload, self.sources), [])

    def test_malformed_provider_envelopes(self):
        for payload in [None, [], {"candidates": None}, {"candidates": [None]}, {"candidates": [{"content": []}]},
                        {"candidates": [{"content": {"parts": [None, {"text": 3}]}}]}]:
            with self.subTest(payload=payload):
                self.assertIsNone(parse_model_response(payload))

    def test_verbatim_quotes_only(self):
        source = self.sources[0]
        quote = source["text"][:100]
        result = validated_selections({"excerpts": [{"id": source["id"], "quote": quote}]}, self.sources)
        self.assertEqual(result[0]["quote"], quote)
        self.assertEqual(validated_selections({"excerpts": [{"id": source["id"], "quote": "fabricated flight certification"}]}, self.sources), [])

    def test_relevant_pressure_passage(self):
        text = "Objectives. We studied a long list of unrelated subjects. Results. The pressure was 1 atm. Flow varied."
        quote = relevant_passage("What pressure was used?", text)
        self.assertIn("pressure was 1 atm", quote)
        self.assertFalse(quote.startswith("Objectives"))

    def test_local_wif_pressure_search(self):
        result = ask_nasa_gemini("What pressure is reported for WIF?", self.catalog, self.sources)
        self.assertTrue(result["excerpts"])
        self.assertTrue(any(s["source_id"] == "19960008389" and "atm" in s["quote"].lower() for s in result["excerpts"]))
        self.assertFalse(result["answered"])

    def test_model_setting_from_dotenv(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".env").write_text("GEMINI_MODEL=test-model\n", encoding="utf-8")
            with patch("src.research.ROOT", root), patch.dict("os.environ", {}, clear=True):
                self.assertEqual(setting("GEMINI_MODEL"), "test-model")
                with patch.dict("os.environ", {"GEMINI_MODEL": "process-model"}):
                    self.assertEqual(setting("GEMINI_MODEL"), "process-model")

    def test_bad_ai_responses_fall_back(self):
        for payload in [[], {"excerpts": [None]}, {"excerpts": None}]:
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]}).encode()
            with patch("src.research.api_key", return_value="fake-test-key"), patch("src.research.setting", return_value="test-model"), patch("src.research.urllib.request.urlopen", return_value=response):
                result = ask_nasa_gemini("WIF pressure", self.catalog, self.sources, True)
            self.assertEqual(result["notice"], "ai_fallback")
            self.assertTrue(result["excerpts"])

    def test_api_failure_falls_back(self):
        with patch("src.research.api_key", return_value="fake-test-key"), patch("src.research.setting", return_value="test-model"), patch("src.research.urllib.request.urlopen", side_effect=OSError("offline")):
            result = ask_nasa_gemini("WIF pressure", self.catalog, self.sources, True)
        self.assertEqual(result["notice"], "ai_fallback")


if __name__ == "__main__":
    unittest.main()
