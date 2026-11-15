"""FLAMEGUARD — evidence intelligence for spaceflight fire safety."""
from pathlib import Path
import json

import streamlit as st

from src import pages
from src.evidence import ENVIRONMENTS, load_datasets, material_keys, material_label
from src.ui import heading, logo, t, evidence_status
from src.labels import label
from src.i18n import available_languages

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="FLAMEGUARD | Research Workspace", page_icon=str(ROOT / "assets/flameguard-symbol.png"),
                   layout="wide", initial_sidebar_state="auto")
st.markdown("<style>" + (ROOT / "assets/style.css").read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)
# Screen readers need the real page language; this also stops browser auto-translation.
from src.access import set_page_language
set_page_language()
st.session_state.setdefault("fg_lang", "EN")
legacy_environment = {"Ay üssü": "Moon Base", "Mars yolculuğu": "Mars Mission"}.get(st.session_state.get("environment"), "Moon Base")
st.session_state.setdefault("mission_environment", legacy_environment)
# One-time migration for sessions opened before the Moon Base became the default.
if not st.session_state.get("_fg_moon_default_v2"):
    if st.session_state.get("mission_environment") == "ISS" and not st.session_state.get("environment"):
        st.session_state.mission_environment = "Moon Base"
    st.session_state["_fg_moon_default_v2"] = True
if st.session_state.mission_environment not in ENVIRONMENTS:
    st.session_state.mission_environment = "Moon Base"
st.session_state.mission_environment = st.session_state.mission_environment

specs = [
    ("overview", pages.overview, "Mission Overview", 'Mission Overview', ":material/public:"),
    ("environment", pages.environments, "Environment Explorer", 'Environment Explorer', ":material/explore:"),
    ("cargo", pages.cargo, "Cargo Screening", 'Cargo Screening', ":material/inventory_2:"),
    ("materials", pages.materials, "Material Explorer", 'Material Explorer', ":material/layers:"),
    ("experiments", pages.experiments, "Experiment Library", 'Experiment Library', ":material/science:"),
    ("gaps", pages.gaps, "Evidence Gap Engine", 'Evidence Gaps', ":material/grid_view:"),
    ("assistant", pages.assistant, "AI Research Assistant", 'AI Research Assistant', ":material/forum:"),
    ("methodology", pages.methodology, "Methodology & Sources", 'Methodology & Sources', ":material/menu_book:"),
]
page_objects = {key: st.Page(function, title=t(en), icon=icon, url_path=key, default=key == "overview")
                for key, function, en, tr, icon in specs}
st.session_state.pages = page_objects
navigation = st.navigation(list(page_objects.values()), position="hidden")
with st.sidebar:
    logo()
    for group_en, group_tr, group_keys in [
        ("MISSION", 'MISSION', ["overview", "environment", "cargo"]),
        ("EVIDENCE LIBRARY", 'EVIDENCE LIBRARY', ["materials", "experiments", "gaps"]),
        ("RESEARCH TOOLS", 'RESEARCH TOOLS', ["assistant", "methodology"]),
    ]:
        for key, _, en, tr, icon in specs:
            if key in group_keys:
                active = navigation.url_path == page_objects[key].url_path
                with st.container(key="nav_active_" + key if active else "nav_item_" + key):
                    st.page_link(page_objects[key], label=t(en), icon=icon, width="stretch")
    st.divider()
    languages = available_languages()
    with st.container(key='language_picker'):
        st.selectbox(":material/language: " + t('Language'), list(languages), key="fg_lang", format_func=languages.get)

tests, mappings, catalog, sources, errors = load_datasets()
if navigation.url_path not in {page_objects[k].url_path for k in ('experiments', 'assistant', 'methodology')}:
    with st.container(key="mission_toolbar"):
        st.segmented_control(t('Environment'), list(ENVIRONMENTS), key="mission_environment",
                             format_func=label, selection_mode="single", required=True)
from src.theme import apply_theme
apply_theme(st.session_state.mission_environment)
for error in errors:
    st.error(error)
if navigation.url_path != page_objects["cargo"].url_path:
    # The soft risk tint belongs to Cargo Screening only; clear it elsewhere.
    st.html("<script>try{const a=window.parent.document.querySelector('.stApp');"
            "if(a){a.classList.remove('fg-mood-high','fg-mood-medium');}}catch(e){}</script>", unsafe_allow_javascript=True)
navigation.run()
st.markdown('<footer class="research-footer">' + t('Independent research tool · No NASA approval · Records await expert review') + '</footer>', unsafe_allow_html=True)
