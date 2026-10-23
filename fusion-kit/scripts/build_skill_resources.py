"""Generate the oracle-fusion skill's REST resource map from the official 26D endpoint index.

Usage: python -I build_skill_resources.py <fusion-kit dir> <out.md>
Every root is looked up in idx/rest_roots.tsv; unknown roots abort the build.
"""
import csv
import json
import re
import sys

STEPS = [
    ("P2P - suppliers", ["suppliers"]),
    ("P2P - requisitions", ["purchaseRequisitions"]),
    ("P2P - purchase orders and agreements", ["purchaseOrders", "draftPurchaseOrders", "purchaseAgreements"]),
    ("P2P - receiving", ["receivingReceiptRequests", "receivingReceiptTransactionRequests"]),
    ("P2P - payables invoices", ["invoices", "invoiceHolds", "payablesInterfaceInvoices"]),
    ("P2P - payments", ["payablesPayments", "paymentProcessRequests", "payablesPaymentTerms"]),
    ("O2C - customers", ["hubOrganizations", "accounts"]),
    ("O2C - pricing", ["priceLists"]),
    ("O2C - sales orders", ["salesOrdersForOrderHub"]),
    ("O2C - shipping", ["shipments", "shipmentTransactionRequests"]),
    ("O2C - billing", ["receivablesInvoices", "receivablesCreditMemos", "receivablesAdjustments", "autoInvoiceInterfaceLines"]),
    ("O2C - receipts and balances", ["standardReceipts", "receivablesCustomerAccountActivities"]),
    ("O2C - collections and revenue", ["collectionsDelinquencies", "collectionPromises", "revenueContracts"]),
    ("Shared - GL, cash, jobs", ["journalBatches", "ledgerBalances", "currencyRates", "cashExternalTransactions",
                                 "accountingPeriodStatusLOV", "erpintegrations"]),
]


def esc(s, n):
    s = " ".join(str(s).split()).replace("|", "\\|")
    return s if len(s) <= n else s[: n - 3] + "..."


def main():
    kit, out = sys.argv[1], sys.argv[2]
    rows = {}
    with open(f"{kit}/idx/rest_roots.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.setdefault(r["root"], []).append(r)
    cat = json.load(open(f"{kit}/rest_catalog.json", encoding="utf-8"))
    children = {}
    for res in cat:
        for o in res["ops"]:
            m = re.match(r"^/\w+/resources/[0-9.]+/(\w+)/[^/]+/child/(\w+)", o["path"])
            if m and not re.search(r"(?i)attachment|dff|flexfield|lob", m.group(2)):
                children.setdefault(m.group(1), [])
                if m.group(2) not in children[m.group(1)]:
                    children[m.group(1)].append(m.group(2))
    missing = [root for _, roots in STEPS for root in roots if root not in rows]
    if missing:
        sys.exit(f"unknown roots: {missing}")
    lines = [
        "# REST resources for P2P and O2C (Oracle Fusion 26D)",
        "",
        "Generated from the official *All REST Endpoints* pages (fusion-kit/idx/rest_roots.tsv). Use the root name as the",
        "`path` of `fusion_get` (with `api=\"crm\"` when the base path starts with /crmRestApi). Custom actions are listed",
        "for orientation only: the oracle-fusion tools are read-only and cannot call them.",
        "",
        "| Step | Root (fusion_get path) | api | Base path | Child paths (use as <root>/<id>/child/<name>) | Custom actions | What it is |",
        "|---|---|---|---|---|---|---|",
    ]
    for step, roots in STEPS:
        for root in roots:
            r = sorted(rows[root], key=lambda x: x["book"] != "fin")[0]
            api = "crm" if r["base_path"].startswith("/crmRestApi") else "fscm"
            kids = children.get(root, [])[:8]
            lines.append(f"| {step} | `{root}` | {api} | {r['base_path']} | {esc(', '.join(kids), 160) or '-'} | "
                         f"{esc(r['actions'].replace('; ', ', '), 120) or '-'} | {esc(r['description'], 140)} |")
    lines += ["", "More: every root and operation is in fusion-kit/rest_catalog.json and the Excel sheet REST_Operations.", ""]
    open(out, "w", encoding="utf-8").write("\n".join(lines))
    print("wrote", out, sum(len(r) for _, r in STEPS), "roots")


if __name__ == "__main__":
    main()
