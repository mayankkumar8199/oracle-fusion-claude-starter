## 7. Bulk data, SOAP services, scheduled processes and events

This section covers the bulk and asynchronous channels for P2P and O2C: file-based data import (FBDI), the ERP Integration Service, ADFdi workbooks, SOAP services, scheduled processes (Oracle Enterprise Scheduler, ESS) and business events. REST resources are in section 6, BI Publisher, OTBI and BICC extracts in section 8, SQL in section 9, roles and privileges in section 12.

### 7.1 FBDI end to end

FBDI has three parts: an XLSM template per business object, the Load Interface File for Import process that loads the generated CSV files into interface tables, and an object-specific import process that validates the interface rows and creates application data.

| # | Step | UI action (26D) | Automation equivalent (7.4) |
|---|---|---|---|
| 1 | Get the template | Open the object page in the FBDI guide for Financials, Procurement or SCM. File Links gives the XLSM template (`https://www.oracle.com/webfolder/technetwork/docs/fbdi-26d/fbdi/xlsm/<TEMPLATE>.xlsm`) and its control files. Templates are Windows Excel only. | Generate files with the same layout as the template output. |
| 2 | Prepare data | Fill the worksheets. Keep the column order; hide unused columns, never delete them. Click Generate CSV File on the Instructions and CSV Generation sheet to get a zip. | Zip the CSV files yourself. |
| 3 | Upload | Navigator > Tools > File Import and Export > Actions > Upload. Select the zip and the UCM account of the object (for example `fin/payables/import`), then Save and Close. | `uploadFileToUcm`, or `importBulkData` (upload, load and import in one call). REST writes the account as `fin$/payables$/import$`. |
| 4 | Load | Tools > Scheduled Processes > Schedule New Process > Load Interface File for Import. Required parameters: Import Process, Data File. Child process: Load File to Interface. The parent ends in error if any row fails to load. | `submitESSJobRequest` with job InterfaceLoaderController, or `importBulkData`. |
| 5 | Import | Submit the import process of the object (7.2, 7.3). Valid rows become application data; rejected rows stay in the interface tables and appear in the import report. | `importBulkData` with `ImportOption=Y`, or `submitESSJobRequest` with the import job. |
| 6 | Correct | Load error: all rows already loaded are deleted and the whole batch is rejected; fix the data, regenerate the zip, upload and reload. Import error: read the import log or report, fix the rows with the correction workbook (table below), resubmit the import. | `updateInterfaceData` uploads corrected interface data for an import process and load request ID. |
| 7 | Purge | FBDI interface data older than 30 days is purged automatically per import process. Manually: Purge Interface Tables (Purge Process Intent = File-based data import (FBDI), Maintenance or Other; Import Process; Load Request ID or a load request ID range; optional Extract Data, Allow Context Purge of Data, Number of Days (more than 30, Maintenance only)). Product purges are in 7.7. | `extractAndPurge`; `PurgeOption=Y` in `importBulkData`; `submitESSJobRequest` with job InterfaceLoaderPurge. |

- Job package, job definition and parameter order: Setup and Maintenance > Application Extensions > Manage Enterprise Scheduler Job Definitions and Job Sets for Financial, Supply Chain Management, and Related Applications. Predefined jobs carry an asterisk.
- The Scheduled Processes work area needs a role with the Manage Scheduled Processes privilege. Purge Interface Tables needs the Load Interface File for Import privilege (privilege codes: section 12).

#### Where import errors land and how to fix them

| Import process | Interface tables (main) | Error or rejection table | Correction tool |
|---|---|---|---|
| Import Payables Invoices | AP_INVOICES_INTERFACE, AP_INVOICE_LINES_INTERFACE | AP_INTERFACE_REJECTIONS | Correct Import Errors spreadsheet, then Upload and Import |
| Import AutoInvoice | RA_INTERFACE_LINES_ALL, RA_INTERFACE_DISTRIBUTIONS_ALL, RA_INTERFACE_SALESCREDITS_ALL, AR_INTERFACE_CONTS_ALL | RA_INTERFACE_ERRORS_ALL | Manage AutoInvoice Lines workbook (Billing work area) or the Import Exceptions infotile, then Save and Run AutoInvoice |
| Process Receipts Through Lockbox | AR_PAYMENTS_INTERFACE_ALL | Lockbox execution report | Manage Lockbox Transmission page: correct or mark for deletion, then Upload |
| Import Orders, Import Blanket Agreements, Import Contract Agreements | PO_HEADERS_INTERFACE, PO_LINES_INTERFACE, PO_LINE_LOCATIONS_INTERFACE, PO_DISTRIBUTIONS_INTERFACE | PO_INTERFACE_ERRORS | Import report; correct the source file and resubmit |
| Import Requisitions | POR_REQ_HEADERS_INTERFACE_ALL, POR_REQ_LINES_INTERFACE_ALL, POR_REQ_DISTS_INTERFACE_ALL | POR_REQ_IMPORT_ERRORS | Correct and reload |
| Import Suppliers and child imports | POZ_SUPPLIERS_INT and the other supplier interface tables (7.2) | POZ_SUPPLIER_INT_REJECTIONS | Job output report; fix the template and reload. Purge: Suppliers work area > Import Suppliers > Actions > Purge Supplier Interface Records |
| Manage Receiving Transactions | RCV_HEADERS_INTERFACE, RCV_TRANSACTIONS_INTERFACE | RCV_INTERFACE_ERRORS | Review Receipts Interface ADFdi workbook (Inventory Management work area task); correct and resubmit |
| Import Trading Community Data in Bulk | Trading Community import tables (7.3) | HZ_IMP_ERRORS | Manage Data Import Batches > batch ID > Edit Data Import Batch > Report |
| Upload Customers | AR_UPD_CUSTOMERS, AR_UPD_CONTACTS, AR_UPD_REF_ACCOUNTS, AR_UPD_BANK_ACCOUNTS | AR_UPD_CUST_ERRORS, AR_UPD_CONTACTS_ERRORS, AR_UPD_REFACCT_ERRORS, AR_UPD_BNKACCT_ERRORS | Correct Customer Data spreadsheet; profile class, payment method, reference account and bank account errors need a new upload |
| Import Intercompany Transactions | FUN_INTERFACE_BATCHES, FUN_INTERFACE_HEADERS, FUN_INTERFACE_DIST_LINES, FUN_INTERFACE_BATCHDISTS | FUN_INTERFACE_REJECTIONS | Intercompany Transactions > Import Errors tab, or Tasks > Correct Import Errors |
| Import Journals | GL_INTERFACE | GL_INTERFACE (STATUS) and GL_JE_ERROR_CODES | Import Errors tab of the General Accounting dashboard > Correct Journal Import Data spreadsheet |
| Load and Import Bank Statement; Import Bank Statement from a Spreadsheet | CE_STATEMENT_HEADERS_INT, CE_STATEMENT_LINES_INT | CE_STMT_IMPORT_ERRORS | Correct and reload |
| Import External Transactions to the Tax Repository | ZX_TRANSACTION, ZX_TRANSACTION_LINES, ZX_TAX_LINES_INTERFACE | ZX_IMPORT_ERRORS | Correct and reload |

Triage the rejected rows of one load request through a BI Publisher data model (sections 8 and 9). The joins follow the documented column meanings; they are not declared foreign keys.

```sql
-- Payables invoice import rejections for one load request
SELECT i.invoice_num, i.vendor_num, i.source, i.status,
       r.parent_table, r.reject_lookup_code, r.rejection_message
FROM   ap_invoices_interface i
JOIN   ap_interface_rejections r
       ON  r.parent_table = 'AP_INVOICES_INTERFACE'
       AND r.parent_id    = i.invoice_id
WHERE  i.load_request_id = :p_load_request_id;

-- AutoInvoice validation errors for one load request
SELECT l.batch_source_name, l.trx_number, ae.message_text, ae.invalid_value
FROM   ra_interface_lines_all l
JOIN   ra_interface_errors_all ae ON ae.interface_line_id = l.interface_line_id
WHERE  l.load_request_id = :p_load_request_id;

-- Purchasing document import errors for one load request
SELECT h.document_num, h.process_code, pe.table_name, pe.column_name, pe.error_message
FROM   po_headers_interface h
JOIN   po_interface_errors pe ON pe.interface_header_id = h.interface_header_id
WHERE  h.load_request_id = :p_load_request_id;
```

### 7.2 FBDI templates for P2P

Template names are the FBDI guide entries. The import process is the scheduled process named on each template page. All interface tables are in the 26D catalogs (Appendix A).

| Template | P2P step | XLSM template; UCM account | Interface tables | Import process |
|---|---|---|---|---|
| Import Suppliers | Supplier master | SupplierImportTemplate.xlsm; `prc/supplier/import` | POZ_SUPPLIERS_INT | Import Suppliers |
| Import Supplier Addresses | Supplier master | SupplierAddressImportTemplate.xlsm; `prc/supplier/import` | POZ_SUP_ADDRESSES_INT | Import Supplier Addresses |
| Import Supplier Sites | Supplier master | SupplierSiteImportTemplate.xlsm; `prc/supplier/import` | POZ_SUPPLIER_SITES_INT, POZ_SUP_THIRDPARTY_INT | Import Supplier Sites |
| Import Supplier Site Assignments | Supplier master | SupplierSiteAssignmentImportTemplate.xlsm; `prc/supplier/import` | POZ_SITE_ASSIGNMENTS_INT | Import Supplier Site Assignments |
| Import Supplier Contacts | Supplier master | SupplierContactImportTemplate.xlsm; `prc/supplier/import` | POZ_SUP_CONTACTS_INT, POZ_SUP_CONTACT_ADDRESSES_INT | Import Supplier Contacts |
| Import Supplier Business Classifications | Supplier master | SupplierBusinessClassificationImportTemplate.xlsm; `prc/supplier/import` | POZ_SUP_BUS_CLASS_INT | Import Supplier Business Classifications |
| Import Supplier Products and Services Categories | Supplier master | SupplierProductsandServicesCategoryImportTemplate.xlsm; `prc/supplier/import` | POZ_SUP_PROD_SERV_INT | Import Supplier Products and Services Categories |
| Import Supplier Attachments | Supplier master | SupplierAttachmentImportTemplate.xlsm; `prc/supplier/import` | POZ_SUP_ATTACHMENTS_INT | Import Supplier Attachments |
| Supplier Bank Account Import (Payments) | Supplier payee and bank accounts | SupplierBankAccountImportTemplate.xlsm; `fin/payables/import` | IBY_TEMP_EXT_PAYEES, IBY_TEMP_EXT_BANK_ACCTS, IBY_TEMP_PMT_INSTR_USES | Import Supplier Bank Accounts |
| Import Requisitions | Requisition | RequisitionImportTemplate.xlsm; `prc/requisition/import` | POR_REQ_HEADERS_INTERFACE_ALL, POR_REQ_LINES_INTERFACE_ALL, POR_REQ_DISTS_INTERFACE_ALL | Import Requisitions |
| Import Negotiation Lines | Sourcing (large negotiations) | PONNegotiationLinesImportTemplate.xlsm; `prc/supplierNegotiation/import` | PON_LINES_INT, PON_LINE_COST_FACTORS_INT, PON_LINE_PRICE_TIERS_INT | Import Negotiation Lines |
| Blanket Purchase Agreements Import | Agreement | POBlanketPurchaseAgreementImportTemplate.xlsm; `prc/blanketPurchaseAgreement/import` | PO_HEADERS_INTERFACE, PO_LINES_INTERFACE, PO_LINE_LOCATIONS_INTERFACE, PO_GA_ORG_ASSIGN_INTERFACE, PO_ATTR_VALUES_INTERFACE, PO_ATTR_VALUES_TLP_INTERFACE | Import Blanket Purchase Agreements (ESS guide title: Import Blanket Agreements) |
| Contract Purchase Agreements Import | Agreement | POContractPurchaseAgreementImportTemplate.xlsm; `prc/contractPurchaseAgreement/import` | PO_HEADERS_INTERFACE, PO_GA_ORG_ASSIGN_INTERFACE | Import Contract Purchase Agreements (ESS guide title: Import Contract Agreements) |
| Purchase Orders Import | Purchase order | POPurchaseOrderImportTemplate.xlsm; `prc/purchaseOrder/import` | PO_HEADERS_INTERFACE, PO_LINES_INTERFACE, PO_LINE_LOCATIONS_INTERFACE, PO_DISTRIBUTIONS_INTERFACE | Import Orders |
| Receiving Receipt Import (SCM) | Receipt, ASN, return, correction | ReceivingReceiptImportTemplate.xlsm; `scm/receivingReceipt/import` | RCV_HEADERS_INTERFACE, RCV_TRANSACTIONS_INTERFACE, INV_TRANSACTION_LOTS_INTERFACE, INV_SERIAL_NUMBERS_INTERFACE, INV_LPN_INTERFACE | Manage Receiving Transactions |
| Payables Standard Invoice Import | Supplier invoice | PayablesStandardInvoiceImportTemplate.xlsm; `fin/payables/import` | AP_INVOICES_INTERFACE, AP_INVOICE_LINES_INTERFACE | Import Payables Invoices |
| Payables Payment Request Import | Payment request | PayablesPaymentRequestImportTemplate.xlsm; `fin/payables/import` | AP_PAYMENT_REQUESTS_INT | Import Payables Payment Request |
| Cash Management Bank Statement Data Import | Bank statement (both cycles) | CashManagementBankStatementImportTemplate.xlsm; `fin/cashManagement/import` | CE_STATEMENT_HEADERS_INT, CE_STATEMENT_LINES_INT, CE_STMT_BALANCES_INT, CE_STMT_BAL_AVALBTY_INT, CE_STMT_LINE_AVALBTY_INT, CE_STMT_LINE_CHARGES_INT | Import Bank Statement from a Spreadsheet |
| Cash Management External Transactions Import | External cash transactions | CashManagementExternalTransactionsImportTemplate.xlsm; `fin/cashManagement/import` | CE_EXT_TRX_INTERFACE | Import External Transactions |
| Cash Management Bank Statement Reconciliation Data Import | Mass reconciliation | CashManagementBankStmtReconImportTemplate.xlsm; `fin/cashManagement/import` | CE_EXTERNAL_RECON_INT | External Bank Statement Reconciliation Data (Using guide: select Autoreconcile Bank Statements as the import process) |

Notes:
- Updates to purchase orders through FBDI aren't supported; Oracle recommends the Purchase Order SOAP web service for updates (7.6). FBDI doesn't support creating or updating purchasing documents with more than 10,000 distributions.
- Supplier imports take Import Options (New, Rejected or All), Report Exceptions Only and Batch ID. For long runs, split into batches of at most 20,000 records. `#NULL` in a column clears that attribute.
- Regional templates (Financials for the Americas): Payables Bank Returns Data Upload Interface (JL_BR_AP_INT_BANK_RETURNS), Payables Collection Documents Data Upload Interface (JL_BR_AP_INT_COLLECT_ALL).

### 7.3 FBDI templates for O2C

| Template | O2C step | XLSM template; UCM account | Interface tables | Import process |
|---|---|---|---|---|
| Customer Import | Customer master: parties, sites, accounts, contacts, profiles, receipt methods, bank accounts | CustomerImportTemplate.xlsm; `fin/receivables/import` | HZ_IMP_PARTIES_T, HZ_IMP_PARTYSITES_T, HZ_IMP_PARTYSITEUSES_T, HZ_IMP_LOCATIONS_T, HZ_IMP_ACCOUNTS_T, HZ_IMP_ACCTSITES_T, HZ_IMP_ACCTSITEUSES_T, HZ_IMP_ACCOUNTRELS, HZ_IMP_ACCTCONTACTS_T, HZ_IMP_CONTACTS_T, HZ_IMP_CONTACTPTS_T, HZ_IMP_CONTACTROLES, HZ_IMP_RELSHIPS_T, HZ_IMP_ROLERESP, HZ_IMP_CLASSIFICS_T, HZ_IMP_PERSONLANG, RA_CUSTOMER_PROFILES_INT_ALL, RA_CUST_PAY_METHOD_INT_ALL, RA_CUSTOMER_BANKS_INT_ALL | Import Trading Community Data in Bulk |
| Upload Customers | Customer master (simplified spreadsheet) | UploadCustomersTemplate.xlsm; `fin/receivables/import` | AR_UPD_CUSTOMERS, AR_UPD_CONTACTS, AR_UPD_REF_ACCOUNTS, AR_UPD_BANK_ACCOUNTS | Upload Customers |
| Credit Management Data Points Import | Credit review | UploadCreditDataTemplate.xlsm; `fin/receivables/import` | AR_CMGT_DATA_POINTS_INT (link target; the page label shows an older name) | Import Credit Management Data Points (Implementing Receivables names the Import Process value Import Credit Data) |
| Price List | Pricing | PriceListImportTemplate.xlsm; `scm/priceLists/import` | QP_PRICE_LISTS_INT, QP_PRICE_LIST_SETS_INT, QP_PRICE_LIST_ITEMS_INT, QP_PRICE_LIST_CHARGES_INT, QP_PL_COMP_ITEMS_INT, QP_PL_COVERED_ITEMS_INT, QP_TIER_HEADERS_INT, QP_TIER_LINES_INT, QP_MATRIX_DIMENSIONS_INT, QP_MATRIX_RULES_INT | Import Price List |
| Price Lists Batch | Pricing (many price lists) | PriceListsImportBatchTemplate.xlsm; `scm/priceLists/import` | Price List tables plus QP_RATE_PLANS_INT | Import Price Lists Batch |
| Discount Lists | Pricing | DiscountListImportTemplate.xlsm; `scm/discountLists/import` | QP_DISCOUNT_LISTS_INT, QP_DISCOUNT_LIST_SETS_INT, QP_DISCOUNT_LIST_ITEMS_INT, QP_PRICING_TERMS_INT, QP_MATRIX_DIMENSIONS_INT, QP_MATRIX_RULES_INT | Import Discount Lists |
| Cost Lists | Pricing | CostListsImportTemplate.xlsm; `scm/costLists/import` | QP_COST_LISTS_INT, QP_COST_LIST_SETS_INT, QP_COST_LIST_ITEMS_INT, QP_COST_LIST_CHARGES_INT | Import Cost Lists |
| Import Sales Orders | Sales order | SourceSalesOrderImportTemplate.xlsm; `scm/sourceSalesOrder/import` | DOO_ORDER_HEADERS_ALL_INT, DOO_ORDER_LINES_ALL_INT, DOO_ORDER_ADDRESSES_INT, DOO_ORDER_TXN_ATTRIBUTES_INT, DOO_ORDER_SALES_CREDITS_INT, DOO_ORDER_PAYMENTS_INT, DOO_ORDER_LOT_SERIALS_INT, DOO_ORDER_DOC_REFERENCES_INT, DOO_ORDER_CHARGES_INT, DOO_ORDER_CHARGE_COMPS_INT, DOO_ORDER_CHARGE_TIERS_INT, DOO_ORDER_BILLING_PLANS_INT, DOO_ORDER_MANUAL_PRICE_ADJ_INT, DOO_ORDER_HDRS_ALL_EFF_B_INT, DOO_ORDER_LINES_ALL_EFF_B_INT, DOO_ORDER_TERMS_INT, DOO_PROJECTS_INT | Import Sales Orders |
| Inventory Reservation Import | Reserve supply | InventoryReservationImportTemplate.xlsm; `scm/inventoryReservation/import` | INV_RESERVATIONS_INTERFACE | Manage Reservation Interface (ESS guide title: Manage Reservations Interface) |
| Shipment Request Import | Shipment lines from sources other than Order Management | ShipmentRequestImportTemplate.xlsm; `scm/shipmentRequest/import` | WSH_DEL_DETAILS_INTERFACE, WSH_TRANSACTIONS_HISTORY | Receive Shipment Request |
| Perform Shipping Transaction Import | Shipping transactions from WMS, 3PL or other execution systems | PerformShippingTransactionImportTemplate.xlsm; `scm/performShippingTransaction/import` | WSH_NEW_DEL_INTERFACE, WSH_DEL_DETAILS_INTERFACE, WSH_FREIGHT_COSTS_INTERFACE, INV_LPN_INTERFACE, INV_TRANSACTION_LOTS_INTERFACE, INV_SERIAL_NUMBERS_INTERFACE | Perform Shipping Transactions |
| Interfaced Pick Transaction Import | Pick transactions from external systems | InterfacedPickTransactionsImportTemplate.xlsm; `scm/interfacedPickTransactions/import` | INV_PERFORM_PICK_TXNS_INT, INV_TRANSACTION_LOTS_INTERFACE, INV_SERIAL_NUMBERS_INTERFACE | Perform Pick Transactions from External Systems |
| AutoInvoice Import | Invoices, credit memos, debit memos | AutoInvoiceImportTemplate.xlsm; `fin/autoInvoice/import` | RA_INTERFACE_LINES_ALL, RA_INTERFACE_DISTRIBUTIONS_ALL, RA_INTERFACE_SALESCREDITS_ALL, AR_INTERFACE_CONTS_ALL | Import AutoInvoice |
| Receivables Standard Receipt Import | Lockbox receipts | ReceivablesStandardReceiptImportTemplate.xlsm; `fin/receivablesStandardReceipt/import` | AR_PAYMENTS_INTERFACE_ALL | Process Receipts Through Lockbox |
| Import Legacy Credit Cards (Payments) | Legacy card data | IbyLegacyCreditCardImportTemplate.xlsm; `fin/payments/import` | Not listed on the template page | Import Legacy Credit Cards |
| Revenue Basis Data Import | Source documents for Revenue Management (pipe-separated file) | RevenueDataImportTemplate.xlsm; `fin/revenueManagement/import` | VRM_SOURCE_DOCUMENTS, VRM_SOURCE_DOC_LINES, VRM_SOURCE_DOC_SUB_LINES, VRM_SOURCE_DOC_ADDL_SUBLINES | Import Revenue Basis Data |
| Billing Data Import | Billing data for Revenue Management (pipe-separated file) | BillingDataImportTemplate.xlsm; `fin/revenueManagement/import` | VRM_BILLING_LINE_DETAILS | Import Billing Data |

Regional template: Receivables Bank Returns Data Upload Interface (JL_BR_AR_RET_INTERFACE_ALL; Import Bank Returns for Customer Payments).

#### Templates shared by both cycles

| Template | Use | XLSM template; UCM account | Interface tables | Import process |
|---|---|---|---|---|
| Item (Product Lifecycle Management) | Items for requisitions, POs and sales orders | ItemImportTemplate.xlsm; `scm/item/import` | EGP_SYSTEM_ITEMS_INTERFACE, EGP_ITEM_REVISIONS_INTERFACE, EGP_ITEM_CATEGORIES_INTERFACE, EGP_ITEM_RELATIONSHIPS_INTF, EGP_TRADING_PARTNER_ITEMS_INTF, EGO_ITEM_ASSOCIATIONS_INTF, EGO_ITEM_INTF_EFF_B, EGO_ITEM_INTF_EFF_TL, EGO_ITEM_REVISION_INTF_EFF_B, EGO_ITEM_SUPPLIER_INTF_EFF_B, EGO_STYLE_VARIANT_ATTR_VS_INTF | Item Import Job |
| Inventory Transaction Import | Inventory movements | InventoryTransactionImportTemplate.xlsm; `scm/inventoryTransaction/import` | INV_TRANSACTIONS_INTERFACE, INV_TRANSACTION_LOTS_INTERFACE, INV_SERIAL_NUMBERS_INTERFACE, CST_I_INCOMING_TXN_COSTS | Create Inventory Transactions (ESS guide: Manage Inventory Transactions processes the interface rows) |
| Standard Costs | Item cost for valuation and COGS | StandardCostImportTemplate.xlsm; `scm/standardCost/import` | CST_INTERFACE_STD_COST_HEADERS, CST_INTERFACE_STD_COST_DETAILS | Define Standard Costs |
| Intercompany Transaction Import | Intercompany charges | IntercompanyTransactionImportTemplate.xlsm; `fin/intercompany/import` | FUN_INTERFACE_CONTROLS, FUN_INTERFACE_BATCHES, FUN_INTERFACE_HEADERS, FUN_INTERFACE_DIST_LINES, FUN_INTERFACE_BATCHDISTS | Import Intercompany Transactions |
| Journal Import | Journals from external systems | JournalImportTemplate.xlsm; `fin/generalLedger/import` | GL_INTERFACE | Import Journals |
| Mapping Set Values Import | Subledger accounting mapping sets | XlaMappingsImportTemplate.xlsm; `fin/fusionAccountingHub/import` | XLA_MAPPING_SET_VALUES_INT | Load Interface File for Import |
| Tax Entry Repository Data Upload Interface | External taxable transactions | Template on the FBDI page; `fin/tax/import` | ZX_TRANSACTION, ZX_TRANSACTION_LINES, ZX_ITEM_DISTRIBUTIONS, ZX_TAX_LINES_INTERFACE, ZX_TAX_DISTS_INTERFACE, ZX_TAX_ALLOCS_INTERFACE | Import External Transactions to the Tax Repository |

### 7.4 ERP Integration Service

The ERP Integration Service automates bulk inbound and outbound flows: file upload to UCM, ESS job submission, status tracking, callbacks and notifications. It supersedes the Financial Utilities Service, which is deprecated and shouldn't be used by new customers.

| Interface | Endpoint |
|---|---|
| SOAP | `https://<POD_HOST>/fscmService/ErpIntegrationService?WSDL`; QName `{http://xmlns.oracle.com/apps/financials/commonModules/shared/model/erpIntegrationService/}ErpIntegrationService` |
| REST actions | `POST /fscmRestApi/resources/11.13.18.05/erpintegrations` with `OperationName` in the body |
| REST queries | `GET /fscmRestApi/resources/11.13.18.05/erpintegrations?finder=<FINDER>;<VARIABLE>=<VALUE>` |
| REST item | `GET /fscmRestApi/resources/11.13.18.05/erpintegrations/{OperationName}` |

| SOAP operation | REST form (documented) | Purpose |
|---|---|---|
| importBulkData | POST, `OperationName=importBulkData` | Upload a base64 zip to a UCM account, run Load Interface File for Import and the import job. `jobOptions` example: `InterfaceDetails=<ID>,ImportOption=Y,PurgeOption=Y,ExtractFileType=ALL`. |
| uploadFileToUcm | POST, `OperationName=uploadFileToUCM` | Upload only; returns the document ID. |
| submitESSJobRequest | POST, `OperationName=submitESSJobRequest` with `JobPackageName`, `JobDefName`, `ESSParameters` | Run any ESS job. Parameters in job order, `#NULL` for empty ones. Returns the request ID. |
| exportBulkData | POST, `OperationName=exportBulkData` | Run a job, then zip its output and log to UCM. For reports and outbound flows. |
| submitJobWithOutput | Not documented | Submit with callback. The Oracle Integration adapter guide says it will be deprecated; use exportBulkData. |
| getESSJobStatus | finder `ESSJobStatusRF;requestId=<ID>` | Status in `RequestStatus`, for example SUCCEEDED. |
| getESSExecutionDetails | finder `ESSExecutionDetailsRF;requestId=<ID>` | JSON tree of the job and its child jobs with statuses. |
| downloadESSJobExecutionDetails | finder `ESSJobExecutionDetailsRF;requestId=<ID>,fileType=<FILE_TYPE>` | Log and output files as a zip; file type LOG, OUT or ALL. |
| getDocumentIdsForFilePrefix, getDocumentForDocumentId | finders `DocumentIdsByFilePrefixRF`, `DocumentRF` | Find and download UCM files. |
| appendFileComment, confirmExtractConsumption | Not documented | Tag a file with a comment (prefix searches can exclude tagged files); confirm an extract was downloaded. |
| updateInterfaceData | Not documented | Upload corrected interface data for an import process and load request ID. |
| extractAndPurge | Not documented | Upload load and import logs to UCM and purge the interface tables. |
| loadAndImportData, downloadExportOutput | Not documented | Older operations; the guide points to importBulkData and downloadESSJobExecutionDetails. |

A complete REST example for a Payables invoice import (request body, submission, status polling and log download) is in 6.5.10.

Callbacks and job status:
- `NotificationCode`: first digit 1 = email, 2 = bell, 3 = both; second digit 0 = always, 1 = on success, 2 = on failure; `#NULL` = none. It applies to loadAndImportData, importBulkData, exportBulkData and extractAndPurge.
- `CallbackURL`: a web service you implement; Fusion sends it the job status when the job ends. `#NULL` means no callback.
- Oracle Integration: the ERP Cloud Adapter action Import Bulk Data into Oracle ERP Cloud with Enable Callback raises the ErpImportBulkDataEvent event, and a separate callback integration subscribes to it. The Financials event list also has ERP Integration Inbound and ERP Integration Outbound (7.8).
- ESS REST API (REST API for Common Features): `POST /ess/rest/scheduler/v1/requests` (body `jobDefinitionId`, `requestParameters`, optional `callbackSubscription` with `callbackUrlPrefix` and `callbackResourcePath`), `GET /ess/rest/scheduler/v1/requests/{requestId}`, `POST /ess/rest/scheduler/v1/requests/{requestId}/cancel`, `POST /ess/rest/scheduler/v1/requests/{requestId}/subscribe`.
- ERP ICS Integration Service (`ErpIcsIntegrationService`, operation getInboundProcesses) lists the FBDI processes registered with the FBDI framework.

### 7.5 ADFdi spreadsheets

ADF Desktop Integration workbooks, their installation, usage rules and the mass-entry workbooks (for example Create Invoice in Spreadsheet and the procurement spreadsheet actions) are described in 5.4. Next to FBDI they are the correction layer; the table lists the correction workbooks for the imports in 7.1 to 7.3.

| Workbook or spreadsheet task | Area | Use |
|---|---|---|
| Correct Import Errors | Payables | Fix rows rejected by Import Payables Invoices, then Upload and Import |
| Manage AutoInvoice Lines | Receivables | Change or delete AutoInvoice interface rows, then Save and Run AutoInvoice |
| Correct Customer Data | Receivables | Fix Upload Customers errors |
| Review Receipts Interface | Receiving | Review receiving interface errors |
| Correct Journal Import Data; journal workbooks | General Ledger | Fix journal import errors; enter journals in workbooks |
| Correct Import Errors (IntercompanyCorrections) | Intercompany | Fix intercompany import errors |
| Correct Contract Document Errors in Spreadsheet | Revenue Management | Fix source data validation errors |

Workbook usage rules: 5.4.

### 7.6 SOAP web services for P2P and O2C

WSDL pattern: `https://<POD_HOST>/fscmService/<SERVICE_NAME>?WSDL`. The Service Catalog Service (getAllServiceEndpoints, getServiceEndpoint) lists endpoints. Below: guide title, WSDL service name in brackets, key operations. All are Active in 26D.

| Service [WSDL name] | Step | Key operations and use |
|---|---|---|
| Supplier [SupplierServiceV2] | Supplier master | createSupplier, updateSupplier |
| Purchase Request Service Version 1 [PurchaseRequestService] | Requisition | createRequisition, changePurchaseRequest, controlPurchaseRequest, getPurchaseRequest, populateInterfaceTable, submitImportRequisition |
| Supplier Negotiation Version 3 [NegotiationManageServiceV3] | Sourcing | initializeNegotiation |
| Purchase Order Service Version 2 [PurchaseOrderServiceV2] | Purchase order | createPurchaseOrder, changePurchaseOrder, cancelPurchaseOrder, getPurchaseOrder, acknowledgePurchaseOrder. Oracle recommends the PO SOAP service for PO updates. |
| Purchase Agreement [PurchaseAgreementService] | Agreement | cancelPurchaseAgreement, cancelChangeOrder, deleteChangeOrder |
| Update Preparer and Requester [UpdatePreparerRequesterService] | Requisition and PO maintenance | updatePreparerRequester |
| Receiving Open Interface Version 2 [ProcessorServiceV2] | Receipt | interfaceTransactions, processor (pending receiving transactions) |
| Receipt Details [ReceiptService]; Receiving Transaction Details [ReceivingTransactionService]; Inbound Shipment Details [InboundShipmentService] | Receipt | findReceipt, findTransaction, findShipment; callback services of the receiving events (7.8) |
| Receipt Advice Version 2 [FlexSupplyInboundServiceV2]; Send Receipt Advice [ReceiptAdviceService] | Receipt with WMS | processReceiptAdvice, interfaceReceiptAdvice; getReceiptAdviceDetails |
| Payables Invoice [InvoiceInterfaceService] | Supplier invoice | createInvoiceInterface, submitInvoiceImport, createB2BInvoice, getSupplierRejections |
| Payables Invoice Management [InvoiceService] | Invoice maintenance | insertSingleHold, releaseSingleHold, cancelInvoice, getInvoiceStatus, updateInvoiceInstallments |
| Customer Profile [ReceivablesCustomerProfileService] | Customer setup | createCustomerProfile, updateCustomerProfile, getActiveCustomerProfile, createReferenceAccountsForBillToSite |
| External Bank Account [ExternalBankAccountServiceV2]; External Payer [PayerDetailServiceV2] | Customer bank accounts and payer instruments | processExternalBankAccount, getExternalBankAccountDetails; processPayerBankAccount, processPayerPaymentCard, findPayer |
| Receivables Credit Checking [CreditCheckingService] | Credit check | creditChecking: credit authorizations and available credit |
| Order Promising [OrderPromisingServiceV2]; Inventory Availability Version 2 [OnhandQuantityServiceV2] | Order capture | checkAvailability, scheduleSalesOrders, autoSchedule; query |
| Order Information Service [OrderInformationService] | Order | ChangeOrderAllowed, ChangeOrderAttributeAllowed, GetCrossReferencedData (enrichment after Sales Order Notification) |
| Order Fulfillment Response Service [OrderFulfillmentResponseService] | Fulfillment | processAcknowledgement, processFulfillmentResponse from external fulfillment systems |
| Outbound Fulfillment Request; Sales Order Business Event; Receive Fulfillment Task Response Service; Release Paused Task Service | Orchestration (process services) | WSDLs to implement (processFulfillmentRequest, pushPayload) or to call (process) |
| Pick Wave [PickWaveService]; Pick Slip [PickConfirmService] | Pick | processCreatePickBatch, processReleasePickBatch; confirmPick |
| Material Shipment [ShipmentService]; Material Shipment Line [ShipmentLineService]; Shipment Request Version 2 [ShipmentRequestServiceV2] | Ship | processShipmentAction, createAndConfirm; getShipmentLineData; processShipmentRequestOrder |
| Manifest Shipment [ShipmentServiceV2] | Ship | getShipmentAdviceData, getAdvancedShipmentNoticeData, getManifestRequestData |
| Transaction Manager Version 2 [TransactionManagerServiceV2] | Inventory | processInventoryTransaction, insertAndProcessInterfaceRows |
| Receivables Invoice [RecInvoiceService] | Billing | createSimpleInvoice, createInterfaceLine, getRevenueProjection |
| Receivables Credit Memo [CreditMemoService]; Receivables Debit Memo [DebitMemoService] | Billing adjustment | createCreditMemo, createApplyOnAccountCreditMemo, createOnAccountCreditMemoRefund; createDebitMemo |
| Receivables Adjustment [AdjustmentService]; Receivables Chargeback [ChargebackService] | Balance change | createAdjustment, createReverseAdjustment; createChargeback |
| Receivables Standard Receipt [StandardReceiptService]; Receivables Standard Receipt and Receipt Application [CreateAndApplyReceiptService]; Receivables Miscellaneous Receipt [MiscellaneousReceiptService] | Cash application | createStandardReceipt, createApplyReceipt, createUnapplyReceipt, createReverseReceipt; createAndApplyReceipt; createMiscellaneousReceipt |
| Receivables Payment Terms [TransactionPaymentTermsService] | Billing | findTransactionPaymentTerms |
| Credit Card [CreditCardServiceV2]; Transaction [TransactionDetailServiceV2]; Transaction Operation [TransactionsServiceV2] | Funds capture | getTokenizationRequest, getPaymentCardDetails; createTransactionExtension; authorizeTransactionExtension |
| Tax Calculation Service [TaxableTransactionService] | Tax, both cycles | calculateTransactionTax, calculateTransactionTaxEstimate |
| Account Combination Validation Service [AccountCombinationService] | Accounting | validateAndCreateAccounts |
| Journal [JournalImportService]; Create Intercompany Transaction [IntercompanyTransactionImportService] | GL and intercompany | importJournals; importTransactions |
| ERP Object Attachment Service [ErpObjectAttachmentService]; ERP Object Descriptive Flexfield Update Service [ErpObjectDFFUpdateService] | Any object | uploadAttachment, downloadAttachment; updateDffEntityDetails |
| Setup Data Export and Import [SetupDataExportImportService] (Common) | Setup | submitTaskCSVExport, submitTaskCSVImport |

Deprecated, not for new work: Financial Utilities Service, Purchase Order (version 1), Import Sales Orders, Price Request Service, the deprecated Receivables Standard Receipt [StandardReceiptAPIService], Collections Delinquency. SOAP calls such as Payables Invoice Management don't raise Payables business events (7.8).

### 7.7 Scheduled processes per step

Submit and monitor processes in Navigator > Tools > Scheduled Processes > Schedule New Process; many also start from work-area task panes. A process set runs several processes in a defined order. Statuses include Blocked (an incompatible process is running), Wait, Ready, Running, Paused, Hold, Succeeded, Warning, Error, Error Auto-Retry, Error Manual Recovery, Validation Failed, Canceling, Canceled, Expired and Schedule Ended (20 values in the 26D scheduled-process guides). Frequency source: [E] Oracle scheduled-process guide, [U] Oracle Using or Implementing guide, [P] common practice, verify in your pod.

#### P2P

| Process | Step | What it does | Typical frequency |
|---|---|---|---|
| Import Suppliers and the other supplier imports (7.2) | Supplier | Create or update suppliers and child objects from the supplier interface tables | Ad hoc [E] |
| Inactivate Suppliers | Supplier | Inactivates suppliers without sourcing, purchasing or invoicing activity in a period, and one-time suppliers paid at least once | First run as a single instance, then monthly, after work hours [E] |
| Import Requisitions | Requisition | Imports requisitions from other systems | Daily to quarterly, as needed [E] |
| Generate Orders | Requisition to PO | Moves approved requisitions to the procurement BU; creates POs for touchless lines, else routes them to the buyer | At least daily [E] |
| Create Purchasing Documents | Sourcing award | Groups awarded lines into purchasing documents | Ad hoc [E] |
| Import Orders; Import Blanket Agreements; Import Contract Agreements | Purchasing | Import POs and agreements loaded by FBDI | At least daily [E] |
| Communicate Purchasing Document | PO dispatch | Prints PDFs or sends documents by email or fax per communication preferences | Per business needs [E] |
| Initiate Retroactive Price Update | Agreement to PO | Applies agreement price changes to POs sourced from it | At least daily [E] |
| Generate Approved Supplier List Entries | Agreement | Creates ASL entries for the items of a blanket agreement | As needed [E] |
| Purge Processed Open Interface Documents | Interface hygiene | Purges purchasing interface records in any status | As needed; purge Accepted and Rejected [E] |
| Manage Receiving Transactions | Receipt | Processes the receiving open interface: receipts, put away, returns, corrections, ASNs | After each load; hourly if scheduled, every 10 minutes for high volume [E] |
| Confirm Receipts | Receipt | Notifies requesters or buyers about past-due purchase orders and transfer orders | Daily; one run processes 900 transactions, so schedule several runs for high volume [E] |
| Send Pay on Receipt | Receipt to invoice | Creates standard unapproved invoices from receipts for pay-on-receipt orders or sites | After receiving; let corrections and returns finish first [E] |
| Transfer Transactions from Receiving to Costing | Receipt accounting | Sends receiving transactions to receipt accounting | Several times a day, up to hourly [E] |
| Create Receipt Accounting Distributions | Receipt accounting | Creates distributions for receipt accruals, deliveries, landed costs and payables transactions for receipts | At least daily [E] |
| Transfer Costs to Cost Management | Invoice to costing | Sends payables invoice data to Cost Management | Daily or more [E] |
| Match Receipt Accruals; Clear Receipt Accrual Balances | Accrual reconciliation | Matches invoices to receipt accruals; clears balances with accrual clearing rules | At least daily [E] |
| Create Uninvoiced Receipt Accrual | Period end | Accrues uninvoiced receipts of POs that accrue at period end | At least once per period, after the AP period closes [E] |
| Purge Receiving Interface | Interface hygiene | Purges error, or error and pending, rows from RCV_TRANSACTIONS_INTERFACE and RCV_HEADERS_INTERFACE | Once or twice a day with REST, SOAP or FBDI; weekly with UI only; run manually above 10,000 interface lines [E] |
| Import Payables Invoices | Invoice | Creates invoices from the AP interface tables; rejection report | Each load [P] |
| Import Payables Payment Request | Payment request | Creates payment requests from AP_PAYMENT_REQUESTS_INT | Each load [P] |
| Validate Payables Invoices | Invoice | Generates distributions, calculates tax, checks tolerances, applies holds | Recurring schedule with AutoIncrement [U] |
| Initiate Invoice Approval Workflow | Approval | Starts approval for ready invoices | Regular schedule [U] |
| Submit Payment Process Request (templates) | Payment | Selects installments and builds payments | Templates can run on a schedule [U] |
| Create Electronic Payment Files; Create Printed Payment Files | Payment | Group payments into files; format and transmit or print | Scheduled when files aren't created immediately [U] |
| Create Positive Pay File; Send Separate Remittance Advice | Payment | Positive pay file for checks; remittance advice to payees | Manual or automatic per payment process profile [U] |
| Update Matured Bills Payable Status; Apply Missing Conversion Rates | Period close | Issued to Negotiable for matured bills payable; rates for invoices with a No rate hold | Period close [U] |
| Create Mass Additions | AP to Assets | Transfers invoice lines to Assets | Period close checklist [U] |
| Payables Unaccounted Transactions and Sweep; Payables Period Close Exceptions report | Period close | Lists unaccounted items and moves them to the next period; lists exceptions that block close | Period close [U] |
| Prepare Payables to General Ledger Reconciliation; Payables Trial Balance report; Payables Open Items Revaluation report; Payables Cash Requirement report | Reconciliation, reporting | Reconciliation extract and reports; cash requirement before a payment run | Period close; each payment run [U] |
| Load and Import Bank Statement; Autoreconcile Bank Statements (submitted as Autoreconciliation from the Bank Statements and Reconciliation work area, 2.11 and 3.12) | Cash Management | Loads statement files from `fin/cashManagement/import`; reconciles with matching rule sets | Per statement file [P] |

#### O2C

| Process | Step | What it does | Typical frequency |
|---|---|---|---|
| Import Trading Community Data in Bulk; Upload Customers | Customer | Import customer data from the 7.3 interface tables | Per batch [P] |
| Import Credit Management Data Points (Import Process value Import Credit Data); Periodic Credit Review | Credit | Loads credit data; reviews credit of selected customers | Per batch; scheduled reviews [U] |
| Import Price Lists Batch; Import Discount Lists; Import Cost Lists | Pricing | Import pricing data from interface tables | Scheduled recommended [E] |
| Delete Pricing Data from Interface Tables | Interface hygiene | Deletes pricing interface data | After each import [E] |
| Import Sales Orders | Order | Imports source orders into Order Management | Depends on the source system [E] |
| Delete Orders from Interface Tables | Interface hygiene | Deletes order interface data | Every time you import [E] |
| Process Responses from Order Fulfillment | Fulfillment | Processes responses from fulfillment systems | Predefined daily runs for failed shipment and invoice records since 24B [E] |
| Recover Errors; Release Pause Tasks | Exceptions | Fix fulfillment and system errors across many orders; release pause tasks | As required [E] |
| Update or Close Sales Orders | Order close | Closes orders and lines that stay open | At least daily [E] |
| Schedule Pick Wave | Pick | Creates pick waves with pick wave release rules | As required [E] |
| Create Shipments; Pack Shipments; Confirm Shipments; Close Shipments | Ship | Background shipment creation, packing, ship confirm and close | As required [E] |
| Ship Confirm Documents | Ship | Job set for the bill of lading and packing slip | Automatic at ship confirm [E] |
| Manage Shipment Interface; Send Shipment Advice | Ship to OM and Inventory | Interfaces shipped lines to the source system and Inventory; publishes Shipment Advice events | Automatic on close, or scheduled when deferred [E] |
| Generate Shipment Request; Receive Shipment Request; Perform Shipping Transactions; Purge Shipping Interface | WMS and 3PL | Outbound shipment request event; inbound shipment request and shipping transaction interfaces; purge | As required [E] |
| Send Receipt Confirmation | Returns (RMA) | Sends RMA receipts to Order Management | Hourly; every 10 minutes for high volume [E] |
| Manage Inventory Transactions; Transfer Transactions from Inventory to Costing | Inventory to costing | Processes inventory interface rows; sends inventory transactions to Cost Management | Every 30 to 60 minutes [E] |
| Import Revenue Lines; Create Cost Accounting Distributions | COGS | Brings sales order revenue recognition events to costing; creates deferred and recognized COGS distributions | Daily or more [E] |
| Generate Recurring Billing Data | Billing | Generates invoice lines for active bill plans; Import AutoInvoice follows | Per billing cycle [P] |
| Import AutoInvoice | Billing | Validates interface lines and creates invoices, credit memos and debit memos | Per batch [P] |
| Purge AutoInvoice Interface Data | Interface hygiene | Purges processed AutoInvoice lines | Automatic after AutoInvoice when the Purge interface tables system option is on [U] |
| Print Receivables Transactions; Create Balance Forward Bill; Create Customer Statements; Create Late Charges | Billing and dunning | Print runs, balance forward bills, statements, late charges | Per billing cycle [P] |
| Recognize Revenue | Revenue | Generates revenue distributions from revenue scheduling rules | Per period or more often [P] |
| Process Receipts Through Lockbox | Cash application | Imports and applies lockbox receipts; one business unit per run | Per transmission [U] |
| Apply Receipts Using AutoMatch | Cash application | Applies receipts by remittance references | After receipt creation [P] |
| Create Automatic Receipts; Create Automatic Remittances; Clear Receipts Automatically; Automatic Receipts Reversal | Automatic receipts | Create, remit, clear and reverse automatic receipts; remittance also processes card refunds | Per cycle [P] |
| Create Automatic Receipt Write-offs | Cash application | Writes off overpayment amounts by amount or percentage | Per cycle [P] |
| Refresh Receivables Transactions for Customer Account Summaries; Collections Delinquency Management; Collections Scoring and Strategy Assignment; Update Collections Summary Data; Initialize and Load Collections Metrics; Incremental Load Collections Metrics | Collections | Refresh delinquencies, scores, strategies and the Collections work area; run in the documented order | Daily [P] |
| Strategy Management; Send Dunning Letters | Collections | Updates strategy task statuses; sends dunning letters | Daily [P] |
| Extract Sales Orders for Revenue Management | Revenue Management | Sends orders, returns, revisions and fulfillment to Revenue Management | Once a day, one to two hours before day end [E] |
| Extract Revenue Basis Data from Oracle Fusion Applications; Import Billing Data from Oracle Fusion Receivables | Revenue Management | Import Receivables transactions and billing into Revenue Management | Periodic [U] |
| Validate Customer Contract Source Data; Identify Customer Contracts | Revenue Management | Validate imported source data (fix errors in the Correct Contract Document Errors spreadsheet); create or revise contracts, performance obligations and satisfaction events | After each revenue basis import, in this order [P] |
| Create Receivables Accounting; Prepare Receivables to General Ledger Reconciliation; Receivables Aging by General Ledger Account | Accounting and close | Accounting; reconciliation extract; aging by account | Period close [U] |
| Sweep Subledger Transactions to Another Period | Period close | Moves invalid Receivables or Revenue Management transactions out of a Close Pending period | Period close [U] |

#### Shared accounting and close

| Process | What it does | Typical frequency |
|---|---|---|
| Create Accounting | Creates subledger journals for a subledger application; can submit Transfer to GL and posting | Recurring schedule; End Date increments [U] |
| Post Subledger Journal Entries | Transfers and posts subledger journals created earlier | As needed [U] |
| Create Accrual Reversal Accounting | Completes and transfers accrual reversal journals, for example uninvoiced receipt accruals | Start of the next period [P] |
| Create Multiperiod Accounting | Multiperiod (deferred) accounting | Per period [P] |
| Import Journals; AutoPost Journals | Import GL_INTERFACE; post by AutoPost criteria sets | AutoPost right after Import Journals [U] |
| Revalue Balances | Revalues foreign currency balances | Period end [U] |
| Transfer Intercompany Transactions to General Ledger, to Receivables, to Payables | Move approved intercompany transactions | After approval [U] |
| Validate and Update Cost Accounting Periods | Cost period validations and close | Weekly and at period end [E] |

### 7.8 Business events and outbound integration

A public business event signals a business occurrence and carries a payload. Subscribers use the Oracle ERP Cloud Adapter in Oracle Integration (OIC) and call a REST or SOAP callback service for details. Enable each event that isn't on by default.

| Area | Events | Enable by | Callback or payload |
|---|---|---|---|
| Payables | Payables Invoice Created, Payables Invoice Approved, Payables Invoice Canceled, Payables Invoice Validated, Invoice Hold Applied, Invoice Hold Released, Payables Payment Created, Payables Payment Voided | Profile option AP: Enable Business Events, site level | Raised from UI and REST only, not from Import Payables Invoices or SOAP |
| Payments | Payment File Created | Profile option IBY: Enable Business Events, site level | Raised when a payment file completes |
| Procurement | Purchase Order Event (created, changed, finally closed, reopened), Supplier Created Event, Supplier Updated Event, Supplier Negotiation Invitation Event | Purchase Order Event is enabled by default | PurchaseOrderService getPurchaseOrder (SOAP, 7.6); no callback service listed for the supplier and negotiation events |
| Receiving | Create Receiving Receipt Event, Create Deliver Transaction Event, Create Return Transaction Event, Create Correction Transaction Event, ASN Creation Event, ASN Cancellation Event, Create Inbound ASN, Cancel Inbound ASN, Outbound Receipt Advice, Receipt Advice Event Notification | Adapter subscription | ReceiptService, ReceivingTransactionService, InboundShipmentService, ReceiptAdviceService |
| Order Management | Sales Order Notification, Order Status Updated, Sales Order Trade Compliance Screening, Sales Order Transportation Planning | Setup and Maintenance > Manage Business Event Trigger Points, for example Fulfillment Line Status Update | DocumentService getSalesOrderNotificationDetails; EventEnrichmentService getEnrichmentDetails; OrderFulfillmentRequestService getOrderFulfillmentRequestDetails. A trigger point can instead publish to a connector set up on Manage Connector Details |
| Shipping and inventory | Shipment Advice Event, Advanced Shipment Notice Event, Outbound Shipment Request, Shipment Request Generate Event, Backorder Line Event, Pick Confirm Event, Manifest Request Event, Trade Screening Request Event, Transfer Price Published Event, Standard Cost Published Event | Adapter subscription; several are published by scheduled processes (7.7) | ShipmentService, ShipmentLineService |
| Receivables | Receivables Invoice Completed, Receivables Invoice Incompleted, Receivables Invoice Paid, Receivables Credit Memo Completed, Receivables Credit Memo Incompleted, Receivables Credit Memo Applied, Receivables Autoinvoice Completed, Receivables Lockbox Batch Completed, Standard Receipt Created, Standard Receipt Applied, Standard Receipt Unapplied, Standard Receipt Reversed, Standard Receipt Deleted, Credit Case Folder Created, Credit Case Folder Refresh Requested | ERP Business Events REST API | Credit Case Folder Closure is also published; one adapter guide version lists it as enabled by default (verify in your pod) |
| Advanced Collections | Strategy Closed, Strategy External Task Opened | Feature Automatically Initiate or Fulfill Collections Tasks in Third Party Systems | External collections task systems |
| Revenue Management | Revenue Contract Batch Created (RevenueContractBatchCreated), raised by Identify Customer Contracts | Feature Generate Public Events on Revenue Contract Batch Created (Using Revenue Management); the adapter guide lists the ERP Business Events REST API | REST Revenue Contracts; payload Request ID, Job Name, Business Context (Contract Creation) |
| General Ledger and common | Accounting Period Opened, Accounting Period Closed, Accounting Period Reopened, Journal Batch Approved, Journal Batch Posting Completed; ERP Integration Inbound, ERP Integration Outbound | ERP Business Events REST API; ERP Integrations REST API | Bulk import and export completion (7.4) |

Enable a Financials event through REST:
- `GET /fscmRestApi/resources/11.13.18.05/erpBusinessEvents` lists events with `BusinessEventCode`, `BusinessEventIdentifier` and `EnabledFlag`.
- `PATCH /fscmRestApi/resources/11.13.18.05/erpBusinessEvents/{ErpBusinessEventId}` with body `{"EnabledFlag": true}`.

ERP Cloud Adapter facts that shape designs:
- Trigger (event) connections must use the Username Password Token policy; an OAuth trigger connection can't receive Fusion events.
- Uploads to UCM of up to 1 GB are possible, but unzip or virus scan can still fail on Fusion size limits. Downloads from UCM aren't supported.
- The adapter can't run SQL; query through a BI Publisher report (section 8).
- Custom business events can be defined in ERP Cloud and subscribed to.
- Outbound bulk data: exportBulkData for BI Publisher jobs with callback (7.4) and BICC extracts (section 8). The Business Objects guides (bo_fin, bo_proc, bo_scm) describe read-optimized business views for extraction, for example payablesInvoiceTransactionsExtract; they document data, not events.

### 7.9 Decision guide

| Need | Use | Why and limits |
|---|---|---|
| One record, entered or fixed by a person | UI (section 5) | Full validation, approvals and attachments |
| Tens to a few thousand rows by a business user | ADFdi workbook where one exists (5.4; correction workbooks 7.5) | Interactive validation and row status; needs the Excel add-in |
| Conversion or recurring high-volume load | FBDI (7.1 to 7.3) | Built for large volumes; asynchronous; errors kept in interface tables; no PO updates; 10,000-distribution limit per purchasing document |
| Automate FBDI or run any ESS job from outside | erpintegrations REST or ErpIntegrationService (7.4) | One call for upload, load and import; callback or event at completion |
| Create, read or update one document in real time | REST (section 6) | Raises Payables events; first choice when a resource exists |
| Operation without a suitable REST resource, or where Oracle recommends SOAP | SOAP (7.6) | Example: PO changes with PurchaseOrderServiceV2; check the deprecation status first |
| React to a change in Fusion | Business events with OIC (7.8) | A signal per occurrence; enrich through the callback service; enable the event first |
| Outbound bulk data or reports | exportBulkData, BI Publisher, BICC (section 8) | Don't page through transactional REST resources for bulk extraction |
| Recurring processing inside Fusion | Scheduled processes and process sets (7.7) | Respect incompatibilities and recommended frequencies |
| Actions by an AI agent (sections 10, 11) | REST for reads and single writes; erpintegrations for bulk, with human approval of each write | Same security and audit as the human channels (section 12) |
