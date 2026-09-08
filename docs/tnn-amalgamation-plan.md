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
| `/beyond-the-game` | `/pages/beyond-the-game` | `feature-tiles` + `product-list` + galleries |
| `/brands/daily-faceoff` | `/pages/daily-faceoff` | `media-with-content` + show grid |
| `/brands/the-nations` | `/pages/the-nations` | `brand-mosaic` + `media-with-content` |
| `/brands/hockey-fights` | `/pages/hockey-fights` | `media-with-content` |
| `/partner-with-us` | `/pages/partner-with-us` | `trust-points` + `network-stats` + Typeform |
| `/work-with-us` | `/pages/work-with-us` | three-route CTA (reuse `feature-tiles`) |
| `/work-with-us/creator`, `/inquiry` | `/pages/...` | Shopify contact form or Typeform |
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

## Still to do

1. **Brand foundation.** Load `AXIS Extra Bold.woff2` as a `@font-face` in
   `assets/` and point `--font-heading--family` at it; today the theme is on
   Archivo/Jost. Set the palette to the network's black/white rather than the
   Experiences lime (`color1: #d2ff28`) — or decide the lime is the unified
   accent. Header logo, favicon, OG image.
2. **Assets.** Import the 266 images and the show/advertiser logos from
   `thenationnetwork-www/assets/images/` into Shopify Files, then wire them into
   the mosaic, partner and leadership blocks. Currently all placeholders.
3. **Page templates** for each row of the map above.
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

1. Brand foundation and assets — everything else looks wrong without it.
2. Page templates and navigation.
3. Forms and blog.
4. Plan upgrade, redirect map, staging review on a preview theme.
5. DNS cutover, then remove the storefront password.
