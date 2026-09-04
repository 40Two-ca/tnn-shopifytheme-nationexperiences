"""Pre-push checks for the theme.

Validates JSON templates and section groups against section/block schemas, and
checks Liquid files for multi-line tags inside a {% liquid %} block.

Shopify's GitHub theme sync rejects JSON files whose values fall outside a
range setting's min/max/step, and it only reports the first problem per file.
Select values that are not in the schema's options are reported as warnings
(Shopify accepts them, Horizon itself ships one in cart.json).

Run this before pushing:

    python scripts/validate_templates.py

Exit code is 1 when there are errors.
"""
import glob
import json
import os
import pathlib
import re
import sys

ROOT = str(pathlib.Path(__file__).resolve().parent.parent)


def load_schema(path):
    source = open(path, encoding='utf-8').read()
    match = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', source, re.S)
    return json.loads(match.group(1)) if match else None


section_schemas = {os.path.basename(p)[:-7]: load_schema(p) for p in glob.glob(f"{ROOT}/sections/*.liquid")}
block_schemas = {os.path.basename(p)[:-7]: load_schema(p) for p in glob.glob(f"{ROOT}/blocks/*.liquid")}
errors = []
warnings = []


def check_settings(where, schema_settings, values):
    by_id = {s.get('id'): s for s in schema_settings if s.get('id')}
    for key, value in values.items():
        setting = by_id.get(key)
        if not setting:
            errors.append(f"{where}: unknown setting '{key}'")
            continue
        kind = setting['type']
        if kind == 'range':
            if not isinstance(value, (int, float)):
                errors.append(f"{where}: '{key}' not numeric ({value!r})")
                continue
            low, high, step = setting['min'], setting['max'], setting.get('step', 1)
            if value < low or value > high:
                errors.append(f"{where}: '{key}'={value} outside [{low},{high}]")
            elif round((value - low) / step, 6) % 1 != 0:
                errors.append(f"{where}: '{key}'={value} not on step {step} from {low}")
        elif kind == 'select':
            options = [o['value'] for o in setting.get('options', [])]
            if value not in options:
                warnings.append(f"{where}: '{key}'={value!r} not in options {options}")
        elif kind == 'checkbox' and not isinstance(value, bool):
            errors.append(f"{where}: '{key}' should be boolean ({value!r})")


def check_blocks(where, blocks, local_block_defs):
    for block_id, block in blocks.items():
        block_type = block['type']
        if block_type in local_block_defs:
            schema = {'settings': local_block_defs[block_type].get('settings', [])}
        elif block_type in block_schemas:
            schema = block_schemas[block_type]
        else:
            errors.append(f"{where}/{block_id}: unknown block type '{block_type}'")
            continue
        check_settings(f"{where}/{block_id}({block_type})", schema.get('settings', []), block.get('settings', {}))
        if block.get('blocks'):
            check_blocks(f"{where}/{block_id}", block['blocks'], {})


def check_file(path):
    raw = open(path, encoding='utf-8').read()
    data = json.loads(raw[raw.index('{'):])  # templates may start with a /* comment */ header
    label = os.path.relpath(path, ROOT).replace(os.sep, '/')
    for section_id, section in data['sections'].items():
        section_type = section['type']
        schema = section_schemas.get(section_type)
        if not schema:
            errors.append(f"{label}/{section_id}: unknown section type '{section_type}'")
            continue
        check_settings(f"{label}/{section_id}({section_type})", schema.get('settings', []), section.get('settings', {}))
        local = {b['type']: b for b in schema.get('blocks', []) if b.get('settings') is not None}
        check_blocks(f"{label}/{section_id}", section.get('blocks', {}), local)


for path in sorted(glob.glob(f"{ROOT}/templates/*.json") + glob.glob(f"{ROOT}/sections/*.json")):
    check_file(path)


LIQUID_BLOCK = re.compile(r'{%-?\s*liquid\b(.*?)-?%}', re.S)


def check_liquid_tags(path):
    """Inside a {% liquid %} block every line is its own tag, so a tag whose
    arguments run onto the next line is a syntax error there. Shopify rejects
    the file on sync ("Unknown tag 'product'"); theme check does not catch it."""
    source = open(path, encoding='utf-8').read()
    label = os.path.relpath(path, ROOT).replace(os.sep, '/')
    for match in LIQUID_BLOCK.finditer(source):
        first_line = source[:match.start()].count(chr(10)) + 1
        for offset, line in enumerate(match.group(1).split(chr(10))):
            stripped = line.split('#')[0].strip()
            if stripped.endswith(','):
                errors.append(
                    f"{label}:{first_line + offset}: tag arguments continue onto the "
                    f"next line inside a liquid tag ({stripped!r}); move the tag out "
                    f"of the liquid block")


for folder in ('sections', 'blocks', 'snippets', 'layout'):
    for liquid_path in sorted(glob.glob(f"{ROOT}/{folder}/*.liquid")):
        check_liquid_tags(liquid_path)

settings_schema = json.load(open(f"{ROOT}/config/settings_schema.json", encoding='utf-8'))
all_settings = [s for group in settings_schema for s in group.get('settings', [])]
current = json.load(open(f"{ROOT}/config/settings_data.json", encoding='utf-8'))['current']
check_settings("config/settings_data.json", all_settings, {k: v for k, v in current.items() if k != 'color_palette'})

for warning in warnings:
    print("warning:", warning)
print("\n".join(errors) if errors else "NO ERRORS")
print(f"-- {len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
