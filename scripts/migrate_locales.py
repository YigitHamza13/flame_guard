"""One-time source migration; retained for reproducible translation extraction."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def migrate():
    folder = ROOT / 'locales'
    folder.mkdir(exist_ok=True)
    catalogs = {code: json.loads((folder / f'{code}.json').read_text(encoding='utf-8')) if (folder / f'{code}.json').exists() else {} for code in ('en','tr')}
    catalogs['en']['_language'], catalogs['tr']['_language'] = 'English', 'Türkçe'
    def add(en, tr):
        catalogs['en'][en], catalogs['tr'][en] = en, tr
    for path in [ROOT/'app.py', *sorted((ROOT/'src').glob('*.py'))]:
        if path.name == 'i18n.py':
            continue
        source = path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        edits = []
        lines = source.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line.encode('utf-8')))
        for node in ast.walk(tree):
            # Runtime page specs, section copy, labels and example question pairs.
            if isinstance(node, (ast.Tuple, ast.List)):
                for a,b in zip(node.elts,node.elts[1:]):
                    if isinstance(a,ast.Constant) and isinstance(a.value,str) and isinstance(b,ast.Constant) and isinstance(b.value,str):
                        if any(c in b.value for c in 'çğıöşüÇĞİÖŞÜ'):
                            add(a.value,b.value)
            if not isinstance(node, ast.Call) or not isinstance(node.func,ast.Name) or node.func.id != 't' or len(node.args) != 2:
                continue
            a,b = node.args
            if isinstance(a,ast.Constant) and isinstance(b,ast.Constant) and isinstance(a.value,str) and isinstance(b.value,str):
                add(a.value,b.value)
                keywords = ''.join(', '+ast.unparse(k) for k in node.keywords)
                replacement = f't({a.value!r}{keywords})'
            elif isinstance(a,ast.JoinedStr) and isinstance(b,ast.JoinedStr):
                expressions = []
                def template(n):
                    text = ''
                    for part in n.values:
                        if isinstance(part,ast.Constant):
                            text += part.value.replace('{','{{').replace('}','}}')
                        elif isinstance(part,ast.FormattedValue):
                            expr = ast.unparse(part.value)
                            if expr not in expressions: expressions.append(expr)
                            text += '{v' + str(expressions.index(expr)) + '}'
                    return text
                en,tr = template(a),template(b)
                add(en,tr)
                replacement = 't(' + repr(en) + ', ' + ', '.join(f'v{i}={expr}' for i,expr in enumerate(expressions)) + ')'
            else:
                continue
            edits.append((offsets[node.lineno-1]+node.col_offset, offsets[node.end_lineno-1]+node.end_col_offset, replacement.encode('utf-8')))
        raw = source.encode('utf-8')
        for start,end,replacement in sorted(edits,reverse=True):
            raw = raw[:start]+replacement+raw[end:]
        path.write_bytes(raw)
    for code,values in catalogs.items():
        (folder/f'{code}.json').write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Locale keys:',len(catalogs['en']))

if __name__ == '__main__': migrate()
