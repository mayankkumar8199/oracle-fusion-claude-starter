"""Assemble the final reference Markdown: sections 00-12 + generated Appendices A-E.

Usage: python -I assemble.py <scratchpad_dir> <out.md> [sources.json]
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

SECTION_FILES = ["00_overview", "01_foundations", "02_p2p", "03_o2c", "04_backbone", "05_ui", "06_rest", "07_bulk",
                 "08_reporting", "09_sql", "10_ai_oracle", "11_ai_claude", "12_security"]
FLOW_ORDER = ["P2P", "O2C", "P2P+O2C", "Shared", "P2P-adjacent", "O2C-adjacent", "Foundation", "Adjacent"]
FLOW_LABEL = {"P2P": "Procure-to-Pay", "O2C": "Order-to-Cash", "P2P+O2C": "Used by both cycles", "Shared": "Shared financial backbone",
              "P2P-adjacent": "P2P-adjacent (optional modules)", "O2C-adjacent": "O2C-adjacent (optional modules)",
              "Foundation": "Foundation (selected FND tables)", "Adjacent": "Adjacent (selected Cost Management tables)"}
GUIDE_LABEL = {"fin": "Tables and Views for Financials", "proc": "Tables and Views for Procurement", "scm": "Tables and Views for SCM",
               "common": "Tables and Views for Common Features", "cx": "Tables and Views for Sales, Fusion Service, and Field Service"}
FRONT = {"Previous", "Next", "Title and Copyright Information", "Get Help"}
REL = {
    "fbdi_fin": {"Budgetary Control", "Cash Management", "Customer Data Model", "Financials Common Module", "General Ledger",
                 "Payables", "Payments", "Receivables", "Revenue Management", "Subledger Accounting", "Tax"},
    "fbdi_proc": {"Purchasing", "Self Service Procurement", "Sourcing", "Supplier Model"},
    "fbdi_scm": {"Inventory Management", "Order Management", "SCM Common"},
    "bicc_fin": {"Advanced Collections", "Budgetary Control", "Cash Management", "Financials Common Module", "General Ledger",
                 "Legal Entity Configurator", "Payables", "Receivables", "Subledger Accounting", "Tax"},
    "bicc_proc": {"Purchasing", "Self Service Procurement", "Sourcing", "Supplier Model", "Supplier Qualification"},
    "bicc_scm": {"Inventory Management", "Order Management", "SCM Common"},
    "ess_proc": {"Self Service Procurement Scheduled Processes", "Supplier Model Scheduled Processes", "Purchasing Scheduled Processes",
                 "Sourcing Scheduled Processes", "Supplier Qualification Management Scheduled Processes"},
    "ess_scm": {"Inventory Management Scheduled Processes", "Order Management Scheduled Processes", "SCM Common Scheduled Processes"},
}
OTBI_EXCLUDE_FIN = re.compile(r"^(Assets|Expenses|Joint Venture|Lease|Fixed Assets|Federal|U\.S\. Federal|OTBI )", re.I)
OTBI_INCLUDE_SCM = re.compile(r"^(Order Management|Shipping|Receiving|Inventory|Pricing|Supply Chain Orchestration|Cost Management|"
                              r"Receipt Accounting|Supply Chain Financial Orchestration|Landed Cost)", re.I)
SOAP_KEEP = re.compile(r"payable|invoice|payment|receivable|receipt|customer|supplier|purchase|requisition|order|shipment|shipping|"
                       r"receiv|tax|accounting|journal|ledger|bank|collection|credit|revenue|intercompany|erp integration|"
                       r"procure|sourcing|negotiation|agreement|price|pricing|inventory|lockbox|billing|transaction", re.I)
SCM_ROLE_KEEP = re.compile(r"receiv|ship|warehouse|inventory|order|fulfil|pricing|cost", re.I)


def esc(s, n=None):
    s = re.sub(r"\s+", " ", str(s or "")).strip().replace("|", "\\|")
    if n and len(s) > n:
        s = s[: n - 1].rstrip() + "..."
    return s


def chapter(path):
    if not path:
        return ""
    c = path[0]
    p = c.split(" ", 1)
    return p[1] if p[0].isdigit() and len(p) == 2 else c


def main():
    d, out = sys.argv[1], sys.argv[2]
    srcs = json.load(open(sys.argv[3], encoding="utf-8")) if len(sys.argv) > 3 and os.path.exists(sys.argv[3]) else []
    secdir = os.path.join(d, "doc_sections")
    cat = json.load(open(os.path.join(d, "catalog.json"), encoding="utf-8"))
    tables = [json.loads(l) for l in open(os.path.join(d, "tables.jsonl"), encoding="utf-8")]
    rest = json.load(open(os.path.join(d, "rest_catalog.json"), encoding="utf-8"))
    toc = json.load(open(os.path.join(d, "guides_toc.json"), encoding="utf-8"))
    tmap = {t["name"]: t for t in tables}

    parts, body_text = [], ""
    for k in SECTION_FILES:
        p = os.path.join(secdir, k + ".md")
        if not os.path.exists(p):
            parts.append(f"<!-- missing section {k} -->")
            continue
        txt = open(p, encoding="utf-8").read().strip()
        if k != "00_overview":
            parts.append("<!-- pagebreak -->")
            body_text += "\n" + txt
        parts.append(txt)

    A = ["<!-- pagebreak -->", "## Appendix A. Complete table catalog for P2P, O2C and the shared backbone", ""]
    shadow = Counter((r["guide"], r["module"]) for r in cat if r["kind"] == "Tables" and r["is_shadow"])
    views = Counter((r["guide"], r["module"]) for r in cat if r["kind"] == "Views")
    bymod = defaultdict(list)
    for t in tables:
        bymod[(t["flow"], t["guide"], t["module"])].append(t)
    A.append(f"This appendix lists all {len(tables):,} tables documented by Oracle in the 26D *Tables and Views* guides for the modules "
             "that take part in Procure-to-Pay, Order-to-Cash and the shared financial backbone, plus selected foundation (FND) and "
             "Cost Management (COGS/revenue matching) tables. Every column, foreign key and index of these tables is in the companion "
             "Excel workbook (sheets Columns, Foreign_Keys, Indexes). Audit shadow tables (names ending in an underscore) and views are "
             "counted below but not listed; the workbook sheet All_Tables lists every one of the 16,000+ tables and views in the five guides.")
    A.append("")
    A.append("| Flow | Module | Guide | Tables listed | Audit shadow tables | Views |")
    A.append("|---|---|---|---|---|---|")
    keys = sorted(bymod, key=lambda k: (FLOW_ORDER.index(k[0]) if k[0] in FLOW_ORDER else 99, k[2]))
    for f, g, m in keys:
        A.append(f"| {FLOW_LABEL.get(f, f)} | {m} | {g} | {len(bymod[(f, g, m)])} | {shadow.get((g, m), 0)} | {views.get((g, m), 0)} |")
    A.append("")
    n = 0
    for f, g, m in keys:
        n += 1
        ts = sorted(bymod[(f, g, m)], key=lambda t: t["name"])
        A.append(f"### A.{n} {m} - {FLOW_LABEL.get(f, f)} ({len(ts)} tables; source: {GUIDE_LABEL.get(g, g)})")
        A.append("")
        A.append("| Table | Primary key | Description |")
        A.append("|---|---|---|")
        for t in ts:
            pk = "; ".join(p["columns"] for p in t["pk"]) or "-"
            A.append(f"| {t['name']} | {esc(pk, 60)} | {esc(t['description'], 170) or '-'} |")
        A.append("")

    # Appendix B: join map for core tables (tables named in sections 2, 3, 4, 9)
    core_txt = ""
    for k in ("02_p2p", "03_o2c", "04_backbone", "09_sql"):
        p = os.path.join(secdir, k + ".md")
        if os.path.exists(p):
            core_txt += open(p, encoding="utf-8").read().upper()
    core = {t for t in tmap if re.search(r"\b" + re.escape(t) + r"\b", core_txt)}
    B = ["<!-- pagebreak -->", "## Appendix B. Foreign-key join map for the core P2P and O2C tables", ""]
    B.append(f"Documented foreign keys between the {len(core)} core tables named in sections 2, 3, 4 and 9 (from the Foreign Keys "
             "sections of Oracle's 26D table pages). Read each row as: child table.child column(s) -> parent table primary key. "
             "Joins that Oracle implements through generic columns (for example subledger SOURCE_ID columns or interface "
             "attribute columns) are not foreign keys and are explained in sections 2, 3, 4 and 9 instead.")
    B.append("")
    edges = sorted({(k["table"].upper(), k["ftable"].upper(), k["col"]) for t in tables for k in t["fks"]
                    if k["table"].upper() in core and k["ftable"].upper() in core and k["table"].upper() != k["ftable"].upper()})
    bychild = defaultdict(list)
    for c, pt, col in edges:
        bychild[c].append((col, pt))
    B.append("| Child table | Child column(s) | Parent table |")
    B.append("|---|---|---|")
    for c in sorted(bychild):
        for col, pt in sorted(bychild[c], key=lambda x: (x[1], x[0])):
            B.append(f"| {c} | {esc(col, 80)} | {pt} |")
    B.append("")

    # Appendix C: REST resources cited + Order Management roots
    cited_paths = set(re.findall(r"/(?:fscm|crm|hcm)RestApi/resources/(?:[0-9.]+|latest)/([A-Za-z0-9_]+)", body_text))
    roots = defaultdict(list)
    for r in rest:
        roots[(r["book"], r["root"])].append(r)
    C = ["<!-- pagebreak -->", "## Appendix C. REST resources for P2P and O2C", ""]
    tot = Counter(r["book"] for r in rest)
    C.append("Root resources cited in this document plus every Order Management root resource, taken from the 26D *All REST "
             "Endpoints* pages. Totals in the official REST guides: " + ", ".join(
                 f"{b}: {len({k[1] for k in roots if k[0] == b})} root resources / {sum(x['n_ops'] for x in rest if x['book'] == b):,} operations"
                 for b in ("fin", "proc", "scm", "common", "cx")) + ". The workbook sheet REST_Operations lists every operation with method and exact path.")
    C.append("")
    C.append("| API | Root resource | Title | Base path | Operations | Custom actions | Description |")
    C.append("|---|---|---|---|---|---|---|")
    sel = [(b, rt) for (b, rt) in roots if rt in cited_paths or (b == "scm" and any(x["resource"].startswith("Order Management/") for x in roots[(b, rt)]))]
    for b, rt in sorted(sel):
        rs = roots[(b, rt)]
        top = min(rs, key=lambda r: r["resource"].count("/"))
        ops = [o for r in rs for o in r["ops"]]
        base = next((re.match(r"^(/\w+/resources/[0-9.]+/" + re.escape(rt) + ")", o["path"]).group(1) for o in top["ops"]
                     if re.match(r"^(/\w+/resources/[0-9.]+/" + re.escape(rt) + ")", o["path"])), "")
        acts = sorted({o["path"].split("/action/")[1] for o in ops if "/action/" in o["path"]})
        C.append(f"| {b} | {rt} | {esc(top['resource'].split('/')[-1] if b == 'scm' else top['resource'], 50)} | {esc(base)} | {len(ops)} | "
                 f"{esc(', '.join(acts), 160) or '-'} | {esc(top['description'], 140)} |")
    C.append("")
    json.dump(sorted({rt for _, rt in sel}), open(os.path.join(secdir, "rest_roots_cited.json"), "w", encoding="utf-8"))

    # Appendix D: interface catalogs from the guide TOCs
    D = ["<!-- pagebreak -->", "## Appendix D. Interface catalogs: FBDI, OTBI, BICC, SOAP, scheduled processes and job roles", ""]
    D.append("Entries are copied from the tables of contents of the Oracle 26D guides and filtered to the chapters that serve "
             "P2P and O2C. Each entry links to its Oracle page in the workbook (sheets FBDI, OTBI, BICC, SOAP, Sched_Processes, Roles).")
    D.append("")

    def rows_for(prefix, keep=lambda e: True):
        for e in toc:
            if e["book"].startswith(prefix) and e["name"] not in FRONT and keep(e):
                yield e

    def block(title, prefix, keep, cols=("Guide", "Chapter", "Entry")):
        D.append(f"### {title}")
        D.append("")
        D.append("| " + " | ".join(cols) + " |")
        D.append("|" + "---|" * len(cols))
        cnt = 0
        for e in rows_for(prefix, keep):
            D.append(f"| {e['book']} | {esc(chapter(e['path']), 50)} | {esc(e['name'], 120)} |")
            cnt += 1
        D.append("")
        return cnt

    def rel(e):
        r = REL.get(e["book"])
        return r is None or chapter(e["path"]) in r

    block("D.1 FBDI import templates", "fbdi_", lambda e: rel(e) and chapter(e["path"]) != "Overview")
    block("D.2 OTBI subject areas", "otbi_", lambda e: chapter(e["path"]) == "Subject Areas" and e["name"] != "Overview" and (
        (e["book"] == "otbi_fin" and not OTBI_EXCLUDE_FIN.search(e["name"])) or e["book"] == "otbi_proc" or
        (e["book"] == "otbi_scm" and OTBI_INCLUDE_SCM.search(e["name"]))))
    block("D.3 BICC extract data stores", "bicc_", lambda e: rel(e) and chapter(e["path"]) != "About This Guide")
    block("D.4 SOAP business object services (service entries; data objects are in the workbook)", "soap_",
          lambda e: chapter(e["path"]) in ("Business Object Services", "Process Services")
          and re.search(r"\bService\b", e["name"]) and SOAP_KEEP.search(e["name"]))
    block("D.5 Scheduled processes (Procurement and SCM guides)", "ess_", lambda e: rel(e) and chapter(e["path"]) not in (
        "About This Guide", "Scheduled Processes", "Scheduled Processes for SCM"))
    block("D.6 Predefined job roles (Security Reference guides)", "sec_", lambda e: chapter(e["path"]) == "Roles" and (
        e["book"] in ("sec_fin", "sec_proc", "sec_om") or (e["book"] == "sec_scm" and SCM_ROLE_KEEP.search(e["name"]))))

    E = ["<!-- pagebreak -->", "## Appendix E. Sources", ""]
    E.append("Oracle Fusion Cloud 26D guides used to build the catalogs (all on docs.oracle.com):")
    E.append("")
    guides = [
        ("Tables and Views for Financials", "https://docs.oracle.com/en/cloud/saas/financials/26d/oedmf/index.html"),
        ("Tables and Views for Procurement", "https://docs.oracle.com/en/cloud/saas/procurement/26d/oedmp/index.html"),
        ("Tables and Views for SCM", "https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/oedsc/index.html"),
        ("Tables and Views for Common Features", "https://docs.oracle.com/en/cloud/saas/applications-common/26d/oedma/index.html"),
        ("Tables and Views for Sales, Fusion Service, and Field Service", "https://docs.oracle.com/en/cloud/saas/sales/oedms/index.html"),
        ("REST API for Oracle Fusion Cloud Financials", "https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/index.html"),
        ("REST API for Oracle Fusion Cloud Procurement", "https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/index.html"),
        ("REST API for Oracle Fusion Cloud SCM", "https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/index.html"),
        ("REST API for Common Features", "https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/index.html"),
        ("REST API for Sales and Fusion Service", "https://docs.oracle.com/en/cloud/saas/sales/faaps/index.html"),
    ]
    seen = set()
    for e in toc:
        if e["book"] in seen:
            continue
        seen.add(e["book"])
        base = re.sub(r"/[^/]*$", "/index.html", e["url"]) if e["url"] else ""
        guides.append((e["book_title"].replace(" - Table of Contents", ""), base))
    for t, u in guides:
        E.append(f"- [{esc(t)}]({u})")
    if srcs:
        E.append("")
        E.append("Additional sources cited by the section authors and reviewers:")
        E.append("")
        for u in sorted(set(srcs)):
            if u.startswith("http"):
                E.append(f"- {u}")
    E.append("")

    md = "\n".join(parts + A + B + C + D + E) + "\n"
    open(out, "w", encoding="utf-8").write(md)
    print("written", out, len(md), "chars | appendix A tables", len(tables), "| B edges", len(edges), "| C roots", len(sel))


if __name__ == "__main__":
    main()
