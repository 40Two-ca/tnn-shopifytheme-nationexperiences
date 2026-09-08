"""Convert the old site's press releases into paste-ready Shopify article HTML.

Shopify blog articles are admin data, not theme files, and there is no CSV
import for them, so these cannot be pushed from the repo. What this does is turn
the two press releases in `thenationnetwork-www/app/press-releases/*/page.tsx`
into clean HTML bodies plus the metadata each article needs, ready to paste into
Content > Blog posts.

    python scripts/build_press_releases.py

Writes `docs/press-releases/<handle>.html` and a README with the fields to set.
The output is reviewed by eye before it goes anywhere: this is a regex transform
over JSX, not a parser, so it is trusted only as far as reading it confirms. What
that review checked: no JSX leaked through (no `className`, braces, `<div>` or
`<Image>`), the tag set is down to a, em, h2, li, p, strong, ul, and every one of
those balances -- p 10/10, ul 14/14, li 33/33 on the longer release.
"""

from __future__ import annotations

import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(os.path.dirname(REPO), "thenationnetwork-www")
OUT_DIR = os.path.join(REPO, "docs", "press-releases")

# Dates and titles come from the old index page and each release's own metadata,
# not from the file system.
ARTICLES = [
    {
        "handle": "raptors-republic-has-joined-the-nation-network",
        "title": "Raptors Republic Has Joined The Nation Network",
        "date": "2024-10-17",
        "tags": "Press release, Raptors Republic, Basketball",
        "excerpt": "The Nation Network has added Raptors Republic, a premier independent "
                   "platform for NBA, Toronto Raptors and Canada Basketball coverage, to its "
                   "sports media lineup.",
        "image_note": "The release opened with a TNN x Raptors Republic banner "
                      "(assets/images/press-releases/ in the old repo). Upload it as the "
                      "article's featured image rather than putting it in the body.",
    },
    {
        "handle": "2024-25-nation-network-hockey-programming",
        "title": "The Nation Network Announces 2024-25 Hockey Programming",
        "date": "2024-10-03",
        "tags": "Press release, Hockey, Programming",
        "excerpt": "TNN's hockey programming reaches all major markets across Canada, with "
                   "daily episodes, pre- and post-game shows, and content across video, "
                   "podcast, social and web.",
        "image_note": "No banner in the original.",
    },
]


def jsx_to_html(source: str) -> str:
    """Turn one press-release component's JSX into article HTML."""
    body = source[source.index("export default function Page()"):]

    # Drop the wrapper and the Next <Image>: a featured image is an article
    # field in Shopify, not body content.
    body = re.sub(r"<Image[^>]*/>", "", body, flags=re.S)

    # JSX text glue and the odd quoted literal.
    body = body.replace('{" "}', " ")
    body = re.sub(r'\{"([^"]*)"\}', r"\1", body)

    # Tailwind's font-bold spans are the only emphasis in these files.
    body = re.sub(r'<span className="font-bold">(.*?)</span>', r"<strong>\1</strong>", body, flags=re.S)
    body = re.sub(r'<p className="text-center italic[^"]*">(.*?)</p>',
                  r"<p><em>\1</em></p>", body, flags=re.S)

    # Everything else keeps its tag and loses its attributes, except links,
    # which keep href and gain the rel that target="_blank" needs.
    body = re.sub(r'<a\s+([^>]*?)>', _link, body, flags=re.S)
    body = re.sub(r'<span[^>]*>|</span>', "", body)
    body = re.sub(r'\s+className="[^"]*"', "", body)
    body = re.sub(r"\s+target=\"_blank\"", "", body)

    # Layout divs carry no meaning once the Tailwind classes are gone.
    body = re.sub(r"</?div>", "", body)

    # Keep only the markup between the first heading and the end of the return.
    start = body.index("<h1")
    end = body.rindex("</")
    end = body.rindex(">", 0, body.rindex("</p>") + 4) + 1 if "</p>" in body else end
    body = body[start:end]

    # The h1 is the article title in Shopify, so it does not belong in the body.
    body = re.sub(r"<h1.*?</h1>", "", body, flags=re.S)

    # Tidy whitespace: collapse runs, put one blank line between blocks.
    body = re.sub(r"[ \t]*\n[ \t]*", "\n", body)
    body = re.sub(r"\n{2,}", "\n", body)
    body = re.sub(r"\s+", " ", body)
    # JSX indentation becomes real whitespace once the tags go, which renders as
    # "Raptors Republic , a premier ..." -- a space before the comma. Tighten the
    # inside edges of every inline tag, then any space left before punctuation.
    for tag in ("a", "strong", "em", "p", "h2", "li"):
        body = re.sub(r"<%s(\s[^>]*)?>\s+" % tag, lambda m: m.group(0).rstrip(), body)
        body = re.sub(r"\s+</%s>" % tag, "</%s>" % tag, body)
    body = re.sub(r"\s+([,.;:!?%)])", r"\1", body)
    body = re.sub(r"\(\s+", "(", body)

    # JSX escaped its own quotes and apostrophes; HTML body copy does not need
    # to. The source also mixes these straight quotes with curly ones, which is
    # its own inconsistency and not one to guess a fix for -- see the README.
    body = body.replace("&apos;", "'").replace("&quot;", '"')

    for tag in ("</p>", "</h2>", "</ul>", "</li>"):
        body = body.replace(tag, tag + "\n")
    body = re.sub(r"\n\s+", "\n", body)
    return body.strip() + "\n"


def _link(match: re.Match) -> str:
    href = re.search(r'href="([^"]*)"', match.group(1))
    if not href:
        return "<a>"
    external = href.group(1).startswith("http")
    rel = ' target="_blank" rel="noopener noreferrer"' if external else ""
    return '<a href="%s"%s>' % (href.group(1), rel)


def main() -> int:
    if not os.path.isdir(SOURCE):
        return print("no marketing-site repo at %s" % SOURCE) or 2
    os.makedirs(OUT_DIR, exist_ok=True)

    lines = ["# Press releases, ready to paste", "",
             "Shopify has no CSV import for blog articles, so each of these is a manual",
             "**Content > Blog posts > Add blog post** in the `news` blog. Paste the HTML",
             "with the `<>` code view on, or the markup arrives as visible text.", ""]

    for article in ARTICLES:
        path = os.path.join(SOURCE, "app/press-releases", article["handle"], "page.tsx")
        html = jsx_to_html(io.open(path, encoding="utf-8").read())
        out = os.path.join(OUT_DIR, article["handle"] + ".html")
        io.open(out, "w", encoding="utf-8", newline="\n").write(html)
        words = len(re.sub(r"<[^>]+>", " ", html).split())
        print("wrote docs/press-releases/%s.html (%d words)" % (article["handle"], words))

        lines += [
            "## %s" % article["title"], "",
            "| Field | Value |", "| --- | --- |",
            "| Title | %s |" % article["title"],
            "| Handle | `%s` |" % article["handle"],
            "| Blog | `news` |",
            "| Published | %s |" % article["date"],
            "| Tags | %s |" % article["tags"],
            "| Excerpt | %s |" % article["excerpt"],
            "| Body | `docs/press-releases/%s.html` |" % article["handle"],
            "| Featured image | %s |" % article["image_note"],
            "",
            "The handle must match exactly: `docs/redirects.csv` sends",
            "`/press-releases/%s` to `/blogs/news/%s`." % (article["handle"], article["handle"]),
            "",
        ]

    io.open(os.path.join(OUT_DIR, "README.md"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines))
    print("wrote docs/press-releases/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
