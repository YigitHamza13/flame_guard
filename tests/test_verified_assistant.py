import unittest
from unittest.mock import patch
from src.answers import resolve_answer, correct_question

class VerifiedAssistantTests(unittest.TestCase):
    def test_topics_in_both_languages(self):
        pairs=[('How do astronauts put out a fire?','Astronotlar yangını nasıl söndürür?','19960008389'),
          ('Does fire spread faster in space?','Uzayda daha hızlı yayılır mı?','20170008805'),
          ('Why test in space?','Neden uzayda test yapılıyor?','20170008805'),
          ('How does gravity affect flames?','Yerçekimi alevi nasıl etkiler?','20250010653'),
          ('Where does the data come from?','Veriler nereden geliyor?','19960008389'),
          ('Are astronauts safe?','Astronotlar güvende mi?','19960008389')]
        for en,tr,doc in pairs:
            for lang,q in [('EN',en),('TR',tr)]:
                a=resolve_answer(q,lang)
                self.assertTrue(a['answer'],q)
                self.assertIn(doc,[s['id'] for s in a['sources']],q)
                self.assertTrue(all('.pdf#page=' in s['url'] for s in a['sources']))
    def test_typos_and_false_matches(self):
        for q in ['uzyda atş nasl yanr','saffre']:
            self.assertTrue(resolve_answer(q,'TR')['answer'])
        for q in ['fayda sağlar mı','telefon','capital of France','When did the smoke alarm go off?']:
            self.assertEqual(resolve_answer(q)['kind'],'none',q)
    def test_missing_pdf_blocks_answer(self):
        with patch('src.answers._source_available',return_value=False):
            self.assertIsNone(resolve_answer('What did LUCI measure for PMMA?')['answer'])
    def test_local_only(self):
        with patch('socket.socket',side_effect=AssertionError('network')):
            self.assertTrue(resolve_answer('How does fire behave in space?')['answer'])
    def test_pmma_has_both_rate_and_limit_pages(self):
        a=resolve_answer('What did LUCI measure for PMMA?')
        self.assertEqual([s['page'] for s in a['sources']],[20,21])
        self.assertIn('did not reach steady',a['answer'])
