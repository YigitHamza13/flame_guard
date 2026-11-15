"""Source-bound display adapters. No risk calculations or test-count changes."""
import pandas as pd
import streamlit as st
from src.extended_evidence import load_extension, eligible_measurements
from src.i18n import t

def short_comparison():
    st.caption(t('Compare reported gravity, oxygen and pressure with your saved assumptions in Cargo Screening.'))
    st.page_link(st.session_state.pages['cargo'], label=t('Open condition comparison'))

def partial_comparison(assumptions):
    records, _, _ = load_extension()
    measured = eligible_measurements(records)
    env = st.session_state.mission_environment
    target = {'Earth Lab':1.0,'Moon Base':1/6}.get(env)
    rows=[]
    for r in measured:
        g=r['gravity_level_g']
        gravity = t('Partial gravity (≈0.16 g)') if r['gravity_class']=='lunar' else t('Earth reference (1 g)')
        rows.append({t('Study'):r['id'], t('Specimen'):r['material'],
                     t('Gravity'):gravity, t('Reported g'):g,
                     t('Assumed g'):target,
                     t('Gravity comparison'): '—' if target is None or g is None else t('Numerically equal') if abs(g-target)<1e-6 else t('Different'),
                     'O₂ (%)':r['measurements'].get('oxygen_pct'), 'P (kPa)':r['measurements'].get('pressure_kpa'),
                     'evidence_type':r['evidence_type'], t('Method'):r['gravity_method'],
                     t('Source pages'):', '.join(map(str,r['source_pages']))})
    st.subheader(t('Measured study conditions'))
    from src.ui import dataframe
    dataframe(pd.DataFrame(rows))
    st.caption(t('≈0.16 g identifies the lunar gravity class. A blank reported g has not been derived from rotation speed. Numerical equality is not an applicability tolerance. Planned and theoretical work is excluded here.'))

def source_cards():
    records,_,_=load_extension()
    lunar=[r for r in records if r['gravity_class']=='lunar' and r['review_status']=='source_checked']
    counts={kind:sum(r['evidence_type']==kind for r in lunar) for kind in ('measured_experiment','planned_experiment','theoretical_model')}
    st.caption(t('{total} lunar partial-gravity records: {measured} measured, {planned} planned, {theory} theoretical.', total=len(lunar), measured=counts['measured_experiment'], planned=counts['planned_experiment'], theory=counts['theoretical_model']))
    columns=st.columns(3)
    for col,sid in zip(columns,['20250010653','20250002114','20260001966']):
        group=[r for r in records if r['source_id']==sid]
        with col.container(border=True):
            st.markdown('**'+group[0]['title']+'**')
            st.caption(t('Original English'))
            for kind in sorted({r['evidence_type'] for r in group}):
                st.caption(t(kind))
            st.link_button(t('Source document'),group[0]['url'])
