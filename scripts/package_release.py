"""Build a reviewed allowlist archive. Never walk credentials, logs or runtime state."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = ["app.py", "README.md", "requirements.txt", "requirements-dev.txt", "Dockerfile", ".dockerignore", ".gitignore", ".streamlit/config.toml"]
PATTERNS = {"src": "*.py", "scripts": "*.py", "tests": "*.py", "docs": "*.md", "sources": "*.txt", "sources/originals": "*.pdf", "static/fonts": "*.[wt]*f*", "static/images": "*.jpg", "static/models": "*.glb", "data/review_queue": "*.json", "static/js": "*.js"}
ASSETS = ["style.css", "planet.html", "earth.jpg", "moon.jpg", "mars.jpg", "bass-ii-msg.jpg",
          "flameguard-symbol.png", "flameguard-icon.png", "flameguard-transparent.png", "context-model.html", "model-viewer.min.js", "model-viewer-LICENSE.txt", "fonts/OFL.txt"]
DATA = ["experiments.csv", "materials.csv", "psi_combustion_investigations.json", "source_review.json", "primary_passages.json", "extended_review.json", "extended_passages.json", "additional_specimens.json", "assistant_sources.json", "assistant_eval_result.json"]


def release_files(root=ROOT):
    paths = [root / name for name in FILES] + [root / "data" / name for name in DATA]
    paths += [root / "assets" / name for name in ASSETS]
    for folder, pattern in PATTERNS.items():
        paths += [p for p in (root / folder).glob(pattern) if p.is_file()]
    paths += [root / 'static/images/flameguard-icon.png']
    paths += list((root / 'locales').glob('*.json'))
    paths += list((root / 'tests/fixtures').glob('*.json'))
    paths += list((root / 'scripts').glob('*.cjs'))
    paths += list((root / 'docs').glob('performance-*.json'))
    return sorted(set(paths))


def build(root=ROOT):
    output = root / "dist"
    output.mkdir(exist_ok=True)
    archive = output / "FLAMEGUARD-DEPLOY-READY.zip"
    paths = release_files(root)
    manifest = {}
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
        for path in paths:
            name = path.relative_to(root).as_posix()
            payload = path.read_bytes()
            manifest[name] = hashlib.sha256(payload).hexdigest()
            bundle.writestr(name, payload)
        bundle.writestr("RELEASE-MANIFEST.json", json.dumps(manifest, indent=2))
    with ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == set(manifest) | {"RELEASE-MANIFEST.json"}
    return archive, hashlib.sha256(archive.read_bytes()).hexdigest(), len(manifest)


if __name__ == "__main__":
    path, digest, count = build()
    print(json.dumps({"archive": str(path), "sha256": digest, "files": count}))
