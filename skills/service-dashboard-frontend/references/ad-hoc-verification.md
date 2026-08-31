# Ad-Hoc Verification Scripts

Pattern for quick structural verification when no test suite exists for UI changes.

## When to use

- UI fix is inline-style-only (no test suite relevant)
- Need to verify 6+ specific changes made it into file
- Manual browser check is not feasible mid-session
- Want programmatic evidence before claiming "done"

## Template

```js
const fs = require('fs');
const src = fs.readFileSync('C:/Users/datel/service-dashboard/frontend/src/pages/ComponentName.jsx', 'utf8');
let ok = true;

const checks = {
  'description of check 1': /regex pattern/.test(src),
  'description of check 2': /another pattern/.test(src),
};

for (const [name, pass] of Object.entries(checks)) {
  console.log(pass ? 'PASS' : 'FAIL', '-', name);
  if (!pass) ok = false;
}
console.log(ok ? '\nALL CHECKS PASSED' : '\nSOME CHECKS FAILED');
process.exit(ok ? 0 : 1);
```

## Workflow

1. Write verify script to `C:/Users/datel/AppData/Local/Temp/hermes-verify-<topic>.js` via `write_file`
2. Run: `node "C:/Users/datel/AppData/Local/Temp/hermes-verify-<topic>.js"`
3. Confirm ALL CHECKS PASSED
4. Cleanup: `rm -f "C:/Users/datel/AppData/Local/Temp/hermes-verify-<topic>.js"`

## Pitfalls

- Node `require` doesn't resolve `/tmp/` on Windows git-bash → use full `C:/Users/datel/...` path
- Write file with `write_file` tool (not `cat > /tmp/...` heredoc — path translation fails)
- Always delete the temp script after verification to avoid clutter
