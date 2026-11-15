"""Streamlit application smoke and interaction regressions, no external AI requests."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["overview", "environments", "cargo", "materials", "experiments", "gaps", "assistant", "methodology"]


def page_test(page, lang="EN", env="ISS"):
    script = f'''
import streamlit as st
from src import pages
st.set_page_config(layout="wide")
st.session_state.setdefault("fg_lang", {lang!r})
st.session_state.setdefault("mission_environment", {env!r})
names = {{"overview":"overview", "environment":"environments", "cargo":"cargo", "materials":"materials", "experiments":"experiments", "gaps":"gaps", "assistant":"assistant", "methodology":"methodology"}}
st.session_state.pages = {{key: st.Page(getattr(pages, value), title=key, url_path=key) for key,value in names.items()}}
st.navigation(list(st.session_state.pages.values()), position="hidden")
pages.{page}()
'''
    return AppTest.from_string(script, default_timeout=20).run()


class InterfaceTests(unittest.TestCase):
    def test_full_app_opens(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        self.assertFalse(app.exception, str(app.exception))

    def test_all_pages_both_languages(self):
        for language in ("EN", "TR"):
            for page in PAGES:
                with self.subTest(language=language, page=page):
                    app = page_test(page, language)
                    self.assertFalse(app.exception, str(app.exception))

    def test_environments(self):
        for env in ("Earth Lab", "ISS", "Moon Base", "Mars Mission"):
            with self.subTest(env=env):
                app = page_test("environments", "TR", env)
                self.assertFalse(app.exception, str(app.exception))

    def test_save_assumptions(self):
        app = page_test("environments")
        app.number_input[0].set_value(21)
        app.number_input[1].set_value(101.325)
        app.button[0].click().run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(app.session_state["mission_assumptions"]["ISS"]["pressure"], 101.325)

    def test_cargo_no_evidence_export(self):
        app = page_test("cargo")
        app.checkbox[0].check()
        app.checkbox[1].check()
        app.slider[0].set_range(0.0, 5.0)
        app.run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(app.metric[2].value, "5")
        self.assertEqual(len(app.get("download_button")), 4)  # CSV, JSON, brief + PDF report

    def test_material_focus(self):
        app = page_test("materials")
        app.session_state["focus_material"] = "kauçuk"
        app.run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(app.session_state["material_profile"], "kauçuk")

    def test_fluid_filter(self):
        app = page_test("experiments")
        app.selectbox(key="experiment_area").select("Fluid Physics").run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(len(app.selectbox(key="experiment_profile").options), 2)

    def test_lunar_chat(self):
        app = page_test("assistant", "TR")
        app.chat_input[0].set_value("Ay’da hangi kanıtlar var?").run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertTrue(any("Ay yerçekimi" in w.value for w in app.warning))


if __name__ == "__main__":
    unittest.main()
