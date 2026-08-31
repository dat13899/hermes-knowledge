// Verify render thực sự của 1 ngày trên daily.btdat.io.vn — đếm pixel sáng, không tin screenshot bytes.
// Dùng cho Canvas 2D (getImageData) và WebGL (readPixels) sau khi pivot khỏi WebGL đen màn hình.
// Usage: node verify-render.js <DDMMYYYY> [port]
// Yêu cầu: playwright-core trong ~/daily-test/node_modules; Chrome full chromium-1228.
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const day = process.argv[2];
  if (!day) { console.error('thiếu mã ngày DDMMYYYY'); process.exit(1); }
  const port = process.argv[3] || '3050';
  const url = `http://localhost:${port}/${day}/?v=${Date.now()}`;   // cache-bust!
  const chrome = 'C:/Users/datel/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe';
  const browser = await chromium.launch({
    executablePath: chrome,
    headless: true,
    args: ['--no-sandbox', '--enable-unsafe-swiftshader']   // SwiftShader flag cho WebGL trong headless
  });
  const page = await browser.newPage({ viewport: { width: 375, height: 667 } });
  const errs = [];
  page.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !m.text().includes('404')) errs.push('CONSOLE: ' + m.text().slice(0, 150)); });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(3500);   // đủ cho fade-in / boot

  // Đọc pixel: ưu tiên 2d context (fallback webgl readPixels)
  const r = await page.evaluate(() => {
    const c = document.getElementById('gl') || document.querySelector('canvas');
    if (!c) return { err: 'no canvas' };
    const ctx2 = c.getContext('2d');
    if (ctx2) {
      const d = ctx2.getImageData(0, 0, c.width, c.height).data;
      let lit = 0, maxV = 0;
      for (let i = 0; i < d.length; i += 4) {
        const v = d[i] + d[i+1] + d[i+2];
        if (v > 30) { lit++; if (v > maxV) maxV = v; }
      }
      return { mode: '2d', lit, maxV, total: d.length/4 };
    }
    const gl = c.getContext('webgl');
    if (gl) {
      const w = c.width, h = c.height;
      const buf = new Uint8Array(w*h*4);
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, buf);
      let lit = 0, maxV = 0;
      for (let i = 0; i < buf.length; i += 4) {
        const v = buf[i] + buf[i+1] + buf[i+2];
        if (v > 30) { lit++; if (v > maxV) maxV = v; }
      }
      return { mode: 'webgl', lit, maxV, total: w*h, lost: gl.isContextLost() };
    }
    return { err: 'no 2d/webgl context' };
  });

  console.log('RENDER:', JSON.stringify(r));
  console.log('ERRS:', errs.join(' | ') || '(none)');
  const ok = !r.err && r.lit > 500 && errs.length === 0;
  console.log(ok ? '✅ RENDER PASS' : '❌ RENDER FAIL');
  await browser.close();
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error('FATAL', e); process.exit(1); });
