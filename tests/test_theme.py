import unittest
from pathlib import Path
from src.theme import THEMES,theme_css,theme_script,environment_strip

def luminance(value):
    rgb=[int(value[i:i+2],16)/255 for i in (1,3,5)]
    rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    return sum(v*w for v,w in zip(rgb,(.2126,.7152,.0722)))
def contrast(a,b):
    hi,lo=sorted([luminance(a),luminance(b)],reverse=True)
    return (hi+.05)/(lo+.05)

class ThemeTokenTests(unittest.TestCase):
    def test_contrast(self):
        for env,p in THEMES.items():
            for fg,bg in [('--text','--bg'),('--muted','--surface'),('--accent','--surface'),('--text','--glow')]:
                self.assertGreaterEqual(contrast(p[fg],p[bg]),4.5,(env,fg,bg))
    def test_script_and_semantic_colours(self):
        for env,p in THEMES.items():
            self.assertIn(p['class'],theme_script(env))
            css=theme_css(env)
            self.assertIn('prefers-reduced-motion:reduce',css)
            for c in ['#e8704a','#e0a53b','#5296dc','#7d8a9c']:
                self.assertNotIn(c,css)
    def test_mars_has_no_unverified_values(self):
        s=environment_strip('Mars Mission')
        self.assertIn('no measured Mars result',s)
        self.assertFalse(any(c.isdigit() for c in s))
    def test_moon_defaults_share_existing_data(self):
        from src.plain import DEFAULT_ASSUMPTIONS
        s=environment_strip('Moon Base');d=DEFAULT_ASSUMPTIONS['Moon Base']
        self.assertIn(f"{d['oxygen']:g}%",s)
        self.assertIn(f"{d['pressure']:g} kPa",s)

class ThemeInterfaceTests(unittest.TestCase):
    def test_apply_theme_script(self):
        from streamlit.testing.v1 import AppTest
        for env in THEMES:
            app=AppTest.from_string(f"from src.theme import apply_theme\napply_theme({env!r})").run()
            self.assertFalse(app.exception)
            self.assertTrue(any(THEMES[env]['class'] in str(x.proto) for x in app.get('html')))
    def test_all_pages_all_environments(self):
        from test_ui import page_test,PAGES
        for env in THEMES:
            for page in PAGES:
                app=page_test(page,'EN',env)
                self.assertFalse(app.exception,(env,page,str(app.exception)))
