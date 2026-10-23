"""Politely scrape Oracle 'Tables and Views' table pages for P2P/O2C scope.

Usage: python -I scrape_tables.py <catalog.json> <out.jsonl>
Resumable: tables already present in out.jsonl are skipped.
"""
import concurrent.futures as cf
import html
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

# (guide, module) -> flow tag. Every non-shadow TABLE in these modules is scraped.
SCOPE = {
    ("proc", "Purchasing"): "P2P",
    ("proc", "Self Service Procurement"): "P2P",
    ("proc", "Supplier Model"): "P2P",
    ("proc", "Supplier Portal"): "P2P",
    ("proc", "Sourcing"): "P2P-adjacent",
    ("proc", "Supplier Qualification"): "P2P-adjacent",
    ("scm", "Receiving"): "P2P",
    ("scm", "Receipt Accounting"): "P2P",
    ("fin", "Payables"): "P2P",
    ("fin", "Payments"): "P2P+O2C",
    ("fin", "Budgetary Control"): "P2P-adjacent",
    ("scm", "Order Management"): "O2C",
    ("scm", "Pricing"): "O2C",
    ("scm", "Shipping"): "O2C",
    ("scm", "Inventory Management"): "P2P+O2C",
    ("scm", "Supply Chain Orchestration"): "O2C-adjacent",
    ("scm", "Supply Chain Financial Orchestration Foundation"): "O2C-adjacent",
    ("fin", "Receivables"): "O2C",
    ("fin", "Advanced Collections"): "O2C",
    ("fin", "Revenue Management"): "O2C",
    ("fin", "Bill Management"): "O2C",
    ("cx", "Customer Data Model"): "O2C",
    ("fin", "Cash Management"): "Shared",
    ("fin", "Tax"): "Shared",
    ("fin", "Subledger Accounting"): "Shared",
    ("fin", "General Ledger"): "Shared",
    ("fin", "Financials Common Module"): "Shared",
    ("fin", "Legal Entity Configurator"): "Shared",
}
# Extra individual tables from otherwise names-only modules.
EXTRA = re.compile(
    r"^(FND_LOOKUP_(TYPES|VALUES)_(B|TL)|FND_CURRENCIES_(B|TL)|FND_TERRITORIES_(B|TL)|FND_ATTACHED_DOCUMENTS|"
    r"FND_DOCUMENTS(_TL)?|FND_DOC_SEQUENCE.*|FND_SETID_.*|FND_VS_VALUES_(B|TL)|FND_VS_VALUE_SETS|"
    r"FND_TREE_NODE|FND_KF_.*|CST_.*COGS.*|CST_.*REVENUE.*)$"
)

UA = {"User-Agent": "Mozilla/5.0 (personal reference build; low rate)"}
LOCK = threading.Lock()
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def clean(x):
    return WS.sub(" ", html.unescape(TAG.sub(" ", x))).strip()


def fetch(url):
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:  # fall back to curl (uses the Windows cert store)
            last = e
            try:
                out = subprocess.run(["curl", "-sS", "-L", "--max-time", "60", "-A", UA["User-Agent"], url],
                                     capture_output=True, timeout=90)
                if out.returncode == 0 and out.stdout:
                    return out.stdout.decode("utf-8", errors="replace")
            except Exception as e2:
                last = e2
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"fetch failed: {url}: {last}")


def table_rows(section_html):
    body = section_html.split("<tbody", 1)
    if len(body) < 2:
        return []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body[1], re.S)
    return [[clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)] for row in rows]


def section(page, summary):
    m = re.search(r'<table[^>]*summary="' + re.escape(summary) + r'"[^>]*>(.*?)</table>', page, re.S)
    return m.group(1) if m else ""


def parse(page):
    a = page.find("<article")
    page = page[a:] if a >= 0 else page
    body = page.split('<div class="body">', 1)
    desc = ""
    if len(body) == 2:
        pre = body[1].split("<section", 1)[0]
        desc = " ".join(clean(p) for p in re.findall(r'<p class="p">(.*?)</p>', pre, re.S)).strip()
    details = {}
    for k in ("Schema", "Object owner", "Object type", "Tablespace"):
        m = re.search(r'<p class="p">' + k + r":\s*(.*?)</p>", page, re.S)
        if m:
            details[k] = clean(m.group(1))
    pk = [{"name": r[0], "columns": r[1]} for r in table_rows(section(page, "Primary Key")) if len(r) >= 2]
    cols = []
    csec = section(page, "Columns")
    heads = [clean(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", csec, re.S)]
    pos = {h: i for i, h in enumerate(heads)}

    def cell(r, label):
        i = pos.get(label)
        return r[i] if i is not None and i < len(r) else ""

    for r in table_rows(csec):
        if r and r[0]:
            cols.append({"name": r[0], "type": cell(r, "datatype"), "len": cell(r, "length"), "prec": cell(r, "precision"),
                         "nn": cell(r, "not-null"), "comment": cell(r, "comments")[:400], "status": cell(r, "status")})
    fks = [{"table": r[0], "ftable": r[1], "col": r[2]} for r in table_rows(section(page, "Foreign Keys")) if len(r) >= 3]
    idx = [{"name": r[0], "unique": r[1], "columns": r[3] if len(r) > 3 else ""}
           for r in table_rows(section(page, "Indexes")) if len(r) >= 2]
    return desc, details, pk, cols, fks, idx


def rescrape(cat_path, out_path, names_path):
    """Re-fetch the named tables with the current parser and replace their records in out_path."""
    names = {n.strip() for n in open(names_path, encoding="utf-8") if n.strip()}
    recs = [json.loads(l) for l in open(out_path, encoding="utf-8")]
    todo = [r for r in recs if r["name"] in names]
    print(f"re-scraping {len(todo)} tables", flush=True)

    def work(rec):
        time.sleep(0.25)
        desc, details, pk, cols, fks, idx = parse(fetch(rec["url"]))
        rec.update({"description": desc or rec["description"], "pk": pk, "n_columns": len(cols), "columns": cols,
                    "fks": fks, "indexes": idx})
        return rec

    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(work, todo))
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    os.replace(tmp, out_path)
    print("re-scrape done; still without columns:", sum(1 for r in todo if not r["columns"]), flush=True)


def main():
    cat_path, out_path = sys.argv[1], sys.argv[2]
    if len(sys.argv) > 4 and sys.argv[3] == "--only":
        return rescrape(cat_path, out_path, sys.argv[4])
    rows = json.load(open(cat_path, encoding="utf-8"))
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path, encoding="utf-8"):
            try:
                done.add(json.loads(line)["name"])
            except Exception:
                pass
    todo, seen = [], set()
    for r in rows:
        if r["kind"] != "Tables" or r["is_shadow"]:
            continue
        flow = SCOPE.get((r["guide"], r["module"]))
        if flow is None and EXTRA.match(r["name"]):
            flow = "Foundation" if r["name"].startswith("FND_") else "Adjacent"
        if flow is None or r["name"] in done or r["name"] in seen:
            continue
        seen.add(r["name"])
        todo.append((r, flow))
    print(f"to scrape: {len(todo)} (already done: {len(done)})", flush=True)

    out = open(out_path, "a", encoding="utf-8")
    t0, n_ok, n_err = time.time(), 0, 0

    def work(item):
        r, flow = item
        time.sleep(0.25)  # politeness per worker
        page = fetch(r["url"])
        desc, details, pk, cols, fks, idx = parse(page)
        return {"name": r["name"], "guide": r["guide"], "module": r["module"], "flow": flow, "url": r["url"],
                "description": desc, "owner": details.get("Object owner", ""), "pk": pk,
                "n_columns": len(cols), "columns": cols, "fks": fks, "indexes": idx}

    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(work, it): it for it in todo}
        for f in cf.as_completed(futs):
            try:
                rec = f.result()
                with LOCK:
                    out.write(json.dumps(rec) + "\n")
                    out.flush()
                n_ok += 1
            except Exception as e:
                n_err += 1
                print("ERR", futs[f][0]["name"], str(e)[:160], flush=True)
            if (n_ok + n_err) % 250 == 0:
                print(f"{n_ok + n_err}/{len(todo)} ok={n_ok} err={n_err} {time.time() - t0:.0f}s", flush=True)
    print(f"DONE ok={n_ok} err={n_err} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
