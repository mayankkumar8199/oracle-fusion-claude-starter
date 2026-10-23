## 9. SQL cookbook for BI Publisher data models

This section gives 16 query patterns for SQL data sets in BI Publisher. Some 26D guides, such as the Order Management SQL topic, call BI Publisher Oracle Analytics Publisher; the SCM reports security topic still says BI Publisher. Every table and column below appears in the 26D Tables and Views guides. Each join cites its basis: **FK** means a documented foreign key (Appendix B), **CC** means an explicit column comment, and **Community** means the join comes from practitioner material and must be verified in your pod. Use OTBI subject areas or BICC data stores when they cover the need (section 8). Use these queries for row-level traces, reconciliations and custom layouts. The flows are in sections 2 and 3, the accounting backbone in section 4 and roles in section 12. Index lists show the table and the indexed columns; index names are in the companion workbook.

### 9.1 Conventions and security context

| Topic | Rule |
|---|---|
| Data source | Create SQL data sets on `ApplicationDB_FSCM`, the default data source. Oracle's Order Management guide uses it and expands FSCM as Fusion Supply Chain Management. |
| Parameters | Bind names are `:p_<name>`. Define each one as a data model parameter, with Date type for dates. Optional filters use `(:p_x IS NULL OR col = :p_x)`. Use no `SELECT *` and no trailing semicolon. |
| Business unit | Always filter on the BU column: `ORG_ID` on AP, AR, Payments and Order Management tables; `PRC_BU_ID`, `BILLTO_BU_ID` and `REQ_BU_ID` on purchasing tables; `BILL_TO_BUSINESS_UNIT_ID` on `CMR_ACCRUAL_SUMMARY`; `SET_ID` on customer account sites. |
| Data security | A data set that selects base tables directly is not subject to data security. Oracle recommends joining secured list views and limiting who can create data models. Add the BU predicate below to every query. |
| Session context | MOAC-secured views such as `IBY_PAYMENTS_SEC_V` filter rows against the session organization list in `MO_GLOB_ORG_ACCESS_TMP`. `IBY_PAYMENTS_SEC_V` also requires the payment function to appear in `IBY_USER_PAY_FUNS_SEC_V` (26D view text). If the data model does not initialize that list, the view returns only rows with `ORG_ID = -1` (verify in your pod). |
| User identity | The system variable `:xdo_user_name` holds the user ID of the person who submits the report. Oracle's Publisher data modeling guides (Oracle Analytics Server and on-premises 12.2.1.2) say it is always lowercase; no Fusion 26D page states this. Compare it case-insensitively, as the predicate below does (verify in your pod). |
| PII | PII tables are protected by VPD policies. BI Publisher returns their rows only to authorized users. |
| Translations | Join `_TL` tables on `LANGUAGE = USERENV('LANG')`, which is how Oracle's `AR_LOOKUPS` view filters. |
| Application IDs | Payables is 200 and Receivables is 222. The view texts of `AP_LOOKUP_CODES` and `AR_LOOKUPS` filter `VIEW_APPLICATION_ID` on these values, and the description of `XLA_SUBLEDGERS` says it replaces `FND_APPLICATION_VL`. Confirm the IDs with helper H1. |
| Seed tables | `ORA_SEED_SET1` and `ORA_SEED_SET2` (on `AP_HOLD_CODES`, `AR_RECEIPT_METHODS`, `DOO_STATUSES_B`, `DOO_HOLD_CODES_TL` and the XLA subledger tables) are documented as Oracle internal use only, with edition-based redefinition context values Y or N. Do not filter on them. Their unique indexes include the seed-set column, but the documented primary keys do not. If a join returns two rows for one logical key, report it to Oracle Support rather than filtering (verify in your pod). |
| Testing | Test every query in a non-production pod. Check row counts and the explain plan before you schedule a query. |

**BU data-access predicate.** `FUN_USER_BO_DATA_ASSIGNMENTS_V` exposes `USERNAME` and the user's active data assignments. A BU assignment has `DATASEC_CONTEXT_TYPE_CODE = 'ORA_BU_ID'` and carries the BU ID as text in `DATASEC_CONTEXT_VALUE1`. Reuse the subquery on the BU column of any query in this section. Test in a non-production pod.

```sql
SELECT ai.invoice_id,
       ai.invoice_num
FROM   ap_invoices_all ai
WHERE  ai.org_id = :p_bu_id
AND    TO_CHAR(ai.org_id) IN (
         SELECT uda.datasec_context_value1
         FROM   fun_user_bo_data_assignments_v uda
         WHERE  UPPER(uda.username) = UPPER(:xdo_user_name)
         AND    uda.datasec_context_type_code = 'ORA_BU_ID')
```

The predicate checks BU access, not a specific privilege. To mirror one privilege, also filter `uda.fndds_privilege` (verify the values in your pod). The 26D view text keeps only assignments, users and roles with `ACTIVE_FLAG = 'Y'`. It does not apply the assignment start and end dates, so an assignment that has expired but is still flagged active still grants access.

**H1. Confirm subledger identifiers.** Lists application IDs and the entity-to-source-column mappings that SLA uses. Test in a non-production pod.

```sql
SELECT xs.application_id,
       xst.application_name,
       xs.je_source_name,
       xem.entity_code,
       xem.source_id_col_name_1,
       xem.transaction_id_col_name_1
FROM   xla_subledgers xs
JOIN   xla_subledgers_tl xst
       ON  xst.application_id = xs.application_id
       AND xst.language       = USERENV('LANG')
LEFT JOIN xla_entity_id_mappings xem
       ON  xem.application_id = xs.application_id
WHERE  xs.application_id IN (200, 222)
ORDER  BY xs.application_id, xem.entity_code
```

Join basis: the primary keys XLA_SUBLEDGERS_TL (APPLICATION_ID, LANGUAGE) and XLA_ENTITY_ID_MAPPINGS (APPLICATION_ID, ENTITY_CODE). Neither table has a documented FK to XLA_SUBLEDGERS.

**H2. List distribution types.** Shows the `SOURCE_DISTRIBUTION_TYPE` values that recent journals use. Run it before you filter Q7 or Q14 on a type. Test in a non-production pod.

```sql
SELECT xdl.source_distribution_type,
       COUNT(*) AS link_rows
FROM   xla_ae_headers xah
JOIN   xla_distribution_links xdl
       ON  xdl.ae_header_id   = xah.ae_header_id
       AND xdl.application_id = xah.application_id
WHERE  xah.application_id  = :p_app_id
AND    xah.ledger_id       = :p_ledger_id
AND    xah.accounting_date >= TRUNC(SYSDATE) - 7
GROUP  BY xdl.source_distribution_type
```

Index: XLA_AE_HEADERS (LEDGER_ID, APPLICATION_ID, ACCOUNTING_DATE).

### 9.2 Procure-to-Pay queries

#### Q1. Requisition to payment trace for one purchase order

| Item | Detail |
|---|---|
| Purpose | Returns one timeline row per document in the chain: requisition, PO distribution, receiving transaction, invoice and payment. A UNION ALL keeps a PO with many receipts and invoices from multiplying rows. |
| Binds | `:p_po_number`, `:p_prc_bu_id` |
| Joins | FK: PO_LINES_ALL to PO_HEADERS_ALL; PO_LINE_LOCATIONS_ALL to PO_LINES_ALL; POR_REQ_DISTRIBUTIONS_ALL to POR_REQUISITION_LINES_ALL to POR_REQUISITION_HEADERS_ALL; RCV_TRANSACTIONS to PO_HEADERS_ALL and RCV_SHIPMENT_HEADERS; AP_INVOICE_LINES_ALL to PO_HEADERS_ALL; AP_INVOICE_PAYMENTS_ALL to AP_INVOICES_ALL and AP_CHECKS_ALL. CC: PO_DISTRIBUTIONS_ALL.LINE_LOCATION_ID (references the schedule) and PO_DISTRIBUTIONS_ALL.REQ_DISTRIBUTION_ID (requisition distribution identifier). |
| Indexes | PO_HEADERS_ALL unique (SEGMENT1, TYPE_LOOKUP_CODE, CASE WHEN TYPE_LOOKUP_CODE = 'STANDARD' THEN SOLDTO_LE_ID ELSE PRC_BU_ID END); PO_DISTRIBUTIONS_ALL (LINE_LOCATION_ID); RCV_TRANSACTIONS (PO_HEADER_ID); AP_INVOICE_LINES_ALL (PO_HEADER_ID); AP_INVOICE_PAYMENTS_ALL (INVOICE_ID, PAYMENT_NUM). |
| Notes | The unique index shows that standard PO numbers are unique per sold-to legal entity. If one procurement BU serves several legal entities, also bind `SOLDTO_LE_ID`. Receiving rows show each `TRANSACTION_TYPE`, such as receipts, deliveries, returns and corrections. Invoice rows include only invoices with at least one line matched to the PO. Apply the 9.1 predicate to `PRC_BU_ID`. For a wide one-row-per-distribution diagnostic with holds, payment files and accounting status, use the 2.13 query. |

Test in a non-production pod.

```sql
WITH po AS (
  SELECT poh.po_header_id, poh.segment1 AS po_number, poh.approved_date
  FROM   po_headers_all poh
  WHERE  poh.segment1         = :p_po_number
  AND    poh.prc_bu_id        = :p_prc_bu_id
  AND    poh.type_lookup_code = 'STANDARD'
),
dist AS (
  SELECT pod.req_distribution_id, pod.quantity_ordered, pod.amount_ordered,
         pll.schedule_status,
         pol.line_num || '.' || pll.shipment_num || '.' || pod.distribution_num AS line_ref
  FROM   po
  JOIN   po_lines_all pol          ON pol.po_header_id     = po.po_header_id
  JOIN   po_line_locations_all pll ON pll.po_line_id       = pol.po_line_id
  JOIN   po_distributions_all pod  ON pod.line_location_id = pll.line_location_id
),
inv AS (
  SELECT DISTINCT ail.invoice_id
  FROM   po
  JOIN   ap_invoice_lines_all ail ON ail.po_header_id = po.po_header_id
)
SELECT 1 AS step, 'Requisition' AS doc_type, prh.requisition_number AS doc_number,
       TO_CHAR(prl.line_number) AS doc_line, CAST(prh.approved_date AS DATE) AS doc_date,
       prh.document_status AS doc_status, prd.distribution_quantity AS quantity,
       prd.distribution_amount AS amount
FROM   dist
JOIN   por_req_distributions_all prd   ON prd.distribution_id       = dist.req_distribution_id
JOIN   por_requisition_lines_all prl   ON prl.requisition_line_id   = prd.requisition_line_id
JOIN   por_requisition_headers_all prh ON prh.requisition_header_id = prl.requisition_header_id
UNION ALL
SELECT 2, 'Purchase order', po.po_number, dist.line_ref, po.approved_date,
       dist.schedule_status, dist.quantity_ordered, dist.amount_ordered
FROM   po CROSS JOIN dist
UNION ALL
SELECT 3, 'Receiving ' || rt.transaction_type, rsh.receipt_num, TO_CHAR(rt.transaction_id),
       rt.transaction_date, rt.destination_type_code, rt.quantity, rt.amount
FROM   po
JOIN   rcv_transactions rt      ON rt.po_header_id        = po.po_header_id
JOIN   rcv_shipment_headers rsh ON rsh.shipment_header_id = rt.shipment_header_id
UNION ALL
SELECT 4, 'Invoice', ai.invoice_num, NULL, ai.invoice_date,
       ai.payment_status_flag, NULL, ai.invoice_amount
FROM   inv
JOIN   ap_invoices_all ai ON ai.invoice_id = inv.invoice_id
UNION ALL
SELECT 5, 'Payment', TO_CHAR(ac.check_number), ai2.invoice_num, ac.check_date,
       ac.status_lookup_code, NULL, aip.amount
FROM   inv
JOIN   ap_invoice_payments_all aip ON aip.invoice_id = inv.invoice_id
JOIN   ap_checks_all ac            ON ac.check_id    = aip.check_id
JOIN   ap_invoices_all ai2         ON ai2.invoice_id = aip.invoice_id
ORDER  BY 1, 5
```

#### Q2. Open PO schedules not fully received or billed

| Item | Detail |
|---|---|
| Purpose | Lists standard PO schedules that still have quantity or amount open to receive or to bill. |
| Binds | `:p_prc_bu_id`, `:p_need_by_from`, `:p_need_by_to` |
| Joins | FK: PO_LINE_LOCATIONS_ALL to PO_HEADERS_ALL and PO_LINES_ALL; PO_HEADERS_ALL to POZ_SUPPLIERS (VENDOR_ID); POZ_SUPPLIERS to HZ_PARTIES (PARTY_ID). |
| Indexes | PO_LINE_LOCATIONS_ALL (PRC_BU_ID); (PO_HEADER_ID, SCHEDULE_STATUS). `NEED_BY_DATE` has no index of its own. To filter on an indexed date, replace the need-by predicate with the function-based index expression TRUNC(NVL(ANTICIPATED_ARRIVAL_DATE, NVL(PROMISED_DATE, NEED_BY_DATE))), written exactly as indexed. For distribution-level variants, PO_DISTRIBUTIONS_ALL has function-based indexes on QUANTITY_ORDERED - NVL(QUANTITY_DELIVERED,0) - NVL(QUANTITY_CANCELLED,0) and on the same expression with QUANTITY_BILLED. Write the predicate exactly as indexed. |
| Notes | Returns one row per schedule. Goods use quantity columns; the comments say the amount columns hold service-line amounts. `CLOSED_FOR_RECEIVING_DATE` and `CLOSED_FOR_INVOICE_DATE` exclude closed schedules without status literals. If `RECEIPT_REQUIRED_FLAG = 'N'`, open-to-receive does not matter. The Purchase Order Statuses topic documents display values only, so `SCHEDULE_STATUS` is returned as data rather than filtered. |

Test in a non-production pod.

```sql
WITH sched AS (
  SELECT pll.line_location_id, pll.po_header_id, pll.po_line_id, pll.shipment_num,
         pll.need_by_date, pll.schedule_status, pll.receipt_required_flag, pll.match_option,
         pll.closed_for_receiving_date, pll.closed_for_invoice_date,
         NVL(pll.quantity, 0) - NVL(pll.quantity_cancelled, 0) AS qty_net,
         NVL(pll.quantity_received, 0)                         AS qty_received,
         NVL(pll.quantity_billed, 0)                           AS qty_billed,
         NVL(pll.amount, 0) - NVL(pll.amount_cancelled, 0)     AS amt_net,
         NVL(pll.amount_received, 0)                           AS amt_received,
         NVL(pll.amount_billed, 0)                             AS amt_billed
  FROM   po_line_locations_all pll
  WHERE  pll.prc_bu_id = :p_prc_bu_id
  AND    NVL(pll.cancel_flag, 'N') = 'N'
  AND    pll.need_by_date BETWEEN :p_need_by_from AND :p_need_by_to
)
SELECT poh.segment1           AS po_number,
       pol.line_num,
       s.shipment_num,
       hp.party_name          AS supplier_name,
       pol.item_description,
       s.need_by_date,
       s.schedule_status,
       s.receipt_required_flag,
       s.match_option,
       s.qty_net - s.qty_received AS qty_open_to_receive,
       s.qty_net - s.qty_billed   AS qty_open_to_bill,
       s.amt_net - s.amt_received AS amt_open_to_receive,
       s.amt_net - s.amt_billed   AS amt_open_to_bill,
       poh.currency_code
FROM   sched s
JOIN   po_headers_all poh ON poh.po_header_id = s.po_header_id
JOIN   po_lines_all pol   ON pol.po_line_id   = s.po_line_id
JOIN   poz_suppliers sup  ON sup.vendor_id    = poh.vendor_id
JOIN   hz_parties hp      ON hp.party_id      = sup.party_id
WHERE  poh.type_lookup_code = 'STANDARD'
AND    poh.approved_date IS NOT NULL
AND   ((s.closed_for_receiving_date IS NULL
        AND (s.qty_net > s.qty_received OR s.amt_net > s.amt_received))
    OR (s.closed_for_invoice_date IS NULL
        AND (s.qty_net > s.qty_billed OR s.amt_net > s.amt_billed)))
ORDER  BY poh.segment1, pol.line_num, s.shipment_num
```

#### Q3. Invoices on hold with hold name, reason and age

| Item | Detail |
|---|---|
| Purpose | Lists unreleased holds on invoices that are not canceled, with the age of each hold in days. |
| Binds | `:p_bu_id`, `:p_held_since` |
| Joins | FK: AP_HOLDS_ALL to AP_INVOICES_ALL (INVOICE_ID) and AP_HOLD_CODES (HOLD_LOOKUP_CODE); AP_INVOICES_ALL to POZ_SUPPLIERS (VENDOR_ID); POZ_SUPPLIERS to HZ_PARTIES. CC: ORG_ID ("identifier of the business unit") to FUN_ALL_BUSINESS_UNITS_V.BU_ID, which the view text maps to the organization ID. |
| Indexes | AP_HOLDS_ALL function-based (NVL(RELEASE_LOOKUP_CODE, 'null'), ORG_ID), which is why the predicate uses that exact expression; (INVOICE_ID). |
| Notes | The table description gives one row per non-matching hold and one row per invoice-shipment match for matching holds. `HOLD_LOOKUP_CODE` is the hold name. A null `RELEASE_LOOKUP_CODE` means the hold is unreleased, and Payables does not pay such invoices. Scheduled-payment holds (`AP_PAYMENT_SCHEDULES_ALL.HOLD_FLAG`) and supplier-site payment holds (`POZ_SUPPLIER_SITES_ALL_M.HOLD_ALL_PAYMENTS_FLAG`) are stored elsewhere. `HOLD_DATE` is a TIMESTAMP. |

Test in a non-production pod.

```sql
SELECT bu.bu_name,
       ai.invoice_num,
       ai.invoice_date,
       ai.invoice_amount,
       ai.invoice_currency_code,
       hp.party_name                                        AS supplier_name,
       ah.hold_lookup_code                                  AS hold_name,
       ahc.hold_type,
       ahc.external_description                             AS hold_description,
       ah.hold_reason,
       ah.line_number                                       AS invoice_line,
       ah.held_by,
       CAST(ah.hold_date AS DATE)                           AS hold_date,
       TRUNC(SYSDATE) - TRUNC(CAST(ah.hold_date AS DATE))   AS days_on_hold,
       ahc.user_releaseable_flag,
       ahc.postable_flag
FROM   ap_holds_all ah
JOIN   ap_invoices_all ai          ON ai.invoice_id        = ah.invoice_id
JOIN   ap_hold_codes ahc           ON ahc.hold_lookup_code = ah.hold_lookup_code
JOIN   fun_all_business_units_v bu ON bu.bu_id             = ah.org_id
LEFT JOIN poz_suppliers sup        ON sup.vendor_id        = ai.vendor_id
LEFT JOIN hz_parties hp            ON hp.party_id          = sup.party_id
WHERE  ah.org_id = :p_bu_id
AND    NVL(ah.release_lookup_code, 'null') = 'null'
AND    ai.cancelled_date IS NULL
AND    ah.hold_date >= :p_held_since
ORDER  BY days_on_hold DESC, ai.invoice_num
```

#### Q4. Unpaid installments due in a date range, by supplier

| Item | Detail |
|---|---|
| Purpose | Lists unpaid and partially paid installments due in a window, with a total per supplier and payment currency. |
| Binds | `:p_bu_id`, `:p_due_from`, `:p_due_to`, `:p_vendor_id` (optional) |
| Joins | FK: AP_PAYMENT_SCHEDULES_ALL to AP_INVOICES_ALL; AP_INVOICES_ALL to POZ_SUPPLIERS; POZ_SUPPLIERS to HZ_PARTIES. The join from AP_INVOICES_ALL.VENDOR_SITE_ID to the POZ_SUPPLIER_SITES_ALL_M primary key is a same-name key with no documented FK. |
| Indexes | AP_PAYMENT_SCHEDULES_ALL (DUE_DATE); (PAYMENT_STATUS_FLAG, HOLD_FLAG); (PAYMENT_STATUS_FLAG, CHECKRUN_ID, ORG_ID, PAYMENT_PRIORITY, PAYMENT_METHOD_CODE). POZ_SUPPLIER_SITES_ALL_M has a unique index on VENDOR_SITE_ID, so the join returns one row per site even though the table has date-effective columns. |
| Notes | Returns one row per installment. `PAYMENT_STATUS_FLAG` is N for unpaid, P for partially paid and Y for paid (table description). Totals are split by payment currency: `INV_CURR_GROSS_AMOUNT` holds the invoice-currency gross, which implies `GROSS_AMOUNT` and `AMOUNT_REMAINING` are in payment currency (verify for cross-currency invoices). Invoices that are not yet validated or approved also have installments; add a filter on `WFAPPROVAL_STATUS` if needed. |

Test in a non-production pod.

```sql
SELECT hp.party_name               AS supplier_name,
       sup.segment1                AS supplier_number,
       sts.vendor_site_code,
       ai.invoice_num,
       ai.invoice_date,
       ai.payment_currency_code,
       apsa.payment_num,
       apsa.due_date,
       apsa.gross_amount,
       apsa.amount_remaining,
       apsa.discount_date,
       apsa.discount_amount_available,
       apsa.payment_status_flag,
       apsa.hold_flag,
       apsa.payment_method_code,
       ai.wfapproval_status,
       SUM(apsa.amount_remaining) OVER
         (PARTITION BY ai.vendor_id, ai.payment_currency_code) AS supplier_total_remaining
FROM   ap_payment_schedules_all apsa
JOIN   ap_invoices_all ai ON ai.invoice_id = apsa.invoice_id
JOIN   poz_suppliers sup  ON sup.vendor_id = ai.vendor_id
JOIN   hz_parties hp      ON hp.party_id   = sup.party_id
LEFT JOIN poz_supplier_sites_all_m sts ON sts.vendor_site_id = ai.vendor_site_id
WHERE  apsa.org_id = :p_bu_id
AND    apsa.payment_status_flag IN ('N', 'P')
AND    apsa.due_date BETWEEN :p_due_from AND :p_due_to
AND    ai.cancelled_date IS NULL
AND    (:p_vendor_id IS NULL OR ai.vendor_id = :p_vendor_id)
ORDER  BY hp.party_name, apsa.due_date, ai.invoice_num, apsa.payment_num
```

#### Q5. Payments with the invoices they paid

| Item | Detail |
|---|---|
| Purpose | Returns one row per invoice payment, with payment, Oracle Payments and invoice attributes. |
| Binds | `:p_bu_id` (paying BU), `:p_pay_from`, `:p_pay_to`, `:p_vendor_id` (optional) |
| Joins | FK: AP_INVOICE_PAYMENTS_ALL to AP_CHECKS_ALL (CHECK_ID) and AP_INVOICES_ALL (INVOICE_ID); AP_CHECKS_ALL to IBY_PAYMENTS_ALL (PAYMENT_ID). |
| Indexes | AP_CHECKS_ALL (CHECK_DATE); (VENDOR_ID); AP_INVOICE_PAYMENTS_ALL (CHECK_ID); IBY_PAYMENTS_ALL primary key (PAYMENT_ID). |
| Notes | A void sets `VOID_DATE` and adds reversal rows with `REVERSAL_FLAG = 'Y'` that point to `REVERSAL_INV_PMT_ID`. Sum `amount_paid` to get net figures. `AP_INVOICE_PAYMENTS_ALL.INV_ORG_ID` is the invoicing BU, which can differ from the paying BU on the payment. For payment-level security, `IBY_PAYMENTS_SEC_V` exists, but see the session note in 9.1. |

Test in a non-production pod.

```sql
SELECT ac.check_number           AS payment_number,
       ac.check_date             AS payment_date,
       ac.status_lookup_code     AS payment_status,
       ac.payment_method_code,
       ac.amount                 AS payment_amount,
       ac.currency_code          AS payment_currency,
       ac.vendor_name            AS payee_name,
       ac.checkrun_name,
       ipa.payment_reference_number,
       ipa.payment_process_request_name,
       ai.invoice_num,
       ai.invoice_date,
       ai.invoice_amount,
       ai.invoice_currency_code,
       aip.amount                AS amount_paid,
       aip.discount_taken,
       aip.accounting_date,
       aip.reversal_flag
FROM   ap_checks_all ac
JOIN   ap_invoice_payments_all aip ON aip.check_id  = ac.check_id
JOIN   ap_invoices_all ai          ON ai.invoice_id = aip.invoice_id
LEFT JOIN iby_payments_all ipa     ON ipa.payment_id = ac.payment_id
WHERE  ac.org_id = :p_bu_id
AND    ac.check_date BETWEEN :p_pay_from AND :p_pay_to
AND    (:p_vendor_id IS NULL OR ac.vendor_id = :p_vendor_id)
ORDER  BY ac.check_date, ac.check_number, ai.invoice_num
```

#### Q6. Received-not-invoiced (uninvoiced receipts)

| Item | Detail |
|---|---|
| Purpose | 6a reads the Receipt Accounting accrual balance per PO distribution from `CMR_ACCRUAL_SUMMARY`, which is described as "all the accrual balances at purchase order distribution level". 6b gives an operational estimate from PO distribution quantities for both accrual modes. 6c reads period-end accrual amounts for POs that do not accrue at receipt. |
| Binds | `:p_bill_to_bu_id`, `:p_as_of_date` (6a), `:p_accrue_on_receipt` (6b, optional Y or N), `:p_period_start_date` (6c, first day of the accounting period) |
| Joins | 6a CC: CMR_ACCRUAL_SUMMARY.VENDOR_ID ("references POZ_SUPPLIERS.vendor_id"); BILL_TO_BUSINESS_UNIT_ID (the BU that creates the invoice) to FUN_ALL_BUSINESS_UNITS_V; FK POZ_SUPPLIERS to HZ_PARTIES. 6b CC: PO_DISTRIBUTIONS_ALL.LINE_LOCATION_ID; FK PO_LINE_LOCATIONS_ALL to PO_LINES_ALL and PO_HEADERS_ALL. 6c CC: CMR_PO_ACCRUAL_AMTS_RPT.VENDOR_ID ("Identifies the Supplier") to POZ_SUPPLIERS.VENDOR_ID, a same-name key with no documented FK. |
| Indexes | CMR_ACCRUAL_SUMMARY (STATUS, BILL_TO_BUSINESS_UNIT_ID); (VENDOR_ID); (PO_NUMBER). PO_DISTRIBUTIONS_ALL (LINE_LOCATION_ID). CMR_PO_ACCRUAL_AMTS_RPT (PERIOD_START_DATE, BILL_TO_BU_ID), which is why 6c filters on the period start date. Its primary key is (CMR_PO_DISTRIBUTION_ID, PERIOD_START_DATE), so 6c returns one row per distribution and period. |
| Notes | The `RECEIVED_AMT` and `INVOICE_AMT` comments describe 6a amounts as net amounts posted to SLA by Receipt Accounting and by Payables, so 6a is only as current as the last accounting runs (section 7; verify the refresh behaviour in your pod). POs that do not accrue at receipt are accrued at period end by the scheduled process Create Uninvoiced Receipt Accrual (modes Report and Accounting), and the Uninvoiced Receipt Accrual Report reviews the result after a Report-mode run. `CMR_PO_ACCRUAL_AMTS_RPT` is described as accrual amounts "for each run, for each period, for all purchase order distributions for report". That the Report-mode run fills it is inferred from that description (verify in your pod). `AMT_DIFFERENCE` is net received minus net invoiced; a positive value means received but not invoiced. `:p_as_of_date` limits rows by last receipt date, but the balances are current, not as of that date. The `STATUS` comment lists Open, Marked for clearing, Cleared and Marked for Reversal; check the stored codes before you filter on them. 6b ignores exchange rates and accounting, and it values quantity at the schedule price. It returns `ACCRUE_ON_RECEIPT_FLAG` so that you can split receipt-time and period-end accruals. |

Test in a non-production pod.

```sql
SELECT bu.bu_name                          AS bill_to_bu,
       cas.po_number,
       cas.line_number,
       cas.shipment_number,
       cas.distribution_number,
       hp.party_name                       AS supplier_name,
       cas.item_description,
       cas.destination_type_code,
       cas.organization_code,
       cas.received_qty,
       cas.invoice_qty,
       cas.qty_difference,
       cas.received_amt,
       cas.invoice_amt,
       cas.amt_difference,
       cas.ledger_currency_code,
       cas.status                          AS accrual_status,
       CAST(cas.receipt_txn_date AS DATE)  AS last_receipt_date
FROM   cmr_accrual_summary cas
JOIN   fun_all_business_units_v bu ON bu.bu_id = cas.bill_to_business_unit_id
LEFT JOIN poz_suppliers sup        ON sup.vendor_id = cas.vendor_id
LEFT JOIN hz_parties hp            ON hp.party_id   = sup.party_id
WHERE  cas.bill_to_business_unit_id = :p_bill_to_bu_id
AND    cas.amt_difference <> 0
AND    cas.receipt_txn_date < :p_as_of_date + 1
ORDER  BY hp.party_name, cas.po_number, cas.line_number
```

6b, operational variant. Test in a non-production pod.

```sql
SELECT poh.segment1                                                  AS po_number,
       pol.line_num,
       pll.shipment_num,
       pod.distribution_num,
       pod.destination_type_code,
       pod.accrue_on_receipt_flag,
       pod.quantity_delivered,
       pod.quantity_billed,
       NVL(pod.quantity_delivered, 0) - NVL(pod.quantity_billed, 0) AS qty_uninvoiced,
       (NVL(pod.quantity_delivered, 0) - NVL(pod.quantity_billed, 0))
         * pll.price_override                                        AS value_at_po_price,
       NVL(pod.amount_delivered, 0) - NVL(pod.amount_billed, 0)     AS amt_uninvoiced,
       poh.currency_code
FROM   po_distributions_all pod
JOIN   po_line_locations_all pll ON pll.line_location_id = pod.line_location_id
JOIN   po_lines_all pol          ON pol.po_line_id       = pll.po_line_id
JOIN   po_headers_all poh        ON poh.po_header_id     = pll.po_header_id
WHERE  poh.billto_bu_id = :p_bill_to_bu_id
AND    (:p_accrue_on_receipt IS NULL OR pod.accrue_on_receipt_flag = :p_accrue_on_receipt)
AND    (NVL(pod.quantity_delivered, 0) > NVL(pod.quantity_billed, 0)
        OR NVL(pod.amount_delivered, 0) > NVL(pod.amount_billed, 0))
ORDER  BY poh.segment1, pol.line_num, pll.shipment_num, pod.distribution_num
```

6c, period-end accrual amounts. Test in a non-production pod.

```sql
SELECT par.period_name,
       par.po_number,
       par.line_number,
       par.shipment_number,
       par.distribution_number,
       hp.party_name          AS supplier_name,
       par.item_description,
       par.received_qty,
       par.invoiced_qty,
       par.accrual_qty,
       par.accrual_amt,
       par.func_currency_code
FROM   cmr_po_accrual_amts_rpt par
LEFT JOIN poz_suppliers sup ON sup.vendor_id = par.vendor_id
LEFT JOIN hz_parties hp     ON hp.party_id   = sup.party_id
WHERE  par.bill_to_bu_id = :p_bill_to_bu_id
AND    par.period_start_date = :p_period_start_date
AND    par.accrual_amt  <> 0
ORDER  BY hp.party_name, par.po_number, par.line_number
```

#### Q7. AP invoice accounting drill-down to GL journal lines

| Item | Detail |
|---|---|
| Purpose | Traces each invoice distribution through its SLA journal entry line to the GL journal line in the primary ledger. |
| Binds | `:p_bu_id`, `:p_invoice_num`, `:p_vendor_id` (optional), `:p_app_id` (200), `:p_src_dist_type` (optional; the invoice-distribution value that H2 returns) |
| Joins | FK: AP_INVOICE_DISTRIBUTIONS_ALL to AP_INVOICES_ALL; GL_IMPORT_REFERENCES to GL_JE_LINES; GL_JE_LINES to GL_JE_HEADERS. CC: AP_INVOICE_DISTRIBUTIONS_ALL.ACCOUNTING_EVENT_ID ("the accounting event that accounted for the distribution") to XLA_AE_HEADERS.EVENT_ID; XLA_AE_LINES.GL_SL_LINK_TABLE ("used to link general ledger journal lines with subledger journal entry lines") with GL_SL_LINK_ID; XLA_AE_LINES.CODE_COMBINATION_ID. SLA joins have no documented FK. They use the primary keys XLA_AE_HEADERS (AE_HEADER_ID, APPLICATION_ID) and XLA_AE_LINES (AE_HEADER_ID, AE_LINE_NUM, APPLICATION_ID), and the comments on XLA_DISTRIBUTION_LINKS.AE_HEADER_ID and AE_LINE_NUM ("Subledger journal entry identifier" and "line number"). Community: SOURCE_DISTRIBUTION_ID_NUM_1 holds INVOICE_DISTRIBUTION_ID (verify with H2). |
| Indexes | AP_INVOICES_ALL (INVOICE_NUM); unique (VENDOR_ID, INVOICE_NUM, ORG_ID, PARTY_ID); AP_INVOICE_DISTRIBUTIONS_ALL (ACCOUNTING_EVENT_ID); XLA_AE_HEADERS (EVENT_ID, LEDGER_ID); XLA_DISTRIBUTION_LINKS (AE_HEADER_ID, AE_LINE_NUM); XLA_AE_LINES (GL_SL_LINK_ID, GL_SL_LINK_TABLE); GL_IMPORT_REFERENCES (GL_SL_LINK_ID, GL_SL_LINK_TABLE). |
| Notes | Returns one row per SLA line per distribution. A summarized GL line repeats across the SLA lines it contains. Drop the `ledger_id` condition to include secondary and reporting-currency ledgers. Invoice numbers are unique only per supplier, BU and party, hence `:p_vendor_id`. `SOURCE_DISTRIBUTION_ID_NUM_1` values come from different ID sequences per distribution type, so an invoice event that also holds prepayment-application links could match a distribution ID by coincidence. Set `:p_src_dist_type` to the invoice-distribution type from H2 to rule that out; XLA_DISTRIBUTION_LINKS also has an index on (SOURCE_DISTRIBUTION_TYPE, SOURCE_DISTRIBUTION_ID_NUM_1, NVL(SOURCE_DISTRIBUTION_ID_NUM_2, -99)) for queries that start from the distribution. Payment accounting uses `AP_INVOICE_PAYMENTS_ALL.ACCOUNTING_EVENT_ID` with the same pattern. |

Test in a non-production pod.

```sql
SELECT ai.invoice_num,
       aid.invoice_line_number,
       aid.distribution_line_number,
       aid.line_type_lookup_code       AS distribution_type,
       aid.amount                      AS distribution_amount,
       xah.event_type_code,
       xah.accounting_date,
       xah.accounting_entry_status_code,
       xah.gl_transfer_status_code,
       xal.ae_line_num,
       xal.accounting_class_code,
       gcc.concatenated_segments       AS account,
       xdl.source_distribution_type,
       xdl.unrounded_accounted_dr,
       xdl.unrounded_accounted_cr,
       gjh.name                        AS journal_name,
       gjh.je_source,
       gjh.je_category,
       gjh.status                      AS journal_status,
       gjl.je_line_num,
       gjl.accounted_dr                AS journal_line_dr,
       gjl.accounted_cr                AS journal_line_cr
FROM   ap_invoices_all ai
JOIN   ap_invoice_distributions_all aid
       ON  aid.invoice_id = ai.invoice_id
JOIN   xla_ae_headers xah
       ON  xah.event_id       = aid.accounting_event_id
       AND xah.application_id = :p_app_id
       AND xah.ledger_id      = ai.set_of_books_id
JOIN   xla_ae_lines xal
       ON  xal.ae_header_id   = xah.ae_header_id
       AND xal.application_id = xah.application_id
JOIN   xla_distribution_links xdl
       ON  xdl.ae_header_id   = xal.ae_header_id
       AND xdl.ae_line_num    = xal.ae_line_num
       AND xdl.application_id = xal.application_id
       AND xdl.source_distribution_id_num_1 = aid.invoice_distribution_id
       AND (:p_src_dist_type IS NULL OR xdl.source_distribution_type = :p_src_dist_type)
JOIN   gl_code_combinations gcc
       ON  gcc.code_combination_id = xal.code_combination_id
LEFT JOIN gl_import_references gir
       ON  gir.gl_sl_link_id    = xal.gl_sl_link_id
       AND gir.gl_sl_link_table = xal.gl_sl_link_table
LEFT JOIN gl_je_lines gjl
       ON  gjl.je_header_id = gir.je_header_id
       AND gjl.je_line_num  = gir.je_line_num
LEFT JOIN gl_je_headers gjh
       ON  gjh.je_header_id = gjl.je_header_id
WHERE  ai.org_id     = :p_bu_id
AND    ai.invoice_num = :p_invoice_num
AND    (:p_vendor_id IS NULL OR ai.vendor_id = :p_vendor_id)
ORDER  BY aid.invoice_line_number, aid.distribution_line_number, xal.ae_line_num
```

### 9.3 Order-to-Cash queries

#### Q8. Sales order to receipt trace for one order

| Item | Detail |
|---|---|
| Purpose | Returns one timeline row each for the order, its fulfillment lines, shipment lines, AR installments and cash applications. |
| Binds | `:p_order_number`, `:p_bu_id` (selling BU) |
| Joins | FK: DOO_LINES_ALL to DOO_HEADERS_ALL; DOO_FULFILL_LINES_ALL to DOO_LINES_ALL; DOO_FULFILL_LINE_DETAILS to DOO_FULFILL_LINES_ALL; WSH_DELIVERY_ASSIGNMENTS to WSH_DELIVERY_DETAILS and WSH_NEW_DELIVERIES; RA_CUSTOMER_TRX_LINES_ALL to RA_CUSTOMER_TRX_ALL; AR_PAYMENT_SCHEDULES_ALL to RA_CUSTOMER_TRX_ALL; AR_RECEIVABLE_APPLICATIONS_ALL to RA_CUSTOMER_TRX_ALL (APPLIED_CUSTOMER_TRX_ID) and AR_CASH_RECEIPTS_ALL. CC: DOO_FULFILL_LINE_DETAILS.CUSTOMER_TRX_LINE_ID ("Unique identifier for the Billing Line"); WSH_DELIVERY_DETAILS.SALES_ORDER_NUMBER ("Sales Order number from order capture system") to DOO_HEADERS_ALL.SOURCE_ORDER_NUMBER ("Order Capture order number"). Community: WSH_DELIVERY_DETAILS.SOURCE_SHIPMENT_ID ("Identifies the shipment from the source system") equals FULFILL_LINE_ID. |
| Indexes | DOO_HEADERS_ALL function-based (UPPER(ORDER_NUMBER)); DOO_LINES_ALL (HEADER_ID); DOO_FULFILL_LINES_ALL (LINE_ID); DOO_FULFILL_LINE_DETAILS (FULFILL_LINE_ID, TASK_TYPE); WSH_DELIVERY_DETAILS (SALES_ORDER_NUMBER); WSH_DELIVERY_ASSIGNMENTS (DELIVERY_DETAIL_ID); AR_PAYMENT_SCHEDULES_ALL (CUSTOMER_TRX_ID); AR_RECEIVABLE_APPLICATIONS_ALL (APPLIED_CUSTOMER_TRX_ID). |
| Notes | `SUBMITTED_FLAG = 'Y'` follows Oracle's own Order Management SQL example. A revised order keeps its earlier version, which the UI shows with status Reference (Order Management Statuses, 26D). DOO_HEADERS_ALL is unique on (ORDER_NUMBER, SOURCE_ORDER_SYSTEM, SUBMITTED_FLAG, CHANGE_VERSION_NUMBER), so one order number can return several headers: one per source system and per version. If that happens, also bind `SOURCE_ORDER_SYSTEM` and keep the current version (verify in your pod; the `CHANGE_VERSION_NUMBER` comment says "Not used"). WSH_DELIVERY_DETAILS also has an index on (SOURCE_HEADER_NUMBER, SOURCE_SHIPMENT_ID). Validate split fulfillment lines; `FULFILLMENT_SPLIT_REF_ID` references the source line of a split. Alternative AR link: `RA_CUSTOMER_TRX_LINES_ALL.SALES_ORDER` ("Sales order"), which has its own index. The AR BU is `DOO_FULFILL_LINES_ALL.RECEIVABLES_ORG_ID`. The O2C spine in 3.14 documents a second billing link (`RA_CUSTOMER_TRX_LINES_ALL.INTERFACE_LINE_ATTRIBUTE5` = fulfillment line ID, from Oracle's Order Management SQL example); its query 1 is a wide join variant of this trace. |

Test in a non-production pod.

```sql
WITH so AS (
  SELECT dha.header_id, dha.order_number, dha.source_order_number,
         dha.ordered_date, dha.status_code
  FROM   doo_headers_all dha
  WHERE  UPPER(dha.order_number) = UPPER(:p_order_number)
  AND    dha.org_id         = :p_bu_id
  AND    dha.submitted_flag = 'Y'
),
fl AS (
  SELECT dfl.fulfill_line_id, dfl.header_id, dfl.status_code, dfl.ordered_qty,
         dfl.extended_amount, dfl.actual_ship_date, dfl.schedule_ship_date,
         dla.display_line_number || '-' || dfl.fulfill_line_number AS line_ref
  FROM   so
  JOIN   doo_lines_all dla         ON dla.header_id = so.header_id
  JOIN   doo_fulfill_lines_all dfl ON dfl.line_id   = dla.line_id
),
trx AS (
  SELECT DISTINCT rctl.customer_trx_id
  FROM   fl
  JOIN   doo_fulfill_line_details dfld  ON dfld.fulfill_line_id     = fl.fulfill_line_id
  JOIN   ra_customer_trx_lines_all rctl ON rctl.customer_trx_line_id = dfld.customer_trx_line_id
)
SELECT 1 AS step, 'Order' AS doc_type, so.order_number AS doc_number, NULL AS doc_line,
       so.ordered_date AS doc_date, so.status_code AS doc_status, NULL AS quantity, NULL AS amount
FROM   so
UNION ALL
SELECT 2, 'Fulfillment line', so.order_number, fl.line_ref,
       NVL(fl.actual_ship_date, fl.schedule_ship_date), fl.status_code,
       fl.ordered_qty, fl.extended_amount
FROM   so
JOIN   fl ON fl.header_id = so.header_id
UNION ALL
SELECT 3, 'Shipment line', wnd.delivery_name, fl.line_ref, wnd.actual_ship_date,
       wdd.released_status, wdd.shipped_quantity, NULL
FROM   so
JOIN   fl ON fl.header_id = so.header_id
JOIN   wsh_delivery_details wdd
       ON  wdd.sales_order_number = so.source_order_number
       AND wdd.source_shipment_id = fl.fulfill_line_id
LEFT JOIN wsh_delivery_assignments wda ON wda.delivery_detail_id = wdd.delivery_detail_id
LEFT JOIN wsh_new_deliveries wnd       ON wnd.delivery_id        = wda.delivery_id
UNION ALL
SELECT 4, 'AR installment', rct.trx_number, TO_CHAR(arps.terms_sequence_number),
       arps.due_date, arps.status, NULL, arps.amount_due_original
FROM   trx
JOIN   ra_customer_trx_all rct       ON rct.customer_trx_id  = trx.customer_trx_id
JOIN   ar_payment_schedules_all arps ON arps.customer_trx_id = rct.customer_trx_id
UNION ALL
SELECT 5, 'Cash application', acr.receipt_number, rct2.trx_number, ara.apply_date,
       ara.status, NULL, ara.amount_applied
FROM   trx
JOIN   ar_receivable_applications_all ara ON ara.applied_customer_trx_id = trx.customer_trx_id
JOIN   ar_cash_receipts_all acr           ON acr.cash_receipt_id         = ara.cash_receipt_id
JOIN   ra_customer_trx_all rct2           ON rct2.customer_trx_id        = ara.applied_customer_trx_id
WHERE  ara.application_type = 'CASH'
AND    ara.status           = 'APP'
AND    ara.reversal_gl_date IS NULL
ORDER  BY 1, 5
```

#### Q9. Orders and lines on hold

| Item | Detail |
|---|---|
| Purpose | Lists active holds at order, order line and fulfillment line level, with the hold name and age. |
| Binds | `:p_bu_id`, `:p_applied_since` |
| Joins | FK: DOO_HOLD_INSTANCES to DOO_HEADERS_ALL (DOO_HEADER_ID), DOO_LINES_ALL (DOO_LINE_ID), DOO_FULFILL_LINES_ALL (FULFILL_LINE_ID) and DOO_HOLD_CODES_B (HOLD_CODE_ID); DOO_HOLD_CODES_TL to DOO_HOLD_CODES_B (HOLD_CODE_ID). The DOO_HOLD_CODES_TL primary key is (HOLD_CODE_ID, LANGUAGE, ORCHESTRATION_APPLICATION_ID), so the TL join also matches `ORCHESTRATION_APPLICATION_ID` from DOO_HOLD_CODES_B; without it a hold name can repeat. |
| Indexes | DOO_HOLD_INSTANCES (ACTIVE_FLAG, TRANSACTION_ENTITY_NAME1, ORCHESTRATION_APPLICATION_ID, TRANSACTION_ENTITY_ID1, HOLD_CODE_ID); (DOO_HEADER_ID); (FULFILL_LINE_ID); DOO_HOLD_CODES_TL (HOLD_CODE_ID, LANGUAGE, HOLD_NAME). |
| Notes | Returns one row per active hold instance. The `DOO_HEADER_ID` comment does not say that line-level hold instances carry the header ID, so the header join falls back to the line's `HEADER_ID` through NVL. `DOO_HOLD_CODES_B` has the single-column primary key `HOLD_CODE_ID`, so the B join cannot repeat. `ON_HOLD` flags on DOO_HEADERS_ALL, DOO_LINES_ALL and DOO_FULFILL_LINES_ALL give a quick yes or no without the hold details. Released holds keep `RELEASE_DATE` and `HOLD_RELEASE_REASON_CODE` for audit queries. |

Test in a non-production pod.

```sql
SELECT bu.bu_name,
       dha.order_number,
       dha.ordered_date,
       dla.display_line_number,
       dfl.fulfill_line_number,
       CASE WHEN dhi.fulfill_line_id IS NOT NULL THEN 'Fulfillment line'
            WHEN dhi.doo_line_id     IS NOT NULL THEN 'Order line'
            ELSE 'Order' END                    AS hold_level,
       dhcb.hold_code,
       dhct.hold_name,
       dhct.hold_description,
       dhi.apply_date,
       TRUNC(SYSDATE) - TRUNC(dhi.apply_date)  AS days_on_hold,
       dhi.apply_system,
       dhi.apply_user_id,
       dhi.hold_comments
FROM   doo_hold_instances dhi
JOIN   doo_hold_codes_b dhcb
       ON  dhcb.hold_code_id = dhi.hold_code_id
JOIN   doo_hold_codes_tl dhct
       ON  dhct.hold_code_id                 = dhcb.hold_code_id
       AND dhct.orchestration_application_id = dhcb.orchestration_application_id
       AND dhct.language                     = USERENV('LANG')
LEFT JOIN doo_fulfill_lines_all dfl ON dfl.fulfill_line_id = dhi.fulfill_line_id
LEFT JOIN doo_lines_all dla         ON dla.line_id = NVL(dhi.doo_line_id, dfl.line_id)
JOIN   doo_headers_all dha          ON dha.header_id = NVL(dhi.doo_header_id, dla.header_id)
JOIN   fun_all_business_units_v bu  ON bu.bu_id      = dha.org_id
WHERE  dhi.active_flag    = 'Y'
AND    dha.org_id         = :p_bu_id
AND    dha.submitted_flag = 'Y'
AND    dhi.apply_date    >= :p_applied_since
ORDER  BY days_on_hold DESC, dha.order_number
```

#### Q10. Shipped but not invoiced fulfillment lines

| Item | Detail |
|---|---|
| Purpose | Lists open, billable fulfillment lines that have shipped quantity but no billing line yet, with the translated line status. |
| Binds | `:p_bu_id`, `:p_ship_from`, `:p_ship_to` |
| Joins | FK: DOO_FULFILL_LINES_ALL to DOO_LINES_ALL; DOO_LINES_ALL to DOO_HEADERS_ALL; DOO_FULFILL_LINE_DETAILS to DOO_FULFILL_LINES_ALL; DOO_STATUSES_TL to DOO_STATUSES_B (STATUS_ID). CC: DOO_FULFILL_LINES_ALL.STATUS_CODE ("Current fulfillment status") to DOO_STATUSES_B.STATUS_CODE. |
| Indexes | DOO_FULFILL_LINES_ALL (OPEN_FLAG, STATUS_CODE); (LINE_ID); DOO_FULFILL_LINE_DETAILS (FULFILL_LINE_ID, TASK_TYPE). |
| Notes | The Line Status values documented in Order Management Statuses are Not Started, Scheduled, Shipped, Awaiting Billing, Billed and Closed, plus Canceled. This query catches lines that have shipped but are not yet billed. `INVOICE_INTERFACED_FLAG` and `INVOICE_INTERFACE_STATUS` separate lines not yet sent to Receivables from lines waiting for AutoInvoice. Lines with `INVOICE_ENABLED_FLAG = 'N'` are excluded; a null flag is treated as billable. DOO_STATUSES_B is unique on (ORCHESTRATION_APPLICATION_ID, STATUS_CODE), and DOO_FULFILL_LINES_ALL has no orchestration application column, so the scalar subquery uses MAX. |

Test in a non-production pod.

```sql
SELECT bu.bu_name,
       dha.order_number,
       dla.display_line_number || '-' || dfl.fulfill_line_number AS fulfillment_line,
       (SELECT MAX(dst.display_name)
        FROM   doo_statuses_b dsb
        JOIN   doo_statuses_tl dst
               ON  dst.status_id = dsb.status_id
               AND dst.language  = USERENV('LANG')
        WHERE  dsb.status_code = dfl.status_code)        AS line_status,
       dfl.shipped_qty,
       dfl.ordered_uom,
       dfl.actual_ship_date,
       TRUNC(SYSDATE) - dfl.actual_ship_date             AS days_since_ship,
       dfl.extended_amount,
       dfl.invoice_interfaced_flag,
       dfl.invoice_interface_status,
       dfl.receivables_org_id
FROM   doo_fulfill_lines_all dfl
JOIN   doo_lines_all dla           ON dla.line_id   = dfl.line_id
JOIN   doo_headers_all dha         ON dha.header_id = dla.header_id
JOIN   fun_all_business_units_v bu ON bu.bu_id      = dfl.org_id
WHERE  dfl.org_id         = :p_bu_id
AND    dha.submitted_flag = 'Y'
AND    dfl.open_flag      = 'Y'
AND    NVL(dfl.shipped_qty, 0) > 0
AND    NVL(dfl.invoice_enabled_flag, 'Y') = 'Y'
AND    dfl.actual_ship_date BETWEEN :p_ship_from AND :p_ship_to
AND    NOT EXISTS (SELECT 1
                   FROM   doo_fulfill_line_details dfld
                   WHERE  dfld.fulfill_line_id = dfl.fulfill_line_id
                   AND    dfld.customer_trx_line_id IS NOT NULL)
ORDER  BY dfl.actual_ship_date, dha.order_number
```

#### Q11. AR open items with aging buckets

| Item | Detail |
|---|---|
| Purpose | Lists open payment schedules aged by days past due on `:p_as_of_date`, with fixed buckets. |
| Binds | `:p_bu_id`, `:p_as_of_date` |
| Joins | FK: AR_PAYMENT_SCHEDULES_ALL to HZ_CUST_ACCOUNTS (CUSTOMER_ID); HZ_CUST_ACCOUNTS to HZ_PARTIES (PARTY_ID). |
| Indexes | AR_PAYMENT_SCHEDULES_ALL (STATUS, CLASS, DUE_DATE); (CUSTOMER_ID, STATUS); (CUSTOMER_SITE_USE_ID, STATUS). |
| Notes | The table description sets `CLASS` to INV, DM, CM, CB, PMT or BR. `STATUS` moves from OP to CL when `AMOUNT_DUE_REMAINING` reaches 0. Credit items such as credit memos and receipts carry negative amounts, so a sum by customer gives the net balance. `AMOUNT_DUE_REMAINING` is the current balance, so this ages today's open amounts against the as-of date; historical as-of aging must back out later applications and adjustments. Receipts with no customer drop out of the inner join. For configured buckets, use `AR_AGING_BUCKETS` and `AR_AGING_BUCKET_LINES_B` (`DAYS_START`, `DAYS_TO`). |

Test in a non-production pod.

```sql
SELECT bu.bu_name,
       hp.party_name                AS customer_name,
       hca.account_number,
       x.trx_number,
       x.class,
       x.trx_date,
       x.due_date,
       x.invoice_currency_code,
       x.amount_due_original,
       x.amount_due_remaining,
       x.acctd_amount_due_remaining,
       x.days_past_due,
       CASE WHEN x.days_past_due <= 0               THEN x.amount_due_remaining ELSE 0 END AS current_amt,
       CASE WHEN x.days_past_due BETWEEN 1   AND 30  THEN x.amount_due_remaining ELSE 0 END AS past_1_30,
       CASE WHEN x.days_past_due BETWEEN 31  AND 60  THEN x.amount_due_remaining ELSE 0 END AS past_31_60,
       CASE WHEN x.days_past_due BETWEEN 61  AND 90  THEN x.amount_due_remaining ELSE 0 END AS past_61_90,
       CASE WHEN x.days_past_due BETWEEN 91  AND 180 THEN x.amount_due_remaining ELSE 0 END AS past_91_180,
       CASE WHEN x.days_past_due > 180               THEN x.amount_due_remaining ELSE 0 END AS past_over_180
FROM  (SELECT arps.org_id, arps.customer_id, arps.trx_number, arps.class, arps.trx_date,
              arps.due_date, arps.invoice_currency_code, arps.amount_due_original,
              arps.amount_due_remaining, arps.acctd_amount_due_remaining,
              TRUNC(:p_as_of_date) - arps.due_date AS days_past_due
       FROM   ar_payment_schedules_all arps
       WHERE  arps.org_id  = :p_bu_id
       AND    arps.status  = 'OP'
       AND    arps.class  IN ('INV', 'DM', 'CB', 'CM', 'PMT')
       AND    arps.gl_date <= :p_as_of_date) x
JOIN   hz_cust_accounts hca        ON hca.cust_account_id = x.customer_id
JOIN   hz_parties hp               ON hp.party_id         = hca.party_id
JOIN   fun_all_business_units_v bu ON bu.bu_id            = x.org_id
ORDER  BY hp.party_name, x.due_date
```

#### Q12. Unapplied, on-account and unidentified receipts

| Item | Detail |
|---|---|
| Purpose | Lists cash receipts that still have an unapplied, on-account or unidentified amount. |
| Binds | `:p_bu_id`, `:p_receipt_from`, `:p_receipt_to` |
| Joins | FK: AR_RECEIVABLE_APPLICATIONS_ALL to AR_CASH_RECEIPTS_ALL; AR_CASH_RECEIPTS_ALL to AR_RECEIPT_METHODS and HZ_CUST_ACCOUNTS (PAY_FROM_CUSTOMER); HZ_CUST_ACCOUNTS to HZ_PARTIES. |
| Indexes | AR_CASH_RECEIPTS_ALL (RECEIPT_DATE); (RECEIPT_NUMBER, ORG_ID); AR_RECEIVABLE_APPLICATIONS_ALL (CASH_RECEIPT_ID, STATUS). |
| Notes | The table description says a new receipt gets one UNAPP row and each application adds an APP row plus a negative UNAPP row. Summing by status therefore gives the remaining amount, so reversed pairs are left in the sum. The `TYPE` comment says to code `!= 'MISC'` rather than `= 'CASH'`. The `CONFIRMED_FLAG` comment says to treat null as Y. |

Test in a non-production pod.

```sql
SELECT bu.bu_name,
       acr.receipt_number,
       acr.receipt_date,
       acr.amount              AS receipt_amount,
       acr.currency_code,
       acr.status              AS receipt_status,
       arm.name                AS receipt_method,
       hca.account_number,
       hp.party_name           AS customer_name,
       SUM(CASE WHEN ara.status = 'UNAPP' THEN ara.amount_applied ELSE 0 END) AS unapplied_amount,
       SUM(CASE WHEN ara.status = 'ACC'   THEN ara.amount_applied ELSE 0 END) AS on_account_amount,
       SUM(CASE WHEN ara.status = 'UNID'  THEN ara.amount_applied ELSE 0 END) AS unidentified_amount
FROM   ar_cash_receipts_all acr
JOIN   ar_receivable_applications_all ara ON ara.cash_receipt_id   = acr.cash_receipt_id
JOIN   ar_receipt_methods arm             ON arm.receipt_method_id = acr.receipt_method_id
JOIN   fun_all_business_units_v bu        ON bu.bu_id              = acr.org_id
LEFT JOIN hz_cust_accounts hca            ON hca.cust_account_id   = acr.pay_from_customer
LEFT JOIN hz_parties hp                   ON hp.party_id           = hca.party_id
WHERE  acr.org_id = :p_bu_id
AND    acr.type  != 'MISC'
AND    acr.reversal_date IS NULL
AND    acr.receipt_date BETWEEN :p_receipt_from AND :p_receipt_to
AND    ara.status IN ('UNAPP', 'ACC', 'UNID')
AND    NVL(ara.confirmed_flag, 'Y') = 'Y'
GROUP  BY bu.bu_name, acr.cash_receipt_id, acr.receipt_number, acr.receipt_date, acr.amount,
          acr.currency_code, acr.status, arm.name, hca.account_number, hp.party_name
HAVING SUM(CASE WHEN ara.status = 'UNAPP' THEN ara.amount_applied ELSE 0 END) <> 0
    OR SUM(CASE WHEN ara.status = 'ACC'   THEN ara.amount_applied ELSE 0 END) <> 0
    OR SUM(CASE WHEN ara.status = 'UNID'  THEN ara.amount_applied ELSE 0 END) <> 0
ORDER  BY acr.receipt_date, acr.receipt_number
```

#### Q13. Receipt applications to invoices

| Item | Detail |
|---|---|
| Purpose | Lists current cash applications to transactions and installments, with line, tax, freight, charges and discount splits. |
| Binds | `:p_bu_id`, `:p_apply_from`, `:p_apply_to` |
| Joins | FK: AR_RECEIVABLE_APPLICATIONS_ALL to AR_CASH_RECEIPTS_ALL, RA_CUSTOMER_TRX_ALL (APPLIED_CUSTOMER_TRX_ID) and AR_PAYMENT_SCHEDULES_ALL (APPLIED_PAYMENT_SCHEDULE_ID); RA_CUSTOMER_TRX_ALL to HZ_CUST_ACCOUNTS (BILL_TO_CUSTOMER_ID); HZ_CUST_ACCOUNTS to HZ_PARTIES. |
| Indexes | AR_RECEIVABLE_APPLICATIONS_ALL (APPLY_DATE); (APPLIED_PAYMENT_SCHEDULE_ID, GL_DATE); (APPLIED_CUSTOMER_TRX_ID). |
| Notes | Returns one row per application. The comment on `REVERSAL_GL_DATE` says it is set on both the reversed row and the reversing row, so the null filter keeps only applications that are still live. For cross-currency applications, `AMOUNT_APPLIED` is in transaction currency and `AMOUNT_APPLIED_FROM` is in receipt currency. Use `APPLICATION_TYPE = 'CM'` for credit memo applications. |

Test in a non-production pod.

```sql
SELECT bu.bu_name,
       acr.receipt_number,
       acr.receipt_date,
       acr.currency_code            AS receipt_currency,
       rct.trx_number,
       rct.trx_date,
       arps.terms_sequence_number   AS installment,
       arps.due_date,
       ara.apply_date,
       ara.gl_date,
       ara.amount_applied,
       ara.amount_applied_from,
       ara.line_applied,
       ara.tax_applied,
       ara.freight_applied,
       ara.receivables_charges_applied,
       ara.earned_discount_taken,
       ara.unearned_discount_taken,
       ara.acctd_amount_applied_to,
       hp.party_name                AS customer_name,
       hca.account_number
FROM   ar_receivable_applications_all ara
JOIN   ar_cash_receipts_all acr      ON acr.cash_receipt_id      = ara.cash_receipt_id
JOIN   ra_customer_trx_all rct       ON rct.customer_trx_id      = ara.applied_customer_trx_id
JOIN   ar_payment_schedules_all arps ON arps.payment_schedule_id = ara.applied_payment_schedule_id
JOIN   hz_cust_accounts hca          ON hca.cust_account_id      = rct.bill_to_customer_id
JOIN   hz_parties hp                 ON hp.party_id              = hca.party_id
JOIN   fun_all_business_units_v bu   ON bu.bu_id                 = ara.org_id
WHERE  ara.org_id           = :p_bu_id
AND    ara.application_type = 'CASH'
AND    ara.status           = 'APP'
AND    ara.reversal_gl_date IS NULL
AND    ara.apply_date BETWEEN :p_apply_from AND :p_apply_to
ORDER  BY acr.receipt_number, rct.trx_number
```

#### Q14. AR transaction accounting drill-down to GL

| Item | Detail |
|---|---|
| Purpose | Traces each AR distribution (revenue, receivable, tax and so on) through its SLA line to the GL journal line in the primary ledger. |
| Binds | `:p_bu_id`, `:p_trx_number`, `:p_app_id` (222), `:p_src_dist_type` (optional) |
| Joins | FK: RA_CUST_TRX_LINE_GL_DIST_ALL to RA_CUSTOMER_TRX_ALL, RA_CUSTOMER_TRX_LINES_ALL and XLA_EVENTS (documented on EVENT_ID, PROGRAM_APPLICATION_ID). CC: XLA_AE_HEADERS.EVENT_ID carries the same event identifier. The SLA and GL joins are as in Q7. Community (EBS-era post): SOURCE_DISTRIBUTION_ID_NUM_1 holds CUST_TRX_LINE_GL_DIST_ID with SOURCE_DISTRIBUTION_TYPE = 'RA_CUST_TRX_LINE_GL_DIST_ALL'; confirm the value with H2 before you set `:p_src_dist_type`. |
| Indexes | RA_CUSTOMER_TRX_ALL (TRX_NUMBER, ORG_ID); RA_CUST_TRX_LINE_GL_DIST_ALL (EVENT_ID); (CUSTOMER_TRX_ID, ACCOUNT_CLASS, LATEST_REC_FLAG, CODE_COMBINATION_ID); then the SLA indexes from Q7. |
| Notes | `ACCOUNT_SET_FLAG = 'N'` keeps actual distributions and drops account-set rows. Per the table description, invoices with rules get their actual distributions only when Revenue Recognition runs. The REC row carries the total invoice amount (table description), so it is not tied to one line; hence the outer join to lines. `LATEST_REC_FLAG = 'Y'` marks the current REC row. Receipt accounting starts from `AR_CASH_RECEIPT_HISTORY_ALL.EVENT_ID` and `AR_RECEIVABLE_APPLICATIONS_ALL.EVENT_ID` with the same pattern. |

Test in a non-production pod.

```sql
SELECT rct.trx_number,
       rctl.line_number,
       rctl.line_type,
       rgd.account_class,
       rgd.gl_date,
       rgd.amount,
       rgd.acctd_amount,
       xah.event_type_code,
       xah.accounting_date,
       xah.accounting_entry_status_code,
       xah.gl_transfer_status_code,
       xal.ae_line_num,
       xal.accounting_class_code,
       gcc.concatenated_segments     AS account,
       xdl.unrounded_accounted_dr,
       xdl.unrounded_accounted_cr,
       gjh.name                      AS journal_name,
       gjh.status                    AS journal_status,
       gjl.je_line_num,
       gjl.accounted_dr              AS journal_line_dr,
       gjl.accounted_cr              AS journal_line_cr
FROM   ra_customer_trx_all rct
JOIN   ra_cust_trx_line_gl_dist_all rgd
       ON  rgd.customer_trx_id  = rct.customer_trx_id
       AND rgd.account_set_flag = 'N'
LEFT JOIN ra_customer_trx_lines_all rctl
       ON  rctl.customer_trx_line_id = rgd.customer_trx_line_id
JOIN   xla_ae_headers xah
       ON  xah.event_id       = rgd.event_id
       AND xah.application_id = :p_app_id
       AND xah.ledger_id      = rct.set_of_books_id
JOIN   xla_ae_lines xal
       ON  xal.ae_header_id   = xah.ae_header_id
       AND xal.application_id = xah.application_id
JOIN   xla_distribution_links xdl
       ON  xdl.ae_header_id   = xal.ae_header_id
       AND xdl.ae_line_num    = xal.ae_line_num
       AND xdl.application_id = xal.application_id
       AND xdl.source_distribution_id_num_1 = rgd.cust_trx_line_gl_dist_id
       AND (:p_src_dist_type IS NULL OR xdl.source_distribution_type = :p_src_dist_type)
JOIN   gl_code_combinations gcc
       ON  gcc.code_combination_id = xal.code_combination_id
LEFT JOIN gl_import_references gir
       ON  gir.gl_sl_link_id    = xal.gl_sl_link_id
       AND gir.gl_sl_link_table = xal.gl_sl_link_table
LEFT JOIN gl_je_lines gjl
       ON  gjl.je_header_id = gir.je_header_id
       AND gjl.je_line_num  = gir.je_line_num
LEFT JOIN gl_je_headers gjh
       ON  gjh.je_header_id = gjl.je_header_id
WHERE  rct.org_id     = :p_bu_id
AND    rct.trx_number = :p_trx_number
ORDER  BY rctl.line_number, rgd.account_class, xal.ae_line_num
```

### 9.4 Master data extracts

#### Q15. Customer master: party, account, site, site use, location

| Item | Detail |
|---|---|
| Purpose | Flat customer extract for reconciliation or migration checks, with an optional incremental filter. |
| Binds | `:p_set_id` (optional), `:p_changed_since` (optional) |
| Joins | FK: HZ_CUST_ACCOUNTS to HZ_PARTIES; HZ_CUST_ACCT_SITES_ALL to HZ_CUST_ACCOUNTS and HZ_PARTY_SITES; HZ_PARTY_SITES to HZ_LOCATIONS; HZ_CUST_SITE_USES_ALL to HZ_CUST_ACCT_SITES_ALL. |
| Indexes | HZ_CUST_ACCOUNTS (PARTY_ID); (LAST_UPDATE_DATE, CUST_ACCOUNT_ID); HZ_CUST_ACCT_SITES_ALL (CUST_ACCOUNT_ID, STATUS, BILL_TO_FLAG, SET_ID); (LAST_UPDATE_DATE, CUST_ACCT_SITE_ID); HZ_CUST_SITE_USES_ALL (CUST_ACCT_SITE_ID, PRIMARY_FLAG, SITE_USE_CODE); HZ_PARTY_SITES (LOCATION_ID). |
| Notes | Returns one row per active site use; a site with no active use returns once with null use columns. Account sites and site uses are reference-data-set enabled (`SET_ID`), not BU-striped. A BU's default set is `FUN_ALL_BUSINESS_UNITS_V.DEFAULT_SET_ID`, and set assignments are in `FND_SETID_ASSIGNMENTS`. The status columns use the CODE_STATUS lookup. A means active and I inactive, the TCA convention documented on `HZ_PARTY_SITE_USES.STATUS`. `BILL_TO_FLAG` and `SHIP_TO_FLAG` hold Y, P (primary) or N. |

Test in a non-production pod.

```sql
SELECT hp.party_number,
       hp.party_name,
       hp.party_type,
       hca.account_number,
       hca.account_name,
       hca.status            AS account_status,
       hca.customer_class_code,
       hps.party_site_number,
       hl.address1,
       hl.address2,
       hl.city,
       hl.state,
       hl.postal_code,
       hl.country,
       hcas.set_id,
       hcas.bill_to_flag,
       hcas.ship_to_flag,
       hcsu.site_use_id,
       hcsu.site_use_code,
       hcsu.location         AS site_use_location,
       hcsu.primary_flag
FROM   hz_cust_accounts hca
JOIN   hz_parties hp              ON hp.party_id          = hca.party_id
JOIN   hz_cust_acct_sites_all hcas ON hcas.cust_account_id = hca.cust_account_id
JOIN   hz_party_sites hps         ON hps.party_site_id    = hcas.party_site_id
JOIN   hz_locations hl            ON hl.location_id       = hps.location_id
LEFT JOIN hz_cust_site_uses_all hcsu
       ON  hcsu.cust_acct_site_id = hcas.cust_acct_site_id
       AND hcsu.status            = 'A'
WHERE  hca.status  = 'A'
AND    hcas.status = 'A'
AND    (:p_set_id IS NULL OR hcas.set_id = :p_set_id)
AND    (:p_changed_since IS NULL
        OR hca.last_update_date  >= :p_changed_since
        OR hcas.last_update_date >= :p_changed_since
        OR hl.last_update_date   >= :p_changed_since)
ORDER  BY hp.party_name, hca.account_number, hps.party_site_number, hcsu.site_use_code
```

#### Q16. Supplier master: supplier, site, address, site assignment

| Item | Detail |
|---|---|
| Purpose | Flat supplier extract by procurement BU, with client BU assignments and the liability account. |
| Binds | `:p_prc_bu_id`, `:p_client_bu_id` (optional), `:p_as_of_date`, `:p_changed_since` (optional) |
| Joins | FK: POZ_SUPPLIERS to HZ_PARTIES (PARTY_ID); POZ_SUPPLIER_SITES_ALL_M to POZ_SUPPLIERS (VENDOR_ID) and HZ_PARTY_SITES (PARTY_SITE_ID); HZ_PARTY_SITES to HZ_LOCATIONS; POZ_SITE_ASSIGNMENTS_ALL_M to GL_CODE_COMBINATIONS (ACCTS_PAY_CODE_COMBINATION_ID). CC: POZ_SITE_ASSIGNMENTS_ALL_M.VENDOR_SITE_ID ("Vendor Site identifier"); BU_ID and BILL_TO_BU_ID to FUN_ALL_BUSINESS_UNITS_V. |
| Indexes | POZ_SUPPLIER_SITES_ALL_M unique (VENDOR_ID, PRC_BU_ID, UPPER(VENDOR_SITE_CODE)); (PARTY_SITE_ID); (LAST_UPDATE_DATE); POZ_SITE_ASSIGNMENTS_ALL_M unique (VENDOR_SITE_ID, BU_ID); POZ_SUPPLIERS (PARTY_ID); (LAST_UPDATE_DATE). |
| Notes | Returns one row per site and client BU assignment. The supplier name is `HZ_PARTIES.PARTY_NAME`; `POZ_SUPPLIERS` has no name column. `SEGMENT1` is the supplier number and has a unique index; the column comment says only "Key Flexfield: segment", so the meaning comes from community sources. Supplier tax and bank attributes may sit in PII-protected tables such as `POZ_SUPPLIER_SITES_PII` (VPD; see 9.1). |

Test in a non-production pod.

```sql
SELECT sup.segment1                AS supplier_number,
       hp.party_name               AS supplier_name,
       sup.vendor_type_lookup_code,
       sup.end_date_active         AS supplier_end_date,
       bu_prc.bu_name              AS procurement_bu,
       sts.vendor_site_code,
       sts.purchasing_site_flag,
       sts.pay_site_flag,
       sts.inactive_date           AS site_inactive_date,
       hl.address1,
       hl.address2,
       hl.city,
       hl.state,
       hl.postal_code,
       hl.country,
       bu_cli.bu_name              AS client_bu,
       bu_bill.bu_name             AS bill_to_bu,
       ssa.inactive_date           AS assignment_inactive_date,
       gcc.concatenated_segments   AS liability_account
FROM   poz_suppliers sup
JOIN   hz_parties hp                   ON hp.party_id       = sup.party_id
JOIN   poz_supplier_sites_all_m sts    ON sts.vendor_id     = sup.vendor_id
JOIN   fun_all_business_units_v bu_prc ON bu_prc.bu_id      = sts.prc_bu_id
LEFT JOIN hz_party_sites hps           ON hps.party_site_id = sts.party_site_id
LEFT JOIN hz_locations hl              ON hl.location_id    = hps.location_id
LEFT JOIN poz_site_assignments_all_m ssa ON ssa.vendor_site_id = sts.vendor_site_id
LEFT JOIN fun_all_business_units_v bu_cli  ON bu_cli.bu_id  = ssa.bu_id
LEFT JOIN fun_all_business_units_v bu_bill ON bu_bill.bu_id = ssa.bill_to_bu_id
LEFT JOIN gl_code_combinations gcc     ON gcc.code_combination_id = ssa.accts_pay_code_combination_id
WHERE  sts.prc_bu_id = :p_prc_bu_id
AND    (:p_client_bu_id IS NULL OR ssa.bu_id = :p_client_bu_id)
AND    NVL(sts.inactive_date, :p_as_of_date + 1) > :p_as_of_date
AND    (:p_changed_since IS NULL
        OR sup.last_update_date >= :p_changed_since
        OR sts.last_update_date >= :p_changed_since)
ORDER  BY hp.party_name, sts.vendor_site_code, bu_cli.bu_name
```

### 9.5 Sources for non-catalog facts

| Fact | Source |
|---|---|
| ApplicationDB_FSCM default data source; Oracle's `SUBMITTED_FLAG = 'Y'` and `OPEN_FLAG` usage | [Use SQL to Query Order Management Data (26D)](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faiom/use-sql-to-query-order-management-data.html) |
| Base-table SQL is not subject to data security; secured list views; VPD on PII tables | [Overview of Security for Oracle Fusion Cloud SCM Reports](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fassc/overview-of-security-for-oracle-fusion-cloud-scm-reports.html); [Business Intelligence Publisher Secured List Views](https://docs.oracle.com/en/cloud/saas/human-resources/ochus/business-intelligence-publisher-secured-list-views.html) |
| `:xdo_user_name` and related system variables (non-Fusion guides; behaviour assumed to match Fusion) | [Include User Information Stored in System Variables (Oracle Analytics Server)](https://docs.oracle.com/en/middleware/bi/analytics-server/design-publish/include-user-information-stored-system-variables-your-report-data.html); [BI Publisher 12.2.1.2 Data Modeling Guide: system variables](https://docs.oracle.com/middleware/12212/bip/BIPDM/GUID-2A6E4B9B-ABCD-4CF0-A458-59B89F2443A1.htm) |
| Create Uninvoiced Receipt Accrual (Report and Accounting modes, POs not accrued at receipt); Uninvoiced Receipt Accrual Report | [Create Uninvoiced Receipt Accrual (26D)](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faspc/create-uninvoiced-receipt-accrual.html); [Uninvoiced Receipt Accrual Report (26D)](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faspc/uninvoiced-receipt-accrual-report.html) |
| View texts: user data assignments, BUs, secured payments, lookups (application IDs) | [FUN_USER_BO_DATA_ASSIGNMENTS_V](https://docs.oracle.com/en/cloud/saas/financials/26d/oedmf/funuserbodataassignmentsv-3514.html); [FUN_ALL_BUSINESS_UNITS_V](https://docs.oracle.com/en/cloud/saas/financials/26d/oedmf/funallbusinessunitsv-5340.html); [IBY_PAYMENTS_SEC_V](https://docs.oracle.com/en/cloud/saas/financials/26d/oedmf/ibypaymentssecv-3968.html); [AP_LOOKUP_CODES](https://docs.oracle.com/en/cloud/saas/financials/26d/oedmf/aplookupcodes-3863.html); [AR_LOOKUPS](https://docs.oracle.com/en/cloud/saas/financials/26d/oedmf/arlookups-4099.html) |
| Order and fulfillment line statuses, including Reference | [Order Management Statuses (26D)](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fauom/order-management-statuses.html) |
| Purchase order and line statuses (display values) | [Purchase Order Statuses (26D)](https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/purchase-order-statuses.html) |
| Community (verify): shipping to fulfillment line join (`SALES_ORDER_NUMBER` to `SOURCE_ORDER_NUMBER`, `SOURCE_SHIPMENT_ID` to `FULFILL_LINE_ID`) | [Open shipment lines SQL](https://www.vm-oracle.com/clouderp/order-mgmt/openshipmentlines/) |
| Community (verify): SLA source distribution types and `SOURCE_DISTRIBUTION_ID_NUM_1` for AP invoice and AR transaction distributions | [Joins between XLA, GL and AP](https://sharingoracle.blogspot.com/2017/10/joins-between-xla-gl-and-ap.html) |
| Community (verify): Receivables application ID 222 in SLA joins | [Receivables accounting SQL in Fusion](https://appsoracle-abhi.blogspot.com/2019/05/receipt-accounting-sql-in-fusion.html) |
| Community (verify): supplier number in `POZ_SUPPLIERS.SEGMENT1`; supplier name in `HZ_PARTIES` | [POZ_SUPPLIERS in Oracle Fusion](https://oraclebytes.com/poz_suppliers-supplier-table-in-oracle-fusion/) |
