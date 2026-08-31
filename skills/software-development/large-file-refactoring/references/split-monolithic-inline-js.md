# Splitting a Monolithic Inline JS Block from HTML

Detailed technique for extracting a large `<script>try{ ... }catch(e){ ... }</script>` block into separate `.js` files.

## 1. Locate the Script Block

```python
import re
with open('public/hermes.html', 'r', encoding='utf-8') as f:
    html = f.read()

# The pattern on this user's server:
m = re.search(r'(<script>\n)(try\{[\s\S]*?)(</script>)', html)
script_open = m.group(1)   # "<script>\n"
script_body = m.group(2)   # "try{...}"
script_close = m.group(3)  # "</script>"

# Extract the body inside try{}:
inner_m = re.match(r'try\{([\s\S]*)\n\}catch\(e\)\{', script_body)
all_js = inner_m.group(1)
```

## 2. Map Section Boundaries

```python
lines = all_js.split('\n')
sections = {}
for i, line in enumerate(lines):
    s = line.strip()
    if s == '// ─── Aurora Mode ───────────': sections['aurora'] = i
    elif s == '// ─── Drawing ──────────────': sections['drawing'] = i
    elif s == '// ─── Loop ─────────────────': sections['loop'] = i
    elif s == '// ─── Start ────────────────': sections['start'] = i

# Core:   0 → aurora-1        (globals, utils, canvas, config vars)
# Visuals: aurora → loop-1    (all drawing functions, audio, UI controls)
# Main:   loop → end          (loop function + init sequence)
```

## 3. Extract and Write Files

```python
# Simple 3-way split on this project:
core_js     = '\n'.join(lines[0:sections['aurora']])
visuals_js  = '\n'.join(lines[sections['aurora']:sections['loop']])
main_js     = '\n'.join(lines[sections['loop']:])

for name, content in [('hermes-core.js', core_js), ('hermes-visuals.js', visuals_js), ('hermes-main.js', main_js)]:
    with open(f'public/hermes/{name}', 'w') as f:
        f.write(f'// == {name} — description ==\n\n{content}\n')
```

## 4. Update HTML

Add script includes at the **bottom of `<body>`**, right before the inline init script — NOT in `<head>`. Placing scripts in `<head>` means `document.getElementById('c')` returns null because the DOM hasn't parsed yet:

```html
<script src="/hermes/hermes-core.js"></script>
<script src="/hermes/hermes-visuals.js"></script>
<script src="/hermes/hermes-main.js"></script>
```

Replace the old giant `<script>try{...}catch...</script>` with a slim init-only script:

```html
<script>
try{
resize();
addEventListener('resize',()=>{resize();initAuroraBands();initWormhole();initGalaxy();initPrismGeometry();});
initAuroraBands();
initWormhole();
initGalaxy();
initPrismGeometry();
buildPaletteUI();
document.getElementById('mode-indicator')&&(document.getElementById('mode-indicator').textContent='✨ Cosmic');
setTimeout(()=>document.getElementById('splash').classList.add('fade'),800);
// NOTE: use window.audioInitialized, NOT bare audioInitialized —
// let in module files doesn't leak to inline script scope
document.addEventListener('click',()=>{if(!window.audioInitialized)initAudio()},{once:true});
document.addEventListener('touchstart',()=>{if(!window.audioInitialized)initAudio()},{once:true});
requestAnimationFrame(loop);
}catch(e){
  document.getElementById('splash').innerHTML = '<pre>'+e.stack+'</pre>';
  document.getElementById('splash').classList.remove('fade');
}
window.onerror=function(msg,url,line,col,err){
  document.getElementById('splash').innerHTML = '<pre>'+msg+'\\nat line '+line+'\\n'+(err&&err.stack||'')+'</pre>';
  document.getElementById('splash').classList.remove('fade');
  return true;
};
</script>
```

## 5. Validation

```bash
# Syntax check each file
node -e "
const fs = require('fs');
['core','visuals','main'].forEach(f => {
  const code = fs.readFileSync('public/hermes/hermes-'+f+'.js','utf8');
  try { new Function(code); console.log(f+': OK'); }
  catch(e) { console.log(f+': ERROR:', e.message); }
});
"

# Check inline script (watch for \r\n on Windows)
node -e "
const html = require('fs').readFileSync('public/hermes.html','utf8');
const idx = html.lastIndexOf('<script>');
const end = html.indexOf('</script>', idx);
const script = html.substring(idx + 8, end);
const m = script.match(/try\{([\s\S]*?)\n\}catch\(e\)\{/);
if (m) { try { new Function(m[1]); console.log('inline: OK'); }
  catch(e) { console.log('inline: ERROR:', e.message); } }
"
```

## 6. Production Verification

```bash
curl -sI "https://example.com/hermes" | head -5
curl -sI "https://example.com/hermes/hermes-core.js" | head -3
curl -sI "https://example.com/hermes/hermes-visuals.js" | head -3
curl -sI "https://example.com/hermes/hermes-main.js" | head -3
```

All should return 200 OK with correct Content-Type.

## Proven Architecture

Based on a 121KB, 3000-line cosmic dreamscape generative art page:

| File | Size | What's Inside |
|------|------|---------------|
| `hermes.html` | ~27KB | Skeleton HTML, CSS, 3 script includes, init inline script, error handler |
| `hermes-core.js` | ~6KB | Canvas refs, PALETTES[], SCENE_MODES[], globals, config vars, resize() |
| `hermes-visuals.js` | ~89KB | ALL draw functions (10+ modes), audio system, UI controls, keyboard, gestures, config panel |
| `hermes-main.js` | ~3KB | loop(), setTimeout splash fade, requestAnimationFrame |

The visuals file is still large (89KB) but is self-contained drawing functions — each mode starts with a clear `// ─── Mode Name ───` comment, making it trivially searchable.
