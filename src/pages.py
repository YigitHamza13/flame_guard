"""Research workflow: context, specimen, evidence, gaps and a traceable export."""
import html
import json

import altair as alt
import pandas as pd
import streamlit as st

from src.evidence import (CATALOG, ENVIRONMENTS, ROOT, evidence_gaps, family, load_datasets,
                          material_keys, material_label, sample_rows, summary)
from src.labels import label
from src.extended_evidence import load_extension, eligible_measurements
from src.presentation import short_comparison, partial_comparison, source_cards
from src.charts import matrix_chart, oxygen_chart, distribution_charts, flame_illustration, chart_style
from src.research import api_key, ask_nasa_gemini
from src.screening import condition_comparison, csv_bytes, evidence_export, research_brief
from src.ui import badge, dataframe, environment_notice, heading, logo, metrics, planet, remember, t

BASS_IMAGE_SOURCE = "https://www.nasa.gov/image-article/astronaut-mike-hopkins-sets-up-bass-experiment/"


def data():
    tests, mappings, catalog, sources = load_datasets()[:4]
    return tests, mappings, catalog, sources + load_extension()[1]


def extended_panel(material=None, gravity_method=None):
    records, _, snapshot = load_extension()
    if material:
        records = [r for r in records if material.casefold() in r['material'].casefold()]
    if gravity_method:
        records = [r for r in records if r['gravity_method'] == gravity_method and r['review_status'] == 'source_checked']
    st.subheader(t('Study evidence') if gravity_method else t('Partial-gravity evidence'))
    types = {'measured_experiment': ('Measured experiment', 'Measured experiment'), 'theoretical_model': ('Theoretical model', 'Theoretical model'),
             'planned_experiment': ('Planned experiment', 'Planned experiment'), 'context_only': ('Context only', 'Context only')}
    for row in records:
        with st.expander(f"{row['id']} · {row['material']} · {t(row['evidence_type'])}"):
            st.write(row['title'])
            st.caption(f"{t(row['document_type'])} · {t(row['source_scope'])} · {t('Peer review: unknown')}")
            gravity = '—' if row['gravity_level_g'] is None else f"{row['gravity_level_g']:.6g} g"
            st.write(f"{t('Gravity')}: {gravity} · {t(row['gravity_method'])}")
            from src.summaries import NOTES_TR
            turkish = st.session_state.get("fg_lang") == "TR" and row['id'] in NOTES_TR
            st.caption(t('Source review notes'))
            st.write(NOTES_TR[row['id']] if turkish else row['notes'])
            if row['measurements']:
                dataframe(pd.DataFrame([{t('Field'): t(k), t('Value'): str(v) if v is not None else '—'} for k,v in row['measurements'].items()]))
            for page in row['source_pages']:
                st.markdown(f"[PDF {page}]({row['url']}#page={page})")
            st.caption(f"{row['review_status']} · {t('Human approval pending')} · SHA-256: {row.get('sha256') or '—'}")
    st.caption(t('Additional study records are separate from the original 11 compiled rows / 39 reported tests. Their total test counts are not supplied; specimens, papers and planned tests are never added to that total.'))
    st.download_button(t('Export classified evidence'), json.dumps({'snapshot':snapshot,'records':records}, ensure_ascii=False, indent=2), 'partial-gravity-evidence.json', 'application/json')


def name(key):
    from src import plain as _p
    if key in _p.EXTRA_KEYWORDS:
        return _p.extra_name(key)
    return material_label(key, st.session_state.get("fg_lang", "EN"))


def assumptions():
    """Saved user assumptions, else a labelled default (never presented as a NASA measurement of a mission)."""
    from src.plain import DEFAULT_ASSUMPTIONS
    env = st.session_state.mission_environment
    saved = st.session_state.get("mission_assumptions", {}).get(env)
    return saved if saved else dict(DEFAULT_ASSUMPTIONS.get(env, {}))


def next_step(page, en, tr):
    return


def context_image():
    st.image(str(ROOT / "assets/bass-ii-msg.jpg"), caption=t('BASS-II preparation in the ISS Destiny laboratory · NASA · 12 Feb 2014'), width="stretch")
    st.caption(t('Mike Hopkins preparing the Microgravity Science Glovebox. Experiment context; no institutional endorsement.'))
    st.markdown(f"[{t('Image source')}]({BASS_IMAGE_SOURCE})")


def comparison_panel(rows):
    st.markdown("**" + t('Mission assumptions versus reported conditions') + "**")
    a = assumptions()
    not_entered = t('Not entered')
    default_note = ""
    if a.get("default"):
        default_note = " · " + (a["note_tr"] if st.session_state.get("fg_lang") == "TR" else a["note_en"])
    st.caption(f"{label(st.session_state.mission_environment)} · O₂: {str(a['oxygen']) + ' %' if a.get('oxygen') is not None else not_entered} · "
               f"P: {str(a['pressure']) + ' kPa' if a.get('pressure') is not None else not_entered}{default_note}")
    compared = condition_comparison(rows, st.session_state.mission_environment, a)
    if compared.empty:
        st.info(t('No reference rows to compare. Add a sample or widen the filters.'))
        return
    frame = rows[["experiment_id", "gravity", "oxygen_pct", "pressure_kpa"]].copy().reset_index(drop=True)
    frame['experiment_id'] = [name(r.material) for _,r in rows.iterrows()]
    frame["gravity"] = frame.gravity.map(label)
    frame.columns = [t('Experiment'), t('Reported gravity'), t('Reported O₂ (%)'), t('Reported pressure (kPa)')]
    frame.insert(1, 'ID', rows.experiment_id.to_numpy())
    frame.insert(2, t('Test group'), rows.record_id.to_numpy())
    for col, field in [(t('Gravity comparison'), "gravity_match"),
                       (t('O₂ comparison'), "oxygen_match"),
                       (t('Pressure comparison'), "pressure_match")]:
        frame[col] = compared[field].map(label).replace(label("unknown"), "—").to_numpy()
    dataframe(frame)
    st.caption(t('Blank measurements are absent from the reviewed records. Enter mission oxygen and pressure in Environments to compare them. The 101.325 kPa values are study-wide conditions, not separate per-test pressure measurements.'))
    st.caption(t('Only gravity class, oxygen and pressure are compared. Equality is numerical, with no acceptance tolerance. Flow, geometry, uncertainty and mission phase still need review. No applicability approval or risk score is produced.'))


def sample_detail(material, tests, mappings):
    rows = sample_rows(tests, material)
    st.subheader(name(material))
    st.caption(t('Results apply to the tested specimen, not the whole material category.'))
    if rows.empty:
        st.info(t('No matched test summary. Test and ignition counts are unknown. This material remains in the research queue.'))
        return
    totals = summary(rows)
    metrics([(t('Reported tests'), totals["tests"], t('Compiled groups')),
             (t('Ignition count'), totals["ignited"], t('Only unambiguous reviewed outcomes'))])
    for _, group in rows.drop_duplicates("source_id").iterrows():
        notice = group.source_note_tr if st.session_state.fg_lang == "TR" else group.source_note_en
        (st.warning if group.review_status == "conflict" else st.info)(notice)
    st.caption(t('All rows await independent human approval. A local gas flame is not counted as sustained sample burning.'))
    frame = rows[["experiment_id", "ignition", "sustained", "propagation", "extinction", "test_count"]].copy()
    frame['experiment_id'] = [name(material) + ' · ' + str(r.record_id) for _,r in rows.iterrows()]
    st.caption(' · '.join('`'+str(x)+'`' for x in rows.experiment_id.unique()))
    for col in ("ignition", "sustained", "propagation", "extinction"):
        frame[col] = frame[col].map(label)
    frame.columns = [t('Experiment / sample'), label("Ignition"), label("Sustained burning"),
                     label("Flame spread"), label("Extinction"), t('Tests')]
    dataframe(frame)
    with st.expander(t('Reported conditions and sample geometry')):
        frame = rows[["experiment_id", "oxygen_pct", "pressure_kpa", "flow_cm_s", "geometry", "composition"]].copy()
        frame.columns = [t('Experiment'), "O₂ (%)", t('Pressure (kPa)'), t('Flow (cm/s)'), label("Geometry"), t('Composition')]
        dataframe(frame)
        st.caption(t('Geometry and composition retain the English source language. Blank values are unknown. A study-wide 1 atm condition is converted to 101.325 kPa; it is not a new per-test measurement. Source ranges are not assigned to individual tests.'))
    with st.expander(t('Primary documents and review trail')):
        _, _, _, passages = data()
        for source_id in rows.source_id.unique():
            subset = [s for s in passages if s["source_id"] == source_id]
            if not subset:
                st.warning(t('Verified file text unavailable; inspect the original source.'))
            for source in subset:
                st.link_button(f"{source['title']} · PDF {source['page']}", source["url"])
                st.caption(f"{source['location']} · {t('Accessed')}: {source['accessed_on']} · SHA-256: {source['sha256']}")
                st.text(source["text"])
        st.caption(t('Original English PDF extraction; layout/OCR errors are possible. File integrity and source inspection do not replace scientific peer review.'))
    with st.expander(t('Original import · historical fields')):
        st.warning(t('Uncorrected project compilation in Turkish. Legacy ignition values are retained for auditing and excluded from reviewed ignition totals.'))
        dataframe(rows[["experiment_id", "sample_material", "legacy_ignited", "raw_pressure_kpa", "flow", "mapping_note"]])


def _load_example():
    """Runs before the page is redrawn, so it may set widget-backed state (environment, cargo list)."""
    from src.plain import SUGGESTIONS
    tr = st.session_state.get("fg_lang") == "TR"
    st.session_state.saved_cargo_manifest = [p[1] if tr else p[0] for p in SUGGESTIONS if p[0] in (
        "Cotton T-shirt", "Headphone cable", "Silicone gasket", "Notebook", "Acrylic window", "Laptop")]
    st.session_state.pop("cargo_samples", None)
    st.session_state.mission_environment = "ISS"


def overview():
    tests, mappings, catalog, sources = data()
    left, right = st.columns([1.05, 1.25], gap="large")
    with left:
        planet(350)
    with right:
        st.markdown('<div class="hero-title">' + t('Combustion research') + '</div>', unsafe_allow_html=True)
        st.write(t('Experiment records, sample properties and test conditions.'))
        st.markdown(t('**Start here:** 1) pick a place · 2) type your cargo in everyday words · 3) read what NASA found, with the report page.'))
        with st.container(key="overview_actions"):
            if st.button(" " + t('Try an example cargo'), key="try_example", type="primary", width="stretch",
                         on_click=_load_example):
                st.switch_page(st.session_state.pages["cargo"])
            if st.button(t('Cargo screening'), key="open_screening", width="stretch"):
                st.switch_page(st.session_state.pages["cargo"])
            if st.button(t('Environments'), key="open_environments", width="stretch"):
                st.switch_page(st.session_state.pages["environment"])
    metrics([(t('Catalog records'), len(catalog), ""),
             (t('Sample groups'), mappings.input_material.nunique(), ""),
             (t('Source documents'), len({s["source_id"] for s in sources}), ""),
             (t('Reported tests'), summary(tests)["tests"], "")])
    st.caption(t('A 276-page NASA source pack; the assistant searches 41 checked passages offline, in English and Turkish. Every number links to its report page.'))
    left, right = st.columns([1.3, 1], gap="large")
    with left:
        st.subheader(t('Experiments by family'))
        frame = pd.Series([label(family(r)) for r in catalog]).value_counts().rename_axis("Family").reset_index(name="Records")
        chart = alt.Chart(frame).mark_bar(color="#8EBBFF", cornerRadiusEnd=3).encode(
            x=alt.X("Records:Q", title=t('Records'), axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("Family:N", sort="-x", title=None), tooltip=[alt.Tooltip('Family:N',title=t('Family')),alt.Tooltip('Records:Q',title=t('Records'))])
        st.altair_chart(chart_style(chart.properties(height=260)), width="stretch")
        from src.access import chart_table
        chart_table(frame.rename(columns={"Family": t('Family'), "Records": t('Records')}))
        st.caption(t('context_only'))
        st.caption(t('GRADFLEX and PBRE: Fluid Physics.'))
    with right:
        st.subheader(t('Data notes'))
        st.write(t('SIBAL ignition counts remain disputed. All records await independent review.'))
        st.write(t('No measured Mars records in this collection.'))
        st.page_link(st.session_state.pages["methodology"], label=t('Sources and methodology'))
    source_cards()
    matrix_chart(tests, sources)


def environments():
    st.caption(t('The environment selected here changes the whole application.'))
    heading(t('Environment Explorer'), t('Define assumptions, then compare them with reported experiment conditions.'))
    if st.session_state.mission_environment not in ENVIRONMENTS:
        st.session_state.mission_environment = "Moon Base"
    env = st.session_state.mission_environment
    a, b = st.columns([1.1, 1])
    with a:
        planet(420)
    with b:
        st.subheader(label(env))
        environment_notice()
        current = assumptions()
        with st.form(f"assumptions_{env}"):
            st.markdown("**" + t('Mission assumptions · user input') + "**")
            oxygen = st.number_input(t('Assumed oxygen (%)'), value=current.get("oxygen"), step=0.1, placeholder=t('Enter volume percent'), key=f'o2_{env}')
            pressure = st.number_input(t('Assumed pressure (kPa)'), value=current.get("pressure"), step=0.1, placeholder=t('Enter absolute pressure'), key=f'p_{env}')
            phase = st.text_input(t('Atmosphere / mission phase (context only)'), value=current.get("atmosphere", ""), key=f'phase_{env}', placeholder=t('Type to search or enter context'))
            if st.form_submit_button(t('Save and compare'), type="primary"):
                if (oxygen is not None and not 0<=oxygen<=100) or (pressure is not None and not 0<=pressure<=1000):
                    st.warning(t('Enter O₂ between 0–100% and pressure between 0–1000 kPa.'))
                else:
                    st.session_state.setdefault("mission_assumptions", {})[env] = {"oxygen": oxygen, "pressure": pressure, "atmosphere": phase}
                    st.success(t('Assumptions saved. Cargo exports now use them.'))
            def reset_assumptions():
                st.session_state.setdefault('mission_assumptions', {}).pop(env, None)
                st.session_state[f'o2_{env}'] = None
                st.session_state[f'p_{env}'] = None
                st.session_state[f'phase_{env}'] = ''
            st.form_submit_button(t('Reset'), on_click=reset_assumptions)
        st.caption(t('Blank inputs remain unknown. Assumptions are not NASA measurements. Mars gravity remains unspecified until a quantitative mission-phase model exists.'))
    tests, _, _, _ = data()
    from src import risk
    st.markdown(risk.CSS, unsafe_allow_html=True)
    st.subheader(t('Risk factors in the cabin environment'))
    st.caption(t('What NASA flight tests showed about the conditions around a fire. Each row links to the report page.'))
    st.markdown(risk.env_table_html(), unsafe_allow_html=True)
    from src import access
    access.glossary()
    short_comparison()
    extended_panel(gravity_method='ground_1g' if env=='Earth Lab' else None)
    oxygen_chart()
    flame_illustration()
    next_step("cargo", "Continue · Choose specimens", "Devam · Numuneleri seç")


def cargo():
    heading(t('Cargo Screening'), t('Inspect reference specimens and export the evidence with its research context.'))
    tests, mappings, _, _ = data()
    keys = material_keys(tests, mappings)
    environment_notice()
    st.session_state.setdefault("saved_cargo_manifest", keys)
    from src import plain
    typed_before = [k for k in st.session_state.saved_cargo_manifest if k not in keys]
    options = list(dict.fromkeys([*keys, *plain.suggestions(), *typed_before]))
    selected = st.multiselect(t('Your cargo · pick a NASA specimen or type your own item'), options,
                             default=list(st.session_state.saved_cargo_manifest),
                             format_func=name, key="cargo_samples", accept_new_options=True,
                             placeholder=t('e.g. cotton t-shirt, cable, rubber seal, notebook'))
    st.session_state.saved_cargo_manifest = selected
    queue = st.checkbox(t('Include PMMA · study evidence available; no compiled test count'))
    typed = selected + (["plastik (pmma)"] if queue else [])
    known = list(dict.fromkeys([*keys, *CATALOG]))
    statuses = {item: plain.classify(item, known) for item in typed}
    asks = [(item, opts) for item, (status_, _k, opts) in statuses.items() if status_ == "ask"]
    if asks:
        st.markdown("**" + t('Which material?') + "**")
        st.caption(t('These items come in several materials. Pick one so FLAMEGUARD can show the matching NASA specimen; it never guesses.'))
        for item, opts in asks:
            st.selectbox(t('What is “{item}” made of?', item=item), [*opts, plain.OTHER], index=None, key=f"mat::{item}",
                         format_func=lambda k: t('Something else (no NASA test in this collection)') if k == plain.OTHER else name(k),
                         placeholder=t('Choose a material'))
    pairs, status_of = [], {}
    for item in typed:
        status_, key, _opts = statuses[item]
        if status_ == "ask":
            key = plain.resolve(item, known, st.session_state.get(f"mat::{item}"))
        word = name(item) if item in known else item
        pairs.append((word, key))
        status_of[word] = status_ if key is None else "match"
    chosen = list(dict.fromkeys(k if k else word for word, k in pairs))
    with st.expander(t('Filter reference conditions')):
        strict = st.checkbox(t('Filter by reported oxygen'))
        oxygen = st.slider(t('Oxygen range (%)'), 0.0, 100.0, (16.0, 23.0), 0.1)
        st.caption(t('The filter applies to every result on this page: counters, cards, tables, the PDF and the exports. Unknown oxygen is excluded when enabled.'))
    filters = {"oxygen_enabled": strict, "oxygen_range": list(oxygen)}
    if st.button(t('Scan selected samples'), type="primary", width="stretch"):
        st.cache_data.clear()
        tests, mappings, _, _ = data()
        st.success(t('Reference records refreshed. Results use the current selections and filters.'))
    # One evidence scope for every output on this page.
    from src.screening import scope
    scoped, ex_scope = scope(tests, plain.extras(), filters)
    reference = scoped[scoped.material.isin(chosen)]
    has_ev = lambda k: bool(k) and (k in ex_scope or not sample_rows(scoped, k).empty)
    existed = lambda k: bool(k) and (k in plain.extras() or not sample_rows(tests, k).empty)
    keys_chosen = [k for k in chosen if k in known or k in plain.EXTRA_KEYWORDS]
    count = sum(1 for k in keys_chosen if has_ev(k))
    metrics([(t('Selected'), len(chosen), t('Specimen groups')),
             (t('With references'), count, t('Under current filters')),
             (t('Without references'), len(chosen) - count, t('Needs research'))])
    if not chosen:
        from src.plain import page_mood
        page_mood([])
        st.info(t('Choose a specimen to begin.'))
        return
    st.markdown(plain.CSS, unsafe_allow_html=True)
    from src import access
    access.enable_read_aloud()
    st.subheader(t('What NASA found, in one sentence per item'))
    st.caption(plain.legend())
    tones, card_list = [], []
    env = st.session_state.mission_environment
    for word, key in pairs:
        if key is None and status_of.get(word) in ("ask", "other_material"):
            card_html, tone = plain.status_card(word, status_of[word])
        else:
            card_html, tone = plain.card(word, key, sample_rows(scoped, key) if key else tests.iloc[0:0], env,
                                         name(key) if key else word, extra_scope=ex_scope,
                                         filtered_out=bool(strict and existed(key) and not has_ev(key)))
        tones.append(tone)
        card_list.append(card_html)
        st.markdown(card_html, unsafe_allow_html=True)
    plain.page_mood(tones)
    from src import worlds
    st.subheader(t('Same cargo, two worlds'))
    st.caption(t('The same items in microgravity experiments and on the Moon, side by side. Gravity changes how a flame behaves, so evidence from one place is never reused for the other.'))
    st.markdown(worlds.CSS, unsafe_allow_html=True)
    st.markdown(worlds.two_worlds_html(pairs, scoped, ex_scope), unsafe_allow_html=True)
    from src import risk
    cargo_table = risk.material_table_html(pairs, scoped, env, name, ex_scope)
    env_table = risk.env_table_html()
    st.session_state["_report_parts"] = (card_list, cargo_table, env_table)
    with st.expander(t('Risk factor tables · every factor with its report page')):
        st.markdown(risk.CSS, unsafe_allow_html=True)
        st.markdown("**" + t('Risk factor table · your cargo') + "**")
        st.caption(risk.legend())
        st.markdown(cargo_table, unsafe_allow_html=True)
        st.markdown("**" + t('Risk factors in the cabin environment') + "**")
        st.caption(t('What NASA flight tests showed about the conditions around a fire. Each row links to the report page.'))
        st.markdown(env_table, unsafe_allow_html=True)
    access.glossary()
    with st.expander(t('Charts, condition comparison and record details')):
        st.markdown("**" + t('Reported outcomes by compiled row') + "**")
        st.caption(t('No validated risk score is available. This chart shows reported outcomes by compiled row, not a safety probability or a count of individual tests.'))
        if any(k in ex_scope for k in chosen):
            st.caption(t('Specimens from the separate verified table (for example PMMA, Nomex, cotton jersey) are in the cards, tables and exports, but not in this row chart.'))
        outcomes = reference[["ignition", "sustained", "propagation", "extinction"]].rename(columns={
            "ignition": label("Ignition"), "sustained": label("Sustained burning"),
            "propagation": label("Flame spread"), "extinction": label("Extinction")}).melt(var_name="Outcome", value_name="Status")
        if not outcomes.empty:
            outcomes["Status"] = outcomes.Status.map(label)
            counts = outcomes.groupby(["Outcome", "Status"]).size().reset_index(name="Rows")
            chart = alt.Chart(counts).mark_bar().encode(
                y=alt.Y("Outcome:N", title=None), x=alt.X("Rows:Q", title=t('Compiled rows'), axis=alt.Axis(tickMinStep=1)),
                color=alt.Color("Status:N", title=t('Outcome'), scale=alt.Scale(
                    domain=[label(x) for x in ["observed", "not_observed", "disputed", "unknown", "local_gas_flame"]],
                    range=["#e3b787", "#a5b9d2", "#ffb487", "#b6a6e8", "#edce81"]), legend=alt.Legend(orient="bottom", labelLimit=350)), tooltip=["Outcome", "Status", "Rows"])
            st.altair_chart(chart_style(chart.properties(height=240)), width="stretch")
            from src.access import chart_table
            chart_table(counts.rename(columns={"Outcome": t('Outcome'), "Status": t('Status'), "Rows": t('Compiled rows')}))
            st.caption(t('measured_experiment'))
        comparison_panel(reference)
        partial_comparison(assumptions())
        for material in chosen:
            if material in known:
                st.markdown("**" + name(material) + "**")
                sample_detail(material, reference, mappings)
    export = evidence_export(tests, chosen, env, assumptions(), filters, tests.attrs["snapshot"],
                             extras=plain.extras(), item_status=status_of, pairs=pairs)
    st.subheader(t('Source-linked research package'))
    st.caption(t('Every download uses the same evidence and filter as the cards above: compiled rows, the separate verified table and items without evidence.'))
    report_pdf = None
    try:
        from src import report
        cards_, cargo_, env_ = st.session_state.get("_report_parts", ([], "", ""))
        a_ = assumptions()
        note = a_.get("note_tr" if st.session_state.fg_lang == "TR" else "note_en", "")
        assumed = f"O₂ {a_.get('oxygen', '–')} %, {a_.get('pressure', '–')} kPa" + (f" ({note})" if note else "")
        if strict:
            assumed += " · " + t('Oxygen filter: {a}–{b} %', a=oxygen[0], b=oxygen[1])
        report_pdf = report.build(t(ENVIRONMENTS[env]["name"]), assumed, str(tests.attrs.get("snapshot", "")),
                                  cards_, cargo_, env_)
    except Exception as exc:  # the other exports must keep working even if PDF layout fails
        st.caption(t('PDF report could not be created: {e}', e=type(exc).__name__))
    st.markdown("**" + t('Printable mission report') + "**")
    st.caption(t('One PDF with the plain sentences, the risk factor tables and every report link — ready to print or attach.'))
    if report_pdf:
        st.download_button(" " + t('Download PDF report'), report_pdf, "flameguard-cargo-report.pdf", "application/pdf",
                           type="primary")
    a, b, c = st.columns(3)
    a.download_button(t('Evidence CSV'), csv_bytes(export), "cargo-evidence.csv", "text/csv")
    b.download_button(t('Manifest JSON'), export.to_json(orient="records", force_ascii=False, indent=2), "cargo-evidence.json", "application/json")
    c.download_button(t('Research brief'), research_brief(export, st.session_state.fg_lang), "research-brief.md", "text/markdown")
    next_step("gaps", "Continue · Review missing evidence", "Devam · Kanıt eksiklerini incele")


def materials():
    heading(t('Material Explorer'), t('Inspect specific samples and the limits of their general-material mappings.'))
    tests, mappings, _, _ = data()
    keys = material_keys(tests, mappings)
    focus = st.session_state.pop("focus_material", None)
    if focus:
        st.session_state["material_profile"] = focus
        st.session_state["material_query"] = ""
        st.session_state["material_category"] = "All"
    a, b = st.columns([2, 1])
    query = a.text_input(t('Search specimens or everyday items'), key="material_query", placeholder=t('e.g. T-shirt, water bottle, phone cable, gasket'))
    category = b.selectbox(t('Category'), ["All"] + sorted({CATALOG[k][2] for k in keys}), format_func=label, key="material_category")
    from src import plain
    keys = list(dict.fromkeys([*keys, *CATALOG]))
    results = [k for k in keys if plain.matches(k, name(k), query) and category in ("All", CATALOG[k][2])]
    if not results:
        st.info(t('No matching specimen. Clear the search or category filter.'))
    else:
        if st.session_state.get("material_profile") not in results:
            st.session_state["material_profile"] = results[0]
        selected = st.selectbox(t('Specimen profile'), results, format_func=name, key="material_profile")
        remember(t('Material'), name(selected))
        st.markdown(plain.CSS, unsafe_allow_html=True)
        st.markdown(plain.everyday_html(selected), unsafe_allow_html=True)
        sample_detail(selected, tests, mappings)
        from src import ntrs
        ntrs.panel(selected, name(selected))
        compare = st.multiselect(t('Compare evidence quantity'), results, format_func=name, placeholder=t('Choose specimens'))
        if compare:
            dataframe(pd.DataFrame([{t('Specimen'): name(k), t('Tests'): summary(sample_rows(tests, k))["tests"],
                                    t('Ignition count'): summary(sample_rows(tests, k))["ignited"]} for k in compare]))
            st.caption(t('Counts cannot rank safety; conditions and specimens differ.'))
    with st.expander(t('Research queue · PMMA')):
        extended_panel('PMMA')
    from src import plain
    ex = plain.extras()
    st.subheader(t('More NASA specimens · separate verified table'))
    st.caption(t('Five more NASA flight specimens, each row with its NASA report page. Kept separate from the 11 compiled rows / 39 tests above.'))
    extra_keys = [k for k in ex if plain.matches(k, plain.extra_name(k), query)] or list(ex)
    pick = st.selectbox(t('Specimen'), extra_keys, format_func=plain.extra_name, key="extra_specimen")
    st.markdown(plain.CSS, unsafe_allow_html=True)
    from src import access
    access.enable_read_aloud()
    st.markdown(plain.extra_card(plain.extra_name(pick), pick, "ISS")[0], unsafe_allow_html=True)
    st.markdown(plain.everyday_html(pick), unsafe_allow_html=True)
    from src import ntrs
    ntrs.panel(pick, plain.extra_name(pick))
    access.glossary()
    dataframe(pd.DataFrame([{t('Specimen'): plain.extra_name(k), t('Tests'): v["tests"], t('Ignition count'): v["ignited"],
                             "O₂ (%)": plain._fmt_range(v["oxygen_pct"], ""), "P (kPa)": plain._fmt_range(v["pressure_kpa"], ""),
                             t('Experiment'): ", ".join(v["experiments"])} for k, v in ex.items()]))
    next_step("gaps", "Continue · Evidence completeness and mission comparison", "Devam · Veri doluluğu ve görev karşılaştırması")


# Catalog experiments that flew a specimen (or, for Saffire-V/VI specimens, the same Saffire series), as stated in the cited reports.
RELATED_EXPERIMENTS = {"pamuklu kumaş": ["BASS", "BASS-II", "SAFFIRE-II"], "kauçuk": ["SAFFIRE-II"], "pmma_extra": ["SAFFIRE-II"],
                       "nomex_extra": ["SAFFIRE-II"], "jersey_extra": ["SAFFIRE-I", "SAFFIRE-II", "SAFFIRE-III"]}


def _go_cargo(item):
    st.session_state.saved_cargo_manifest = [item]
    st.session_state.pop("cargo_samples", None)


def item_lookup(query, catalog):
    """An everyday item typed in the experiment search: explain the match and return related catalog records."""
    from src import plain
    status, key, _opts = plain.classify(query, list(CATALOG))
    if status in ("match", "known") and key:
        tests = data()[0]
        rows = sample_rows(tests, key) if key in CATALOG else tests.iloc[0:0]
        from src.links import platform
        where = platform(plain.extras()[key]["experiments"], st.session_state.get("fg_lang") == "TR") if key in plain.extras() \
            else platform(rows.experiment_id.dropna().unique(), st.session_state.get("fg_lang") == "TR")
        st.info(t('“{q}” is an everyday item, not an experiment name. Closest NASA-tested specimen: {s}. Flown on: {w}.',
                  q=query, s=name(key), w=where or t('not reported')))
        related = RELATED_EXPERIMENTS.get(key, [])
        st.caption(t('Experiments in this catalog that flew this specimen or its experiment series are listed below.') if related
                   else t('The experiment that tested this specimen is not in this catalog; its report is linked in Cargo Screening.'))
    elif status == "ask":
        st.info(t('“{q}” is an everyday item that comes in several materials. Open it in Cargo Screening and choose the material.', q=query))
        related = []
    else:
        st.info(t('No experiment and no tested specimen match “{q}”. Missing data does not mean safe.', q=query))
        related = []
    st.button(t('See what NASA found for “{q}” in Cargo Screening', q=query), on_click=_go_cargo, args=(query,), type="primary")
    if st.session_state.get("pages"):
        st.page_link(st.session_state.pages["cargo"], label=t('Open Cargo Screening'))
    return [r for r in catalog if (r.get("acronym") or "") in related]


def experiments():
    heading(t('Experiment Library'), t('Browse catalog metadata separately from sample-level findings.'))
    _, _, catalog, _ = data()
    focus = st.session_state.pop("focus_experiment", None)
    if focus:
        st.session_state["experiment_query"] = ""
        st.session_state["experiment_family"] = "All"
        st.session_state["experiment_area"] = "All"
        st.session_state["experiment_profile"] = focus
    st.caption(t('This page lists NASA combustion experiments: name, aims and where they flew. To check an everyday item such as a T-shirt, type it here or use Cargo Screening.'))
    a, b, c = st.columns([2, 1, 1])
    query = a.text_input(t('Search experiments'), key="experiment_query", placeholder=t('Experiment (Saffire, BASS, FLEX) or an everyday item (T-shirt)'))
    selected_family = b.selectbox(t('Family'), ["All"] + sorted({family(r) for r in catalog}), format_func=label, key="experiment_family")
    area = c.selectbox(t('Research area'), ["All"] + sorted({r.get("research_area", "Unknown") for r in catalog}), format_func=label, key="experiment_area")
    records = [r for r in catalog if query.casefold() in json.dumps(r, ensure_ascii=False).casefold()
               and selected_family in ("All", family(r)) and area in ("All", r.get("research_area"))]
    looked_up = False
    if query.strip() and not records:
        records, looked_up = item_lookup(query.strip(), catalog), True
    st.caption(t('Original English catalog text · metadata does not establish experimental findings.'))
    if not records:
        if not looked_up:
            st.info(t('No catalog records match. Widen the filters.'))
        return
    lookup = {r["accession"]: r for r in records}
    if st.session_state.get("experiment_profile") not in lookup:
        st.session_state["experiment_profile"] = next(iter(lookup))
    selected = st.selectbox(t('Experiment profile'), list(lookup), key="experiment_profile", format_func=lambda k: f"{k} · {lookup[k]['title']}")
    record = lookup[selected]
    from src.theme import gravity_badge
    badge(gravity_badge(record, st.session_state.mission_environment))
    remember(t('Experiment'), record.get("acronym") or record["title"])
    badge(t('Original English'))
    st.subheader(record["title"])
    st.caption(label(record.get("research_area", "unknown")))
    st.caption(f"{record.get('flight_platform', '')} · {family(record)}")
    for field, en, tr in [("objectives", "Objectives", 'Objectives'), ("approach", "Approach", 'Approach'), ("hypothesis", "Hypothesis", "Hipotez"), ("earth_benefits", "Reported catalog benefits", "Katalogda belirtilen faydalar")]:
        with st.expander(t(en), expanded=field == "objectives"):
            st.write(record.get(field) or t('Not available'))
    if record.get("source_url"):
        st.link_button(t('Open NASA PSI record'), record["source_url"])
    with st.expander(t('Publications · original source language')):
        for publication in record.get("publications", []):
            st.write(publication)
    st.download_button(t('Export catalog record'), json.dumps(record, ensure_ascii=False, indent=2), f"{selected}.json", "application/json")
    next_step("materials", "Continue · Inspect sample findings", "Devam · Numune bulgularını incele")


def gaps():
    heading(t('Evidence Gaps'), t('Distinguish populated fields from evidence that matches your mission conditions.'))
    tests, mappings, _, _ = data()
    from src import worlds
    from src.plain import EVERYDAY, extras as _extras
    st.subheader(t('Tests NASA still needs to fly'))
    st.caption(t('Found by fixed rules from the gaps in this collection. The order is only the number of specimens each test would cover — not scientific importance, urgency or risk. A list of missing evidence, not a forecast of results.'))
    st.markdown(worlds.CSS, unsafe_allow_html=True)
    st.markdown(worlds.wishlist_html(worlds.wishlist(tests, _extras(), name), EVERYDAY), unsafe_allow_html=True)
    keys = material_keys(tests, mappings) + ["plastik (pmma)"]
    chosen = st.multiselect(t('Specimens to inspect'), keys, default=keys, format_func=name, placeholder=t('Choose specimens'))
    environment_notice()
    frame = evidence_gaps(tests, chosen)
    if frame.empty:
        st.info(t('Choose a specimen to inspect.'))
        return
    st.subheader(t('1 · Structured field completeness'))
    display = frame.copy()
    replacements = {material_label(k): name(k) for k in chosen}
    display["Material"] = display.Material.map(replacements)
    display["Variable"] = display.Variable.map(label)
    display["Status"] = display.Status.map(label)
    chart = alt.Chart(display).mark_rect(stroke="#0B1220", strokeWidth=3).encode(
        x=alt.X("Variable:N", axis=alt.Axis(labelAngle=-35, labelLimit=250, labelFontSize=13), title=None), y=alt.Y("Material:N", title=None, axis=alt.Axis(labelLimit=450, labelOverlap=False, labelFontSize=13)),
        color=alt.Color("Status:N", title=t('Status'), scale=alt.Scale(
            domain=[label(x) for x in ["Reported", "Partly reported", "Not reported", "Unknown", "Disputed"]],
            range=["#7ad7bb", "#edce81", "#91a0b4", "#b6a6e8", "#ffb487"]), legend=alt.Legend(orient="bottom", labelLimit=250)),
        tooltip=[alt.Tooltip("Material", title=t('Specimen')), alt.Tooltip("Variable", title=t('Variable')), alt.Tooltip("Status", title=t('Status'))])
    display['Symbol'] = display.Status.map({label('Reported'):'●', label('Partly reported'):'◐', label('Not reported'):'—', label('Unknown'):'?', label('Disputed'):'!'})
    text = alt.Chart(display).mark_text(fontSize=18,color='#080d16').encode(x='Variable:N',y='Material:N',text='Symbol:N')
    st.altair_chart(chart_style((chart + text).properties(height=max(300, len(chosen) * 72))), width="stretch")
    from src.access import chart_table
    chart_table(display[["Material", "Variable", "Status", "Symbol"]].rename(
        columns={"Material": t('Specimen'), "Variable": t('Variable'), "Status": t('Status')}))
    st.caption(t('context_only'))
    st.caption(t('Reported means populated, possibly qualitative. Unknown means no matching rows. Disputed means a source conflict. Missing data never means no ignition or low risk.'))
    st.subheader(t('2 · Mission condition comparison'))
    short_comparison()
    source_map={material_label(k): '; '.join(sorted(set(tests.loc[tests.material.eq(k),'source_url'].dropna()))) for k in chosen}
    export_frame=frame.assign(source=frame.Material.map(source_map), evidence_type='context_only', snapshot_sha256=tests.attrs['snapshot'], selected_environment=st.session_state.mission_environment)
    st.download_button(t('Export completeness matrix'), csv_bytes(export_frame), "evidence-gaps.csv", "text/csv")
    ext = eligible_measurements(load_extension()[0])
    st.subheader(t('Partial-gravity coverage'))
    dataframe(pd.DataFrame([{t('Study'): r['id'], t('Gravity method'): r['gravity_method'],
                             'g': r['gravity_level_g'], t('Scope'): r['source_scope'], t('Test count'): None} for r in ext]))
    distribution_charts()
    next_step("cargo", "Continue · Export a source-linked brief", "Devam · Kaynaklı özeti indir")


def item_answer(question):
    """A question about an everyday item is answered with the same sentence as its Cargo Screening card."""
    from src import plain
    from src.report import card_parts
    status, key, _opts = plain.classify(question, list(CATALOG))
    if status == "ask":
        return t('This item comes in several materials. Open Cargo Screening and choose what it is made of; FLAMEGUARD does not guess.'), None
    if status == "other_material":
        return t('You named a material that NASA did not test in this collection (for example glass, metal or polyester). It is not matched to a different material. Missing data does not mean safe.'), None
    if status in ("match", "known") and key:
        tests = data()[0]
        html_, _tone = plain.card(question, key, sample_rows(tests, key) if key in CATALOG else tests.iloc[0:0],
                                  st.session_state.get("mission_environment", "ISS"), name(key))
        c = card_parts(html_)
        return f"{name(key)}: {c['text']}", t('Closest NASA-tested specimen, not your exact product.') + (" " + c["next"] if c["next"] else "")
    return None, None


def assistant():
    heading(t('Research Assistant'), t('Find relevant primary-source passages and compare them with the original PDF.'))
    _, _, catalog, sources = data()
    configured = bool(api_key())
    ai_enabled = st.toggle(t('Use Gemini to select excerpts'), value=False, disabled=not configured)
    st.caption(t('When enabled, the question and public source passages are sent to Gemini. Keys stay on the server. Local search works without an API key.'))
    if not configured:
        st.success(t('Local search is working now: ask a question below and you get NASA passages with page links and a plain summary — no key needed.'))
        with st.expander(" " + t('Turn on Gemini (optional)')):
            st.markdown(t('**On the live site:** the site owner adds `GEMINI_API_KEY = "..."` once under Streamlit Cloud → App settings → Secrets. Visitors never need a key.\n\n'
                          '**On your own computer:** 1) get a free key at Google AI Studio (aistudio.google.com); 2) in the app folder copy `.env.example` to `.env`; '
                          '3) write your key after `GEMINI_API_KEY=`; 4) restart the app.\n\n'
                          'Never share a key in a ZIP, a chat or a public file — anyone who has it can use your quota.'))
    st.info(t('Passages are extracted from saved NASA PDFs with checked file hashes. Human scientific approval is pending. Related passages are not presented as validated answers.'))
    suggestions = [('How does fire behave in space?', 'How does fire behave in space?'), ('Does a headphone cable burn in space?', 'Does a headphone cable burn in space?'), ('When did the smoke alarm go off?', 'When did the smoke alarm go off?'), ('Has anything been burned on the Moon?', 'Has anything been burned on the Moon?'), ('What did LUCI measure for PMMA?', 'What did LUCI measure for PMMA?'), ('How do astronauts put out a fire?', 'How do astronauts put out a fire?'), ('Which material is the most dangerous?', 'Which material is the most dangerous?'), ('Where does the data come from?', 'Where does the data come from?')]
    if st.session_state.mission_environment == 'Moon Base':
        suggestions.sort(key=lambda pair: 'Moon' not in pair[0])
    elif st.session_state.mission_environment == 'Mars Mission':
        suggestions.insert(0, ('Which measured Mars results are available?', 'Which measured Mars results are available?'))
    selected_question = None
    with st.container():
        chips = st.columns(2)
        for i, pair in enumerate(suggestions):
            if chips[i % 2].button(t(pair[0]), key=f"suggest_{i}", width="stretch"):
                selected_question = t(pair[0])
    history = st.session_state.setdefault("research_history", [])
    if not history:
        st.caption(t('Choose a question or search the local PDF collection below. No API key is needed for local search.'))
    question = st.chat_input(t('Ask about a specimen or experiment')) or selected_question
    if question:
        with st.spinner(t('Searching primary passages…')):
            history.append(ask_nasa_gemini(question, catalog, sources, ai_enabled))
        st.session_state.research_history = history[-20:]
        history = st.session_state.research_history
    notices = {
        "unanswered": ("No answer was found in the available primary-source collection.", 'No answer was found in the available primary-source collection.'),
        "future_unanswered": ("The collection cannot answer future mission or manifest decisions. No supported answer is available.", 'The collection cannot answer future mission or manifest decisions. No supported answer is available.'),
        "related_only": ("Related passages found. Whether they answer the question requires source review.", 'Related passages found. Whether they answer the question requires source review.'),
        "ai_fallback": ("No valid AI excerpt was returned. Local search supplied related passages; no validated answer is claimed.", 'No valid AI excerpt was returned. Local search supplied related passages; no validated answer is claimed.')}
    from src.summaries import summary_for
    from src.answers import short_answer
    lang = st.session_state.get("fg_lang", "EN")
    st.markdown("""<style>.fg-answer{font-size:19px;line-height:1.55;font-weight:600;padding:14px 18px;border-left:5px solid #ff8a3d;
    background:rgba(255,138,61,.08);border-radius:8px;margin:4px 0 8px}.fg-means{color:var(--muted,#abbace);margin:0 0 6px}</style>""",
                unsafe_allow_html=True)
    for answer in history:
        with st.chat_message("user"):
            st.write(answer["question"])
        with st.chat_message("assistant"):
            excerpts = answer["excerpts"]
            from src.answers import resolve_answer
            resolved = resolve_answer(answer["question"], lang, t)
            short, means = resolved["answer"], resolved["meaning"]
            from_glossary = resolved["kind"] == "glossary"
            related_note, topic_src = None, None
            if resolved["sources"]:
                ref = resolved["sources"][0]
                topic_src = (f"{ref['id']} · PDF {ref['page']}", ref['url'])
            if short:
                st.markdown("<div class='fg-answer'>" + html.escape(t(short)) + "</div>", unsafe_allow_html=True)
                if means:
                    st.markdown("<p class='fg-means'> <b>" + html.escape(t('What it means')) + ":</b> " + html.escape(t(means)) + "</p>",
                                unsafe_allow_html=True)
            else:
                st.info(t('No direct answer to this question in this NASA collection. FLAMEGUARD does not make one up.'))
                if related_note:
                    st.caption(t('Related NASA source (not an answer)') + ": " + related_note)
            if topic_src:
                st.markdown(f" **{t('Source')}:** {html.escape(topic_src[0])}")
                for ref in resolved["sources"]:
                    st.link_button(t('Open the NASA PDF page') + f" · {ref['id']} / {ref['page']}", ref['url'])
            elif excerpts:
                first = excerpts[0]
                st.markdown(f" **{t('Related source') if from_glossary or not short else t('Source')}:** {html.escape(first['title'])} · PDF {first['page']}")
                st.link_button(t('Open the NASA PDF page'), first["url"])
            if answer.get("lunar"):
                lunar = [r for r in eligible_measurements(load_extension()[0]) if r['gravity_class'] == 'lunar']
                st.warning(t('{v0} checked lunar-gravity study records are available. Simulated gravity does not establish lunar-surface material approval.', v0=len(lunar)))
            if excerpts:
                with st.expander(t('Proof: the original NASA text ({n} passages, English)', n=len(excerpts))):
                    st.caption((t('AI-selected excerpts · text match checked') if answer["mode"] == "ai_excerpts" else t('Local passage search'))
                               + " · " + t(notices.get(answer["notice"], notices["unanswered"])[0]))
                    for excerpt in excerpts:
                        st.markdown(f"**{html.escape(excerpt['title'])} · PDF {excerpt['page']}**")
                        st.caption(f"{excerpt.get('evidence_type', 'measured_experiment').replace('_', ' ')} · {excerpt.get('document_type', 'unknown').replace('_', ' ')} · {t('Human approval pending')}")
                        st.markdown("> " + excerpt["quote"].replace("\n", " "))
                        st.markdown(f"[{t('Inspect source page')}]({excerpt['url']}) · SHA-256 `{excerpt['sha256'][:12]}…` · {excerpt['accessed_on']}")
    if history:
        st.download_button(t('Export research history'), json.dumps(history, ensure_ascii=False, indent=2), "research-history.json", "application/json")
    next_step("methodology", "Continue · Review the method and sources", "Devam · Yöntem ve kaynakları incele")


def methodology():
    from src.ui import evidence_status
    evidence_status()
    heading(t('Methodology & Sources'), t('Inspect provenance, calculations and the remaining review requirements.'))
    tests, mappings, catalog, sources = data()
    from src.assistant_eval import load_current
    benchmark = load_current()
    if benchmark:
        st.subheader(t('Offline assistant evaluation'))
        st.caption(t('Local regression questions; not independent scientific validation.'))
        dataframe(pd.DataFrame([
            {t('Measure'): t('Correct source'), t('Result'): f"{benchmark['source_correct']}/{benchmark['source_total']}"},
            {t('Measure'): t('Abstained without evidence'), t('Result'): f"{benchmark['abstained']}/{benchmark['absent_total']}"},
            {t('Measure'): t('Correct answer type'), t('Result'): f"{benchmark['kind_correct']}/{benchmark['question_count']}"}]))
    else:
        st.caption(t('Assistant evaluation is missing or outdated. Run the evaluation script again.'))

    st.info(t('Independent research support. NASA approval, flight qualification and a validated safety model have not been established.'))
    sections = [
        ("Data and review", "Veri ve inceleme", "11 compiled rows and 39 reported tests are retained losslessly in versioned SQLite snapshots. The original CSV values, reviewed fields, PDF hashes, page references and reviewer are preserved. Human approval remains pending for all rows. Catalog records are metadata, not measured outcomes.", '11 compiled rows and 39 reported tests are retained losslessly in versioned SQLite snapshots. The original CSV values, reviewed fields, PDF hashes, page references and reviewer are preserved. Human approval remains pending for all rows. Catalog records are metadata, not measured outcomes.'),
        ("Counting rules", 'Counting rules', "Reported tests sum test_count. Ignition totals require every selected row to have an unambiguous observed/not-observed outcome. Disputed SIBAL and local gas-phase Saffire outcomes make ignition totals unavailable. No rows means unknown, never zero. Ignition, sustained burning, propagation and extinction are separate.", 'Reported tests sum test_count. Ignition totals require every selected row to have an unambiguous observed/not-observed outcome. Disputed SIBAL and local gas-phase Saffire outcomes make ignition totals unavailable. No rows means unknown, never zero. Ignition, sustained burning, propagation and extinction are separate.'),
        ("Condition comparison", 'Condition comparison', "Oxygen and pressure inputs are user assumptions. Comparisons use numerical equality and reported gravity class, not acceptance tolerances. Other variables and uncertainty remain unassessed. Study-wide pressure is labelled as such. No lunar or Martian test rows or validated mission risk model are available.", 'Oxygen and pressure inputs are user assumptions. Comparisons use numerical equality and reported gravity class, not acceptance tolerances. Other variables and uncertainty remain unassessed. Study-wide pressure is labelled as such. No lunar or Martian test rows or validated mission risk model are available.'),
        ("Source search", "Kaynak arama", "Only primary PDF passages whose files match the reviewed hashes enter source search. Catalog objectives and handwritten summaries are excluded. Optional Gemini selects verbatim text; malformed responses fall back to local retrieval. Text matching does not validate scientific meaning or answer relevance. Questions go to Gemini only when enabled.", 'Only primary PDF passages whose files match the reviewed hashes enter source search. Catalog objectives and handwritten summaries are excluded. Optional Gemini selects verbatim text; malformed responses fall back to local retrieval. Text matching does not validate scientific meaning or answer relevance. Questions go to Gemini only when enabled.'),
        ("Next validation steps", 'Next validation steps', "Reconcile reused SIBAL specimens with a domain expert; independently approve every reviewed row; assess mission-specific requirements; run the documented user study. These are open acceptance tasks, not completed certifications. See docs/VALIDATION.md for the protocol and operating assumptions.", 'Reconcile reused SIBAL specimens with a domain expert; independently approve every reviewed row; assess mission-specific requirements; run the documented user study. These are open acceptance tasks, not completed certifications. See docs/VALIDATION.md for the protocol and operating assumptions.')]
    st.markdown('<nav class="method-toc" aria-label="'+t('Contents')+'">'+''.join(f'<a href="#method-{i}">{html.escape(t(en))}</a>' for i,(en,tr,_,_) in enumerate(sections))+'</nav>', unsafe_allow_html=True)
    for i, (en, tr, body_en, body_tr) in enumerate(sections):
        st.markdown(f'<span id="method-{i}"></span>', unsafe_allow_html=True)
        st.subheader(t(en))
        st.write(t(body_en))
    st.caption("Snapshot SHA-256: " + tests.attrs["snapshot"])
    st.caption(t('The comparison rules above describe the original compilation. The separately versioned partial-gravity collection includes measured simulated-lunar studies; their test counts remain unquantified. No measured Mars row has been imported.'))
    extended_panel()
    st.subheader(t('Primary source library'))
    for source_id in dict.fromkeys(s["source_id"] for s in sources):
        entries = [s for s in sources if s["source_id"] == source_id]
        with st.expander(entries[0]["title"]):
            st.write(entries[0]["finding_tr"] if st.session_state.fg_lang == "TR" else entries[0]["finding_en"])
            for entry in entries:
                st.link_button(f"PDF {entry['page']}", entry["url"])
            st.caption(f"{entries[0]['location']} · {entries[0]['accessed_on']} · SHA-256: {entries[0]['sha256']}")
    a, b, c = st.columns(3)
    a.download_button(t('Reviewed reference CSV'), csv_bytes(tests), "reviewed-references.csv", "text/csv")
    b.download_button(t('Original mappings CSV'), csv_bytes(mappings), "materials.csv", "text/csv")
    c.download_button(t('Review metadata JSON'), (ROOT / "data/source_review.json").read_bytes(), "source-review.json", "application/json")
    st.caption(t('Planet textures: Solar System Scope / INOVE · CC BY 4.0 · unchanged. BASS-II photograph: NASA, ISS038-E-046394 · educational research context.'))
    st.markdown("[Solar System Scope](https://www.solarsystemscope.com/textures/) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [NASA media guidance](https://www.nasa.gov/nasa-brand-center/images-and-media/)")
    feasibility()
    review_queue()
    next_step("environment", "Start a new research context", "Yeni araştırma bağlamı oluştur")


def review_queue():
    """New NASA reports processed by scripts/ingest_ntrs.py: candidate sentences waiting for a human check. Never scored."""
    folder = ROOT / "data" / "review_queue"
    files = sorted(folder.glob("*.json")) if folder.exists() else []
    st.subheader(t('How new NASA data gets in · review queue'))
    st.markdown(t('1. Find a report (Material Explorer → Search NASA NTRS). 2. Run `python scripts/ingest_ntrs.py <NTRS ID>`: the PDF is downloaded from ntrs.nasa.gov, hashed (SHA-256) and read page by page. 3. Sentences with oxygen, pressure, airflow or ignition values become candidates. 4. A reviewer checks each one on its page before any value is used.'))
    if not files:
        st.caption(t('The review queue is empty.'))
        return
    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        with st.expander(f"{rec['source_id']} · {len(rec['candidates'])} {t('candidates')} · {t(rec.get('status', 'awaiting review'))}"):
            st.caption(f"SHA-256: {rec['pdf_sha256']} · {rec['pages']} {t('pages')} · {rec['extracted_on']}")
            st.markdown(f"[NASA NTRS]({rec['url']})")
            dataframe(pd.DataFrame([{t('Page'): c['page'], t('Values'): ", ".join(c['values']), t('Sentence'): c['sentence'],
                                     t('Status'): t('pending')} for c in rec['candidates']]))


def feasibility():
    """What it costs, what it needs and how it keeps growing (judging form: feasibility and sustainability)."""
    st.subheader(t('Feasibility and sustainability'))
    rows = [(t('Running cost'), t('Free hosting tier is enough for the core app. Local search needs no paid API. Gemini is optional and pay-per-use.')),
            (t('What it needs'), t('Python 3.12 and Streamlit. About 92 MB including the NASA PDFs and 3D models. Works offline.')),
            (t('Maintenance'), t('Estimated 2–4 hours per month plus expert review of each new source (an estimate, not a measured cost).')),
            (t('Growth'), t('Live search of NASA NTRS finds new reports; scripts/ingest_ntrs.py hashes a report and queues candidate values; a person approves each value.')),
            (t('Quality'), t('Automated regression tests and PDF hash checks. Expert scientific review remains pending.')),
            (t('Who it serves'), t('Mission planners, students and educators who need NASA fire evidence without reading whole reports.'))]
    dataframe(pd.DataFrame([{t('Topic'): a, t('Answer'): b} for a, b in rows]))
