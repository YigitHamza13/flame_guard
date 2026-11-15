"""Run from the project root; only the bundled offline answer route is evaluated."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.assistant_eval import ROOT,evaluate
if __name__=='__main__':
    result=evaluate()
    (ROOT/'data/assistant_eval_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"Correct source: {result['source_correct']}/{result['source_total']} | Abstained without evidence: {result['abstained']}/{result['absent_total']} | Correct type: {result['kind_correct']}/{result['question_count']}")
