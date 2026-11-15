"""Cross-page state, offline assets and release boundary regressions."""
import json
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from scripts.package_release import release_files

ROOT = Path(__file__).resolve().parents[1]


class ReleaseContracts(unittest.TestCase):
    def test_single_environment_and_language_controls(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
        self.assertFalse(app.exception)
        controls = app.get('button_group')
        keys = [c.key for c in controls]
        self.assertEqual(keys.count('mission_environment'), 1)
        self.assertEqual(len([c for c in app.selectbox if c.key == 'fg_lang']), 1)
        self.assertEqual(len(app.get('page_link')), 9)

    def test_release_excludes_runtime_and_secrets(self):
        names = {p.relative_to(ROOT).as_posix() for p in release_files()}
        self.assertTrue({'data/extended_review.json', 'static/models/iss.glb', 'static/fonts/IBMPlexSans-Regular.woff2'} <= names)
        self.assertFalse(any(n == '.env' or n.startswith(('backups/', '.venv')) or '.sqlite3' in n or n.endswith('.log') for n in names))

    def test_all_model_dependencies_are_local(self):
        import struct
        for path in (ROOT / 'static/models').glob('*.glb'):
            raw = path.read_bytes()
            self.assertEqual(raw[:4], b'glTF')
            scene = json.loads(raw[20:20+struct.unpack('<I',raw[12:16])[0]])
            self.assertFalse(scene.get('extensionsRequired'))
            self.assertFalse(any(x.get('uri','').startswith('http') for x in scene.get('images',[]) + scene.get('buffers',[])))

    def test_status_colors_have_readable_contrast(self):
        def luminance(hex_color):
            values=[int(hex_color[i:i+2],16)/255 for i in (1,3,5)]
            values=[v/12.92 if v<=0.04045 else ((v+.055)/1.055)**2.4 for v in values]
            return sum(a*b for a,b in zip(values,[.2126,.7152,.0722]))
        for color in ['#abbace','#7ad7bb','#a5b9d2','#ffb487','#b6a6e8','#91a0b4','#edce81']:
            self.assertGreaterEqual((luminance(color)+.05)/(luminance('#101a29')+.05),4.5)
