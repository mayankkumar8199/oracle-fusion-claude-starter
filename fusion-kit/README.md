# fusion-kit

Ground-truth Oracle Fusion Cloud 26D catalogs and the scripts that built `..\docs`. Everything was parsed from docs.oracle.com on 2026-10-21.

| File | Contents |
|---|---|
| `catalog.json` | All 16,006 tables and views in the five 26D *Tables and Views* guides |
| `tables.jsonl` | 3,633 in-scope P2P/O2C/shared tables: columns, PK, FKs, indexes |
| `rest_catalog.json` | Every REST operation (26,152) with method, exact path and doc URL |
| `guides_toc.json` | TOC entries of the FBDI, SOAP, OTBI, BICC, scheduled-process, security, business-object, AI-agent and user guides |
| `idx/` | Grep-friendly indexes (`tables_index.tsv`, `fk_edges.tsv`, `rest_roots.tsv`, `guides_index.tsv`, `views_index.tsv`) |
| `doc_sections/` | Markdown sources of the reference document |

Common commands (run from this folder):

```
python -I scripts/check_refs.py <file.md>                         # validate tables, SQL columns, REST paths
python -I scripts/assemble.py . ..\docs\Oracle_Fusion_26D_P2P_O2C_Reference.md sources.json
python -I scripts/md2docx.py ..\docs\Oracle_Fusion_26D_P2P_O2C_Reference.md ..\docs\Oracle_Fusion_26D_P2P_O2C_Reference.docx
python -I scripts/build_xlsx.py . ..\docs\Oracle_Fusion_26D_P2P_O2C_Data_Dictionary.xlsx
python -I scripts/build_skill_resources.py . ..\.claude\skills\oracle-fusion\references\rest-resources.md
```

The Word and Excel builders need `python-docx` and `openpyxl`, which the Anaconda Python already has. To refresh the catalogs for a later release, rerun `scrape_tables.py`, `parse_rest.py` and `dump_toc.py` with that release's URLs, then `build_indexes.py`.
