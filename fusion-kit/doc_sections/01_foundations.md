## 1. Fusion foundations for P2P and O2C

Abbreviations used throughout the document:

| Abbreviation | Meaning in this document |
|---|---|
| P2P | Procure-to-Pay: supplier onboarding, requisition, sourcing, purchase order, receipt, supplier invoice, payment, accounting and bank reconciliation (section 2) |
| O2C | Order-to-Cash: customer setup, pricing, sales order, fulfillment and shipping, billing, revenue, collections, customer receipt, accounting and bank reconciliation (section 3) |
| BU, LE | Business unit, legal entity (1.2) |
| SLA | Subledger Accounting (section 4) |
| TCA | Trading Community Architecture, the Customer Data Model behind customers and supplier parties (HZ_ tables) |
| FBDI, ADFdi, ESS | File-based data import, ADF Desktop Integration (Excel workbooks), Oracle Enterprise Scheduler (scheduled processes) (sections 5 and 7) |
| OTBI, BICC, FDI | Oracle Transactional Business Intelligence, Business Intelligence Cloud Connector, Oracle Fusion Data Intelligence (section 8). BI Publisher is called Oracle Analytics Publisher in the 26D guides |
| SoD | Segregation of duties (section 12) |
| `<POD_HOST>` | Placeholder for the host name of your Fusion environment (pod) |

Counts in this section come from the five 26D Tables and Views guides (Financials, Procurement, SCM, Common, CX). The in-scope set has 3,633 documented tables. Those tables have 532 audit shadow tables, and their modules hold 1,501 views. Appendix A lists every table, and Appendix B lists the joins.

### 1.1 Product areas and table prefixes

Column key: **Tables** = in-scope tables (no shadows); **GT** = `_GT` temporary tables; **Intf** = interface and import tables (no `_GT`); **Shadow** = audit tables of in-scope base tables; **Views** = all views of the module.

| Product area (guide) | Prefixes (tables) | Tables | GT | Intf | Shadow | Views | Anchor tables |
|---|---|---|---|---|---|---|---|
| **P2P** | | | | | | | |
| Payables (fin) | AP_ 111, FINANCIALS_ 1 | 112 | 15 | 5 | 37 | 54 | AP_INVOICES_ALL, AP_INVOICE_LINES_ALL, AP_INVOICE_DISTRIBUTIONS_ALL, AP_CHECKS_ALL |
| Purchasing (proc) | PO_ 105 | 105 | 12 | 8 | 0 | 44 | PO_HEADERS_ALL, PO_LINES_ALL, PO_LINE_LOCATIONS_ALL, PO_DISTRIBUTIONS_ALL |
| Self Service Procurement (proc) | POR_ 83 | 83 | 5 | 4 | 0 | 24 | POR_REQUISITION_HEADERS_ALL, POR_REQUISITION_LINES_ALL |
| Supplier Model (proc) | POZ_ 86 | 86 | 1 | 11 | 9 | 32 | POZ_SUPPLIERS, POZ_SUPPLIER_SITES_ALL_M |
| Supplier Portal (proc) | POS_ 2 | 2 | 0 | 0 | 0 | 2 | POS_USER_ACCESS_VALUES |
| Receiving (scm) | RCV_ 21 | 21 | 0 | 5 | 1 | 4 | RCV_SHIPMENT_HEADERS, RCV_TRANSACTIONS |
| Receipt Accounting (scm) | CMR_ 107 | 107 | 47 | 3 | 0 | 58 | CMR_RCV_EVENTS, CMR_RCV_DISTRIBUTIONS |
| Sourcing (proc, adjacent) | PON_ 114 | 114 | 1 | 26 | 7 | 24 | PON_AUCTION_HEADERS_ALL, PON_BID_HEADERS |
| Supplier Qualification (proc, adjacent) | POQ_ 59 | 59 | 0 | 2 | 0 | 14 | POQ_INITIATIVES |
| Budgetary Control (fin, adjacent) | XCC_ 98 | 98 | 15 | 4 | 21 | 11 | XCC_CONTROL_BUDGETS, XCC_BALANCE_ACTIVITIES |
| **O2C** | | | | | | | |
| Order Management (scm) | DOO_ 221 | 221 | 4 | 31 | 0 | 63 | DOO_HEADERS_ALL, DOO_LINES_ALL, DOO_FULFILL_LINES_ALL |
| Pricing (scm) | QP_ 185 | 185 | 4 | 21 | 0 | 42 | QP_PRICE_LISTS_ALL_B, QP_PRICE_LIST_ITEMS |
| Shipping (scm) | WSH_ 41 | 41 | 0 | 6 | 0 | 20 | WSH_DELIVERY_DETAILS, WSH_NEW_DELIVERIES |
| Supply Chain Orchestration (scm, adjacent) | DOS_ 31 | 31 | 0 | 4 | 0 | 25 | DOS_SUPPLY_LINES |
| Supply Chain Financial Orchestration (scm, adjacent) | FOS_ 42 | 42 | 1 | 3 | 0 | 16 | FOS_FLOW_INSTANCES |
| Receivables (fin) | AR_ 254, RA_ 43, HZ_ 4, ARI_ 1 | 302 | 69 | 11 | 57 | 145 | RA_CUSTOMER_TRX_ALL, RA_CUSTOMER_TRX_LINES_ALL, AR_PAYMENT_SCHEDULES_ALL, AR_CASH_RECEIPTS_ALL, AR_RECEIVABLE_APPLICATIONS_ALL |
| Advanced Collections (fin) | IEX_ 44, AR_ 4 | 48 | 1 | 0 | 16 | 16 | IEX_DELINQUENCIES_ALL, IEX_STRATEGIES |
| Revenue Management (fin) | VRM_ 181 | 181 | 43 | 2 | 25 | 71 | VRM_CUSTOMER_CONTRACT_HEADERS, VRM_PERF_OBLIGATIONS |
| Bill Management (fin) | ARB_ 10 | 10 | 1 | 0 | 2 | 3 | ARB_REG_USER_PROFILES |
| Customer Data Model, TCA (cx) | HZ_ 220, JTF_ 21 | 241 | 3 | 102 | 44 | 41 | HZ_PARTIES, HZ_CUST_ACCOUNTS, HZ_CUST_ACCT_SITES_ALL, HZ_CUST_SITE_USES_ALL |
| Cost Management, COGS subset (scm) | CST_ 22 (module: 679) | 22 | 12 | 2 | 0 | 217* | CST_COGS_TRANSACTIONS, CST_COGS_DETAILS |
| **Shared** | | | | | | | |
| Payments (fin) | IBY_ 168 | 168 | 8 | 1 | 88 | 129 | IBY_DOCS_PAYABLE_ALL, IBY_PAYMENTS_ALL, IBY_TRXN_SUMMARIES_ALL |
| Inventory Management (scm) | INV_ 228 | 228 | 16 | 20 | 6 | 60 | INV_ORG_PARAMETERS, INV_MATERIAL_TXNS |
| Cash Management (fin) | CE_ 104 | 104 | 12 | 16 | 36 | 40 | CE_BANK_ACCOUNTS, CE_STATEMENT_LINES |
| Tax (fin) | ZX_ 156, JG_ 13, JE_ 4 | 173 | 30 | 5 | 20 | 23 | ZX_LINES, ZX_RATES_B |
| Subledger Accounting (fin) | XLA_ 184 | 184 | 43 | 9 | 22 | 48 | XLA_EVENTS, XLA_AE_HEADERS, XLA_AE_LINES, XLA_DISTRIBUTION_LINKS |
| General Ledger (fin) | GL_ 240, RG_ 1 | 241 | 64 | 20 | 53 | 34 | GL_LEDGERS, GL_CODE_COMBINATIONS, GL_JE_HEADERS, GL_JE_LINES |
| Financials Common, incl. Intercompany (fin) | FUN_ 263, FLA_ 83, MO_ 1, PER_ 1 | 348 | 12 | 33 | 58 | 98 | FUN_TRX_HEADERS, FUN_BU_USAGES |
| Legal Entity Configurator (fin) | XLE_ 14 | 14 | 0 | 0 | 8 | 17 | XLE_ENTITY_PROFILES, XLE_REGISTRATIONS |
| Middleware Extensions, FND subset (common) | FND_ 62 (module: 739) | 62 | 0 | 0 | 22 | 126* | FND_LOOKUP_VALUES_B, FND_SETID_SETS |
| **Total (40 prefixes)** | | **3,633** | 419 | 354 | 532 | 1,501 | |

\* The view count covers the whole module.

- **A prefix does not tell you the module.** HZ_CUSTOMER_PROFILES_F is documented under Receivables, AR_COLLECTORS under Advanced Collections, the JG_/JE_ VAT tables under Tax, and the FLA_ lease-accounting tables under Financials Common.
- **There is no Payables-owned supplier master.** AP_INVOICES_ALL.VENDOR_ID points to POZ_SUPPLIERS, and POZ_SUPPLIERS.PARTY_ID points to HZ_PARTIES. Some column comments cite older object names that are not in the 26D catalog, so join on the documented foreign keys (Appendix B).
- **Some modules have no audit shadow tables.** Purchasing, Self Service Procurement, Order Management, Pricing, Shipping and Receipt Accounting have none.

### 1.2 Enterprise structures that partition the data

The 26D rules behind every P2P and O2C query:

- **Ledgers.** A primary ledger combines a chart of accounts, accounting calendar, currency and accounting method. Legal entities (LEs) are assigned to ledgers, and balancing segment values to LEs ([Implementing Applications](https://docs.oracle.com/en/cloud/saas/applications-common/26d/facia/ledgers-legal-entities-balancing-segments-and-business-units.html)).
- **Business units (BUs).** "Each business unit can post transactions to a single primary ledger, but it can process transactions for many legal entities." BUs whose functions produce financial transactions need a primary ledger and a default LE. Functions used in P2P and O2C include Procurement, Requisitioning, Receiving, Payables invoicing, Payables payments, Materials management, Billing and revenue management, Customer payments and Collections management ([Business Functions](https://docs.oracle.com/en/cloud/saas/applications-common/26d/faesc/business-functions.html)).
- **Service providers.** Requisitioning and payables-invoicing BUs can be clients of a procurement BU ([Service Provider Models](https://docs.oracle.com/en/cloud/saas/applications-common/26d/faesc/service-provider-models.html)). The procurement BU owns the supplier sites, and client BUs subscribe through site assignments ([supplier sites](https://docs.oracle.com/en/cloud/saas/applications-common/26d/faesc/items-and-supplier-site-reference-data-sharing.html)).
- **Inventory organizations.** Each is "associated with one business unit, one legal entity, and one primary ledger" ([Inventory Organizations](https://docs.oracle.com/en/cloud/saas/applications-common/26d/facia/inventory-organizations.html)).
- **Reference data sets.** Each BU has a default set, which can be overridden per reference group, and the Common Set is always available ([sets](https://docs.oracle.com/en/cloud/saas/applications-common/26d/facia/how-business-units-work-with-reference-data-sets.html)). Receivables transaction types, transaction sources, memo lines and payment terms, and Order Management hold codes, use "Assignment to one set only, with common values". Payables payment terms use "Assignment to multiple sets, no common values allowed" ([shareable objects](https://docs.oracle.com/en/cloud/saas/applications-common/26d/faesc/what-reference-data-objects-can-be-shared-across-business-units.html)).

| Structure | Defined in (useful columns) | Column(s) carrying it, with examples (in-scope tables with the column) | REST read |
|---|---|---|---|
| Ledger | GL_LEDGERS (LEDGER_ID, NAME, CURRENCY_CODE, CHART_OF_ACCOUNTS_ID, LEDGER_CATEGORY_CODE) | LEDGER_ID (272): GL_JE_HEADERS, XLA_AE_HEADERS, ZX_LINES, CST_COGS_DETAILS. SET_OF_BOOKS_ID (56): AP_INVOICES_ALL, PO_DISTRIBUTIONS_ALL, RA_CUSTOMER_TRX_ALL, AR_CASH_RECEIPTS_ALL, IBY_PAYMENTS_ALL | `/fscmRestApi/resources/11.13.18.05/ledgersLOV` |
| Legal entity | XLE_ENTITY_PROFILES (LEGAL_ENTITY_ID, NAME, LEGAL_ENTITY_IDENTIFIER, PARTY_ID) | LEGAL_ENTITY_ID (131): AP_INVOICES_ALL, AP_CHECKS_ALL, RA_CUSTOMER_TRX_ALL, AR_CASH_RECEIPTS_ALL, DOO_HEADERS_ALL, GL_JE_HEADERS. SOLDTO_LE_ID (13): PO_HEADERS_ALL, POR_REQUISITION_HEADERS_ALL | `/fscmRestApi/resources/11.13.18.05/legalEntitiesLOV` |
| Business unit | FUN_ALL_BUSINESS_UNITS_V (BU_ID, BU_NAME, PRIMARY_LEDGER_ID, LEGAL_ENTITY_ID, DEFAULT_SET_ID), built on HCM organization tables. FUN_BU_USAGES holds the functions and FUN_BU_SERVICE_PROVIDERS the service providers. XLE_LE_OU_LEDGER_V maps BU to ledger and LE | ORG_ID (240, "the identifier of the business unit associated to the row"): AP_INVOICES_ALL, RA_CUSTOMER_TRX_ALL, AR_CASH_RECEIPTS_ALL, IBY_PAYMENTS_ALL, DOO_HEADERS_ALL, WSH_DELIVERY_DETAILS | `/fscmRestApi/resources/11.13.18.05/finBusinessUnitsLOV` |
| Procurement BU roles | FUN_ALL_BUSINESS_UNITS_V | PRC_BU_ID (91): PO_HEADERS_ALL, POR_REQUISITION_HEADERS_ALL, PON_AUCTION_HEADERS_ALL, POZ_SUPPLIER_SITES_ALL_M. REQ_BU_ID (58): PO_DISTRIBUTIONS_ALL, POR_REQUISITION_LINES_ALL. BILLTO_BU_ID and SOLDTO_BU_ID: PO_HEADERS_ALL. BILL_TO_BU_ID: POZ_SITE_ASSIGNMENTS_ALL_M | `/fscmRestApi/resources/11.13.18.05/procurementBusinessUnitsLOV` |
| O2C BU roles | FUN_ALL_BUSINESS_UNITS_V | On DOO_FULFILL_LINES_ALL: RECEIVABLES_ORG_ID ("Receivables Business Unit") and SELLING_PROFIT_CENTER_BU_ID. PROFIT_CENTER_BU_ID: INV_ORG_PARAMETERS, CST_COGS_DETAILS | `/fscmRestApi/resources/11.13.18.05/receivablesBusinessUnitsLOV` |
| Inventory organization | INV_ORG_PARAMETERS (ORGANIZATION_ID, ORGANIZATION_CODE, BUSINESS_UNIT_ID, LEGAL_ENTITY_ID) | ORGANIZATION_ID (131): INV_MATERIAL_TXNS, RCV_TRANSACTIONS, WSH_DELIVERY_DETAILS. Under other names: SHIP_TO_ORGANIZATION_ID (PO_LINE_LOCATIONS_ALL), DESTINATION_ORGANIZATION_ID (PO_DISTRIBUTIONS_ALL), INVENTORY_ORGANIZATION_ID (DOO_FULFILL_LINES_ALL) | `/fscmRestApi/resources/11.13.18.05/inventoryOrganizations` |
| Cost organization | CST_COST_ORGS_V (COST_ORG_ID, COST_ORG_NAME, LEGAL_ENTITY_ID) | COST_ORG_ID: CST_COGS_DETAILS, CST_COGS_TRANSACTIONS | (none) |
| Reference data set | FND_SETID_SETS (SET_ID, SET_CODE, SET_NAME). FND_SETID_ASSIGNMENTS maps REFERENCE_GROUP_NAME, DETERMINANT_TYPE and DETERMINANT_VALUE to a SET_ID | SET_ID (63): RA_CUST_TRX_TYPES_ALL, RA_BATCH_SOURCES_ALL, RA_TERMS_B, AR_COLLECTORS, HZ_CUST_ACCT_SITES_ALL, HZ_CUST_SITE_USES_ALL, DOO_HOLD_CODES_B, AP_TERMS_ST | (none) |
| Data access | FUN_USER_ROLE_DATA_ASGNMNTS (USER_GUID, ROLE_NAME, DATASEC_CONTEXT_TYPE_CODE, plus one column per context such as ORG_ID, LEDGER_ID, SET_ID, INV_ORGANIZATION_ID) | Security model, not transactions (section 12) | `/fscmRestApi/resources/11.13.18.05/dataSecurities` |

Join traps:

- **`_ALL` does not always mean ORG_ID.** 53 of the 210 in-scope tables ending `_ALL`, `_ALL_B`, `_ALL_TL` or `_ALL_M` have no ORG_ID. Purchasing uses PRC_BU_ID and REQ_BU_ID. HZ_CUST_ACCT_SITES_ALL and HZ_CUST_SITE_USES_ALL are partitioned by SET_ID.
- **Set-enabled Receivables setups use `_SEQ_ID` keys.** RA_CUSTOMER_TRX_ALL joins RA_CUST_TRX_TYPES_ALL on CUST_TRX_TYPE_SEQ_ID (the documented PK and FK); RA_CUSTOMER_TRX_ALL has no CUST_TRX_TYPE_ID column. Likewise, RA_CUSTOMER_TRX_ALL.BATCH_SOURCE_SEQ_ID joins RA_BATCH_SOURCES_ALL, and RA_CUSTOMER_TRX_LINES_ALL.MEMO_LINE_SEQ_ID joins AR_MEMO_LINES_ALL_B.
- **Payables terms keep their sets in a separate table.** The set link is in AP_TERMS_ST (TERM_ID, SET_ID), not on AP_TERMS_B.
- **The ledger column has two names.** Core AP, PO, AR and IBY transaction tables say SET_OF_BOOKS_ID. GL, XLA, ZX and CST tables, and the AP and AR reconciliation tables, say LEDGER_ID.

```sql
-- Business unit, ledger and legal entity behind Payables invoices
SELECT bu.bu_name,
       led.name                 AS ledger_name,
       led.currency_code        AS ledger_currency,
       le.name                  AS legal_entity_name,
       COUNT(*)                 AS invoice_count
FROM   ap_invoices_all          inv
JOIN   fun_all_business_units_v bu  ON bu.bu_id = inv.org_id
JOIN   gl_ledgers               led ON led.ledger_id = inv.set_of_books_id
LEFT JOIN xle_entity_profiles   le  ON le.legal_entity_id = inv.legal_entity_id
WHERE  inv.invoice_date >= :p_from_date
GROUP  BY bu.bu_name, led.name, led.currency_code, le.name;
```

### 1.3 Naming conventions

| Pattern | Meaning | In scope | All 5 guides | Examples |
|---|---|---|---|---|
| `_ALL`, `_ALL_B`, `_ALL_TL`, `_ALL_M` | All BUs or sets in one table; filter on the partition column (1.2) | 210 | 477 | AP_INVOICES_ALL, PO_HEADERS_ALL, AR_MEMO_LINES_ALL_B, POZ_SUPPLIER_SITES_ALL_M |
| `_B` / `_TL` / `_VL` | `_B` is the base row and `_TL` the text per LANGUAGE, with SOURCE_LANG. `_VL` is a view that joins them for `USERENV('LANG')` | 281 `_B`, 292 `_TL`. 259 `_B` tables have a matching `_TL` and `_VL` | 812 / 872 | AP_TERMS_B, AP_TERMS_TL and AP_TERMS_VL; ZX_RATES_B, ZX_RATES_TL and ZX_RATES_VL; DOO_STATUSES_B, DOO_STATUSES_TL and DOO_STATUSES_VL |
| `_V`, `_VL` views | Stored queries; each view page shows its SQL | 1,014 `_V`, 371 `_VL` | 1,968 `_V`, 943 `_VL` | FUN_ALL_BUSINESS_UNITS_V, XLE_LE_OU_LEDGER_V, POZ_SUPPLIERS_V |
| `_INTERFACE`, `_INTERFACE_ALL`, `_INT`, `_INT_A`, TCA import tables (HZ_IMP_PARTIES_T), Cost import tables (CST_I_AR_REVENUE_LINES) | Staging tables that file-based import loads before an import process validates them (section 7). LOAD_REQUEST_ID (262 tables) identifies the load job, for example AP_INVOICES_INTERFACE.LOAD_REQUEST_ID: "Oracle Enterprise Scheduler: request identifier of the interface load job that created the row". Error and rejection tables sit next to them | 354 | 801 | AP_INVOICES_INTERFACE, AP_INTERFACE_REJECTIONS, PO_HEADERS_INTERFACE, POR_REQ_HEADERS_INTERFACE_ALL, RCV_TRANSACTIONS_INTERFACE, POZ_SUPPLIERS_INT, RA_INTERFACE_LINES_ALL, AR_PAYMENTS_INTERFACE_ALL, DOO_ORDER_HEADERS_ALL_INT, GL_INTERFACE |
| `_GT` | Temporary work tables ("used internally by Oracle"); do not report from them | 419 | 1,005 | CST_COGS_DETAILS_GT, IBY_AR_DOC_HEADER_GT |
| Trailing `_` | Audit shadow: "AP_INVOICES_ALL_ is the audit table for AP_INVOICES_ALL". The PK is LAST_UPDATE_DATE plus LAST_UPDATED_BY plus the base key (on AP_INVOICES_ALL_: LAST_UPDATE_DATE, LAST_UPDATED_BY, INVOICE_ID). It adds AUDIT_ACTION_TYPE_ (INSERT, UPDATE, DELETE), AUDIT_CHANGE_BIT_MAP_ and AUDIT_IMPERSONATOR_ | 532 (not in the 3,633) | 1,126 | AP_INVOICES_ALL_, POZ_SUPPLIERS_, HZ_CUST_ACCOUNTS_ |
| `_BK`, `_SB` | Backup copies keyed by CUST_SET_ID ("Stores the backup data of Lookup Types"); sandbox copies keyed by SANDBOX_ID | 18 / 0 | 86 / 7 | FND_LOOKUP_TYPES_BK, FND_LOOKUP_TYPES_SB |
| `_F` | Date-effective; EFFECTIVE_START_DATE and EFFECTIVE_END_DATE are in the PK | 25 | 35 | HZ_CUSTOMER_PROFILES_F |
| `_EFF_B` / `_EFF_TL` | Extensible flexfields: CONTEXT_CODE plus ATTRIBUTE_CHAR, ATTRIBUTE_NUMBER, ATTRIBUTE_DATE and ATTRIBUTE_TIMESTAMP columns | 12 / 12 | 21 / 19 | DOO_HEADERS_EFF_B, DOO_FULFILL_LINES_EFF_B |
| `_DRAFT_ALL`, `_ARCHIVE_ALL` | Unaccepted PO changes; archived revisions | 4 + 4 | 4 + 4 | PO_HEADERS_DRAFT_ALL, PO_HEADERS_ARCHIVE_ALL |
| `_H`, `_ST` | Historical snapshots; set or BU assignments | 5 / 8 | 46 / 8 | IBY_PAYMENTS_H, AP_TERMS_ST, QP_PRICE_LISTS_ALL_B_ST |

### 1.4 Standard columns

The table checks the standard columns on the four anchor headers. The last column counts the in-scope tables that carry each group (out of 3,633).

| Group | Columns | AP_INVOICES_ALL | PO_HEADERS_ALL | RA_CUSTOMER_TRX_ALL | DOO_HEADERS_ALL | Tables |
|---|---|---|---|---|---|---|
| WHO ("Who column: indicates the user who created the row", and so on) | CREATED_BY VARCHAR2(64), CREATION_DATE TIMESTAMP, LAST_UPDATED_BY, LAST_UPDATE_DATE, LAST_UPDATE_LOGIN VARCHAR2(32) | all | all | all | all | 3,178 |
| Optimistic lock ("incremented every time that the row is updated") | OBJECT_VERSION_NUMBER | yes | yes | yes | yes | 2,752 |
| Scheduler ("Enterprise Service Scheduler: ... request ID of the job that created or last updated the row") | REQUEST_ID, JOB_DEFINITION_NAME, JOB_DEFINITION_PACKAGE | all 3 | all 3, plus PROGRAM_NAME and PROGRAM_APP_NAME | REQUEST_ID, PROGRAM_APPLICATION_ID, PROGRAM_ID, PROGRAM_UPDATE_DATE | none | 852 |
| Descriptive flexfield | ATTRIBUTE_CATEGORY, ATTRIBUTE1..n VARCHAR2(150), ATTRIBUTE_NUMBER1..n, ATTRIBUTE_DATE1..n, ATTRIBUTE_TIMESTAMP1..n | 1-15, NUMBER 1-5, DATE 1-5 | 1-20, NUMBER 1-10, DATE 1-10, TIMESTAMP 1-10 | 1-15, NUMBER 1-5, DATE 1-5 | none: uses DOO_HEADERS_EFF_B (ATTRIBUTE_CHAR1-20, ATTRIBUTE_NUMBER1-10, ATTRIBUTE_DATE1-5, ATTRIBUTE_TIMESTAMP1-5) | 1,019 |
| Global flexfield (localizations) | GLOBAL_ATTRIBUTE_CATEGORY, GLOBAL_ATTRIBUTE1..n, GLOBAL_ATTRIBUTE_NUMBER1..n, GLOBAL_ATTRIBUTE_DATE1..n | 1-20, NUMBER 1-5, DATE 1-5 | 1-20, NUMBER 1-5, DATE 1-5 | 1-30 VARCHAR2(240), NUMBER 1-12, DATE 1-5 | none | 142 |

Other columns that recur:

- **LANGUAGE and SOURCE_LANG** on `_TL` tables.
- **Seed-data columns** on setup tables: SEED_DATA_SOURCE, ORA_SEED_SET1, ORA_SEED_SET2 and MODULE_ID.
- **ENTERPRISE_ID**, documented as "used for multi-tenancy partitioning".
- **LAST_UPDATE_DATE as the incremental key.** The BICC data store `FscmTopModelAM.FinExtractAM.ApBiccExtractAM.InvoiceLineExtractPVO` uses ApInvoiceLinesAllLastUpdateDate as its incremental extract date ([data store](https://docs.oracle.com/en/cloud/saas/financials/26d/oadsr/InvoiceLineExtractPVO.html)).

### 1.5 How the tables are reached

Every documented path goes through an application service. The channels differ mainly in whether Fusion data security filters what you get back.

| Channel | R/W | Reads tables directly? | Fusion data security | Typical use | Source; section |
|---|---|---|---|---|---|
| Application pages and spreadsheets | R/W | No | Yes: "who can do what on which data". Job role plus data access by context (BU, ledger, data access set, inventory organization, reference data set) | Daily transactions | [Data Access](https://docs.oracle.com/en/cloud/saas/applications-common/26d/faser/data-access.html); 5 |
| REST (for example `/fscmRestApi/resources/11.13.18.05/invoices`) | R/W | No. Business objects are "exposed through APIs, which consist of REST resources" | Through the caller's roles: "Authorization enforces access privileges by service role." Role data policies scope rows. For example, an Accounts Payable Specialist "can manage payables invoice for the business units for which they are authorized" (verify per resource) | Integrations, agent tools. `/fscmRestApi/resources/11.13.18.05/erpintegrations` automates bulk import and export | [Quick Start](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Quick_Start.html), [business objects](https://docs.oracle.com/en/cloud/saas/financials/26d/fabof/overview.html), [AP Specialist](https://docs.oracle.com/en/cloud/saas/financials/26d/oafrm/Accounts_Payable_Specialist_job_roles.html); 6, 11 |
| SOAP business object and process services | R/W | No (ADF services, SOA composites) | A custom role holding the privileges each operation needs | Integrations built on an existing SOAP service | [About SOAP](https://docs.oracle.com/en/cloud/saas/financials/26d/oeswf/about-soap-web-services-in-oracle-applications-cloud.html); 7 |
| FBDI | Write | Interface tables only. Load Interface File for Import fills them, then the product import process moves valid rows. Rows older than 30 days are purged automatically | Through the scheduled processes the user can run (verify data checks per import) | Conversions, high-volume loads | [Load Data into Tables](https://docs.oracle.com/en/cloud/saas/financials/26d/oefbf/load-data-into-tables.html); 7 |
| OTBI | R | No. The BI Server maps subject areas to ADF view objects | Yes: "OTBI uses the same data security as Oracle Fusion Financials." Transaction Analysis Duty roles open subject areas | Real-time analysis | [OTBI](https://docs.oracle.com/en/cloud/saas/applications-common/26d/faacc/overview-of-transactional-business-intelligence.html), [subject area](https://docs.oracle.com/en/cloud/saas/financials/26d/faofb/Payables-Invoices-Transactions-Real-Time-SA-193.html); 8 |
| Analytics Publisher (BI Publisher) | R | Yes: physical SQL on the ApplicationDB_FSCM data source | No, for direct table SQL: such data "isn't subject to data-security restrictions". Secured list views apply the user's security profiles. Limit who can author data models | Formatted reports, section 9 queries | [Secured list views](https://docs.oracle.com/en/cloud/saas/financials/26d/facsf/business-intelligence-publisher-secured-list-views.html), [OM SQL](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/use-sql-to-query-order-management-data.html); 8, 9 |
| BICC | R (bulk) | No. View-object data stores; lineage spreadsheets map each view object to tables and columns | Access through roles (8.3.1): console access via a custom BIACM_ADMIN role or BI Administrator Role; file download via a custom BICC_UCM_CONTENT_ADMIN role holding OBIA_EXTRACTTRANSFORMLOAD_RWD. Row filtering is not described (verify in your pod) | Warehouse feeds. An Oracle tutorial calls it "the preferred tool" for medium to high volumes | [BICC](https://docs.oracle.com/en/cloud/saas/applications-common/26d/biacc/overview-of-business-intelligence-cloud-connector.html), [console roles](https://docs.oracle.com/en/cloud/saas/applications-common/26d/biacc/provision-a-user-with-access-to-bicc.html), [UCM roles](https://docs.oracle.com/en/cloud/saas/applications-common/26d/biacc/provision-a-user-with-access-to-bicc-content-on-ucm.html), [tutorial](https://docs.oracle.com/en/learn/fusion-saas-adw-ocidi/index.html); 8 |
| Data Extraction tool | R (bulk) | No. Business views and user-defined queries run on a read-optimized replica in Oracle Autonomous AI Lakehouse | Custom job role built around ORA_RCS_EXTRACT_SPECIALIST_DUTY (full role and permission-group list in 8.4.1); opt-in feature. Row filtering not described (verify in your pod) | New extracts. Oracle says it "will eventually replace data extracts using BI Cloud Connector (BICC) and BI Publisher" | [Playbook](https://docs.oracle.com/en/cloud/saas/applications-common/faude/data-extraction-tool.pdf), [26C note](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/ppm26c/26C-ppm-wn-f49647.htm); 8 |

Practical rules:

- **Treat Analytics Publisher SQL as unsecured.** Restrict who can open the report and its catalog folder.
- **Use the extract tools for volume.** Use REST for record-level reads and writes. Use BICC or the Data Extraction tool for bulk feeds, not BI Publisher.
- **Agents inherit their identity's access.** Oracle AI agents and Claude Code reach Fusion through these same channels, with the access of the identity they run as (sections 10 to 12).

### 1.6 Lookups and statuses

A lookup type is a set of codes with translated meanings. The three kinds are Standard, Set-enabled and Common ([Overview of Lookups](https://docs.oracle.com/en/cloud/saas/applications-common/26d/facia/overview-of-lookups.html)). You maintain them in Setup and Maintenance with Manage Standard Lookups, Manage Common Lookups and Manage Set-enabled Lookups ([predefined lookups](https://docs.oracle.com/en/cloud/saas/applications-common/26d/facia/how-can-i-access-predefined-lookups.html)). Module tasks such as Manage Payables Lookups also appear in column comments.

| Object | Content (from the view SQL in the guides) |
|---|---|
| FND_LOOKUP_TYPES, FND_LOOKUP_TYPES_TL | Types; the base table has no `_B` suffix |
| FND_LOOKUP_VALUES_B, FND_LOOKUP_VALUES_TL | Codes. The PK is LOOKUP_TYPE, LOOKUP_CODE, VIEW_APPLICATION_ID, SET_ID, ENTERPRISE_ID and SANDBOX_ID. MEANING and DESCRIPTION are in `_TL` |
| FND_LOOKUP_VALUES / FND_LOOKUP_VALUES_VL | `_B` joined to `_TL`. FND_LOOKUP_VALUES has no language filter (one row per language); FND_LOOKUP_VALUES_VL filters on `USERENV('LANG')` |
| FND_LOOKUPS, FND_COMMON_LOOKUPS, FND_SETID_LOOKUPS | Standard (VIEW_APPLICATION_ID 0, SET_ID 0), common (3, SET_ID 0) and set-enabled (2) lookups |
| AP_LOOKUP_CODES, AR_LOOKUPS, PO_LOOKUP_CODES | Payables (VIEW_APPLICATION_ID 200; meaning in DISPLAYED_FIELD), Receivables (222, SET_ID 0), Purchasing (filtered by MODULE_ID; meaning in DISPLAYED_FIELD). AP_LOOKUP_CODES and PO_LOOKUP_CODES do not filter SET_ID. Others: POZ_LOOKUP_CODES, WSH_LOOKUPS, XLA_LOOKUPS, VRM_LOOKUPS, HZ_LOOKUPS, IEX_LOOKUPS_V |

| Column | Lookup type (from the column comment) | Decode with | Documented values |
|---|---|---|---|
| AP_INVOICES_ALL.INVOICE_TYPE_LOOKUP_CODE | INVOICE TYPE (comment on AP_INVOICES_INTERFACE.INVOICE_TYPE_LOOKUP_CODE) | AP_LOOKUP_CODES | "standard, credit memo, or prepayment" |
| PO_HEADERS_ALL.FREIGHT_TERMS_LOOKUP_CODE | FREIGHT TERMS | PO_LOOKUP_CODES | not listed |
| AP_INVOICES_ALL.FINANCING_STATUS_CODE | ORA_FINANCING_STATUS_CODE | FND_LOOKUP_VALUES_VL | not listed |
| RA_CUSTOMER_TRX_ALL.DOCUMENT_STATUS_CODE | ORA_AR_TRX_DOCUMENT_STATUS | FND_LOOKUP_VALUES_VL | for example Approved |
| HZ_CUST_ACCOUNTS.CUSTOMER_TYPE | CUSTOMER_TYPE ("Receivables lookup code") | AR_LOOKUPS | I = internal, R = revenue-generating external |
| DOO_FULFILL_LINES_ALL.ACTION_TYPE_CODE | ORA_QP_ACTION_TYPES | FND_LOOKUP_VALUES_VL | Add, Terminate, Amend |

Some statuses are not lookups:

- **Order statuses.** DOO_HEADERS_ALL.STATUS_CODE and DOO_FULFILL_LINES_ALL.STATUS_CODE decode through DOO_STATUSES_VL, which returns DISPLAY_NAME in the session language. The view also carries ORCHESTRATION_APPLICATION_ID; check it if a STATUS_CODE repeats.
- **Flags.** AP_INVOICES_ALL.PAYMENT_STATUS_FLAG holds "Y, N, or P".
- **One-character codes.** WSH_DELIVERY_DETAILS.RELEASED_STATUS tracks the line through "ready to release, released, staged, shipped, or backordered".

```sql
-- 1) Module view: Payables invoice type
SELECT inv.invoice_num,
       lc.displayed_field AS invoice_type
FROM   ap_invoices_all inv
LEFT JOIN ap_lookup_codes lc
       ON lc.lookup_type = 'INVOICE TYPE'
      AND lc.lookup_code = inv.invoice_type_lookup_code
WHERE  inv.org_id = :p_bu_id;

-- 2) Base and translation tables: Receivables document status
--    (if the type exists in several views or sets, also filter lb.view_application_id and lb.set_id)
SELECT trx.trx_number,
       tl.meaning AS document_status
FROM   ra_customer_trx_all trx
LEFT JOIN fnd_lookup_values_b lb
       ON lb.lookup_type = 'ORA_AR_TRX_DOCUMENT_STATUS'
      AND lb.lookup_code = trx.document_status_code
LEFT JOIN fnd_lookup_values_tl tl
       ON tl.lookup_type         = lb.lookup_type
      AND tl.lookup_code         = lb.lookup_code
      AND tl.view_application_id = lb.view_application_id
      AND tl.set_id              = lb.set_id
      AND tl.language            = USERENV('LANG')
WHERE  trx.org_id = :p_bu_id;
```

For set-enabled lookups:

1. Find the SET_ID that applies to the business unit for the lookup's reference group. FND_SETID_ASSIGNMENTS holds the assignments, and the BU default is DEFAULT_SET_ID on FUN_ALL_BUSINESS_UNITS_V.
2. Read FND_SETID_LOOKUPS for that SET_ID. Confirm the determinant type, and whether Common Set values also apply (verify in your pod).
