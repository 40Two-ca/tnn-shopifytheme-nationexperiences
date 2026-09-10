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
        # A template carrying more blocks than the section allows is rejected on
        # sync, and raising max_blocks has to reach the theme before the template
        # that needs it does.
        limit = schema.get('max_blocks')
        count = len(section.get('blocks', {}))
        if limit and count > limit:
            errors.append(
                f"{label}/{section_id}({section_type}): {count} blocks but the section "
                f"allows {limit}; raise max_blocks and push the section first")


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

BUNDLED_FAMILIES = {
    'brand-mosaic': ('tile', 'brand'),
    'partner-logos': ('logo', 'partner'),
    'leadership-grid': ('person', 'team'),
    'story-strand': ('photo', None),
    'feature-tiles': ('tile', None),
    'hero-rotator': ('slide', None),
}


def check_bundled_images():
    """Blocks with no picked image fall back to a bundled one keyed on the
    block's name (see snippets/bundled-image.liquid). Rename the block and the
    logo quietly turns back into a text placeholder, so flag names that have no
    bundled image behind them."""
    # The keys live in the per-family snippets; bundled-image.liquid itself is
    # only a dispatcher, so reading it alone finds five family names and nothing
    # else -- which reported every block on the site as missing its image.
    snippets = glob.glob(f"{ROOT}/snippets/bundled-image-*.liquid")
    if not snippets:
        return
    keys = set()
    for path in snippets:
        keys |= set(re.findall(r"when '([^']+)'", open(path, encoding='utf-8').read()))
    for template_path in sorted(glob.glob(f"{ROOT}/templates/*.json") + glob.glob(f"{ROOT}/sections/*-group.json")):
        label = os.path.relpath(template_path, ROOT).replace(os.sep, '/')
        raw = open(template_path, encoding='utf-8').read()
        document = json.loads(raw[raw.index('{'):])  # skip any /* comment */ header
        for section in document.get('sections', {}).values():
            family = BUNDLED_FAMILIES.get(section.get('type'))
            if not family:
                continue
            block_type, prefix = family
            for block in section.get('blocks', {}).values():
                if block.get('type') != block_type:
                    continue
                values = block.get('settings', {})
                if values.get('image'):
                    continue
                if prefix is None:
                    # story-strand names its bundled photo outright rather than
                    # deriving it from a block name.
                    key = values.get('bundled', '')
                    if key and key not in keys:
                        warnings.append(
                            f"{label}/{section.get('type')}: bundled photo {key!r} does not exist; "
                            f"the frame will fall back to a placeholder")
                    continue
                name = values.get('name', '')
                # Matches Liquid's handleize: apostrophes are dropped, every
                # other run of non-alphanumerics becomes one hyphen. Keep this
                # in step with slug() in build_bundled_images.py.
                handle = name.lower().replace("'", '').replace('’', '')
                handle = re.sub(r'[^a-z0-9]+', '-', handle).strip('-')
                if f"{prefix}-{handle}" not in keys:
                    warnings.append(
                        f"{label}/{section.get('type')}: no bundled image for {name!r} "
                        f"(expected assets/{prefix}-{handle}.*); it will render as text")


check_bundled_images()

# UTF-8 text decoded as Windows-1252 and re-encoded leaves these behind. It
# happened here: a curly apostrophe in the home page's Hockey Fights tile became
# "a<euro>(tm)" and shipped to the live storefront, because nothing looked for it.
MOJIBAKE = ('â€', 'Ã©', 'Ã¨', 'Â ', '�')


def check_mojibake():
    for path in sorted(glob.glob(f"{ROOT}/templates/*.json") + glob.glob(f"{ROOT}/sections/*.json")):
        label = os.path.relpath(path, ROOT).replace(os.sep, '/')
        text = open(path, encoding='utf-8').read()
        for sequence in MOJIBAKE:
            index = text.find(sequence)
            if index != -1:
                errors.append(
                    f"{label}: mis-encoded text near {text[max(0, index - 30):index + 10]!r} "
                    f"-- read the source as UTF-8 rather than the system locale")
                break


check_mojibake()


# Shopify validates every `richtext` setting server-side and rejects the whole
# file if the HTML is not in its allowed subset -- attributes in particular,
# `href` on a link aside. A rejected file is not reported anywhere: the push
# succeeds, GitHub is happy, and the store quietly keeps serving the previous
# version. templates/page.hockey.json sat three commits behind the repo for
# exactly this reason, after `id="..."` was added to three headings to hang
# anchors off. Anything caught here would ship as an invisible no-op.
RICHTEXT_OK_ATTRS = ('href', 'target', 'title', 'rel')


def check_richtext_attrs():
    pattern = re.compile(r'<(\w+)((?:\s+[\w:-]+="[^"]*")+)\s*/?>')
    attr = re.compile(r'([\w:-]+)="')
    for path in sorted(glob.glob(f"{ROOT}/templates/*.json") + glob.glob(f"{ROOT}/sections/*.json")):
        label = os.path.relpath(path, ROOT).replace(os.sep, '/')
        raw = open(path, encoding='utf-8').read()
        try:
            doc = json.loads(raw[raw.index('{'):])
        except ValueError:
            continue

        def walk(node, trail):
            for key, block in (node.get('blocks') or {}).items():
                for name, value in (block.get('settings') or {}).items():
                    if not isinstance(value, str) or '<' not in value:
                        continue
                    for tag, attrs in pattern.findall(value):
                        bad = [a for a in attr.findall(attrs) if a not in RICHTEXT_OK_ATTRS]
                        if bad:
                            errors.append(
                                f"{label}/{'/'.join(trail + [key])}: setting '{name}' puts "
                                f"{', '.join(bad)} on <{tag}>; Shopify rejects the whole file "
                                f"and keeps serving the last good version, silently")
                walk(block, trail + [key])

        for key, section in doc.get('sections', {}).items():
            walk(section, [key])


check_richtext_attrs()

settings_schema = json.load(open(f"{ROOT}/config/settings_schema.json", encoding='utf-8'))
all_settings = [s for group in settings_schema for s in group.get('settings', [])]
current = json.load(open(f"{ROOT}/config/settings_data.json", encoding='utf-8'))['current']
check_settings("config/settings_data.json", all_settings, {k: v for k, v in current.items() if k != 'color_palette'})

for warning in warnings:
    print("warning:", warning)
print("\n".join(errors) if errors else "NO ERRORS")
print(f"-- {len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
