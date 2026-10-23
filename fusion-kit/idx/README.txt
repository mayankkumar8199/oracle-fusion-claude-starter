Oracle Fusion Cloud 26D reference indexes (built from docs.oracle.com, 2026-10-21)
tables_index.tsv : every in-scope P2P/O2C/shared table scraped from the official Tables and Views guides
                   (Financials oedmf, Procurement oedmp, SCM oedsc, Common oedma, CX oedms) with PK + description.
                   Full columns/FKs/indexes per table: ../tables.jsonl (one JSON object per line).
fk_edges.tsv     : documented foreign keys child -> parent (columns on the child side).
views_index.tsv  : all documented views (names only).
rest_roots.tsv   : every REST root resource (fin, proc, scm, common, cx) with base path, actions, children.
                   Full operations (method + exact path): ../rest_catalog.json
guides_index.tsv : TOC entries of FBDI (fbdi_*), SOAP (soap_*), OTBI subject areas (otbi_*), BICC data stores (bicc_*),
                   scheduled processes (ess_proc, ess_scm), security references (sec_*), business objects (bo_*),
                   AI agent adoption guides (ai_*), user guides (use_*), implementation guides (impl_*).
All tables/views names: ../catalog.json. Checker: ../scripts/check_refs.py <file>
