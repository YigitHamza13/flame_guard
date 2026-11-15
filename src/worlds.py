"""Two features built only from data already in the collection:
1. "Same cargo, two worlds": each cargo item's ISS evidence next to its lunar-gravity evidence.
2. "Tests NASA still needs to fly": rule-based list of missing tests, ranked by how many specimens each would cover.
Nothing here is estimated: a missing value is reported as missing."""
from __future__ import annotations

import html

from src.i18n import t

from src.links import page as _pdf

LUCI = _pdf("20250010653")
FM2 = _pdf("20240015307")
LPSC = _pdf("20260001966")

# Lunar-gravity evidence per specimen key (extended_review.json: LUCI-SIBAL p. 19, LUCI-PMMA p. 21, LPSC-*).
LUNAR = {
    "pamuklu kumaş": {
        "en": "Simulated lunar gravity (LUCI sounding rocket): the flame base spread about 0.92 mm/s. Earlier centrifuge and aircraft tests also burned this fabric. None of these was on the lunar surface.",
        "tr": "Benzetilmiş Ay yerçekimi (LUCI sonda roketi): alev tabanı yaklaşık 0,92 mm/s yayıldı. Daha önceki santrifüj ve uçak testlerinde de bu kumaş yakıldı. Hiçbiri Ay yüzeyinde değil.",
        "src": [("LUCI 2025, p. 19", _pdf("20250010653", 19)), ("LPSC 2026", LPSC)]},
    "plastik (pmma)": {
        "en": "Simulated lunar gravity (LUCI sounding rocket): the flame tip spread about 1.5 mm/s along a 4 mm rod. Not on the lunar surface.",
        "tr": "Benzetilmiş Ay yerçekimi (LUCI sonda roketi): 4 mm'lik çubukta alev ucu yaklaşık 1,5 mm/s yayıldı. Ay yüzeyinde değil.",
        "src": [("LUCI 2025, p. 21", _pdf("20250010653", 21))]},
}
LUNAR["pmma_extra"] = LUNAR["plastik (pmma)"]


def _tr() -> bool:
    return t("Read aloud") == "Sesli oku"


def _p(label: str) -> str:
    return label.replace("p. ", "s. ") if _tr() else label


def _links(src) -> str:
    return " · ".join(f"<a href='{u}' target='_blank'>{html.escape(_p(lbl))}</a>" for lbl, u in src)


def iss_summary(key, tests, extras) -> tuple:
    """(text, tone) for the microgravity side, same counting rules and scope as the plain cards."""
    from src.links import platform
    from src.plain import EXTRA_KEYWORDS
    tr = _tr()
    if key in EXTRA_KEYWORDS:
        if key not in extras:
            return t("Outside the oxygen filter"), "none"
        s = extras[key]
        n, k = s["tests"], s["ignited"]
        return _count_text(n, k) + " · " + platform(s["experiments"], tr), ("low" if k == 0 else "medium")
    rows = tests[tests.material == key] if key else tests.iloc[0:0]
    if rows.empty:
        from src.evidence import CATALOG
        return (t("Study evidence only · no compiled test count") if key in CATALOG else t("No compiled NASA test")), "none"
    where = platform(rows.experiment_id.dropna().unique(), tr)
    n = int(rows.test_count.fillna(0).sum())
    if (rows.ignition == "disputed").any():
        return t("{n} tests in microgravity · ignition count disputed", n=n) + f" · {where}", "none"
    ign = int(rows.loc[rows.ignition == "observed", "test_count"].fillna(0).sum())
    if (rows.ignition == "local_gas_flame").all():
        return t("{n} tests in microgravity · only a brief local flame", n=n) + f" · {where}", "low"
    spread = int(rows.loc[rows.propagation == "observed", "test_count"].fillna(0).sum())
    text = _count_text(n, ign)
    if spread:
        text += " · " + t("flame spread in {s}", s=spread)
    return text + f" · {where}", ("high" if spread else "medium")


def _count_text(n: int, k: int) -> str:
    if n == 1:
        return t("1 test in microgravity · it ignited") if k else t("1 test in microgravity · it did not ignite")
    return t("{n} tests in microgravity · ignited in {k}", n=n, k=k)


def two_worlds_html(pairs, tests, extras) -> str:
    tr = _tr()
    head = (f"<div class='tw-row tw-head'><div></div><div> {html.escape(t('Microgravity experiments (ISS, Space Shuttle, Mir, Cygnus)'))}</div>"
            f"<div> {html.escape(t('On the Moon · lunar gravity (about 1/6 g)'))}</div></div>")
    rows = []
    for word, key in pairs:
        iss, tone = iss_summary(key, tests, extras)
        lunar = LUNAR.get(key)
        if lunar:
            moon = (f"<div class='tw-cell tw-some'><b>{html.escape(t('Simulated lunar gravity only'))}</b><br>"
                    f"{html.escape(lunar['tr' if tr else 'en'])}<div class='tw-src'>{_links(lunar['src'])}</div></div>")
        else:
            moon = (f"<div class='tw-cell tw-none'><b>{html.escape(t('No lunar-gravity test in this collection'))}</b><br>"
                    f"{html.escape(t('Microgravity results cannot be reused for the Moon. NASA plans burn tests on the lunar surface (FM²).'))}"
                    f"<div class='tw-src'>{_links([('FM² poster 2024, p. 1', _pdf('20240015307', 1))])}</div></div>")
        rows.append(f"<div class='tw-row'><div class='tw-item'>{html.escape(word)}</div>"
                    f"<div class='tw-cell tone-{tone}'>{html.escape(iss)}</div>{moon}</div>")
    return f"<div class='tw' role='table' aria-label='{html.escape(t('Same cargo, two worlds'))}'>{head}{''.join(rows)}</div>"


CSS = """<style>
.tw{margin:6px 0 10px}
.tw-row{display:grid;grid-template-columns:minmax(120px,1fr) 2fr 3fr;gap:8px;margin:6px 0;align-items:stretch}
.tw-head div{font-weight:600;font-size:14px;color:var(--muted,#abbace);padding:0 4px}
.tw-item{font-weight:600;padding:12px 4px}
.tw-cell{border:1px solid var(--line,#314156);border-radius:8px;padding:10px 14px;font-size:14px;line-height:1.45;border-left-width:5px}
.tw-cell.tone-high{border-left-color:#e8704a;background:rgba(232,110,72,.12)}
.tw-cell.tone-medium{border-left-color:#e0a53b;background:rgba(224,165,59,.10)}
.tw-cell.tone-low{border-left-color:#5296dc;background:rgba(82,150,220,.10)}
.tw-cell.tone-none,.tw-none{border-left-color:#7d8a9c;border-style:dashed solid dashed solid}
.tw-some{border-left-color:#c9b6ff;background:rgba(201,182,255,.08)}
.tw-src{margin-top:6px;font-size:13px}
@media (max-width:760px){.tw-row{grid-template-columns:1fr}.tw-head{display:none}
  .tw-cell.tone-high:before,.tw-cell.tone-medium:before,.tw-cell.tone-low:before,.tw-cell.tone-none:before{content:" ";}
  .tw-some:before,.tw-none:before{content:" ";}}
.wish{border:1px solid var(--line,#314156);border-left:5px solid #ff8a3d;border-radius:8px;padding:12px 16px;margin:8px 0}
.wish-n{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;background:#ff8a3d;color:#0b1322;font-weight:700;margin-right:8px}
.wish-t{font-size:17px;font-weight:600}
.wish p{margin:6px 0 0;max-width:90ch}
.wish-m{color:var(--muted,#abbace);font-size:13.5px;margin-top:6px}
</style>"""


def wishlist(tests, extras, name) -> list:
    """Missing tests, each with the rule that found it, the specimens it covers and its source.
    Ranked by how many specimens a test would cover (ties keep rule order)."""
    from src.evidence import CATALOG
    tr = _tr()
    pick = (lambda en, trt: trt if tr else en)
    keys = list(CATALOG) + list(extras)
    nm = lambda k: (extras[k]["name_tr"] if tr else extras[k]["name_en"]) if k in extras else name(k)
    stats = {}
    for k in keys:
        if k in extras:
            s = extras[k]
            stats[k] = {"n": s["tests"], "k": s["ignited"], "o2": bool(s["oxygen_pct"]), "p": bool(s["pressure_kpa"]),
                        "spread": False, "disputed": False}
            continue
        rows = tests[tests.material == k]
        if rows.empty:
            stats[k] = None
            continue
        stats[k] = {"n": int(rows.test_count.fillna(0).sum()),
                    "k": int(rows.loc[rows.ignition == "observed", "test_count"].fillna(0).sum()),
                    "o2": rows.oxygen_pct.notna().any(), "p": rows.pressure_kpa.notna().any(),
                    "spread": rows.propagation.isin(["observed", "not_observed"]).any(),
                    "disputed": (rows.ignition == "disputed").any()}
    tested = [k for k in keys if stats[k]]
    lunar = [k for k in tested if k in LUNAR]
    items = [
        {"title": pick("A burn test on the lunar surface", "Ay yüzeyinde bir yanma testi"),
         "why": pick("No material in this collection has been burned on the Moon itself. Lunar-gravity results so far come from a sounding rocket and short centrifuge or aircraft tests. NASA's FM² experiment is planned to do this.",
                     "Bu koleksiyondaki hiçbir malzeme Ay'ın kendisinde yakılmadı. Şimdiye kadarki Ay yerçekimi sonuçları bir sonda roketinden ve kısa santrifüj ya da uçak testlerinden geliyor. NASA'nın FM² deneyi bunu yapmayı planlıyor."),
         "keys": tested, "src": [("LUCI 2025, p. 19", _pdf("20250010653", 19)), ("FM² poster 2024, p. 1", _pdf("20240015307", 1))]},
        {"title": pick("Lunar-gravity tests of everyday cabin materials", "Günlük kabin malzemelerinin Ay yerçekiminde testi"),
         "why": pick("Measured lunar-gravity flame spread exists here only for SIBAL fabric and a PMMA rod. Every other specimen has microgravity results only, and those cannot be reused for the Moon.",
                     "Burada ölçülmüş Ay yerçekimi alev yayılımı sadece SIBAL kumaşı ve bir PMMA çubuğu için var. Diğer numunelerin sadece mikroyerçekimi sonuçları var ve bunlar Ay için kullanılamaz."),
         "keys": [k for k in tested if k not in lunar], "src": [("LUCI 2025, p. 19", _pdf("20250010653", 19)), ("LUCI 2025, p. 21", _pdf("20250010653", 21))]},
        {"title": pick("Measured results in Martian gravity", "Mars yerçekiminde ölçülmüş sonuçlar"),
         "why": pick("A 2026 NASA presentation is titled 'lunar and Martian gravity', but it gives no measured Mars result that we could verify. A Mars mission planner has no compiled test here.",
                     "2026 tarihli bir NASA sunumunun başlığında 'Ay ve Mars yerçekimi' geçiyor, ama doğrulayabildiğimiz ölçülmüş bir Mars sonucu vermiyor. Bir Mars görevi planlayıcısı için burada derlenmiş test yok."),
         "keys": tested, "src": [("LPSC 2026", LPSC)]},
    ]
    small = sorted((k for k in tested if not stats[k]["disputed"] and 0 < stats[k]["n"] <= 6), key=lambda k: stats[k]["n"])
    if small:
        widest = small[0]
        items.append({"title": pick("More repeat tests in microgravity", "Mikroyerçekiminde daha fazla tekrar testi"),
                      "why": pick(f"These specimens were tested 6 times or fewer, often under different conditions, so a few tests cannot show how often they ignite. Repeats under the same oxygen, pressure and airflow are needed. Fewest: {nm(widest)} ({stats[widest]['n']} test(s)).",
                                  f"Bu numuneler 6 kez ya da daha az, çoğu zaman farklı koşullarda test edildi; birkaç test ne sıklıkla tutuştuklarını gösteremez. Aynı oksijen, basınç ve hava akışında tekrar gerekiyor. En az test: {nm(widest)} ({stats[widest]['n']} test)."),
                      "keys": small, "src": []})
    nospread = [k for k in tested if not stats[k]["spread"] and not stats[k]["disputed"]]
    if nospread:
        items.append({"title": pick("A measured flame-spread result", "Ölçülmüş bir alev yayılma sonucu"),
                      "why": pick("For these specimens the compiled tables say whether they ignited, but not whether the flame spread.",
                                  "Bu numuneler için derlenmiş tablolar tutuşup tutuşmadığını söylüyor, ama alevin yayılıp yayılmadığını söylemiyor."),
                      "keys": nospread, "src": []})
    nocond = [k for k in tested if not (stats[k]["o2"] and stats[k]["p"])]
    if nocond:
        items.append({"title": pick("Report the oxygen level and cabin pressure of past tests", "Geçmiş testlerin oksijen ve kabin basıncının raporlanması"),
                      "why": pick("Oxygen and pressure change whether a material ignites. For these specimens at least one of them is missing from the report we could verify.",
                                  "Oksijen ve basınç bir malzemenin tutuşup tutuşmayacağını değiştirir. Bu numunelerde doğrulayabildiğimiz raporda bunlardan en az biri eksik."),
                      "keys": nocond, "src": []})
    disputed = [k for k in tested if stats[k]["disputed"]]
    if disputed:
        items.append({"title": pick("A recount of disputed results", "Çelişkili sonuçların yeniden sayılması"),
                      "why": pick("The report gives conflicting ignition counts for these specimens.", "Rapor bu numuneler için çelişkili tutuşma sayıları veriyor."),
                      "keys": disputed, "src": []})
    for it in items:
        it["names"] = [nm(k) for k in it["keys"]]
    return sorted(items, key=lambda it: -len(it["keys"]))


def wishlist_html(items, everyday) -> str:
    tr = _tr()
    out = []
    import streamlit as st
    env = st.session_state.get('mission_environment', 'ISS')
    for i, it in enumerate(items, 1):
        title = it['title'].casefold()
        relevant = (env == 'Moon Base' and any(w in title for w in ('lunar', 'moon', 'ay '))) or (env == 'Mars Mission' and any(w in title for w in ('martian', 'mars')))
        marker = "<span class='fg-env-badge'>" + html.escape(t('Relevant to the selected environment')) + "</span>" if relevant else ""

        ex = []
        for k in it["keys"]:
            if k in everyday:
                ex += everyday[k][1 if tr else 0][:1]
        ex_txt = (t("Everyday examples") + ": " + ", ".join(dict.fromkeys(ex))) if ex else ""
        src = f" · {_links(it['src'])}" if it["src"] else ""
        out.append(f"<div class='{'wish fg-env-relevant' if relevant else 'wish'}'>{marker}<span class='wish-n'>{i}</span><span class='wish-t'>{html.escape(it['title'])}</span>"
                   f"<p>{html.escape(it['why'])}</p>"
                   f"<div class='wish-m'><b>{html.escape(t('Specimens it would cover ({n})', n=len(it['keys'])))}:</b> {html.escape(', '.join(it['names']))}"
                   + (f"<br>{html.escape(ex_txt)}" if ex_txt else "") + f"{src}</div></div>")
    return "".join(out)
