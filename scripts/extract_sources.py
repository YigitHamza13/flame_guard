"""Rebuild page-level primary-source passages after reviewing the downloaded PDFs."""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PAGES = {"20150008962": [2, 3, 9], "19960008389": [1, 2, 3], "20170008805": [9, 12, 29], "SP-4225": [104]}


def main():
    passages = []
    for source, pages in PAGES.items():
        path = ROOT / "sources/originals" / f"{source}.pdf"
        reader = PdfReader(path)
        for page in pages:
            passages.append({"source_id": source, "page": page,
                             "pdf_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                             "text": reader.pages[page - 1].extract_text()})
    target = ROOT / "data/primary_passages.json"
    target.write_text(json.dumps(passages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
