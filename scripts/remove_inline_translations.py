"""Finish migration: runtime page specifications retain only English message keys."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
en=json.loads((ROOT/'locales/en.json').read_text(encoding='utf-8'))
tr=json.loads((ROOT/'locales/tr.json').read_text(encoding='utf-8'))
reverse={value:en[key] for key,value in tr.items() if key in en and value!=en[key] and not key.startswith('label:') and key!='_language'}
for path in [ROOT/'app.py',ROOT/'src/pages.py',ROOT/'src/presentation.py',ROOT/'src/ui.py',ROOT/'src/charts.py']:
    source=path.read_text(encoding='utf-8');tree=ast.parse(source)
    lines=source.splitlines(keepends=True);offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line.encode('utf-8')))
    edits=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value in reverse:
            edits.append((offsets[n.lineno-1]+n.col_offset,offsets[n.end_lineno-1]+n.end_col_offset,repr(reverse[n.value]).encode('utf-8')))
    raw=source.encode('utf-8')
    for start,end,value in sorted(edits,reverse=True):raw=raw[:start]+value+raw[end:]
    # Translation values now live only in JSON. Existing specs retain their shape.
    text=raw.decode('utf-8')
    text=text.replace('t(en, tr)','t(en)').replace('t(en,tr)','t(en)').replace('t(body_en, body_tr)','t(body_en)')
    text=text.replace('t(*pair)','t(pair[0])').replace("t(*types[row['evidence_type']])","t(row['evidence_type'])")
    text=text.replace('t(*notices.get(answer["notice"], notices["unanswered"]))','t(notices.get(answer["notice"], notices["unanswered"])[0])')
    path.write_text(text,encoding='utf-8')
# Clarify the old collection scope without retaining an obsolete global absence claim.
key=next(k for k in en if k.startswith('Oxygen and pressure inputs are user assumptions.'))
en[key]='Oxygen and pressure inputs are user assumptions. The original compilation comparison uses numerical equality and reported gravity classes. Additional measured studies list their reported g separately. Unknown g remains blank. No validated mission risk model or acceptance tolerance is defined.'
tr[key]='Oksijen ve basınç girdileri kullanıcı varsayımlarıdır. Özgün derleme karşılaştırması sayısal eşitliği ve raporlanan yerçekimi sınıflarını kullanır. Ek ölçülmüş çalışmalar raporlanan g değerini ayrıca gösterir. Bilinmeyen g boş kalır. Doğrulanmış görev risk modeli veya kabul toleransı tanımlı değildir.'
extra={
 'sounding_rocket_centrifuge':('Sounding rocket centrifuge','Sonda roketi santrifüjü'),
 'drop_tower_centrifuge':('Drop tower centrifuge','Düşme kulesi santrifüjü'),
 'parabolic_flight':('Parabolic flight','Parabolik uçuş'),'ground_1g':('Ground 1 g','Yer laboratuvarı 1 g'),
 'lunar_surface':('Lunar surface','Ay yüzeyi'),
 'rotation_rpm':('Rotation (rpm)','Dönüş (dev/dk)'), 'radius_m':('Radius (m)','Yarıçap (m)'),
 'width_cm':('Width (cm)','Genişlik (cm)'), 'length_cm':('Length (cm)','Uzunluk (cm)'),
 'diameter_mm':('Diameter (mm)','Çap (mm)'), 'flame_base_spread_mm_s':('Flame base spread (mm/s)','Alev tabanı yayılımı (mm/s)'),
 'flame_tip_spread_mm_s':('Flame tip spread (mm/s)','Alev ucu yayılımı (mm/s)'),
 'oxygen_range_pct':('Reported O₂ range (%)','Raporlanan O₂ aralığı (%)'),
 'pressure_description':('Pressure · source description','Basınç · kaynak açıklaması'),
 'duration_description':('Duration · source description','Süre · kaynak açıklaması'),
 'pressure_kpa':('Pressure (kPa)','Basınç (kPa)'), 'sample_width_cm':('Sample width (cm)','Numune genişliği (cm)'),
 'sample_length_cm':('Sample length (cm)','Numune uzunluğu (cm)'), 'drop_duration_s':('Drop duration (s)','Düşme süresi (s)'),
 'duration_s':('Duration (s)','Süre (s)'), 'flame_base_spread_cm_s':('Flame base spread (cm/s)','Alev tabanı yayılımı (cm/s)'),
 'oxygen_pct':('O₂ (%)','O₂ (%)'), 'pressure_atm':('Pressure (atm)','Basınç (atm)')}
for key,(a,b) in extra.items():en[key],tr[key]=a,b
for code,values in [('en',en),('tr',tr)]:
    (ROOT/f'locales/{code}.json').write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
