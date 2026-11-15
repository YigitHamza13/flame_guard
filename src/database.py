"""Transactional, versioned local evidence store. Imported content never implies human approval."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, manifest TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sources(snapshot TEXT, id TEXT, document TEXT NOT NULL,
 PRIMARY KEY(snapshot,id), FOREIGN KEY(snapshot) REFERENCES snapshots(id));
CREATE TABLE IF NOT EXISTS experiments(snapshot TEXT, id TEXT, platform TEXT, experiment_date TEXT, source_id TEXT,
 PRIMARY KEY(snapshot,id), FOREIGN KEY(snapshot,source_id) REFERENCES sources(snapshot,id));
CREATE TABLE IF NOT EXISTS samples(snapshot TEXT, id INTEGER, name TEXT, composition TEXT, geometry TEXT, mapping_note TEXT,
 PRIMARY KEY(snapshot,id), FOREIGN KEY(snapshot) REFERENCES snapshots(id));
CREATE TABLE IF NOT EXISTS test_groups(snapshot TEXT, id INTEGER, experiment_id TEXT, sample_id INTEGER,
 test_count REAL, raw_json TEXT NOT NULL, reviewed_json TEXT NOT NULL,
 PRIMARY KEY(snapshot,id), FOREIGN KEY(snapshot,experiment_id) REFERENCES experiments(snapshot,id),
 FOREIGN KEY(snapshot,sample_id) REFERENCES samples(snapshot,id));
CREATE TABLE IF NOT EXISTS measurements(snapshot TEXT, group_id INTEGER, variable TEXT, value REAL, unit TEXT,
 scope TEXT, uncertainty REAL, source_id TEXT, location TEXT,
 PRIMARY KEY(snapshot,group_id,variable), FOREIGN KEY(snapshot,group_id) REFERENCES test_groups(snapshot,id),
 FOREIGN KEY(snapshot,source_id) REFERENCES sources(snapshot,id));
CREATE TABLE IF NOT EXISTS outcomes(snapshot TEXT, group_id INTEGER, ignition TEXT, sustained TEXT,
 propagation TEXT, extinction TEXT, source_id TEXT, location TEXT,
 PRIMARY KEY(snapshot,group_id), FOREIGN KEY(snapshot,group_id) REFERENCES test_groups(snapshot,id));
CREATE TABLE IF NOT EXISTS reviews(snapshot TEXT, group_id INTEGER, status TEXT, reviewer TEXT, reviewed_on TEXT,
 human_approval TEXT NOT NULL, source_id TEXT, location TEXT,
 PRIMARY KEY(snapshot,group_id), FOREIGN KEY(snapshot,group_id) REFERENCES test_groups(snapshot,id));
CREATE TABLE IF NOT EXISTS collections(snapshot TEXT, kind TEXT, content TEXT NOT NULL,
 PRIMARY KEY(snapshot,kind), FOREIGN KEY(snapshot) REFERENCES snapshots(id));
CREATE TABLE IF NOT EXISTS passages(snapshot TEXT, source_id TEXT, page INTEGER, text TEXT NOT NULL,
 PRIMARY KEY(snapshot,source_id,page), FOREIGN KEY(snapshot,source_id) REFERENCES sources(snapshot,id));
"""


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def sync_store(root, tests, mappings, catalog, excerpts):
    """Keep immutable import versions, comparing every original row before committing."""
    root = Path(root).resolve()
    required = [root / "data" / name for name in ("experiments.csv", "materials.csv", "source_review.json", "psi_combustion_investigations.json")]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required evidence files missing: " + ", ".join(missing))
    review = json.loads((root / "data/source_review.json").read_text(encoding="utf-8"))
    files = [root / "data" / name for name in ("experiments.csv", "materials.csv", "psi_combustion_investigations.json", "source_review.json", "primary_passages.json")]
    files += sorted((root / "sources").glob("*.txt"))
    files += sorted((root / "sources/originals").glob("*.pdf"))
    manifest = {path.relative_to(root).as_posix(): digest(path) for path in files if path.exists()}
    manifest["import_schema"] = "2.3.0"
    snapshot = hashlib.sha256(encode(manifest).encode()).hexdigest()
    source_docs = {s["id"]: s for s in review["sources"]}
    input_matches = manifest.get("data/experiments.csv") == review["experiments_sha256"]
    raw_rows = json.loads(tests.to_json(orient="records", force_ascii=False))
    map_rows = json.loads(mappings.to_json(orient="records", force_ascii=False))
    reviews = {g["row"]: g for g in review["groups"]} if input_matches else {}
    issues = [] if input_matches else ["Source review is stale. Imported rows require a new source review."]
    passages = []
    if manifest.get("data/primary_passages.json") == review.get("primary_passages_sha256"):
        passages = json.loads((root / "data/primary_passages.json").read_text(encoding="utf-8"))
    else:
        issues.append("Primary source text unavailable or changed. Source search is disabled until review.")
    passages = [p for p in passages if p["source_id"] in source_docs and
                p["pdf_sha256"] == source_docs[p["source_id"]]["sha256"] and
                manifest.get("sources/originals/" + source_docs[p["source_id"]]["pdf"]) == p["pdf_sha256"]]
    db_path = root / "data/flameguard.sqlite3"
    with closing(sqlite3.connect(db_path, timeout=30)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(SCHEMA)
        with db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT 1 FROM snapshots WHERE id=?", (snapshot,)).fetchone():
                db.execute("INSERT INTO snapshots VALUES(?,?,?)", (snapshot, datetime.now(timezone.utc).isoformat(), encode(manifest)))
                for source in source_docs.values():
                    db.execute("INSERT INTO sources VALUES(?,?,?)", (snapshot, source["id"], encode(source)))
                db.execute("INSERT INTO sources VALUES(?,?,?)", (snapshot, "unreviewed", encode({"id": "unreviewed"})))
                for passage in passages:
                    db.execute("INSERT INTO passages VALUES(?,?,?,?)", (snapshot, passage["source_id"], passage["page"], passage["text"]))
                for index, original in enumerate(raw_rows, 1):
                    group = reviews.get(index, {})
                    source = source_docs.get(group.get("source"), {})
                    source_ok = bool(source) and manifest.get("sources/originals/" + source["pdf"]) == source["sha256"]
                    if not source_ok:
                        group, source = {}, {}
                    source_id = source.get("id", "unreviewed")
                    reviewed = dict(original)
                    reviewed.update(evidence_type="measured_experiment", document_type="unknown", peer_review_status="unknown",
                                    gravity_level_g=None, gravity_method="unknown", source_scope="full_text_read" if source_ok else "abstract_only")
                    reviewed.update({"record_id": index, "review_status": group.get("status", "pending"),
                                     "source_id": source_id, "source_location": source.get("location", ""),
                                     "source_page": source.get("page"), "source_pdf": source.get("pdf"),
                                     "human_approval": "pending", "reviewed_on": review["reviewed_on"] if group else None,
                                     "platform": source.get("platform", "Unknown"), "geometry": group.get("geometry"),
                                     "composition": group.get("composition"), "flow_cm_s": group.get("flow_cm_s"),
                                     "source_note_en": source.get("finding_en", "Source review pending."),
                                     "source_note_tr": source.get("finding_tr", "Kaynak incelemesi bekliyor."),
                                     "legacy_ignited": original.get("ignited"), "raw_pressure_kpa": original.get("pressure_kpa")})
                    for field in ("ignition", "sustained", "propagation", "extinction"):
                        reviewed[field] = group.get(field, "unknown")
                    if "pressure_kpa" in group:
                        reviewed["pressure_kpa"] = group["pressure_kpa"]
                    reviewed["pressure_basis"] = group.get("pressure_original")
                    reviewed["pressure_scope"] = group.get("pressure_scope")
                    # Keep the original yes/no field for legacy export only. It is never used for reviewed totals.
                    experiment_id = str(original["experiment_id"])
                    db.execute("INSERT OR IGNORE INTO experiments VALUES(?,?,?,?,?)", (snapshot, experiment_id, source.get("platform"), source.get("experiment_date"), source_id))
                    db.execute("INSERT INTO samples VALUES(?,?,?,?,?,?)", (snapshot, index, original["sample_material"], group.get("composition"), group.get("geometry"), original.get("mapping_note")))
                    db.execute("INSERT INTO test_groups VALUES(?,?,?,?,?,?,?)", (snapshot, index, experiment_id, index, original["test_count"], encode(original), encode(reviewed)))
                    for variable, unit in (("oxygen_pct", "%"), ("pressure_kpa", "kPa"), ("flow_cm_s", "cm/s")):
                        scope = group.get("pressure_scope") if variable == "pressure_kpa" else "compiled sample / reported initial condition"
                        db.execute("INSERT INTO measurements VALUES(?,?,?,?,?,?,?,?,?)", (snapshot, index, variable, reviewed.get(variable), unit, scope, None, source_id, source.get("location")))
                    db.execute("INSERT INTO outcomes VALUES(?,?,?,?,?,?,?,?)", (snapshot, index, reviewed["ignition"], reviewed["sustained"], reviewed["propagation"], reviewed["extinction"], source_id, source.get("location")))
                    db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?)", (snapshot, index, reviewed["review_status"], review["reviewer"] if group else None, reviewed["reviewed_on"], "pending", source_id, source.get("location")))
                for kind, content in (("mappings", map_rows), ("catalog", catalog), ("excerpts", excerpts)):
                    db.execute("INSERT INTO collections VALUES(?,?,?)", (snapshot, kind, encode(content)))
                imported = [json.loads(row[0]) for row in db.execute("SELECT raw_json FROM test_groups WHERE snapshot=? ORDER BY id", (snapshot,))]
                if imported != raw_rows:
                    raise ValueError("Lossless migration check failed")
                if db.execute("PRAGMA foreign_key_check").fetchall():
                    raise ValueError("Evidence relationships failed validation")
            rows = [json.loads(row[0]) for row in db.execute("SELECT reviewed_json FROM test_groups WHERE snapshot=? ORDER BY id", (snapshot,))]
            collections = {kind: json.loads(content) for kind, content in db.execute("SELECT kind,content FROM collections WHERE snapshot=?", (snapshot,))}
            documents = [json.loads(row[0]) for row in db.execute("SELECT document FROM sources WHERE snapshot=? AND id != 'unreviewed'", (snapshot,))]
    checked_sources = []
    for source in documents:
        if manifest.get("sources/originals/" + source["pdf"]) != source["sha256"]:
            issues.append(f"Source document unavailable or changed: {source['id']}")
            continue
        for passage in passages:
            if passage["source_id"] == source["id"]:
                checked_sources.append({**source, "source_id": source["id"], "id": f"{source['id']}:p{passage['page']}",
                                        "page": passage["page"], "text": passage["text"], "review_status": "source_checked",
                                        "human_approval": "pending", "accessed_on": review["reviewed_on"],
                                        "url": source["url"] + f"#page={passage['page']}"})
    return rows, collections, checked_sources, issues, snapshot
