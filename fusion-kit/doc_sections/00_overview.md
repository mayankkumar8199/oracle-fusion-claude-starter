# Oracle Fusion Cloud 26D - Procure-to-Pay and Order-to-Cash
Data model, every way to interact, and agentic AI - a reference for Oracle Fusion Financials practitioners
Release 26D | Prepared 2026-10-21 | Built from the Oracle Fusion Cloud 26D documentation on docs.oracle.com and the cited sources

**Scope and how to use this document.** This reference covers Procure-to-Pay (P2P) and Order-to-Cash (O2C) in Oracle Fusion Cloud Applications 26D: Financials (Payables, Payments, Receivables, Advanced Collections, Revenue Management, Bill Management, Cash Management, Tax, Subledger Accounting, General Ledger, Intercompany), Procurement (Purchasing, Self Service Procurement, Supplier Model, Supplier Portal, Sourcing where relevant), the SCM touchpoints (Receiving, Receipt Accounting, Order Management, Pricing, Shipping, Inventory, Cost Management for COGS) and the Customer Data Model (TCA). It does not cover HCM, Projects, Assets, Expenses (except where an agent touches P2P), planning or manufacturing. Sections 1 to 4 describe the data model and the two cycles. Sections 5 to 9 describe every channel into Fusion. Sections 10 and 11 cover Oracle's AI agents and Claude Code. Section 12 covers security and controls. Fusion is SaaS: you can't connect to its database. Tables are reachable only through BI Publisher data models, OTBI, BICC and the Data Extraction tool, REST and SOAP services, and the FBDI interface tables (section 1.5). Table, column and REST names were checked against the 26D catalogs. Validate every query, payload, role and agent setting in a non-production pod before you use it in production.

## Executive summary

- **Everything goes through an application service.** No channel gives direct database access. REST, SOAP, the UI, spreadsheets and OTBI apply Fusion function and data security. BI Publisher SQL on base tables does not: Oracle says such data "isn't subject to data-security restrictions" ([Secured list views](https://docs.oracle.com/en/cloud/saas/financials/26d/facsf/business-intelligence-publisher-secured-list-views.html)). Restrict who can author data models (1.5, 8.2.6).
- **Two data spines carry both cycles.** P2P runs POR_REQUISITION_HEADERS_ALL > PO_HEADERS_ALL > RCV_TRANSACTIONS > AP_INVOICES_ALL > AP_CHECKS_ALL and IBY_PAYMENTS_ALL. O2C runs HZ_CUST_ACCOUNTS > DOO_HEADERS_ALL > WSH_DELIVERY_DETAILS > RA_CUSTOMER_TRX_ALL > AR_CASH_RECEIPTS_ALL. Both meet in XLA_AE_HEADERS and XLA_AE_LINES, then GL_JE_LINES, with GL_IMPORT_REFERENCES for drill-back (2.13, 3.14, 4.1).
- **REST is the default channel for record-level work.** Use `/fscmRestApi/resources/11.13.18.05/` (customer master under `/crmRestApi`). Custom actions such as validateInvoice, applyHold and applyReceipt run business logic that a plain PATCH doesn't (section 6).
- **Use FBDI for volume.** Run it through the `erpintegrations` resource or ErpIntegrationService. Errors stay in the interface tables, and rows older than 30 days are purged automatically ([Load Data into Tables](https://docs.oracle.com/en/cloud/saas/financials/26d/oefbf/load-data-into-tables.html)). Bank statements have no 26D REST resource and are loaded by file (2.11, 3.12, 7.1 to 7.4).
- **Match the reporting tool to the question.** OTBI gives secured, real-time answers. BI Publisher gives formatted output and full-table SQL. BICC and the Data Extraction tool feed warehouses. Oracle says the Data Extraction tool "will eventually replace" BICC and BI Publisher extracts (1.5, 8.6).
- **Oracle's 26D agents cover most P2P and O2C steps.** They include the Payables Agent, Payments Agent, Payables Period Close Workspace, Cash Processing Agent, Billing Operations Workspace, Collector Workspace, Sales Order Command Center and the procurement assistants. Many are on by default but work only after security setup. Others are templates that you copy and publish in AI Agent Studio (10.2).
- **Availability changes fast.** Status is as of 2026-10-21. For example, the 26D Collector Workspace features are announced from 2026-11-13. Recheck section 10 against each quarterly update.
- **Oracle agents can't widen access, but some act without a prior approval step.** Agents run under the user's roles. The Receipt Creation Assistant creates receipts directly, and the Billing Operations Workspace approves or rejects eligible disputes when policy permits. Review execution modes and audit trails such as DOO_AGENT_ACTION_HISTORY (10.6, 12.6).
- **Oracle documents no MCP server that exposes Fusion business objects directly.** None was found in the 26D sources reviewed. To use Claude Code, build your own MCP servers over REST and BI reports: one read-only server, one report server and a separately launched write server with human approval. Alternatively, use an Oracle Integration MCP server, or call published Fusion agents through the Agent Team REST or A2A endpoints (10.5, 11).
- **Give every external agent its own integration user.** Grant a least-privilege custom role, only the BUs and ledgers it needs, and SoD checks like any person. Never grant Procurement REST Service Duty to such a user, because it opens all data. Data sent to Claude leaves Oracle's boundary, so approve the plan and the data terms first (11.1, 12.3, 12.6).
- **Give each exception queue one owner.** Keep a register of which queue an Oracle agent, a Claude workflow or a person owns, and whether it advises or acts. This avoids two automations acting on the same invoice, order or receipt (11.6.2).

### The two cycles at a glance

P2P (section 2; REST in 6.2; UI in 5.2; agents in 10.2):

| Step | Main table(s) | Main REST resource | Main UI work area | AI assistance available |
|---|---|---|---|---|
| 2.1 Supplier onboarding | POZ_SUPPLIERS, POZ_SUPPLIER_SITES_ALL_M, POZ_SITE_ASSIGNMENTS_ALL_M, HZ_PARTIES | `suppliers` | Suppliers | Supplier Qualification Workspace; Supplier Portal Advisor |
| 2.2 Requisitioning | POR_REQUISITION_HEADERS_ALL, POR_REQUISITION_LINES_ALL, POR_REQ_DISTRIBUTIONS_ALL | `purchaseRequisitions` | Purchase Requisitions (New) | Procurement Request Concierge; Purchase Requisition Creation Guide; Purchase Requisition Status Advisor; Quote to Purchase Requisition Assistant |
| 2.3 Sourcing and agreements | PON_AUCTION_HEADERS_ALL, PON_BID_HEADERS; PO_HEADERS_ALL (BLANKET, CONTRACT) | `supplierNegotiations`, `purchaseAgreements` | Negotiations; Purchase Agreements | Autonomous Sourcing Assistant; Supplier Negotiation Award Assistant; Sourcing Command Center |
| 2.4 Purchase orders | PO_HEADERS_ALL, PO_LINES_ALL, PO_LINE_LOCATIONS_ALL, PO_DISTRIBUTIONS_ALL | `purchaseOrders`, `draftPurchaseOrders` | Purchase Orders | Purchase Order Status Advisor |
| 2.5 Receiving | RCV_SHIPMENT_HEADERS, RCV_SHIPMENT_LINES, RCV_TRANSACTIONS | `receivingReceiptRequests` | Inventory Management; My Receipts | ASN Creation Assistant; Receipt Creation Assistant |
| 2.6 Invoice capture | AP_INVOICES_ALL, AP_INVOICE_LINES_ALL | `invoices`, `payablesInterfaceInvoices` | Payables > Invoices | Payables Agent (Document IO capture, invoice completion) |
| 2.7 Matching, validation, holds, approval | AP_INVOICE_DISTRIBUTIONS_ALL, AP_HOLDS_ALL | `invoices` (validateInvoice), `invoiceHolds` | Payables > Invoices | Payables Agent (anomaly controls, insights) |
| 2.8 Prepayments, memos, withholding | AP_INVOICES_ALL, AP_INVOICE_LINES_ALL, ZX_WITHHOLDING_LINES | `invoices` (applyPrepayments), `withholdingTaxLines` | Payables > Invoices | No dedicated agent in section 10 |
| 2.9 Payments | AP_CHECKS_ALL, AP_INVOICE_PAYMENTS_ALL, IBY_PAYMENTS_ALL, IBY_PAY_INSTRUCTIONS_ALL | `paymentProcessRequests`, `payablesPayments` | Payables > Payments | Payments Agent |
| 2.10 Accounting | XLA_EVENTS, XLA_AE_HEADERS, XLA_AE_LINES, GL_JE_HEADERS, GL_JE_LINES | `erpintegrations` (Create Accounting), `journalBatches` | Scheduled Processes; Receipt Accounting | Ledger Agentic Application |
| 2.11 Bank reconciliation | CE_STATEMENT_HEADERS, CE_STATEMENT_LINES, CE_RECON_HISTORY_ITEMS | `cashExternalTransactions` (no bank statement resource) | Bank Statements and Reconciliation | Cash Processing Agent for bank statement reconciliation |
| 2.12 Period close | GL_PERIOD_STATUSES, CMR_PERIOD_STATUSES, CMR_ACCRUAL_SUMMARY | `erpintegrations`, `accountingPeriodStatusLOV` | Payables Period Close Workspace; Receipt Accounting | Payables Period Close Workspace; Supplier Accruals Assistant; Cost Accounting Close Workspace |

O2C (section 3; REST in 6.3; UI in 5.3; agents in 10.2):

| Step | Main table(s) | Main REST resource | Main UI work area | AI assistance available |
|---|---|---|---|---|
| 3.1 Customer setup | HZ_PARTIES, HZ_CUST_ACCOUNTS, HZ_CUST_SITE_USES_ALL | `hubOrganizations`, `accounts` (`/crmRestApi`) | Receivables > Billing > Manage Customers | No dedicated agent in section 10 |
| 3.2 Pricing | QP_PRICE_LISTS_ALL_B, DOO_ORDER_CHARGES | `priceLists` | Pricing Administration | Price Administration Assistant |
| 3.3 Order capture | DOO_HEADERS_ALL, DOO_LINES_ALL | `salesOrdersForOrderHub` | Order Management | Purchase Orders to Sales Orders Converter; Sales Order Correction Assistant; Sales Order Assistant (Oracle advised against it in 25D) |
| 3.4 Orchestration and fulfillment | DOO_FULFILL_LINES_ALL, INV_RESERVATIONS | `salesOrdersForOrderHub`, `inventoryReservations` | Order Management | Sales Order Command Center; Order Exception Assistant |
| 3.5 Shipping | WSH_NEW_DELIVERIES, WSH_DELIVERY_DETAILS, INV_MATERIAL_TXNS | `shipments`, `shipmentTransactionRequests` | Inventory Management | Sales Order Command Center (backorders, reservation failures) |
| 3.6 Billing | RA_INTERFACE_LINES_ALL, RA_CUSTOMER_TRX_ALL, RA_CUSTOMER_TRX_LINES_ALL, AR_PAYMENT_SCHEDULES_ALL | `receivablesInvoices`, `autoInvoiceInterfaceLines` | Receivables > Billing | Billing Operations Workspace; Customer Billing Agent |
| 3.7 Revenue recognition | RA_CUST_TRX_LINE_GL_DIST_ALL, VRM_PERF_OBLIGATION_LINES | `revenueContracts` | Revenue Management | Gross Margin Analyst (COGS and margin side only) |
| 3.8 Credit and collections | AR_CMGT_CASE_FOLDERS, IEX_DELINQUENCIES_ALL, IEX_PROMISE_DETAILS | `collectionsDelinquencies`, `collectionPromises` | Credit Management; Collections | Collector Workspace |
| 3.9 Receipts and cash application | AR_CASH_RECEIPTS_ALL, AR_RECEIVABLE_APPLICATIONS_ALL | `standardReceipts` | Receivables > Accounts Receivable (Receivables Balances) | Cash Processing Agent for receipt processing and cash application |
| 3.10 Adjustments, credit memos, write-offs | AR_ADJUSTMENTS_ALL, RA_CUSTOMER_TRX_ALL | `receivablesCreditMemos`, `receivablesAdjustments` (GET only) | Receivables > Billing | Billing Operations Workspace (disputes for incorrect price and duplicate invoices) |
| 3.11 Accounting | XLA_EVENTS, XLA_AE_HEADERS, XLA_AE_LINES, GL_JE_HEADERS, GL_JE_LINES | `journalBatches` | Billing; Receivables Balances; General Ledger | Ledger Agentic Application |
| 3.12 Bank reconciliation | CE_STATEMENT_LINES, CE_RECON_HISTORY | `cashExternalTransactions` (no bank statement resource) | Bank Statements and Reconciliation | Cash Processing Agent for bank statement reconciliation |
| 3.13 Period close | GL_PERIOD_STATUSES | `accountingPeriodStatusLOV`, `erpintegrations` | Receivables Balances; General Ledger | Cost Accounting Close Workspace; Ledger Agentic Application |

All REST resources are under `https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/` unless marked otherwise. The agents listed are documented for the step. Check availability, opt-in and roles in section 10 and section 12.6.

### Ways to interact with Fusion

| Channel | What it is | Read/write | Best for | Where in this document |
|---|---|---|---|---|
| User interface | Redwood and classic pages, work areas, infotiles, Worklist approvals | R/W | One record at a time with full validation, approvals and attachments | 5.1 to 5.10 |
| ADFdi spreadsheets | Excel workbooks bound to Fusion pages, such as Create Invoice in Spreadsheet and the correction workbooks | R/W | Tens to a few thousand rows entered or corrected by a business user | 5.4, 7.5 |
| REST APIs | Business-object resources and custom actions under `fscmRestApi` and `crmRestApi` | R/W | Real-time create, read and update of single documents; agent tools | 6 |
| SOAP web services | ADF business object and process services | R/W | Operations without a suitable REST resource, or where Oracle recommends SOAP | 7.6 |
| FBDI with the ERP Integration Service | CSV templates loaded into interface tables, then imported. Automated with `erpintegrations` or ErpIntegrationService | W (plus error read-back) | Conversions and recurring high-volume loads | 7.1 to 7.4 |
| Scheduled processes | Oracle Enterprise Scheduler jobs and process sets: imports, Create Accounting, AutoInvoice, close processes | Runs processing | Recurring processing inside Fusion | 5.5, 7.7 |
| Business events and Oracle Integration | Event subscriptions that signal a change. Oracle Integration enriches the event and routes it | R (outbound signal) | Reacting to changes without polling | 7.8 |
| OTBI | Real-time analyses on subject areas; `analytics` executeLogicalQuery for integrations | R | Secured, current, user-scoped answers | 8.1 |
| BI Publisher (Oracle Analytics Publisher) | Data models (SQL or other sources), layouts, bursting, scheduling, runReport | R | Formatted documents and datasets that no subject area covers | 8.2, 9 |
| BICC and the Data Extraction tool | View-object or business-view bulk extracts, full and incremental, to storage | R (bulk) | Warehouse and lake feeds | 8.3, 8.4 |
| Oracle AI agents | Prebuilt agents and agentic apps, plus AI Agent Studio for custom agents, running inside Fusion under the user's security | R/W (with human confirmation where documented) | In-app assistance at the transaction | 10 |
| Claude Code through MCP | Claude Code calling your own MCP servers over REST and BI reports as an integration user | R; W through a separate approval-gated server | Cross-module analysis, reconciliations, data-quality work, building and testing Oracle agents | 11 |

Security for every channel, including agents: section 12.

### Companion files

| File | Content |
|---|---|
| Excel data dictionary | Sheets: Tables_P2P_O2C (the 3,633 in-scope tables with primary key, counts and description); Columns; Foreign_Keys; Indexes; All_Tables (all 16,006 table and view names in the five 26D Tables and Views guides, including audit shadow tables); REST_Operations (every operation with method and exact path); FBDI; BICC; OTBI; SOAP; Sched_Processes; Roles; Business_Objects. Every row links to its Oracle page |
| Appendix A | Complete table catalog for P2P, O2C and the shared backbone |
| Appendix B | Foreign-key join map for the core P2P and O2C tables |
| Appendix C | REST resources for P2P and O2C, with totals per REST guide |
| Appendix D | Interface catalogs: FBDI, OTBI, BICC, SOAP, scheduled processes and job roles |
| Appendix E | Sources |

### Conventions

- **Placeholders.** Angle brackets mark values from your environment, such as `<POD_HOST>`, `<BU_NAME>`, `<LEDGER_ID>`, `<INTEGRATION_USER_READ>` and `<INTEGRATION_USER_WRITE>`. The document contains no real hostnames, credentials or person names.
- **"(verify in your pod)".** This marks a value that Oracle doesn't document precisely or that depends on setup, opt-in or update level. Confirm it in a non-production pod.
- **Names.** Tables, columns and views are in upper case as Oracle documents them. REST resources are in code font and use the 26D casing. UI labels, job roles, scheduled processes and agents use Oracle's exact names.
- **REST paths.** Paths are relative to `https://<POD_HOST>` and use version `11.13.18.05`. A path without a version returns 404 (6.1).
- **SQL.** SQL appears only in fenced blocks. It is written for BI Publisher data models on the ApplicationDB_FSCM data source and was checked against the 26D column lists (section 9).
- **Naming patterns.** For `_ALL`, `_B`/`_TL`/`_VL`, `_INTERFACE`, `_GT`, audit shadow tables ending in `_`, `_F` and the other patterns, see section 1.3. For enterprise structures that partition the data, see section 1.2.
- **Dates.** Agent and feature availability is stated as of 2026-10-21 with the update in which Oracle first documented it (25C to 26D).
