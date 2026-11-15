import unittest
from unittest.mock import patch
from src.assistant_eval import evaluate,load_current
class EvaluationTests(unittest.TestCase):
    def test_fixture_has_bilingual_positive_and_negative_coverage(self):
        result=evaluate()
        self.assertGreaterEqual(result['question_count'],30)
        self.assertGreaterEqual(result['absent_total'],8)
        self.assertEqual({r['lang'] for r in result['cases']},{'TR','EN'})
        self.assertEqual(result['source_correct'],result['source_total'])
        self.assertEqual(result['abstained'],result['absent_total'])
    def test_persisted_result_matches_code(self):
        self.assertIsNotNone(load_current())
        with patch('src.assistant_eval.fingerprint',return_value={'changed':'yes'}):
            self.assertIsNone(load_current())
