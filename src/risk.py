"""Risk-factor tables. Words and sources only: no score, no 'safe'. Colour is a reading aid next to the words."""
import html

import pandas as pd
import streamlit as st

from src.i18n import t

NTRS = "https://ntrs.nasa.gov/citations/"
from src.links import page as _pdf
from src.links import platform as _platform
from src.plain import EXTRA_KEYWORDS
BASS2_TM = "https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf#page=104"  # direct PDF page

# Each finding was read on the cited PDF page (2026-11-14).
ENV_FACTORS = [
    {"factor": ("Oxygen level", "Oksijen seviyesi"),
     "seen": ("In BASS the SIBAL fabric did not ignite at 16.4% O₂ but ignited at 17.1%. On Mir the cabin O₂ was 22.5–25.4%, above the expected 21%.",
              "BASS'ta SIBAL kumaş %16,4 O₂'de tutuşmadı, %17,1'de tutuştu. Mir'de kabin O₂'si beklenen %21'in üstünde, %22,5–25,4 arasındaydı."),
     "why": ("A small rise in oxygen can change whether a material ignites at all.",
             "Oksijendeki küçük bir artış, malzemenin tutuşup tutuşmayacağını değiştirebilir."),
     "src": [("BASS 2015, p. 9", _pdf("20150008962", 9)), ("Mir FFFT 1999, p. 16", _pdf("20000024924", 16))]},
    {"factor": ("Airflow", "Hava akışı"),
     "seen": ("In BASS-II, 6 SIBAL tests went out at very low airflow (2.2–5 cm/s) and one blew off at 47 cm/s. In WIF a weak flame in still air brightened as soon as airflow started.",
              "BASS-II'de 6 SIBAL testi çok düşük akışta (2,2–5 cm/s) söndü, biri 47 cm/s'de üflenerek söndü. WIF'te durgun havada zayıf yanan alev, akış başlar başlamaz parladı."),
     "why": ("Ventilation feeds or starves a flame; there is no rising hot air in microgravity.",
             "Havalandırma alevi besler ya da söndürür; mikroyerçekiminde sıcak hava yükselmez."),
     "src": [("BASS-II summary, Table 7.1, p. 104", BASS2_TM), ("WIF 1994, p. 2", _pdf("19960008389", 2))]},
    {"factor": ("Smoke and toxic gases", "Duman ve zehirli gazlar"),
     "seen": ("In Saffire VI the temperature rose only near the fire, but CO and CO₂ rose significantly; PMMA tests exceeded the 1-hour CO₂ and 24-hour CO limits. A typical smoke-alarm threshold was reached only at 981 s.",
              "Saffire VI'da sıcaklık sadece alevin yakınında yükseldi, ama CO ve CO₂ belirgin şekilde arttı; PMMA testleri 1 saatlik CO₂ ve 24 saatlik CO sınırlarını aştı. Tipik duman alarmı eşiğine ancak 981. saniyede ulaşıldı."),
     "why": ("In a closed cabin the gases can matter more than the heat.",
             "Kapalı bir kabinde gazlar ısıdan daha önemli olabilir."),
     "src": [("Saffire VI 2024, p. 6", _pdf("20240002981", 6))]},
    {"factor": ("Cabin pressure and oxygen together", "Kabin basıncı ve oksijen birlikte"),
     "seen": ("Saffire VI burned samples at 100, 70.7 and about 54–55 kPa with 22–31% O₂ — the kind of low-pressure, oxygen-rich air planned for exploration cabins.",
              "Saffire VI numuneleri 100, 70,7 ve yaklaşık 54–55 kPa basınçta, %22–31 O₂ ile yaktı; keşif kabinleri için planlanan düşük basınçlı, oksijence zengin havaya benzer koşullar."),
     "why": ("Lower pressure usually comes with more oxygen, which is why both are listed in Environments.",
             "Düşük basınç genellikle daha fazla oksijenle birlikte gelir; bu yüzden ikisi de Ortamlar sayfasında yer alır."),
     "src": [("Saffire VI 2024, p. 3", _pdf("20240002981", 3))]},
    {"factor": ("Gravity", "Yerçekimi"),
     "seen": ("In simulated lunar gravity (LUCI) the SIBAL flame base spread about 0.92 mm/s and the PMMA flame tip about 1.5 mm/s. No test has yet been done on the lunar surface; FM² is planned.",
              "Benzetilmiş Ay yerçekiminde (LUCI) SIBAL alev tabanı yaklaşık 0,92 mm/s, PMMA alev ucu yaklaşık 1,5 mm/s yayıldı. Ay yüzeyinde henüz test yapılmadı; FM² planlanıyor."),
     "why": ("Results from microgravity cannot simply be reused for the Moon or Mars.",
             "Mikroyerçekimi sonuçları Ay veya Mars için olduğu gibi kullanılamaz."),
     "src": [("LUCI 2025, p. 19 and 21", _pdf("20250010653", 19)), ("FM² poster 2024, p. 1", _pdf("20240015307", 1))]},
]

STATUS_STYLE = {"yes": ("#e8704a", "▲"), "no": ("#5296dc", "▼"), "mixed": ("#e0a53b", "◆"), "unknown": ("#7d8a9c", "?")}


def _tr() -> bool:
    return st.session_state.get("fg_lang", "EN") == "TR"


def _cell(state: str, text: str) -> str:
    colour, icon = STATUS_STYLE[state]
    return (f"<td><span style='display:inline-block;width:10px;height:10px;border-radius:2px;background:{colour};"
            f"margin-right:6px'></span>{icon} {html.escape(text)}</td>")


def _word(state: str, count: str = "") -> str:
    words = {"yes": t("Observed"), "no": t("Not observed"), "mixed": t("Mixed"), "unknown": t("Unknown")}
    return words[state] + (f" ({count})" if count else "")


def _ci(count: str) -> str:
    """Kept for compatibility: counts are shown as observed numbers only (no general probability is derived)."""
    return ""


def _status(rows, column, yes=("observed",), no=("not_observed",)):
    if rows.empty or column not in rows:
        return "unknown", ""
    vals = rows[column].fillna("unknown")
    n = int(rows.test_count.fillna(0).sum())
    y = int(rows.loc[vals.isin(yes), "test_count"].fillna(0).sum())
    nn = int(rows.loc[vals.isin(no), "test_count"].fillna(0).sum())
    if y and not nn and y == n:
        return "yes", f"{y}/{n}"
    if nn and not y and nn == n:
        return "no", f"0/{n}"
    if y or nn:
        return "mixed", f"{y}/{n}"
    return "unknown", ""


def _range(series, unit):
    v = pd.to_numeric(series, errors="coerce").dropna()
    if v.empty:
        return t("not reported")
    return f"{v.min():g} {unit}" if v.min() == v.max() else f"{v.min():g}–{v.max():g} {unit}"


def material_table_html(pairs, tests, env, name, extras) -> str:
    """One row per cargo item: ignition, sustained burning, spread, extinction, conditions, gravity match, source."""
    head = [t("Item"), t("NASA specimen"), t("Ignition"), t("Sustained burning"), t("Flame spread"), t("Extinction"),
            "O₂", t("Pressure"), t("Same gravity as selected?"), t("Source")]
    body = []
    for word, key in pairs:
        if key in EXTRA_KEYWORDS and key not in extras:
            body.append(f"<tr><td><b>{html.escape(word)}</b></td><td colspan='9'>"
                        f"{html.escape(t('NASA tests of this specimen exist, but none was run inside the selected oxygen range. Missing data does not mean safe.'))}</td></tr>")
            continue
        if key in extras:
            s = extras[key]
            ign = ("yes", f"{s['ignited']}/{s['tests']}") if s["ignited"] == s["tests"] else \
                  (("no", f"0/{s['tests']}") if s["ignited"] == 0 else ("mixed", f"{s['ignited']}/{s['tests']}"))
            o2 = _range(pd.Series(s["oxygen_pct"] or [], dtype=float), "%")
            p = _range(pd.Series(s["pressure_kpa"] or [], dtype=float), "kPa")
            src = ", ".join(f"<a href='{x['url']}' target='_blank'>{html.escape(x['short'])} {t('p.')} {x['page']}</a>" for x in s["sources"])
            spec = (s["name_tr"] if _tr() else s["name_en"]) + " · " + _platform(s["experiments"], _tr())
            cells = [_cell(ign[0], _word(*ign) + _ci(ign[1])), _cell("unknown", t("not in this table")), _cell("unknown", t("not in this table")),
                     _cell("unknown", _word("unknown"))]
        else:
            rows = tests[tests.material == key] if key else tests.iloc[0:0]
            if rows.empty:
                body.append(f"<tr><td><b>{html.escape(word)}</b></td><td colspan='9'>"
                            f"{html.escape(t('No compiled NASA test for this item — every factor is unknown. Missing data does not mean safe.'))}</td></tr>")
                continue
            ign = _status(rows, "ignition")
            if (rows.ignition == "disputed").any():
                ign = ("mixed", t("count disputed"))
            elif (rows.ignition == "local_gas_flame").all():
                ign = ("mixed", t("brief local flame only"))
            sus = _status(rows, "sustained")
            spr = _status(rows, "propagation")
            ext = _status(rows, "extinction", yes=("observed", "after_flow_stop", "fuel_consumed"))
            o2, p = _range(rows.oxygen_pct, "%"), _range(rows.pressure_kpa, "kPa")
            src = ", ".join(f"<a href='{u}#page={pg}' target='_blank'>PDF {pg}</a>"
                            for u, pg in rows[["source_url", "source_page"]].drop_duplicates().itertuples(index=False))
            spec = name(key) + " · " + _platform(rows.experiment_id.dropna().unique(), _tr())
            cells = [_cell(ign[0], ign[1] if ign[0] == "mixed" and not ign[1][:1].isdigit() else _word(*ign) + _ci(ign[1])),
                     _cell(sus[0], _word(*sus)), _cell(spr[0], _word(*spr)), _cell(ext[0], _word(*ext))]
        same = env == "ISS"
        grav = _cell("yes" if same else "unknown", t("yes · microgravity") if same else t("no · tests were in microgravity"))
        body.append(f"<tr><td><b>{html.escape(word)}</b></td><td>{html.escape(spec)}</td>{''.join(cells)}"
                    f"<td>{html.escape(o2)}</td><td>{html.escape(p)}</td>{grav}<td>{src}</td></tr>")
    return (f"<div style='overflow-x:auto' tabindex='0' role='region' aria-label='{html.escape(t('Risk factor table · your cargo'))}'>"
            "<table class='risk-table'><tr>" + "".join(f"<th scope='col'>{html.escape(h)}</th>" for h in head)
            + "</tr>" + "".join(body) + "</table></div>")


def env_table_html() -> str:
    tr = _tr()
    rows = "".join(
        f"<tr><td><b>{html.escape(f['factor'][tr])}</b></td><td>{html.escape(f['seen'][tr])}</td>"
        f"<td>{html.escape(f['why'][tr])}</td><td>"
        + "<br>".join(f"<a href='{u}' target='_blank'>{html.escape(lbl if not tr else lbl.replace('p. ', 's. ').replace(' and ', ' ve '))}</a>" for lbl, u in f["src"])
        + "</td></tr>" for f in ENV_FACTORS)
    head = [t("Risk factor"), t("What NASA observed"), t("Why it matters in a cabin"), t("Source")]
    return (f"<div style='overflow-x:auto' tabindex='0' role='region' aria-label='{html.escape(t('Risk factors in the cabin environment'))}'>"
            "<table class='risk-table'><tr>" + "".join(f"<th scope='col'>{html.escape(h)}</th>" for h in head)
            + "</tr>" + rows + "</table></div>")


CSS = """<style>
.risk-table{width:100%;border-collapse:collapse;font-size:14px;margin:6px 0 4px}
.risk-table th{background:#151f2e;color:#f3f6fb;text-align:left;padding:10px;border-bottom:2px solid #ffb36b;white-space:nowrap}
.risk-table td{padding:9px 10px;border-bottom:1px solid #314156;vertical-align:top;line-height:1.45}
.risk-table tr:hover td{background:rgba(255,179,107,.06)}
</style>"""


def legend() -> str:
    return t("▲ observed · ▼ not observed · ◆ mixed or disputed · ? unknown (not reported). Numbers are observed counts under the listed conditions, not a general probability. This table lists evidence, not a risk score; an empty or unknown cell never means safe.")
