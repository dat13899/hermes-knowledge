# CDP Direct-Use Pitfalls: Multi-Tab Chrome

When using `browser_cdp` directly against a CDP-override Chrome
(`browser.cdp_url` set, e.g. `http://127.0.0.1:9222`), the browser may
have multiple tabs open (user's new-tab page + your site). Stateless CDP
calls and the higher-level browser tools can silently target the WRONG
tab. Learned 2026-08-01 debugging btdat.io.vn.

## Symptom
- `browser_console` / `Runtime.evaluate` (without target_id) returns
  `chrome://new-tab-page/` scripts, empty body, or `#root` missing —
  while `browser_navigate`/`browser_vision` screenshots show the real
  site. The two tools disagree because they evaluate on different tabs.
- `Emulation.setDeviceMetricsOverride` returns `{}` success but the
  viewport does NOT change on the page you're looking at — it applied to
  another tab. `innerHeight` stays small (e.g. 429) no matter what you set.

## Fix
1. **List tabs first:** `browser_cdp` → `Target.getTargets` → note the
   `targetId` whose `url` matches your site.
2. **Always pass `target_id`** on page-level CDP calls (`Runtime.evaluate`,
   `Emulation.setDeviceMetricsOverride`, `Page.captureScreenshot`).
   Stateless CDP calls without a target hit the browser's active/attached
   tab, which is often the new-tab page.
3. **Sanity-check before trusting measurements:**
   ```js
   // Runtime.evaluate with returnByValue:true, target_id=<your tab>
   ({ url: location.href, hasRoot: !!document.getElementById('root'),
     vh: innerHeight, docH: document.documentElement.scrollHeight })
   ```
   If `url` isn't your site, you measured the wrong tab.
4. **Screenshot size:** `Page.captureScreenshot` on a large viewport
   returns a base64 blob of hundreds of KB — the tool result gets
   persisted to a file and preview is truncated. Use `browser_vision`
   (which routes to the right tab after `browser_navigate`) for visual
   checks instead of raw `Page.captureScreenshot`.

## Related
- `browser_console` (no expression) reads console of the *attached* tab —
  can show zero errors even when the site under test has errors, if the
  attached tab is the new-tab page.
