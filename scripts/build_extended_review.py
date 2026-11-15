"""Reproducible extraction of inspected public PDFs. Requires pypdf for maintenance only."""
from pathlib import Path
import hashlib
import json
from pypdf import PdfReader
from fetch_review_assets import URLS

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
 ('20250010653', 'Lunar Combustion Investigation: Flammability Results from a Rotating Sounding Rocket', 'conference_presentation', 'LUCI-2025', [4,12,13,16,17,19,20,21,22,33,36,42]),
 ('20250002114', 'Solid Fuel Ignition Testing for Lunar Applications, Theory and Experimental Results', 'conference_paper', 'ICES-2025-392', [2,4,5,6,7,8,9]),
 ('20240015307', 'Flammability of Materials on the Moon', 'poster', 'FM2-2024', [1]),
 ('20260001966', 'Material Flammability at Lunar and Martian Gravity', 'conference_presentation', 'LPSC-2026', [5,6,9,10,13,20,21,22]),
 ('20210021318', 'Development of Spacecraft Fire Safety Technology for Exploration', 'conference_presentation', 'FIRE-SAFETY-2021', [3,7,13]),
]


def build():
    sources, passages = [], []
    for sid, title, dtype, logical, pages in SPECS:
        path = ROOT / 'sources/originals' / (sid + '.pdf')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        reader = PdfReader(path)
        sources.append(dict(id=sid, title=title, pdf=path.name, sha256=digest, document_type=dtype,
                            logical_source=logical, source_scope='full_text_read', peer_review_status='unknown',
                            url=URLS[f'sources/originals/{sid}.pdf'],
                            related_ids=['20250006779'] if sid == '20250002114' else ['20260000646'] if sid == '20260001966' else []))
        for page in pages:
            passages.append(dict(source_id=sid, page=page, text=reader.pages[page-1].extract_text(), pdf_sha256=digest))
    sources.append(dict(id='PMMA-2024', title='Partial gravity flammability of cast PMMA rods in concurrent axial stagnation flow',
                        document_type='journal_article', logical_source='DOI:10.1016/j.firesaf.2024.104267',
                        source_scope='abstract_only', peer_review_status='unknown', url='https://doi.org/10.1016/j.firesaf.2024.104267'))
    def record(rid, source, kind, material, gravity, method, pages, note, **values):
        return dict(id=rid, source_id=source, evidence_type=kind, material=material, gravity_class=gravity,
                    gravity_method=method, gravity_level_g=values.pop('gravity_level_g', None), source_pages=pages,
                    test_count=None, notes=note, measurements=values)
    records = [
      record('LUCI-SIBAL', '20250010653', 'measured_experiment', 'SIBAL cotton–fiberglass fabric', 'lunar', 'sounding_rocket_centrifuge', [4,12,13,16,19,33,42],
             'Simulated lunar gravity, not the lunar surface. Same flight as LUCI-PMMA. Page 19 gives 0.92 mm/s base spread; page 33 rounds to 0.9. Total test count is not inferred from sample count.', rotation_rpm=11, radius_m=1.22, width_cm=5, length_cm=30, flame_base_spread_mm_s=0.92, flame_tip_spread_mm_s=1.1, oxygen_range_pct=[18,20], pressure_description='Normal pressure; no exact per-test value assigned', duration_description='Burn over two and a half minutes (flight experiment)'),
      record('LUCI-PMMA', '20250010653', 'measured_experiment', 'PMMA rod', 'lunar', 'sounding_rocket_centrifuge', [4,12,16,17,20,21,22,36],
             'Same flight as LUCI-SIBAL. Tip spread is approximately linear; base spread is not steady. Oxygen changes during burning, not a constant boundary condition.', diameter_mm=4, rotation_rpm=11, radius_m=1.22, flame_tip_spread_mm_s=1.5, oxygen_range_pct=[14.3,20], pressure_description='Normal pressure; no exact per-test value assigned'),
      record('ICES-WSTF', '20250002114', 'measured_experiment', 'PMMA, P213 tape, cotton, polycarbonate, Nomex Velcro', 'normal', 'ground_1g', [6,8,9],
             'Measured WSTF high-flow tests; limits are not transcribed from plot pixels. Method is under development; not an accepted lunar material standard.', gravity_level_g=1, pressure_kpa=57, sample_width_cm=5.2, sample_length_cm=14),
      record('ICES-GRC', '20250002114', 'measured_experiment', 'PMMA, P213 tape, cotton, polycarbonate, Nomex Velcro', 'lunar', 'drop_tower_centrifuge', [7,8,9],
             'Short-duration GRC centrifuge tests, gravity gradient and Coriolis effects. Not lunar-surface data. Five materials are not five tests.', gravity_level_g=1/6, rotation_rpm=20.4, drop_duration_s=5.2),
      record('ICES-MODEL', '20250002114', 'theoretical_model', 'Thin solid fuels', 'unknown', 'unknown', [4,5,9],
             'Damkohler-number and heat-transfer model. Model parameters are not imported as measured outcomes.'),
      record('FM2-PLAN-2024', '20240015307', 'planned_experiment', 'SIBAL fabric and PMMA', 'lunar', 'lunar_surface', [1],
             'Historical 2024 plan: four samples, 21% O2 at 14.7 psia and 34% at 8.2 psia. Poster includes earlier laboratory work; it does not report completed lunar surface tests. CP-21 and HLS descriptions coexist in this poster.'),
      record('FM2-PLAN-2026', '20260001966', 'planned_experiment', 'Synergy Pro Navy fabric', 'lunar', 'lunar_surface', [5,6,9,10],
             'Revised 2026 concept, separate from 2024 plan. Four planned atmospheres 37/33/29/25% O2 at 8.2 psia. No completed lunar surface test results.'),
      record('LPSC-CENTRIFUGE', '20260001966', 'measured_experiment', 'SIBAL fabric', 'lunar', 'drop_tower_centrifuge', [13,22],
             'Earlier experimental work reproduced in a 2026 presentation; no new test count. Air at 1 atm is the reported study condition.', gravity_level_g=0.165, width_cm=2, flame_base_spread_cm_s=0.11),
      record('LPSC-AIRCRAFT', '20260001966', 'measured_experiment', 'SIBAL fabric', 'lunar', 'parabolic_flight', [21,22],
             'Test 2-29, downward spread for 20 seconds. Title mentions Mars but supplies no measured Mars row here. No new aggregate test count.', gravity_level_g=0.165, width_cm=5, oxygen_pct=21, pressure_atm=1, duration_s=20, flame_base_spread_cm_s=0.086),
      record('FIRE-SAFETY-CONTEXT', '20210021318', 'context_only', 'Spacecraft fire safety', 'unknown', 'unknown', [3,7,13],
             'Historical 2021 capability gaps and roadmap. Dates are historical plans, not current mission schedules.'),
      record('PMMA-2024-UNVERIFIED', 'PMMA-2024', 'context_only', 'PMMA', 'unknown', 'unknown', [],
             'Full journal PDF unavailable. Bibliographic title corroborated in LPSC PDF page 20. No numerical measurements imported; provide the article PDF for review.'),
    ]
    payload = json.dumps(passages, ensure_ascii=False, indent=2).encode('utf-8')
    (ROOT / 'data/extended_passages.json').write_bytes(payload)
    review = dict(schema='2.3.0', reviewed_on='2026-11-14', human_approval='pending', sources=sources, records=records,
                  passages_sha256=hashlib.sha256(payload).hexdigest())
    (ROOT / 'data/extended_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(records)} classified records; {len(passages)} hash-linked pages; no inferred test counts')


if __name__ == '__main__':
    build()
