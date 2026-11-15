"""Prevent planned/theoretical work and duplicate documents entering test totals."""
import unittest
from src.extended_evidence import eligible_measurements, logical_sources, load_extension


class ExtendedEvidenceTests(unittest.TestCase):
    def test_only_checked_measurements(self):
        rows = [{'id': str(i), 'evidence_type': kind, 'review_status': 'source_checked'} for i, kind in enumerate(
            ['measured_experiment', 'planned_experiment', 'theoretical_model', 'mission_assumption', 'context_only'])]
        self.assertEqual(len(eligible_measurements(rows)), 1)
        rows[0]['review_status'] = 'unverified_source'
        self.assertEqual(eligible_measurements(rows), [])

    def test_related_documents_one_source(self):
        self.assertEqual(logical_sources([{'logical_source': 'ICES-2025-392'}, {'logical_source': 'ICES-2025-392'}]), {'ICES-2025-392'})

    def test_luci_is_measured_fm2_is_planned(self):
        records, sources, snapshot = load_extension()
        self.assertEqual(len(snapshot), 64)
        self.assertTrue(any(r['id'] == 'LUCI-PMMA' for r in eligible_measurements(records)))
        self.assertTrue(all(r['evidence_type'] == 'planned_experiment' for r in records if r['id'].startswith('FM2')))
        self.assertTrue(all(r['test_count'] is None for r in records))
        self.assertTrue(all(s['sha256'] and s['page'] for s in sources))

    def test_no_mars_results_inferred_from_title(self):
        records, _, _ = load_extension()
        self.assertFalse(any(r.get('gravity_class') == 'martian' for r in eligible_measurements(records)))
