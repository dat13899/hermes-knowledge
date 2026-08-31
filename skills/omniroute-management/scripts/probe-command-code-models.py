#!/usr/bin/env python
"""Probe every command-code/* model exposed by OmniRoute and report which are
actually usable (not plan-blocked, not unrecognised), so the Hermes picker can
be pinned to a verified list.

WHY: GET /api/models shows a tiny subset and its `available` flag is unreliable
(it can say available for models that 403 MODEL_NOT_IN_PLAN at request time).
GET /v1/models shows MANY command-code entries, but a chunk of them fail on a
real request. The only ground truth is a live probe.

Usage:
    python probe-command-code-models.py [--list FILE] [--base URL]

      --list FILE : file of model IDs to probe (one per line). Default: pull
                    command-code/* (or cmd/*) from GET /v1/models.
      --base URL  : OmniRoute base, default http://localhost:20128.

Mgmt key is read from ~/.omniroute/management_key.txt.

Output:
    - Prints OK / PLANBLOCKED / UNRECOGNIZED / OTHER counts.
    - Writes probe_results.json (categorised) into the current dir.
    - Prints the usable (OK) list as a YAML-ready `models:` dict block, so you
      can paste it straight under `providers.omniroute.models:`.

Verified 2026-08-27 on OmniRoute v3.8.48 — correctly classified the 87
command-code/* models (39 OK / 22 PLANBLOCKED / 26 UNRECOGNIZED).

Known gotcha baked into the probe: a working model returns **SSE** (the raw
body starts with "data:"), so a naive ``json.loads`` on the response mislabels
healthy models as failures. We detect "data:" OR '"choices"' as success; we
never assume the body is a plain JSON object.
"""

import argparse
import concurrent.futures
import json
import os
import re
import urllib.error
import urllib.request


def load_models(args):
    if args.list:
        with open(args.list, encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]
    base = args.base.rstrip("/")
    req = urllib.request.Request(
        f"{base}/v1/models", headers={"Authorization": f"Bearer {mgmt_key()}"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8", "ignore"))
    ids = [m["id"] for m in data.get("data", [])]
    return [i for i in ids if i.startswith(("command-code/", "cmd/"))]


def mgmt_key():
    p = os.path.expanduser("~/.omniroute/management_key.txt")
    with open(p, encoding="utf-8") as f:
        return f.read().strip()


def probe(model, base):
    body = json.dumps(
        {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}
    ).encode()
    req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {mgmt_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            chunk = r.read(4000).decode("utf-8", "ignore")
            # SSE (streaming) or bare JSON with choices == success.
            if chunk.startswith("data:") or '"choices"' in chunk:
                return (model, "OK")
            return (model, "OK_EMPTY")
    except urllib.error.HTTPError as e:
        txt = b""
        try:
            txt = e.read()
        except Exception:
            pass
        s = txt.decode("utf-8", "ignore")
        code = msg = ""
        m = re.search(r'"code"\s*:\s*"([^"]*)"', s)
        code = m.group(1) if m else ""
        m = re.search(r'"message"\s*:\s*"([^"]*)"', s)
        msg = m.group(1) if m else s[:120]
        if "MODEL_NOT_IN_PLAN" in (code + msg) or "not available in" in msg.lower() or "plan" in msg.lower():
            return (model, f"PLANBLOCK:{msg[:80]}")
        if "not recognized" in msg.lower() or "provider not" in msg.lower():
            return (model, f"UNRECOGNIZED:{msg[:80]}")
        return (model, f"ERR:{code}:{msg[:80]}")
    except Exception as e:
        return (model, f"BAD:{str(e)[:50]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", help="file of model IDs to probe (default: discover command-code/* from /v1/models)")
    ap.add_argument("--base", default="http://localhost:20128", help="OmniRoute base URL")
    ap.add_argument("--jobs", type=int, default=10, help="parallel workers")
    args = ap.parse_args()

    models = load_models(args)
    print(f"probing {len(models)} models (base={args.base}) ...")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for m, r in ex.map(lambda m: probe(m, args.base), models):
            results[m] = r

    with open("probe_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sorted(m for m, r in results.items() if r == "OK")
    pb = [m for m, r in results.items() if r.startswith("PLANBLOCK")]
    un = [m for m, r in results.items() if r.startswith("UNRECOGNIZED")]
    other = [m for m, r in results.items() if not r.startswith("OK") and not r.startswith("PLANBLOCK") and not r.startswith("UNRECOGNIZED")]
    print(f"TOTAL={len(results)}  OK={len(ok)}  PLANBLOCKED={len(pb)}  UNRECOGNIZED={len(un)}  OTHER={len(other)}")

    print("\n=== USABLE (OK) %d — copy under providers.omniroute.models: ===" % len(ok))
    print("models:")
    for m in ok:
        print(f"  {m}: {{}}")

    print("\n=== PLAN-BLOCKED (exclude) ===")
    for m in pb:
        print("  ", m)
    print("\n=== UNRECOGNIZED (exclude) ===")
    for m in un:
        print("  ", m)
    print("\nresults written to probe_results.json")


if __name__ == "__main__":
    main()
