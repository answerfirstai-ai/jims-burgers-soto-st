#!/usr/bin/env python3
"""Builds the static site (English + Spanish) from src/. Standard library only.

Everything that changes after launch lives in two files:
  src/site.json   hours, phone, prices, rating, links, domain
  src/i18n.json   every sentence, in English and Spanish (and the FAQ)

  python3 scripts/build.py                        rebuild all pages
  python3 scripts/build.py --check                exit 1 if built files are out of date
  python3 scripts/build.py --touch                set "updated" to today, then rebuild
  python3 scripts/build.py --domain example.com   move to a custom domain (writes CNAME), then rebuild
  python3 scripts/build.py --github-pages         go back to the github.io address, then rebuild

The output is plain static files, served by GitHub Pages exactly as before.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
TOKEN = re.compile(r'\{\{(@?[A-Za-z0-9_]+)\}\}')

# (page key, language, folder under the site root, template)
PAGES = [
    ('home', 'en', '', 'index.template.html'),
    ('home', 'es', 'es', 'index.template.html'),
    ('order', 'en', 'order', 'order.template.html'),
    ('order', 'es', 'es/order', 'order.template.html'),
    ('privacy', 'en', 'privacy', 'privacy.template.html'),
    ('privacy', 'es', 'es/privacy', 'privacy.template.html'),
]
LANG_TAG = {'en': 'en-US', 'es': 'es-US'}


def load():
    site = json.loads((SRC / 'site.json').read_text(encoding='utf-8'))
    i18n = json.loads((SRC / 'i18n.json').read_text(encoding='utf-8'))
    return site, i18n


def render(tpl, ctx):
    def sub(m):
        k = m.group(1)
        if k not in ctx:
            raise KeyError(f'unknown placeholder {{{{{k}}}}}')
        return ctx[k]
    for _ in range(8):
        new = TOKEN.sub(sub, tpl)
        if new == tpl:
            return new
        tpl = new
    raise RuntimeError('placeholders keep expanding; check for a loop')


def esc(s):
    return html.escape(s, quote=False)


def page_dir(d):
    return d or '.'


def rel_url(from_dir, to_dir):
    r = os.path.relpath(page_dir(to_dir), start=page_dir(from_dir))
    return './' if r == '.' else r.replace(os.sep, '/') + '/'


def path_of(d):
    return '/' + (d + '/' if d else '')


def price_text(prices, lang):
    if not prices:
        return None
    if len(prices) == 1 and not prices[0].get('en'):
        return '$' + prices[0]['amt']
    return ' &middot; '.join(f"{esc(p[lang])} ${p['amt']}" for p in prices)


def menu_html(site, lang, strings):
    tilts = ['-0.8', '0.7', '-0.5', '0.9']
    out = []
    for gi, g in enumerate(site['menu']):
        lis = []
        for it in g['items']:
            name = esc(it[lang])
            if lang == 'es' and it['es'] != it['en']:
                name += f' <span class="bn">({esc(it["en"])})</span>'
            if it.get('desc'):
                name += f'<span class="ds">{esc(it["desc"][lang])}</span>'
            pt = price_text(it['prices'], lang)
            pr = f'<span class="pr">{pt}</span>' if pt else f'<span class="pr ask">{strings["ask"]}</span>'
            lis.append(f'            <li><span class="it">{name}</span>{pr}</li>')
        note = f'\n          <p class="combo">{g["note"][lang]}</p>' if g.get('note') else ''
        out.append(
            f'        <div class="sheet rv pop" style="--t:{tilts[gi % 4]}deg;--d:{gi * 90}ms">\n'
            f'          <h3>{esc(g["title"][lang])}</h3>\n'
            f'          <ul class="rl">\n' + '\n'.join(lis) + f'\n          </ul>{note}\n        </div>')
    return '\n'.join(out)


def apps_html(site, lang, style):
    out = []
    for i, a in enumerate(site['apps']):
        if style == 'index':
            attr = 'class="app rv"' + (f' style="--d:{70 * i}ms"' if i else '')
        else:
            attr = 'class="app"'
        out.append(f'      <a {attr} href="{a["url"]}" target="_blank" rel="noopener">{esc(a["name"][lang])} <small>{esc(a["small"][lang])}</small></a>')
    return '\n'.join(out)


def faq_html(i18n, lang):
    out = []
    for i, f in enumerate(i18n[lang]['faq']):
        style = f' style="--d:{50 * i}ms"' if i else ''
        out.append(f'      <details class="qa rv"{style}><summary>{f["q"]}</summary><p>{f["a"]}</p></details>')
    return '\n'.join(out)


def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s)


def jsonld(kind, site, i18n, lang, ctx, canonical, alt_urls):
    base = ctx['base']
    site_id, rest_id = base + '/#website', base + '/#restaurant'
    modified = site['updated']
    page = {
        '@type': 'WebPage', '@id': canonical + '#webpage', 'url': canonical, 'name': ctx['title'],
        'isPartOf': {'@id': site_id}, 'inLanguage': LANG_TAG[lang],
    }
    if kind == 'home':
        page.update({
            'about': {'@id': rest_id},
            'primaryImageOfPage': {'@type': 'ImageObject', 'url': base + '/assets/og.jpg', 'width': 1200, 'height': 630},
            'datePublished': site['published'], 'dateModified': modified,
        })
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        menu = {'@type': 'Menu', '@id': canonical + '#menu', 'name': render(i18n[lang]['strings']['ld_menu_name'], ctx), 'inLanguage': LANG_TAG[lang], 'hasMenuSection': []}
        for g in site['menu']:
            items = []
            for it in g['items']:
                node = {'@type': 'MenuItem', 'name': it[lang]}
                if it.get('desc'):
                    node['description'] = it['desc'][lang]
                offers = []
                for p in it['prices']:
                    o = {'@type': 'Offer', 'price': p['amt'], 'priceCurrency': 'USD'}
                    if p.get('en'):
                        o['name'] = p[lang]
                    offers.append(o)
                if offers:
                    node['offers'] = offers[0] if len(offers) == 1 else offers
                items.append(node)
            menu['hasMenuSection'].append({'@type': 'MenuSection', 'name': g['title'][lang], 'hasMenuItem': items})
        faq = {'@type': 'FAQPage', '@id': canonical + '#faq', 'inLanguage': LANG_TAG[lang], 'mainEntity': [
            {'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': strip_tags(render(f['a'], ctx))}}
            for f in i18n[lang]['faq']]}
        restaurant = {
            '@type': ['Restaurant', 'FastFoodRestaurant'], '@id': rest_id, 'name': site['name'], 'url': base + '/',
            'description': render(i18n[lang]['strings']['ld_desc'], ctx),
            'image': [base + '/assets/' + n for n in ['og.jpg', 'burger.webp', 'chicken.webp', 'fries-pastrami.webp']],
            'logo': base + '/assets/logo.png', 'telephone': site['tel_dash'], 'priceRange': site['price_range'],
            'servesCuisine': ['Hamburgers', 'American', 'Fast food'],
            'address': {'@type': 'PostalAddress', 'streetAddress': site['address']['street'], 'addressLocality': site['address']['city'],
                        'addressRegion': site['address']['region'], 'postalCode': site['address']['zip'], 'addressCountry': 'US'},
            'geo': {'@type': 'GeoCoordinates', 'latitude': float(site['geo']['lat']), 'longitude': float(site['geo']['lng'])},
            'hasMap': site['links']['directions'],
            'openingHoursSpecification': [{'@type': 'OpeningHoursSpecification', 'dayOfWeek': days, 'opens': site['hours']['opens'], 'closes': site['hours']['closes']}],
            'sameAs': [site['links']['listing']] + [a['url'] for a in site['apps'] if 'order.online' not in a['url']],
            'hasMenu': {'@id': canonical + '#menu'},
            'potentialAction': [{'@type': 'OrderAction', 'target': {'@type': 'EntryPoint', 'urlTemplate': base + path_of('order') if lang == 'en' else base + path_of('es/order'),
                                 'actionPlatform': ['http://schema.org/DesktopWebPlatform', 'http://schema.org/MobileWebPlatform']}}],
        }
        website = {'@type': 'WebSite', '@id': site_id, 'url': base + '/', 'name': site['name'], 'inLanguage': ['en-US', 'es-US'], 'publisher': {'@id': rest_id}}
        graph = [website, page, restaurant, menu, faq]
    else:
        home_url = base + path_of('' if lang == 'en' else 'es')
        label = i18n[lang]['strings']['breadcrumb_order'] if kind == 'order' else i18n[lang]['strings']['nav_privacy']
        page['about'] = {'@id': rest_id}
        graph = [page, {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': site['name'], 'item': home_url},
            {'@type': 'ListItem', 'position': 2, 'name': label, 'item': canonical}]}]
    body = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, indent=1)
    return '<script type="application/ld+json">\n' + body + '\n</script>'


def build_all(site, i18n):
    """Returns {relative output path: text}."""
    base = site['base_url'].rstrip('/')
    base_path = urlparse(base).path.rstrip('/')
    out = {}
    a = site['address']
    addr_line = f"{a['street']}, {a['city']}, {a['region']} {a['zip']}"
    for key, lang, folder, tpl_name in PAGES:
        alt_lang = 'es' if lang == 'en' else 'en'
        alt_folder = ('' if key == 'home' else key) if alt_lang == 'en' else ('es' if key == 'home' else 'es/' + key)
        if key == 'home' and lang == 'en':
            alt_folder = 'es'
        depth = len([p for p in folder.split('/') if p])
        strings = dict(i18n[lang]['strings'])
        alt_strings = i18n[alt_lang]['strings']
        alt_url = rel_url(folder, alt_folder)
        canonical = base + path_of(folder)
        urls = {'en': base + path_of(folder if lang == 'en' else alt_folder), 'es': base + path_of(folder if lang == 'es' else alt_folder)}
        email = site['privacy'].get('email', '').strip()
        ctx = {
            'name': site['name'], 'lang': lang, 'root': '../' * depth, 'home': '' if key == 'home' else '../', 'privacy_rel': '../privacy/',
            'base': base, 'base_path': base_path, 'canonical': canonical,
            'phone': site['phone'], 'tel': site['tel'], 'tel_dash': site['tel_dash'],
            'phone_link': f'<a href="tel:{site["tel"]}">{site["phone"]}</a>',
            'street': a['street'], 'city': a['city'], 'region': a['region'], 'zip': a['zip'], 'addr_line': addr_line,
            'addr_q': addr_line.replace(' ', '+'), 'lat': site['geo']['lat'], 'lng': site['geo']['lng'],
            'hours': site['hours'][lang], 'h_open': str(site['hours']['open']), 'h_close': str(site['hours']['close']),
            'open_label': site['hours']['open_label'], 'close_label': site['hours']['close_label'],
            'rating': site['rating']['value'], 'review_count': site['rating']['count'], 'price_range': site['price_range'],
            'combo_add': site['combo_add'], 'jr_combo_add': site['jr_combo_add'],
            'dir_url': site['links']['directions'], 'apple_url': site['links']['apple'], 'metro_url': site['links']['metro'], 'listing_url': site['links']['listing'],
            'privacy_updated': site['privacy']['updated'] if lang == 'en' else site['privacy']['updated_es'],
            'privacy_email': email, 'privacy_email_html': strings['pv_contact_email'] if email else '',
        }
        ctx.update(strings)
        # page-specific head text
        ctx['title'] = strings[f'{key}_title']
        ctx['meta_desc'] = strings[f'{key}_meta_desc']
        ctx['og_title'] = strings[f'{key}_og_title']
        ctx['og_desc'] = strings[f'{key}_og_desc']
        ctx['tw_desc'] = strings[f'{key}_tw_desc']
        # language link and alternates
        ctx['@lang_link'] = (f'<a class="lang" id="lang-toggle" href="{alt_url}" hreflang="{alt_lang}" lang="{alt_lang}" data-base="{alt_url}" '
                             f'aria-label="{alt_strings["lang_aria"]}">{alt_strings["lang_label"]}</a>')
        ctx['@alternates'] = '\n'.join([
            f'<link rel="alternate" hreflang="en" href="{urls["en"]}">',
            f'<link rel="alternate" hreflang="es" href="{urls["es"]}">',
            f'<link rel="alternate" hreflang="x-default" href="{urls["en"]}">'])
        ctx['@apps_index'] = apps_html(site, lang, 'index')
        ctx['@apps_order'] = apps_html(site, lang, 'order')
        ctx['@menu_groups'] = menu_html(site, lang, strings)
        ctx['@faq_html'] = faq_html(i18n, lang)
        ctx['@jsonld'] = jsonld(key, site, i18n, lang, ctx, canonical, urls)
        text = render((SRC / tpl_name).read_text(encoding='utf-8'), ctx)
        out[(folder + '/' if folder else '') + 'index.html'] = text

    # 404 (one bilingual page)
    ctx404 = {'name': site['name'], 'base_path': base_path}
    for k in ('nf_h1', 'nf_p', 'nf_btn'):
        ctx404[k + '_en'] = i18n['en']['strings'][k]
        ctx404[k + '_es'] = i18n['es']['strings'][k]
    out['404.html'] = render((SRC / '404.template.html').read_text(encoding='utf-8'), ctx404)

    # robots, sitemap, llms.txt
    out['robots.txt'] = f'User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n'
    mod = site['updated']
    en_s, es_s = i18n['en']['strings'], i18n['es']['strings']
    sctx = {'name': site['name'], 'street': a['street']}
    images = [('burger.webp', 'alt_burger'), ('chicken.webp', 'alt_chicken'), ('fries-pastrami.webp', 'alt_fries_pastrami'), ('menu-screen.webp', 'cap_sitemap_menu')]
    pairs = [('', 'es', 1.0), ('order', 'es/order', 0.9), ('privacy', 'es/privacy', 0.3)]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for en_dir, es_dir, prio in pairs:
        for lang, d in (('en', en_dir), ('es', es_dir)):
            xml.append('  <url>')
            xml.append(f'    <loc>{base}{path_of(d)}</loc>')
            xml.append(f'    <lastmod>{mod}</lastmod>')
            xml.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{base}{path_of(en_dir)}"/>')
            xml.append(f'    <xhtml:link rel="alternate" hreflang="es" href="{base}{path_of(es_dir)}"/>')
            xml.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{base}{path_of(en_dir)}"/>')
            xml.append(f'    <changefreq>monthly</changefreq>')
            xml.append(f'    <priority>{prio}</priority>')
            if en_dir == '':
                for fn, ck in images:
                    cap = render(i18n[lang]['strings'][ck], sctx)
                    xml.append(f'    <image:image><image:loc>{base}/assets/{fn}</image:loc><image:caption>{html.escape(cap)}</image:caption></image:image>')
            xml.append('  </url>')
    xml.append('</urlset>')
    out['sitemap.xml'] = '\n'.join(xml) + '\n'

    h = site['hours']
    menu_lines = []
    for g in site['menu']:
        menu_lines.append(f"- {g['title']['en']}: " + ', '.join(i['en'].lower() if i['en'][0].islower() or i['en'] != 'D.U.I. fries' else i['en'] for i in g['items']))
    llms = f"""# {site['name']}

> Charbroiled quarter-pound burgers, chili cheese fries and onion rings at {addr_line} (Boyle Heights). Dine-in, takeout and delivery through apps. Open every day, {h['en']}.

## Facts
- Name: {site['name']} (hamburger restaurant)
- Address: {addr_line}
- Phone: {site['phone']}
- Hours: Monday to Sunday, {h['en']}
- Price: {site['price_range']} per person, as reported by diners
- Payment: a charge applies to credit card purchases
- Google rating: {site['rating']['value']} from {site['rating']['count']} Google reviews
- Languages: this website is in English and Spanish
- Directions: {site['links']['directions']}

## Order
- Order page: {base}/order/
""" + ''.join(f"- {a_['name']['en']}: {a_['url']}\n" for a_ in site['apps'] if 'order.online' not in a_['url']) + f"""
## Menu (names only; prices are on the website and can change, call to confirm)
""" + '\n'.join(menu_lines) + f"""

## Pages
- Home (English): {base}/
- Inicio (Español): {base}/es/
- Order: {base}/order/
- Pedir: {base}/es/order/
- Privacy: {base}/privacy/
- Privacidad: {base}/es/privacy/
"""
    out['llms.txt'] = llms
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--touch', action='store_true')
    ap.add_argument('--domain')
    ap.add_argument('--github-pages', action='store_true')
    args = ap.parse_args()

    site, i18n = load()
    changed_site = False
    if args.touch:
        site['updated'] = datetime.date.today().isoformat()
        changed_site = True
    if args.domain:
        host = args.domain.strip().lower().replace('https://', '').replace('http://', '').strip('/')
        site['base_url'] = 'https://' + host
        changed_site = True
    if args.github_pages:
        site['base_url'] = site['github_pages_url']
        changed_site = True
    if changed_site and not args.check:
        (SRC / 'site.json').write_text(json.dumps(site, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    out = build_all(site, i18n)
    base = site['base_url'].rstrip('/')
    cname = ROOT / 'CNAME'
    host = urlparse(base).netloc
    want_cname = host if not urlparse(base).path.rstrip('/') else None

    stale = []
    for rel, text in out.items():
        p = ROOT / rel
        if args.check:
            if not p.exists() or p.read_text(encoding='utf-8') != text:
                stale.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8')
    if args.check:
        cur = cname.read_text().strip() if cname.exists() else None
        if cur != want_cname:
            stale.append('CNAME')
        if stale:
            print('Out of date (run: python3 scripts/build.py):', ', '.join(stale))
            sys.exit(1)
        print('Built files are up to date.')
        return
    if want_cname:
        cname.write_text(want_cname + '\n', encoding='utf-8')
    elif cname.exists():
        cname.unlink()
    print(f'Built {len(out)} files for {base}')
    if args.domain:
        print(f'''
Next steps for {host}:
  1. At the domain registrar, add four A records for @ pointing to 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
     and a CNAME record for www pointing to <github-username>.github.io
  2. Repo Settings > Pages > Custom domain: {host}, then tick Enforce HTTPS once it is available.
  3. Commit and push, then in Google Search Console add the new domain and submit {base}/sitemap.xml
''')


if __name__ == '__main__':
    main()
