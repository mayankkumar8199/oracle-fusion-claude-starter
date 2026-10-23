"""Download Oracle docs toc.htm pages and dump every entry with its group path.

Usage: python -I dump_toc.py <download_dir> <out.json> <key>=<book_base_url> [...]
(book_base_url ends with '/'; toc.htm is appended)
"""
import html
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser


class Toc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.labels, self.in_wrap, self.in_a, self.href, self.buf, self.entries = [], False, False, None, "", []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "li":
            self.labels.append(None)
        elif tag == "span" and "wrap" in (a.get("class") or ""):
            self.in_wrap, self.buf = True, ""
        elif tag == "a":
            self.in_a, self.href, self.buf = True, a.get("href"), ""

    def handle_endtag(self, tag):
        if tag == "span" and self.in_wrap:
            self.in_wrap = False
            if self.labels:
                self.labels[-1] = self.buf.strip()
        elif tag == "a" and self.in_a:
            self.in_a = False
            self.entries.append(([l for l in self.labels if l], self.buf.strip(), self.href))
        elif tag == "li" and self.labels:
            self.labels.pop()

    def handle_data(self, d):
        if self.in_wrap or self.in_a:
            self.buf += d


def main():
    ddir, out = sys.argv[1], sys.argv[2]
    os.makedirs(ddir, exist_ok=True)
    allrows = []
    for spec in sys.argv[3:]:
        key, base = spec.split("=", 1)
        path = os.path.join(ddir, key + ".toc.htm")
        if not os.path.exists(path):
            subprocess.run(["curl", "-sS", "-L", "--max-time", "120", "-A", "Mozilla/5.0", "-o", path, base + "toc.htm"])
        s = open(path, encoding="utf-8", errors="replace").read()
        m = re.search(r"<title>(.*?)</title>", s, re.S)
        title = html.unescape(m.group(1)).strip() if m else "?"
        p = Toc()
        p.feed(s)
        rows = [{"book": key, "book_title": title, "path": g, "name": n, "url": base + (h or "").split("#")[0]}
                for g, n, h in p.entries if n]
        allrows.extend(rows)
        print(f"{key:16} | {len(rows):5} entries | {title[:90]}")
    json.dump(allrows, open(out, "w", encoding="utf-8"), indent=0)
    print("total", len(allrows))


if __name__ == "__main__":
    main()
