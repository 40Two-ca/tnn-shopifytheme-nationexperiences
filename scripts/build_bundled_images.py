"""Bundle the network's brand imagery into the theme and generate the resolver snippet.

The Nation Network's logos, advertiser marks and staff portraits live in the old
marketing-site repo (thenationnetwork-www). Shopify's `image_picker` settings can
only point at Shopify Files, which nobody has uploaded to this development store
yet, so the theme ships the images in `assets/` and resolves them by name through
`snippets/bundled-image.liquid` until real ones are picked in the editor. That is
the same arrangement `snippets/stock-image.liquid` uses for the Unsplash photos.

Run it from the repo root with the source repo beside this one:

    python scripts/build_bundled_images.py
    python scripts/build_bundled_images.py --source "E:/Github Repos/thenationnetwork-www"

It rewrites `assets/brand-*`, `assets/partner-*`, `assets/team-*`, the four
`assets/tnn-*` identity files and `snippets/bundled-image.liquid`. Block content
for the templates is written to `--blocks-out` if asked for; the templates
themselves are hand-maintained, because merchants edit them in the theme editor.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install pillow")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SOURCE = os.path.join(os.path.dirname(REPO), "thenationnetwork-www")

# Logo art has to read against the tile colour it sits on. The `_new.png` nation
# marks are dark-on-transparent and vanish on their own dark brand colour, so
# these four take a different file than brands.ts names. Checked on a contact
# sheet of every logo over its tile colour.
LOGO_OVERRIDES = {
    "OilersNation": "assets/images/logos/sites/oilersnation.svg",
    "FlamesNation": "assets/images/logos/sites/flamesnation.svg",
    "TheLeafsNation": "assets/images/logos/sites/theleafsnation.svg",
    "CanucksArmy": "assets/images/logos/sites/canucksarmy.png",
}

# brands.ts carries two entries named after their logo file rather than the show.
NAME_FIXES = {
    "TSH Primary": "Tri-State Hockey",
    "Primary Blk": "Off The Roster",
}

# Dark artwork on a near-black tile; no colour combination makes it legible.
EXCLUDE_BRANDS = {"Warmies"}

# Front-page leadership, in the order the old site used (frontPageOrder).
TEAM_TITLE_FIXES = {
    "Amil Delic": "Head of Original Production - Audio Video, Producer",
}

# On-air talent for the brand pages' host grids. Only these four are here
# because only these four clear both bars: they front a show the Daily Faceoff
# page actually covers, and they have a real portrait. Of 93 staff entries in
# staff.ts, 56 point at placeholder.jpg -- including Johnny Lazarus and Colby
# Cohen, who host Morning Cuppa Hockey on that same page.
HOST_PORTRAITS = [
    "Frank Seravalli",
    "Tyler Yaremchuk",
    "Jason Gregor",
    "Brock Seguin",
]

LOGO_MAX = (480, 480)
PARTNER_MAX = (520, 320)
PORTRAIT = 560
PHOTO_MAX = (1000, 1000)
SCREENSHOT_MAX = (780, 780)
# Hero photography goes full-bleed, so it needs more pixels than a tile -- but
# six of them load on one page, so not many more.
HERO_MAX = (1600, 1600)

# The six the marketing site rotated behind its headline.
HERO_PHOTOS = [
    ("hero-studio-two", "assets/images/design/herospinner/1.jpg",
     "Two hosts recording in the studio under neon signs"),
    ("hero-fans-vegas", "assets/images/design/herospinner/2.jpg",
     "A large group of fans with an OilersNation flag outside T-Mobile Arena"),
    ("hero-cap", "assets/images/design/herospinner/3.jpg",
     "A fan laughing in an OilersNation cap against a brick wall"),
    ("hero-studio-three", "assets/images/design/herospinner/4.jpg",
     "Three hosts recording a show together in the studio"),
    ("hero-sekeres-price", "assets/images/design/herospinner/5.jpg",
     "The Sekeres & Price hosts at their desk on set"),
    ("hero-the-sheet-live", "assets/images/design/herospinner/6.jpg",
     "The Sheet recorded live on stage in front of an audience"),
    # The only usable photograph in the old repo's `hero/` folder -- the other
    # three there are Pexels stock, which is no better than what the theme
    # already ships.
    ("nation-hoodie", "assets/images/hero/hero.jpg",
     "Someone wearing a Nation hoodie, shot in black and white"),
]

# Beyond The Game runs four strands, each beside a small grid of photos. The
# source folders hold 36 shots between them; these are the picks and the alt text
# after looking through all of them on a contact sheet. Giving Back gets two
# rather than four: of its four photos one is a dog with no visible connection to
# the story, so it is left out until the client supplies more.
PAGE_PHOTOS = [
    ("travel-1", "assets/images/beyondthegame/travel/2.jpg",
     "Fans with an OilersNation flag outside the arena before a road game"),
    ("travel-2", "assets/images/beyondthegame/travel/9.jpg",
     "Four fans with hockey sticks on a frozen mountain lake"),
    ("travel-3", "assets/images/beyondthegame/travel/11.jpg",
     "A Nation Vacation group outside Climate Pledge Arena"),
    ("travel-4", "assets/images/beyondthegame/travel/5.jpg",
     "Fans in Oilers jerseys gathered outside their Las Vegas hotel"),
    ("events-1", "assets/images/beyondthegame/events/1.jpg",
     "A host with a microphone in front of a watch-party crowd"),
    ("events-2", "assets/images/beyondthegame/events/6.jpg",
     "Four hosts recording a live show in front of a mural"),
    ("events-3", "assets/images/beyondthegame/events/9.jpg",
     "Fans in Oilers jerseys at a Nation Network event"),
    ("events-4", "assets/images/beyondthegame/events/12.jpg",
     "The Hello & Welcome show recorded in front of an audience"),
    ("gear-1", "assets/images/beyondthegame/gear/3.png", "A fan wearing a Nation hoodie"),
    ("gear-2", "assets/images/beyondthegame/gear/5.jpg", "An OilersNation cap worn by the water"),
    ("gear-3", "assets/images/beyondthegame/gear/6.jpg", "A Nation cap and tee against a brick wall"),
    ("gear-4", "assets/images/beyondthegame/gear/1.png", "A CanucksArmy snapback cap"),
    ("giving-1", "assets/images/beyondthegame/giving/2.jpg",
     "Two volunteers at a Free Play for Kids fundraiser"),
    ("giving-2", "assets/images/beyondthegame/giving/4.jpg",
     "A youth ball team lined up on the diamond at RE/MAX Field"),
]

# Site and show screenshots in their device frames, for the brand pages.
PAGE_SCREENSHOTS = [
    ("site-oilersnation", "assets/images/design/laptopwidget/laptop/oilers-nation.png", "OilersNation on a laptop"),
    ("site-canucksarmy", "assets/images/design/laptopwidget/cellphone/ca-mobile.png", "CanucksArmy on a phone"),
    ("site-theleafsnation", "assets/images/design/laptopwidget/cellphone/tln-mobile.png", "TheLeafsNation on a phone"),
    ("site-flamesnation", "assets/images/design/laptopwidget/laptop/fn-laptop.png", "FlamesNation on a laptop"),
    ("show-thesheet", "assets/images/design/laptopwidget/laptop/thesheet-laptop.png", "The Sheet on a laptop"),
    ("show-hello-and-welcome", "assets/images/design/laptopwidget/cellphone/hellowandwelcome-cellphone.png", "Hello & Welcome on a phone"),
    ("show-barnburner", "assets/images/design/laptopwidget/laptop/barnburner-laptop.png", "Barn Burner on a laptop"),
    ("show-oilersnation-everyday", "assets/images/design/laptopwidget/cellphone/oilers-nation-everyday.png", "OilersNation Everyday on a phone"),
    ("social-oilersnation-x", "assets/images/design/laptopwidget/laptop/on-twitter.png", "OilersNation on X"),
    ("social-oilersnation-tiktok", "assets/images/design/laptopwidget/cellphone/oilers-nation-tiktok.png", "OilersNation on TikTok"),
    ("social-oilersnation-facebook", "assets/images/design/laptopwidget/laptop/oilers-nation-facebook.png", "OilersNation on Facebook"),
    ("site-dailyfaceoff", "assets/images/design/laptopwidget/laptop/dfo-site.png", "dailyfaceoff.com on a laptop"),
    ("site-dailyfaceoff-mobile", "assets/images/design/laptopwidget/cellphone/dfo-site.png", "dailyfaceoff.com on a phone"),
    ("site-hockeyfights", "assets/images/design/laptopwidget/laptop/hockeyfights.png", "hockeyfights.com on a laptop"),
    ("site-hockeyfights-mobile", "assets/images/design/laptopwidget/cellphone/hockeyfights.png", "hockeyfights.com on a phone"),
    ("show-dfo-live", "assets/images/design/laptopwidget/laptop/dfo-live.png", "Daily Faceoff Live on a laptop"),
    ("show-dfo-live-mobile", "assets/images/design/laptopwidget/cellphone/dfo-live.png", "Daily Faceoff Live on a phone"),
    ("show-dfo-rundown", "assets/images/design/laptopwidget/laptop/dfo-rundown.png", "The DFO Rundown on a laptop"),
    ("show-dfo-rundown-mobile", "assets/images/design/laptopwidget/cellphone/dfo-rundown.png", "The DFO Rundown on a phone"),
    ("show-frankly-speaking", "assets/images/design/laptopwidget/laptop/frankly-speaking.png", "Frankly Speaking on a laptop"),
    ("show-frankly-speaking-mobile", "assets/images/design/laptopwidget/cellphone/frankly-speaking.png", "Frankly Speaking on a phone"),
    ("show-dfo-fantasy", "assets/images/design/laptopwidget/laptop/dfo-fantasy.png", "The DFO Fantasy Podcast on a laptop"),
    ("show-dfo-fantasy-mobile", "assets/images/design/laptopwidget/cellphone/dfo-fantasy.png", "The DFO Fantasy Podcast on a phone"),
    ("show-morning-cuppa-hockey", "assets/images/design/laptopwidget/laptop/morning-cuppa-hockey.png", "Morning Cuppa Hockey on a laptop"),
    ("show-morning-cuppa-hockey-mobile", "assets/images/design/laptopwidget/cellphone/morning-cuppa-hockey.png", "Morning Cuppa Hockey on a phone"),
    # Named ca-twitter-laptop.png in the source, but the screenshot is the
    # Instagram profile. Checked rather than trusted.
    ("social-canucksarmy-instagram", "assets/images/design/laptopwidget/laptop/ca-twitter-laptop.png",
     "The CanucksArmy Instagram profile"),
]


def slug(text: str) -> str:
    """Reproduce Liquid's `handleize`, which resolves these keys at render time.

    Apostrophes are **dropped**, not turned into a separator: "Wendy's" becomes
    wendys and "Wanye's World" wanyes-world. Every other run of
    non-alphanumerics collapses to a single hyphen, so "Hello & Welcome" is
    hello-welcome.

    This was wrong in the first version -- it hyphenated the apostrophe, which
    produced keys the theme never asked for, and both affected tiles rendered as
    text on the live home page. Checking `handleize` against the real storefront
    is the only way to settle it; the validator re-implements this same rule, so
    it agreed with the mistake rather than catching it.
    """
    text = text.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def read(path: str) -> str:
    return io.open(path, encoding="utf-8", errors="ignore").read()


def field(block: str, key: str) -> str:
    m = re.search(r'\b%s:\s*(?:"([^"]*)"|([^,\n]+))' % key, block)
    if not m:
        return ""
    return (m.group(1) if m.group(1) is not None else m.group(2)).strip().rstrip(",")


def imports_of(source: str, path: str) -> dict:
    return {
        name: "assets/" + rel
        for name, rel in re.findall(
            r'import\s+(\w+)\s+from\s+"@/assets/(images/[^"]+)"', read(os.path.join(source, path))
        )
    }


def objects_of(text: str, marker: str):
    body = text[text.index(marker):]
    return re.findall(r"\{([^{}]*)\}", body, re.S)


def parse_brands(source: str) -> list:
    text = read(os.path.join(source, "assets/config/brands.ts"))
    imports = imports_of(source, "assets/config/brands.ts")
    # Seven logo identifiers are used in brands.ts but never imported: the repo
    # was left mid-edit. They name their files unambiguously.
    imports.update({
        "sundayLeaguePunditsLogo": "assets/images/logos/podcasts/sunday-league-pundits.svg",
        "kickedBackLogo": "assets/images/logos/podcasts/kicked-back.svg",
        "puckPooliesLogo": "assets/images/logos/podcasts/puck-poolies.png",
        "wanyesWorldLogo": "assets/images/logos/podcasts/wanyes-world.svg",
        "startingGoaliesShowLogo": "assets/images/logos/podcasts/starting-goalies-bet-365.png",
        "kevinKariusShowLogo": "assets/images/logos/podcasts/kevi-karius-show.svg",
        "slanginTheBizkitLogo": "assets/images/logos/podcasts/slangin-the-bizkit.jpeg",
    })
    rows = []
    for block in objects_of(text, "export const brands"):
        name = field(block, "name")
        if not name or name in EXCLUDE_BRANDS:
            continue
        rel = LOGO_OVERRIDES.get(name) or imports.get(field(block, "logo"), "")
        if not rel or not os.path.exists(os.path.join(source, rel)):
            print("  ! no logo file for %s" % name)
            continue
        rows.append({
            "name": NAME_FIXES.get(name, name),
            "colour": field(block, "primaryColor") or "#ffffff",
            "url": field(block, "url"),
            "source": rel,
        })
    return rows


def parse_advertisers(source: str) -> list:
    text = read(os.path.join(source, "assets/config/advertisers.ts"))
    imports = imports_of(source, "assets/config/advertisers.ts")
    rows = []
    for block in objects_of(text, "export const advertisers"):
        name = field(block, "name")
        rel = imports.get(field(block, "logo"), "")
        if name and rel and os.path.exists(os.path.join(source, rel)):
            rows.append({"name": name, "source": rel})
    return rows


def parse_hosts(source: str) -> list:
    """The named on-air talent, with whatever portrait staff.ts gives them."""
    text = read(os.path.join(source, "assets/config/staff.ts"))
    imports = imports_of(source, "assets/config/staff.ts")
    wanted = {name: None for name in HOST_PORTRAITS}
    for block in objects_of(text, "export const staff"):
        name = field(block, "name")
        if name in wanted:
            rel = imports.get(field(block, "image"), "")
            if rel.endswith("placeholder.jpg"):
                print("  ! %s has no portrait, only placeholder.jpg" % name)
                continue
            wanted[name] = {"name": name, "title": field(block, "title"), "source": rel}
    missing = [name for name, row in wanted.items() if not row]
    if missing:
        print("  ! no usable portrait for: %s" % ", ".join(missing))
    return [row for row in wanted.values() if row]


def parse_team(source: str) -> list:
    text = read(os.path.join(source, "assets/config/staff.ts"))
    imports = imports_of(source, "assets/config/staff.ts")
    rows = []
    for block in objects_of(text, "export const staff"):
        order = field(block, "frontPageOrder")
        name = field(block, "name")
        if not order or not name:
            continue
        rel = imports.get(field(block, "image"), "")
        if not rel or not os.path.exists(os.path.join(source, rel)):
            print("  ! no portrait for %s" % name)
            continue
        rows.append({
            "order": int(order),
            "name": name,
            "title": TEAM_TITLE_FIXES.get(name, field(block, "title")),
            "source": rel,
        })
    return sorted(rows, key=lambda r: r["order"])


def viewbox_size(path: str):
    m = re.search(r'viewBox="([\d.\s-]+)"', read(path))
    if not m:
        return 0, 0
    parts = m.group(1).split()
    if len(parts) != 4:
        return 0, 0
    return int(round(float(parts[2]))), int(round(float(parts[3])))


def write_logo(src_path: str, dest_stem: str, box) -> tuple:
    """Write one logo at tile size and return (filename, width, height).

    SVGs pass straight through. Rasters are downscaled and then written in
    whichever format suits the artwork: a mark that needs transparency stays PNG,
    quantised so the flat-colour ones stay small, while the handful of solid
    photographic tiles go out as JPEG, which halves them.
    """
    if src_path.lower().endswith(".svg"):
        dest = dest_stem + ".svg"
        shutil.copyfile(src_path, dest)
        width, height = viewbox_size(dest)
        return os.path.basename(dest), width, height

    image = Image.open(src_path).convert("RGBA")
    image.thumbnail(box, Image.LANCZOS)
    transparent = image.getchannel("A").getextrema()[0] < 250

    if transparent:
        dest = dest_stem + ".png"
        quantised = image.quantize(colors=128, method=Image.FASTOCTREE)
        quantised.save(dest, format="PNG", optimize=True)
        # Banding can cost more than it saves on photographic art; keep whichever
        # is smaller, as long as the full-colour version is not much bigger.
        full = dest + ".full"
        image.save(full, format="PNG", optimize=True)
        if os.path.getsize(full) < os.path.getsize(dest):
            shutil.move(full, dest)
        else:
            os.remove(full)
    else:
        dest = dest_stem + ".jpg"
        image.convert("RGB").save(dest, quality=82, optimize=True, progressive=True)

    return os.path.basename(dest), image.width, image.height


def write_photo(src_path: str, dest_stem: str, box) -> tuple:
    """Write one page photo or screenshot as JPEG and return (filename, w, h).

    The sources run to 5MB apiece straight off a phone. Photography does not
    need an alpha channel and the frames it sits in are opaque, so anything with
    transparency (the product shots) is composited onto white rather than kept
    as a PNG that would be several times the size.
    """
    image = Image.open(src_path).convert("RGBA")
    image.thumbnail(box, Image.LANCZOS)
    flattened = Image.new("RGB", image.size, (255, 255, 255))
    flattened.paste(image, mask=image.getchannel("A"))
    dest = dest_stem + ".jpg"
    quality = 78 if max(box) > 1200 else 82
    flattened.save(dest, quality=quality, optimize=True, progressive=True)
    return os.path.basename(dest), image.width, image.height


def write_portrait(src_path: str, dest_path: str) -> tuple:
    image = Image.open(src_path).convert("RGB")
    side = min(image.size)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((PORTRAIT, PORTRAIT), Image.LANCZOS)
    image.save(dest_path, quality=82, optimize=True, progressive=True)
    return image.size


def write_identity(source: str, assets: str) -> list:
    wordmark_src = os.path.join(source, "assets/images/logos/tnn-logo-wordmark-white-rgb-900px-w-72ppi.png")
    wordmark = Image.open(wordmark_src).convert("RGBA")
    wordmark.save(os.path.join(assets, "tnn-wordmark-white.png"), optimize=True)

    # The header sits on white, and the only wordmark the brand ships is flat
    # white on transparency, so recolour its alpha mask to the theme's near-black.
    dark = Image.new("RGBA", wordmark.size, (11, 11, 11, 0))
    dark.putalpha(wordmark.getchannel("A"))
    dark.save(os.path.join(assets, "tnn-wordmark.png"), optimize=True)

    Image.open(os.path.join(source, "app/icon.png")).convert("RGBA").save(
        os.path.join(assets, "tnn-icon.png"), optimize=True
    )
    Image.open(os.path.join(source, "public/og-image.png")).convert("RGB").save(
        os.path.join(assets, "tnn-og-image.png"), optimize=True
    )
    print("identity: tnn-wordmark.png, tnn-wordmark-white.png, tnn-icon.png, tnn-og-image.png")

    # The wordmarks are resolved through the snippet so the header can fall back
    # to them; the icon and OG image are referenced by asset_url in the layout.
    # The third key is the network's own tile on the Experiences partner strip.
    return [
        ("identity-wordmark", "tnn-wordmark.png", "The Nation Network", wordmark.width, wordmark.height),
        ("identity-wordmark-white", "tnn-wordmark-white.png", "The Nation Network", wordmark.width, wordmark.height),
        ("partner-the-nation-network", "tnn-wordmark.png", "The Nation Network", wordmark.width, wordmark.height),
    ]


SNIPPET_HEAD = """{%- doc -%}
  Resolves a bundled brand image (assets/brand-*, assets/partner-*, assets/team-*)
  from a handleized name, so the network's logos and portraits render before
  anyone has uploaded them to Shopify Files. A real image picked in the editor
  always wins: sections only fall back to this.

  Generated by scripts/build_bundled_images.py -- edit the script, not this file.

  @param {string} key - '<family>-<handleized name>', e.g. 'brand-daily-faceoff'
  @param {string} [class] - CSS classes for the <img>
  @param {string} [alt] - overrides the generated alt text
  @param {string} [style] - inline style for the <img>
  @param {string} [loading] - loading attribute (default lazy)
{%- enddoc -%}

{%- liquid
  assign file = ''
  assign label = ''
  assign width = 0
  assign height = 0
  case key
"""

SNIPPET_TAIL = """  endcase
  assign loading = loading | default: 'lazy'
  if alt != blank
    assign label = alt
  endif
-%}

{%- if file != blank -%}
  <img
    src="{{ file | asset_url }}"
    alt="{{ label | escape }}"
    class="{{ class }}"
    width="{{ width }}"
    height="{{ height }}"
    {% if style != blank %}style="{{ style }}"{% endif %}
    loading="{{ loading }}"
    decoding="async"
  >
{%- endif -%}
"""


def write_snippet(path: str, entries: list) -> None:
    # The snippet writes width and height unconditionally, both to satisfy
    # theme check's ImgWidthAndHeight rule and to stop the tiles reflowing as
    # the images load, so every entry has to carry real dimensions.
    undimensioned = [key for key, _f, _l, width, height in entries if not (width and height)]
    if undimensioned:
        raise SystemExit("no dimensions for: %s" % ", ".join(undimensioned))

    out = [SNIPPET_HEAD]
    for key, filename, label, width, height in entries:
        out.append("    when '%s'\n" % key)
        out.append("      assign file = '%s'\n" % filename)
        out.append("      assign label = %s\n" % json.dumps(label))
        out.append("      assign width = %d\n" % width)
        out.append("      assign height = %d\n" % height)
    out.append(SNIPPET_TAIL)
    io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
    print("snippet: %s (%d keys)" % (os.path.relpath(path, REPO), len(entries)))


def clean(assets: str, prefixes) -> None:
    for name in os.listdir(assets):
        if any(name.startswith(p) for p in prefixes):
            os.remove(os.path.join(assets, name))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=DEFAULT_SOURCE, help="path to the thenationnetwork-www repo")
    ap.add_argument("--blocks-out", help="write template block JSON here (not committed)")
    args = ap.parse_args()

    source = args.source
    if not os.path.isdir(os.path.join(source, "assets/config")):
        return print("no marketing-site repo at %s" % source) or 2

    assets = os.path.join(REPO, "assets")
    clean(assets, ("brand-", "partner-", "team-", "photo-"))

    entries = write_identity(source, assets)
    blocks = {"mosaic": [], "partners": [], "team": []}

    brands = parse_brands(source)
    for brand in brands:
        handle = slug(brand["name"])
        filename, width, height = write_logo(
            os.path.join(source, brand["source"]), os.path.join(assets, "brand-%s" % handle), LOGO_MAX
        )
        entries.append(("brand-%s" % handle, filename, brand["name"], width, height))
        blocks["mosaic"].append({
            "type": "tile",
            "settings": {"name": brand["name"], "tile_color": brand["colour"], "link": brand["url"]},
        })
    print("brands: %d logos" % len(brands))

    advertisers = parse_advertisers(source)
    for advertiser in advertisers:
        handle = slug(advertiser["name"])
        filename, width, height = write_logo(
            os.path.join(source, advertiser["source"]), os.path.join(assets, "partner-%s" % handle), PARTNER_MAX
        )
        entries.append(("partner-%s" % handle, filename, advertiser["name"], width, height))
        blocks["partners"].append({"type": "logo", "settings": {"name": advertiser["name"], "link": ""}})
    print("advertisers: %d logos" % len(advertisers))

    team = parse_team(source)
    for person in team:
        handle = slug(person["name"])
        filename = "team-%s.jpg" % handle
        size = write_portrait(os.path.join(source, person["source"]), os.path.join(assets, filename))
        entries.append(("team-%s" % handle, filename, person["name"], size[0], size[1]))
        blocks["team"].append({
            "type": "person",
            "settings": {"name": person["name"], "title": person["title"], "link": ""},
        })
    print("team: %d portraits" % len(team))

    for family, rows, box in (("photo", PAGE_PHOTOS, PHOTO_MAX),
                              ("photo", PAGE_SCREENSHOTS, SCREENSHOT_MAX),
                              ("photo", HERO_PHOTOS, HERO_MAX)):
        for handle, relative, label in rows:
            source_file = os.path.join(source, relative)
            if not os.path.exists(source_file):
                print("  ! missing %s" % relative)
                continue
            filename, width, height = write_photo(
                source_file, os.path.join(assets, "%s-%s" % (family, handle)), box
            )
            entries.append(("%s-%s" % (family, handle), filename, label, width, height))
    print("page imagery: %d photos, %d screenshots, %d hero" % (
        len(PAGE_PHOTOS), len(PAGE_SCREENSHOTS), len(HERO_PHOTOS)))

    hosts = parse_hosts(source)
    for person in hosts:
        handle = slug(person["name"])
        filename = "team-%s.jpg" % handle
        width, height = write_portrait(
            os.path.join(source, person["source"]), os.path.join(assets, filename)
        )
        entries.append(("team-%s" % handle, filename, person["name"], width, height))
    print("hosts: %d portraits" % len(hosts))

    write_snippet(os.path.join(REPO, "snippets", "bundled-image.liquid"), entries)

    if args.blocks_out:
        json.dump(blocks, io.open(args.blocks_out, "w", encoding="utf-8"), indent=1)
        print("blocks: %s" % args.blocks_out)

    total = sum(
        os.path.getsize(os.path.join(assets, f))
        for f in os.listdir(assets)
        if f.startswith(("brand-", "partner-", "team-", "photo-", "tnn-"))
    )
    print("bundled %.1f MB of imagery" % (total / 1024.0 / 1024.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
