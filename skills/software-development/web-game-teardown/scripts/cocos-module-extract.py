#!/usr/bin/env python3
"""Extract modules from a Cocos Creator 2.x bundle index.js (browserify-style require map).

Usage:
  python cocos-module-extract.py <index.js> list [filter]   # list module keys
  python cocos-module-extract.py <index.js> dump <Name> [chars]

Module body = brace-matched span after `Name:[function(e,t,i){`.
Naive regex fails on nested braces; module keys also appear in cc._RF.push(t,"<uuid>","<Name>").
"""
import re
import sys


def read_src(path):
    return open(path, encoding="utf-8", errors="replace").read()


def module_keys(src):
    # Keys are literal strings before ':[function' — works for minified browserify maps
    return list(dict.fromkeys(re.findall(r"([A-Za-z0-9_/.\-$@]+):\[function", src)))


def dump_module(src, name, chars=3000):
    i = src.find(name + ":[function")
    if i < 0:
        return None
    start = src.find("{", i)
    depth = 0
    k = start
    while k < len(src):
        c = src[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return src[start + 1 : k][:chars]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    path, action = sys.argv[1], sys.argv[2]
    src = read_src(path)
    if action == "list":
        keys = module_keys(src)
        f = sys.argv[3] if len(sys.argv) > 3 else ""
        if f:
            keys = [k for k in keys if f in k]
        print(f"modules: {len(keys)}")
        for k in keys:
            print(k)
    elif action == "dump":
        name = sys.argv[3]
        chars = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
        body = dump_module(src, name, chars)
        if body is None:
            print(f"NOT FOUND: {name}")
        else:
            print(f"=== {name} len {len(body)} ===")
            print(body)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
