#!/usr/bin/env python3
"""Review HTML + CSS for correctness & responsive layout.
Usage: python review.py [path]
Default: ~/service-dashboard/public/
"""
import os, re, sys, json, subprocess, urllib.request, html.parser

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/service-dashboard/public')
SERVER = 'http://localhost:3000'
LIVE = 'https://btdat.io.vn'

errors = []
warnings = []

def e(msg, file=None): errors.append(f'  ✖ {msg}' + (f' ({file})' if file else ''))
def w(msg, file=None): warnings.append(f'  ⚠ {msg}' + (f' ({file})' if file else ''))

# ── 1. HTML files exist & parse ──
html_files = []
for f in ['index.html', 'dashboard.html', 'documents.html']:
    p = os.path.join(ROOT, f)
    if not os.path.exists(p): e(f'{f} not found')
    else: html_files.append(p)

# ── 2. Check each HTML ──
for fp in html_files:
    name = os.path.basename(fp)
    raw = open(fp, encoding='utf-8').read()

    # 2a. Forbidden patterns
    for pat, label in [
        ('skip-link', 'skip-link element'),
        ('kb-overlay', 'old kb-overlay class'),
        ('class="navbar"', 'missing navbar'),
    ]:
        if pat == 'class="navbar"':
            if '<nav ' not in raw: e(f'Missing <nav> element', name)
        else:
            if pat in raw: e(f'Contains "{label}"', name)

    # 2b. Viewport meta
    if '<meta name="viewport"' not in raw:
        e('Missing viewport meta', name)

    # 2c. Inter font
    if 'Inter' not in raw:
        w('Missing Inter font', name)

    # 2d. Theme script
    if 'theme.js' not in raw:
        w('Missing theme.js', name)

    # 2e. DOCTYPE
    if not raw.startswith('<!DOCTYPE html>'):
        e('Missing DOCTYPE', name)

    # 2f. Closing body + html
    if '</body>' not in raw: e('Missing </body>', name)
    if '</html>' not in raw: e('Missing </html>', name)

    # 2g. Hardcoded pixel widths (responsive red flags)
    px_matches = re.findall(r'width:\s*(\d+)px', raw)
    for val in px_matches:
        v = int(val)
        if v > 200:
            w(f'Hardcoded width: {v}px (use rem/%/flex)', name)

    # 2h. Unclosed tags check (basic)
    for tag in ['div', 'section', 'main', 'nav', 'footer', 'ul', 'ol']:
        opens = len(re.findall(f'<{tag}[ >]', raw))
        closes = len(re.findall(f'</{tag}>', raw))
        if opens != closes:
            e(f'<{tag}>: {opens} open, {closes} close', name)

# ── 3. CSS file ──
css_path = os.path.join(ROOT, 'assets', 'global.css')
if os.path.exists(css_path):
    css = open(css_path, encoding='utf-8').read()
    if '@media' not in css:
        w('No @media queries in global.css')
    if 'prefers-reduced-motion' not in css:
        w('Missing prefers-reduced-motion')
    if 'px' in css:
        # check if all px are small (borders, shadows) or large (layout breaks)
        big_px = re.findall(r'(\d+)px', css)
        for v in big_px:
            if int(v) > 100 and 'box-shadow' not in css.split(v+'px')[0][-50:]:
                w(f'Large px value ({v}px) in CSS — consider rem')

# ── 4. Server health ──
for name, url in [('local', SERVER), ('live', LIVE)]:
    try:
        r = urllib.request.urlopen(url + '/api/version', timeout=5)
        data = json.loads(r.read())
        print(f'  ✓ {name} server: v{data["version"]}, uptime {data.get("uptime", "?")}s')
    except Exception as ex:
        e(f'{name} server unreachable: {ex}')

# ── 5. Live page check ──
for page in ['/', '/dashboard', '/documents']:
    for url_base in [SERVER, LIVE]:
        try:
            r = urllib.request.urlopen(url_base + page, timeout=5)
            body = r.read().decode()
            ct = r.headers.get('Content-Type', '')
            if 'skip-link' in body:
                e(f'skip-link found on {page} via {url_base}')
            sz = len(body)
            status = '✓' if sz > 2000 else '✖ small'
            print(f'  {status} {url_base}{page} ({sz} bytes)')
        except Exception as ex:
            e(f'{url_base}{page} failed: {ex}')

# ── Summary ──
print()
if errors:
    print(f'\n✖ {len(errors)} ERRORS:')
    for l in errors: print(l)
else:
    print('\n✓ No errors')

if warnings:
    print(f'\n⚠ {len(warnings)} WARNINGS:')
    for l in warnings: print(l)
else:
    print('\n✓ No warnings')

sys.exit(1 if errors else 0)
