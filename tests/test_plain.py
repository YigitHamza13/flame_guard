"""Plain-language cargo cards, free-text cargo, labelled default assumptions and the soft risk tint."""
import re
import unittest

from streamlit.testing.v1 import AppTest

SCRIPT = '''
import streamlit as st
from src import pages
st.set_page_config(layout="wide")
st.session_state.setdefault("fg_lang", {lang!r})
st.session_state.setdefault("mission_environment", {env!r})
st.session_state.setdefault("saved_cargo_manifest", ["cotton t-shirt", "cable", "rubber seal", "notebook", "laptop", "plastik (pmma)"])
names = {{"overview":"overview", "environment":"environments", "cargo":"cargo", "materials":"materials", "experiments":"experiments", "gaps":"gaps", "assistant":"assistant", "methodology":"methodology"}}
st.session_state.pages = {{k: st.Page(getattr(pages, v), title=k, url_path=k) for k, v in names.items()}}
st.navigation(list(st.session_state.pages.values()), position="hidden")
pages.cargo()
'''


def run(lang="EN", env="ISS"):
    app = AppTest.from_string(SCRIPT.format(lang=lang, env=env), default_timeout=60).run()
    html = "\n".join(m.value for m in app.markdown)
    return app, html, re.findall(r"plain-card (tone-\w+)", html)


class PlainCargoTests(unittest.TestCase):
    def test_typed_items_map_to_closest_specimen(self):
        app, html, tones = run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(len(tones), 6)
        self.assertIn("Polyethylene wire insulation", html)
        self.assertIn("It ignited in 4 of them.", html)
        self.assertIn("The flame spread in 3.", html)
        self.assertIn("Test conditions: O₂ 21 %, pressure 101.325 kPa.", html)   # counts come with their conditions
        self.assertNotIn("true ignition rate", html)
        self.assertNotIn("95% interval", html)
        self.assertIn("only a brief local flame", html)

    def test_tones_follow_reported_outcomes_on_iss(self):
        _, _, tones = run()
        # t-shirt → Saffire-V cotton jersey (ignited), cable spread, rubber local flame, paper ignited, laptop none, PMMA study only
        self.assertEqual(tones, ["tone-medium", "tone-high", "tone-low", "tone-medium", "tone-none", "tone-none"])

    def test_other_gravity_is_always_grey(self):
        _, _, tones = run(env="Moon Base")
        self.assertEqual(set(tones), {"tone-none"})

    def test_never_calls_anything_safe(self):
        for lang in ("EN", "TR"):
            _, html, _ = run(lang)
            text = html.lower()
            for ok in ("does not mean safe", "not a safety rating", "güvenli olduğu anlamına gelmez", "güvenli demek değildir"):
                text = text.replace(ok, "")
            self.assertNotIn(" safe", text, lang)
            self.assertNotIn("güvenli", text, lang)

    def test_default_assumption_is_labelled(self):
        app, _, _ = run(env="Moon Base")
        captions = " ".join(c.value for c in app.caption)
        self.assertIn("34.0 %", captions)
        self.assertIn("20240015307", captions)

    def test_soft_risk_tint_is_set(self):
        app, _, _ = run()
        scripts = " ".join(str(getattr(h, "proto", "")) for h in app.get("html"))
        self.assertIn("fg-mood-high", scripts)


if __name__ == "__main__":
    unittest.main()


class VarietyTests(unittest.TestCase):
    def test_extra_specimens_are_listed_with_pages(self):
        from src.plain import extras
        ex = extras()
        self.assertEqual(set(ex), {"pmma_extra", "delrin_extra", "hdpe_extra", "nomex_extra", "jersey_extra"})
        for spec in ex.values():
            self.assertTrue(spec["sources"] and all(src["page"] > 0 for src in spec["sources"]))

    def test_everyday_words_map_to_extra_specimens(self):
        from src.plain import resolve
        self.assertEqual(resolve("Plastic water bottle (HDPE)", []), "hdpe_extra")
        self.assertEqual(resolve("Nomex uçuş tulumu", []), "nomex_extra")
        self.assertEqual(resolve("Akrilik pencere", []), "pmma_extra")

    def test_turkish_summary_exists_for_every_passage_source(self):
        import json
        from pathlib import Path
        from src.summaries import summary_for
        root = Path(__file__).resolve().parents[1]
        ids = {p["source_id"] for f in ("primary_passages.json", "extended_passages.json")
               for p in json.loads((root / "data" / f).read_text(encoding="utf-8"))}
        for sid in ids:
            self.assertTrue(summary_for(sid, "TR"), sid)
            self.assertTrue(summary_for(sid, "EN"), sid)


class EverydayExampleTests(unittest.TestCase):
    PAGE = '''
import streamlit as st
from src import pages
st.set_page_config(layout="wide")
st.session_state.setdefault("fg_lang", {lang!r})
st.session_state.setdefault("mission_environment", "ISS")
st.session_state.setdefault("material_query", {query!r})
names = {{"overview":"overview", "environment":"environments", "cargo":"cargo", "materials":"materials", "experiments":"experiments", "gaps":"gaps", "assistant":"assistant", "methodology":"methodology"}}
st.session_state.pages = {{k: st.Page(getattr(pages, v), title=k, url_path=k) for k, v in names.items()}}
st.navigation(list(st.session_state.pages.values()), position="hidden")
pages.materials()
'''

    def test_every_specimen_has_everyday_examples(self):
        from src.plain import EVERYDAY, extras
        from src.evidence import CATALOG
        for key in [*CATALOG, *extras()]:
            self.assertIn(key, EVERYDAY)
            self.assertGreaterEqual(len(EVERYDAY[key][0]), 3)
            self.assertEqual(len(EVERYDAY[key][0]), len(EVERYDAY[key][1]))

    def test_everyday_search_finds_specimen(self):
        cases = (("TR", "conta", "material_profile", "kauçuk"), ("EN", "charger", "material_profile", "kablo kılıfı"),
                 ("TR", "su şişesi", "extra_specimen", "hdpe_extra"), ("EN", "flight suit", "extra_specimen", "nomex_extra"))
        for lang, query, state_key, expected in cases:
            app = AppTest.from_string(self.PAGE.format(lang=lang, query=query), default_timeout=60).run()
            self.assertFalse(app.exception, str(app.exception))
            self.assertEqual(app.session_state[state_key], expected, (lang, query))
            body = "\n".join(m.value for m in app.markdown)
            self.assertIn("Günlük hayattan örnekler" if lang == "TR" else "Everyday examples", body)


class RiskTableTests(unittest.TestCase):
    def test_cargo_risk_tables_render_without_scores(self):
        for lang, env in (("EN", "ISS"), ("TR", "Moon Base")):
            app, html, _ = run(lang, env)
            self.assertFalse(app.exception, str(app.exception))
            self.assertEqual(html.count("class='risk-table'"), 2)
            low = html.lower()
            self.assertNotIn("risk score:", low)
            self.assertNotIn("26.2–26.2", html)
        _, html, _ = run("EN", "Moon Base")
        self.assertIn("no · tests were in microgravity", html)

    def test_environment_factors_cite_pages(self):
        from src.risk import ENV_FACTORS
        self.assertEqual(len(ENV_FACTORS), 5)
        for factor in ENV_FACTORS:
            self.assertTrue(factor["src"])
            self.assertTrue(all("p. " in label for label, _ in factor["src"]))
            self.assertNotIn("safe", (factor["seen"][0] + factor["why"][0]).lower())


class AccessibilityTests(unittest.TestCase):
    def test_cards_have_read_aloud_buttons_in_the_page_language(self):
        for lang, code, label in (("EN", "en-US", "Read aloud"), ("TR", "tr-TR", "Sesli oku")):
            app, html, tones = run(lang)
            self.assertEqual(html.count("class='say-btn'"), len(tones))
            self.assertIn(f"data-lang='{code}'", html)
            self.assertIn(label, html)

    def test_glossary_is_offered(self):
        app, _, _ = run("TR")
        self.assertTrue(any("Terimler sözlüğü" in e.label for e in app.expander))

    def test_page_language_is_announced(self):
        from src.access import set_page_language  # noqa: F401  (import check)
        app, _, _ = run("TR")
        full = AppTest.from_file(str(__import__("pathlib").Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60)
        full.session_state["fg_lang"] = "TR"
        full.run()
        scripts = " ".join(str(getattr(h, "proto", "")) for h in full.get("html")).replace("\\", "")
        self.assertIn("'lang','tr'", scripts)

    def test_charts_have_text_alternatives(self):
        app, _, _ = run("EN")
        self.assertTrue(any("Accessible chart data" in e.label for e in app.expander))


class ScoreGapTests(unittest.TestCase):
    def test_every_card_names_the_next_evidence(self):
        for lang, env in (("EN", "ISS"), ("TR", "Moon Base")):
            app, html, tones = run(lang, env)
            self.assertFalse(app.exception, str(app.exception))
            self.assertEqual(html.count("class='plain-next'"), len(tones))
        _, html, _ = run("EN", "Moon Base")
        self.assertIn("lunar surface", html)          # PMMA: lunar-gravity results exist, surface test missing

    def test_overview_offers_an_example_and_methodology_feasibility(self):
        import test_ui
        app = test_ui.page_test("overview")
        self.assertFalse(app.exception, str(app.exception))
        self.assertTrue(any("Try an example cargo" in b.label for b in app.button))
        app = test_ui.page_test("methodology", "TR")
        self.assertFalse(app.exception, str(app.exception))
        self.assertTrue(any("Uygulanabilirlik" in s.value for s in app.subheader))


class PdfReportTests(unittest.TestCase):
    def test_cargo_page_offers_a_pdf_report_in_both_languages(self):
        for lang, env, label in (("EN", "ISS", "Download PDF report"), ("TR", "Moon Base", "PDF raporu indir")):
            app, _, tones = run(lang, env)
            self.assertFalse(app.exception, str(app.exception))
            self.assertTrue(any(label in b.proto.label for b in app.get("download_button")), lang)
            cards, cargo, env_table = app.session_state["_report_parts"]
            self.assertEqual(len(cards), len(tones))
            self.assertIn("risk-table", cargo)

    def test_pdf_has_every_item_sentence_and_source_link(self):
        import io
        from pypdf import PdfReader
        from src import report
        app, _, _ = run("EN", "ISS")
        data = report.build("ISS", "O2 21 %", "0" * 64, *app.session_state["_report_parts"])
        self.assertTrue(data.startswith(b"%PDF"))
        text = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(data)).pages)
        flat = " ".join(text.split())
        for item in ("cotton t-shirt", "cable", "rubber seal", "notebook", "laptop"):
            self.assertIn(item, flat)
        self.assertIn("It ignited in 4 of them.", flat)
        self.assertIn("ntrs.nasa.gov", flat)
        self.assertIn("not a risk score", flat)
        low = flat.lower().replace("does not mean safe", "")
        self.assertNotIn(" safe ", low)

    def test_card_parts_drop_the_read_aloud_button(self):
        from src.report import card_parts
        parts = card_parts("<div class='plain-card'><button class='say-btn'>Read aloud</button>"
                           "<div class='plain-title'>Cable<span class='plain-map'> → Wire</span></div><p>It ignited.</p>"
                           "<div class='plain-next'>→ Next: more tests</div></div>")
        self.assertEqual(parts["title"], "Cable")
        self.assertEqual(parts["text"], "It ignited.")
        self.assertNotIn("Read aloud", str(parts))


class TwoWorldsTests(unittest.TestCase):
    def test_every_cargo_item_gets_an_iss_and_a_moon_cell(self):
        for lang, env in (("EN", "ISS"), ("TR", "Moon Base")):
            app, html, tones = run(lang, env)
            self.assertFalse(app.exception, str(app.exception))
            self.assertEqual(html.count("<div class='tw-row'>"), len(tones))
        _, html, _ = run("EN", "ISS")
        self.assertIn("4 tests in microgravity · ignited in 4 · flame spread in 3", html)   # cable, same as its card
        self.assertIn("1 test in microgravity · it ignited", html)                          # t-shirt, no "1 tests"
        self.assertIn("about 1.5 mm/s", html)                                               # PMMA: LUCI, p. 21
        self.assertIn("LUCI 2025, p. 21", html)
        self.assertEqual(html.count("No lunar-gravity test in this collection"), 5)

    def test_lunar_values_match_the_reviewed_records(self):
        import json
        from pathlib import Path
        from src.worlds import LUNAR
        records = {r["id"]: r for r in json.loads((Path(__file__).resolve().parents[1] / "data/extended_review.json").read_text(encoding="utf-8"))["records"]}
        self.assertIn(str(records["LUCI-SIBAL"]["measurements"]["flame_base_spread_mm_s"]), LUNAR["pamuklu kumaş"]["en"])
        self.assertIn(str(records["LUCI-PMMA"]["measurements"]["flame_tip_spread_mm_s"]), LUNAR["plastik (pmma)"]["en"])
        self.assertIn(19, records["LUCI-SIBAL"]["source_pages"])
        self.assertIn(21, records["LUCI-PMMA"]["source_pages"])
        for v in LUNAR.values():
            self.assertIn("lunar surface", v["en"])          # always says it was not on the Moon itself


class WishlistTests(unittest.TestCase):
    def test_gap_page_lists_ranked_missing_tests(self):
        import test_ui
        for lang, first in (("EN", "A burn test on the lunar surface"), ("TR", "Ay yüzeyinde bir yanma testi")):
            app = test_ui.page_test("gaps", lang)
            self.assertFalse(app.exception, str(app.exception))
            body = "\n".join(m.value for m in app.markdown)
            self.assertGreaterEqual(body.count("<div class='wish'>"), 5)
            self.assertLess(body.index(first), body.index("<div class='wish'>", body.index(first)) if body.count("<div class='wish'>") > 1 else len(body))

    def test_wishlist_is_sorted_and_never_estimates(self):
        from src.evidence import load_datasets
        from src.plain import extras
        from src.worlds import wishlist
        tests = load_datasets()[0]
        items = wishlist(tests, extras(), lambda k: k)
        counts = [len(i["keys"]) for i in items]
        self.assertEqual(counts, sorted(counts, reverse=True))
        text = " ".join(i["title"] + " " + i["why"] for i in items).lower()
        for banned in (" safe", "will ignite", "would ignite", "predict"):
            self.assertNotIn(banned, text)
        self.assertIn("pamuklu kumaş", next(i for i in items if "recount" in i["title"].lower())["keys"])



class CodexReviewTests(unittest.TestCase):
    """Regression tests for the external review (wrong matches, unknown vs not observed, filter and export consistency)."""
    KEYS = ["pamuklu kumaş", "kablo kılıfı", "kauçuk", "kağıt", "plastik (pmma)"]

    def test_other_materials_are_never_mapped(self):
        from src.plain import classify
        for item in ("Cam şişe", "glass bottle", "Metal dişli", "metal gear", "Polyester gömlek", "polyester shirt",
                     "glass window", "steel knob", "wool sweater"):
            self.assertEqual(classify(item, self.KEYS)[:2], ("other_material", None), item)

    def test_substrings_do_not_match(self):
        from src.plain import classify
        for item in ("Telefon", "hotel", "camera", "fiberglass panel"):
            self.assertIsNone(classify(item, self.KEYS)[1], item)

    def test_ambiguous_items_ask_instead_of_guessing(self):
        from src.plain import classify, resolve
        for item, option in (("Şişe", "hdpe_extra"), ("bottle", "hdpe_extra"), ("t-shirt", "jersey_extra"),
                             ("pencere", "pmma_extra"), ("gear", "delrin_extra"), ("seal", "kauçuk")):
            status, key, options = classify(item, self.KEYS)
            self.assertEqual((status, key), ("ask", None), item)
            self.assertIn(option, options)
            self.assertIsNone(resolve(item, self.KEYS))
            self.assertEqual(resolve(item, self.KEYS, option), option)
            self.assertIsNone(resolve(item, self.KEYS, "__other__"))

    def test_named_material_wins(self):
        from src.plain import classify
        cases = {"Cotton T-shirt": "jersey_extra", "Pamuklu tişört": "jersey_extra", "Bath towel": "pamuklu kumaş",
                 "Kulaklık kablosu": "kablo kılıfı", "Silikon conta": "kauçuk", "Akrilik pencere": "pmma_extra",
                 "Plastic water bottle (HDPE)": "hdpe_extra", "Delrin dişli": "delrin_extra", "Nomex uçuş tulumu": "nomex_extra"}
        for item, key in cases.items():
            self.assertEqual(classify(item, self.KEYS)[1], key, item)

    def test_unknown_spread_is_not_called_not_observed(self):
        _, html, _ = run()
        self.assertIn("The report does not say whether the flame spread.", html)     # Mir FFFT paper
        self.assertIn("Ignited; spread not reported", html)
        self.assertNotIn("Flame spread was not reported as observed", html)

    def test_real_platform_is_named(self):
        _, html, _ = run()
        for where in ("Space Shuttle, Spacelab USML-1 (WIF)", "Mir space station (FFFT)", "uncrewed Cygnus cargo vehicle (Saffire)"):
            self.assertIn(where, html)
        self.assertIn("Microgravity experiments (ISS, Space Shuttle, Mir, Cygnus)", html)
        self.assertNotIn("On the ISS · microgravity", html)

    def test_extra_specimens_reach_every_export(self):
        from src.evidence import load_datasets
        from src.plain import extras
        from src.screening import evidence_export, research_brief
        tests = load_datasets()[0]
        sel = ["pmma_extra", "nomex_extra", "jersey_extra", "kablo kılıfı"]
        frame = evidence_export(tests, sel, "ISS", {}, {}, tests.attrs["snapshot"], extras=extras())
        status = dict(zip(frame.material, frame.evidence_status))
        for k in ("pmma_extra", "nomex_extra", "jersey_extra"):
            self.assertEqual(status[k], "verified_separate_table", k)
        self.assertFalse(frame.sample_group.str.contains("_extra").any())        # no internal code names
        pmma = frame[frame.material == "pmma_extra"].iloc[0]
        self.assertEqual(int(pmma.test_count), 6)
        self.assertIn("#page=", pmma.source_page_url)
        brief = research_brief(frame)
        self.assertIn("PMMA (acrylic)", brief)
        self.assertIn("Nomex", brief)
        self.assertNotIn("No matching evidence", brief.split("## PMMA")[1].split("##")[0])

    def test_one_filter_scope_for_every_output(self):
        from src.evidence import load_datasets
        from src.plain import extras
        from src.screening import evidence_export, scope
        tests = load_datasets()[0]
        f = {"oxygen_enabled": True, "oxygen_range": [20.0, 23.0]}
        scoped, ex = scope(tests, extras(), f)
        self.assertTrue(scoped.oxygen_pct.between(20, 23).all())
        self.assertNotIn("pmma_extra", ex)            # 22.5–30.3 % is not fully inside 20–23 %
        frame = evidence_export(tests, ["pmma_extra", "kablo kılıfı", "kağıt"], "ISS", {}, f, tests.attrs["snapshot"], extras=extras())
        status = dict(zip(frame.material, frame.evidence_status))
        self.assertEqual(status["pmma_extra"], "outside_filter")
        self.assertEqual(status["kağıt"], "outside_filter")           # Mir paper: oxygen not reported
        self.assertEqual(status["kablo kılıfı"], "compiled_reference")

    def test_cards_follow_the_same_filter(self):
        script = SCRIPT.replace('pages.cargo()', 'st.session_state.setdefault("_f", 1)\npages.cargo()')
        app = AppTest.from_string(script.format(lang="EN", env="ISS"), default_timeout=60).run()
        app.expander[0].checkbox[0].check() if app.expander and app.expander[0].checkbox else None
        app.checkbox(key=None) if False else None
        boxes = [c for c in app.checkbox if "oxygen" in c.label.lower()]
        boxes[0].check()
        app.slider[0].set_range(20.0, 23.0)
        app.run()
        self.assertFalse(app.exception, str(app.exception))
        html = "\n".join(m.value for m in app.markdown)
        self.assertIn("none was run inside the selected oxygen range", html)       # paper (no O2) and PMMA extra
        self.assertIn("Polyethylene wire insulation", html)
        metrics = {m.label: m.value for m in app.metric}
        self.assertEqual(metrics["With references"], "2")        # in 20–23 %: cable 21 %, rubber 22.1 %; out: t-shirt 26.2 %, paper (no O2); none: laptop, PMMA

    def test_links_open_the_pdf_page(self):
        from src.plain import extras
        from src.risk import ENV_FACTORS
        for s in extras().values():
            for src in s["sources"]:
                self.assertIn(".pdf#page=", src["url"])
        for f in ENV_FACTORS:
            for _label, url in f["src"]:
                self.assertIn(".pdf", url)

    def test_search_scope_is_not_overstated(self):
        import json
        from pathlib import Path
        en = json.loads((Path(__file__).resolve().parents[1] / "locales/en.json").read_text(encoding="utf-8"))
        src = (Path(__file__).resolve().parents[1] / "src/pages.py").read_text(encoding="utf-8")
        self.assertNotIn("276 pages of NASA reports, searchable", src)
        self.assertIn("41 checked passages", src)

    def test_priority_order_is_explained(self):
        src = (__import__("pathlib").Path(__file__).resolve().parents[1] / "src/pages.py").read_text(encoding="utf-8")
        self.assertIn("not scientific importance", src)



class PlainAnswerTests(unittest.TestCase):
    def test_suggested_questions_have_short_answers_in_both_languages(self):
        import test_ui
        for lang in ("EN", "TR"):
            app = test_ui.page_test("assistant", lang)
            [b for b in app.button if "LUCI" in b.label][0].click()
            app.run()
            self.assertFalse(app.exception, str(app.exception))
            answers = [m.value for m in app.markdown if "class='fg-answer'" in m.value]
            self.assertTrue(answers and ("1.5 mm" in answers[0] or "1,5 mm" in answers[0]), lang)
            self.assertTrue(any(e.label.startswith(("Proof", "Kanıt")) for e in app.expander))   # quotes stay, folded

    def test_item_questions_reuse_the_cargo_card(self):
        import test_ui
        app = test_ui.page_test("assistant", "EN")
        app.chat_input[0].set_value("does a headphone cable burn").run()
        answers = [m.value for m in app.markdown if "class='fg-answer'" in m.value]
        self.assertIn("It ignited in 4 of them.", answers[-1])
        app.chat_input[0].set_value("glass bottle").run()
        answers = [m.value for m in app.markdown if "class='fg-answer'" in m.value]
        self.assertIn("not matched to a different material", answers[-1])

    def test_short_answers_only_restate_reviewed_values(self):
        from src.answers import SHORT
        text = " ".join(en for en, _tr in SHORT.values())
        for value in ("1.5 mm", "21% oxygen", "34% oxygen", "25% to 37%"):
            self.assertIn(value, text)
        self.assertNotIn(" safe", text.lower())


class ExperimentLibraryItemTests(unittest.TestCase):
    PAGE = EverydayExampleTests.PAGE.replace('st.session_state.setdefault("material_query", {query!r})',
                                             'st.session_state.setdefault("experiment_query", {query!r})').replace("pages.materials()", "pages.experiments()")

    def test_everyday_item_leads_to_specimen_and_cargo(self):
        for lang, query, expect in (("EN", "cotton t-shirt", "Cotton jersey fabric"), ("TR", "kulaklık kablosu", "Polietilen kablo yalıtımı"),
                                    ("EN", "glass bottle", "No experiment and no tested specimen")):
            app = AppTest.from_string(self.PAGE.format(lang=lang, query=query), default_timeout=60).run()
            self.assertFalse(app.exception, str(app.exception))
            info = " ".join(i.value for i in app.info)
            self.assertIn(expect, info)
            self.assertNotIn("Widen the filters", info)
            self.assertTrue(any("Cargo Screening" in b.label or "Kargo Taraması" in b.label for b in app.button))


class GeneralQuestionTests(unittest.TestCase):
    def test_concept_question_uses_glossary_and_unrelated_question_gets_no_answer(self):
        import test_ui
        app = test_ui.page_test("assistant", "TR")
        app.chat_input[0].set_value("Dünyada oksijen yüzdesi nekadardır").run()
        answers = [m.value for m in app.markdown if "class='fg-answer'" in m.value]
        self.assertIn("%21", answers[-1])
        self.assertNotIn("WIF", answers[-1])                       # no unrelated summary in the answer box
        app = test_ui.page_test("assistant", "EN")
        app.chat_input[0].set_value("what is the capital of France").run()
        self.assertFalse([m for m in app.markdown if "class='fg-answer'" in m.value])
        self.assertTrue(any("does not make one up" in i.value for i in app.info))


class TopicAnswerTests(unittest.TestCase):
    def test_common_questions_get_sourced_answers(self):
        from src.answers import topic_answer
        cases = [("TR", "Uzayda ateş nasıl yanar", "2,2–5 cm/s"), ("TR", "duman alarmı ne zaman çaldı", "981"),
                 ("TR", "Mars'ta yangın", "Mars için ölçülmüş bir alev sonucu yok"), ("EN", "What did BASS find", "17.1%"),
                 ("EN", "Is it safe to bring a laptop", "never calls a material safe"), ("TR", "Ay'da test yapıldı mı", "Ay yüzeyinde henüz")]
        for lang, q, expect in cases:
            ans, _means, src = topic_answer(q, lang)
            self.assertIn(expect, ans or "", q)
        self.assertIsNone(topic_answer("fayda sağlar mı", "TR")[0])          # no false match on 'ay' inside a word
        self.assertIsNone(topic_answer("what is the capital of France", "EN")[0])

    def test_topic_sources_open_pdf_pages(self):
        from src.answers import TOPICS, _src
        for _w, _a, _m, src in TOPICS:
            if src and src[1]:
                self.assertIn(".pdf#page=", _src(*src)[1])
