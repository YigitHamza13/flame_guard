"""Local evidence loading and sample-specific summaries.

Catalog metadata, compiled test groups and source excerpts retain their provenance.
No mission risk model is defined by the supplied dataset.
"""
from pathlib import Path
import json
import re

import pandas as pd
import streamlit as st
from src.database import sync_store

ROOT = Path(__file__).resolve().parents[1]
CATALOG = {
    "pamuklu kumaş": ("SIBAL cotton–fiberglass composite", "SIBAL pamuk–cam elyafı kompoziti", "Composite fabrics"),
    "kablo kılıfı": ("Polyethylene wire insulation", "Polietilen kablo yalıtımı", "Cable insulation"),
    "kauçuk": ("Saffire-II silicone sheets 2-1 to 2-4", "Saffire-II silikon levhalar 2-1 / 2-4", "Elastomers"),
    "kağıt": ("Mir FFFT flat cellulose specimens", "Mir FFFT düz selüloz numuneleri", "Paper and cellulose"),
    "plastik (pmma)": ("PMMA", "PMMA", "Polymers"),
}
ENVIRONMENTS = {
    "Moon Base": {"name": "Lunar habitat", "planet": "moon", "gravity": "Partial gravity"},
    "ISS": {"name": "International Space Station", "planet": "earth", "gravity": "Microgravity"},
    "Mars Mission": {"name": "Mars mission", "planet": "mars", "gravity": "Mission phase unspecified"},
    "Earth Lab": {"name": "Earth laboratory", "planet": "earth", "gravity": "Normal gravity"},
}
TEST_COLUMNS = ["experiment_id", "source_url", "material", "gravity", "oxygen_pct", "pressure_kpa",
                "flow", "ignited", "flame_spread", "test_count", "sample_material", "mapping_note"]
MAPPING_COLUMNS = ["input_material", "source_material", "experiment_id", "source_url", "gravity", "mapping_note"]


def load_datasets():
    paths = [ROOT / "data" / p for p in ("experiments.csv", "materials.csv", "psi_combustion_investigations.json")]
    paths += sorted((ROOT / "sources").glob("*.txt"))
    paths += [ROOT / "data/source_review.json", ROOT / "data/primary_passages.json"]
    paths += sorted((ROOT / "sources/originals").glob("*.pdf"))
    stamps = tuple((str(p), p.stat().st_mtime_ns if p.exists() else None) for p in paths)
    return _load_datasets(stamps)


@st.cache_data(show_spinner=False)
def _load_datasets(stamps):
    errors = []
    tables = []
    for filename, columns in [("experiments.csv", TEST_COLUMNS), ("materials.csv", MAPPING_COLUMNS)]:
        try:
            frame = pd.read_csv(ROOT / "data" / filename)
            missing = set(columns) - set(frame.columns)
            if missing:
                errors.append(f"{filename} has missing columns: {', '.join(sorted(missing))}")
            tables.append(frame.reindex(columns=columns))
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            errors.append(f"Unable to load {filename} ({type(exc).__name__}).")
            tables.append(pd.DataFrame(columns=columns))
    try:
        catalog = json.loads((ROOT / "data/psi_combustion_investigations.json").read_text(encoding="utf-8"))
        if not isinstance(catalog, list) or not all(isinstance(r, dict) for r in catalog):
            raise ValueError("Invalid catalog")
    except (OSError, ValueError):
        errors.append("Unable to load the local PSI catalog.")
        catalog = []
    sources = []
    for path in sorted((ROOT / "sources").glob("*.txt")):
        try:
            body = path.read_text(encoding="utf-8")
            links = re.findall(r"https?://[^\s]+", body)
            sources.append({"id": path.name, "title": body.splitlines()[0].removeprefix("Title: "),
                            "text": body, "url": links[0] if links else ""})
        except (OSError, UnicodeError):
            errors.append(f"Unable to read {path.name}.")
    if not sources:
        errors.append("No local source excerpts were found in sources/.")
    tests, mappings = tables
    for col in ("oxygen_pct", "pressure_kpa", "test_count"):
        tests[col] = pd.to_numeric(tests[col], errors="coerce")
    invalid_counts = tests.test_count.isna() | (tests.test_count < 0) | (tests.test_count % 1 != 0)
    if invalid_counts.any():
        errors.append("Some test counts are missing or invalid. Their totals are unavailable.")
        tests.loc[invalid_counts, "test_count"] = float("nan")
    rows, collections, checked_sources, issues, snapshot = sync_store(ROOT, tests, mappings, catalog, sources)
    tests = pd.DataFrame(rows)
    tests.attrs["snapshot"] = snapshot
    return tests, pd.DataFrame(collections["mappings"]), collections["catalog"], checked_sources, errors + issues


def family(record):
    name = str(record.get("acronym") or record.get("title", "")).upper()
    for term in ("GRADFLEX", "PBRE", "SAFFIRE", "BASS", "FLEX", "SAME", "ACME", "SOFIE", "FM²", "FM2"):
        if re.search(r"(?<![A-Z])" + re.escape(term) + r"(?![A-Z])", name):
            return "FM²" if term == "FM2" else term
    return "Other research"


def material_label(key, lang="EN"):
    return CATALOG.get(key, (key, key, "Unclassified"))[lang == "TR"]


def material_keys(tests, mappings):
    return list(dict.fromkeys([*mappings.input_material.dropna(), *tests.material.dropna()]))


def sample_rows(tests, material):
    return tests.loc[tests.material == material].copy()


def summary(rows):
    if "evidence_type" in rows:
        rows = rows[rows.evidence_type.eq("measured_experiment") & rows.review_status.isin(["source_checked", "conflict"])]
    if rows.empty:
        return {"tests": None, "ignited": None, "ratio": None}
    if rows.test_count.isna().any():
        return {"tests": None, "ignited": None, "ratio": None}
    count = int(rows.test_count.sum())
    if "ignition" in rows:
        known = rows.ignition.isin(["observed", "not_observed"])
        ignition = int(rows.loc[rows.ignition.eq("observed"), "test_count"].sum())
        return {"tests": count, "ignited": ignition if known.all() else None,
                "ratio": ignition / count if count and known.all() else None}
    known = rows.ignited.fillna("").str.casefold().isin(["evet", "hayır", "yes", "no"])
    ignition = int(rows.loc[rows.ignited.fillna("").str.casefold().isin(["evet", "yes"]), "test_count"].sum())
    return {"tests": count, "ignited": ignition if known.all() else None,
            "ratio": ignition / count if count and known.all() else None}


def evidence_gaps(tests, keys):
    dimensions = {"Gravity": "gravity", "Oxygen": "oxygen_pct", "Pressure": "pressure_kpa",
                  "Airflow": "flow", "Sample identity": "sample_material", "Ignition": "ignition",
                  "Sustained burning": "sustained", "Flame spread": "propagation", "Geometry": "geometry",
                  "Extinction": "extinction", "Smoke / aerosol": None}
    result = []
    for material in keys:
        rows = sample_rows(tests, material)
        for dimension, column in dimensions.items():
            if rows.empty:
                status, reason = "Unknown", "No matching test summary is available in the local dataset."
            elif column is None:
                status, reason = "Not reported", "No dedicated structured field is available. Inspect source excerpts for qualitative details."
            else:
                available = rows[column].notna() & ~rows[column].astype(str).str.strip().isin(["", "unknown", "disputed"])
                status = "Reported" if available.all() else "Partly reported" if available.any() else "Not reported"
                reason = f"{int(available.sum())} of {len(rows)} compiled rows contain this field."
                if rows[column].astype(str).eq("disputed").any():
                    status, reason = "Disputed", "Legacy ignition groups conflict with the source Appendix. Review the source before deriving a count."
                if column == "flow":
                    reason += " Values include qualitative descriptions, so numerical flow matching is unavailable."
            result.append({"Material": material_label(material), "Variable": dimension, "Status": status, "Explanation": reason})
    return pd.DataFrame(result, columns=["Material", "Variable", "Status", "Explanation"])
