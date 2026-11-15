"""One place for source links: every citation opens the NASA PDF at the cited page, not just the record page.
PDF addresses are the ones listed by the NTRS API (/api/citations/<id>) for each document."""

PDF = {
    "19960008389": "https://ntrs.nasa.gov/api/citations/19960008389/downloads/19960008389.pdf",          # WIF (USML-1, Spacelab)
    "20150008962": "https://ntrs.nasa.gov/api/citations/20150008962/downloads/20150008962.pdf",          # BASS (ISS)
    "20170008805": "https://ntrs.nasa.gov/api/citations/20170008805/downloads/20170008805.pdf",          # Saffire-II
    "20000024924": "https://ntrs.nasa.gov/api/citations/20000024924/downloads/20000024924.pdf",          # Mir FFFT 1999
    "20240002981": "https://ntrs.nasa.gov/api/citations/20240002981/downloads/Saffire-ICES-2024-ICES-365-accepted%20final.pdf",
    "20210011385": "https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf",      # BASS-II summary
    "20250010653": "https://ntrs.nasa.gov/api/citations/20250010653/downloads/ASGSR%202025-LUCI-Ferkul-Presentation-v2-20250010653.pdf",
    "20240015307": "https://ntrs.nasa.gov/api/citations/20240015307/downloads/Glenn_2024_ZayacPoster.pdf",
    "20260001966": "https://ntrs.nasa.gov/api/citations/20260001966/downloads/Ferkul-Lunar%20and%20Planetary%20Science%20Conf%202026%20v2.pdf",
}


def page(doc_id: str, page_no: int | None = None) -> str:
    """Direct PDF link, opened at the page when one is given."""
    url = PDF.get(doc_id, f"https://ntrs.nasa.gov/citations/{doc_id}")
    return f"{url}#page={int(page_no)}" if page_no and doc_id in PDF else url


# Where each microgravity experiment actually flew (stated in the cited reports).
PLATFORM = {
    "20150008962": ("International Space Station (BASS)", "Uluslararası Uzay İstasyonu (BASS)"),
    "WIF": ("Space Shuttle, Spacelab USML-1 (WIF)", "Uzay Mekiği, Spacelab USML-1 (WIF)"),
    "Saffire": ("uncrewed Cygnus cargo vehicle (Saffire)", "insansız Cygnus kargo aracı (Saffire)"),
    "SAFFIRE": ("uncrewed Cygnus cargo vehicle (Saffire)", "insansız Cygnus kargo aracı (Saffire)"),
    "FFFT": ("Mir space station (FFFT)", "Mir uzay istasyonu (FFFT)"),
    "MIR-FFFT": ("Mir space station (FFFT)", "Mir uzay istasyonu (FFFT)"),
}


def platform(experiment_ids, tr: bool = False) -> str:
    names = []
    for eid in experiment_ids:
        for prefix, label in PLATFORM.items():
            if str(eid).startswith(prefix):
                names.append(label[1 if tr else 0])
                break
    return ", ".join(dict.fromkeys(names))
