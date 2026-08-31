#!/usr/bin/env node
/**
 * verify-artifact.js — Structural verification for creative-iteration artifacts.
 *
 * Supports both single-file HTML and split JS (core.js → visuals.js → main.js).
 *
 * Usage:
 *   node scripts/verify-artifact.js [expectedModeCount] [http-url]
 *
 * Examples:
 *   node scripts/verify-artifact.js 12
 *   node scripts/verify-artifact.js 12 http://localhost:3000/hermes
 *
 * Checks:
 *   1. JS syntax via `new Function()` — catches ?.number errors, unmatched braces
 *   2. HTML tag balance (single-file mode only)
 *   3. SCENE_MODES mode count vs expected
 *   4. Loop wiring — update/draw calls present in main.js (split mode)
 *   5. HTTP 200 from live endpoint
 *   6. Exits with code 0 on pass, 1 on fail
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

const EXPECTED_MODES = parseInt(process.argv[2], 10) || 0;
const HTTP_URL = process.argv[3] || 'http://localhost:3000/hermes';

const BASE = process.cwd();
const HTML_PATH = path.join(BASE, 'public/hermes.html');
const JS_DIR  = path.join(BASE, 'public/hermes');
const SPLIT_FILES = ['hermes-core.js', 'hermes-visuals.js', 'hermes-main.js'];

let ok = true;
function check(pass, msg) {
  console.log(pass ? 'PASS' : 'FAIL', '—', msg);
  if (!pass) ok = false;
}

function readSafe(p) {
  try { return fs.readFileSync(p, 'utf8'); }
  catch { return null; }
}

// ─── Detect architecture ──────────────────────────────────────────────
const htmlContent = readSafe(HTML_PATH);
const hasHtml = !!htmlContent;
const hasSplit = SPLIT_FILES.every(f => !!readSafe(path.join(JS_DIR, f)));

console.log('=== Artifact Verification ===');
console.log(`Expected modes: ${EXPECTED_MODES}`);
if (hasHtml && hasSplit) console.log('Architecture: hybrid (HTML + split JS)');
else if (hasHtml) console.log('Architecture: single-file HTML');
else if (hasSplit) console.log('Architecture: split JS modules');
else console.log('Architecture: NONE FOUND');

// ─── 1. JS syntax ────────────────────────────────────────────────────
if (hasHtml) {
  const scriptMatch = htmlContent.match(/<script>([\s\S]*?)<\/script>/);
  if (scriptMatch) {
    try { new Function(scriptMatch[1]); check(true, 'HTML inline JS syntax'); }
    catch(e) { check(false, `HTML inline JS syntax: ${e.message}`); }
  } else {
    check(true, 'No inline <script> block (may be external-only)');
  }
}
if (hasSplit) {
  for (const f of SPLIT_FILES) {
    const code = readSafe(path.join(JS_DIR, f));
    if (!code) { check(false, `${f}: file not found`); continue; }
    try { new Function(code); check(true, `${f} syntax`); }
    catch(e) { check(false, `${f} syntax: ${e.message}`); }
  }
}

// ─── 2. HTML structure (single-file or hybrid) ────────────────────────
if (hasHtml) {
  check(htmlContent.length > 10240, `File size > 10KB (${(htmlContent.length/1024).toFixed(1)}KB)`);
  check(/<!DOCTYPE/i.test(htmlContent), 'Has DOCTYPE');
  check(/<\/html>/.test(htmlContent), 'Has </html>');
  check(/<\/body>/.test(htmlContent), 'Has </body>');

  const tags = ['div', 'span', 'button', 'canvas'];
  for (const tag of tags) {
    const openRe = new RegExp('<' + tag + '[\\s>]', 'g');
    const closeRe = new RegExp('</' + tag + '>', 'g');
    const open = (htmlContent.match(openRe) || []).length;
    const close = (htmlContent.match(closeRe) || []).length;
    if (Math.abs(open - close) > 5) {
      check(false, `Tag <${tag}>: ${open} open vs ${close} close (gap=${Math.abs(open-close)})`);
    }
  }
}

// ─── 3. Combine all code for pattern searches ─────────────────────────
const allCode = (hasHtml ? htmlContent : '') +
  SPLIT_FILES.map(f => readSafe(path.join(JS_DIR, f)) || '').join('\n');

const lines = allCode.split('\n');

// ─── 4. SCENE_MODES count ─────────────────────────────────────────────
const sceneModes = (allCode.match(/\{id:'[a-z]+'/g) || []).length;
if (EXPECTED_MODES > 0) {
  check(sceneModes === EXPECTED_MODES, `SCENE_MODES: found ${sceneModes} (expected ${EXPECTED_MODES})`);
} else {
  console.log(`Info: SCENE_MODES entries found: ${sceneModes} (no expected count provided)`);
}

// ─── 5. Mode buttons (HTML-only) ──────────────────────────────────────
if (hasHtml) {
  const modeBtns = (htmlContent.match(/class="mode-btn"/g) || []).length;
  if (EXPECTED_MODES > 0) {
    check(modeBtns === EXPECTED_MODES, `Mode buttons: found ${modeBtns} (expected ${EXPECTED_MODES})`);
  }
}

// ─── 6. Loop wiring (split-mode) ──────────────────────────────────────
if (hasSplit) {
  const loopCode = readSafe(path.join(JS_DIR, 'hermes-main.js')) || '';
  const updateCalls = (loopCode.match(/update\w+\(dt\)/g) || []).length;
  const drawCalls   = (loopCode.match(/draw\w+\(time\)/g) || []).length;
  if (EXPECTED_MODES > 0) {
    check(updateCalls >= EXPECTED_MODES * 0.5, `Loop updateXxx(dt) calls: ${updateCalls} (expected ~${Math.floor(EXPECTED_MODES*0.5)})`);
    check(drawCalls   >= EXPECTED_MODES * 0.5, `Loop drawXxx(time) calls: ${drawCalls} (expected ~${Math.floor(EXPECTED_MODES*0.5)})`);
  } else {
    console.log(`Info: Loop wiring — ${updateCalls} update calls, ${drawCalls} draw calls`);
  }
}

// ─── 7. 🚫 key patterns (commonly broken ─ check negative) ────────────
const badNumericTernary = /(\?\.\d)/;
const matches = allCode.match(badNumericTernary);
if (matches) {
  for (const m of matches) {
    const line = lines.find(l => l.includes(m));
    check(false, `'${m}' pattern found (likely ?.number ternary error): ${(line||'').trim().slice(0,80)}`);
  }
}

// ─── 8. HTTP 200 ──────────────────────────────────────────────────────
const urlObj = new URL(HTTP_URL);
http.get({ hostname: urlObj.hostname, port: urlObj.port, path: urlObj.pathname }, (res) => {
  check(res.statusCode === 200, `HTTP ${res.statusCode} from ${HTTP_URL}`);

  console.log('');
  console.log(ok ? '✅ ALL CHECKS PASSED' : '❌ SOME CHECKS FAILED');
  process.exit(ok ? 0 : 1);
}).on('error', e => {
  check(false, `HTTP request failed: ${e.message}`);
  process.exit(1);
});
