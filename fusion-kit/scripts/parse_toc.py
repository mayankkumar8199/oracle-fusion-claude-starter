"""Parse Oracle 'Tables and Views' toc.htm files into a flat JSON catalog.

Usage: python -I parse_toc.py <out.json> <guide>=<toc.htm>=<base_url> [...]
"""
import json
import sys
from html.parser import HTMLParser


class TocParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # labels of enclosing <li><span class=wrap> groups
        self.li_depth = 0
        self.li_labels = []      # per-<li> label (None if the li is a leaf link)
        self.in_wrap = False
        self.in_a = False
        self.cur_href = None
        self.buf = ""
        self.entries = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "li":
            self.li_labels.append(None)
        elif tag == "span" and "wrap" in (a.get("class") or ""):
            self.in_wrap, self.buf = True, ""
        elif tag == "a":
            self.in_a, self.cur_href, self.buf = True, a.get("href"), ""

    def handle_endtag(self, tag):
        if tag == "span" and self.in_wrap:
            self.in_wrap = False
            if self.li_labels:
                self.li_labels[-1] = self.buf.strip()
        elif tag == "a" and self.in_a:
            self.in_a = False
            groups = [l for l in self.li_labels if l]
            self.entries.append({"groups": groups, "name": self.buf.strip(), "href": self.cur_href})
        elif tag == "li" and self.li_labels:
            self.li_labels.pop()

    def handle_data(self, data):
        if self.in_wrap or self.in_a:
            self.buf += data


def main():
    out = sys.argv[1]
    rows = []
    for spec in sys.argv[2:]:
        guide, path, base = spec.split("=", 2)
        p = TocParser()
        p.feed(open(path, encoding="utf-8", errors="replace").read())
        for e in p.entries:
            g = e["groups"]
            if len(g) < 2:
                continue  # front matter (title, get help, overview)
            module = g[0].split(" ", 1)[1] if g[0].split(" ", 1)[0].isdigit() else g[0]
            kind = g[1]
            rows.append({
                "guide": guide,
                "module": module,
                "kind": kind,
                "subgroups": g[2:],
                "name": e["name"],
                "is_shadow": e["name"].endswith("_"),
                "url": base + (e["href"] or "").split("#")[0],
            })
    json.dump(rows, open(out, "w", encoding="utf-8"), indent=0)
    # summary
    from collections import Counter
    c = Counter((r["guide"], r["module"], r["kind"], r["is_shadow"]) for r in rows)
    mods = sorted({(r["guide"], r["module"]) for r in rows})
    print(f"total entries: {len(rows)}")
    for gm in mods:
        t = c.get((gm[0], gm[1], "Tables", False), 0)
        ts = c.get((gm[0], gm[1], "Tables", True), 0)
        v = c.get((gm[0], gm[1], "Views", False), 0)
        other = sum(n for (g, m, k, s), n in c.items() if (g, m) == gm and k not in ("Tables", "Views"))
        print(f"{gm[0]:5} | {gm[1]:45} | tables {t:4} | shadow {ts:4} | views {v:4} | other {other}")


if __name__ == "__main__":
    main()
