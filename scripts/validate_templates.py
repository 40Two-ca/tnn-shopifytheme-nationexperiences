"""Validate JSON templates and section groups against section/block schemas.

Shopify's GitHub theme sync rejects JSON files whose values fall outside a
range setting's min/max/step, and it only reports the first problem per file.
Run this before pushing:

    python scripts/validate_templates.py
"""
import json, re, glob, os, sys
import pathlib
ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
def load_schema(path):
    s = open(path, encoding='utf-8').read()
    m = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', s, re.S)
    return json.loads(m.group(1)) if m else None
section_schemas = {os.path.basename(p)[:-7]: load_schema(p) for p in glob.glob(f"{ROOT}/sections/*.liquid")}
block_schemas = {os.path.basename(p)[:-7]: load_schema(p) for p in glob.glob(f"{ROOT}/blocks/*.liquid")}
errors = []
def check_settings(where, schema_settings, values):
    byid = {s.get('id'): s for s in schema_settings if s.get('id')}
    for k, v in values.items():
        st = byid.get(k)
        if not st:
            errors.append(f"{where}: unknown setting '{k}'"); continue
        t = st['type']
        if t == 'range':
            if not isinstance(v, (int, float)): errors.append(f"{where}: '{k}' not numeric ({v!r})"); continue
            mn, mx, step = st['min'], st['max'], st.get('step', 1)
            if v < mn or v > mx: errors.append(f"{where}: '{k}'={v} outside [{mn},{mx}]")
            elif round((v - mn) / step, 6) % 1 != 0: errors.append(f"{where}: '{k}'={v} not on step {step} from {mn}")
        elif t == 'select':
            opts = [o['value'] for o in st.get('options', [])]
            if v not in opts: errors.append(f"{where}: '{k}'={v!r} not in options {opts}")
        elif t == 'checkbox' and not isinstance(v, bool):
            errors.append(f"{where}: '{k}' should be boolean ({v!r})")
def check_blocks(where, blocks, order, local_block_defs):
    for bid, b in blocks.items():
        btype = b['type']
        if btype in local_block_defs:
            bschema = {'settings': local_block_defs[btype].get('settings', []), 'blocks': []}
        elif btype in block_schemas:
            bschema = block_schemas[btype]
        else:
            errors.append(f"{where}/{bid}: unknown block type '{btype}'"); continue
        check_settings(f"{where}/{bid}({btype})", bschema.get('settings', []), b.get('settings', {}))
        if b.get('blocks'):
            check_blocks(f"{where}/{bid}", b['blocks'], b.get('block_order', []), {})
def check_file(path):
    d = json.load(open(path, encoding='utf-8'))
    for sid, sec in d['sections'].items():
        stype = sec['type']
        schema = section_schemas.get(stype)
        if not schema: errors.append(f"{path}/{sid}: unknown section type '{stype}'"); continue
        check_settings(f"{path}/{sid}({stype})", schema.get('settings', []), sec.get('settings', {}))
        local = {b['type']: b for b in schema.get('blocks', []) if b.get('settings') is not None}
        check_blocks(f"{path}/{sid}", sec.get('blocks', {}), sec.get('block_order', []), local)
for f in ['templates/index.json','templates/collection.json','templates/product.json','sections/header-group.json','sections/footer-group.json']:
    check_file(f"{ROOT}/{f}")
# settings_data vs settings_schema
ss = json.load(open(f"{ROOT}/config/settings_schema.json", encoding='utf-8'))
all_settings = [s for g in ss for s in g.get('settings', [])]
check_settings("config/settings_data.json", all_settings, {k: v for k, v in json.load(open(f"{ROOT}/config/settings_data.json", encoding='utf-8'))['current'].items() if k != 'color_palette'})
print("\n".join(errors) if errors else "NO ERRORS")
print(f"-- {len(errors)} issue(s)")
