# Native git path mismatch on Windows (MSYS)

## Symptom

```bash
git -C /c/Users/datel/service-dashboard remote -v
# fatal: cannot change to '/c/Users/datel/service-dashboard': No such file or directory
```

But the directory **exists** and `cd /c/Users/datel/service-dashboard` (a bash
builtin) works fine. Same failure on other drives:

```bash
git -C /d/daily log                    # fatal: cannot change to '/d/daily'
```

## Root cause

Under git-bash/MSYS, MSYS **path conversion is disabled** for the arguments of
native Windows executables. `bash` builtins (`cd`, `ls`, `du`, `find`) understand
MSYS paths (`/c/...`, `/d/...`), but native `.exe` tools (`git`, `node`, `rg`,
`python`) do **not** get them translated — so `git -C /c/...` genuinely cannot
find the directory even though it is on disk.

## Fix

Pass **native forward-slash paths** (Git/Windows accept `C:/...`, `D:/...`):

```bash
git -C "C:/Users/datel/service-dashboard" remote -v     # works
git -C "D:/daily" log                                    # works
git -C "C:/Users/datel/dlv" status -sb                   # works
```

Home is `C:/Users/<user>` (never `/c/Users/<user>`), and the drive letter plus
forward slash is the universal safe form across git/rg/node/python.

## Diagnostic pattern

If `git -C <path>` claims a dir is **missing** but `ls <path>` shows it: the
**path form is wrong, not the directory**. Check for the three common
mismatches:
- `/c/Users/x` vs `C:/Users/x` vs `C:\Users\x`
- `/d/x` vs `D:/x`
- trailing-slash or case differences

Note also that `git -C` on a **different drive** than the shell cwd can
sometimes still fail for MSYS-drive-letter reasons — the `D:/...` native form
fixes that too.

## When verifying multiple repos (loop pattern)

A `for` loop over `~/dir1 ~/dir2` that runs `git status` will hit this. Move
`git` calls off the MSYS-style path first:

```bash
for d in "C:/Users/datel/diagram-service" "C:/Users/datel/dlv"; do
  git -C "$d" status -sb | head -1
done
```
