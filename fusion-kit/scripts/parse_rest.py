"""Parse Oracle 'All REST Endpoints' pages into a resource/operation catalog.

Usage: python -I parse_rest.py <out.json> <book>=<file.htm>=<base_url> [...]
"""
import html
import json
import re
import sys
from collections import Counter

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def clean(x):
    return WS.sub(" ", html.unescape(TAG.sub(" ", x))).strip()


def main():
    out = sys.argv[1]
    resources = []
    for spec in sys.argv[2:]:
        book, path, base = spec.split("=", 2)
        s = open(path, encoding="utf-8", errors="replace").read()
        # Split on group headings and resource panels, keeping order.
        tokens = re.split(r'(<h[23][^>]*>.*?</h[23]>|<div class="panel panel-default">)', s, flags=re.S)
        group = ""
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if re.match(r"<h[23]", t or ""):
                g = clean(t)
                if g and not g.lower().startswith(("all rest endpoints", "rest api")):
                    group = g
            elif t == '<div class="panel panel-default">' and i + 1 < len(tokens):
                body = tokens[i + 1]
                m = re.search(r'<div class="heading-title">(.*?)</div>', body, re.S)
                title = clean(m.group(1)) if m else ""
                m = re.search(r'<div class="panel-body">\s*<div>(.*?)</div>', body, re.S)
                desc = clean(m.group(1)) if m else ""
                ops = []
                for dt, dd in re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", body, re.S):
                    a = re.search(r'<a href="([^"]+)">(.*?)</a>', dt, re.S)
                    meth = re.search(r'Method:\s*<span[^>]*>(.*?)</span>', dd, re.S)
                    p = re.search(r"Path:\s*<code>(.*?)</code>", dd, re.S)
                    ops.append({
                        "op": clean(a.group(2)) if a else clean(dt),
                        "method": clean(meth.group(1)).upper() if meth else "",
                        "path": clean(p.group(1)) if p else "",
                        "doc": base + a.group(1) if a else "",
                    })
                if title and ops:
                    roots = Counter(
                        re.sub(r"^/(\w+)/resources/[0-9.]+/", "", o["path"]).split("/")[0] for o in ops if o["path"]
                    )
                    resources.append({
                        "book": book, "group": group, "resource": title,
                        "root": roots.most_common(1)[0][0] if roots else "",
                        "api": (re.match(r"^/(\w+)/", ops[0]["path"]) or [None, ""])[1] if ops[0]["path"] else "",
                        "description": desc[:700], "n_ops": len(ops), "ops": ops,
                    })
                i += 1
            i += 1
    json.dump(resources, open(out, "w", encoding="utf-8"), indent=0)
    c = Counter(r["book"] for r in resources)
    print("resources per book:", dict(c), "| total ops:", sum(r["n_ops"] for r in resources))
    groups = Counter((r["book"], r["group"]) for r in resources)
    for (b, g), n in sorted(groups.items()):
        print(f"  {b:6} | {g[:60]:60} | {n}")


if __name__ == "__main__":
    main()
