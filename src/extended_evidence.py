"""Separately versioned partial-gravity evidence; original compilation is immutable."""
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
TYPES = {'measured_experiment', 'theoretical_model', 'planned_experiment', 'mission_assumption', 'context_only'}


def eligible_measurements(records):
    return [r for r in records if r.get('evidence_type') == 'measured_experiment' and r.get('review_status') == 'source_checked']


def logical_sources(records):
    return {r['logical_source'] for r in records}


def load_extension(root=ROOT):
    root = Path(root)
    registry = root / 'data/extended_review.json'
    if not registry.exists():
        return [], [], ''
    raw = registry.read_bytes()
    document = json.loads(raw)
    passage_path = root / 'data/extended_passages.json'
    passage_bytes = passage_path.read_bytes()
    passages_ok = hashlib.sha256(passage_bytes).hexdigest() == document['passages_sha256']
    manifest = {'registry': hashlib.sha256(raw).hexdigest(), 'passages': hashlib.sha256(passage_bytes).hexdigest()}
    sources = {s['id']: s for s in document['sources']}
    for source in sources.values():
        path = root / 'sources/originals' / source.get('pdf', '')
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        manifest[source['id']] = digest
        source['review_status'] = 'source_checked' if digest and digest == source.get('sha256') and passages_ok else 'unverified_source'
    records = []
    for original in document['records']:
        row = {**original}
        source = sources[row['source_id']]
        assert row['evidence_type'] in TYPES
        row.update(review_status=source['review_status'], human_approval='pending', source_scope=source['source_scope'],
                   document_type=source['document_type'], peer_review_status=source['peer_review_status'], sha256=source.get('sha256'),
                   url=source['url'], title=source['title'], logical_source=source['logical_source'])
        records.append(row)
    passages = []
    for p in json.loads(passage_bytes) if passages_ok else []:
        source = sources[p['source_id']]
        if source['review_status'] == 'source_checked' and p['pdf_sha256'] == source['sha256']:
            kinds = sorted({r['evidence_type'] for r in records if r['source_id'] == p['source_id'] and p['page'] in r['source_pages']})
            passages.append({**source, **p, 'id': f"{source['id']}-p{p['page']}", 'source_id': source['id'],
                             'evidence_type': ', '.join(kinds) or 'context_only',
                             'url': source['url'] + f"#page={p['page']}", 'accessed_on': document['reviewed_on'],
                             'location': f"PDF page {p['page']}", 'finding_en': source['title'], 'finding_tr': source['title']})
    snapshot = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    with sqlite3.connect(root / 'data/flameguard.sqlite3', timeout=30) as db:
        db.execute('CREATE TABLE IF NOT EXISTS extended_snapshots(id TEXT PRIMARY KEY, manifest TEXT NOT NULL, records TEXT NOT NULL)')
        db.execute('INSERT OR IGNORE INTO extended_snapshots VALUES(?,?,?)', (snapshot, json.dumps(manifest), json.dumps(records, ensure_ascii=False)))
    return records, passages, snapshot
