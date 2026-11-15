import unittest
from pathlib import Path
class ModelLoadingTests(unittest.TestCase):
    def test_models_start_automatically(self):
        source=(Path(__file__).resolve().parents[1]/'assets/context-model.html').read_text(encoding='utf-8')
        self.assertIn("\nstart();",source)
        self.assertNotIn('id="load"',source)
        self.assertIn('id="retry" type="button" hidden',source)
        self.assertNotIn("model.hidden=false;photo.hidden=true",source)
        self.assertNotIn('IntersectionObserver',source)
        self.assertNotIn('setTimeout(fallback',source)
        self.assertIn('fetch(config.library)',source)
    def test_local_library_is_packaged(self):
        from scripts.package_release import release_files
        root=Path(__file__).resolve().parents[1]
        self.assertIn(root/'static/js/model-viewer.min.js',release_files())
