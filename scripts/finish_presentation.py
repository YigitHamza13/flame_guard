"""Apply bounded cosmetic replacements and explicit widget placeholders."""
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
css=ROOT/'assets/style.css'
text=css.read_text(encoding='utf-8').replace('--accent:#7cbcff','--accent:#ffb36b').replace('--observed:#7ad7bb','--observed:#e3b787')
text=text.replace('background:#1b3553!important','background:#3c281c!important').replace('border-color:#547ba5;box-shadow','border-color:#a56e40;box-shadow')
text += '\n.method-toc{display:flex;gap:12px;flex-wrap:wrap;font-size:13px}.method-toc a{display:block;padding:8px}.st-key-overview_actions .stButton button{min-height:48px} code{font-family:PlexMono,monospace;font-size:13px}\n@media(min-width:1280px){[data-testid="stMainBlockContainer"]:has(.method-toc){padding-right:224px}.method-toc{position:fixed;right:24px;top:140px;width:180px;display:block;border-left:1px solid var(--line);padding-left:12px}}\n'
css.write_text(text,encoding='utf-8')
path=ROOT/'src/pages.py'
text=path.read_text(encoding='utf-8')
tree=ast.parse(text)
lines=text.splitlines(keepends=True); offsets=[0]
for line in lines: offsets.append(offsets[-1]+len(line.encode('utf-8')))
edits=[]
for n in ast.walk(tree):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('multiselect','text_input') and not any(k.arg=='placeholder' for k in n.keywords):
        value="t('Choose specimens', 'Numune seçin')" if n.func.attr=='multiselect' else "t('Type to search or enter context', 'Arayın veya bağlam girin')"
        edits.append((offsets[n.end_lineno-1]+n.end_col_offset-1,(', placeholder='+value).encode()))
raw=text.encode('utf-8')
for pos,value in sorted(edits,reverse=True):raw=raw[:pos]+value+raw[pos:]
path.write_bytes(raw)
