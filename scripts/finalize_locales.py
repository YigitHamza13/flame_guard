"""Move the legacy label catalog to locale JSON files."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'src/labels.py'
tree=ast.parse(path.read_text(encoding='utf-8'))
pairs={}
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PAIRS' for x in n.targets):pairs=ast.literal_eval(n.value)
extra={
 'measured_experiment':('Measured experiment','Ölçülmüş deney'), 'planned_experiment':('Planned experiment','Planlanan deney'),
 'theoretical_model':('Theoretical model','Teorik model'),'context_only':('Context only','Yalnızca bağlam'),
 'mission_assumption':('Mission assumption','Görev varsayımı'),
 'conference_presentation':('Conference presentation','Konferans sunumu'),'conference_paper':('Conference paper','Konferans bildirisi'),
 'poster':('Poster','Poster'),'journal_article':('Journal article','Dergi makalesi'),
 'normal':('Normal gravity','Normal yerçekimi'),'lunar':('Lunar partial gravity','Ay kısmi yerçekimi'),
 'unknown':('Unknown','Bilinmiyor'),'Earth 1 g':('Earth 1 g','Dünya 1 g'),'Lunar ≈0.16 g':('Lunar ≈0.16 g','Ay ≈0,16 g'),
 'Microgravity':('Microgravity','Mikro yerçekimi'),'No data':('No data','Veri yok'),
 'Flame spread reported':('Flame spread reported','Alev yayılımı raporlanmış'),'Mixed observations':('Mixed observations','Karma gözlemler'),
 'full_text_read':('Full text inspected','Tam metin incelendi'),'abstract_only':('Full text unavailable','Tam metne erişilemedi')}
for i,code in enumerate(['en','tr']):
    file=ROOT/'locales'/f'{code}.json';d=json.loads(file.read_text(encoding='utf-8'))
    for key,pair in pairs.items():d['label:'+key]=pair[i]
    for key,pair in extra.items():d[key]=pair[i]
    file.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if pairs:
    path.write_text('''"""Machine-value display labels from the shared JSON catalogs."""
from src.i18n import t, catalog

def label(value):
    key = str(value)
    choices = catalog('en')
    if 'label:' + key in choices:
        return t('label:' + key)
    if 'label:' + key.casefold() in choices:
        return t('label:' + key.casefold())
    return t(key)
''',encoding='utf-8')
css=ROOT/'assets/style.css'
text=css.read_text(encoding='utf-8')
if '.flame-illustration' not in text:
    text+='\n.flame-illustration{width:160px;display:flex;justify-content:center}.flame-illustration svg{transform-origin:center bottom;animation:flame-breathe 3s ease-in-out infinite}@keyframes flame-breathe{50%{transform:scaleX(.96) scaleY(1.025)}}@media(prefers-reduced-motion:reduce){.flame-illustration svg{animation:none}}\n'
    css.write_text(text,encoding='utf-8')
