## 8. Reporting and analytics (OTBI, BI Publisher, BICC, FDI)

Fusion has five reporting and extraction layers. They differ in data latency, in how they apply security and in who can build content. Use this section together with section 9 (SQL cookbook), section 6 (REST), section 7 (FBDI, SOAP, scheduled processes) and section 12 (security). The 26D guides call BI Publisher "Oracle Analytics Publisher"; this section uses both names.

| Tool | Reads from | Latency | Security applied | Typical P2P and O2C use |
|---|---|---|---|---|
| OTBI (Oracle Transactional Business Intelligence) | Subject areas mapped to ADF view objects and their tables | Real time | Same function and data security as the application pages | Ad hoc analyses, dashboards, infolets, operational lists (holds, open POs, unapplied cash) |
| BI Publisher (Oracle Analytics Publisher) | Data models: SQL on Fusion tables, OTBI analyses, other sources | Real time | Catalog permissions; SQL data sets are not data-secured (8.2.6) | Formatted documents, predefined close reports, bursting, file outputs |
| BICC (Business Intelligence Cloud Connector) | Public view objects (data stores) | Batch, full or incremental | BICC console and storage roles; treat output as unrestricted bulk data | Bulk feeds to a warehouse or data lake |
| Data Extraction tool | Business views and user-defined queries on a replicated read-optimized store | Near real-time replica, batch or on-demand extracts | Custom job role; OAuth for REST | Oracle's long-term replacement for BICC and Publisher-based extraction |
| FDI (Oracle Fusion Data Intelligence) | Prebuilt pipelines into Oracle Autonomous AI Lakehouse, analysed in Oracle Analytics Cloud | Scheduled incremental refresh | Separate FDI subscription and security | KPIs, history, cross-pillar analytics, ML predictions |

### 8.1 OTBI

#### 8.1.1 Concept

- OTBI is the real-time, self-service reporting layer. The BI Server builds physical SQL from metadata that maps subject areas to ADF view objects and their database tables. The Presentation Server formats the result.
- A subject area holds one fact folder (numeric measures) and several dimension folders (attributes such as dates, IDs and text, BI-enabled flexfield segments, and hierarchies such as Year, Quarter, Month).
- To combine subject areas in one analysis, use columns only from dimension folders common to all of them (at least one) and include one fact column from each subject area.
- The catalog is organized as Shared Folders > product family > product, for example Shared Folders > Financials > Payables. Save new or copied content in Shared Folders > Custom (preserved across updates) or My Folders (private). You can't change folder or object permissions on predefined catalog content, and changes saved outside Custom can be lost during updates; for predefined reports use Customize (8.2.1). Don't store anything in the predefined Temp folder in My Folders; Publisher uses it and purges it automatically every 24 hours.
- Flexfield segments appear in subject areas only after they are BI-enabled and the scheduled process Import Oracle Fusion Data Extensions for Transactional Business Intelligence has run.

#### 8.1.2 Build an analysis

1. Open the Reports and Analytics work area (Navigator > Tools > Reports and Analytics; verify in your pod) or the Reports and Analytics panel tab of a work area.
2. Click Create > Analysis, select a subject area and click Continue. This starts the wizard. For advanced features (dashboards, catalog management, links to application pages), click Browse Catalog.
3. Select Columns: expand folders and pick columns. Interaction Default or Drill adds the next hierarchy level; Navigate to Transaction opens the source record but needs extra link configuration; None turns off drilling; Hidden keeps a column for filters only. Use Add/Remove Subject Areas to combine subject areas.
4. Select Views: table, graph or both. A graph needs at least one fact column.
5. Edit Table or Edit Graph: layout options Columns, Prompt For, Section By and Excluded.
6. Sort and Filter, then Highlight (numeric thresholds). Turn on Preview to check the data.
7. Save: enter a name, choose a folder under Shared Folders > Custom and click Submit.
8. Optionally add the analysis to a dashboard, an infolet or the Reports and Analytics panel tab of a work area, or deliver it on a schedule with an agent.

#### 8.1.3 Security

| Layer | Mechanism | Notes |
|---|---|---|
| Subject area access | Transaction Analysis Duty roles (OBI roles, role codes start with FBI_), for example Payables Invoice Transaction Analysis Duty | Each inherits BI Consumer Role. A custom job role needs both the OBI and the Financials version of the duty (for example Fixed Asset Transaction Analysis Duty and Fixed Asset Transaction Analysis). Predefined Transaction Analysis Duty roles can't be copied or modified. |
| Data security | Data security policies and security profiles granted through the Transaction Analysis Duty roles (business unit, ledger, inventory organization and so on) | Oracle: OTBI data "is secured in a similar way to the data that's returned in application pages." Analyses fail if the user can't access every subject area in the analysis. |
| Authoring | BI Consumer Role (run), BI Author Role (create and edit; inherits BI Consumer Role), BI Administrator Role (superuser; inherits BI Author Role) | Predefined Financials job roles that inherit a Transaction Analysis Duty are assigned BI Author Role by default. None of the predefined Financials job roles inherits BI Administrator Role; Oracle recommends provisioning it in a test environment only. |
| Catalog folders | Folder reporting duty roles, for example Financials Folder Reporting Duty, Procurement Folder Reporting Duty, Supply Chain Management Folder Reporting Duty; all users hold Custom BI Web cat Reporting Duty | To hide predefined folders, build a custom role based on Custom BI Web cat Reporting Duty, run Import User and Role Application Security Data, then Browse Catalog > Administration > Reload Files and Metadata. |

#### 8.1.4 OTBI from integrations and agents

- The 26D Financials REST API documents the `analytics` resource: `GET /fscmRestApi/resources/11.13.18.05/analytics`, `GET /fscmRestApi/resources/11.13.18.05/analytics/{analyticsUniqID}` and `POST /fscmRestApi/resources/11.13.18.05/analytics/action/executeLogicalQuery`. The action takes a list of BI Logical SQL requests, each with a request identifier and a query, plus an optional asynchronous option, and returns results grouped by request identifier. Because it queries OTBI, expect the caller's OTBI roles and data security to apply (verify in your pod). This gives an agent a direct, secured read path (sections 6 and 11).
- In BI Publisher, a data set of type Oracle BI Analysis reuses an OTBI analysis, so the report inherits the subject area security of the user who runs it (verify in your pod).

```sql
-- Body query for POST /fscmRestApi/resources/11.13.18.05/analytics/action/executeLogicalQuery
-- Copy real folder and column names from an analysis built in the UI (verify in your pod).
SELECT
  "<DIMENSION_FOLDER>"."<ATTRIBUTE_COLUMN>" s_1,
  "<FACT_FOLDER>"."<MEASURE_COLUMN>" s_2
FROM "Payables Invoices - Installments Real Time"
WHERE "<DIMENSION_FOLDER>"."<FILTER_COLUMN>" = '<VALUE>'
FETCH FIRST 500 ROWS ONLY
```

#### 8.1.5 P2P subject areas

Names, grains and duty roles are from the 26D Subject Areas for Transactional Business Intelligence guides (Financials, Procurement, SCM). The Procurement and SCM guides document no table grain (shown as a dash).

| Subject area | P2P step it serves | Lowest grain | Securing duty role(s) |
|---|---|---|---|
| Supplier Registration - Supplier Registration Real Time | Supplier onboarding: registration requests | – | Supplier Master Data Transaction Analysis Duty |
| Supplier - Supplier Real Time | Supplier master: profiles, sites, business classifications, spend authorization | – | Supplier Master Data Transaction Analysis Duty |
| Supplier - Profile Change Request Real Time | Supplier maintenance: profile change requests | – | Supplier Master Data Transaction Analysis Duty |
| Supplier Import - Supplier Real Time | Export supplier data to populate import templates for bulk updates (section 7) | – | Supplier Master Data Transaction Analysis Duty |
| Supplier Qualification - Qualifications and Assessments Real Time | Supplier qualification: qualifications, assessments, initiatives | – | Supplier Qualification Analysis Duty |
| Supplier Qualification - Question Responses Real Time | Supplier qualification: question responses | – | Supplier Question and Responses Analysis Duty |
| Supplier Qualification - Supplier Eligibility Real Time | Supplier eligibility for transactions | – | Supplier Eligibility Transaction Analysis Duty |
| Supplier Qualification - Supplier Eligibility History Real Time | Eligibility history | – | Supplier Eligibility History Transaction Analysis Duty |
| Procurement - Requisitions Real Time | Requisition: line quantities and amounts, approval times, distributions | – | Purchase Requisitions Transaction Analysis Duty |
| Sourcing - Supplier Negotiations Real Time | Sourcing: negotiations, lines, requirements, invited suppliers | – | Sourcing Transaction Analysis Duty |
| Sourcing - Supplier Responses Real Time | Sourcing: supplier responses, prices and quantities | – | Sourcing Transaction Analysis Duty |
| Sourcing - Supplier Awards Real Time | Sourcing: awards | – | Sourcing Transaction Analysis Duty |
| Sourcing - Program Real Time | Sourcing programs: savings and spend goals | – | Sourcing Program Transaction Analysis Duty |
| Procurement - Purchasing Agreements Real Time | Blanket and contract agreements, price breaks, retroactive pricing | – | Agreement Transaction Analysis Duty |
| Procurement - Purchasing Real Time | Purchase order: items, costs, quantities, schedules, distributions | – | Purchase Order Transaction Analysis Duty |
| Procurement - Pending Change Orders Real Time | Change orders in process for POs and agreements | – | Pending Change Order Transaction Analysis Duty |
| Procurement - Implemented Change Orders Real Time | Implemented change orders | – | Implemented Change Order Transaction Analysis Duty |
| Supplier Portal - Purchasing Real Time | Supplier-facing PO amounts | – | Supplier Facing Purchase Order Transaction Analysis Duty |
| Receiving - In-Transit Advanced Shipment Notifications Real Time | Inbound: supplier ASNs in transit | – | Receiving Transaction Analysis Duty |
| Receiving - In-Transit Shipments Real Time | Inbound: all in-transit shipments, ASNs and internal transfers | – | Receiving Transaction Analysis Duty |
| Receiving - Purchase Receipts Real Time | Receipt against PO schedules: delivered, accepted, rejected, returned quantities | – | Receiving Transaction Analysis Duty |
| Receiving - Receipts Real Time | Receipts of all types | – | Receiving Transaction Analysis Duty |
| Receiving - Transactions Real Time | Receiving transactions into, within and out of receiving | – | Receiving Transaction Analysis Duty |
| Receiving - Unordered Receipts Real Time | Receipts not yet matched to a PO | – | Receiving Transaction Analysis Duty |
| Costing - Receipt Accounting Real Time | Receipt accounting entries and distributions (accruals) | – | Receipt Accounting Transaction Analysis Duty |
| Costing - Receipt Accounting Period Close Real Time | Close: receipt accounting period-end validation errors | – | Receipt Accounting Transaction Analysis Duty |
| Costing - Landed Costs Real Time | Estimated and actual landed costs | – | Cost Transaction Analysis Duty |
| Supplier Portal - Invoice Real Time | Supplier-facing invoices: header, line, distribution | – | Supplier Facing Invoice Transaction Analysis Duty |
| Payables Invoices - Transactions Real Time | Invoice: header, lines, distributions, holds, approval, PO and receipt match | `AP_INVOICE_DISTRIBUTIONS_ALL` | Payables Invoice Transaction Analysis Duty; also Grants, Inter Company and Project duties |
| Payables Invoices - Prepayment Applications Real Time | Prepayment application | `AP_PREPAY_APP_DISTS` | Payables Invoice Transaction Analysis Duty |
| Payables Invoices - Withholding Real Time | Withholding by supplier | `ZX_BUCKETS_F` | Payables Invoice Transaction Analysis Duty |
| Payables Invoices - Installments Real Time | Payment selection and AP aging: due dates, discounts, unpaid amounts | `AP_PAYMENT_SCHEDULES_ALL` | Payables Invoice Transaction Analysis Duty |
| Payables Payments - Disbursements Real Time | Payment: payee, bank accounts, paid installments, payment accounting | `AP_PAYMENT_HIST_DISTS` | Payables Payment Transaction Analysis Duty |
| Payables Payments - Payment History Real Time | Payment clearing, gain or loss | `AP_PAYMENT_HISTORY_ALL` | Payables Payment Transaction Analysis Duty |
| Payables Invoices - Trial Balance Real Time | Close: posted invoices and payments to reconcile AP with GL | `AP_TRIAL_BALANCES` | Payables Invoice Transaction Analysis Duty |
| Subledger Accounting - Payables Summary Reconciliation Real Time | Close: for the predefined Payables to Ledger Reconciliation report only, not ad hoc use | `AP_RECON_SUMMARY_DETAILS` | Payables to Ledger Reconciliation Transaction Analysis Duty |
| Procurement - Procure To Pay Real Time | End to end: requisitions, POs, receipts, invoices | – | Spend Transaction Analysis Duty Role |
| Procurement - Spend Real Time | Spend by supplier, business unit, item, buyer, category | – | Spend Transaction Analysis Duty Role |

Every Payables subject area is also secured by Payables to Ledger Reconciliation Transaction Analysis Duty.

#### 8.1.6 O2C subject areas

| Subject area | O2C step it serves | Lowest grain | Securing duty role(s) |
|---|---|---|---|
| Receivables - Customer Real Time | Customer: accounts, sites, profiles, billing, payment and credit data | `HZ_CUST_ACCOUNTS`, `HZ_CUST_ACCT_SITES_ALL`, `HZ_CUSTOMER_PROFILES_F` | Receivables Customer Transaction Analysis Duty |
| Receivables - Customer Tax Profile Real Time | Customer tax registrations and exemptions | `ZX_PARTY_TAX_PROFILE` | Receivables Customer Transaction Analysis Duty |
| Receivables - Customer Account Site Tax Profile Real Time | Site-level tax profiles | `HZ_CUST_ACCT_SITES_ALL`, `ZX_PARTY_TAX_PROFILE` | Receivables Customer Transaction Analysis Duty |
| Order Management - Order Headers Real Time | Order capture: headers | – | Order Transaction Analysis Duty |
| Order Management - Order Lines Real Time | Order capture: lines | – | Order Transaction Analysis Duty |
| Order Management - Price Adjustments Real Time | Pricing: discounts, promotions and other adjustments | – | Order Transaction Analysis Duty |
| Order Management - Order Holds Real Time | Holds on orders, lines and fulfillment lines | – | Order Holds Transaction Analysis Duty; Order Transaction Analysis Duty |
| Order Management - Process Instances Real Time | Orchestration: process, task and step instances; on-time fulfillment | – | Orchestration Process Transaction Analysis Duty; Order Transaction Analysis Duty |
| Supply Chain Orchestration - Supply Request Real Time | Supply requests, for example in back-to-back flows | – | Supply Chain Orchestration Transaction Analysis Duty |
| Supply Chain Orchestration - Supply Order Real Time | Supply orders managed by Supply Chain Orchestration | – | Supply Chain Orchestration Transaction Analysis Duty |
| Shipping Real Time | Pick, pack and ship: shipments and shipment lines | – | Order Pick Transaction Analysis Duty |
| Costing - New COGS and Gross Margin Details Real Time | COGS recognition, revenue and gross margin | – | COGS and Gross Margin Transaction Analysis Duty |
| Receivables - Transactions Real Time | Billing: invoices, credit memos, debit memos, chargebacks with tax, freight, sales credits, accounting | `RA_CUST_TRX_LINE_GL_DIST_ALL` | Receivables Transaction Analysis Duty; also Grants, Inter Company and Project duties |
| Receivables - Credit Memo Requests Real Time | Credit memo requests and status | `RA_CM_REQUESTS_ALL` | Receivables Transaction Analysis Duty |
| Receivables - Payment Schedules Real Time | Open items and installments, the basis for aging and collections | `AR_PAYMENT_SCHEDULES_ALL` (class other than PMT) | Receivables Transaction Analysis Duty |
| Receivables - Adjustments Real Time | Adjustments with approval and accounting | `AR_DISTRIBUTIONS_ALL` (source ADJ) | Receivables Transaction Analysis Duty |
| Receivables - Standard Receipts Application Details Real Time | Cash application: manual, spreadsheet and lockbox receipts | `AR_DISTRIBUTIONS_ALL` (receipt type CASH) | Receivables Receipts Transaction Analysis Duty |
| Receivables - Receipts Details Real Time | Receipt lifecycle: status, dates, accounting | `AR_DISTRIBUTIONS_ALL`, `AR_CASH_RECEIPT_HISTORY_ALL` | Receivables Receipts Transaction Analysis Duty |
| Receivables - Credit Memo Applications Real Time | Credit memo applications to debit items and receipts | `AR_RECEIVABLE_APPLICATIONS_ALL` (type CM) | Receivables Receipts Transaction Analysis Duty |
| Receivables - Miscellaneous Receipts Real Time | Non-trade receipts, credit card refunds and chargebacks | `AR_MISC_CASH_DISTRIBUTIONS_ALL` | Receivables Receipts Transaction Analysis Duty |
| Receivables - Receipt Conversion Rate Adjustments Real Time | Receipt rate adjustments, gains and losses | `AR_RATE_ADJUSTMENTS_ALL` | Receivables Receipts Transaction Analysis Duty |
| Receivables - Bills Receivable Real Time | Bills receivable and their applications | `AR_DISTRIBUTIONS_ALL` | Receivables Receipts Transaction Analysis Duty |
| Receivables - Revenue Adjustments Real Time | Revenue adjustments in Receivables | `AR_REVENUE_ADJUSTMENTS_ALL` | Receivables Revenue Adjustments Transaction Analysis Duty |
| Revenue Management - Customer Contracts Real Time | Revenue contracts, performance obligations, standalone selling prices, allocation, billed and recognized revenue | Four grains: contract, performance obligation, promised detail, revenue distribution | Revenue Management Administration Duty |
| Revenue Management - Standalone Selling Price Real Time | Standalone selling prices | – | Revenue Management Administration Duty |
| Subledger Accounting - Receivables Summary Reconciliation Real Time | Close: for the predefined Receivables to Ledger Reconciliation report only | `AR_RECON_SUMMARY_DETAILS` | Receivables to Ledger Reconciliation Transaction Analysis Duty |

Every Receivables subject area except the three customer subject areas is also secured by Receivables to Ledger Reconciliation Transaction Analysis Duty.

#### 8.1.7 Shared backbone subject areas (both flows)

| Subject area | Use | Lowest grain | Securing duty role(s) |
|---|---|---|---|
| Subledger Accounting - Journals Real Time | Subledger journal lines from all subledgers | `XLA_AE_LINES` | Subledger Accounting Transaction Analysis Duty; General Ledger Transaction Analysis Duty |
| Subledger Accounting - Supporting References Real Time | Supporting reference balances | `XLA_AC_BALANCES` | Subledger Accounting Transaction Analysis Duty; General Ledger Transaction Analysis Duty |
| General Ledger - Journals Real Time | GL journals, linked to subledger lines through import references | `GL_IMPORT_REFERENCES`, `GL_JE_LINES` | General Ledger Transaction Analysis Duty |
| General Ledger - Balances Real Time | Balances at any account hierarchy level; read from Essbase at run time, not from `GL_BALANCES` | `GL_BALANCES` | General Ledger Transaction Analysis Duty |
| General Ledger - Transactional Balances Real Time | Detail balances with drill to journals | `GL_BALANCES` | General Ledger Transaction Analysis Duty |
| General Ledger - Period Status Real Time | Period definitions and open or closed status | `GL_FISCAL_DAY_V` | General Ledger Transaction Analysis Duty |
| Cash Management - Bank Statements Real Time | Bank statements and their reconciliation status (cleared payments and receipts) | `CE_STATEMENT_HEADERS`, `CE_STATEMENT_LINES` | Cash Management Transaction Analysis Duty |
| Cash Management - Bank Statement Balances Real Time | Statement balances by bank account | `CE_STMT_BALANCES` | Cash Management Transaction Analysis Duty |
| Cash Management - Bank Statement Line Charges Real Time | Bank charges on statement lines | `CE_STMT_LINE_CHARGES` | Cash Management Transaction Analysis Duty |
| Cash Management - External Cash Transactions Real Time | External cash transactions from statements and reconciliation | `CE_EXTERNAL_TRANSACTIONS` | Cash Management Transaction Analysis Duty |
| Financials Common Module - Intercompany Transactions Real Time | Intercompany transactions | `FUN_TRX_HEADERS`, `FUN_DIST_LINES` | Inter Company Transaction Analysis Duty |
| Supply Chain Financial Orchestration Real Time | Intercompany trade flows, transfer pricing audit | – | Supply Chain Financials Orchestration Transaction Analysis Duty; Cost Transaction Analysis Duty |
| Inventory - Inventory Transactions Real Time | Material movements by transaction type | – | Inventory Transaction Analysis Duty |
| Inventory - Inventory Balance Real Time | On-hand by item and organization, down to lot and grade | – | Inventory Transaction Analysis Duty |
| Costing - Cost Accounting Real Time | Cost transactions and cost distributions | – | Cost Transaction Analysis Duty |
| Costing - Cost Accounting Period Close Real Time | Cost accounting period-end validation errors | – | Cost Transaction Analysis Duty |
| Costing - Period Inventory Valuation Real Time | Inventory valuation by costing period | – | Cost Transaction Analysis Duty |
| Costing - Period Intransit Inventory Valuation Real Time | In-transit valuation by costing period | – | Cost Transaction Analysis Duty |
| Budgetary Control - Transactions Real Time | Transactions validated with budgetary control and their budget consumption, where budgetary control is enabled | `XCC_BALANCE_ACTIVITIES` | Budgetary Control Analysis Duty |
| Budgetary Control - Balances Real Time | Budget, consumption, funds available | `XCC_BALANCES` | Budgetary Control Analysis Duty |
| Enterprise Contracts - Contracts Real Time | Buy-side and sell-side contracts, where Enterprise Contracts is used | – | Enterprise Contracts Transaction Analysis Duty Role |

Notes: the General Ledger and Subledger Accounting subject areas are also secured by both reconciliation duties. The 26D Financials subject area guide lists no dedicated Payments, Advanced Collections or Tax subject area; use the Payables and Receivables subject areas above and the collections aging reports in 8.5. Expenses, Fixed Assets, Joint Venture, manufacturing, maintenance, product and internal-transfer subject areas are out of scope; Appendix D lists all subject areas.

### 8.2 BI Publisher (Oracle Analytics Publisher)

#### 8.2.1 Building blocks

| Object | Holds | P2P and O2C examples |
|---|---|---|
| Data model | Data sets (SQL Query, Oracle BI Analysis, View Object, Web Service, HTTP XML feed, Excel, XML, CSV, LDAP, MDX), parameters, lists of values, bursting definitions | Open AP installments; customer statement data |
| Layout | RTF (Template Builder for Word), Excel, PDF form, eText for character-delimited or fixed-position files such as EFT and EDI, XSL | Remittance advice, dunning letters, bank files |
| Report | One or more layouts, a data model reference and properties; optional style templates and subtemplates | Predefined close reports (8.5); custom reports under Shared Folders > Custom |
| Job definition | Scheduled process wrapper (job type BIPJobType) | Lets users submit a custom report from Scheduled Processes (8.2.4) |

- Create content from Reports and Analytics > Browse Catalog > New. Creating or editing data models needs BI Publisher Data Model Developer Role ("Creates and edits Business Intelligence Publisher data models"). It is inherited by Application Developer, which Application Implementation Consultant inherits in turn.
- SQL data sets run against the Fusion schema through provisioned data sources: ApplicationDB_FSCM for Financials data, ApplicationDB_CRM and ApplicationDB_HCM. These names come from the Fusion Applications 11.1.7 Data Modeling Guide; Procurement and SCM tables are normally queried through ApplicationDB_FSCM as well (verify in your pod).
- To change a predefined report, use Customize. It copies the report, folder structure and permissions to Custom and links the copy to the original. For a predefined data model, copy it into Custom and point the custom report at the copy.
- Oracle's SaaS best practices: the 26D Financials guide points to My Oracle Support document 2145444.1. The following come from the 2016 white paper version and may have changed (verify in your pod): select only needed columns, filter with WHERE clauses and bind parameters, avoid inline queries per row and PL/SQL functions in WHERE clauses, avoid binding more than 100 values to one parameter, keep queries under the default 600-second query timeout, and schedule reports that run longer than 10 minutes instead of running them online.

#### 8.2.2 SQL data model on Appendix A tables

The example lists open AP installments and restricts rows to business units assigned to the user running the report. Section 9 has more patterns.

```sql
-- Data set OPEN_AP_INSTALLMENTS (SQL Query, data source ApplicationDB_FSCM)
SELECT aia.ORG_ID,
       pz.SEGMENT1               AS supplier_number,
       hp.PARTY_NAME             AS supplier_name,
       aia.INVOICE_NUM,
       aia.INVOICE_CURRENCY_CODE,
       aps.PAYMENT_NUM,
       aps.DUE_DATE,
       aps.AMOUNT_REMAINING
FROM   AP_INVOICES_ALL aia
JOIN   AP_PAYMENT_SCHEDULES_ALL aps ON aps.INVOICE_ID = aia.INVOICE_ID
JOIN   POZ_SUPPLIERS pz              ON pz.VENDOR_ID  = aia.VENDOR_ID
JOIN   HZ_PARTIES hp                 ON hp.PARTY_ID   = pz.PARTY_ID
WHERE  aia.CANCELLED_DATE IS NULL
AND    aps.AMOUNT_REMAINING <> 0
AND    aps.DUE_DATE <= :P_AS_OF_DATE
-- Row filter: business units assigned to the user who runs the report.
-- This approximates Fusion data security; it is not the same check (verify in your pod).
AND    EXISTS (SELECT 1
               FROM   FUN_USER_ROLE_DATA_ASGNMNTS urda
               WHERE  urda.USER_GUID = (<USER_GUID_FOR_XDO_USER_NAME>)
               AND    urda.ORG_ID = aia.ORG_ID
               AND    urda.ACTIVE_FLAG = 'Y')
-- Optional inside the subquery: AND urda.ROLE_NAME IN (<ROLE_CODE_LIST>)
```

- `FUN_USER_ROLE_DATA_ASGNMNTS` holds user, role and data security context assignments (Appendix A). USER_GUID identifies the user in Oracle Identity Management, ORG_ID is the business unit and ACTIVE_FLAG = 'Y' marks an active assignment (column comments).
- `<USER_GUID_FOR_XDO_USER_NAME>` is a scalar subquery that returns the USER_GUID of the login in `:xdo_user_name`. The user account table it needs is documented in the Tables and Views for HCM guide, outside the catalogs used for this document (verify in your pod).
- A ready-to-use alternative that matches on the user name directly, through `FUN_USER_BO_DATA_ASSIGNMENTS_V` (USERNAME, DATASEC_CONTEXT_TYPE_CODE 'ORA_BU_ID'), is the BU data-access predicate in 9.1; it needs no HCM user table. Use the same predicate across reports.
- `:xdo_user_name` is a Publisher system variable that holds the user who submits the report. Use the same filter in the business unit parameter's list of values so users can only pick their own business units.

#### 8.2.3 Bursting

A bursting definition is part of the data model:

- Split By: the element that splits the data, for example supplier or customer ID. The data set must be sorted or grouped by it.
- Deliver By: the element that drives formatting and delivery; often the same element.
- Delivery Query: SQL that returns, for each key, the template, output format, locale and delivery channel and destination.

P2P and O2C uses: remittance advice per supplier, statements and dunning letters per customer, report packs per business unit. Delivery channels such as email or FTP must be set up by a BI administrator (verify in your pod).

#### 8.2.4 Scheduling

| Option | How | Notes |
|---|---|---|
| Publisher scheduler | Open the report and click Schedule; monitor in Report Job History (verify in your pod) | For custom reports without a job definition |
| Scheduled process (ESS) | Setup and Maintenance > Application Extensions functional area > Manage Enterprise Scheduler Job Definitions and Job Sets for Financial, Supply Chain Management, and Related Applications > Manage Job Definitions tab > Create. Job Application Name FscmEss, Job Type BIPJobType (no other type), Report ID `Custom/<FAMILY>/<PRODUCT>/<REPORT>.xdo` including the .xdo extension, plus parameters | Creates a privilege with code RUN_<JOB_DEFINITION_NAME> and name "Run <display name>"; assign it to roles in the Security Console. Users then submit from Scheduled Processes, with process sets and recurrence (section 7). If the task is missing, enable the Enterprise Scheduler Job Definitions and Job Sets feature for the offering. |
| Predefined Financials reports | Scheduled Processes > Schedule New Process | Most close reports in 8.5 |

#### 8.2.5 Run reports from integrations

| Interface | Endpoint, relative to `https://<POD_HOST>` | Use |
|---|---|---|
| ExternalReportWSSService, operation runReport (protected; credentials in the SOAP header) | `/xmlpserver/services/ExternalReportWSSService?wsdl` | Oracle recommends the protected services when a synchronous call is needed. Output is always a base64-encoded string; response attachments aren't supported, so MTOM doesn't apply. Keep it for short, small reports within the integration payload limits. |
| ScheduleReportWSSService, operation getDocumentData | `/xmlpserver/services/ScheduleReportWSSService?wsdl` | Fetch output of a scheduled job |
| ReportService runReport and ScheduleService getDocumentData (public; credentials in the payload) | `/xmlpserver/services/v2/ReportService?wsdl`, `/xmlpserver/services/v2/ScheduleService?wsdl` | Same functions with credentials in the body |
| Large or long reports | Wrap the report in a custom job definition; submit with ErpIntegrationService exportBulkData or `POST /fscmRestApi/resources/11.13.18.05/erpintegrations` (ExportBulkData); with EnableEvent=Y; output goes to UCM; react to ExportBulkDataEvent (it carries the documentId) or a callback; download with the UCM GenericSoapService GET_FILE command | Oracle's asynchronous pattern for long-running or large reports (section 7) |
| Publisher REST API | `.../services/rest/v1/reports/{reportPath}/run` (multipart; URL-encoded report path) | Documented for Oracle Analytics Cloud and Oracle Analytics Server, not in the Fusion 26D guides (verify in your pod) |

#### 8.2.6 Security considerations

Oracle states that a data model with physical SQL can either select directly from tables, "in which case the data you return isn't subject to data-security restrictions", or join to secured list views, in which case the user's security profiles decide the rows. Personally identifiable information tables stay protected by virtual private database policies, also for Publisher reports. A Financials report built on `AP_INVOICES_ALL` therefore returns every business unit unless you filter it.

| Mitigation | How |
|---|---|
| Few data model authors | Oracle: "Because you can create data models on unsecured data, you're recommended to minimize the number of users who can create data models." Limit BI Publisher Data Model Developer Role (and Application Developer, which inherits it), above all in production. |
| Secured sources first | Use OTBI subject areas or Oracle BI Analysis data sets; join secured list views where they exist |
| Explicit row filters | Filter by the running user's assignments as in 8.2.2, and test with users who have different access |
| Catalog permissions | Keep data models and reports in dedicated Custom folders; grant run access through an existing or custom role, not to everyone |
| Controlled outputs | Review bursting destinations and scheduled report recipients; outputs leave Fusion security |
| Agents | Expose parameterized reports to an agent through an integration user (section 11), never a free-form SQL data model |

### 8.3 BICC (Business Intelligence Cloud Connector)

#### 8.3.1 What it is

- BICC extracts business intelligence and other data in bulk to external storage. It is part of the Oracle Applications Cloud subscription. Sign in at `https://<POD_HOST>/biacm`.
- Access: create a role (for example BIACM_ADMIN, category BI - Abstract Roles) with ESS Administrator Role and ORA_ASM_APPLICATION_IMPLEMENTATION_ADMIN_ABSTRACT, or assign BI Administrator Role. For extract files on UCM, create a role (for example BICC_UCM_CONTENT_ADMIN) with OBIA_EXTRACTTRANSFORMLOAD_RWD; files sit in the OBIAImport security group.
- A data store is a public view object (PVO). Its page in the Extract Data Stores guides (Financials, Procurement, SCM) gives the Data Store Key, Primary Keys, Initial Extract Date column, Incremental Extract Date column and attributes. For example, Payables Invoices has PK ApInvoicesInvoiceId, initial column ApInvoicesCreationDate and incremental column ApInvoicesLastUpdateDate. Lineage spreadsheets on Oracle Cloud Customer Connect map PVO attributes to the tables and columns in Appendix A.
- Offerings group data stores. You can create offerings, add data stores, select columns and add filters written as `__DATASTORE__.<BI_VO_COLUMN_NAME>`.

#### 8.3.2 Data store key prefixes

The full Data Store Key is the prefix, a dot and the PVO name from 8.3.3, for example `FscmTopModelAM.FinExtractAM.ApBiccExtractAM.InvoiceHeaderExtractPVO`.

| Guide chapter | Prefix |
|---|---|
| Payables | `FscmTopModelAM.FinExtractAM.ApBiccExtractAM` |
| Receivables | `FscmTopModelAM.FinExtractAM.ArBiccExtractAM` |
| Advanced Collections | `FscmTopModelAM.FinExtractAM.IexBiccExtractAM` |
| Cash Management | `FscmTopModelAM.FinExtractAM.CeBiccExtractAM` |
| Financials Common Module | `FscmTopModelAM.FinExtractAM.FunBiccExtractAM` |
| General Ledger | `FscmTopModelAM.FinExtractAM.GlBiccExtractAM` |
| Subledger Accounting | `FscmTopModelAM.FinExtractAM.XlaBiccExtractAM` |
| Tax | `FscmTopModelAM.FinExtractAM.ZxBiccExtractAM` |
| Purchasing | `FscmTopModelAM.PrcExtractAM.PoBiccExtractAM` |
| Self Service Procurement | `FscmTopModelAM.PrcExtractAM.PorBiccExtractAM` |
| Sourcing | `FscmTopModelAM.PrcExtractAM.PonBiccExtractAM` |
| Supplier Model | `FscmTopModelAM.PrcExtractAM.PozBiccExtractAM` |
| Receiving | `FscmTopModelAM.ScmExtractAM.RcvBiccExtractAM` |
| Receipt Accounting | `FscmTopModelAM.ScmExtractAM.CmrBiccExtractAM` |
| Cost Management | `FscmTopModelAM.ScmExtractAM.CstBiccExtractAM` |
| Inventory Management | `FscmTopModelAM.ScmExtractAM.InvBiccExtractAM` |
| Shipping | `FscmTopModelAM.ScmExtractAM.WshBiccExtractAM` |
| Distributed Order Orchestration | `FscmTopModelAM.ScmExtractAM.DooBiccExtractAM` |
| Pricing | `FscmTopModelAM.ScmExtractAM.QpBiccExtractAM` |
| Supply Chain Financial Orchestration Foundation | `FscmTopModelAM.ScmExtractAM.FosBiccExtractAM` |

#### 8.3.3 P2P and O2C data stores

Names are the 26D guide entries; the PVO name follows in parentheses.

| Step | Data stores | Notes |
|---|---|---|
| P2P: supplier | Supplier Details (`SupplierExtractPVO`); Supplier Site Details (`SupplierSiteExtractPVO`); Supplier Site Assignment Details (`SupplierSiteAssignmentExtractPVO`) | PK VendorId, VendorSiteId |
| P2P: requisition | Requisition Header (`RequisitionHeaderExtractPVO`); Requisition Lines (`RequisitionLineExtractPVO`); Requisition Distributions (`RequisitionDistributionExtractPVO`) | Self Service Procurement |
| P2P: sourcing | Negotiation Header Public Details (`NegotiationHeaderPublicBIVO`); Negotiation Response Header Details (`NegotiationResponseHeaderExtractPVO`) | Several Sourcing data stores are marked Desupported; use their replacements |
| P2P: purchase order | Purchasing Document Header Details (`PurchasingDocumentHeaderExtractPVO`); Purchasing Document Line Details (`PurchasingDocumentLineExtractPVO`); Purchasing Document Line Locations (`PurchasingDocumentLineLocationExtractPVO`); Purchasing Document Distributions (`PurchasingDocumentDistributionExtractPVO`); Purchasing Document Action History Details (`PurchasingDocumentActionHistoryExtractPVO`); Purchasing Document Versions (`PurchasingDocumentVersionExtractPVO`) | PK PoHeaderId, PoLineId, LineLocationId, PoDistributionId; incremental column LastUpdateDate. The Purchasing descriptive flexfield data stores list no PK or incremental column. |
| P2P: receipt | Receiving Inbound Shipment Headers (`ReceivingInboundShipmentHeaderExtractPVO`); Receiving Inbound Shipment Lines (`ReceivingInboundShipmentLineExtractPVO`); Receiving Receipt Transactions (`ReceivingReceiptTransactionExtractPVO`); Receiving Supply Details (`ReceivingSupplyExtractPVO`) | Receiving |
| P2P: receipt accounting | Receipt Accounting Distribution Entries (`CmrRcvDistributionsExtractPVO`); Receiving Transactions (`CmrRcvTransactionsExtractPVO`); Purchase Order Accrual Amounts (`CmrPoAccrualAmtsExtractPVO`); Accrual Clearing Amounts (`CmrAccrualClrAmtsExtractPVO`); Accrual Reconciliation Headers (`CmrAccrReconcHeadersExtractPVO`); Accrual Reconciliation Details (`CmrAccrReconcDtlsExtractPVO`); Accounts Payable Invoice Details (`CmrApInvoiceDtlsExtractPVO`) | Accrual analysis outside Fusion |
| P2P: invoice | Payables Invoices (`InvoiceHeaderExtractPVO`); Invoice Lines (`InvoiceLineExtractPVO`); Invoice Distributions (`InvoiceDistributionExtractPVO`); Invoice Holds (`InvoiceHoldExtractPVO`); Invoice Approval History (`InvoiceApprovalHistoryExtractPVO`); Invoice Groups (`InvoiceBatchExtractPVO`); Prepayment Application Distributions (`PrepaymentApplicationDistributionExtractPVO`) | PK ApInvoicesInvoiceId |
| P2P: installment and payment | Invoice Installments (`InvoicePaymentScheduleExtractPVO`); Payables Payments (`DisbursementHeaderExtractPVO`); Invoice Payments (`PaidDisbursementScheduleExtractPVO`); Payment History (`DisbursementHistoryHeaderExtractPVO`); Payment History Distributions (`PaymentHistoryDistributionExtractPVO`); setup Payment Terms (`PaymentTermHeaderExtractPVO`) and Aging Periods (`AgingPeriodHeaderExtractPVO`) | Payables Payments PK ApChecksAllCheckId |
| P2P: tax | Detailed Tax Lines (`DetailTaxLineExtractPVO`); Withholding Detailed Tax Lines (`WithholdingDetailTaxLineExtractPVO`) | The withholding page names WithholdingDetailTaxLineLastUpdatedBy as incremental column (verify in your pod) |
| O2C: customer profile | Customer Profile (`CustProfileExtractPVO`); Customer Profile Amount (`CustFinancialProfileDExtractPVO`); Customer Profile Class (`CustomerProfileClassExtractPVO`); Customer Receipt Method (`CustomerReceiptMethodExtractPVO`) | Party and account data stores aren't in these three guides; look in the CX Sales and Fusion Service extract guide or the BICC console (verify in your pod) |
| O2C: order capture | Sales Order Headers (`HeaderExtractPVO`); Sales Order Lines (`LineExtractPVO`); Order Addresses (`OrderAddressExtractPVO`); Order Totals (`OrderTotalExtractPVO`); Document References (`DocumentReferencesExtractPVO`); Billing Plans (`BillingPlanExtractPVO`); Sales Credits (`SalesCreditExtractPVO`); Payments (`PaymentExtractPVO`) | PK HeaderId, LineId |
| O2C: pricing | Order Charges (`OrderChargeExtractPVO`); Order Charge Components (`OrderChargeComponentExtractPVO`); Price Adjustments (`PriceAdjustmentExtractPVO`); Price List Headers (`PriceListHeaderBaseExtractPVO`); Pricing Strategies (`PricingStrategyBaseExtractPVO`) | Charge Definitions, Price Elements and Total Definitions list no PK or incremental column |
| O2C: orchestration and holds | Fulfillment Lines (`FulfillLineExtractPVO`); Fulfillment Details (`FulfillLineDetailExtractPVO`); Orchestration Process Instances (`ProcessInstanceExtractPVO`); Hold Instances (`HoldInstanceExtractPVO`) | PK FulfillLineId |
| O2C: shipping | Shipments (`DeliveryExtractPVO`); Shipment Lines (`DeliveryLineExtractPVO`); Shipment Line Assignments (`DeliveryLineAssignmentExtractPVO`); Shipping Costs (`ShippingCostExtractPVO`) | Shipping Costs and Outbound Loads list no incremental column |
| O2C: inventory | Inventory Material Transaction Details (`InventoryTransactionDetailExtractPVO`); Inventory On-Hand Balances (`InventoryOnhandExtractPVO`); Inventory Reservations (`InventoryReservationsExtractPVO`) | Inventory Management |
| O2C: COGS and margin | Cost of Goods Sold Transactions (`CstCogsTransactionsExtractPVO`); Cost of Goods Sold Details (`CstCogsDetailsExtractPVO`); Costing Revenue Lines (`CstRevenueLinesExtractPVO`); Gross Margin Details (`CstGrossMarginDetailsExtractPVO`); Cost Distributions (`CostDistributionsExtractPVO`); Cost Distribution Lines (`CostDistributionLinesExtractPVO`) | Cost Management |
| O2C: billing | Transaction Header (`TransactionHeaderExtractPVO`); Transaction Line (`TransactionLineExtractPVO`); Transaction Distribution (`TransactionDistributionExtractPVO`); Transaction Line Revenue Deferral (`TransactionLineRevenueDeferralExtractPVO`); Transaction Type (`TransactionTypeExtractPVO`); Transaction Source (`TransactionBatchSourceExtractPVO`) | PK RaCustomerTrxCustomerTrxId |
| O2C: open items | Payment Schedule (`PaymentScheduleExtractPVO`); Adjustment (`AdjustmentExtractPVO`); Interest Header (`InterestHeaderExtractPVO`); Interest Line (`InterestLineExtractPVO`); Balance Forward Bill (`ConsolidatedBillExtractPVO`) | Basis for aging outside Fusion |
| O2C: receipts | Receipt Header (`ReceiptHeaderExtractPVO`); Receipt History (`ReceiptHistoryExtractPVO`); Receivable Application (`ReceivableApplicationExtractPVO`); Receipt Distribution (`DistributionExtractPVO`); Receipt Batch (`ReceiptBatchExtractPVO`); Lockbox Transmission (`TransmissionExtractPVO`); Miscellaneous Cash Distribution (`MiscellaneousReceiptDistributionExtractPVO`) | Cash application history |
| O2C: revenue | Revenue Adjustment (`RevenueAdjustmentExtractPVO`); Revenue Scheduling Rule (`DistributionRuleExtractPVO`) | The 26D Financials guide has no Revenue Management or Payments chapter |
| O2C: collections | Collector (`CollectorExtractPVO`) | The only data store in the Advanced Collections chapter |
| Both: cash | Bank Statement Headers (`BankStatementHeaderExtractPVO`); Bank Statement Lines (`BankStatementLinesExtractPVO`); External Cash Transactions (`ExternalTransactionExtractPVO`); Bank Statement Reconciliation Exceptions (`ReconExceptionExtractionPVO`); Bank Account (`BankAccountExtractPVO`) | Cash Management |
| Both: subledger accounting | Subledger Journal Entry Headers (`SubledgerJournalHeaderExtractPVO`); Subledger Journal Entry Lines (`SubledgerJournalLineExtractPVO`); Subledger Journal Distribution Links (`SubledgerJournalDistributionExtractPVO`); Subledger Accounting Events (`SubledgerJournalEventExtractPVO`); Subledger Transaction Entities (`SubledgerJournalTransactionEntityExtractPVO`) | Links accounting to source documents (sections 4 and 9) |
| Both: general ledger | Journals (`JournalHeaderExtractPVO`); Journal Line (`JournalLineExtractPVO`); Journal Import Reference (`JournalImportReferenceExtractPVO`); Ledger Balance (`BalanceExtractPVO`); General Ledger Accounts (`CodeCombinationExtractPVO`); Period Statuses (`PeriodStatusExtractPVO`); Ledgers (`LedgerExtractPVO`) | Ledger Balance lists no Initial Extract Date column |
| Both: organization and intercompany | Business Units (`BusinessUnitExtractPVO`); Flow Instances (`FosFlowInstanceExtractPVO`) | Financials Common Module; Supply Chain Financial Orchestration Foundation |

#### 8.3.4 Full and incremental extracts

- Job types: Application Data Extract (incremental after the last successful extract), Active Primary Key Extract (all primary keys, to find deleted rows), Application Data and Active Primary Key Extract, Delete Expired UCM Files and Delete Files in Storage.
- An incremental run compares the data store's Incremental Extract Date column with the stored last extract date. For full loads, set an Initial Extract Date and chunk by creation date (number of days) or by a single numeric primary key (number of rows) in Advanced Extract Configuration.
- Reset Last Extract Date (offering) or Reset to Full Extract (offering or data store) when requirements change or data is corrupted.
- The last extract date is tracked across all storage locations. Don't put the same data store in schedules with different storage, or increments are lost; use the Upload to Multiple External Storage preference instead.
- Data stores whose pages list no incremental column (see 8.3.3) need full extracts or a filter strategy (verify in your pod).
- BI Broker extract mode (data store, schedule or job level) bypasses the BI Server and queries the data stores in the Fusion database directly, which can help performance. Only some data stores support it; BICC checks when you set the mode. Columns used in filters must be in the select list, date and timestamp values can differ in their time component from the default mode, and primary key extracts with a custom filter need the filter columns flagged as primary key columns.
- Cast to String handles numbers with more than 15 digits and CLOBs. BICC doesn't transform data.
- Schedules: Simple (once), Hourly, Daily, Weekly, Monthly and Yearly. Oracle warns that hourly extracts add load on the Fusion database and aren't recommended. Per schedule you set notifications, compression, split file size (1 to 5 GB, default 1 GB) and uploaded file expiry.
- Automation: the ESS web service at `/bi/ess/esswebservice` submits job BICloudConnectorJobDefinition (package oracle.apps.ess.biccc) with the extract type VO_EXTRACT, PRIMARY_KEY_EXTRACT or VO_AND_PK_EXTRACT and an optional comma-separated DATA_STORE_LIST (without it, the globally enabled data stores run). The 26D page names the type parameter EXTRACT_TYPE in one place and EXTRACT_JOB_TYPE in its sample request (verify in your pod). The metadata REST API at `/biacm/rest/meta/datastores/{dataStoreId}` returns columns, keys and the last-update-date flag.

#### 8.3.5 Destinations

| Destination | Notes |
|---|---|
| UCM (Oracle Universal Content Management, WebCenter Content) | Files land in the OBIAImport security group with a default expiry of 90 days. Purge them with Delete Expired UCM Files and don't use UCM as an archive. Optional PGP encryption, signed or unsigned; encrypted files get a .gpg suffix. |
| OCI Object Storage | Tenancy OCID, user OCID, namespace, bucket and an API signing key generated in BICC |
| Oracle Cloud Storage Service | Host, service name and container; optional OAC External Storage flag (encryption disabled) |

### 8.4 Data Extraction tool and Fusion Data Intelligence (FDI)

#### 8.4.1 Data Extraction tool

| Topic | 26D facts |
|---|---|
| What it is | Redwood application that extracts data from a read-optimized store replicated near real-time into Oracle Autonomous AI Lakehouse, which offloads extraction from the transactional database. Oracle calls it the long-term replacement for BICC and Oracle Analytics Publisher for data extraction. |
| Where | Navigator > Tools > Data Extraction; tabs for extract definitions, schedules, storage and monitoring |
| Offerings and opt-in | Available under Financials, Procurement, Order Management, Manufacturing and Supply Chain Materials Management, Fusion Accounting Hub and others. Enable the feature Redwood: Extract Application Data from a Read-Optimized Data Store using a Redwood Page; storage and user-defined queries have their own Redwood opt-ins. |
| Access | Custom job role with Enable Permission Group selected: ORA_RCS_EXTRACT_SPECIALIST_DUTY, ESSAdmin and ORA_FUN_FSCM_LOAD_INTERFACE_ADMIN_DUTY on the Roles and Privileges tab; ORA_RCS_EXTRACT_SPECIALIST_DUTY and ORA_DR_RCS_EXTRACT_INTEGRATION on the Roles and Permission Groups tab. Don't add the Supply Chain Integration Specialist job role. |
| Content | Standard business views with attributes and filtering rules, or user-defined queries for multi-table needs. Keep the timeCreated and timeUpdated attributes. Full and incremental extracts; an Initial Extract Date skips older records. |
| Output | Oracle WebCenter Content, Oracle Managed Storage or customer-managed OCI Object Storage (with server-side or client-side encryption options). Asynchronous user-defined queries return CSV (default) or JSON. |
| API | `POST /fscmRestApi/scm/redwood/11.13.18.05/runExtract` with a required Mode: ORA_SYNC runs a user-defined query and returns the output immediately; ORA_ASYNC runs a user-defined query or an extract definition and returns a request ID to monitor. Prerequisites: an OAuth client with the client credentials grant, the permissions Oracle SaaS Batch Cloud Service and Oracle Boss Cloud, and the client ID registered as a user with the custom job role. |
| AI | Data Extraction Query Transformer AI agent converts SQL into extract queries; the guide also covers a SQL to BQL agent guided journey and a callback workflow agent that receives completion details (section 10). |
| Migration from BICC | Apply BICC column headers to views; the BV_to_BICC_Database_Mapping spreadsheet (My Oracle Support KA1401) maps BICC PVOs to business views, attribute by attribute. |
| Limits | Bulk only; not for real-time needs; no custom objects or analytic views. Extract only required columns, split heavy views into separate jobs and filter. |

The 26D Business Objects guides list these extraction views for P2P and O2C. Coverage is still growing: the 26D Procurement guide lists no purchase order view, so purchase orders still need BICC or BI Publisher (verify in your pod).

| Flow | Extraction views (26D) |
|---|---|
| P2P | Suppliers (suppliersExtract), Supplier Sites (supplierSitesExtract), Requisitions (requisitionsExtract), Requisition Lines (requisitionLinesExtract), Receiving Shipment Lines (receivingShipmentLinesExtract), Receipt Accounting Distributions (receiptAcctngDistributionsExtract), Invoice Transaction (payablesInvoiceTransactionsExtract), Payables Invoice Line (payablesInvoiceLinesExtract), Payables Invoice Distribution (payablesInvoiceDistributionsExtract), Payables Invoice Holds (payablesInvoiceHoldsExtract), Invoice Installment (payablesInvoiceInstallmentsExtract), Payables Payment (payablesPaymentExtract) |
| O2C | Customer Accounts (customerAccountsExtract), Customer Account Sites (customerAccountSitesExtract), Sales Order Headers (salesOrdersExtract), Sales Order Lines (orderLinesExtract), Sales Order Fulfillment Lines (fulfillmentLinesExtract), Sales Order Holds (holdsExtract), Shipping Shipments (shipmentsExtract), Cost Accounting Cost of Goods Sold Transactions (costOfGoodsTransactionsExtract), Receivables Transactions (receivablesTransactionsExtract), Receivables Transaction Payment Schedules (receivablesTransactionPaymentSchedulesExtract), Receivables Receipts (receivablesReceiptsExtract), Collectors (collectorsExtract), Revenue Contracts (revenueContractsExtract) |
| Both | Subledger Accounting Entry Lines (subledgerAccountingEntryLinesExtract), Journal Lines (journalLinesExtract), Ledger Balances (ledgerBalancesExtract), Bank Account Statement Lines (bankAccountStatementLinesExtract) |

#### 8.4.2 Fusion Data Intelligence (FDI)

- FDI is a set of prebuilt, cloud-native analytics applications for Fusion, powered by Oracle Autonomous AI Lakehouse and Oracle Analytics Cloud, with more than 2,000 prebuilt key metrics, one analytics data model that can take external data, and prebuilt machine learning.
- It is a separate subscription, activated into the OCI tenancy that holds the Fusion environment; the welcome email names the pillars, for example Fusion ERP Analytics.
- Data arrives by scheduled incremental refresh, not in real time. Oracle notes that transactions created since the last load can be missing, that invoices without installments aren't loaded and that closed invoices before the initial extract date aren't loaded. Compare FDI Financials - AP Invoices with OTBI Payables Invoices - Installments Real Time when you validate.
- What it adds over OTBI: one analytics data model across pillars that can include external data, prebuilt KPIs and dashboards, and ML predictions, without query load on the transactional database.

| Flow | FDI functional area (26.R3) | Subject areas |
|---|---|---|
| P2P | Purchasing; Purchasing History (Preview) | Procurement - Agreements, Procurement - Purchase Orders, Procurement - Receipts, Procurement - Requisitions; Procurement - Agreement Change Orders (Preview), Procurement - Purchase Order Change Orders (Preview) |
| P2P | Procurement Spend; Procurement Suppliers; Procurement Supplier Qualification Management | Procurement - Spend; Procurement - Suppliers, Procurement - Supplier Registration; Procurement - Supplier Qualification Management |
| P2P | Procurement (ERP) Receipt Accounting; Receipts (SCM Analytics) | Procurement - Receipt Accounting (Preview), Procurement - Accrual Balances at Period End (Preview), Procurement - Accrual Balances at Receipt (Preview); SCM - Inventory Receipts |
| P2P | Accounts Payable; Payable Aging | Financials - AP Aging, Financials - AP Holds, Financials - AP Invoices, Financials - AP Liabilities, Financials - AP Payments, Financials - Payables Payments All (Opt-in GA) |
| P2P | Supplier On-time Payments Prediction (Opt-in GA) | Uses Financials - AP Aging, Financials - AP Invoices, Financials - AP Payments |
| O2C | Order Management; Draft Sales Order Management (Preview) | SCM - Sales Orders, SCM - Sales Orders Holds; SCM - Draft Sales Orders (Preview), SCM - Draft Sales Orders Holds (Preview) |
| O2C | Inventory Management; Shipping Costs (Preview) | SCM - Inventory Transactions, SCM - Picking and Shipping, SCM - Transfer Orders |
| O2C | Cost Management; Projected COGS and Gross Margin (Preview) | SCM - COGS and Gross Margin, SCM - Inventory Valuations, SCM - Item Cost; SCM - Sales Orders |
| O2C | Accounts Receivable; Receivable Aging; AR Unaccounted Transactions | Financials - AR Aging, Financials - AR Transactions, Financials - AR Receipts and Applications, Financials - AR Credit Memo Applications, Financials - AR Adjustments, Financials - AR Revenue |
| O2C | Advanced Collections (Preview) | Financials - Collections Delinquencies, Financials - Collections Scores and Risk, Financials - Collections Strategies and Work Items |
| O2C | Customer Collections Date Prediction (Opt-in GA); Customer Collections Risk Prediction (Opt-in GA) | Use Financials - AR Aging, Financials - AR Transactions |
| Both | General Ledger; Cash Management (Preview); Global Intercompany (Preview) | Financials - GL Balance Sheet, Financials - GL Detail Transactions, Financials - GL Profitability; Financials - Cash Management Bank Statements (Preview) and related; Financials - Global Intercompany Transactions (Preview) |

### 8.5 Standard reports for reconciliation and close

Type is as stated in the 26D guides; Publisher means Oracle Analytics Publisher (BI Publisher).

| Report | Type | Where to run and prerequisite | What it shows at close |
|---|---|---|---|
| Payables Trial Balance Report | Publisher | Scheduled Processes | Unpaid and partially paid invoices transferred to GL, by supplier and liability account; cross-check with the GL liability balance |
| Payables to Ledger Reconciliation Report | OTBI | Run Prepare Payables to General Ledger Reconciliation, then Shared Folders > Financials > Payables > Payables to Ledger Reconciliation | AP, accounting and GL balances with drill to Differences Detail. Primary ledger and non-adjustment periods only; begin and end balances should agree with the trial balance. |
| Payables Posted Invoice Register; Payables Posted Payment Register | OTBI (invoice register; verify the payment register type in your pod) | Shared Folders > Financials > Payables > Period Close | Accounting lines transferred to GL; used with the two reports above |
| Payables Period Close Exceptions Report | Publisher | Generated by the Payables period close; also Scheduled Processes | Transactions that prevent closing; sweep option |
| Payables Unaccounted Transactions and Sweep Report | Publisher | Scheduled Processes | Unaccounted invoices and payments, incomplete supplier portal invoices; sweep to another period |
| Payables Invoice Aging Report; Supplier Balance Aging Report | Publisher | Scheduled Processes; define aging periods on the Create Aging Periods page first | Open AP by bucket. Supplier Balance Aging uses only invoices accounted and transferred to GL, so it agrees with the trial balance. |
| Payables Open Items Revaluation Report | Publisher | Scheduled Processes, before close | Change in value of open items from rate changes |
| Payables Tax Reconciliation with General Ledger Report | Publisher | Scheduled Processes; validate, account and post invoices first | Payables tax against GL tax account balances |
| Uninvoiced Receipt Accrual Report | Scheduled process | After Create Uninvoiced Receipt Accrual in Report mode; then run Accounting mode before Create Accounting | Receipts due for period-end accrual or already accrued |
| Accrual Reconciliation Report | Scheduled process | Scheduled Processes, at least once per reporting period; privilege Run Accrual Reconciliation Report; required parameters business unit and transaction date range | Accrued supplier liabilities by business unit. If it doesn't match GL, run Transfer Costs to Cost Management, Create Receipt Accounting Distributions and Run Receipt Accounting Period End Validations first. |
| Accrual Clearing Report | Scheduled process | Receipt Accounting, at period end | Accruals cleared automatically or manually, by PO and accrual account |
| Run Receipt Accounting Period End Validations, with OTBI reports Receipt Accounting Period End Validation Summary and Receipt Accounting Period End Validation Details | Scheduled process and OTBI | Reports in Supply Chain Management/Cost Management/Transaction Analysis Samples/Period End | Health of receipt and period-end accruals; run throughout the period |
| Receivables to General Ledger Reconciliation Report | OTBI | Run Prepare Receivables to General Ledger Reconciliation, then Shared Folders > Financials > Receivables > Receivables to Ledger Reconciliation | Receivables, accounting and GL balances with drill to Differences Detail. Begin and end balances normally agree with the Receivables Aging by General Ledger Account Report; the reconciliation always excludes receipts at risk, so exclude them in the aging too. Specify the business unit and its balancing segment values when preparing. |
| Receivables Aging by General Ledger Account Report | Publisher | Shared Folders > Financials > Receivables > Receivables Balances | Open receivables by GL account as of an accounting date |
| Potential Reconciling Items Report | – | Before final accounting, after setup changes | Journal items posted to unexpected account types |
| Aging 4 Bucket Report; Aging by Collector 7 Bucket Report; Aging by Common Currency Report | Publisher | Scheduled Processes (Advanced Collections) | Customer open items by bucket, Staged or Aged method |
| Customer Account Status Report | Publisher | Shared Folders > Financials > Receivables > Receivables Balances | Open items and balance by account status or collector |
| Transaction Register; Adjustment Register; Applied Receipts Register; Unapplied Receipts Register | OTBI | Shared Folders > Financials > Receivables > Period Close | Period activity for reconciliation; on-account, unapplied and unidentified receipts by business unit |
| Receivables Open Items Revaluation Report | Publisher | Shared Folders > Financials > Receivables > Receivables Balances | Manual GL adjustment for revalued open items |
| Revenue Contract Account Activity Report | Publisher | – | Account balances by accounting contract and performance obligation, for audit |
| Open Performance Obligation Report | OTBI | Shared Folders > Financials > Revenue Management > Revenue Recognition | Open obligations with expected settlement and recognition; copy to Custom to print all rows |
| Period Inventory Valuation Report; Costing Account Balances Report | Scheduled process | For valuation, run Create Cost Accounting Distributions frequently | Inventory value by cost organization and cost book; costing account balances for the period |
| Cash to General Ledger Reconciliation Report | Publisher | Scheduled Processes; bank account and period range | GL cash against bank balance; unreconciled journals and statement lines |
| Third-Party Control Account Balances Report | Publisher | Scheduled Processes | Supplier and customer control account balances and activity |
| Subledger Period Close Exception Report | Publisher | Submitted automatically at period close when events are unprocessed or journals untransferred; also Scheduled Processes | Events and journals that fail period close validation |
| Intercompany Reconciliation Period Summary Report; Intercompany Reconciliation Summary by Source Report; Intercompany Reconciliation Journal Lines Report | Publisher | Generated by the scheduled process Prepare Intercompany Reconciliation Reporting Information; the three reports can't be run individually | Intercompany receivables against payables by provider and receiver legal entity |

### 8.6 Which reporting tool for which question

| Question | Use | Why |
|---|---|---|
| Which invoices are on hold or pending approval now? | OTBI Payables Invoices - Transactions Real Time | Real time, with the user's business unit security |
| What is due next week and which discounts are at risk? | OTBI Payables Invoices - Installments Real Time; Payables Cash Requirement Report; Payables Discounts Taken and Lost Report | Installment grain; predefined forecasts |
| Which receipts are not invoiced at period end? | Uninvoiced Receipt Accrual Report; OTBI Costing - Receipt Accounting Real Time | Same logic as the accrual process |
| Do AP and AR agree with GL? | Payables to Ledger Reconciliation Report; Receivables to General Ledger Reconciliation Report (8.5) | Oracle-maintained reconciliation logic with drill-down |
| Which orders are stuck on holds or late in fulfillment? | OTBI Order Management - Order Holds Real Time; Order Management - Process Instances Real Time | Real-time orchestration status |
| What is gross margin by customer, item or order? | OTBI Costing - New COGS and Gross Margin Details Real Time; FDI SCM - COGS and Gross Margin for trends | COGS and revenue matched in Cost Management |
| Which customers are overdue, and who collects? | Aging by Collector 7 Bucket Report; OTBI Receivables - Payment Schedules Real Time; FDI collections subject areas and predictions | Open-item grain |
| Send one formatted document per supplier or customer | BI Publisher layout with bursting | Pixel-perfect output with per-key delivery |
| A dataset no subject area covers, such as order line to invoice line to receipt | BI Publisher SQL data model on Appendix A tables (section 9) with the 8.2.6 controls, or a Data Extraction user-defined query | Full table access; you own the security |
| Nightly bulk copy to a warehouse or lake | BICC incremental extracts, or the Data Extraction tool where views exist | Built for bulk and incremental loads; the Data Extraction tool also offloads the transactional database |
| Multi-year KPIs, cross-pillar analysis, predictions | FDI | History and machine learning outside the transactional database |
| An integration or AI agent needs a small, current, user-scoped answer | OTBI `analytics` executeLogicalQuery; Publisher runReport through ExternalReportWSSService; transactional REST (section 6) | Synchronous; keeps OTBI or report security |
| An integration needs a large report file | Custom job definition with ExportBulkData and UCM; Data Extraction runExtract in ORA_ASYNC mode | Asynchronous, without synchronous payload limits |
| What blocks the period close? | Payables Period Close Exceptions Report; Subledger Period Close Exception Report; OTBI Costing - Receipt Accounting Period Close Real Time and Costing - Cost Accounting Period Close Real Time | Exception lists by subledger |
| Is the bank reconciled to GL? | Cash to General Ledger Reconciliation Report; OTBI Cash Management - Bank Statements Real Time | Book-to-bank comparison |

For agentic AI (sections 10 to 12): give an agent its own integration user with only the Transaction Analysis Duty roles and report privileges it needs. Route reads through OTBI or predefined parameterized reports so Fusion security applies. Use BICC or Data Extraction output for bulk analysis.
