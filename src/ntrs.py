"""Live link to NASA's public Technical Reports Server (NTRS) API.

Only public search terms are sent (never user input or personal data). Results are listed as reports *to review*;
nothing found here enters the scored data until it passes the ingestion and review steps (scripts/ingest_ntrs.py).
"""
import json
import urllib.parse
import urllib.request

import streamlit as st

from src.i18n import t

API = "https://ntrs.nasa.gov/api/citations/search"
KNOWN = {"19960008389", "20150008962", "20170008805", "20210021318", "20240015307", "20250002114",
         "20250010653", "20260001966", "20000024924", "20240002981", "20030075805", "20160000593", "20210011385"}

QUERIES = {
    "pamuklu kumaş": "cotton fiberglass fabric flame spread",
    "kablo kılıfı": "wire insulation flammability microgravity",
    "kauçuk": "silicone flammability spacecraft fire",
    "kağıt": "cellulose paper flame spread microgravity",
    "plastik (pmma)": "PMMA flame spread microgravity",
    "pmma_extra": "PMMA flame spread microgravity",
    "delrin_extra": "Delrin flame spread",
    "hdpe_extra": "polyethylene flammability microgravity",
    "nomex_extra": "Nomex flammability spacecraft",
    "jersey_extra": "cotton fabric flammability spacecraft",
}


def parse(payload: dict) -> list:
    """NTRS JSON → [{id, title, date, url, pdf, known}] (robust to missing fields)."""
    out = []
    for r in (payload or {}).get("results", []) or []:
        rid = str(r.get("id", "")).strip()
        if not rid:
            continue
        pubs = r.get("publications") or [{}]
        date = (pubs[0] or {}).get("publicationDate", "") or ""
        pdf = next((d.get("links", {}).get("pdf") for d in (r.get("downloads") or []) if d.get("links", {}).get("pdf")), None)
        out.append({"id": rid, "title": str(r.get("title", "")).strip(), "date": date[:10],
                    "url": f"https://ntrs.nasa.gov/citations/{rid}",
                    "pdf": f"https://ntrs.nasa.gov{pdf}" if pdf and pdf.startswith("/") else pdf,
                    "known": rid in KNOWN})
    return out


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def search(query: str, size: int = 6) -> list | None:
    """Live NTRS search; None when offline or the API does not answer in time."""
    url = API + "?" + urllib.parse.urlencode({"q": query, "page.size": size})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FLAMEGUARD research tool", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return parse(json.loads(resp.read().decode("utf-8")))
    except Exception:
        return None


def panel(key: str, label: str) -> None:
    """Button-triggered panel so the app never needs the internet unless asked."""
    query = QUERIES.get(key)
    if not query:
        return
    st.subheader(t("Live from NASA: reports to review"))
    st.caption(t("Searches NASA's public Technical Reports Server for this specimen. Results are listed for review only — "
                 "nothing is added to the evidence until it is checked page by page."))
    if not st.button(" " + t("Search NASA NTRS"), key=f"ntrs_{key}"):
        return
    with st.spinner(t("Asking NASA NTRS…")):
        results = search(query)
    if results is None:
        st.info(t("NASA NTRS could not be reached (offline?). The rest of the app works without it."))
        return
    if not results:
        st.info(t("No NTRS reports found for this search."))
        return
    rows = []
    for r in results:
        status = "✓ " + t("already in FLAMEGUARD") if r["known"] else "◌ " + t("not yet reviewed")
        pdf = f" · [PDF]({r['pdf']})" if r["pdf"] else ""
        rows.append(f"- **[{r['title']}]({r['url']})** ({r['date'] or '—'}) — {status}{pdf}")
    st.markdown("\n".join(rows))
    st.caption(t("Query sent to NASA: {q}", q=query))
