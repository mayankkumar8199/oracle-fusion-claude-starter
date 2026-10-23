"""Extract the embedded book list JSON from Oracle docs 'books.html' pages.

Usage: python -I parse_books.py <dir> <out.json>
"""
import json
import os
import re
import sys

AREAS = {
    "books_fin.htm": "https://docs.oracle.com/en/cloud/saas/financials/26d/",
    "books_proc.htm": "https://docs.oracle.com/en/cloud/saas/procurement/26d/",
    "books_scm.htm": "https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/",
    "books_common.htm": "https://docs.oracle.com/en/cloud/saas/applications-common/26d/",
    "books_sales.htm": "https://docs.oracle.com/en/cloud/saas/sales/26d/",
}
OBJ = re.compile(r'\{"title":"(.*?)","description":"(.*?)","category":"(.*?)","html":"(.*?)"')
KEEP = re.compile(
    r"subject area|extract|data store|REST|Tables and Views|SOAP|File-Based|FBDI|Trading Community|"
    r"Customer Data|\bAI\b|Agent|Security Reference|Scheduled Process|Business Event|Analytics|"
    r"Order Management|Receivables|Payables|Procure|Collections|Cash|Tax|Subledger|Credit to Cash|"
    r"Invoice to Pay|Revenue|Supplier|Purchas|Requisition|Shipping|Inventory|Receiv|Pricing|"
    r"Implementing|Integrat|Redwood|Visual Builder|Order to|Fulfillment|Billing",
    re.I,
)


def main():
    d, out = sys.argv[1], sys.argv[2]
    books = []
    for f, base in AREAS.items():
        p = os.path.join(d, f)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8", errors="replace").read()
        for t, desc, cat, h in OBJ.findall(s):
            url = base + h if not h.startswith("http") else h
            books.append({"area": f[6:-4], "title": t, "category": cat, "url": url, "desc": desc})
    json.dump(books, open(out, "w", encoding="utf-8"), indent=0)
    print(len(books), "books")
    for b in books:
        if KEEP.search(b["title"]):
            print(f"{b['area']:6} | {b['category'][:26]:26} | {b['title'][:78]:78} | {b['url']}")


if __name__ == "__main__":
    main()
