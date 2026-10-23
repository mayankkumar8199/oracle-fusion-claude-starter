"""Build compact, grep-friendly index files from the scraped Oracle 26D catalogs.

Usage: python -I build_indexes.py <scratchpad_dir>
Writes <dir>/idx/: tables_index.tsv, fk_edges.tsv, rest_roots.tsv, guides_index.tsv, views_index.tsv, README.txt
"""
import json
import os
import re
import sys
from collections import defaultdict


def tsv(v):
    return re.sub(r"[\t\r\n]+", " ", str(v)).strip()


def main():
    d = sys.argv[1]
    idx = os.path.join(d, "idx")
    os.makedirs(idx, exist_ok=True)
    cat = json.load(open(os.path.join(d, "catalog.json"), encoding="utf-8"))
    tables = [json.loads(l) for l in open(os.path.join(d, "tables.jsonl"), encoding="utf-8")]
    tnames = {t["name"] for t in tables}

    with open(os.path.join(idx, "tables_index.tsv"), "w", encoding="utf-8") as f:
        f.write("table\tguide\tmodule\tflow\towner\tpk_columns\tn_columns\tn_fk_out\tn_fk_in\tdescription\turl\n")
        for t in sorted(tables, key=lambda x: (x["flow"], x["module"], x["name"])):
            pk = "; ".join(p["columns"] for p in t["pk"])
            out = sum(1 for k in t["fks"] if k["table"].upper() == t["name"])
            f.write("\t".join(tsv(x) for x in (t["name"], t["guide"], t["module"], t["flow"], t["owner"], pk,
                                                t["n_columns"], out, len(t["fks"]) - out, t["description"][:300], t["url"])) + "\n")

    edges = set()
    for t in tables:
        for k in t["fks"]:
            child, parent = k["table"].upper(), k["ftable"].upper()
            edges.add((child, parent, k["col"]))
    with open(os.path.join(idx, "fk_edges.tsv"), "w", encoding="utf-8") as f:
        f.write("child_table\tparent_table\tchild_fk_columns\tboth_in_scope\n")
        for c, p, col in sorted(edges):
            f.write(f"{c}\t{p}\t{tsv(col)}\t{'Y' if c in tnames and p in tnames else 'N'}\n")

    with open(os.path.join(idx, "views_index.tsv"), "w", encoding="utf-8") as f:
        f.write("view\tguide\tmodule\turl\n")
        for r in cat:
            if r["kind"] == "Views":
                f.write(f"{r['name']}\t{r['guide']}\t{tsv(r['module'])}\t{r['url']}\n")

    rest = json.load(open(os.path.join(d, "rest_catalog.json"), encoding="utf-8"))
    roots = defaultdict(list)
    for r in rest:
        roots[(r["book"], r["root"])].append(r)
    with open(os.path.join(idx, "rest_roots.tsv"), "w", encoding="utf-8") as f:
        f.write("book\troot\ttop_resource\tbase_path\tn_resources\tn_ops\tmethods\tactions\tchild_resources\tdescription\tdoc\n")
        for (book, root), rs in sorted(roots.items()):
            top = min(rs, key=lambda r: r["resource"].count("/"))
            ops = [o for r in rs for o in r["ops"]]
            base = ""
            for o in top["ops"]:
                m = re.match(r"^(/\w+/resources/[0-9.]+/" + re.escape(root) + r")", o["path"])
                if m:
                    base = m.group(1)
                    break
            methods = sorted({o["method"] for o in ops})
            actions = sorted({o["path"].split("/action/")[1] for o in ops if "/action/" in o["path"]})
            children = sorted({r["resource"] for r in rs if r is not top})
            f.write("\t".join(tsv(x) for x in (book, root, top["resource"], base, len(rs), len(ops), ",".join(methods),
                                                "; ".join(actions), " | ".join(children)[:1500], top["description"][:300],
                                                top["ops"][0]["doc"] if top["ops"] else "")) + "\n")

    toc = json.load(open(os.path.join(d, "guides_toc.json"), encoding="utf-8"))
    with open(os.path.join(idx, "guides_index.tsv"), "w", encoding="utf-8") as f:
        f.write("book\tbook_title\tchapter_path\tentry\turl\n")
        for e in toc:
            if e["name"] in ("Previous", "Next", "Title and Copyright Information", "Get Help"):
                continue
            f.write("\t".join(tsv(x) for x in (e["book"], e["book_title"], " > ".join(e["path"]), e["name"], e["url"])) + "\n")

    with open(os.path.join(idx, "README.txt"), "w", encoding="utf-8") as f:
        f.write(
            "Oracle Fusion Cloud 26D reference indexes (built from docs.oracle.com, 2026-10-21)\n"
            "tables_index.tsv : every in-scope P2P/O2C/shared table scraped from the official Tables and Views guides\n"
            "                   (Financials oedmf, Procurement oedmp, SCM oedsc, Common oedma, CX oedms) with PK + description.\n"
            "                   Full columns/FKs/indexes per table: ../tables.jsonl (one JSON object per line).\n"
            "fk_edges.tsv     : documented foreign keys child -> parent (columns on the child side).\n"
            "views_index.tsv  : all documented views (names only).\n"
            "rest_roots.tsv   : every REST root resource (fin, proc, scm, common, cx) with base path, actions, children.\n"
            "                   Full operations (method + exact path): ../rest_catalog.json\n"
            "guides_index.tsv : TOC entries of FBDI (fbdi_*), SOAP (soap_*), OTBI subject areas (otbi_*), BICC data stores (bicc_*),\n"
            "                   scheduled processes (ess_proc, ess_scm), security references (sec_*), business objects (bo_*),\n"
            "                   AI agent adoption guides (ai_*), user guides (use_*), implementation guides (impl_*).\n"
            "All tables/views names: ../catalog.json. Checker: ../scripts/check_refs.py <file>\n"
        )
    print("tables", len(tables), "| fk edges", len(edges), "| rest roots", len(roots), "| guide entries", len(toc))


if __name__ == "__main__":
    main()
