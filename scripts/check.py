#!/usr/bin/env python3
"""Pre-publish check: python3 scripts/check.py  (exit 1 on any problem)."""
import glob, json, os, re, subprocess, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(root)
bad = []
r = subprocess.run([sys.executable, '-I', 'scripts/build.py', '--check'], capture_output=True, text=True)
if r.returncode: bad.append('built files are stale: run python3 scripts/build.py\n' + r.stdout + r.stderr)
pages = [f for f in glob.glob('**/index.html', recursive=True) if not f.startswith('src/')] + ['404.html']
alltxt = ''
for f in pages + ['sitemap.xml', 'llms.txt', 'robots.txt', 'manifest.webmanifest', 'assets/track.js']:
    t = open(f, encoding='utf-8').read(); alltxt += t
    if '{{' in t and f != 'assets/track.js': bad.append(f + ': unfilled {{token}}')
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try: json.loads(m)
        except Exception as e: bad.append(f + ': bad JSON-LD ' + str(e))
for a in set(re.findall(r'assets/([\w.\-]+)', alltxt)):
    if not os.path.exists('assets/' + a): bad.append('missing asset ' + a)
ids = lambda f: sorted(re.findall(r'\bid="([^"]+)"', open(f, encoding='utf-8').read()))
for p in ['index.html', 'order/index.html', 'privacy/index.html']:
    if ids(p) != ids('es/' + p): bad.append('EN/ES id mismatch: ' + p)
print('\n'.join(bad) if bad else 'All checks passed.'); sys.exit(1 if bad else 0)
