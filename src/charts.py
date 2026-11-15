"""Presentation-only, page-bound chart datasets. Missing cells remain null."""
import json
import altair as alt
import pandas as pd
import streamlit as st
from src.extended_evidence import load_extension, eligible_measurements
from src.i18n import t
from src.ui import dataframe
from src.screening import csv_bytes

PALETTE=['#e3b787','#a5b9d2','#b6a6e8','#edce81','#91a0b4']

def reviewed_matrix(tests, passages):
    """Only already hash-checked passages can populate LUCI comparison cells."""
    by_page={(p['source_id'],p['page']):p for p in passages if p.get('review_status')=='source_checked'}
    output=[]
    for material,page in [('SIBAL',33),('PMMA',36)]:
        for gravity in ['Earth 1 g','Lunar ≈0.16 g','Microgravity']:
            row=dict(material=material,gravity=gravity,outcome='No data',source=None,page=None,evidence_type=None,quote=None)
            passage=by_page.get(('20250010653',page))
            if gravity!='Microgravity' and passage and '1-G' in passage['text'] and 'Flame' in passage['text']:
                row.update(outcome='Flame spread reported',source=passage['url'],page=page,
                           evidence_type='measured_experiment',quote=passage['text'])
            elif gravity=='Microgravity' and material=='SIBAL':
                subset=tests[tests.material.eq('pamuklu kumaş') & tests.gravity.str.casefold().eq('microgravity')]
                if not subset.empty and subset.propagation.eq('mixed').any():
                    group=subset[subset.propagation.eq('mixed')].iloc[0]
                    row.update(outcome='Mixed observations',source=group.source_url,page=int(group.source_page),
                               evidence_type='measured_experiment',quote=None)
            output.append(row)
    return pd.DataFrame(output)

def chart_style(chart):
    return chart.configure(font='Plex').configure_axis(labelFontSize=13,titleFontSize=14,labelLimit=350).configure_legend(labelFontSize=13,titleFontSize=13,labelLimit=350).configure_title(fontSize=18)

def matrix_chart(tests, passages, key='overview'):
    frame=reviewed_matrix(tests,passages)
    st.subheader(t('Reported outcomes (Earth 1 g reference)'))
    st.caption(t('This is not a safety score. Specimens, directions and atmospheres differ; categories do not establish equivalent test conditions.'))
    display=frame.copy()
    for field in ['material','gravity','outcome']: display[field]=display[field].map(t)
    display['symbol']=frame.outcome.map({'No data':'╱ — ╱','Flame spread reported':'●','Mixed observations':'◐'})
    display['type_label']=frame.evidence_type.map(lambda x:t(x) if pd.notna(x) else '—')
    base=alt.Chart(display).encode(x=alt.X('gravity:N',sort=[t(x) for x in ['Earth 1 g','Lunar ≈0.16 g','Microgravity']],title=None,axis=alt.Axis(labelAngle=0)),
                                    y=alt.Y('material:N',title=None,axis=alt.Axis(labelOverlap=False)),
                                    tooltip=[alt.Tooltip('material:N',title=t('Specimen')),alt.Tooltip('outcome:N',title=t('Outcome')),
                                             alt.Tooltip('source:N',title=t('Source')),alt.Tooltip('page:Q',title=t('PDF page')),alt.Tooltip('type_label:N',title=t('Evidence type'))])
    rect=base.mark_rect(stroke='#080d16',strokeWidth=4,aria=True).encode(color=alt.Color('outcome:N',title=t('Outcome'),
        scale=alt.Scale(domain=[t(x) for x in ['Flame spread reported','Mixed observations','No data']],range=['#e3b787','#b6a6e8','#596575']),legend=alt.Legend(orient='bottom')))
    text=base.mark_text(fontSize=20,color='#080d16').encode(text='symbol:N')
    st.altair_chart(chart_style((rect+text).properties(height=200,description=t('Reported outcome matrix. Missing cells contain a dash.'))),width='stretch')
    with st.expander(t('Accessible data and source passages')):
        dataframe(display[['material','gravity','outcome','source','page','type_label']])
        for p in (33,36):
            found=next((r for r in passages if r['source_id']=='20250010653' and r['page']==p),None)
            if found:
                st.markdown(f"[LUCI · PDF {p}]({found['url']})")
                st.caption(t('Original English'))
                st.text(found['text'])
    st.download_button(t('Export outcome matrix'),csv_bytes(frame),'outcome-matrix.csv','text/csv',key=f'matrix_export_{key}')

def oxygen_points(records):
    rows=[]
    for record in eligible_measurements(records):
        g=record.get('gravity_level_g'); oxygen=record['measurements'].get('oxygen_pct')
        # A logarithmic axis cannot represent zero. Ranges are not point values.
        if g is not None and g>0 and oxygen is not None:
            rows.append(dict(record=record['id'],gravity_level_g=g,oxygen_pct=oxygen,source=record['url'],
                             pages=', '.join(map(str,record['source_pages'])),evidence_type=record['evidence_type']))
    return pd.DataFrame(rows,columns=['record','gravity_level_g','oxygen_pct','source','pages','evidence_type'])

def oxygen_chart():
    frame=oxygen_points(load_extension()[0])
    st.subheader(t('Oxygen and gravity'))
    if frame.gravity_level_g.nunique()<2:
        st.info(t('Insufficient verified data: at least two gravity levels with a reported oxygen point are required. Oxygen ranges and planned conditions are excluded.'))
    else:
        chart=alt.Chart(frame).mark_point(size=100,color='#e3b787',aria=True).encode(
            x=alt.X('gravity_level_g:Q',scale=alt.Scale(type='log'),title=t('Gravity (g)')),
            y=alt.Y('oxygen_pct:Q',title='O₂ (%)'),tooltip=list(frame.columns))
        st.altair_chart(chart_style(chart.properties(height=280)),width='stretch')
        from src.access import chart_table
        chart_table(frame)
    st.download_button(t('Export verified oxygen points'),csv_bytes(frame),'oxygen-gravity.csv','text/csv')

def distribution_charts():
    records,_,_=load_extension()
    checked=[r for r in records if r['review_status']=='source_checked']
    years={'20250010653':2025,'20250002114':2025,'20240015307':2024,'20260001966':2026,'20210021318':2021}
    frame=pd.DataFrame([dict(record=r['id'],document_type=r['document_type'],evidence_type=r['evidence_type'],
                             gravity=r['gravity_class'],year=years.get(r['source_id']),source=r['url'],
                             pages=', '.join(map(str,r['source_pages']))) for r in checked])
    st.subheader(t('Evidence distribution'))
    st.caption(t('Counts describe classified study records, not tests or independent replications. Years are document publication years. No imported records are plotted for empty years.'))
    display=frame.copy()
    for col in ['document_type','evidence_type','gravity']: display[col]=display[col].map(t)
    color=alt.Color('evidence_type:N',title=t('Evidence type'),scale=alt.Scale(range=PALETTE),legend=alt.Legend(orient='bottom'))
    for field,title in [('document_type',t('Document type')),('gravity',t('Gravity class'))]:
        chart=alt.Chart(display).mark_bar(aria=True).encode(y=alt.Y(f'{field}:N',title=None),x=alt.X('count():Q',title=t('Records'),axis=alt.Axis(tickMinStep=1)),color=color,
            tooltip=[alt.Tooltip(f'{field}:N',title=title),alt.Tooltip('evidence_type:N',title=t('Evidence type')),alt.Tooltip('count():Q',title=t('Records'))])
        st.altair_chart(chart_style(chart.properties(height=220,title=title)),width='stretch')
    chart=alt.Chart(display.dropna(subset=['year'])).mark_circle(size=100,aria=True).encode(
        x=alt.X('year:Q',scale=alt.Scale(domain=[2014,2026]),axis=alt.Axis(format='d',tickMinStep=1),title=t('Publication year')),
        y=alt.Y('record:N',title=None,axis=alt.Axis(labelOverlap=False)),color=color,tooltip=['record','source','pages','evidence_type','year'])
    st.altair_chart(chart_style(chart.properties(height=max(280,len(frame)*32),title=t('Source timeline'))),width='stretch')
    with st.expander(t('Accessible chart data')):dataframe(display)
    st.download_button(t('Export evidence distribution'),csv_bytes(frame),'evidence-distribution.csv','text/csv')

def flame_illustration():
    st.subheader(t('Qualitative flame illustration'))
    options={key:t(key) for key in ['Earth 1 g','Lunar ≈0.16 g','Microgravity']}
    shape=st.radio(t('Illustrated environment'),list(options),format_func=options.get,horizontal=True,key='flame_environment')
    paths={'Earth 1 g':'M60 135 C5 110 45 75 60 10 C70 65 120 100 60 135Z',
           'Lunar ≈0.16 g':'M60 135 C-5 110 20 65 60 40 C105 65 130 110 60 135Z',
           'Microgravity':'M60 135 C0 135 0 45 60 45 C120 45 120 135 60 135Z'}
    st.markdown('<div class="flame-illustration" role="img" aria-label="'+t('Qualitative flame shape')+'"><svg viewBox="0 0 120 150" width="120" height="150" aria-hidden="true"><path fill="#e3b787" d="'+paths[shape]+'"/></svg></div>',unsafe_allow_html=True)
    st.caption(t('Illustrative visualization — not a prediction, not experimental data'))
