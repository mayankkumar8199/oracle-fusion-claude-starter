"""Validate Oracle Fusion references in a Markdown/JSON/SQL file against the official 26D catalogs.

Checks:
  * table/view names         -> catalog.json (Tables and Views guides: fin, proc, scm, common, cx)
  * TABLE.COLUMN / alias.COL -> tables.jsonl (scraped column lists) inside SQL (``` blocks or .sql files)
  * REST paths               -> rest_catalog.json (All REST Endpoints pages)
  * JSON list fields named fbdi* / scheduled_processes* / ess* / otbi* / bicc* / soap* / rest_roots*
                             -> guides_toc.json / rest_catalog.json
Usage: python -I check_refs.py <file> [--data <scratchpad_dir>]
Prints a report; unknown names come with close-match suggestions. Exit code is always 0.
"""
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.dirname(HERE)
PREFIXES = (
    "AP AR ARB CE CMR CST DOO DOS EGO EGP EXM FA FLA FND FUN GL HR HZ IBY IEX INV JA JE JG JL JMF MO MSC "
    "OKC PER PJB PJC PJF PON POQ POR POZ PO QP RA RCV VRM WSH XCC XLA XLE ZX POS FOS INL"
).split()
TOKEN = re.compile(r"\b(?:%s)_[A-Z0-9_$#]{2,}\b" % "|".join(PREFIXES))
REST = re.compile(r"/(?:fscm|crm|hcm)RestApi/resources/(?:[0-9.]+|latest)/[^\s`'\")\]|<>,]+")


def load(data):
    cat = json.load(open(os.path.join(data, "catalog.json"), encoding="utf-8"))
    names = {r["name"].upper() for r in cat}
    cols, scraped = {}, set()
    p = os.path.join(data, "tables.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            try:
                t = json.loads(line)
            except Exception:
                continue
            scraped.add(t["name"].upper())
            cols[t["name"].upper()] = {c["name"].upper() for c in t["columns"]}
    allcols = set().union(*cols.values()) if cols else set()
    rest = json.load(open(os.path.join(data, "rest_catalog.json"), encoding="utf-8"))
    paths, roots = set(), set()
    for r in rest:
        roots.add(r["root"])
        for o in r["ops"]:
            paths.add(norm(o["path"]))
    toc = json.load(open(os.path.join(data, "guides_toc.json"), encoding="utf-8"))
    tocnames = {}
    for e in toc:
        kind = e["book"].split("_")[0]
        tocnames.setdefault(kind, set()).add(e["name"].strip().lower())
    return names, cols, scraped, allcols, paths, roots, tocnames


def norm(path):
    path = path.split("?")[0].rstrip("/.")
    path = re.sub(r"/resources/(?:[0-9.]+|latest)/", "/resources/V/", path)
    return re.sub(r"\{[^}]*\}", "{}", path)


def suggest(x, pool, n=3):
    return difflib.get_close_matches(x, list(pool), n=n, cutoff=0.75)


def sql_blocks(text, fname):
    if fname.lower().endswith(".sql"):
        return [text]
    return re.findall(r"```(?:sql|SQL)?\s*\n(.*?)```", text, re.S)


def check_sql(sql, names, cols):
    bad = []
    alias = {}
    for t, a in re.findall(r"(?:FROM|JOIN|,)\s+([A-Za-z_][A-Za-z0-9_$#]*)\s+(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*)", sql, re.I):
        if t.upper() in names and a.upper() not in ("ON", "WHERE", "JOIN", "LEFT", "INNER", "RIGHT", "FULL", "CROSS", "GROUP", "ORDER", "AND", "OR"):
            alias[a.lower()] = t.upper()
    for a, c in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_$#]*)\b", sql):
        t = alias.get(a.lower()) or (a.upper() if a.upper() in names else None)
        if not t or t not in cols:
            continue
        if c.upper() not in cols[t]:
            bad.append((f"{t}.{c.upper()}", suggest(c.upper(), cols[t])))
    return alias, bad


def walk_lists(obj, key=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_lists(v, k)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, str):
                yield key, v
            else:
                yield from walk_lists(v, key)


def main():
    f = sys.argv[1]
    data = sys.argv[sys.argv.index("--data") + 1] if "--data" in sys.argv else DATA
    names, cols, scraped, allcols, paths, roots, tocnames = load(data)
    text = open(f, encoding="utf-8", errors="replace").read()

    found = set(TOKEN.findall(text.upper()))
    unknown_tables = sorted(t for t in found if t not in names and t not in allcols and not t.endswith("_ID"))
    print(f"== tables/views referenced: {len(found)} | unknown: {len(unknown_tables)}")
    for t in unknown_tables:
        print(f"   UNKNOWN TABLE/VIEW {t}  ~ {suggest(t, names)}")

    nbad = 0
    for i, block in enumerate(sql_blocks(text, f)):
        alias, bad = check_sql(block, names, cols)
        for col, sug in bad:
            nbad += 1
            print(f"   UNKNOWN COLUMN (sql block {i + 1}) {col}  ~ {sug}")
    print(f"== SQL column problems: {nbad} (only tables with scraped columns are checked: {len(scraped)} scraped)")

    rp = set(REST.findall(text))
    bad_rest = []
    for p in sorted(rp):
        n = norm(p)
        if n in paths or any(q.startswith(n + "/") for q in paths):
            continue
        bad_rest.append(p)
    print(f"== REST paths referenced: {len(rp)} | unknown: {len(bad_rest)}")
    for p in bad_rest:
        root = re.sub(r"^.*/resources/(?:[0-9.]+|latest)/", "", p).split("/")[0]
        print(f"   UNKNOWN REST PATH {p}  (root '{root}' {'exists' if root in roots else 'UNKNOWN ~ ' + str(suggest(root, roots))})")

    if f.lower().endswith(".json"):
        try:
            obj = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print("   (json parse failed:", e, ")")
            obj = None
        kinds = {"fbdi": "fbdi", "scheduled": "ess", "ess": "ess", "otbi": "otbi", "bicc": "bicc", "soap": "soap"}
        nmiss = 0
        for k, v in walk_lists(obj):
            kl = k.lower()
            if kl.startswith("rest_root"):
                if v not in roots:
                    nmiss += 1
                    print(f"   UNKNOWN REST ROOT [{k}] {v} ~ {suggest(v, roots)}")
                continue
            kind = next((kinds[p] for p in kinds if kl.startswith(p)), None)
            if not kind:
                continue
            x = v.strip().lower()
            pool = tocnames.get(kind, set())
            if x in pool or any(x in e or e in x for e in pool if len(e) > 12):
                continue
            everywhere = set().union(*tocnames.values())
            if any(x in e for e in everywhere if len(x) > 12):
                continue
            nmiss += 1
            note = " (Financials scheduled processes have no dedicated 26D guide: verify on the web)" if kind == "ess" else ""
            print(f"   NOT IN {kind.upper()} GUIDE TOC [{k}] {v} ~ {suggest(x, pool)}{note}")
        print(f"== named interface items not found in guide TOCs: {nmiss}")


if __name__ == "__main__":
    main()
