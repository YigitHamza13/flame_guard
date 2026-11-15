"""Ingestion pipeline: NASA NTRS report → hashed PDF → page text → candidate findings in a review queue.

Usage (development machine, needs `pip install pypdf`):
    python scripts/ingest_ntrs.py 20010073996                 # downloads the PDF from ntrs.nasa.gov
    python scripts/ingest_ntrs.py 20010073996 --pdf file.pdf  # uses a PDF you already have

Nothing written here is used in results. Every candidate keeps human_approval = "pending" until a reviewer checks
the sentence on the cited page and moves the value into the reviewed data by hand.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "sources" / "incoming"
QUEUE = ROOT / "data" / "review_queue"

UNIT = re.compile(r"(\d+(?:\.\d+)?)\s*(%|percent|kPa|psia|psi|atm|cm/s|mm/s|s\b|seconds)", re.I)
TOPIC = re.compile(r"ignit|extinguish|extinction|quench|blow-?off|flame spread|spread rate|burn|oxygen|O2|pressure|flow", re.I)


def fetch(source_id: str) -> Path:
    if not re.fullmatch(r"\d{11}", source_id):
        sys.exit("NTRS IDs are 11 digits, e.g. 20010073996")
    url = f"https://ntrs.nasa.gov/api/citations/{source_id}/downloads/{source_id}.pdf"
    INCOMING.mkdir(parents=True, exist_ok=True)
    target = INCOMING / f"{source_id}.pdf"
    req = urllib.request.Request(url, headers={"User-Agent": "FLAMEGUARD ingestion"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if not resp.headers.get("Content-Type", "").startswith("application/pdf"):
            sys.exit(f"NTRS did not return a PDF for {source_id}")
        target.write_bytes(resp.read())
    return target


def candidates(pdf: Path) -> tuple:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf))
    found = []
    for number, page in enumerate(reader.pages, 1):
        text = re.sub(r"\s+", " ", page.extract_text() or "")
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text):
            units = UNIT.findall(sentence)
            if units and TOPIC.search(sentence) and 30 <= len(sentence) <= 400:
                found.append({"page": number, "sentence": sentence.strip(),
                              "values": [f"{v} {u}" for v, u in units][:6],
                              "topics": sorted({m.group(0).lower() for m in TOPIC.finditer(sentence)})[:6],
                              "human_approval": "pending"})
    return len(reader.pages), found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source_id")
    ap.add_argument("--pdf", type=Path, help="use a local PDF instead of downloading")
    ap.add_argument("--out", type=Path, default=QUEUE, help="queue folder (default data/review_queue)")
    args = ap.parse_args(argv)
    pdf = args.pdf or fetch(args.source_id)
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    pages, found = candidates(pdf)
    args.out.mkdir(parents=True, exist_ok=True)
    record = {"source_id": args.source_id, "url": f"https://ntrs.nasa.gov/citations/{args.source_id}",
              "pdf_sha256": digest, "pages": pages, "extracted_on": dt.date.today().isoformat(),
              "status": "awaiting review", "candidates": found}
    (args.out / f"{args.source_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{args.source_id}: {pages} pages, {len(found)} candidate sentences → {args.out / (args.source_id + '.json')}")


if __name__ == "__main__":
    main()
