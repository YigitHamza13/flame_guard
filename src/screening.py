"""Transparent condition comparisons and context-preserving research exports."""
import json
from datetime import datetime, timezone

import pandas as pd

from src.evidence import material_label, sample_rows


def numeric_comparison(reported, assumed):
    if assumed is None or pd.isna(reported):
        return "unknown"
    return "equal" if abs(float(reported) - float(assumed)) < 0.000001 else "different"


def condition_comparison(rows, environment, assumptions):
    target = {"ISS": "microgravity", "Earth Lab": "normal gravity", "Moon Base": "lunar", "Mars Mission": None}[environment]
    output = []
    for _, row in rows.iterrows():
        gravity = "unknown" if target is None or pd.isna(row.gravity) else "equal" if row.gravity.casefold() == target else "different"
        oxygen = numeric_comparison(row.oxygen_pct, assumptions.get("oxygen"))
        pressure = numeric_comparison(row.pressure_kpa, assumptions.get("pressure"))
        state = "source_conflict" if row.get("review_status") == "conflict" else "different_conditions" if "different" in (gravity, oxygen, pressure) else "incomplete_conditions"
        if state == "incomplete_conditions" and all(v == "equal" for v in (gravity, oxygen, pressure)):
            state = "three_fields_equal"
        output.append({"record_id": row.record_id, "experiment_id": row.experiment_id, "material": row.material,
                       "gravity_match": gravity, "oxygen_match": oxygen, "pressure_match": pressure, "comparison": state})
    return pd.DataFrame(output, columns=["record_id", "experiment_id", "material", "gravity_match", "oxygen_match", "pressure_match", "comparison"])


def scope(tests, extras, filters):
    """The one evidence scope used by every output (cards, tables, two worlds, PDF, CSV, JSON, brief).
    With the oxygen filter on, compiled rows need a reported oxygen inside the range; a separate-table specimen
    stays only if its whole reported oxygen range is inside (its tests cannot be split)."""
    if not filters.get("oxygen_enabled"):
        return tests, dict(extras)
    lo, hi = filters["oxygen_range"]
    scoped = tests[tests.oxygen_pct.between(lo, hi)]
    ex = {k: v for k, v in extras.items() if v.get("oxygen_pct") and lo <= min(v["oxygen_pct"]) and max(v["oxygen_pct"]) <= hi}
    return scoped, ex


def _extra_record(key, spec):
    from src.links import page, platform
    first = spec["sources"][0]
    return {"material": key, "experiment_id": ", ".join(spec["experiments"]), "test_count": spec["tests"],
            "ignition": f"ignited {spec['ignited']} of {spec['tests']}", "sustained": "not_reported", "propagation": "not_reported",
            "extinction": "not_reported", "oxygen_pct": "–".join(f"{x:g}" for x in sorted(set(spec["oxygen_pct"] or []))) or None,
            "pressure_kpa": "–".join(f"{x:g}" for x in sorted(set(spec["pressure_kpa"] or []))) or None,
            "gravity": spec.get("gravity"), "platform": platform(spec["experiments"]),
            "source_url": first["url"].split("#")[0], "source_page": first["page"],
            "source_page_url": page(first["id"], first["page"]),
            "all_source_pages": "; ".join(f"{x['short']} p. {x['page']}: {page(x['id'], x['page'])}" for x in spec["sources"]),
            "source_note_en": f"{spec['name_en']} · separate verified table · {', '.join(spec['experiments'])}",
            "source_note_tr": f"{spec['name_tr']} · ayrı doğrulanmış tablo · {', '.join(spec['experiments'])}",
            "evidence_status": "verified_separate_table", "comparison": "different_conditions_possible"}


def evidence_export(tests, selected, environment, assumptions, filters, snapshot, extras=None, item_status=None, pairs=None):
    from src.extended_evidence import load_extension
    from src.links import platform
    extended, _, extended_snapshot = load_extension()
    extras = extras or {}
    reference, ex_scope = scope(tests, extras, filters)
    reference = reference[reference.material.isin(selected)].copy()
    words = {k if k else w: w for w, k in (pairs or [])}
    records = []
    comparison = condition_comparison(reference, environment, assumptions).set_index("record_id").to_dict("index")
    for material in selected:
        if material in extras:
            if material in ex_scope:
                records.append(_extra_record(material, extras[material]))
            else:
                records.append({"material": material, "evidence_status": "outside_filter", "test_count": None,
                                "ignition": "unknown", "comparison": "outside_filter"})
            continue
        rows = sample_rows(reference, material)
        if rows.empty:
            status = (item_status or {}).get(words.get(material, material), "none")
            reason = {"ask": "material_not_chosen", "other_material": "material_not_tested_in_collection"}.get(
                status, "outside_filter" if filters.get("oxygen_enabled") and not sample_rows(tests, material).empty else "no_matching_evidence")
            records.append({"material": material, "evidence_status": reason, "test_count": None,
                            "ignition": "unknown", "comparison": reason})
        else:
            for row in json.loads(rows.to_json(orient="records", force_ascii=False)):
                records.append({**row, **comparison[row["record_id"]], "evidence_status": "compiled_reference",
                                "platform": platform([row.get("experiment_id", "")])})
    for row in records:
        aliases = {'plastik (pmma)': 'PMMA', 'pamuklu kumaş': 'SIBAL', 'pmma_extra': 'PMMA'}
        term = aliases.get(row['material'])
        related = [r for r in extended if term and term.casefold() in r['material'].casefold()]
        label = extras[row["material"]]["name_en"] if row["material"] in extras else material_label(row["material"])
        row.update({"cargo_item": words.get(row["material"], row["material"]),
                    "sample_group": label, "selected_environment": environment,
                    "related_study_records_json": json.dumps(related, ensure_ascii=False), "extended_snapshot_sha256": extended_snapshot,
                    "assumed_oxygen_pct": assumptions.get("oxygen"), "assumed_pressure_kpa": assumptions.get("pressure"),
                    "assumed_mission_phase": assumptions.get("atmosphere", ""), "filters_json": json.dumps(filters),
                    "snapshot_sha256": snapshot, "exported_utc": datetime.now(timezone.utc).isoformat(),
                    "risk_status": "unavailable", "human_approval": "pending",
                    "count_note": "observed counts under the listed conditions; not a general ignition probability"})
        if row.get("source_url") and row.get("source_page") and not row.get("source_page_url"):
            row["source_page_url"] = row["source_url"] + "#page=" + str(int(row["source_page"]))
    return pd.DataFrame(records)


def csv_bytes(frame):
    safe = frame.map(lambda x: "'" + x if isinstance(x, str) and x.lstrip().startswith(("=", "+", "-", "@")) else x)
    return safe.to_csv(index=False).encode("utf-8-sig")


def research_brief(frame, lang="EN"):
    tr = lang == "TR"
    title = "FLAMEGUARD araştırma özeti" if tr else "FLAMEGUARD research brief"
    lines = [f"# {title}", "", "İnsan uzman onayı bekliyor. Uçuşa uygunluk kararı içermez. Sayılar, belirtilen koşullarda gözlenen sonuçlardır; genel bir tutuşma olasılığı değildir." if tr else
             "Human expert approval pending. No flight qualification decision. Counts are observed results under the listed conditions, not a general ignition probability.", ""]
    if frame.empty:
        return "\n".join(lines)
    first = frame.iloc[0]
    lines += [f"Environment / Ortam: {first.selected_environment}", f"Snapshot SHA-256: {first.snapshot_sha256}",
              f"Assumptions / Varsayımlar: O₂={first.assumed_oxygen_pct} %, P={first.assumed_pressure_kpa} kPa; {first.assumed_mission_phase}",
              f"Filters / Filtreler: {first.filters_json}", ""]
    for material, group in frame.groupby("sample_group", sort=False):
        lines += [f"## {material}"]
        for _, row in group.iterrows():
            if row.evidence_status in ("no_matching_evidence", "outside_filter", "material_not_chosen", "material_not_tested_in_collection"):
                why = {"outside_filter": ("Seçili oksijen aralığında test yok.", "No test inside the selected oxygen range."),
                       "material_not_chosen": ("Malzeme seçilmedi; FLAMEGUARD tahmin etmez.", "Material not chosen; FLAMEGUARD does not guess."),
                       "material_not_tested_in_collection": ("Bu malzeme koleksiyonda test edilmemiş.", "This material was not tested in the collection.")}.get(
                    row.evidence_status, ("Özgün derlemede eşleşen kanıt yok; ek çalışma kayıtları JSON alanındadır.",
                                          "No matching evidence in the original compilation; related study records are preserved in the JSON field."))
                lines += [why[0] if tr else why[1]]
            else:
                lines += [f"- {row.experiment_id} ({row.get('platform', '') or 'platform not listed'}): {row.test_count} tests; ignition={row.ignition}; sustained={row.sustained}; spread={row.propagation}; extinction={row.extinction}; O2={row.get('oxygen_pct')}; P={row.get('pressure_kpa')}",
                          f"  Source: {row.source_page_url}", f"  {row.source_note_tr if tr else row.source_note_en}"]
        lines += [""]
    return "\n".join(lines)
