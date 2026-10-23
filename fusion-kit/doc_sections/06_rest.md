## 6. REST APIs for P2P and O2C

REST is the interactive integration layer of Fusion: one record or a small set of records per call, synchronous validation, and custom actions that run business actions such as invoice validation or hold release. Do not assume UI behaviour: Oracle notes that cascade defaulting from the Create or Edit Invoice pages does not happen on a REST update of a Payables invoice ([Points to Consider](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Points_to_Consider.html)). Use FBDI and scheduled processes (section 7) for volume, OTBI and BICC (section 8) for reporting, and REST for lookups, single transactions, status checks and agent tools (sections 10 and 11). This section is built from the 26D *All REST Endpoints* lists of the Financials (farfa), Procurement (fapra), SCM (fasrp), Common Features (farca) and CX Sales and Fusion Service (faaps) guides. The 26D SCM library links to the SCM REST guide published as 26C; SCM rows and examples use that edition. Appendix C lists every root resource cited here.

### 6.1 Conventions

Table 6-1. Rules that apply to every resource in this section.

| Topic | Rule in 26D | Source |
|---|---|---|
| Base URL | `https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/<resource>` for Financials, Procurement and SCM. CX resources such as `accounts` and `hubOrganizations` use `https://<POD_HOST>/crmRestApi/resources/11.13.18.05/<resource>`. A path without a version returns 404; Oracle recommends 11.13.18.05 (some Oracle examples use `latest`). | [URL Paths](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/URL_Paths_for_REST_Services.html) |
| Spectra (v1) resources | `https://<POD_HOST>/api/boss/data/objects/<module>/v1/<service>`; query with `$filter`, `$limit`, `$offset`, `$sortBy`, `$fields`; every Spectra resource needs an OAuth token from OCI IAM. ERP Document IO and ERP Data Integrations use a separate `/api/erp/integrations/resources/v1/...` pattern (see 6.2 and 6.4). | [Quick Start](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Quick_Start.html), [Manage Collections](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Collections.html) |
| Authentication | OWSM policy accepts Basic over SSL, SAML 2.0 bearer, JWT (passes the user name only) and OAuth 2.0 tokens from the OCI IAM identity domain. Fusion paths accept the Authorization Code, Authorization Code with PKCE and JWT User Assertion grants; Client Credentials works only for Spectra `/api/...` resources. | [Quick Start](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Quick_Start.html), [Configure OAuth](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/configure_oauth.html), [JWT](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Use_JWT_Token_for_Authorization.html) |
| Media types | POST, PATCH: `Content-Type: application/vnd.oracle.adf.resourceitem+json` (or `application/json`). Custom action: `application/vnd.oracle.adf.action+json`, result `application/vnd.oracle.adf.actionresult+json`. Batch: `application/vnd.oracle.adf.batch+json`. Send `Accept: application/json`. | [Media Types](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Media_Types.html) |
| Framework version | Header `REST-Framework-Version: <1-9>`. Without it the server uses the API default (version 1 unless the API declares another); `GET https://<POD_HOST>/fscmRestApi/resources/` shows `defaultFrameworkVersion` and `allowedFrameworkVersions`. Versions are not backward compatible: 2 RowMatch `q` with child filters and UPPER; 3 nested children returned as paged collections; 4 structured errors (`o:errorCode`, `o:errorPath`); 5 typed custom-method results, some dependent LOVs become roots; 6 item metadata in `@context`; 7 row-level LOVs hidden; 8 CLOB as plain text, multi-select values as arrays, encoded keys; 9 high-precision numbers as strings, 404 for disabled accessors, backslash escape in LIKE. | [Set the REST Framework Version](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Setting_the_REST_Framework_Version.html) |
| Child resources and keys | `/<root>/{key}/child/<child>/{key}`. A key can be a primary, alternate or hashed composite key; take it from the `self` link instead of building it. For composite keys (invoice lines, installments) query the child collection with `q` on the key columns. Never send both a generated ID and its user key (for example `InvoiceId` and `InvoiceNumber`) in one payload. | [HTTP Methods](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Resource_Methods.html), [Points to Consider](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Points_to_Consider.html), [Quick Start](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Quick_Start.html) |
| Custom actions | `POST /<root>/{key}/action/<name>` (item level) or `POST /<root>/action/<name>` (collection level, marked (C) in 6.2 to 6.4) with action+json. When the URL names the action, the body holds only its parameters. | [Custom Actions](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/custom-actions.html) |
| Metadata | `GET <base>/<resource>/describe` returns attributes (type, mandatory, updatable, queryable), finders, child and LOV links and actions; `<base>/describe?metadataMode=list` or `metadataMode=minimal` covers the whole catalog (`<base>` = `https://<POD_HOST>/fscmRestApi/resources/11.13.18.05`). `Accept: application/vnd.oracle.openapi3+json` returns OpenAPI; `Accept-Language` translates labels. Filtering on an attribute with `queryable: false` returns 400. | [Access Metadata](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Use_Metadata_Catalog.html), [Manage Collections](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Collections.html) |
| List of values | LOV roots (titled *List of Values*, most ending in `LOV`): 115 in Financials, 35 in Procurement, 227 in SCM; a few more roots end in `LOV` under other titles. Row-level LOVs appear as `.../{key}/lov/<name>` links and are hidden from version 7. Use `finder` or `q` on LOV roots and `dependency=` for dependent LOVs. Cross-pillar LOV access uses the orphan privileges Get Enterprise Structures Using REST API and Get General Ledger Setups Using REST API. | [Framework Version](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Setting_the_REST_Framework_Version.html), [LOV Privileges](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/LOV_REST_API_Privileges.html), [Enterprise Structures](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Get_Enterprise_Structures_Using_REST_API.html) |
| Flexfields | DFF and GDF values are child resources: `invoiceDff`, `invoiceLineDff`, `invoiceDistributionDff`, `invoiceGdf`, `receivablesInvoiceDFF`, `standardReceiptDFF`, `invoiceHoldDff`, and `DFF` or `globalDFF` on procurement and SCM resources. The context is the attribute `__FLEX_Context`; each segment is an attribute of the child (check names with `describe`). LOV roots `FlexFndDffDescriptiveFlexfieldContexts` and `FlexFndPvsCharacterIdCharacterValues` list contexts and values. | resource pages in the endpoint lists |
| Attachments | Child `attachments` (some resources use another name, such as `batchAttachment`). Create with `DatatypeCode` FILE plus Base64 `FileContents`, TEXT plus `UploadedText`, or WEB_PAGE plus `Url`, and a `CategoryName`; download through the `FileContents` enclosure link. | [Work with Attachments](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Work_with_Attachments.html) |
| Batch | POST to the version root with batch+json and a `parts` array (Oracle's examples post to `https://<POD_HOST>/crmRestApi/resources/11.13.18.05`; for Financials, Procurement and SCM resources use the `fscmRestApi` version root, verify in your pod); each part has `id`, relative `path`, `operation` (get, create, update, replace, delete) and optional `payload`. All or nothing: one failing part fails the batch and only failing parts are returned. Some custom actions are not enabled for batch. | [Batch Actions](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Batch_Actions.html) |
| Upsert | POST with header `Upsert-Mode: true` updates the matching record or creates a new one; the payload still needs the attributes mandatory for create. | [HTTP Methods](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Resource_Methods.html) |
| Concurrency | Read the `ETag` header (inside `@context` from version 6). PATCH with `If-Match` returns 412 if the record changed; GET with `If-None-Match` returns 304 if unchanged. Singular resources only. | [ETag](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/verify_your_resource_using_the_etag_value.html) |
| Status codes | 200 OK; 201 Created with `Location`; 202 Accepted (asynchronous, poll the `Location` job); 400 validation error or non-queryable filter; 401 credentials; 403 missing role or privilege (or access from a location blocked by export rules); 404 unknown URI; 405 method not allowed; 406 or 415 wrong Accept or Content-Type; 500 server error; 503 or 504 overload or gateway timeout. From version 4 the error body has `title`, `status` and `o:errorDetails` with `detail`, `o:errorCode`, `o:errorPath`. | [Status Codes](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Status_Codes.html) |
| Privileges | Every operation checks a function privilege and data security; a 403 means the role lacks one. Examples: Purchase Orders GET needs View Purchase Order plus procurement-agent or BU data access; Suppliers needs View Supplier (GET) or Maintain Supplier (POST, PATCH); Sales Orders for Order Hub needs `FOM_SALES_ORDER_REST_GET_PRIV` (GET) or `FOM_SALES_ORDER_REST_POST_PRIV` (POST), and applyHold adds `FOM_APPLY_UPDATE_HOLDS_PRIV` and Manage Orchestration Order Modification; Standard Receipts has separate privileges for POST and for GET or DELETE. Procurement REST Service Duty (`ORA_PO_PROCUREMENT_REST_SERVICE_DUTY`) is for application-to-application integration only and sees all data. See section 12. | [Procurement Privileges](https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/Roles_and_Privileges.html), [SCM Privileges](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/Roles_and_Privileges.html), [Standard Receipts](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Get_Started_Standard_Receipts.html) |
| Opt-in features | Some resources and attributes work only after the related feature is opted in; the `features` resource returns each feature's `EnabledFlag`. | [Quick Start](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Quick_Start.html) |

Table 6-2. Query parameters (collection GET unless noted).

| Parameter | Syntax | Notes |
|---|---|---|
| `q` | `q=Supplier='<SUPPLIER>' and StatusCode='OPEN'` | Version 2 and later: `=`, `<>`, `<`, `>`, `LIKE` with `%`, `IN`, `BETWEEN`, `IS NULL`, `UPPER()`, `and`, `or`; child filters such as `invoiceHoldDff.approvedBy='Business'` or `lines.StatusCode='AWAIT_SHIP'`. Version 1 uses semicolon query-by-example (`q=a=1;b=2`). URL-encode spaces and quotes. |
| `finder` | `finder=<Finder>;<var>=<value>,<var2>=<value2>` | Predefined where clause; finder names and variables are on each *Get all* page, for example `PrimaryKey`, `findByOrderNumber`, `invoiceSearch`, `ESSJobStatusRF`. |
| `fields` | `fields=InvoiceNumber,InvoiceAmount;invoiceLines:LineNumber,LineAmount;invoiceLines.invoiceDistributions:DistributionAmount` | Returns only the listed attributes and children (item and collection). If combined with `expand`, only `fields` is applied. |
| `expand` | `expand=lines`, `expand=all`, `expand=invoiceLines.invoiceDistributions` | Includes children; from version 3 they come back as paged collections with `hasMore`. |
| `onlyData` | `onlyData=true` | Drops `links`; cannot be combined with `links`. |
| `limit`, `offset` | `limit=100&offset=200` | Default page size 25; the server can lower it; `offset` is 0-based; continue while `hasMore` is true. |
| `totalResults` | `totalResults=true` | Adds the total match count. |
| `orderBy` | `orderBy=CreationDate:desc,OrderNumber` | Without it paged results are unordered; sort on a unique attribute for stable paging, or page by key (`orderBy=Id&q=Id>'last value'`). |
| `links`, `dependency` | `links=self,canonical`; `dependency=Country=BR` | Filter link relations; pass the driving value of a dependent LOV. |

Sources: [Manage Collections](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Collections.html), [HTTP Methods](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Resource_Methods.html), [Resource Types](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Resource_Types.html).

Safe defaults for scripts and AI agents: GET with `fields` or `onlyData=true`, a `limit` and a finder or key filter; treat every POST, PATCH, DELETE and action as a write that needs approval and an audit trail (sections 11 and 12).

### 6.2 P2P resource catalog

The endpoint lists (as indexed for Appendix C) contain 211 root resources in Procurement (35 titled List of Values, 3,342 operations), 313 in Financials (115 LOV, 2,407 operations), 740 in SCM (227 LOV, 12 titled Deprecated, 10,335 operations), 19 in Common Features and 575 in CX Sales and Fusion Service; the counts include roots with non-standard paths (`/api/...`, `fom`, `msp`, `priceExecution`), and roots shared by several guides are counted in each. Table 6-3 covers the P2P roots. Paths are relative to `https://<POD_HOST>`; "(C)" marks collection-level actions; action lists name item-level actions on the root unless stated.

Table 6-3. Procure-to-Pay REST resources.

| Step | Resource (exact title) | Base path | Important child resources | Custom actions (exact) | Typical use |
|---|---|---|---|---|---|
| Supplier | Suppliers | `/fscmRestApi/resources/11.13.18.05/suppliers` | addresses, sites (assignments, thirdPartyPaymentRelationships), contacts (addresses, roles), productsAndServices, businessClassifications, attachments, DFF, globalDFF | submitSpendAuthorizationRequest, submitSpendAuthorizationRequestWithSites, resubmitSpendAuthorizationRequest, markSupplierChanged, externalValidationForSupplierAttributes, addRecentSupplier, getSupplierProfileOptions, scores, signals, callExternalProviderAPI (C) | Create and maintain suppliers, sites and site assignments; finders ActiveSuppliersFinder, FindByBilltoBU, FindByRequisitionBU |
| Supplier | Supplier Registration Options; Supplier Registration Configurations | `/fscmRestApi/resources/11.13.18.05/supplierRegistrationOptions`; `/fscmRestApi/resources/11.13.18.05/supplierRegistrationConfigurations` | - | - | Read the Configure Supplier Registrations and Profile Change Request setup (GET) |
| Supplier | Supplier Registration Questionnaire Responses | `/fscmRestApi/resources/11.13.18.05/supplierRegistrationQuestionnaireResponses`; `/fscmRestApi/resources/11.13.18.05/registrationQuestionnaireResponses` | questionnaireResponseSections, questionnaireAttachments | generateQuestionnaire (C) | Registration questionnaire answers |
| Supplier | Banks, Bank Branches, Certifying Agencies, Supplier Products and Services, Supplier User Roles List of Values | `/fscmRestApi/resources/11.13.18.05/supplierRegistrationBanksLOV`; `/fscmRestApi/resources/11.13.18.05/supplierRegistrationBankBranchesLOV`; `/fscmRestApi/resources/11.13.18.05/supplierRegistrationCertifyingAgenciesLOV`; `/fscmRestApi/resources/11.13.18.05/supplierRegistrationProductsAndServicesLOV`; `/fscmRestApi/resources/11.13.18.05/supplierRegistrationRolesLOV` | - | - | Value lists for a registration front end |
| Supplier | New Supplier Notification; Supplier User Roles | `/fscmRestApi/resources/11.13.18.05/newSupplierNotification`; `/fscmRestApi/resources/11.13.18.05/supplierUserRoles` | attachments | - | Notification text for new or spend-authorized suppliers; roles granted to supplier users |
| Supplier | Supplier Qualifications; Supplier Assessments | `/fscmRestApi/resources/11.13.18.05/supplierQualifications`; `/fscmRestApi/resources/11.13.18.05/supplierAssessments` | responses, qualifications, attachments, DFF | finalizeQualification, reviseQualification, cancelQualification, recalculateScores, overrideOutcome, uptakeNewResponses; finalizeAssessment, reviseAssessment, cancelAssessment, recalculateScore | Supplier qualification and assessment |
| Supplier | Procurement Approved Supplier List Entries; Approved Supplier List Source Documents | `/fscmRestApi/resources/11.13.18.05/procurementApprovedSupplierListEntries`; `/fscmRestApi/resources/11.13.18.05/approvedSupplierListSourceDocuments` | DFF | - | Approved supplier list by item or category and ship-to organization |
| Sourcing | Supplier Negotiations | `/fscmRestApi/resources/11.13.18.05/supplierNegotiations` | lines, sections, suppliers, attachments, negotiationVersions, DFF | CreateNegotiation (C), CreateNegotiationFromTemplate (C), ValidateAndPublishNegotiation, CreateAmendment, CreateNewRound, CompleteNegotiation, plus 66 more | RFx and auction authoring and life cycle |
| Sourcing | Supplier Negotiation Responses; Supplier Negotiation Award Responses | `/fscmRestApi/resources/11.13.18.05/supplierNegotiationResponses`; `/fscmRestApi/resources/11.13.18.05/supplierNegotiationAwards` | lines, sections, attachments; responses, recommendedResponses | InitializeProcess, SubmitProcess, DisqualifyResponse (C), OverrideScore; ApplyRecommendedAward, FinalizeAward, SubmitAwardForApproval, ReopenAward, ShareAwardDecision | Responses, scoring and award |
| Sourcing | Supplier Negotiation Purchasing Documents | `/fscmRestApi/resources/11.13.18.05/supplierNegotiationPurchasingDocuments` | purchasingDocuments, lineAllocationsSummary | CreatePurchasingDocuments, SubmitPurchasingDocuments, CancelPurchasingDocumentCreation | Create purchase orders or agreements from an award |
| Requisition | Shopping Search | `/fscmRestApi/resources/11.13.18.05/shoppingSearches` | resultItems, resultPunchoutCatalogs, brandFilters | - | Catalog search for requesters |
| Requisition | Purchase Requisitions | `/fscmRestApi/resources/11.13.18.05/purchaseRequisitions` | lines (distributions, informationTemplates), attachments, DFF, summaryAttributes | submitRequisition, cancel, withdraw, checkFunds, calculateTaxAndAccounting, createDefaultDistributions, deriveChargeAccount, copyLine, splitLine, retrieveCurrentApprovers, getApprovalWorkflowStatus, reassignBuyer (C), plus 16 more | Create, submit and track requisitions |
| Requisition | Requisition Processing Requests | `/fscmRestApi/resources/11.13.18.05/requisitionProcessingRequests` | lines | processRequest | Turn approved requisition lines into a new order or add them to an existing order; then submit the resulting draft |
| Requisition | Requisition Lifecycle Details | `/fscmRestApi/resources/11.13.18.05/requisitionLifecycleDetails` | requisitionLines, negotiations, purchaseOrderHistoryDetails, shipments, receipts, invoices | - | Requisition-to-invoice trace (GET) |
| Order | Draft Purchase Orders | `/fscmRestApi/resources/11.13.18.05/draftPurchaseOrders` | lines (schedules, distributions), attachments, DFF, globalDFFs, contractDocuments, templateUsages | submit, validateDocument, calculateTaxAndAccounting, checkFunds, applyDiscount, withdraw, cancelChangeOrder, deleteChangeOrder, processRequesterChanges, eSign, viewPDF, plus 11 more | Create a purchase order or change order not yet communicated, then submit; finder findByIntent |
| Order | Purchase Orders | `/fscmRestApi/resources/11.13.18.05/purchaseOrders` | lines (schedules, distributions), attachments, DFF, globalDFFs, contractDocuments, templateUsages | submit, cancel, close, communicate, communicateOnePurchaseOrder, acknowledge, hold, removeHold, freeze, unfreeze, reopen, renumberPO, duplicate, viewPDF, viewMasterContract, generateHighlights; schedules: firm, unfirm, close, reopen; lines: close | Read approved orders and run life-cycle actions; no POST create (use Draft Purchase Orders); finders PrimaryKey, findByIntent |
| Order | Purchase Order Schedules; Purchase Order Acknowledgments | `/fscmRestApi/resources/11.13.18.05/purchaseOrderSchedules`; `/fscmRestApi/resources/11.13.18.05/purchaseOrderAcknowledgments` | -; schedules | close, confirmWork | Schedule close and work confirmation; supplier acknowledgment (PATCH) |
| Change order | Purchasing Document Changes; Purchasing Change Order Templates; Purchasing Document Versions | `/fscmRestApi/resources/11.13.18.05/purchasingDocumentChanges`; `/fscmRestApi/resources/11.13.18.05/purchasingChangeOrderTemplates`; `/fscmRestApi/resources/11.13.18.05/purchasingDocumentHistoryDetails` | compareHeaders, compareLines, comparePOSchedules, comparePODistributions; attributes; documentVersionActions | validateChangeOrderTemplateIsUsedByADocument | Compare a change order with the approved version; change order templates; version history |
| Order | Purchase Order Lifecycle Details; Purchasing Document Import Errors | `/fscmRestApi/resources/11.13.18.05/purchaseOrderLifeCycleDetails`; `/fscmRestApi/resources/11.13.18.05/purchasingDocumentImportErrors` | schedules, shipments, receipts, invoices, workConfirmations | - | Order-to-invoice trace; errors from purchasing document import (section 7) |
| Order | Work Confirmations | `/fscmRestApi/resources/11.13.18.05/workConfirmations` | lines, attachments, documentActions | submit, cancel, withdraw | Progress on complex work orders |
| Agreement | Draft Purchase Agreements | `/fscmRestApi/resources/11.13.18.05/draftPurchaseAgreements` | lines, businessUnitAccess, attachments, DFF, contractDocuments | submit, validateDocument, withdraw, cancelChangeOrder, deleteChangeOrder, transferAuthoring, eSign, plus 9 more | Create or change blanket and contract agreements |
| Agreement | Purchase Agreements; Purchase Agreement Lines | `/fscmRestApi/resources/11.13.18.05/purchaseAgreements`; `/fscmRestApi/resources/11.13.18.05/purchaseAgreementLines` | lines, businessUnitAccess, notificationControls, lifecycleDetails; priceBreaks, itemAttributes | cancel, finallyClose, freeze, unfreeze, hold, removeHold, renegotiate, communicatePurchaseAgreement, duplicate, createProposal, cancelChangeOrder, generateHighlights, manageCatalogAdminAuthoring, viewPDF, viewMasterContract | Approved agreements (no POST create) and their lines |
| Agreement | Purchase Agreement Import Requests; Purchase Agreement Acknowledgments | `/fscmRestApi/resources/11.13.18.05/purchaseAgreementImportRequests`; `/fscmRestApi/resources/11.13.18.05/purchaseAgreementAcknowledgments` | lines, businessUnitAccess | importPurchaseAgreements | Import agreements through REST; supplier acknowledgment |
| Receipt | Inbound Shipments | `/fscmRestApi/resources/11.13.18.05/inboundShipments` | shipmentLines, headerAttachments, shipmentHeaderDFFs | cancelASN (C), cancelASNLine (C), closeASNLine (C) | Query and cancel advance shipment notices |
| Receipt | Receiving Receipt Requests | `/fscmRestApi/resources/11.13.18.05/receivingReceiptRequests` | lines (lotItemLots, serialItemSerials, lotSerialItemLots, processingErrors, transactionDFF), attachments, DFF | submitForApproval (C); lines: processInlineApprovalOutcome (C), submitForApproval (C) | Create receipts and ASNs for purchase orders, RMAs, in-transit shipments and transfer orders; replaces Receipts (Deprecated); example 6.5.5 |
| Receipt | Requests for Receiving Transactions | `/fscmRestApi/resources/11.13.18.05/receivingReceiptTransactionRequests` | lotItemLots, serialItemSerials, processingErrors, attachments, DFF | processInlineApprovalOutcome (C), submitForApproval (C) | Inspect, put away, correct and return; replaces Receiving Transactions (Deprecated) |
| Receipt | Receiving Receipt Deliveries; Receiving Transactions History | `/fscmRestApi/resources/11.13.18.05/receivingReceiptDeliveries`; `/fscmRestApi/resources/11.13.18.05/receivingTransactionsHistory` | Attachments; lots, serials, receiptDFF, transactionDFFs | completeDeliveriesForLPN (C), completeDeliveriesForCart (C), isReceiptLineEligibleForAutoCreateDelivery (C) | Deliveries in receiving; receipt and transaction history |
| Receipt | Receiving Returns; Supplier Returns | `/fscmRestApi/resources/11.13.18.05/receivingReturns`; `/fscmRestApi/resources/11.13.18.05/supplierReturns` | lines | submitForApproval (C); lines: cancel | Returns to supplier |
| Receipt | Purchase Orders, Purchase Order Lines, Purchase Order Schedules, ASNs for Receiving; Validate Receive Quantities | `/fscmRestApi/resources/11.13.18.05/purchaseOrdersForReceiving`; `/fscmRestApi/resources/11.13.18.05/purchaseOrderLinesForReceiving`; `/fscmRestApi/resources/11.13.18.05/purchaseOrderSchedulesForReceiving`; `/fscmRestApi/resources/11.13.18.05/asnsForReceiving`; `/fscmRestApi/resources/11.13.18.05/validateReceiveQuantities` | - | - | Find receivable documents; validate a quantity before posting |
| Receipt | Receipt Advice Lines | `/fscmRestApi/resources/11.13.18.05/receiptAdviceLines` | lots, serials, reservations, manufacturerParts | generateReceiptAdviceLines (C) | Receipt advice for a 3PL or WMS |
| Receipt accounting | Receipt Cost Adjustments; Invoice Matching Receipt Quantity Transactions | `/fscmRestApi/resources/11.13.18.05/receiptCosts`; `/fscmRestApi/resources/11.13.18.05/invoiceMatchingReceiptQuantityTransactions` | ReceiptCostDetails | - | Receipt cost adjustments; ordered, received, delivered and billed quantities for invoice matching |
| Landed cost | Trade Operations; Invoice Lines for Landed Costs | `/fscmRestApi/resources/11.13.18.05/tradeOperations`; `/fscmRestApi/resources/11.13.18.05/invoiceLinesForLandedCosts` | charges, tradeOperationShipments; chargeAssociations | createTradeOperationFromInvoices (C), allocateCharges, calculateTax, plus 7 more; associateChargeLines, updateChargeId | Landed cost charges and their invoice lines |
| Invoice | Invoices | `/fscmRestApi/resources/11.13.18.05/invoices` | invoiceLines (invoiceDistributions, invoiceLineDff, invoiceLineProjectDff), invoiceInstallments, appliedPrepayments, availablePrepayments, attachments, invoiceDff, invoiceGdf | validateInvoice (C), calculateTax (C), generateDistributions (C), reverseDistributions (C), applyPrepayments (C), unapplyPrepayments (C), cancelInvoice (C), cancelLine (C) | Create, query, update and validate supplier invoices; only certain attributes are updatable and no cascade defaulting happens; examples 6.5.2 and 6.5.3 |
| Invoice | Invoice Holds; Payables Invoice Holds | `/fscmRestApi/resources/11.13.18.05/invoiceHolds`; `/fscmRestApi/resources/11.13.18.05/payablesInvoiceHolds` | invoiceHoldDff | - | Place (POST), release (PATCH `ReleaseName`) and query holds; hold definitions (GET); example 6.5.4 |
| Invoice | Supplier Portal Payables Invoices | `/fscmRestApi/resources/11.13.18.05/payablesInvoicesInSupplierPortal` | ispInvoiceRestLines, ispInvoiceRestAttachments | submitInvoice (C), calculateTax (C), cancelInvoice (C), cancelLine (C) | Supplier-entered invoices; the Invoices resource does not run actions on them |
| Invoice | Payables Interface Invoices | `/fscmRestApi/resources/11.13.18.05/payablesInterfaceInvoices` | interfaceInvoiceLines, interfaceInvoiceRejections, attachments | submitImportInvoices (C), interfaceRejections | Oracle states these endpoints are for Oracle internal use with the Visual Builder add-in for Excel only; integrate through FBDI or erpintegrations |
| Invoice | Invoice Approvals and Notifications History; Interim Payables Documents | `/fscmRestApi/resources/11.13.18.05/invoiceApprovalsAndNotificationsHistory`; `/fscmRestApi/resources/11.13.18.05/interimDocumentsPayables` | - | - | Approval and hold-resolution history; interim documents for validation and payment |
| Invoice | ERP Document IO (supplier invoices) | `/api/erp/integrations/resources/v1/payables/supplierInvoices/files/import`; `/api/erp/integrations/resources/v1/payables/supplierInvoices/requests/{requestId}` | - | - | Multipart upload of a supplier invoice file, processed asynchronously into Payables interface tables; flowCode example `FIN_AP_IMPORT_PAYABLES_INVOICES` |
| Payment | Payables Payments | `/fscmRestApi/resources/11.13.18.05/payablesPayments` | relatedInvoices, paymentDff, paymentGdf | initiateStopPayment (C), initiateEscheat (C) | Create manual payments (Quick and Refund payment types are not supported), void (PATCH with `VoidDate` and `VoidAccountingDate`), query; finder PaidInvoicesFinder |
| Payment | Payment Process Requests | `/fscmRestApi/resources/11.13.18.05/paymentProcessRequests` | - | none; PATCH `Action` RESUME or TERMINATE | Monitor and resume or terminate payment process requests; finder SearchPaymentProcessRequest |
| Payment | External Payees; External Bank Accounts; Instrument Assignments | `/fscmRestApi/resources/11.13.18.05/paymentsExternalPayees`; `/fscmRestApi/resources/11.13.18.05/externalBankAccounts`; `/fscmRestApi/resources/11.13.18.05/instrumentAssignments` | externalPartyPaymentMethods, digitalPaymentAccountAssignments; accountOwners, intermediaryBankAccounts | - | Supplier payee setup, bank accounts and their assignment |
| Payment | Early Payment Offers | `/fscmRestApi/resources/11.13.18.05/buyerInitiatedEarlyPaymentOffers` | assignments | sendEarlyPaymentOffers (C), getSupplierContacts (C), getCampaignDetailsUsingVendorId (C), updateSupplierAssignments (C) | Early payment (discount) campaigns |
| Setup | Payment Terms; Invoice Tolerances | `/fscmRestApi/resources/11.13.18.05/payablesPaymentTerms`; `/fscmRestApi/resources/11.13.18.05/payablesInvoiceTolerances` | payablesPaymentTermsLines, payablesPaymentTermsSets, payablesPaymentTermsTranslations | - | Payables terms and matching tolerances (GET) |
| Setup | Payables Options; Payables and Procurement Options; Payables Distribution Sets; Payables Calendar Types; Income Tax Types; Payables Income Tax Regions; Tax Reporting Entities | `/fscmRestApi/resources/11.13.18.05/payablesOptions`; `/fscmRestApi/resources/11.13.18.05/payablesAndProcurementOptions`; `/fscmRestApi/resources/11.13.18.05/payablesDistributionSets`; `/fscmRestApi/resources/11.13.18.05/payablesCalendarTypes`; `/fscmRestApi/resources/11.13.18.05/payablesIncomeTaxTypes`; `/fscmRestApi/resources/11.13.18.05/payablesIncomeTaxRegions`; `/fscmRestApi/resources/11.13.18.05/payablesTaxReportingEntities` | payablesDistributionSetsLines; payablesCalendarPeriods; payablesTaxReportingEntityLine | - | Business-unit defaults, distribution sets, calendars and 1099 setup (GET) |
| Setup | Procurement Agents | `/fscmRestApi/resources/11.13.18.05/procurementAgents` | DFF | getPrinters (C) | Procurement agents (buyers, catalog administrators, supplier managers) and their document access |
| Setup | List of Values | `/fscmRestApi/resources/11.13.18.05/suppliersLOV`; `/fscmRestApi/resources/11.13.18.05/purchaseOrdersLOV`; `/fscmRestApi/resources/11.13.18.05/procurementBusinessUnitsLOV`; `/fscmRestApi/resources/11.13.18.05/buyersLOV`; `/fscmRestApi/resources/11.13.18.05/payablesPaymentTermsLOV`; `/fscmRestApi/resources/11.13.18.05/payablesInvoiceHoldsLOV`; `/fscmRestApi/resources/11.13.18.05/payablesInvoiceTolerancesLOV`; `/fscmRestApi/resources/11.13.18.05/disbursementPaymentMethodsLOV`; `/fscmRestApi/resources/11.13.18.05/paymentProcessProfilesLOV`; `/fscmRestApi/resources/11.13.18.05/payeeBankAccountsLOV`; `/fscmRestApi/resources/11.13.18.05/purchaseToPayLegalEntitiesLOV` | - | - | Valid values for P2P payloads |

### 6.3 O2C resource catalog

Customer resources are split between books. The party layer of TCA (organizations, persons, addresses, contact points, usages) is exposed in the CX guide under `crmRestApi`; Financials exposes customer account inquiry, and SCM exposes a create-customer service for order capture. None of the root resources in the 26D lists creates customer accounts (HZ_CUST_ACCOUNTS), account sites or site uses directly (a negative finding from the endpoint lists). Use the Order Management create-customer service below, the SOAP Customer Account Service operation `mergeCustomerAccount`, which creates an account with its account site and site use for an existing party and party site ([Oracle example](https://docs.oracle.com/en/cloud/saas/sales/oesws/Create-CustomerAccount-including-CustomerAccountSite-and-CustomerAccountSiteUse.html)), or the bulk options in section 7.

Table 6-4. Which customer resource to use.

| Need | Resource (exact title) | Path | Notes |
|---|---|---|---|
| Organization party with addresses, contact points, classifications and usages | Hub Organizations | `/crmRestApi/resources/11.13.18.05/hubOrganizations` | Children Address, ContactPoint, UsageAssignment, Relationship, SourceSystemReference; actions findDuplicates (C), promoteDuplicateParty (C) |
| Person party | Hub Persons | `/crmRestApi/resources/11.13.18.05/hubPersons` | Same pattern; findDuplicates (C) |
| Sales account (selling relationship) | Accounts | `/crmRestApi/resources/11.13.18.05/accounts` | Children Address, AccountContact, SalesTeamMember; actions getFinancialCustomerInfo (C), findDuplicates (C) |
| Contacts and cross-references | Contacts; Source System References | `/crmRestApi/resources/11.13.18.05/contacts`; `/crmRestApi/resources/11.13.18.05/hubSourceSystemReferences` | Contact persons; source-system keys for TCA objects |
| Sold-to party, bill-to account and ship-to in one call | Customer for Sales Orders | `/fscmRestApi/fom/11.13.18.05/customerForSalesOrders/createCustomer` (POST) | Request objects soldTo, billTo, shipTo; `manualCustomerNumberingFlag` for user-supplied party, site and account numbers |
| Account balances, open items and contacts | Receivables Customer Account Activities; Receivables Customer Account Site Activities | `/fscmRestApi/resources/11.13.18.05/receivablesCustomerAccountActivities`; `/fscmRestApi/resources/11.13.18.05/receivablesCustomerAccountSiteActivities` | Read-only inquiry plus contact actions addExistingContact, createNewContact, updateContact; example 6.5.8 |
| Bill-to site lookup; receipt method on an account or site | Customer Account Sites List of Values; Receipt Method Assignments | `/fscmRestApi/resources/11.13.18.05/customerAccountSitesLOV`; `/fscmRestApi/resources/11.13.18.05/receiptMethodAssignments` | LOV keyed by SiteUseId; assignment supports POST, PATCH, DELETE |

The CX root Sales Orders (`/crmRestApi/resources/11.13.18.05/salesOrders`) holds quote and order headers of CX Sales, not Order Management orders; for fulfillment use Sales Orders for Order Hub.

Table 6-5. Order-to-Cash REST resources (base path relative to `https://<POD_HOST>`).

| Step | Resource (exact title) | Base path | Important child resources | Custom actions (exact) | Typical use |
|---|---|---|---|---|---|
| Pricing | Price Lists | `/fscmRestApi/resources/11.13.18.05/priceLists` | items, headerDFF, accessSets, referencedEntities | - (validateDateOverlap at child level) | Maintain list prices |
| Pricing | Discount Lists; Shipping Charge Lists; Cost Lists; Currency Conversion Lists | `/fscmRestApi/resources/11.13.18.05/discountLists`; `/fscmRestApi/resources/11.13.18.05/shippingChargeLists`; `/fscmRestApi/resources/11.13.18.05/costLists`; `/fscmRestApi/resources/11.13.18.05/currencyConversionLists` | items, details, conversions, accessSets | copy (discount lists); populateChargeAndCostElement (cost lists) | Discounts, freight charges, costs for margin, currency conversion |
| Pricing | Pricing Strategies; Pricing Strategy Assignments; Customer Pricing Profiles; Pricing Matrixes; Pricing Segments | `/fscmRestApi/resources/11.13.18.05/pricingStrategies`; `/fscmRestApi/resources/11.13.18.05/pricingStrategyAssignments`; `/fscmRestApi/resources/11.13.18.05/customerPricingProfiles`; `/fscmRestApi/resources/11.13.18.05/pricingMatrixes`; `/fscmRestApi/resources/11.13.18.05/pricingSegments` | associatedDiscountLists, associatedShippingChargeLists, associatedCostLists; pricingMatrixes; DFF; dimensions, rules | - | Which price lists apply to which customer segment |
| Pricing | Price Books; Price Book Retrieval | `/fscmRestApi/resources/11.13.18.05/priceBooks`; `/fscmRestApi/resources/11.13.18.05/priceBookRetrievals` | dimensions, lines, publications | copyPriceBook, generatePriceBook, deletePriceBook; publications: publishPriceBook | List and net prices calculated and saved to a price book, then retrieved |
| Pricing | Document Prices | `/fscmRestApi/priceExecution/documentPrices/priceSalesTransaction`; `/fscmRestApi/priceExecution/documentPrices/calculateSalesTotals`; `/fscmRestApi/priceExecution/documentPrices/getSalesPricingStrategy` (POST) | - | - | Price a sales transaction, calculate sales totals or get the pricing strategy |
| Order | Sales Orders for Order Hub | `/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub` | lines (holds, charges, priceAdjustments, salesCredits, billingPlans), holds, billToCustomer, shipToCustomer, payments, totals, attachments | applyHold (C), releaseHold (C), splitFulfillmentLine (C), updateActualDeliveryDate (C), updateSchedulingAttribute (C) | Create, update and query orders; finders findByOrderNumber, findBySourceOrderNumberAndSystem, findByOrderKey, findByOrderedDate; item key OrderKey; examples 6.5.6 and 6.5.7 |
| Order | Sales Orders for Order Hub Requests | `/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHubRequests` | lines, billToCustomer, shipToCustomer, payments, orderPreferences | - | Staged orders before submission |
| Order | Sales Order Action Requests; OM Search Mass Action Requests | `/fscmRestApi/resources/11.13.18.05/salesOrderActionRequests`; `/fscmRestApi/resources/11.13.18.05/omSearchMassActionRequests` | requests, manualPriceAdjustments; - | - (ActionCode in payload, for example `ORA_FOM_APPLY_ORDER_HOLD`) | Mass action on many orders (for example apply hold): POST returns StatusCode PRE_PROCESSING while a batch process runs offline; GET the request for the summary and per-order status. OM Search Mass Action Requests (GET only) searches actions applied to orders or lines |
| Order | Global Order Promising | `/fscmRestApi/msp/latest/globalOrderPromises/checkAvailability`; `/fscmRestApi/msp/latest/globalOrderPromises/scheduleSalesOrders`; `/fscmRestApi/msp/latest/globalOrderPromises/supplyAvailability` (POST) | - | - | Availability and scheduling; replaces Order Promises (`/fscmRestApi/resources/11.13.18.05/orderPromises`) and Available Supplies (Deprecated) |
| Order | Configurations | `/fscmRestApi/resources/11.13.18.05/configurations` | ConfigurationLines, ConfigurationMessages, modelNodes | validate, finish, copy, cancel, reviseQuantity | Configure-to-order models |
| Fulfillment | Inventory Reservations; Inventory On-Hand Balances; Available Quantity Details | `/fscmRestApi/resources/11.13.18.05/inventoryReservations`; `/fscmRestApi/resources/11.13.18.05/inventoryOnhandBalances`; `/fscmRestApi/resources/11.13.18.05/availableQuantityDetails` | serials, serialRanges; lots, serials | transferRsvToAnotherDemand (C) | Reserve and check stock for order lines |
| Fulfillment | Pick Waves; Picks; Pick Transactions | `/fscmRestApi/resources/11.13.18.05/pickWaves`; `/fscmRestApi/resources/11.13.18.05/inventoryPicks`; `/fscmRestApi/resources/11.13.18.05/pickTransactions` | DFF; pickLines | - | Release lines to the warehouse and confirm picks |
| Shipping | Shipment Line Change Requests | `/fscmRestApi/resources/11.13.18.05/shipmentLineChangeRequests` | shipmentLines | pickRelease (C), confirm (C), backorderLine (C), backorderAll (C), split (C), assign (C), unassign (C), pack (C), unpack (C), generateShipmentRequest (C), checkTradeCompliance (C), plus 15 more | Change shipment lines and run shipping actions; generateShipmentRequest sends lines to a WMS |
| Shipping | Shipment Lines; Shipments | `/fscmRestApi/resources/11.13.18.05/shipmentLines`; `/fscmRestApi/resources/11.13.18.05/shipments` | reservations, serials, lineDFF, notes; outerPackingUnits, unpackedShipmentLines, shippingCosts, shipmentsDFF | - | Query shipment lines and shipments (no POST create on Shipments) |
| Shipping | Shipment Transaction Requests; Shipment Line Transaction Requests; Shipping Transactions | `/fscmRestApi/resources/11.13.18.05/shipmentTransactionRequests`; `/fscmRestApi/resources/11.13.18.05/shipmentLineTransactionRequests`; `/fscmRestApi/resources/11.13.18.05/shippingTransactions` | shipments (outerPackingUnits, unpackedLines, costs), errors; shipmentLines, errors | shipmentActions (C) | Ship confirmation from a 3PL or WMS through the open interface, processed by the Perform Shipping Transactions scheduled process; Shipping Transactions supports only CONFIRM |
| Shipping | Shipping Costs; Shipping Exceptions; Carriers; Release Rules; Ship Confirm Rules | `/fscmRestApi/resources/11.13.18.05/shippingCosts`; `/fscmRestApi/resources/11.13.18.05/shippingExceptions`; `/fscmRestApi/resources/11.13.18.05/carriers`; `/fscmRestApi/resources/11.13.18.05/releaseRules`; `/fscmRestApi/resources/11.13.18.05/shipConfirmRules` | DFF; contacts, shippingMethods, inboundTrackingRules | - | Freight costs, exceptions and shipping setup |
| Returns | Receiving Receipt Requests | `/fscmRestApi/resources/11.13.18.05/receivingReceiptRequests` | lines | as in 6.2 | RMA receipts with `ReceiptSourceCode` CUSTOMER and `SourceDocumentCode` RMA |
| Costing | Item Costs; Estimated Transfer Price for Sales Order Shipments | `/fscmRestApi/resources/11.13.18.05/itemCosts`; `/fscmRestApi/resources/11.13.18.05/financialOrchestrationTransferPriceforShipments` | costDetails | calculateTransferPrice (C) | Perpetual average item cost by cost organization and cost book (margin and COGS checks); estimated intercompany transfer price |
| Billing | AutoInvoice Interface Lines | `/fscmRestApi/resources/11.13.18.05/autoInvoiceInterfaceLines` | autoInvoiceHeaderInformationDFF, autoInvoiceLineInformationDFF, autoInvoiceInterfaceLineTransactionDFF | - | Find and correct interface lines (GET, PATCH); PATCH covers only transaction type, payment terms, line status, tax code, description, internal notes and DFF attributes; AutoInvoice itself is in section 7 |
| Billing | Receivables Invoices | `/fscmRestApi/resources/11.13.18.05/receivablesInvoices` | receivablesInvoiceLines (receivablesInvoiceLineTaxLines), receivablesInvoiceDistributions, receivablesInvoiceInstallments, notes, attachments, receivablesInvoiceDFF | approve, rework, resendInvoiceCopy, splitInstallments | Create and query invoices; PATCH only InvoiceStatus, PaymentTerms and TransactionDate; finders PrimaryKey, invoiceSearch |
| Billing | Receivables Credit Memos | `/fscmRestApi/resources/11.13.18.05/receivablesCreditMemos` | receivablesCreditMemoLines, receivablesCreditMemoDistributions, notes, attachments, receivablesCreditMemoDFF | approve, rework | Create and query credit memos; approve or rework. Standard credit memos support GET and PATCH (only AllowCompletion, CreditMemoStatus and TransactionType) once the lookup code named in Oracle's [Process Standard Credit Memos](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Process_Standard_Credit_Memos.html) topic is enabled through the Manage Receivables Lookups task |
| Billing | Receivables Adjustments | `/fscmRestApi/resources/11.13.18.05/receivablesAdjustments` | receivablesAdjustmentDFF | - | Query adjustments (GET only in 26D) |
| Billing | Bill Management Users; Salesperson Reference Accounts | `/fscmRestApi/resources/11.13.18.05/billManagementUsers`; `/fscmRestApi/resources/11.13.18.05/salespersonReferenceAccounts` | - | - | Enroll customer contacts in Bill Management; reference accounts of a salesperson |
| Billing | Receivables Transaction Types, Transaction Sources, Memo Lines, Payment Terms, Revenue Scheduling Rules, Business Units List of Values | `/fscmRestApi/resources/11.13.18.05/transactionTypesLOV`; `/fscmRestApi/resources/11.13.18.05/transactionSourcesLOV`; `/fscmRestApi/resources/11.13.18.05/memoLinesLOV`; `/fscmRestApi/resources/11.13.18.05/paymentTermsLOV`; `/fscmRestApi/resources/11.13.18.05/revenueSchedulingRulesLOV`; `/fscmRestApi/resources/11.13.18.05/receivablesBusinessUnitsLOV` | - | - | Valid values for invoice and credit memo payloads |
| Cash | Standard Receipts | `/fscmRestApi/resources/11.13.18.05/standardReceipts` | remittanceReferences, attachments, standardReceiptDFF, standardReceiptGdf | applyReceipt, bulkApplyReceipt, unapplyReceipt, reverseReceipt, refundReceipt | Create, apply and reverse receipts; PATCH only customer attributes; finder StandardReceiptsFinder; example 6.5.9 |
| Cash | Receipt Methods; Debit Authorizations | `/fscmRestApi/resources/11.13.18.05/receiptMethods`; `/fscmRestApi/resources/11.13.18.05/debitAuthorizations` | receiptMethodDFF; debitAuthorizationVersions | - | Receipt class and remittance bank by method; direct debit mandates |
| Collections | Collections Delinquencies; Collections Strategies; Collection Promises | `/fscmRestApi/resources/11.13.18.05/collectionsDelinquencies`; `/fscmRestApi/resources/11.13.18.05/collectionStrategies`; `/fscmRestApi/resources/11.13.18.05/collectionPromises` | strategyExecutionTasks, strategyUserTasks, strategyTemplateTasks; collectionPromiseDFF | - | Delinquencies, strategy tasks (skip or cancel with PATCH on the task children) and promises to pay; dunning has no root resource (scheduled processes, section 7) |
| Collections | Receivables Disputes; Credit Data Points; Credit Data Point Values | `/fscmRestApi/resources/11.13.18.05/receivablesDisputes`; `/fscmRestApi/resources/11.13.18.05/creditAndCollectionsDataPoints`; `/fscmRestApi/resources/11.13.18.05/dataPointValues` | receivablesDisputeLines | - | Disputes on transactions; credit and collections data points (firmographic, receivables and financial data) and their values |
| Claims | Channel Customer Claims | `/fscmRestApi/resources/11.13.18.05/channelCustomerClaims` | settlementLines, settlementMethods, associations, splits | settle, settleCustom, cancel, reopenCustom | Customer claims and deductions from investigation to settlement |
| Revenue | Source Document Lines; Revenue Contracts | `/fscmRestApi/resources/11.13.18.05/sourceDocumentLines`; `/fscmRestApi/resources/11.13.18.05/revenueContracts` | performanceObligations (promisedDetails, satisfactionEvents, sourceDocuments) | - | Revenue basis lines from Order Management and Subscription Management (GET, PATCH); contract inquiry (GET) |
| Revenue | Standalone Selling Prices (Spectra); Source Document Additional Sublines (Spectra) | `/api/boss/data/objects/ora/erpCore/revenueManagement/v1/revenueContractStandaloneSellingPrices`; `/api/boss/data/objects/ora/erpCore/revenueManagement/v1/revenueSourceDocumentAdditionalSublines` | - | `$bulk`, `$query` | Load selling prices and sublines (OAuth only) |
| B2B | B2B Message Transactions | `/fscmRestApi/resources/11.13.18.05/b2bMessageTransactions` | deliveryAttempts, receiptConfirmations | reprocessMessage (C), resubmitMessage (C), cancelMessage (C), retransmitPurchaseOrders (C), plus 11 more | Monitor and reprocess B2B messages between trading partners, including purchase order messages (also P2P) |

### 6.4 Shared resources

Table 6-6. Resources used by both cycles.

| Area | Resource (exact title) | Base path | Use, finders, actions |
|---|---|---|---|
| General Ledger | Journal Batches | `/fscmRestApi/resources/11.13.18.05/journalBatches` | GET batches with journalHeaders (journalLines), journalErrors, journalActionLogs; PATCH only completion status and reversal attributes; DELETE; finder JournalsFinder (BatchName, AccountingPeriod, BatchSource, BatchStatus, JournalCategory). No POST: load journals through erpintegrations (section 7) |
| General Ledger | Ledger Balances | `/fscmRestApi/resources/11.13.18.05/ledgerBalances` | Finder AccountBalanceFinder (ledgerName, accountCombination with `%` per segment, accountingPeriod, currency, amountType such as PTD, mode Summary or Detail); AccountGroupBalanceFinder |
| General Ledger | Currency Rates | `/fscmRestApi/resources/11.13.18.05/currencyRates` | Finder CurrencyRatesFinder (fromCurrency, toCurrency, userConversionType, startDate, endDate, maxRollDays) |
| General Ledger | Ledgers, Account Combinations, Accounting Periods, Accounting Period Status, Chart of Accounts, Journal Categories, Journal Sources, Currency Conversion Types, Legal Entities, Financials Business Units List of Values | `/fscmRestApi/resources/11.13.18.05/ledgersLOV`; `/fscmRestApi/resources/11.13.18.05/accountCombinationsLOV`; `/fscmRestApi/resources/11.13.18.05/accountingPeriodsLOV`; `/fscmRestApi/resources/11.13.18.05/accountingPeriodStatusLOV`; `/fscmRestApi/resources/11.13.18.05/chartOfAccountsLOV`; `/fscmRestApi/resources/11.13.18.05/journalCategoriesLOV`; `/fscmRestApi/resources/11.13.18.05/journalSourcesLOV`; `/fscmRestApi/resources/11.13.18.05/currencyConversionTypesLOV`; `/fscmRestApi/resources/11.13.18.05/legalEntitiesLOV`; `/fscmRestApi/resources/11.13.18.05/finBusinessUnitsLOV` | Values and validation for accounts, periods and business units |
| Subledger Accounting | Subledger Accounting Account Rules; Subledger Accounting Mapping Sets; Accounting Hub Applications | `/fscmRestApi/resources/11.13.18.05/accountingSetupAccountRules`; `/fscmRestApi/resources/11.13.18.05/accountingSetupMappingSets`; `/fscmRestApi/resources/11.13.18.05/accountingHubApplications` | Maintain account rules and mapping sets; LOVs subledgerApplicationsLOV, accountingEventClassesLOV, accountingEventTypesLOV. No root exposes subledger journal entries; query them with OTBI, BICC or SQL (sections 8 and 9) |
| Tax | Tax Registrations; Party Tax Profiles; Tax Exemptions; Party Fiscal Classifications; Taxpayer Identifiers | `/fscmRestApi/resources/11.13.18.05/taxRegistrations`; `/fscmRestApi/resources/11.13.18.05/partyTaxProfiles`; `/fscmRestApi/resources/11.13.18.05/taxExemptions`; `/fscmRestApi/resources/11.13.18.05/partyFiscalClassifications`; `/fscmRestApi/resources/11.13.18.05/taxPayerIdentifiers` | Supplier and customer tax setup (GET, POST, PATCH) |
| Tax | Transaction Tax Lines; Withholding Tax Lines; Validate Tax Configurations | `/fscmRestApi/resources/11.13.18.05/transactionTaxLines`; `/fscmRestApi/resources/11.13.18.05/withholdingTaxLines`; `/fscmRestApi/resources/11.13.18.05/validateTaxConfigurations` | Tax lines of a transaction (finder findByTransactionFinder with ApplicationId, EntityCode, EventClassCode, TrxId); configuration check; LOVs taxClassifications, taxRatesLOV, taxRegimesLOV, inputTaxClassificationsLOV, outputTaxClassificationsLOV |
| Cash Management | Bank Accounts; Banks; Bank Branches; External Cash Transactions; Cash Bank Account Transfers | `/fscmRestApi/resources/11.13.18.05/cashBankAccounts`; `/fscmRestApi/resources/11.13.18.05/cashBanks`; `/fscmRestApi/resources/11.13.18.05/cashBankBranches`; `/fscmRestApi/resources/11.13.18.05/cashExternalTransactions`; `/fscmRestApi/resources/11.13.18.05/cashBankAccountTransfers` | Internal bank accounts (bankAccountUses, bankAccountPaymentDocuments); external cash transactions, voided by updating their status |
| Intercompany and netting | Intercompany Agreements; Intercompany Transaction Source Documents; Netting Agreements | `/fscmRestApi/resources/11.13.18.05/intercompanyAgreements`; `/fscmRestApi/resources/11.13.18.05/intercompanyTransactionSourceDocuments`; `/fscmRestApi/resources/11.13.18.05/nettingAgreements` | generateTransactions (C), approveTransferAuthorizations (C), generateAccountingLines (C), reverseTransferAuthorizationGrp (C); createTransferAuthorization (C); AP and AR netting rules (nettingSupplierTradingPartners, nettingCustomerTradingPartners) |
| Bulk and jobs | ERP Integrations | `/fscmRestApi/resources/11.13.18.05/erpintegrations` | POST with `OperationName` importBulkData, exportBulkData, uploadFileToUCM or submitESSJobRequest; GET finders ESSJobStatusRF, ESSExecutionDetailsRF, ESSJobExecutionDetailsRF, DocumentRF, DocumentIdsByFilePrefixRF; callback and notification options; example 6.5.10 |
| Bulk and jobs | ERP Processes; ERP Business Events; Analytics | `/fscmRestApi/resources/11.13.18.05/erpProcesses`; `/fscmRestApi/resources/11.13.18.05/erpBusinessEvents`; `/fscmRestApi/resources/11.13.18.05/analytics` | Process and parameter details; enable or disable business events (section 7); executeLogicalQuery (C) runs an OTBI logical query (section 8) |
| Bulk and jobs | Scheduler; ERP Data Integrations | `ess/rest/scheduler/v1/requests/{requestId}` (Common Features guide); `/api/erp/integrations/resources/v1/{locale}/files/upload` | Job status, cancel, hold and release; Accounting Hub file upload with file and transaction metrics |
| Lookups | Common Lookups; Generic Lookups; Standard Lookups List of Values; Lookups | `commonLookups` and `genericLookups` (Common Features guide, CRUD with child lookupCodes); `/fscmRestApi/resources/11.13.18.05/standardLookupsLOV`; `/crmRestApi/resources/11.13.18.05/fndStaticLookups` | Lookup views Standard, Common and Set-Enabled; Generic Lookups reads any view. The Common Features guide also lists Spectra versions (Standard Lookups, Common Lookups and Set-Enabled Lookups, Lookup Types and Lookup Codes (Spectra)) |
| Attachments | child `attachments` of each resource | - | See Table 6-1; no root resource |
| Audit | Audit Report | `/fscmRestApi/fndAuditRESTService/audittrail/getaudithistory` (POST) | Audit history by product, business object type, user and event type; fromDate, toDate and product are required; up to one month per request; audit setup operations sit beside it |
| Setup | Features; Setup Tasks | `/fscmRestApi/resources/11.13.18.05/features`; `/fscmRestApi/resources/11.13.18.05/setupTasks` | Opt-in feature status (`EnabledFlag`); setup task metadata, with CSV export and import in `setupTaskCSVExports` and `setupTaskCSVImports` |

Sources for 6.2 to 6.4: the 26D endpoint lists ([Financials](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/rest-endpoints.html), [Procurement](https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/rest-endpoints.html), [SCM](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/rest-endpoints.html), [Common Features](https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/rest-endpoints.html)), resource descriptions in those lists, [Deprecated REST Resources (SCM)](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/Deprecated_REST_APIs.html), [Work with Lookups](https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/work-with-lookups.html), [Process Requisition Lines into a New Order](https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/use-case_process_requisition_lines_into_a_new_order.html), [Shipment integration use case](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/use_case_integrate_shipment_request_shipment_confirmation_processes_external_systems.html), [Apply Hold on Large Volume of Sales Orders](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/use-case_ApplyHoldonLargeVolumeofSalesOrders.html), [Create customer for sales orders](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/op-fscmrestapi-fom-11.13.18.05-customerforsalesorders-createcustomer-post.html), [Get Started with Payables Invoices](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Get_Started_Payables_Invoices.html), [Void a Payment](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Void_a_Payment.html), [Get Started with Payments](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Get_Started_Payments.html), [Process Standard Credit Memos](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Process_Standard_Credit_Memos.html), [Update a payment process request](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-paymentprocessrequests-paymentprocessrequestid-patch.html), [Manage AutoInvoice Interface Lines](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Manage_AutoInvoice_Interface_Lines.html), [Skip a Strategy User Task](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Skip_a_Strategy_User_Task.html), [Get all ledger balances](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-ledgerbalances-get.html), [Get all currency rates](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-currencyrates-get.html), [Get all journal batches](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-journalbatches-get.html), [Get all transaction tax lines](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-transactiontaxlines-get.html), [Features](https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-resources-11.13.18.05-features-featurecode-get.html), [Scheduler request](https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-ess-rest-scheduler-v1-requests-requestid-get.html), [Audit report](https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-fndauditrestservice-audittrail-getaudithistory-post.html).

### 6.5 Worked examples

Placeholders in angle brackets are environment values. `curl -u "<USER>"` prompts for the password, so no secret is typed on the command line; with OAuth use `-H "Authorization: Bearer <ACCESS_TOKEN>"` instead. All examples send `REST-Framework-Version: 4` (expanded `q` syntax, nested children as collections, structured errors); lower it if the API's `allowedFrameworkVersions` does not include 4. `-G --data-urlencode` builds an encoded query string. Check every filtered attribute with `describe` (`queryable: true`) before relying on it. Run write examples (6.5.3, 6.5.5, 6.5.7, 6.5.9, 6.5.10) only in a test pod: they create real transactions, approvals and accounting.

#### 6.5.1 Open purchase orders for a supplier

```bash
curl -s -u "<USER>" -H "REST-Framework-Version: 4" -G \
  --data-urlencode "q=Supplier='<SUPPLIER_NAME>' and StatusCode='OPEN'" \
  --data-urlencode "fields=POHeaderId,OrderNumber,Supplier,SupplierSite,ProcurementBU,Status,Ordered,Total,CurrencyCode" \
  --data-urlencode "orderBy=OrderNumber" --data-urlencode "limit=100" \
  --data-urlencode "totalResults=true" --data-urlencode "onlyData=true" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/purchaseOrders"
```

Read `items`, `totalResults` and `hasMore`; repeat with `offset=100`. Lines and schedules are under `/fscmRestApi/resources/11.13.18.05/purchaseOrders/<ORDER_KEY_FROM_SELF_LINK>/child/lines`; take the key from the `self` link. Rows are filtered by data security: buyers see orders of their procurement business units, Payables users see orders of their bill-to business units. Sources: [Get all purchase orders](https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-purchaseorders-get.html), [Procurement Privileges](https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/Roles_and_Privileges.html).

#### 6.5.2 One invoice with lines, distributions and installments

```bash
curl -s -u "<USER>" -H "REST-Framework-Version: 4" -G \
  --data-urlencode "q=InvoiceNumber='<INVOICE_NUMBER>' and Supplier='<SUPPLIER_NAME>' and BusinessUnit='<BU_NAME>'" \
  --data-urlencode "fields=InvoiceId,InvoiceNumber,InvoiceAmount,ValidationStatus,ApprovalStatus,PaidStatus;invoiceLines:LineNumber,LineType,LineAmount,PurchaseOrderNumber;invoiceLines.invoiceDistributions:DistributionLineNumber,DistributionLineType,DistributionAmount,DistributionCombination;invoiceInstallments:InstallmentNumber,DueDate,UnpaidAmount,HoldFlag" \
  --data-urlencode "onlyData=true" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/invoices"
```

The same invoice number can exist for more than one supplier, so filter on supplier and business unit as well (Oracle's holds example uses this combination). The only finder on Invoices is PrimaryKey (InvoiceId). Sources: [Get Specific Details example](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Get_Specific_Details_for_Invoices_Lines_Distributions_and_Installments.html), [Get all invoices](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-invoices-get.html).

#### 6.5.3 Create an invoice, then validate it

Warning: this creates a real Payables invoice that can be approved, accounted and paid. Use a test pod and a unique invoice number per supplier; a duplicate returns "This invoice number already exists" (AP-810776).

```json
{
  "InvoiceNumber": "<INVOICE_NUMBER>",
  "InvoiceCurrency": "<CURRENCY_CODE>",
  "InvoiceAmount": "<AMOUNT>",
  "InvoiceDate": "<YYYY-MM-DD>",
  "BusinessUnit": "<BU_NAME>",
  "Supplier": "<SUPPLIER_NAME>",
  "SupplierSite": "<SUPPLIER_SITE>",
  "Description": "<DESCRIPTION>",
  "invoiceLines": [
    { "LineNumber": 1, "LineType": "Item", "LineAmount": "<AMOUNT>",
      "DistributionCombination": "<ACCOUNT_COMBINATION>" }
  ]
}
```

```bash
curl -s -u "<USER>" -X POST -H "REST-Framework-Version: 4" \
  -H "Content-Type: application/vnd.oracle.adf.resourceitem+json" -d @invoice.json \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/invoices"

curl -s -u "<USER>" -X POST -H "REST-Framework-Version: 4" \
  -H "Content-Type: application/vnd.oracle.adf.action+json" \
  -d '{"InvoiceNumber":"<INVOICE_NUMBER>","BusinessUnit":"<BU_NAME>","Supplier":"<SUPPLIER_NAME>","ProcessAction":"Validate"}' \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/invoices/action/validateInvoice"
```

A 201 returns `InvoiceId` and the defaulted header. For a PO-matched line replace `DistributionCombination` with `PurchaseOrderNumber`, `PurchaseOrderLineNumber`, `PurchaseOrderScheduleLineNumber`, `Quantity` and `UnitPrice`. Validation returns `{"result": "The current action Validate Invoice has completed successfully."}`; validation calculates tax, checks tolerances and places holds, so check 6.5.4 afterwards. Sources: [PO-matched invoice example](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Create_an_Invoice_with_a_PO_Matched_Line_and_Freight_Line.html), [Unmatched line example](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Create_an_Invoice_with_an_Unmatched_Line_with_Project_Information.html), [Validate an invoice](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-invoices-action-validateinvoice-post.html).

#### 6.5.4 Invoices on hold

```bash
curl -s -u "<USER>" -H "REST-Framework-Version: 4" -G \
  --data-urlencode "q=BusinessUnit='<BU_NAME>' and ReleaseName IS NULL" \
  --data-urlencode "fields=HoldId,InvoiceNumber,Supplier,HoldName,HoldReason,HoldDate,LineHeld" \
  --data-urlencode "orderBy=HoldDate:desc" --data-urlencode "onlyData=true" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/invoiceHolds"
```

Unreleased holds have empty `ReleaseName` and `ReleaseDate`. To release one (write), PATCH `/fscmRestApi/resources/11.13.18.05/invoiceHolds/<HOLD_ID>` with `{"ReleaseName": "<RELEASE_NAME>"}`; Oracle's example uses the release name "Amount approved". Valid hold and release names come from `payablesInvoiceHoldsLOV` and the row-level LOVs of the hold. Sources: [Holds without unique invoice number](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Get_Holds_Information_for_Invoices_Without_Unique_Invoice_Number.html), [Holds by child attribute](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Get_Invoice_Holds_Using_a_Child_Resource_Attribute.html), [Release an Invoice Hold](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Release_an_Invoice_Hold.html).

#### 6.5.5 Receive a purchase order through receivingReceiptRequests

Warning: this records a real receipt against the purchase order; it feeds receipt accounting and invoice matching and, once delivered, inventory.

```json
{
  "ReceiptSourceCode": "VENDOR",
  "OrganizationCode": "<ORG_CODE>",
  "VendorName": "<SUPPLIER_NAME>",
  "VendorSiteCode": "<SUPPLIER_SITE>",
  "BusinessUnit": "<PROCUREMENT_BU>",
  "EmployeeName": "<RECEIVER_NAME>",
  "lines": [
    { "ReceiptSourceCode": "VENDOR", "SourceDocumentCode": "PO", "TransactionType": "RECEIVE",
      "OrganizationCode": "<ORG_CODE>", "DocumentNumber": "<PO_NUMBER>",
      "DocumentLineNumber": 1, "DocumentShipmentLineNumber": 1,
      "ItemNumber": "<ITEM_NUMBER>", "Quantity": 1, "UnitOfMeasure": "<UOM_NAME>" }
  ]
}
```

```bash
curl -s -u "<USER>" -X POST -H "REST-Framework-Version: 4" \
  -H "Content-Type: application/vnd.oracle.adf.resourceitem+json" -d @receipt.json \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/receivingReceiptRequests"

curl -s -u "<USER>" -H "REST-Framework-Version: 4" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/receivingReceiptRequests/<HEADER_INTERFACE_ID>/child/lines/<INTERFACE_TRANSACTION_ID>/child/processingErrors"
```

With the default `InsertAndProcessFlag` true the request is processed immediately; `ReturnStatus` is SUCCESS or ERROR for synchronous processing (SUBMITTED or QUEUED when asynchronous), `ProcessingStatusCode` is PENDING, ERROR or SUCCESS, and `ReceiptNumber` is returned. With false, rows wait in the interface for the Manage Receiving Transactions scheduled process. `DocumentShipmentLineNumber` (PO schedule) is mandatory for PO receipts. Oracle's examples also pass `AutoTransactCode`, but its attribute description says to leave it blank. Supply `EmployeeId` instead of `EmployeeName` if names are ambiguous. Sources: [Create receipt requests](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/op-receivingreceiptrequests-post.html), [Get all receipt requests](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/op-receivingreceiptrequests-get.html).

#### 6.5.6 Get a sales order by order number

```bash
curl -s -u "<USER>" -H "REST-Framework-Version: 4" -G \
  --data-urlencode "fields=OrderKey,HeaderId,OrderNumber,SourceTransactionSystem,SourceTransactionId,StatusCode,OnHoldFlag,BuyingPartyName,TransactionalCurrencyCode;lines:FulfillLineId,DisplayLineNumber,ProductNumber,OrderedQuantity,OrderedUOM,StatusCode,ScheduleShipDate,OnHoldFlag;holds:HoldCode,HoldName,ActiveFlag,ApplyDate" \
  --data-urlencode "onlyData=true" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub?finder=findByOrderNumber;OrderNumber='<ORDER_NUMBER>'"
```

Other finders: findBySourceOrderNumberAndSystem (SourceTransactionNumber, SourceTransactionSystem), findByOrderKey (OrderKey = source system, colon, source order ID), findByHeaderId, findByOrderedDate (FromDate, ToDate). The item path uses `OrderKey`: `/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub/<ORDER_KEY>/child/lines`. Line-level filters such as `q=lines.StatusCode='AWAIT_SHIP'` need version 2 or later. Sources: [Get all sales orders](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/op-salesordersfororderhub-get.html), [SCM Privileges](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/Roles_and_Privileges.html).

#### 6.5.7 Apply a hold to a sales order

Warning: a hold stops fulfillment of the order or its lines until released.

```bash
curl -s -u "<USER>" -X POST -H "REST-Framework-Version: 4" \
  -H "Content-Type: application/vnd.oracle.adf.action+json" \
  -d '{"processRequestOfflineAfter":240,"holdRequests":[{"SourceTransactionSystem":"<SOURCE_SYSTEM>","OrderNumber":"<ORDER_NUMBER>","HoldCode":"<HOLD_CODE>","HoldComments":"<COMMENT>"}]}' \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub/action/applyHold"
```

Take `SourceTransactionSystem` from 6.5.6. Every request needs `SourceTransactionSystem` and `HoldCode` or `HoldName`; a header hold also needs `SourceTransactionId` or `OrderNumber`, a fulfillment line hold needs `FulfillLineId`. Each `result` entry returns `RequestStatus` SUCCESS or ERROR with `Message`. `processRequestOfflineAfter` is the number of seconds after which the call returns and processing continues in the background. Release with `/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub/action/releaseHold` and the same keys plus `HoldReleaseReasonCode` or `HoldReleaseReason`. For many orders post Sales Order Action Requests with `ActionCode` `ORA_FOM_APPLY_ORDER_HOLD`. Sources: [Apply hold](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/op-salesordersfororderhub-action-applyhold-post.html), [Release hold](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/fasrp/op-salesordersfororderhub-action-releasehold-post.html).

#### 6.5.8 Open receivables installments for a customer account

```bash
curl -s -u "<USER>" -H "REST-Framework-Version: 4" -G \
  --data-urlencode "fields=AccountId,AccountNumber,CustomerName,TotalOpenReceivablesForAccount;transactionPaymentSchedules:InstallmentId,TransactionNumber,TransactionClass,TransactionDate,PaymentScheduleDueDate,TotalBalanceAmount,EnteredCurrency,InstallmentStatus,PaymentDaysLate" \
  --data-urlencode "onlyData=true" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/receivablesCustomerAccountActivities?finder=CustomerAccountActivitiesFinder;AccountNumber=<ACCOUNT_NUMBER>,TransactionLimitByDays=<DAYS>"

curl -s -u "<USER>" -H "REST-Framework-Version: 4" -G \
  --data-urlencode "q=InstallmentStatus='Open'" --data-urlencode "onlyData=true" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/receivablesCustomerAccountActivities/<ACCOUNT_ID>/child/transactionPaymentSchedules"
```

The finder considers transactions up to 90 days past the transaction date unless `TransactionLimitByDays` is set; `TransactionStatus` (Complete or Incomplete) is a further variable. The second call keeps only the open installments of the account found by the first (check in your pod whether the 90-day window also applies to it). Per invoice, use `receivablesInvoices?finder=invoiceSearch;BillToCustomerNumber=<ACCOUNT_NUMBER>,InvoiceStatus=Complete` and read `InvoiceBalanceAmount`. Sources: [Get all customer account activities](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-receivablescustomeraccountactivities-get.html), [Site invoices and installments](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Search_for_All_Customer_Site_Invoices_and_Installments.html), [Find Invoices that are Overdue](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Find_Invoices_that_are_Overdue.html).

#### 6.5.9 Create a standard receipt and apply it

Warning: this records customer cash, updates customer balances and creates accounting. Reverse mistakes with `reverseReceipt`; PATCH can change only the customer attributes (CustomerAccountNumber, CustomerBankAccountNumber, CustomerName, CustomerSite).

```json
{
  "ReceiptNumber": "<RECEIPT_NUMBER>",
  "ReceiptMethod": "<RECEIPT_METHOD>",
  "ReceiptDate": "<YYYY-MM-DD>",
  "BusinessUnit": "<BU_NAME>",
  "CustomerAccountNumber": "<ACCOUNT_NUMBER>",
  "CustomerSite": "<BILL_TO_SITE>",
  "Amount": "<AMOUNT>",
  "Currency": "<CURRENCY_CODE>",
  "RemittanceBankAccountNumber": "<REMITTANCE_BANK_ACCOUNT_NUMBER>"
}
```

```bash
curl -s -u "<USER>" -X POST -H "REST-Framework-Version: 4" \
  -H "Content-Type: application/vnd.oracle.adf.resourceitem+json" -d @cash_receipt.json \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/standardReceipts"

curl -s -u "<USER>" -X POST -H "REST-Framework-Version: 4" \
  -H "Content-Type: application/vnd.oracle.adf.action+json" \
  -d '{"appliedPaymentScheduleId": <INSTALLMENT_ID>, "amountApplied": <AMOUNT>, "calledFrom": "REST"}' \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/standardReceipts/<STANDARD_RECEIPT_ID>/action/applyReceipt"
```

The POST returns `StandardReceiptId`, `State` and `Status`. `appliedPaymentScheduleId` identifies the invoice installment; use the `InstallmentId` from 6.5.8 or from the invoice's `receivablesInvoiceInstallments` (verify in your pod). Without `amountApplied` the full open balance is applied; success returns `{"result": "SUCCESS"}`. Find receipts with `finder=StandardReceiptsFinder;ReceiptNumber=<RECEIPT_NUMBER>`. Prerequisites: customers, Receivables system options, receipt classes and methods, receivables activities. Sources: [Get Started with Standard Receipts](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Get_Started_Standard_Receipts.html), [Create a Standard Receipt](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Create_a_Standard_Receipt.html), [Apply receipt](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-standardreceipts-standardreceiptid-action-applyreceipt-post.html), [What fields can I update](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/what-fields-can-i-update-using-the-standard-receipts-rest-api.html).

#### 6.5.10 Submit importBulkData and poll the job

Warning: this loads and imports every row of the file. Build the zip from the FBDI template of the target object (section 7) and Base64-encode it, for example `base64 -w0 <FILE>.zip`.

```json
{
  "OperationName": "importBulkData",
  "DocumentContent": "<BASE64_OF_ZIP>",
  "ContentType": "zip",
  "FileName": "<FILE>.zip",
  "DocumentAccount": "fin$/payables$/import$",
  "JobName": "oracle/apps/ess/financials/payables/invoices/transactions,APXIIMPT",
  "ParameterList": "<PARAMETER_LIST>",
  "CallbackURL": "#NULL",
  "NotificationCode": "10",
  "JobOptions": "InterfaceDetails=1,ImportOption=Y ,PurgeOption = Y,ExtractFileType=ALL"
}
```

```bash
curl -s -u "<USER>" -X POST -H "Content-Type: application/vnd.oracle.adf.resourceitem+json" \
  -d @import.json "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/erpintegrations"

curl -s -u "<USER>" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/erpintegrations?finder=ESSJobStatusRF;requestId=<REQUEST_ID>"

curl -s -u "<USER>" \
  "https://<POD_HOST>/fscmRestApi/resources/11.13.18.05/erpintegrations?finder=ESSJobExecutionDetailsRF;requestId=<REQUEST_ID>,fileType=ALL"
```

The POST returns `ReqstId`. Poll ESSJobStatusRF until `RequestStatus` reaches a final value (Oracle's example shows SUCCEEDED); ESSExecutionDetailsRF returns the job tree (Load Interface File for Import with child jobs Transfer File and Load File to Interface) as JSON in `RequestStatus`; ESSJobExecutionDetailsRF returns logs and output as a Base64 zip in `DocumentContent`. `JobName` (job package and definition), `DocumentAccount` and `JobOptions` above come from Oracle's Payables invoice import example, whose `ParameterList` is `#NULL,<BU_NAME>,#NULL,#NULL,#NULL,#NULL,#NULL,INVOICE GATEWAY,#NULL,#NULL,#NULL,1,#NULL` (comma-separated in job order, `#NULL` for empty parameters); take the values for other objects from their FBDI template (section 7). Prefer `CallbackURL` or `NotificationCode` to tight polling. For exports, `exportBulkData` runs the report and an Upload Interface Error and Output Details to UCM job, and `getDocumentForDocumentId` (finder DocumentRF) downloads the result. Sources: [POST erpintegrations](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-erpintegrations-post.html), [GET erpintegrations](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-erpintegrations-get.html), [Get job details (examples)](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-erpintegrations-operationname-get.html), [Import Financials Data](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Importing_Financials_Data.html), [Export Financials Data](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Export_Financials_Data.html).
