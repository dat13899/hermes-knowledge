# Playwright-core E2E Skeleton for Web Games (Windows/git-bash)

Proven against VẬN RUNE. Plain JS (`.mjs`) — **no TypeScript annotations** (Node runs it directly).

## Setup

```js
import { chromium } from 'playwright-core';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// CHECK THIS PATH — version dir changes!
const CHROME = 'C:/Users/datel/AppData/Local/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-win64/chrome-headless-shell.exe';
```

Find the real version dir: `ls /c/Users/datel/AppData/Local/ms-playwright/` (chromium_headless_shell-<ver>/).

## Tiny static server over dist/ (SPA-aware)

```js
const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.png': 'image/png', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml',
};

function startServer() {
  return new Promise(resolve => {
    const server = http.createServer((req, res) => {
      let urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
      if (urlPath === '/') urlPath = '/index.html';
      const filePath = path.join(dist, urlPath);
      if (!filePath.startsWith(dist)) { res.writeHead(403); res.end(); return; }
      fs.readFile(filePath, (err, data) => {
        if (err) {
          fs.readFile(path.join(dist, 'index.html'), (e2, idx) => {
            if (e2) { res.writeHead(404); res.end('not found'); return; }
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(idx);
          });
          return;
        }
        const ext = path.extname(filePath).toLowerCase();
        res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
        res.end(data);
      });
    });
    server.listen(PORT, () => resolve(server));
  });
}
```

## Core test harness

```js
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage({ viewport: { width: 390, height: 844 } }); // iPhone-ish
const errors = [];
page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
page.on('pageerror', err => errors.push('PAGEERROR: ' + err.message));
page.on('requestfailed', req => errors.push('REQFAIL: ' + req.url() + ' ' + (req.failure()?.errorText || '')));

const pass = (name, ok, extra = '') => {
  console.log(`${ok ? '✅' : '❌'} ${name}${extra ? ' — ' + extra : ''}`);
  if (!ok) process.exitCode = 1;
};
```

## Auto-play loop (exercises full death/victory flow)

```js
let endSeen = false;
const startTime = Date.now();
while (Date.now() - startTime < 30000 && !endSeen) {
  const runeCount = await page.locator('.rune-card').count();
  if (runeCount === 3) {
    await page.locator('.rune-card').first().click();
    await page.waitForTimeout(300);
  }
  if (await page.locator('.end-title').count()) { endSeen = true; break; }
  await page.waitForTimeout(200);
}
```

## Check list

1. Home loads, title correct
2. Start run → HUD visible
3. Picker appears (poll up to 20s), picking hides it
4. Game progresses (score/HUD changes over 3s)
5. Death/victory flow → end screen → stats → save persists after reload
6. **Zero console/page/request errors**
7. Run against BOTH local static server AND live public URL (tunnel)
8. Screenshots → `vision_analyze` for visual bugs (fonts, duplicated elements, layout)

## Pitfalls

- `.mjs` = plain JS. `const errors: string[] = []` throws SyntaxError — drop annotations.
- Poll with `waitForTimeout` loops instead of `waitForSelector` when timing is game-dependent.
- `taskkill /F /PID <pid>` in git-bash (double-slash `//PID` is invalid).
- Headless shell ignores system Chrome — always pass `executablePath`.
