"""Reproducible local regression benchmark; not independent scientific validation."""
import hashlib
import json
from pathlib import Path
from src.answers import resolve_answer
ROOT = Path(__file__).resolve().parents[1]

def fingerprint(root=ROOT):
    files=['src/answers.py','tests/fixtures/assistant_eval.json','data/assistant_sources.json','data/experiments.csv']
    return {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}

def evaluate(root=ROOT):
    fixture=json.loads((root/'tests/fixtures/assistant_eval.json').read_text(encoding='utf-8'))
    rows=[]
    for f in fixture:
        result=resolve_answer(f['question'],f['lang'])
        ids=sorted({s['id'] for s in result['sources']})
        rows.append(dict(**f, actual_kind=result['kind'], actual_sources=ids,
                         correct_kind=result['kind']==f['expected_kind'],
                         correct_source=f['expected_source'] in ids if f['expected_source'] else None))
    sourced=[r for r in rows if r['expected_source']]
    absent=[r for r in rows if r['expected_kind']=='none']
    return dict(schema=1, fingerprint=fingerprint(root), question_count=len(rows),
                source_correct=sum(r['correct_source'] for r in sourced), source_total=len(sourced),
                abstained=sum(r['actual_kind']=='none' for r in absent), absent_total=len(absent),
                kind_correct=sum(r['correct_kind'] for r in rows), cases=rows)

def load_current(root=ROOT):
    path=root/'data/assistant_eval_result.json'
    if not path.exists(): return None
    result=json.loads(path.read_text(encoding='utf-8'))
    return result if result.get('fingerprint')==fingerprint(root) else None
