"""Shared components for the FLAMEGUARD research workspace."""
import base64
import html
import json

import streamlit as st

from src.evidence import ROOT, ENVIRONMENTS
from src.i18n import t


@st.cache_data(show_spinner=False)
def asset(name):
    path = ROOT / "assets" / name
    mime = "image/png" if path.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def logo(variant="compact"):
    if variant == "full":
        st.markdown(f'<img class="logo-full" src="{asset("flameguard-transparent.png")}" alt="FLAMEGUARD logo">', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="brand brand-original"><a href="/" target="_self" aria-label="Overview"><img src="{asset("flameguard-icon.png")}" alt="FLAME GUARD"></a></div>', unsafe_allow_html=True)


def heading(title, description):
    st.title(title)
    st.markdown(f'<p class="page-description">{html.escape(description)}</p>', unsafe_allow_html=True)


def metrics(items):
    for col, (label, value, caption) in zip(st.columns(len(items)), items):
        with col:
            st.metric(label, "—" if value is None else value)
            if caption:
                st.caption(caption)


def badge(label, tone="neutral"):
    st.markdown(f'<span class="badge {tone}">{html.escape(label)}</span>', unsafe_allow_html=True)


def environment_notice():
    from src.extended_evidence import load_extension, eligible_measurements
    env = st.session_state["mission_environment"]
    if env == "Moon Base":
        rows = eligible_measurements(load_extension()[0])
        count = sum(r.get('gravity_class') == 'lunar' for r in rows)
        st.caption(t('{v0} measured lunar-gravity evidence records. Simulated gravity; no completed lunar-surface tests in this collection.', v0=count) if count else
                   t('No checked lunar-gravity measurements in the current collection.'))
    elif env == "Mars Mission":
        st.info(t('Mars mission phase, atmosphere and applicable combustion measurements are unknown. Define assumptions in Environment Explorer.'))
    elif env == 'Earth Lab':
        st.caption(t('Earth is a comparison reference; this is not a safety assessment.'))
        if not any(r['gravity_method']=='ground_1g' for r in eligible_measurements(load_extension()[0])):
            st.info(t('No normal-gravity reference records in this collection.'))


def evidence_status():
    with st.expander(t('Evidence status · details')):
        st.write(t('Missing measurements remain unknown, never zero or a safety score. Source inspection does not establish flight qualification. SIBAL ignition counts remain disputed; gas-phase ignition is distinct from sustained specimen burning.'))


def planet(height=340):
    context_model(st.session_state["mission_environment"], height)


def context_model(env, height=360):
    model_name = {'Moon Base':'moon', 'ISS':'iss', 'Mars Mission':'mars', 'Earth Lab':'earth'}.get(env, 'moon')
    template = (ROOT / 'assets/context-model.html').read_text(encoding='utf-8')
    fallback = ''
    if model_name != 'iss':
        fallback = (ROOT / 'assets/planet.html').read_text(encoding='utf-8').replace('__PLANET_CONFIG__', json.dumps(
            {'name':model_name.title(), 'texture':asset(f'{model_name}.jpg'), 'atmosphere':model_name == 'earth'}))
    config = dict(name=env, model=f'/app/static/models/{model_name}.glb', hasModel=(ROOT / 'static' / 'models' / f'{model_name}.glb').is_file(), poster=asset(f'{"bass-ii-msg" if model_name == "iss" else model_name}.jpg'),
                  library='/app/static/js/model-viewer.min.js',
                  retryLabel=t('Retry 3D model'),
                  loadingLabel=t('Loading 3D model…'), errorLabel=t('Model could not load. Retry when the connection is ready.'),
                  fallbackHTML=fallback, instructions=t('Drag or use arrow keys to explore'),
                  rotate=t('Rotate'), pause=t('Pause rotation'),
                  fallbackLabel=t('Local fallback sphere / image · not a NASA 3D model'),
                  loadedLabel=t('NASA 3D model'))
    payload = json.dumps(config).replace('<', '\\u003c')
    st.iframe(template.replace('__CONFIG__', payload),
              height=height, alt=t('NASA model · visual context only'))
    links = {'moon':'https://svs.gsfc.nasa.gov/14959/', 'mars':'https://science.nasa.gov/resource/planet-mars-3d-model/',
             'iss':'https://science.nasa.gov/resource/international-space-station-3d-model/', 'earth':'https://science.nasa.gov/learn/heat/resource/earth-3d-model/'}
    st.caption(t('NASA content does not imply institutional endorsement. View type is shown inside the model panel.'))
    st.link_button(t('NASA · Model source'), links[model_name])


def remember(kind, value):
    recent = st.session_state.setdefault("recent_research", [])
    item = {"kind": kind, "value": value}
    st.session_state.recent_research = [item] + [entry for entry in recent if entry != item][:7]


def dataframe(frame, **kwargs):
    from src.labels import label
    frame = frame.copy().replace({'None': '—', 'nan': '—', 'NaN': '—'})
    colors = {label(k): v for k,v in [('observed','#e3b787'), ('not_observed','#a5b9d2'), ('disputed','#ffb487'),
                                     ('unknown','#b6a6e8'), ('Not reported','#91a0b4'), ('Partly reported','#edce81')]}
    styled = frame.style.format(precision=3, na_rep="—").map(lambda value: f"color: {colors[value]}" if isinstance(value, str) and value in colors else '')
    if 'ID' in frame:
        styled=styled.set_properties(subset=['ID'], **{'font-family':'PlexMono, monospace','font-size':'13px'})
    st.dataframe(styled, hide_index=True, width="stretch", **kwargs)
