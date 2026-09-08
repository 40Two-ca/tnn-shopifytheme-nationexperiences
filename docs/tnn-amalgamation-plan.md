# Folding thenationnetwork.com into this store

The decision: **Shopify becomes the whole site.** `thenationnetwork.com` is
served by this theme, the marketing pages are rebuilt as Shopify pages and
sections, and the WordPress install is retired. Nation Experiences stops being
a separate destination and becomes the commerce layer of Beyond The Game.

## Where things stand

**The live site** is WordPress 7.1, Astra child theme, Elementor. Not the
`thenationnetwork-www` Next.js repo — that was the previous build and its last
commits are Dec 2025. The repo is still the best source for structured content
and assets (`assets/config/*.ts`, 266 images under `assets/images/`, and
`AXIS Extra Bold.woff2`, the headline face), but **copy must be taken from the
live site**, which has drifted.

**This store** is a development store on the 40Two Group Shopify org, password
protected, primary domain still `.myshopify.com`. Live theme is stock Horizon
4.1.5; all real work is on the GitHub-connected draft theme. Catalogue is two
experiences, one collection, two stock pages.

## Page map

| WordPress | Shopify | Built with |
|---|---|---|
| `/` | `/` | `templates/index.json` — **done** |
| `/beyond-the-game` | `/pages/beyond-the-game` | `story-strand` × 4 + `product-list` — **done** |
| `/brands/daily-faceoff` | `/pages/daily-faceoff` | `story-strand` × 6 + `network-stats` — **done** |
| `/brands/the-nations` | `/pages/the-nations` | `brand-mosaic` + `story-strand` × 3 — **done** |
| `/brands/hockey-fights` | `/pages/hockey-fights` | `story-strand` + `network-stats` — **done** |
| `/partner-with-us` | `/pages/partner-with-us` | `story-strand` + `network-stats` + `partner-logos` + Typeform — **done** |
| `/work-with-us` | `/pages/work-with-us` | three-route `feature-tiles` — **done** |
| `/work-with-us/creator`, `/inquiry` | `/pages/contact` for now | Shopify contact form or Typeform — undecided |
| `/press-releases/*` | `/blogs/news/*` | native blog |
| — | `/collections/experiences` | trips |
| — | `/collections/nation-gear` | merch |

Nation Gear is currently an outbound link on the marketing site. Folding it in
is the main open question — see below.

## Sections added

Four patterns the marketing site had and the theme did not. All follow the
existing conventions (`section--{width}`, `spacing-style`, `contrast-override`,
scoped `{% stylesheet %}`, presets under a **The Nation Network** category), so
they are available in the editor on any template.

- `network-stats` — the audience counters. Counts up on scroll via
  IntersectionObserver, honours `prefers-reduced-motion`, offset plate behind
  each card. Values and decimal places are per-block settings.
- `distribution-channels` — the platform row. Uses Horizon's icon set
  (`snippets/icon.liquid`); `image_picker` per block covers anything without a
  built-in icon, e.g. the web glyph.
- `brand-mosaic` — the edge-to-edge show/brand tile wall. Per-tile background
  colour so it reads as one mosaic; up to 48 tiles.
- `leadership-grid` — portrait cards with name, title, optional bio and
  LinkedIn. Reusable for hosts and on-air talent on the brand pages.

The trip-led home page is preserved verbatim as `templates/page.experiences.json`.

## Brand foundation — done

The first two items are built. `AXIS Extra Bold` is the heading face
(`snippets/brand-variables.liquid`), and the palette needed nothing: white
ground, near-black text, lime accent is already the network's.

The rest of the identity now ships in the theme rather than waiting on an
upload, because Shopify's `image_picker` settings can only point at Shopify
Files and this store has none:

| Asset | File | Wired as |
| --- | --- | --- |
| Wordmark, recoloured near-black for the white header | `assets/tnn-wordmark.png` | fallback in `blocks/_header-logo.liquid` |
| Wordmark, white | `assets/tnn-wordmark-white.png` | for dark surfaces |
| App icon | `assets/tnn-icon.png` | favicon fallback in `layout/theme.liquid` and `layout/password.liquid` |
| Share card | `assets/tnn-og-image.png` | `og:image` fallback in `snippets/meta-tags.liquid` |

Each is a fallback: anything uploaded in theme settings wins, and these stop
rendering. The brand only ships a white-on-transparent wordmark, so the dark
one is generated from its alpha mask — the artwork is flat white, so nothing is
lost. The recolour happens in the build script, not by hand.

### Bundled brand imagery

`scripts/build_bundled_images.py` pulls the logos, advertiser marks and staff
portraits out of `thenationnetwork-www`, downscales them to tile size and
generates `snippets/bundled-image.liquid`. Run it when the source art changes:

```bash
python scripts/build_bundled_images.py
```

It parses `brands.ts`, `advertisers.ts` and `staff.ts` rather than restating
them, so the theme cannot drift from the old site's data, and it picks a format
per image (SVG through, PNG where transparency matters, JPEG for the solid
photographic tiles): 4.4MB of source art lands as 1.8MB.

Sections resolve a bundled image from the block's own **name**, handleized —
a tile named "Daily Faceoff" gets `assets/brand-daily-faceoff.svg`. There is no
extra setting to keep in step, but renaming a block does drop its logo back to
a text placeholder, so `scripts/validate_templates.py` warns when a block name
has no bundled image behind it.

Two logo notes worth keeping: the `_new.png` nation marks are dark on
transparency and vanish on their own dark brand colour, so those four tiles use
the older light variants or the SVG; and Warmies is dropped for the same reason
with no legible combination available, which lands the wall on 48 tiles — the
mosaic's own limit.

## Still to do

1. **Real photography.** Everything above is the network's own artwork, but the
   three brand tiles on the home page and the trip pages still use Unsplash
   placeholders from `assets/stock-*.jpg`. The `beyondthegame`, `casestudies`
   and `playmaker` folders in the old repo hold 266 images that have not been
   sorted through yet.
2. **Confirm the roster.** The six leadership names, titles and portraits come
   from the old repo, last touched December 2025, and `frontPageOrder` skips a
   slot, so someone has left. The live WordPress site sits behind a bot check
   that blocks reading it from here — the client should confirm the six people
   and the 19 unlinked show tiles.
3. **Acast players and the enquiry forms.** The brand pages carried an embedded
   podcast player per show; six iframes on one page is a decision about page
   weight and consent, so the strands ship with copy and screenshots instead.
   The creator and general-enquiry routes ran on Mailgun and reCAPTCHA in the
   Next repo and now point at `/pages/contact` as a placeholder.
4. **Navigation.** Main menu → Our Brands (dropdown), Beyond The Game,
   Experiences, Shop, Partner With Us, Contact. Footer → brands, company,
   legal, LinkedIn, Better Collective attribution.
5. **Forms.** The Typeform embeds and the two `work-with-us` API routes
   (Mailgun + reCAPTCHA in the Next repo) have no Shopify equivalent. Either
   keep Typeform or rebuild on Shopify's contact form.
6. **Blog** for press releases, plus authors and tags.
7. **Redirect map.** Every WordPress URL → its Shopify path, loaded via
   `URL redirects` (bulk CSV import). Non-negotiable: these are indexed pages.
8. **Analytics.** GA4 + Search Console on the new property; the network runs 15
   GA4 properties, so confirm which one this rolls into.

## The pages need creating in admin

A page template renders nothing until a Page record points at it, and none of
these exist on the store yet — the catalogue has only Contact and Your Privacy
Choices. Each row below is **Content → Pages → Add page**, with the title typed
exactly as given so Shopify generates the handle the templates link to, and the
**Template** set to the matching entry:

| Title | Handle it should generate | Template |
| --- | --- | --- |
| Experiences | `experiences` | `page.experiences` |
| Beyond The Game | `beyond-the-game` | `page.beyond-the-game` |
| The Nations | `the-nations` | `page.the-nations` |
| Daily Faceoff | `daily-faceoff` | `page.daily-faceoff` |
| Hockey Fights | `hockey-fights` | `page.hockey-fights` |
| Partner With Us | `partner-with-us` | `page.partner-with-us` |
| Work With Us | `work-with-us` | `page.work-with-us` |

Leave the body content empty: every page's copy is in its template, so anything
typed here renders as well and would duplicate it. New pages default to
**Hidden**, so each needs setting to Visible.

The handles matter beyond tidiness — the home page's brand tiles link to
`/pages/daily-faceoff`, `/pages/the-nations` and `/pages/hockey-fights`, its
partner CTA to `/pages/partner-with-us`, and Beyond The Game's travel strand to
`/pages/experiences`. A handle that does not match is a dead link.

Two things worth knowing before starting. Shopify builds the Template dropdown
from the **published** theme, and the GitHub-connected theme here is a draft, so
the new templates may not be offered until it is published — if they are
missing, publish first, or expect to come back and set them. And this cannot be
done from an agent: the current admin is built from web components in shadow
DOM, and neither typing nor clicking reaches them through browser automation.

## Cutover blockers

These are decisions, not code.

- **Store plan.** A development store cannot connect a custom domain. It needs a
  paid plan before `thenationnetwork.com` can point here.
- **Ownership.** The store sits under **40Two Group Inc.**; the site is a Better
  Collective property. The domain, the Shopify account and the commercial
  relationship need to line up before DNS moves.
- **Nation Gear.** If merch stays on its current platform, "one cohesive site"
  is only partly true. Migrating it into this catalogue is a separate project
  with its own SKU, fulfilment and tax implications.
- **Editorial.** The brand sites (dailyfaceoff.com, oilersnation.com, …) stay
  where they are. Only the corporate/marketing layer moves.

## Order of work

1. ~~Brand foundation and assets~~ — done, bar the photography.
2. ~~Page templates~~ — done; the Page records and the two menus are admin work.
3. Forms and blog.
4. Plan upgrade, redirect map, staging review on a preview theme.
5. DNS cutover, then remove the storefront password.
