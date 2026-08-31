#!/usr/bin/env node
/**
 * verify-cron.js — Standalone HTML-project verifier for cron-mode autonomous loops
 *
 * Usage:
 *   node scripts/verify-cron.js <path-to-html> <url-to-curl> [--features "feat1,feat2,..."]
 *
 * Examples:
 *   node verify-cron.js public/hermes.html http://localhost:3000/hermes.html
 *   node verify-cron.js public/hermes.html http://localhost:3000/hermes.html --features "cfgBtn,toggleConfigPanel,drawSceneTransition,getTunnelSpeed"
 *
 * What it checks:
 *   1. JS_SYNTAX — compiles the <script> block via new Function()
 *   2. DOM_REFS — every getElementById() has a matching id= in the HTML
 *   3. HTTP_STATUS — curl to the URL returns 200
 *   4. BRACE_BALANCE — { and } counts match
 *   5. BACKTICK_BALANCE — template literal backticks are even
 *   6. REQUIRED_IDS — required structural elements exist
 *   7. FEATURES — (optional, via --features) verify specific JS/DOM identifiers exist
 *
 * Works in cron mode (no execute_code), no temp files, handles MSYS2 paths.
 * Returns exit code 0 on full pass, 1 on any failure.
 */

const fs = require('fs');
const { execSync } = require('child_process');

// ── Parse CLI ────────────────────────────────────────────────────────
const args = process.argv.slice(2);
if (args.some(a => /^--help|-h$/.test(a))) {
  console.log('Usage: node verify-cron.js [path] [url] [--features "a,b,c"]');
  console.log('  path  — path to HTML file (default: public/hermes.html)');
  console.log('  url   — URL to curl for HTTP check (default: http://localhost:3000/hermes.html)');
  console.log('  --features — comma-separated list of JS identifiers/element IDs to verify');
  process.exit(0);
}

let htmlPath = 'public/hermes.html';
let urlToCheck = 'http://localhost:3000/hermes.html';
let requiredFeatures = [];

let pos = 0;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--features' && i + 1 < args.length) {
    requiredFeatures = args[++i].split(',').map(s => s.trim()).filter(Boolean);
  } else if (!a.startsWith('--')) {
    if (pos === 0) { htmlPath = a; pos++; }
    else if (pos === 1) { urlToCheck = a; pos++; }
  }
}

// ── Read HTML ────────────────────────────────────────────────────────
let html;
try {
  html = fs.readFileSync(htmlPath, 'utf8');
} catch (e) {
  console.log(`=== Verify: ${htmlPath} ===`);
  console.log(`  FAIL READ_FILE — ${e.message}`);
  process.exit(1);
}

const checks = [];

// ── 1. JS Syntax ──────────────────────────────────────────────────────
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  checks.push({ name: 'JS_SCRIPT_TAG', ok: false, detail: 'no <script> tag found' });
} else {
  try {
    new Function(scriptMatch[1]);
    checks.push({ name: 'JS_SYNTAX', ok: true });
  } catch (e) {
    checks.push({ name: 'JS_SYNTAX', ok: false, detail: e.message.split('\n')[0] });
  }
}

// ── 2. DOM Integrity ──────────────────────────────────────────────────
const jsIds = [...new Set(
  [...html.matchAll(/getElementById\(['"]([^'"]+)['"]\)/g)].map(m => m[1])
)];
const htmlIds = [...new Set(
  [...html.matchAll(/id=['"]([^'"]+)['"]/g)].map(m => m[1])
)];
const missing = jsIds.filter(id => !htmlIds.includes(id));
checks.push({
  name: 'DOM_REFS',
  ok: missing.length === 0,
  detail: missing.length
    ? `DOM_ELEMENTS_MISSING: ${missing.join(', ')}`
    : `${jsIds.length} JS refs -> ${htmlIds.length} DOM ids, all match`
});

// ── 3. HTTP 200 ─────────────────────────────────────────────────────
const isWin = process.platform === 'win32';
try {
  const nul = isWin ? 'nul' : '/dev/null';
  const result = execSync(
    `curl -s -o ${nul} -w "%{http_code}" "${urlToCheck}"`,
    { timeout: 8000, encoding: 'utf8', shell: true }
  );
  const code = result.trim();
  checks.push({ name: 'HTTP_STATUS', ok: code === '200', detail: code });
} catch (e) {
  const stdout = (e.stdout || '').trim();
  checks.push({
    name: 'HTTP_STATUS',
    ok: stdout === '200',
    detail: stdout || e.stderr?.trim() || e.message.split('\n')[0]
  });
}

// ── 4. Structural balance ───────────────────────────────────────────
const opens = (html.match(/\{/g) || []).length;
const closes = (html.match(/\}/g) || []).length;
const bticks = (html.match(/`/g) || []).length;
checks.push({
  name: 'BRACE_BALANCE',
  ok: opens === closes,
  detail: opens === closes ? `${opens} pairs` : `${opens} open / ${closes} close (delta ${opens - closes})`
});
checks.push({
  name: 'BACKTICK_BALANCE',
  ok: bticks % 2 === 0,
  detail: bticks % 2 === 0 ? `${bticks} backticks, even` : `${bticks} backticks, ODD`
});

// ── 5. Required Elements ─────────────────────────────────────────────
const REQUIRED_IDS = [
  'c', 'trailCanvas', 'bloom', 'hud', 'mode-badge', 'palette-indicator',
  'help-overlay', 'mode-panel', 'paint-controls', 'snapshot-toast'
];
const missingReq = REQUIRED_IDS.filter(id => !htmlIds.includes(id));
checks.push({
  name: 'REQUIRED_IDS',
  ok: missingReq.length === 0,
  detail: missingReq.length ? `MISSING: ${missingReq.join(', ')}` : `${REQUIRED_IDS.length}/${REQUIRED_IDS.length} present`
});

// ── 6. Feature Inventory (--features) ───────────────────────────────
if (requiredFeatures.length > 0) {
  const failed = requiredFeatures.filter(f => {
    return !jsIds.includes(f) && !htmlIds.includes(f)
      && !html.includes(`"${f}"`) && !html.includes(`'${f}'`)
      && !html.includes(f);
  });
  checks.push({
    name: 'FEATURES',
    ok: failed.length === 0,
    detail: failed.length
      ? `MISSING IN HTML/JS: ${failed.join(', ')}`
      : `${requiredFeatures.length}/${requiredFeatures.length} found`
  });
}

// ── Output ───────────────────────────────────────────────────────────
console.log(`=== Verify: ${htmlPath}${requiredFeatures.length ? ` [${requiredFeatures.length} features]` : ''} ===`);
let allPass = true;
for (const c of checks) {
  const status = c.ok ? 'OK' : 'FAIL';
  if (!c.ok) allPass = false;
  console.log(`  ${status} ${c.name}${c.detail ? ' — ' + c.detail : ''}`);
}
console.log(`Result: ${allPass ? 'PASS' : 'FAIL'}`);
process.exit(allPass ? 0 : 1);
