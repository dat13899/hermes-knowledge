/* Verify daily idea — dùng cho mọi ngày. Chạy: node verify-daily.js <DDMMYYYY>
   Copy vào ~/daily-test/ (nơi có playwright-core + chromium).
   Trả về exit 0 nếu pass hết, 1 nếu fail. In ra từng check. */
const { chromium } = require('playwright-core');
const CHROME = 'C:/Users/datel/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe';
const DAY = process.argv[2];
if (!DAY || !/^\d{8}$/.test(DAY)) { console.error('Usage: node verify-daily.js <DDMMYYYY>'); process.exit(2); }
const BASE = 'http://localhost:3050/' + DAY + '/';

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const allErrors = [], all404 = [];
  let pass = 0, fail = 0;
  const check = (name, cond) => { cond ? pass++ : (fail++, console.log('FAIL: ' + name)); };

  // ── Mobile 375×667 ──
  const ctxM = await browser.newContext({ viewport: { width: 375, height: 667 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const pm = await ctxM.newPage();
  pm.on('console', m => { if (m.type() === 'error') allErrors.push('[M] ' + m.text()); });
  pm.on('pageerror', e => allErrors.push('[M] ' + e.message));
  pm.on('response', r => { if (r.status() === 404) all404.push(r.url()); });
  await pm.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
  await pm.waitForTimeout(500);
  check('mobile: no horizontal scroll', await pm.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth === 0));
  // nút hiển thị đều ≥44px
  const mSmall = await pm.evaluate(() => [...document.querySelectorAll('button')].filter(b => { const r = b.getBoundingClientRect(); return r.height > 0 && (r.height < 44 || r.width < 44); }).length);
  check('mobile: no small visible buttons (<44px)', mSmall === 0);
  await pm.screenshot({ path: __dirname + '/shot-' + DAY + '-mobile.png', fullPage: true });

  // ── Desktop 1280×800 ──
  const ctxD = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const pd = await ctxD.newPage();
  pd.on('console', m => { if (m.type() === 'error') allErrors.push('[D] ' + m.text()); });
  pd.on('pageerror', e => allErrors.push('[D] ' + e.message));
  pd.on('response', r => { if (r.status() === 404) all404.push(r.url()); });
  await pd.goto(BASE, { waitUntil: 'networkidle', timeout: 20000 });
  await pd.waitForTimeout(400);
  check('desktop: no horizontal scroll', await pd.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth === 0));
  const dSmall = await pd.evaluate(() => [...document.querySelectorAll('button')].filter(b => { const r = b.getBoundingClientRect(); return r.height > 0 && (r.height < 44 || r.width < 44); }).length);
  check('desktop: no small visible buttons (<44px)', dSmall === 0);
  await pd.screenshot({ path: __dirname + '/shot-' + DAY + '-desktop.png' });

  check('ZERO JS console/page errors', allErrors.length === 0);
  check('ZERO 404s', all404.length === 0);

  await browser.close();
  console.log('RESULT ' + DAY + ': pass=' + pass + ' fail=' + fail);
  if (allErrors.length) { console.log('JS ERRORS:'); allErrors.forEach(e => console.log('  ' + e)); }
  if (all404.length) { console.log('404:'); all404.forEach(u => console.log('  ' + u)); }
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('FATAL', e); process.exit(2); });
