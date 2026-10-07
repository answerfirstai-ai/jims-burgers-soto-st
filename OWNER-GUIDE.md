# Jim's Burgers site: owner guide

Live site: https://answerfirstai-ai.github.io/jims-burgers-soto-st/
Ad landing page for delivery and pickup: https://answerfirstai-ai.github.io/jims-burgers-soto-st/order/

## 1. Turn on tracking (5 minutes)
Open `assets/track.js` and paste your IDs into the `CFG` block at the top. Nothing loads until an ID is present.

| Field | Looks like | Use |
|---|---|---|
| `gtm` | GTM-XXXXXXX | Google Tag Manager (best option, maps every event below) |
| `ga4` | G-XXXXXXXXXX | Google Analytics 4 |
| `googleAds` | AW-1234567890 | Google Ads conversions |
| `metaPixel` | 15 digits | Facebook and Instagram ads |
| `adsLabels` | {order: "...", call: "...", directions: "..."} | Google Ads conversion labels |

Events the site sends (to `dataLayer`, GA4 and Meta): `order_open`, `order_click` (with `provider`), `call_click`, `directions_click`, `reviews_click`, `photo_zoom`, `faq_open`, `scroll_depth` (25/50/75/100). Every event carries the visit's `utm_*`, `gclid` and `fbclid` values.
Meta mapping: order_click = InitiateCheckout, call_click = Contact, directions_click = FindLocation.

Privacy: once tracking is on, add a notice and an opt-out for California visitors (CCPA/CPRA).

## 2. Ads
- Delivery and pickup campaigns: send traffic to `/order/`. It has one job: pick an app or call.
- Brand and menu campaigns: send traffic to the home page.
- Tag every ad URL, for example `/order/?utm_source=google&utm_medium=cpc&utm_campaign=delivery&utm_term={keyword}`.
- Call-only and call extensions: use (323) 269-9732. Tap-to-call clicks are tracked as `call_click`.
- Order clicks go to DoorDash, Uber Eats, Postmates, Caviar or Jim's DoorDash order page. Those sites own the checkout, so purchases there cannot be tracked from this site. `order_click` is the conversion we can measure.

## 3. Search and local visibility
1. Google Business Profile: the listing still says "Add website". Claim it, then add https://answerfirstai-ai.github.io/jims-burgers-soto-st/ (or the custom domain) as the website and the `/order/` page as the order link. Confirm hours are 8 AM to 9 PM every day. Reply to reviews.
2. Google Search Console: add the site, verify, submit `sitemap.xml`. Do the same in Bing Webmaster Tools (it also feeds Apple Maps, Copilot and ChatGPT search).
3. Custom domain (recommended before spending on ads): buy something like jimsburgerssoto.com, point it at GitHub Pages (repo Settings, Pages, Custom domain). Then update the domain in `index.html`, `order/index.html`, `sitemap.xml`, `robots.txt` and `llms.txt`.
4. Keep these identical everywhere (site, Google, DoorDash, Yelp, Facebook): Jim's Burgers, 915 S Soto St, Los Angeles, CA 90023, (323) 269-9732.
5. Ask happy customers for Google reviews. The home page links to the listing.

## 4. When things change
- Hours: edit the three places in `index.html` (hero chip logic, schema, visit section), `order/index.html`, and `llms.txt`.
- Menu photos and prices: replace `assets/menu-*.webp`. Prices appear only inside those photos.
