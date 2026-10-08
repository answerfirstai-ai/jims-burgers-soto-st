# Jim's Burgers site: maintenance guide

The site is static (GitHub Pages). Pages are generated from `src/` by one script, so a change is made once and appears in both English and Spanish.

## How it is organized
- `src/site.json`: phone, address, hours, rating, app links, **menu and prices**.
- `src/i18n.json`: all English and Spanish text, including the FAQ and the privacy policy.
- `src/*.template.html`: page layouts (look and feel).
- `scripts/build.py`: builds the pages. `scripts/check.py`: verifies them.
- Built files (`index.html`, `es/`, `order/`, `privacy/`, `sitemap.xml`, `llms.txt`, `robots.txt`, `404.html`) are committed. Never edit them by hand; they are overwritten.

## Routine change (about 5 minutes)
1. Edit `src/site.json` (price, hours, link) or `src/i18n.json` (wording; change both `en` and `es`).
2. `python3 scripts/build.py --touch` (also refreshes the "updated" dates).
3. `python3 scripts/check.py` must print "All checks passed."
4. Commit and push to `main`. The site updates in about a minute.

## Go live on the client's domain
`python3 scripts/build.py --domain https://www.theirdomain.com --touch`, then commit and push. This rewrites canonical links, hreflang, sitemap, schema and `CNAME`. At the registrar, point DNS to GitHub Pages, then set the custom domain in repo Settings, Pages, and tick Enforce HTTPS. To go back to the GitHub address: `--github-pages`.

## Tracking and ads
- Paste IDs into the `CFG` block of `assets/track.js` (`gtm`, `ga4`, `googleAds`, `metaPixel`, `adsLabels`). Nothing loads until an ID is present.
- Events: `order_open`, `order_click` (with `provider`), `call_click`, `directions_click`, `reviews_click`, `photo_zoom`, `faq_open`, `scroll_depth`, `language_switch`. Each carries `lang` and any `utm_*`/`gclid`/`fbclid`.
- Visitors can opt out on the privacy page; the Global Privacy Control signal is honored. Both stop all tracking.
- Before ads run: add a contact email in `privacy.email` in `src/site.json`, have the owner or a lawyer review the policy, and update its text in `src/i18n.json` if you add other tools.
- Send delivery/pickup ads to `/order/` (or `/es/order/`), tagged with UTMs. Orders happen in the delivery apps, so `order_click` is the measurable conversion.

## Monthly checklist
- Open both languages on a phone; tap Call, Directions and each app link.
- Confirm hours and prices still match the restaurant and Google Business Profile.
- Run `python3 scripts/check.py`.
- Reply to new Google reviews; check Search Console for errors.
- Re-test the hero video plays; keep `hero-720.mp4` under a few MB.
- Quarterly: refresh review count/rating in `src/site.json` and the date in the privacy policy.

## Keep consistent everywhere
Jim's Burgers, 915 S Soto St, Los Angeles, CA 90023, (323) 269-9732 on the site, Google, DoorDash, Yelp and Facebook.
