"""Download explicitly listed public review inputs; never prints credentials."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import urllib.request
import hashlib

ROOT = Path(__file__).resolve().parents[1]
URLS = {
 "static/models/earth.glb": "https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/e/Earth_1_12756.glb",
 "static/models/moon.glb": "https://svs.gsfc.nasa.gov/vis/a010000/a014900/a014959/moon_small.glb",
 "static/models/mars.glb": "https://assets.science.nasa.gov/content/dam/science/psd/mars/resources/gltf_files/24881_Mars_1_6792.glb",
 "static/models/iss.glb": "https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/i/ISS_stationary.glb",
 "assets/model-viewer.min.js": "https://unpkg.com/@google/model-viewer@4.1.0/dist/model-viewer.min.js",
 "assets/model-viewer-LICENSE.txt": "https://raw.githubusercontent.com/google/model-viewer/master/LICENSE",
 "sources/originals/20250010653.pdf": "https://ntrs.nasa.gov/api/citations/20250010653/downloads/ASGSR%202025-LUCI-Ferkul-Presentation-v2-20250010653.pdf",
 "sources/originals/20250002114.pdf": "https://ntrs.nasa.gov/api/citations/20250002114/downloads/ICES_2025-392-correctedcaptions.pdf",
 "sources/originals/20240015307.pdf": "https://ntrs.nasa.gov/api/citations/20240015307/downloads/Glenn_2024_ZayacPoster.pdf",
 "sources/originals/20260001966.pdf": "https://ntrs.nasa.gov/api/citations/20260001966/downloads/Ferkul-Lunar%20and%20Planetary%20Science%20Conf%202026%20v2.pdf",
 "sources/originals/20210021318.pdf": "https://ntrs.nasa.gov/api/citations/20210021318/downloads/Tech%20Dev%20for%20Spacecraft%20Fire%20Safety_Location_10-7-2021.pdf",
 "assets/fonts/IBMPlexSans-Regular.woff2": "https://cdn.jsdelivr.net/npm/@ibm/plex@6.4.1/IBM-Plex-Sans/fonts/complete/woff2/IBMPlexSans-Regular.woff2",
 "assets/fonts/IBMPlexSans-SemiBold.woff2": "https://cdn.jsdelivr.net/npm/@ibm/plex@6.4.1/IBM-Plex-Sans/fonts/complete/woff2/IBMPlexSans-SemiBold.woff2",
 "assets/fonts/IBMPlexMono-Regular.woff2": "https://cdn.jsdelivr.net/npm/@ibm/plex@6.4.1/IBM-Plex-Mono/fonts/complete/woff2/IBMPlexMono-Regular.woff2",
 "assets/fonts/OFL.txt": "https://raw.githubusercontent.com/IBM/plex/master/LICENSE.txt",
}

def fetch(item):
    name, url = item
    path = ROOT / name
    try:
        if path.exists() and path.stat().st_size > 100:
            return f"{name}: already saved"
        if name.endswith('.woff2'):
            family = 'plex-mono' if 'Mono' in name else 'plex-sans'
            url = f'https://raw.githubusercontent.com/IBM/plex/master/packages/{family}/fonts/complete/woff2/{path.name}'
            path = ROOT / 'static/fonts' / path.name
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = response.read()
        if name.endswith('.pdf') and not payload.startswith(b'%PDF'):
            raise ValueError('Not a PDF')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return f"{name}: {len(payload)} bytes SHA256={hashlib.sha256(payload).hexdigest()}"
    except Exception as error:
        return f"{name}: {type(error).__name__}: {error}"

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(fetch, URLS.items()):
            print(result)
