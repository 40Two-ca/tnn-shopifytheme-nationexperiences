# Contiki review and Nation Experiences theme direction

Reviewed: https://www.contiki.com/en-ca (home, a tour page, a destination landing page) on 2026-09-04.
Compared against: https://nationexperiences.ca (Dawn 12, black header, Jost, event promos in a slideshow).

## What makes Contiki look like Contiki

| Element | Contiki | This theme now |
| --- | --- | --- |
| Palette | Black text on white, one loud accent (lime `#CCFF00`) for the announcement bar, CTAs and the search button; red `#FF1E37` for savings badges; `#F9F9F9` panels | Same structure. Accent is **one setting**: Theme settings → Colors → palette colour 1 (default `#D2FF28`). Red is used for sale badges. |
| Type | Heavy grotesque headings (Acumin Pro 800–950, hero in uppercase), geometric body (Soleil 400/700) | Archivo 900 headings, H1 uppercase; Jost body (already the Nation Experiences font) |
| Buttons | Full pills, bold, short uppercase labels ("VIEW TRIPS", "SEARCH") | Pill radius 100, bold uppercase, accent primary, outline secondary |
| Announcement bar | Lime, bold uppercase, one line | Accent background, bold uppercase |
| Header | White, sticky, logo left, uppercase nav, prominent pill search ("Find your adventure" + lime search circle), phone + account on the right | White sticky header, uppercase nav, search rendered as a pill with an accent circle |
| Hero | Full-bleed photo, dark overlay, centred 2-line uppercase headline, one-line sub, lime pill CTA | Same layout in `templates/index.json` (hero section) |
| Trip finder | White rounded bar overlapping the hero: Where / What / When + lime SEARCH | New `trip-finder` section: destination select, keyword, month, accent search button. Overlaps the hero. |
| Value props | Three photo tiles with white bold copy ("200+ trips across 6 continents…") under "Why Contiki?" | New `feature-tiles` section |
| Trip cards | White card, 6px radius, soft shadow, 2:1 photo, badge top corner (POPULAR / BUDGET-FRIENDLY / SAVE $), rating, bold title, icon meta row (11 Days · 5 Places · 1 Country), one-line hook, "From $2,723" + lime VIEW TRIP pill | Product cards rebuilt from blocks: `trip-badge`, `trip-meta`, `product-excerpt`, `trip-price`, `product-link-button` (all editable in the theme editor) |
| Card carousels | Centred heading + sub ("From Reels to Real / Explore our most popular trips"), circle arrows, VIEW ALL pill | `product-list` section in carousel mode with centred header and a bottom button |
| Social proof | "Rated 5★ by over 20,000 travellers", three quotes with traveller name + trip | New `testimonials` section |
| Destinations | Photo tiles per region + "See all trips" | New `destination-tiles` section (falls back to all collections) |
| Book with confidence | Four check-marked reassurances + FIND OUT MORE, with a photo | New `trust-points` section |
| As seen in | Grey logo strip | New `partner-logos` section |
| Tour page | Photo hero, badge, title, meta row (days / country / cities), rating, "FROM $2,495" + deposit line, lime PICK DATES, then What's included, Itinerary, Reviews, FAQs accordions | `templates/product.json`: a short booking column (badge, title, meta, stats, price, "Book now"), then full-width `trip-overview`, `trip-timeline`, `trust-points` and `trip-faqs` sections |
| Itinerary rail | Vertical day-by-day list with markers, "Day 1" over the place name, each day expandable | `trip-timeline` section: markers on a rail, day label, title and description |
| Listing page | Title hero, left filter sidebar, trip cards | `templates/collection.json`: vertical filters, trip cards |
| Footer | Dark, three link columns, newsletter, legal row | Dark footer, two menu columns, newsletter, socials, legal row |

## Where the trip-card data comes from

Everything degrades gracefully: a card with no metafields still shows image, title, hook, price and button.

| Card element | Source (first match wins) |
| --- | --- |
| Badge | Product metafield `custom.badge` (single line text) → product tag `badge:Popular` → block override |
| Duration / Location / Dates / Group | Metafields `custom.duration`, `custom.location`, `custom.dates`, `custom.group_size` (single line text) → tags `duration:3 days`, `location:Jasper, AB`, `dates:Jan 22–24`, `group:Small group` |
| One-line hook | Metafield `custom.short_description` → first words of the description |
| Price | Cheapest variant; "Was" shown when it has a compare-at price; $0 products show "See details" (editable) |
| Product page accordions | Description, plus metafields `custom.whats_included`, `custom.itinerary`, `custom.good_to_know` (rich text or multi-line text) |
| Itinerary timeline | Metafield `custom.itinerary_days` (multi-line text), one day per line as `Day label \| Title \| Description` |
| Trip FAQs | Metafield `custom.faqs`, one per line as `Question \| Answer`. General FAQs are blocks on the section, shared by every product |
| Trip stats | Metafield `custom.stats`, one per line as `Value \| Label`, e.g. `4 \| days` |
| What's included | Metafields `custom.included` and `custom.not_included`, one item per line. Prefix an item with an icon name and a pipe (`plane \| Return airfare`) to change its icon |

Create the metafield definitions in Shopify admin → Settings → Custom data → Products (namespace `custom`, keys above).

## What the store needs to upload or set

1. A dark version of the wordmark for the white header (the current logo is white-on-transparent). Theme settings → Logo. The white one can go in "Inverse logo".
2. A hero photo (and an optional mobile crop) on the home page hero.
3. Photos for the three feature tiles, the destination tiles (collection images) and the "Book with confidence" panel.
4. Menus: `main-menu` for the header/footer "Experiences" column, `footer` for the "Help" column.
5. Partner logos (Jetset Vacations, Expedia Cruises, The Nation Network, Fairmont…) in the partner logo strip.
6. Metafields listed above on each experience. The `custom.itinerary_days`, `custom.faqs`, `custom.stats`, `custom.included` and `custom.not_included` definitions already exist on the demo store (Settings, Custom data, Products) and are filled for both demo experiences.

7. Alt text on the three stock photos added to the Toronto trip (Toronto skyline, arena, fans). The admin was returning errors on that product's page when they went up, so it was not set.
8. Real prices for the eight Toronto variants. The demo uses $3,099 flight/single, $2,799 flight/double, $2,299 land/single, $1,999 land/double, and a $500 deposit on every combination. Every variant is stocked at 50.
9. The Afterpay button on the trip page is a demo placeholder and takes no payment. Install the provider's Shopify app and swap in their app block, or remove the `pay-later` block, before this store goes live.

## Deliberate differences from Contiki

- No "Add to compare", "Quick view", live chat or account tiers: those are Contiki platform features, not theme work.
- The trip finder searches Shopify (destination → collection, keyword/month → product search) rather than a booking engine.
- Accent colour ships as a volt green next to Contiki's lime; change palette colour 1 to recolour the whole site.

## Before pushing

The store syncs `main` through Shopify's GitHub integration, which rejects JSON template values outside a setting's range and reports only the first error per file. Run the validator first:

```bash
python scripts/validate_templates.py
```

Then `shopify theme check`. The demo store is `tnn-nationexperiences.myshopify.com`; the synced theme sits under Online Store > Themes > Draft themes (preview it from its ... menu).

Two sync rules cost a lot of time on this theme, so the validator now checks both:

- **A new section and a template that uses it cannot go up in the same push.** The template is validated against the section files already on the theme, so it is rejected with "Section type 'x' does not refer to an existing section file". Push the section first, then the template.
- **Inside a `{% liquid %}` block every line is its own tag.** A `render` with its arguments spread over several lines is a syntax error there, reported as "Unknown tag" for the first argument name. Theme check does not catch it. Keep such tags outside the `liquid` block.

When a push does not show up, read the sync log: Online Store > Themes, then **View logs** under the draft theme. It names the file and the reason. It is the fastest way to find out what was rejected.

## Stock photos

`assets/stock-*.jpg` are Unsplash photos (Unsplash License, free to use) bundled as placeholders. Sections show them only until a real image is picked in the editor. Replace them with Nation Experiences photography before launch.

| File | Unsplash photo |
| --- | --- |
| stock-hero-crowd.jpg | unsplash.com/photos/WrNbw7UeNqI |
| stock-arena.jpg | unsplash.com/photos/HwZTYUkIP6c |
| stock-airport.jpg | unsplash.com/photos/rUXh5USKfUQ |
| stock-fans.jpg | unsplash.com/photos/U4KutCl_GKg |
| stock-toronto.jpg | unsplash.com/photos/s0grRYEDaL4 |
| stock-edmonton.jpg | unsplash.com/photos/kczeUEAhDZI |
| stock-calgary.jpg | unsplash.com/photos/_QOR7cwVDik |
| stock-jasper.jpg | unsplash.com/photos/tYZH_KWl_IM |
| stock-stadium-seats.jpg | unsplash.com/photos/HDwBnsB9Tkc |
| stock-road-trip.jpg | unsplash.com/photos/C9DziWnywgo |

## Page width

Page width is set to **narrow** in theme settings, which is 1440px in Horizon despite the name. That matches Contiki's content column. The wide option is 2400px and stretches long-form copy past a readable line length on large monitors.

Long-form text also caps its own measure at 68 characters (`ch` units) in the timeline and FAQ sections, so a single long sentence cannot run the full width of the page whatever the page width setting is.

## Product page layout

Trip artwork is a wide banner, roughly two to one. In Horizon's product layout the
image sits in a 2fr column and the booking details in a 1fr column, so a banner is
always short while the details column is tall. Anything long in that column leaves a
block of empty space under the image, and no page width or column ratio fixes it:
a wider image column makes the image shorter, a narrower one makes the details taller.

So the booking column holds only what someone needs in order to book: badge, title,
trip meta, stats, price and the buy buttons. That comes out close to the height of the
banner. The reading material moved into full-width sections underneath, which is also
how Contiki orders a tour page:

1. `trip-overview` - the product description beside What's included / What's not included
2. `trip-timeline` - the day-by-day itinerary
3. `trust-points`
4. `trip-faqs` - trip FAQs from the metafield beside the general FAQs

If a trip ever ships with tall portrait photography instead of a banner, blocks can move
back into the booking column without any code change.

### Gallery shapes

Trip artwork is not one shape. The Toronto banner is roughly 1.8:1, the Jasper
poster is square. The supporting photos have to match each other or the grid
looks ragged, so the gallery frame is set to landscape in the theme editor, but
that frame cut half the Jasper poster off.

The lead image therefore sizes to its own ratio and everything after it uses the
frame. That is a CSS rule in `assets/brand.css` keyed to the `--ratio` variable
the gallery already puts on each image wrapper, so it needs no per-product
setting and no second product template.

### Variants and price

The Toronto trip carries three options, matching the live site: Package Type
(flight or land), Occupancy (single or double) and Payment (pay in full or a
non-refundable deposit). That last one changes what the headline price should
be: a deposit is the cheapest variant, so a "From" price reads as $500 for a
$3,099 trip. The `trip-price` block therefore takes a **Price shown** setting.
Cards use the lowest price, the trip page uses the selected variant.

Blocks that show variant-specific content have to follow the picker themselves.
Horizon morphs only the variant picker and leaves everything else to listen for
the product select event, so `assets/variant-refresh.js` does that swap
generically: wrap the block's markup in `<variant-refresh
data-block-id="{{ block.id }}">` and it re-renders. Both `trip-price` and
`pay-later` use it.

### Buy now, pay later

The `pay-later` block draws a payment pill, a decal and the instalment amount
worked out from the selected variant. **It is a demo placeholder and takes no
payment.** The real button is installed by the provider's own Shopify app,
which renders it from the cart and handles approval and settlement. Replace or
remove this block before launch.
