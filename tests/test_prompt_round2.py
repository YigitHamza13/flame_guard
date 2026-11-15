"""Source eligibility, missing cells and user-facing form regressions."""
import copy
import json
import unittest
import pandas as pd
from pathlib import Path
from unittest.mock import patch
from src.charts import reviewed_matrix, oxygen_points
from src.evidence import load_datasets
from src.extended_evidence import load_extension
from src.i18n import t, catalog
from test_ui import page_test

ROOT=Path(__file__).resolve().parents[1]

class PromptRoundTwo(unittest.TestCase):
    def test_missing_matrix_cells_are_not_zero(self):
        tests,_,_,_,_=load_datasets()
        matrix=reviewed_matrix(tests,load_extension()[1])
        missing=matrix[(matrix.material=='PMMA') & (matrix.gravity=='Microgravity')].iloc[0]
        self.assertEqual(missing.outcome,'No data')
        self.assertTrue(pd.isna(missing.evidence_type))
        self.assertTrue(matrix[matrix.outcome!='No data'].evidence_type.eq('measured_experiment').all())

    def test_unchecked_passage_cannot_populate_matrix(self):
        tests,_,_,_,_=load_datasets()
        passages=copy.deepcopy(load_extension()[1])
        for p in passages:p['review_status']='unverified_source'
        matrix=reviewed_matrix(tests,passages)
        self.assertTrue(matrix[matrix.gravity!='Microgravity'].outcome.eq('No data').all())

    def test_planned_and_theoretical_are_not_oxygen_points(self):
        base={'id':'fixture','review_status':'source_checked','gravity_level_g':1,'measurements':{'oxygen_pct':21},'url':'https://example.test','source_pages':[1]}
        records=[dict(base,evidence_type=k) for k in ['planned_experiment','theoretical_model','context_only']]
        self.assertTrue(oxygen_points(records).empty)
        records.append(dict(base,evidence_type='measured_experiment'))
        self.assertEqual(len(oxygen_points(records)),1)

    def test_current_oxygen_levels_insufficient(self):
        self.assertLess(oxygen_points(load_extension()[0]).gravity_level_g.nunique(),2)

    def test_earth_view_and_invalid_assumptions(self):
        app=page_test('environments','TR','Earth Lab')
        self.assertFalse(app.exception)
        app.session_state['mission_assumptions']={}
        app.number_input[0].set_value(101)
        app.button[0].click().run()
        self.assertTrue(app.warning)
        self.assertNotIn('Earth Lab',app.session_state['mission_assumptions'])

    def test_reset_assumptions(self):
        app=page_test('environments')
        app.number_input[0].set_value(21)
        app.button[0].click().run()
        app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.number_input[0].value)
        self.assertNotIn('ISS',app.session_state['mission_assumptions'])

    def test_locale_fallback_and_interpolation(self):
        with patch('src.i18n.st') as mock:
            mock.session_state={'fg_lang':'zz'}
            self.assertEqual(t('measured_experiment'),'Measured experiment')
            self.assertEqual(t('Untranslated key'),'Untranslated key')
            mock.session_state={'fg_lang':'TR'}
            self.assertEqual(t('measured_experiment'),'Ölçülmüş deney')

    def test_illustration_has_no_numeric_results(self):
        app=page_test('environments','EN','Earth Lab')
        illustrations=[m.value for m in app.markdown if 'flame-illustration' in m.value]
        self.assertEqual(len(illustrations),1)
        self.assertNotIn('%',illustrations[0])
        self.assertNotIn('risk',illustrations[0].lower())
        self.assertTrue(any('not experimental data' in c.value for c in app.caption))
