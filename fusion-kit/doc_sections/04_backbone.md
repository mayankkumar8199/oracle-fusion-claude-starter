## 4. The shared financial backbone

Procure-to-Pay (section 2) and Order-to-Cash (section 3) end in the same backbone. Tax is calculated on the source documents, Payments moves money, Cash Management reconciles it, each subledger raises accounting events, Subledger Accounting (SLA) turns them into journal entries and General Ledger posts them. All tables named here are in the 26D Tables and Views guides (columns in Appendix A, joins in Appendix B).

| Layer | Prefix | P2P touchpoint | O2C touchpoint | Anchor tables |
|---|---|---|---|---|
| Tax | ZX | requisition, PO, receipt, AP invoice | sales order, AR transaction | ZX_LINES, ZX_REC_NREC_DIST |
| Payments | IBY | payment process requests | funds capture, settlements | IBY_PAYMENTS_ALL, IBY_TRXN_SUMMARIES_ALL |
| Cash Management | CE | payment reconciliation | receipt reconciliation | CE_STATEMENT_LINES, CE_RECON_HISTORY |
| Subledger Accounting | XLA | Payables, Receipt Accounting, Costing | Receivables, Revenue Management, Costing (COGS) | XLA_EVENTS, XLA_AE_LINES |
| General Ledger | GL | journals from P2P subledgers | journals from O2C subledgers | GL_JE_LINES, GL_BALANCES |
| Intercompany, SCFO | FUN, FOS | cross-BU purchasing | cross-BU shipping | FUN_TRX_HEADERS, FOS_FLOW_INSTANCES |
| Budgetary control | XCC | funds check on requisitions and POs | — | XCC_BALANCE_ACTIVITIES |

### 4.1 Subledger Accounting: event model and tables

#### 4.1.1 From transaction to GL line

| Step | Table | Primary key | Key columns | Next join |
|---|---|---|---|---|
| Subledger | XLA_SUBLEDGERS | APPLICATION_ID | APPLICATION_SHORT_NAME, JE_SOURCE_NAME | APPLICATION_ID |
| Entity definition | XLA_ENTITY_TYPES_B, XLA_ENTITY_ID_MAPPINGS | APPLICATION_ID, ENTITY_CODE | TRANSACTION_ID_COL_NAME_1..4 (document key) mapped to SOURCE_ID_COL_NAME_1..4 | APPLICATION_ID, ENTITY_CODE |
| Classes, types | XLA_EVENT_CLASSES_B, XLA_EVENT_TYPES_B | + EVENT_CLASS_CODE, EVENT_TYPE_CODE | ENABLED_FLAG; on event types also ACCOUNTING_FLAG, TAX_FLAG | — |
| Transaction | XLA_TRANSACTION_ENTITIES | ENTITY_ID | ENTITY_CODE, SOURCE_ID_INT_1..4, SOURCE_ID_CHAR_1..4, TRANSACTION_NUMBER, LEDGER_ID | ENTITY_ID, APPLICATION_ID |
| Event | XLA_EVENTS | EVENT_ID, APPLICATION_ID | EVENT_TYPE_CODE, EVENT_DATE, EVENT_STATUS_CODE, PROCESS_STATUS_CODE, ON_HOLD_FLAG | EVENT_ID, APPLICATION_ID |
| Journal header | XLA_AE_HEADERS | AE_HEADER_ID, APPLICATION_ID | LEDGER_ID, ACCOUNTING_DATE, JE_CATEGORY_NAME, ACCOUNTING_ENTRY_STATUS_CODE, GL_TRANSFER_STATUS_CODE | AE_HEADER_ID, APPLICATION_ID |
| Journal line | XLA_AE_LINES | AE_HEADER_ID, AE_LINE_NUM, APPLICATION_ID | CODE_COMBINATION_ID, ACCOUNTING_CLASS_CODE, ACCOUNTED_DR, ACCOUNTED_CR, PARTY_ID | GL_SL_LINK_ID, GL_SL_LINK_TABLE |
| Distribution link | XLA_DISTRIBUTION_LINKS | none documented | SOURCE_DISTRIBUTION_TYPE, SOURCE_DISTRIBUTION_ID_NUM_1..5, AE_HEADER_ID, AE_LINE_NUM, TAX_LINE_REF_ID | source distribution |
| GL reference | GL_IMPORT_REFERENCES | none documented | JE_HEADER_ID, JE_LINE_NUM, GL_SL_LINK_ID, GL_SL_LINK_TABLE | JE_HEADER_ID, JE_LINE_NUM |
| Errors, logs | XLA_ACCOUNTING_ERRORS, XLA_TRANSFER_LOGS | ACCOUNTING_ERROR_ID; GROUP_ID, LEDGER_ID | accounting errors; failed transfer recovery | — |

Keep APPLICATION_ID in every XLA join: events, headers and lines have composite keys. XLA_AE_HEADERS.ENTITY_ID is the SLA entity, not the document ID; resolve the document through XLA_TRANSACTION_ENTITIES.

#### 4.1.2 How each product raises events

| Product (APPLICATION_ID) | ENTITY_CODE predicate | SOURCE_ID_INT_1 holds | Event classes | Event ID also stored on |
|---|---|---|---|---|
| Payables (200) | `entity_code LIKE 'AP\_INVOICES' ESCAPE '\'` | AP_INVOICES_ALL.INVOICE_ID | Invoices, Credit Memos, Debit Memos, Prepayments, Prepayment Applications | AP_INVOICE_DISTRIBUTIONS_ALL, AP_PREPAY_HISTORY_ALL (ACCOUNTING_EVENT_ID) |
| Payables (200) | `entity_code LIKE 'AP\_PAYMENTS' ESCAPE '\'` | AP_CHECKS_ALL.CHECK_ID | Payments, Reconciled Payments, Refunds, Bills Payable, Escheated Payments | AP_PAYMENT_HISTORY_ALL, AP_INVOICE_PAYMENTS_ALL (ACCOUNTING_EVENT_ID) |
| Receivables (222) | `entity_code = 'TRANSACTIONS'` | RA_CUSTOMER_TRX_ALL.CUSTOMER_TRX_ID | Invoice, Credit Memo, Debit Memo, Chargeback | RA_CUST_TRX_LINE_GL_DIST_ALL.EVENT_ID |
| Receivables (222) | `entity_code = 'RECEIPTS'` | AR_CASH_RECEIPTS_ALL.CASH_RECEIPT_ID | Receipt, Miscellaneous Receipt | AR_CASH_RECEIPT_HISTORY_ALL, AR_RECEIVABLE_APPLICATIONS_ALL, AR_MISC_CASH_DISTRIBUTIONS_ALL (EVENT_ID) |
| Receivables (222) | `entity_code = 'ADJUSTMENTS'` (verify in your pod) | AR_ADJUSTMENTS_ALL.ADJUSTMENT_ID (verify) | Adjustment (entity Adjustments); a fourth entity, Bills Receivable, carries the Bills Receivable class | AR_ADJUSTMENTS_ALL.EVENT_ID |
| Receipt Accounting | ENTITY_CODE on CMR_RCV_EVENTS, mapped in CMR_RCV_EVENT_TYPES | — | receipt accounting event types: read them from CMR_RCV_EVENT_TYPES | CMR_RCV_EVENTS, CMR_RCV_DISTRIBUTIONS (EVENT_ID) |
| Cost Management | ENTITY_CODE, EVENT_CLASS_CODE, EVENT_TYPE_CODE on CST_COST_DISTRIBUTIONS | — | inventory, COGS and RMA recognition | CST_COST_DISTRIBUTIONS.EVENT_ID; lines carry AE_HEADER_ID, AE_LINE_NUM |
| Revenue Management, Cash Management | query below | — | revenue: initial performance, satisfaction, billing; cash: external transactions, bank transfers | VRM_PERF_OBLIGATION_LIN_DISTS.EVENT_ID; CE_EXTERNAL_TRANSACTIONS.ACCOUNTING_FLAG |
| Payments | no separate entity in the documented event models | — | disbursements use the Payables payment classes; funds capture uses the Receivables Receipt class | AP_CHECKS_ALL.PAYMENT_ID = IBY_PAYMENTS_ALL.PAYMENT_ID |

- The Payables codes are LIKE patterns with the underscore escaped: an exact match you can paste as is.
- Event type names show the trigger. Payables: Invoice Validated, Adjusted or Canceled; Payment Created, Adjusted or Canceled; Payment Cleared, Clearing Adjusted or Uncleared; Prepayment Applied or Unapplied; Bill Payable Matured; Payment Escheated. Receivables: Invoice, Credit Memo, Debit Memo Created or Updated; Chargeback Created; Receipt Created, Updated or Reverse; Adjustment Created.
- The Receivables event model names the entities Transactions, Receipts, Adjustments and Bills Receivable, with the process categories Transactions, Standard Receipts, Miscellaneous Receipts, Adjustments and Third Party Merge (use them in the Create Accounting Process Category parameter).
- APPLICATION_ID 200 and 222 and the entity codes come from published Fusion queries. Confirm them, and read the codes of the other subledgers:

```sql
SELECT s.application_id, s.application_short_name, s.je_source_name,
       m.entity_code, m.transaction_id_col_name_1, m.source_id_col_name_1
FROM   xla_subledgers         s
JOIN   xla_entity_id_mappings m ON m.application_id = s.application_id
ORDER  BY s.application_id, m.entity_code;
```

#### 4.1.3 Create Accounting and transfer to GL

| Step | Process | Notes |
|---|---|---|
| Stage (Receipt Accounting, Cost Management) | Create Receipt Accounting Distributions; Create Cost Accounting Distributions | entries wait in the Receipt Accounting or Costing subledger until Create Accounting |
| Account | Create Accounting (Receivables also: Create Receivables Accounting) | parameters Subledger Application, Ledger, Process Category, End Date, Accounting Mode (Draft or Final), Process Events, Report Style (Summary, Detail, No report), Transfer to General Ledger, Post in General Ledger, Journal Batch, Include User Transaction Identifiers |
| Transfer | Transfer to General Ledger = Yes, or Post Subledger Journal Entries later | a run transfers only the entries it created; earlier untransferred Final entries need Post Subledger Journal Entries; Draft entries and entries in error are not transferred until corrected; the Payables close topic calls the catch-up run Post Journal Entries to General Ledger |
| Post | Post in General Ledger = Yes, or post in GL | needs the journal posting privilege (see section 12) and the Enable Posting from Subledger option; without it entries transfer but do not post |
| Review, diagnose | Create Accounting Execution Report (submitted automatically on success or warning); Subledger Period Close Exception Report; profile option SLA: Diagnostic Enabled plus the Accounting Event Diagnostic process (Accounting Event Diagnostic Report) | errors on the Manage Accounting Errors page and in XLA_ACCOUNTING_ERRORS; purge with Purge Accounting Event Diagnostic Data; diagnostics slow Create Accounting, so enable them only while investigating |

Status codes as published for the shared SLA model (verify in your pod): EVENT_STATUS_CODE U unprocessed, I incomplete, N no action, P processed; PROCESS_STATUS_CODE D draft, E error, I invalid, R related event in error, U unprocessed, P processed; ACCOUNTING_ENTRY_STATUS_CODE F final, D draft; GL_TRANSFER_STATUS_CODE Y transferred.

#### 4.1.4 GL_IMPORT_REFERENCES drill-back

- Set Import Journal References for each subledger source on Manage Journal Sources (GL_JE_SOURCES_B.JOURNAL_REFERENCE_FLAG). The Payables posted invoice and payment registers require it.
- One GL line can summarize many subledger lines; GL_IMPORT_REFERENCES keeps the individual subledger lines behind it. Join on GL_SL_LINK_ID and GL_SL_LINK_TABLE (published Fusion examples show XLAJEL; verify). GL_JE_HEADERS.JE_FROM_SLA_FLAG marks subledger journals.
- Distribution level: XLA_DISTRIBUTION_LINKS.SOURCE_DISTRIBUTION_TYPE and SOURCE_DISTRIBUTION_ID_NUM_1. Receivables is commonly shown with RA_CUST_TRX_LINE_GL_DIST_ALL and AR_DISTRIBUTIONS_ALL as types; list the values in your pod with SELECT DISTINCT.

AP invoice and AR transaction to GL journal lines (bind variables; LEFT JOINs keep lines not yet transferred):

```sql
WITH src AS (
  SELECT 200 AS application_id, 'AP invoice' AS doc_type,
         ai.invoice_num AS doc_number, ai.invoice_id AS doc_id
  FROM   ap_invoices_all ai
  WHERE  ai.invoice_num = :p_invoice_num AND ai.org_id = :p_bu_id
  UNION ALL
  SELECT 222, 'AR transaction', rct.trx_number, rct.customer_trx_id
  FROM   ra_customer_trx_all rct
  WHERE  rct.trx_number = :p_trx_number AND rct.org_id = :p_bu_id
)
SELECT src.doc_type, src.doc_number, xte.entity_code,
       xe.event_id, xe.event_type_code,
       xah.ae_header_id, xah.accounting_date, xah.je_category_name,
       xah.accounting_entry_status_code, xah.gl_transfer_status_code,
       xal.ae_line_num, xal.accounting_class_code,
       gcc.segment1, gcc.segment2, gcc.segment3,     -- extend to your chart of accounts
       xal.accounted_dr, xal.accounted_cr,
       gjb.name AS journal_batch, gjh.name AS journal_name,
       gjh.je_source, gjh.status AS journal_status,
       gjl.je_line_num, gjl.accounted_dr AS journal_dr, gjl.accounted_cr AS journal_cr
FROM   src
JOIN   xla_transaction_entities xte
       ON  xte.application_id  = src.application_id
       AND xte.source_id_int_1 = src.doc_id
       AND (   (src.application_id = 200 AND xte.entity_code LIKE 'AP\_INVOICES' ESCAPE '\')
            OR (src.application_id = 222 AND xte.entity_code = 'TRANSACTIONS'))
JOIN   xla_events xe
       ON xe.entity_id = xte.entity_id AND xe.application_id = xte.application_id
JOIN   xla_ae_headers xah
       ON xah.event_id = xe.event_id AND xah.application_id = xe.application_id
JOIN   xla_ae_lines xal
       ON xal.ae_header_id = xah.ae_header_id AND xal.application_id = xah.application_id
JOIN   gl_code_combinations gcc ON gcc.code_combination_id = xal.code_combination_id
LEFT JOIN gl_import_references gir
       ON gir.gl_sl_link_id = xal.gl_sl_link_id AND gir.gl_sl_link_table = xal.gl_sl_link_table
LEFT JOIN gl_je_lines gjl
       ON gjl.je_header_id = gir.je_header_id AND gjl.je_line_num = gir.je_line_num
LEFT JOIN gl_je_headers gjh ON gjh.je_header_id = gjl.je_header_id
LEFT JOIN gl_je_batches gjb ON gjb.je_batch_id = gjh.je_batch_id
ORDER  BY src.doc_type, xah.ae_header_id, xal.ae_line_num;
```

For payments or receipts, use the payment or RECEIPTS row of 4.1.2 (AP_CHECKS_ALL.CHECK_ID, AR_CASH_RECEIPTS_ALL.CASH_RECEIPT_ID). Distribution-level variants are in section 9 (Q7 for AP invoices, Q14 for AR transactions).

### 4.2 General Ledger touchpoints

| Table | Primary key | Role |
|---|---|---|
| GL_LEDGERS | LEDGER_ID | CURRENCY_CODE, PERIOD_SET_NAME, CHART_OF_ACCOUNTS_ID per ledger |
| GL_PERIOD_STATUSES | APPLICATION_ID, LEDGER_ID, PERIOD_NAME | GL and subledger (Payables, Receivables) period status; CLOSING_STATUS O open, F future enterable, C closed, P permanently closed, N never opened, W close pending (W from the `accountingPeriodStatusLOV` REST resource) |
| GL_CODE_COMBINATIONS | CODE_COMBINATION_ID | every account on distributions, SLA and GL lines |
| GL_JE_SOURCES_B, GL_JE_CATEGORIES_B (+ _TL) | JE_SOURCE_NAME; JE_CATEGORY_NAME | sources (JOURNAL_REFERENCE_FLAG) and categories; display names USER_JE_SOURCE_NAME, USER_JE_CATEGORY_NAME |
| GL_INTERFACE | none | Journal Import interface; loaded by FBDI Journal Import |
| GL_JE_BATCHES | JE_BATCH_ID | STATUS (values from lookup MJE_BATCH_STATUS; list them in your pod) |
| GL_JE_HEADERS | JE_HEADER_ID | JE_SOURCE, JE_CATEGORY, STATUS, ACTUAL_FLAG, JE_FROM_SLA_FLAG |
| GL_JE_LINES | JE_HEADER_ID, JE_LINE_NUM | CODE_COMBINATION_ID, ACCOUNTED_DR, ACCOUNTED_CR, GL_SL_LINK_ID, GL_SL_LINK_TABLE, STATUS |
| GL_BALANCES | none documented | by LEDGER_ID, CODE_COMBINATION_ID, CURRENCY_CODE, PERIOD_NAME; ACTUAL_FLAG balance type (Actual, Budget, Encumbrance) |

| Subledger | Journal source | Default categories |
|---|---|---|
| Payables | Payables | Purchase Invoices (invoice classes), Payments, Reconciled Payments (from the Payables event class options; verify) |
| Receivables | Receivables | Sales Invoices (Invoice), Credit Memos, Debit Memos, Chargebacks, Receipts (Receipt), Misc Receipts (Miscellaneous Receipt), Adjustment, Bills Receivable |
| Others | XLA_SUBLEDGERS.JE_SOURCE_NAME | read XLA_AE_HEADERS.JE_CATEGORY_NAME |

GL close, after the subledgers (4.9):

1. Import Journals for non-SLA feeds; post everything.
2. Revalue Balances and post the results; revalue before translating.
3. Translate General Ledger Account Balances once journals and translation rates are final.
4. Close on Manage Accounting Periods or as a scheduled process. With the ledger option Prevent General Ledger Period Closure When Open Subledger Periods Exist (Specify Ledger Options, Period Close section), open Assets, Cost Management, Payables, Project Foundation, Receivables or Revenue Management periods block the close (Assets excluded by default; lookup type ORA_GL_INCLD_STRICT_PRD_CLOSE excludes others).
5. Always blocking: unprocessed or untransferred subledger transactions, pending GL interface rows, unposted journals, and intercompany transactions in Approved, Error, Received, Sent, Transferred to provider general ledger, Transferred to receiver general ledger or Transferred to Receivables.
6. Monitor with Close Monitor (Close Monitor task in the Period Close work area, or the Open Subledgers infolet on the General Accounting Infolets page): period status for General Ledger, Payables, Receivables, Assets, Projects and Costing.

Interfaces: REST `journalBatches`, `ledgerBalances`, `accountingPeriodStatusLOV`, `journalSourcesLOV`, `journalCategoriesLOV`; FBDI Journal Import; OTBI General Ledger - Journals Real Time, General Ledger - Period Status Real Time, Subledger Accounting - Journals Real Time.

### 4.3 Tax

| Cycle | Document | When Oracle Fusion Tax calculates | Stored in |
|---|---|---|---|
| P2P | Requisition | quote mode, reference only; nonrecoverable part included in the approval amount | POR_REQ_DISTRIBUTIONS_ALL (RECOVERABLE_TAX, NONRECOVERABLE_TAX) |
| P2P | Purchase order | automatically; tax lines view-only, determinants editable; recalculated as of the PO date | ZX_LINES, ZX_REC_NREC_DIST; PO_DISTRIBUTIONS_ALL (RECOVERABLE_TAX, NONRECOVERABLE_TAX) |
| P2P | Receipt (tax point basis Delivery) | receipt accounting process, from receipt attributes | CMR_TRANSACTION_TAXES |
| P2P | Payables invoice | on validation, when tax lines are opened, or Calculate Taxes; PO-matched invoices copy PO tax lines and recalculate at invoice date; differences become tax invoice price, tax rate and tax conversion rate variances | ZX_LINES, ZX_LINES_SUMMARY, ZX_REC_NREC_DIST; AP_INVOICE_LINES_ALL.SUMMARY_TAX_LINE_ID; AP_INVOICE_DISTRIBUTIONS_ALL.DETAIL_TAX_DIST_ID |
| O2C | Sales order | after Save, Submit or a shipping method change | DOO_ORDER_TAX_DETAILS (via DOO_ORDER_CHARGES, DOO_ORDER_CHARGE_COMPONENTS) |
| O2C | Receivables transaction | on save, edit or complete; recalculated on change | ZX_LINES; RA_CUSTOMER_TRX_LINES_ALL.TAX_LINE_ID |
| O2C | Receivables adjustment | in the tax repository only if the activity has Recoverable set | ZX_LINES |

| Table | Primary key | Content |
|---|---|---|
| ZX_LINES | TAX_LINE_ID | detail tax lines: APPLICATION_ID, ENTITY_CODE, EVENT_CLASS_CODE, TRX_ID, TRX_LINE_ID, TRX_LEVEL_TYPE, TAX_REGIME_CODE, TAX, TAX_RATE_CODE, TAX_RATE, TAXABLE_AMT, TAX_AMT, REC_TAX_AMT, NREC_TAX_AMT |
| ZX_LINES_SUMMARY | SUMMARY_TAX_LINE_ID | summary tax lines |
| ZX_LINES_DET_FACTORS | LINES_DET_FACTOR_ID | determinants: TRX_BUSINESS_CATEGORY, INPUT_TAX_CLASSIFICATION_CODE, OUTPUT_TAX_CLASSIFICATION_CODE, locations, party tax profiles |
| ZX_REC_NREC_DIST | REC_NREC_TAX_DIST_ID | recoverable and nonrecoverable distributions: RECOVERABLE_FLAG, REC_NREC_TAX_AMT, ACCOUNT_CCID |
| ZX_REGIMES_B, ZX_TAXES_B, ZX_STATUS_B, ZX_RATES_B, ZX_JURISDICTIONS_B, ZX_RULES_B | per table | configuration |
| ZX_PARTY_TAX_PROFILE, ZX_REGISTRATIONS | PARTY_TAX_PROFILE_ID; REGISTRATION_ID | party tax profiles and registrations |
| ZX_REP_TRX_DETAIL_T | DETAIL_TAX_LINE_ID | Tax Reporting Ledger extract (Payables, Receivables, tax repository) |

- SLA lines reach tax rows through XLA_DISTRIBUTION_LINKS.TAX_LINE_REF_ID, TAX_SUMMARY_LINE_REF_ID and TAX_REC_NREC_DIST_REF_ID.
- Payables accounting: recoverable tax debits the tax recoverable account; nonrecoverable tax debits the rate's tax expense account, else the line charge account, and on receipt-matched invoices the Payables accrual account. Tax point basis Payment parks recoverable tax in interim tax until payment. Self-assessed tax credits the tax liability account.
- Reports: the Tax Register calls the Tax Reporting Ledger. With the Payables close run Tax Reconciliation by Taxable Account, Tax Audit Trial report, Use Tax Liability report, Financial Tax Register and Payables Tax by Ledger Extract report. FBDI: Tax Entry Repository Data Upload Interface. REST: `partyTaxProfiles`, `invoices` action `calculateTax`.

### 4.4 Payments (IBY)

| Disbursement stage (P2P) | Tables |
|---|---|
| Payables selects installments into a payment process request | AP_INV_SELECTION_CRITERIA_ALL (CHECKRUN_ID), AP_PAYMENT_TEMPLATES, AP_SELECTED_INVOICES_ALL |
| Request handed to Payments | IBY_PAY_SERVICE_REQUESTS (CALL_APP_PAY_SERVICE_REQ_CODE, PAYMENT_SERVICE_REQUEST_STATUS) |
| Documents payable validated | IBY_DOCS_PAYABLE_ALL (CALLING_APP_ID, CALLING_APP_DOC_UNIQUE_REF1..5, DOCUMENT_STATUS, PAYMENT_ID) |
| Payments built by payment process profile rules, reviewed, approved | IBY_PAYMENTS_ALL (PAYMENT_STATUS, PAPER_DOCUMENT_NUMBER); AP_CHECKS_ALL (PAYMENT_ID), AP_INVOICE_PAYMENTS_ALL |
| Payment file (payment instruction) formatted with Oracle Analytics Publisher, transmitted or printed | IBY_PAY_INSTRUCTIONS_ALL, IBY_FORMATS_B, IBY_FILE_ACKS; errors IBY_TRANSACTION_ERRORS |

Request stages: Installment selection, Document validation, Payment validation, Payment file build, Terminated. Statuses that need action: Pending installments review, Missing payment conversion rates, Missing cross-currency rates, Pending action to complete information required, Pending action to address document validation errors, Pending action to address payment validation errors, Pending proposed payment review; Waiting for payment file processing depends on the payment file. Terminated statuses: Terminated, No available installments, Failed document validation, Failed payment validation. Act on requests from the Payments Overview page; a missing disbursement bank account or payment process profile (Pending action to complete information required) is supplied on Assign Payment Process Attributes. Post-processing produces remittance advice, positive pay and payment file registers.

| Funds capture stage (O2C) | Tables |
|---|---|
| Payment instrument on the transaction or receipt (card token or customer bank account) | IBY_FNDCPT_TX_EXTENSIONS, referenced by RA_CUSTOMER_TRX_ALL and AR_CASH_RECEIPTS_ALL (PAYMENT_TRXN_EXTENSION_ID) |
| Payer and instruments | IBY_EXTERNAL_PAYERS_ALL, IBY_CREDITCARD, IBY_EXT_BANK_ACCOUNTS, IBY_PMT_INSTR_USES_ALL, IBY_DEBIT_AUTHORIZATIONS_F |
| Create Automatic Receipt, approve (Payments authorizes cards), confirm, remit | AR_CASH_RECEIPTS_ALL, AR_BATCHES_ALL, AR_RECEIPT_METHODS |
| Remittance batch approval sends settlements as a funds capture process request; Create Settlement Batches; Retrieve Settlement Batch (acknowledgment, optional) | IBY_TRXN_SUMMARIES_ALL, IBY_FNDCPT_TX_OPERATIONS; IBY_BATCHES_ALL (credit card batch operations) |
| ISO 20022 direct debit: Receivables submits the receipts to Payments; Payments builds the settlement batch in an ISO 20022 SEPA or CGI format (pain.008) | IBY_DEBIT_AUTHORIZATIONS_F (debit authorizations) |

Payments updates settlement status from acknowledgments; Receivables keeps the receipt status but restricts follow-on actions such as refunds.

| Party or account | Tables | Interface |
|---|---|---|
| External payee (supplier), external payer (customer), first-party payer | IBY_EXTERNAL_PAYEES_ALL, IBY_EXTERNAL_PAYERS_ALL, IBY_INTERNAL_PAYERS_ALL | — |
| External bank account | IBY_EXT_BANK_ACCOUNTS, IBY_ACCOUNT_OWNERS, IBY_PMT_INSTR_USES_ALL | REST `externalBankAccounts`; FBDI Supplier Bank Account Import |
| Internal bank account | CE_BANK_ACCOUNTS (legal entity), CE_BANK_ACCT_USES_ALL (business unit use) | REST `cashBankAccounts` |
| Bank, branch | CE_INDEX_BANKS (BANK_PARTY_ID), CE_INDEX_BANK_BRANCHES (BRANCH_PARTY_ID) | REST `cashBanks`, `cashBankBranches` |
| Methods, profiles | IBY_PAYMENT_METHODS_B, IBY_FNDCPT_PMT_CHNNLS_B, IBY_ACCT_PMT_PROFILES_B, IBY_SYS_PMT_PROFILES_B | — |

### 4.5 Cash Management

| Area | Tables | Processes and interfaces |
|---|---|---|
| Bank accounts | CE_BANK_ACCOUNTS (ASSET_CODE_COMBINATION_ID cash, CASH_CLEARING_CCID, RECON_RULESET_ID, RECON_DIFFERENCE_CCID), CE_BANK_ACCT_USES_ALL, CE_GL_ACCOUNTS_CCID | REST `cashBankAccounts` |
| Statements | CE_STATEMENT_HEADERS_INT, CE_STATEMENT_LINES_INT, then CE_STATEMENT_HEADERS, CE_STATEMENT_LINES (RECON_STATUS, RECON_REFERENCE, EXCEPTION_FLAG), CE_STMT_BALANCES | Load and Import Bank Statement (BAI2, SWIFT MT940, EDIFACT FINSTA, ISO20022 CAMT052, CAMT053) with Submit Autoreconciliation; FBDI Cash Management Bank Statement Data Import |
| Automatic reconciliation | CE_RECON_RULESETS, CE_RECON_RULESET_ITEMS, CE_RECON_MATCHING_RULES, CE_RECON_TOLERANCE_RULES | Autoreconciliation (from the Bank Statements and Reconciliation page) with the Bank Statement Automatic Reconciliation Matching Rule Set assigned to the bank account (matching rules plus date, amount and percentage tolerance rules); its Generate Cash Transactions parameter then submits Create Bank Statement Transactions for unreconciled lines such as bank charges and interest |
| Manual reconciliation, exceptions | CE_RECON_HISTORY, CE_RECON_HISTORY_ITEMS (RECON_SOURCE), CE_RECON_EXCEPTIONS | Bank Statements and Reconciliation work area: Manual Reconciliation page; autoreconciliation exceptions (Ambiguous, Date, Amount) are shown against the bank statement line for manual matching |
| External cash transactions | CE_EXTERNAL_TRANSACTIONS (SOURCE, STATUS Reconciled, Unreconciled or Voided, ACCOUNTING_FLAG, ASSET_CCID, OFFSET_CCID), CE_EXT_TRX_INTERFACE, CE_ACCT_TRX_CREAT_RULES (Bank Statement Transactions Creation Rules); transfers CE_BAT_TRANSFERS | sources Manual Entry, Import, Balancing Transactions, Bank Statement, Bank Account Transfer, Ad Hoc Payment, Reversal Reconciliation; FBDI Cash Management External Transactions Import; REST `cashExternalTransactions` |

- External transactions are accounted once reconciled: with ACCOUNTING_FLAG set (the REST default), the accounting event is raised at reconciliation, and Create Accounting for Cash Management creates the journals.
- Reconciliation differences on 1-1 payment or receipt matches can split automatically into the exchange gain or loss and bank charges accounts of the bank account's business unit access; 1-M, M-1 and M-M matches, and payroll, external transaction or journal sources, use the bank account's reconciliation differences account.
- The Payables Reconciled Payments class (Payment Cleared, Payment Clearing Adjusted, Payment Uncleared) accounts payment clearing; the Payables close checklist reconciles payments to bank statement activity before transferring to GL.
- Cash to General Ledger Reconciliation Report compares the GL cash account balance with the bank account balance. OTBI: Cash Management - Bank Statements Real Time, Cash Management - External Cash Transactions Real Time.

### 4.6 Intercompany and Supply Chain Financial Orchestration

| Table | Primary key | Content and links |
|---|---|---|
| FUN_TRX_BATCHES | BATCH_ID | BATCH_NUMBER, TRX_TYPE_ID, FROM_LE_ID, FROM_LEDGER_ID, GL_DATE |
| FUN_TRX_HEADERS | TRX_ID | one per recipient; STATUS; AR_CUSTOMER_TRX_ID to RA_CUSTOMER_TRX_ALL; AP_INVOICE_ID to AP_INVOICES_ALL; PROVIDER_JE_HEADER_ID, RECEIVER_JE_HEADER_ID to GL_JE_HEADERS |
| FUN_TRX_LINES, FUN_DIST_LINES | LINE_ID; DIST_ID | transaction line; provider and receiver distributions (CCID) |
| FUN_TRX_TYPES_B, FUN_TRX_TYPE_AR_MAPS | TRX_TYPE_ID; TRX_TYPE_MAP_ID | ALLOW_INVOICING_FLAG, MANUAL_APPROVE_FLAG; mapping to a Receivables transaction type and memo line |
| FUN_IC_CUST_SUPP_MAP, FUN_INTERCO_ORGANIZATIONS | CUST_SUPP_MAP_ID; INTERCO_ORG_ID | customer and supplier of each intercompany organization |
| FUN_PERIOD_STATUSES | TRX_TYPE_ID, PERIOD_NAME, INTECO_CALENDAR, INTECO_PERIOD_TYPE | intercompany periods when an intercompany calendar is used |
| FUN_BAL_INTER_RULES, FUN_BAL_INTRA_RULES | INTER_RULE_ID; INTRA_RULE_ID | balancing rules |
| FUN_INTERFACE_CONTROLS, FUN_INTERFACE_BATCHES, FUN_INTERFACE_HEADERS, FUN_INTERFACE_DIST_LINES, FUN_INTERFACE_BATCHDISTS | per table | Import Intercompany Transactions (FBDI Intercompany Transaction Import) |
| FUN_INTERCO_MASTER_DOCUMENTS, FUN_INTERCO_SOURCE_DOCUMENTS, FUN_INTERCO_TRX_SOURCE_DOCS | per table | multitier intercompany source documents |

Transaction statuses: New, Sent, Received, Pending Approval from Others, Approved, Rejected, Rejection Reviewed, Requiring Attention, Error, Complete, Not Applicable, plus the in-flight Transferred to provider general ledger, Transferred to receiver general ledger and Transferred to Receivables. Batch statuses: New, Submitted, Error, Requiring Attention, Complete.

| Trigger | Mechanism | Result |
|---|---|---|
| Intercompany type requires invoicing | approve where manual approval applies; Transfer Intercompany Transactions to Receivables (option to run the Receivables Invoice Import), then Transfer Intercompany Transactions to Payables (option to run the Payables Invoice Import); then Create Accounting in Receivables and Payables | provider AR invoice, receiver AP invoice; Transfer to Payables skips transactions whose Receivables invoice is incomplete |
| No invoicing | Transfer Intercompany Transactions to General Ledger (option to run Journal Import), then post | provider and receiver journals |
| Entry crossing legal entities or balancing segments | FUN_BAL_INTER_RULES, FUN_BAL_INTRA_RULES | intercompany or intracompany balancing lines on the journal, no invoice |
| Multitier flows, Automated Intercompany Cross Charge of Payables Invoices | agreements and transfer authorizations (REST `intercompanyAgreements`) | intercompany transactions from source documents |
| SCFO route whose documentation and accounting rule creates intercompany invoices | Import AutoInvoice, Transaction Source ORA_Supply Chain Financial Orchestration (triggers Update Intercompany Receivables Invoice Import Details); Import Payables Invoices, Source Supply Chain Financial Flow Orchestration | intercompany AR and AP invoices between profit center BUs |
| SCFO route whose rule tracks trade distributions or profit in inventory instead | Cost Management trade events | trade distributions accounted in Costing (exact accounts per your rules; verify in your pod) |

SCFO separates the financial flow from the physical one. In global procurement the Sold-to BU owns the supplier liability, not the consuming plant. In global shipments and drop shipments the selling profit center BU on the order line is the seller, else the order header BU. Transfer prices come from transaction cost, PO price or sales order price.

| SCFO object | Tables |
|---|---|
| Financial trade agreement, buy-sell relationships | FOS_AGREEMENT_DEFINITION_B_F, FOS_AGREEMENT_PTR_F, FOS_AGREEMENT_FTR_F, FOS_BUY_SELL_RELATIONSHIP_B_F |
| Documentation and accounting rules, transfer pricing | FOS_TA_RULE_SET_B_F, FOS_TA_RULE_SET_DOCUMENTS_F, FOS_PRICING_OPTION_F, FOS_PRICING_DETAILS |
| Events, tasks, downstream results | FOS_SOURCE_EVENTS_INT, FOS_TXN_EVENTS, FOS_FLOW_INSTANCES, FOS_CALLBACK_INT, FOS_CALLBACK_ERRORS_INT |
| Party and BU links | FOS_CUSTOMER_ASSOCIATION, FOS_SUPPLIER_ASSOCIATION, FOS_RECEIVABLES_BU_ASSIGNMENT, FOS_PAYABLES_BU_ASSIGNMENT |

### 4.7 Receipt Accounting (CMR) and Cost Management (CST) touchpoints

#### 4.7.1 Receipt Accounting

| Step | Process | Tables |
|---|---|---|
| Receipts to costing | Transfer Transactions from Receiving to Costing | CMR_I_RCV_TRANSACTIONS, then CMR_RCV_TRANSACTIONS |
| PO data | purchase order interface | CMR_I_PURCHASE_ORDER_DTLS, then CMR_PURCHASE_ORDER_DTLS |
| Invoices | Transfer Costs to Cost Management (only invoices posted to GL; schedule at least daily, finishing before the distribution and accrual processes) | CMR_I_AP_INVOICE_DTLS, then CMR_AP_INVOICE_DTLS; errors CMR_AP_INTERFACE_ERRORS |
| Distributions | Create Receipt Accounting Distributions | CMR_RCV_EVENTS (EVENT_ID, ACCOUNTED_FLAG N, D, F), CMR_RCV_DISTRIBUTIONS (CODE_COMBINATION_ID, LEDGER_AMOUNT, ACCOUNTING_LINE_TYPE), CMR_RCV_EVENT_COSTS |
| Period-end accrual | Create Uninvoiced Receipt Accrual (Report or Accounting mode) | CMR_PO_ACCRUAL_AMTS |
| Accrual balances | Clear Receipt Accrual Balances; Accrual Reconciliation Report; Accrual Clearing Report | CMR_ACCRUAL_SUMMARY, CMR_ACCRUAL_TXNS, CMR_ACCR_RECONC_HEADERS, CMR_ACCR_RECONC_DTLS, CMR_ACCRUAL_CLR_AMTS |
| Period close | Run Receipt Accounting Period End Validations; close the period | CMR_PERIOD_STATUSES (STATUS_CODE N, O, P pending close, C, F permanently closed), CMR_PERIOD_CLOSE_ACTIONS |

| Accrual method | Applies to | Receipt and delivery | Invoice |
|---|---|---|---|
| Perpetual, accrue at receipt (PO_LINE_LOCATIONS_ALL.ACCRUE_ON_RECEIPT_FLAG) | inventory items always; expense items when set to accrue at receipt | receipt: debit receipt inventory, credit uninvoiced receipts; delivery clears receipt inventory to the material account | debit accrual, credit liability |
| Period end | expense items only | none. Run Create Uninvoiced Receipt Accrual in Report mode during the period to preview; after the Payables close, run it in Accounting mode (final; no Report runs for that period afterwards). It books the accrual and an incomplete reversing journal; Create Accrual Reversal Accounting in the next open period completes and transfers it | debit expense, credit liability |

#### 4.7.2 Cost Management and COGS matched to revenue

| Step | Process | Tables |
|---|---|---|
| Shipments, RMAs to costing | Transfer Transactions from Inventory to Costing | CST_INV_TRANSACTIONS, CST_TRANSACTIONS |
| Ship-to-bill link | from Order Management | CST_SHIPMENT_REVENUE_MAP (shipment and billing fulfillment lines, delivery, RMA) |
| Revenue feed | Import Revenue Lines: Ship and Bill and Bill Only orders; at least daily, just before Create Cost Accounting Distributions | CST_I_AR_REVENUE_LINES, then CST_REVENUE_LINES (CUSTOMER_TRX_ID, CUSTOMER_TRX_LINE_ID, REVENUE_PERCENTAGE, DOO_FULFILL_LINE_ID) |
| Cost processing | Create Cost Accounting Distributions | CST_COGS_TRANSACTIONS (TRANSACTION_ACTION_ID 1 COGS, 9 RMA recognition; COGS_PERCENTAGE; ACCOUNTING_STATUS), CST_COGS_LAYER_COSTS, CST_COST_DISTRIBUTIONS (EVENT_ID, ACCOUNTED_FLAG), CST_COST_DISTRIBUTION_LINES (AE_HEADER_ID, AE_LINE_NUM) |
| Accounting | Create Accounting for the Costing subledger | SLA tables; view XLA_CST_DISTRIBUTION_LINES_VL |
| Gross margin | — | CST_COGS_DETAILS, CST_REVENUE_DETAILS; OTBI Costing - New COGS and Gross Margin Details Real Time |
| Period close | Validate and Update Cost Accounting Periods: validations include Pending Revenue Recognition Events Import and Pending Create Accounting in Final Mode; types Run Validations Only, Close Period Pending, Close Period, Close Period Permanently | CST_PERIOD_STATUSES |

Deferred COGS is booked when the sales order issue is processed; recognized COGS follows recognized revenue in proportion. Compare both percentages for one AR transaction:

```sql
-- REVENUE_LINE_ID join inferred from the column descriptions (verify in your pod)
SELECT crl.invoice_number, crl.customer_trx_line_id, crl.revenue_percentage,
       cct.transaction_id AS cogs_event_id,
       cct.transaction_action_id,             -- 1 COGS recognition, 9 RMA recognition
       cct.cogs_percentage, cct.accounting_status
FROM   cst_revenue_lines     crl
JOIN   cst_cogs_transactions cct ON cct.revenue_line_id = crl.revenue_line_id
WHERE  crl.customer_trx_id = :p_customer_trx_id
ORDER  BY crl.customer_trx_line_id, cct.transaction_id;
```

### 4.8 Budgetary control (XCC) for P2P funds checks

- Purchase orders reserve funds automatically at submit or at approval, per the setup for the requisitioning BU and business function (Setup and Maintenance, Financials offering, Manage Budgetary Control task, Manage Budgetary Control and Encumbrance Accounting page). Requisitions are funds-checked and reserved the same way when budgetary control is enabled for them.
- Short of funds, a funds override is possible when enabled for the control budget, within its overall override limit, and with an override approver identified from the control budget's override rules. On a requisition that approver is added to the end of the approver list; the override reservation happens after all approvals, and Funds Status then shows Reserved.
- A rejected PO releases its funds or reinstates them to the backing requisition. Encumbrance accounting is created only when the PO or change order is implemented.

| Table | Content |
|---|---|
| XCC_CONTROL_BUDGETS, XCC_BUDGET_ACCOUNTS, XCC_CB_PERIOD_STATUSES | control budgets, budget accounts, budget periods |
| XCC_BALANCES, XCC_BALANCE_ACTIVITIES | balances and consumption; how each transaction affected them |
| XCC_TR_HEADERS, XCC_TR_LINES, XCC_DATA_SETS | transactions that called the engine (keys back to the source); one row per engine call with result status |
| XCC_BUDGET_INTERFACE | budget load (FBDI Budgetary Control Budget Import) |
| XCC_BCE_LEDGERS, XCC_BCE_BUSINESS_UNITS, XCC_BCE_TRANSACTION_TYPES | enablement |

P2P and SLA hooks: PO_DISTRIBUTIONS_ALL (FUNDS_STATUS, ENCUMBERED_FLAG, BUDGET_DATE), CMR_RCV_EVENTS (XCC_DATA_SET_ID, FUND_RESERVATION_STATUS), XLA_EVENTS.BUDGETARY_CONTROL_FLAG, XLA_AE_HEADERS.FUNDS_STATUS_CODE, XLA_DISTRIBUTION_LINKS.DATA_SET_ID; encumbrances in GL_BALANCES with ACTUAL_FLAG E by GL_ENCUMBRANCE_TYPES_B. Interfaces: REST `budgetaryControlResults`; OTBI Budgetary Control - Balances Real Time, Budgetary Control - Transactions Real Time.

### 4.9 Recommended period-close sequence across P2P and O2C

The order follows documented dependencies: Payables closes after payments are reconciled, the uninvoiced receipt accrual runs after the Payables close, cost close checks the revenue import, and GL close fails on open subledger work. Run the transfer-to-costing processes daily, not only at month end.

| Order | Module | Key processes | Reconciliation report or check |
|---|---|---|---|
| 1 | Receiving, Order Management, Shipping, Inventory | finish receipts and shipments; Transfer Transactions from Receiving to Costing; Transfer Transactions from Inventory to Costing | Run Receipt Accounting Period End Validations |
| 2 | Intercompany | approve; Transfer Intercompany Transactions to Receivables, to Payables, to General Ledger | nothing left in Sent, Received, Approved or Error |
| 3 | Cash Management | Load and Import Bank Statement; Autoreconciliation; manual reconciliation; Create Bank Statement Transactions; Create Accounting | exceptions cleared; Cash to General Ledger Reconciliation Report (rerun after GL posting) |
| 4 | Payables | Import Payables Invoices; validate; Update Matured Bills Payable Status; Apply Missing Conversion Rates; finish payment files; Create Accounting (transfer Yes); Post Subledger Journal Entries; Unaccounted Transactions and Sweep; close | Payables Period Close Exceptions Report; Payables Trial Balance; Payables Posted Invoice Register and Payables Posted Payment Register (need Import Journal References on the Payables source); Prepare Payables to General Ledger Reconciliation, Payables to Ledger Reconciliation Report; Payables Open Items Revaluation Report |
| 5 | Receivables, Revenue Management | complete transactions and receipts; Recognize Revenue (Receivables revenue scheduling rules; Revenue Management contracts follow section 3); Create Receivables Accounting or Create Accounting; Sweep Subledger Transactions to Another Period if needed; set Close Pending, clear the Subledger Period Close Exception Report, then close | Subledger Period Close Exception Report; Prepare Receivables to General Ledger Reconciliation, Receivables to General Ledger Reconciliation Report; Receivables Aging by General Ledger Account Report; Receivables Open Items Revaluation Report |
| 6 | Receipt Accounting | Transfer Costs to Cost Management; Create Receipt Accounting Distributions; Create Uninvoiced Receipt Accrual (Accounting); Create Accounting; close | Accrual Reconciliation Report; Uninvoiced Receipt Accrual Report; OTBI Costing - Receipt Accounting Period Close Real Time |
| 7 | Cost Management | Import Revenue Lines; Create Cost Accounting Distributions; Create Accounting; Validate and Update Cost Accounting Periods (Close Period) | OTBI Costing - Cost Accounting Period Close Real Time |
| 8 | Tax | registers and reconciliation | Tax Reconciliation by Taxable Account; Tax Audit Trial report; Financial Tax Register |
| 9 | General Ledger | Import Journals; post; Revalue Balances; Translate General Ledger Account Balances; Prepare Intercompany Reconciliation Reporting Information; close | Close Monitor; Account Analysis Report; trial balance; intercompany reconciliation reports |
| 10 | Next period | open periods; Create Accrual Reversal Accounting; Create Mass Additions; Transfer Costs to Cost Management | — |

Use a unique request name for each Prepare ... Reconciliation run (a reused name can return no data). For Receivables, Oracle's best practice is to close the period before the extract and select the Closed period (the parameter defaults to the latest Close Pending period); an Open period gives only a point-in-time view. Both extracts need natural account values tagged with the Accounts Payable or Accounts Receivable financial category. One read-only status check per ledger and period:

```sql
SELECT TO_CHAR(gps.application_id) AS module,   -- 101 GL, 200 Payables, 222 Receivables
       gps.period_name, gps.closing_status AS status
FROM   gl_period_statuses gps
WHERE  gps.ledger_id = :p_ledger_id
AND    gps.period_name = :p_period_name
AND    gps.application_id IN (101, 200, 222)
UNION ALL
SELECT 'Receipt Accounting BU ' || TO_CHAR(cps.business_unit_id),
       cps.period_name, cps.status_code
FROM   cmr_period_statuses cps
WHERE  cps.ledger_id = :p_ledger_id
AND    cps.period_name = :p_period_name;
```
