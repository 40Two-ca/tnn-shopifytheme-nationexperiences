"""Generate the URL redirect map for the thenationnetwork.com cutover.

Every old URL has to land somewhere on the new store or it becomes a 404 on a
page search engines already index. This writes `docs/redirects.csv` in the
format Shopify's bulk importer expects (Online Store > Navigation > URL
redirects > Import).

    python scripts/build_redirects.py
    python scripts/build_redirects.py --trailing-slash   # add "/path/" variants

WHERE THE OLD URLS COME FROM, AND THE LIMIT OF THAT

The live site is WordPress and cannot be read from here -- it sits behind a bot
check that blocks automated requests. So this inventory is built from the
`thenationnetwork-www` repo, the previous Next.js build: its route files, and
its own `app/sitemap.ts`. Those two disagree with each other -- the sitemap
publishes `/brands/case-studies`, `/brands/our-team` and `/brands/work-with-us`
while the routes are `/case-studies`, `/our-team` and `/work-with-us` -- so both
shapes are included. A redirect for a URL nobody ever indexed simply never
fires; a missing one loses a page. The asymmetry is worth exploiting.

**This is a starting point, not the finished map.** Before importing, diff it
against what is actually indexed: the live site's own sitemap.xml, or better,
the Search Console page list for the property. Anything there and not here
still needs a row.
"""

from __future__ import annotations

import argparse
import csv
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (old path, new path, why) -- new paths are the handles the templates expect,
# so they depend on the Page records in docs/tnn-amalgamation-plan.md existing.
REDIRECTS = [
    ("/beyond-the-game", "/pages/beyond-the-game", "same page, rebuilt"),
    # The three brand pages were folded into /pages/hockey, one destination per
    # sport. Shopify wraps each section of a JSON template in
    # <div id="shopify-section-KEY">, so each old URL still lands on the part of
    # the page that holds its brand rather than at the top of a long page.
    ("/brands/daily-faceoff", "/pages/hockey#shopify-section-dfo", "folded into the hockey page"),
    ("/brands/hockey-fights", "/pages/hockey#shopify-section-hf", "folded into the hockey page"),
    ("/brands/the-nations", "/pages/hockey#shopify-section-nations", "folded into the hockey page"),
    ("/partner-with-us", "/pages/partner-with-us", "same page, rebuilt"),
    ("/work-with-us", "/pages/work-with-us", "same page, rebuilt"),
    ("/brands/work-with-us", "/pages/work-with-us", "sitemap.ts variant of the same page"),

    # The creator and general-enquiry routes ran on their own forms (Mailgun and
    # reCAPTCHA). Until that choice is made they land on the contact page, which
    # is where the Work With Us tiles point too.
    ("/work-with-us/creator", "/pages/contact", "form has no Shopify equivalent yet"),
    ("/work-with-us/inquiry", "/pages/contact", "form has no Shopify equivalent yet"),
    ("/work-with-us/thank-you", "/pages/work-with-us", "post-submit page, no equivalent"),

    # Case studies were partner-facing proof, so they go where that argument now
    # lives rather than nowhere.
    ("/case-studies", "/pages/partner-with-us", "no equivalent page; nearest intent"),
    ("/case-studies/bet365", "/pages/partner-with-us", "no equivalent page; nearest intent"),
    ("/case-studies/mcleod-law", "/pages/partner-with-us", "no equivalent page; nearest intent"),
    ("/case-studies/telus", "/pages/partner-with-us", "no equivalent page; nearest intent"),
    ("/case-studies/wendys", "/pages/partner-with-us", "no equivalent page; nearest intent"),
    ("/brands/case-studies", "/pages/partner-with-us", "sitemap.ts variant"),

    # The leadership grid is a section on the home page rather than a page of
    # its own, so this is the closest honest destination. A real Our Team page
    # would be better, and would want its own row here.
    ("/our-team", "/", "leadership now lives on the home page"),
    ("/brands/our-team", "/", "sitemap.ts variant"),

    ("/socials", "/", "link hub, already disabled on the old build"),

    ("/press-releases", "/blogs/news", "needs the blog from plan item 6"),
    ("/press-releases/2024-25-nation-network-hockey-programming",
     "/blogs/news/2024-25-nation-network-hockey-programming", "needs the blog and this article"),
    ("/press-releases/raptors-republic-has-joined-the-nation-network",
     "/blogs/news/raptors-republic-has-joined-the-nation-network", "needs the blog and this article"),
]

# Deliberately not redirected. A wrong destination on one of these is worse
# than a 404 that someone notices and fixes.
UNRESOLVED = [
    ("/survey-terms", "Legal terms for a survey. Sending it to the home page would be "
                      "misleading; it needs either its own page or a policy page to point at."),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trailing-slash", action="store_true",
                        help="also emit a \"/path/\" row for each entry, in case the live "
                             "WordPress site serves trailing slashes")
    parser.add_argument("--out", default=os.path.join(REPO, "docs", "redirects.csv"))
    args = parser.parse_args()

    rows = [(old, new) for old, new, _why in REDIRECTS]
    if args.trailing_slash:
        rows += [(old + "/", new) for old, new in rows if not old.endswith("/")]

    with io.open(args.out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Redirect from", "Redirect to"])
        writer.writerows(rows)

    print("wrote %s" % os.path.relpath(args.out, REPO).replace(os.sep, "/"))
    print("  %d redirects" % len(rows))
    destinations = sorted({new for _old, new in rows})
    print("  %d destinations: %s" % (len(destinations), ", ".join(destinations)))
    print("\nnot redirected, needs a decision:")
    for path, why in UNRESOLVED:
        print("  %-16s %s" % (path, why))
    print("\nDestinations that do not exist yet: every /pages/* row needs its Page record,")
    print("and the /blogs/news rows need the blog and both articles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
