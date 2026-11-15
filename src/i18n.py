"""JSON locale catalog with English fallback and named interpolation."""
import json
from functools import lru_cache
from pathlib import Path
import streamlit as st

DIRECTORY = Path(__file__).resolve().parents[1] / 'locales'

@lru_cache(maxsize=20)
def catalog(code):
    path = DIRECTORY / f'{code.lower()}.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}

def available_languages():
    return {p.stem.upper(): json.loads(p.read_text(encoding='utf-8')).get('_language', p.stem.upper())
            for p in sorted(DIRECTORY.glob('*.json'))}

def t(key, fallback=None, **values):
    english = catalog('en').get(key, key)
    translated = catalog(st.session_state.get('fg_lang', 'EN')).get(key, english)
    return translated.format(**values) if values else translated
