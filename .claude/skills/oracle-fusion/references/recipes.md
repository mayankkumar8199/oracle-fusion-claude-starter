# Recipes (oracle-fusion tools)

The field lists below were checked against the Oracle 26D REST docs. For anything else, call `<resource>/describe` first.
Replace `<...>` with values from the user.

## Procure-to-Pay

| Question | Call |
|---|---|
| Is the connection working? | `connection_status()` |
| Recent invoices | `fusion_get("invoices", fields="InvoiceId,InvoiceNumber,Supplier,InvoiceAmount,ValidationStatus,ApprovalStatus,PaidStatus", order_by="InvoiceId:desc", limit=10)` |
| One invoice by number | `fusion_get("invoices", q="InvoiceNumber='<NUMBER>' and Supplier='<SUPPLIER>'", fields="InvoiceId,InvoiceNumber,Supplier,InvoiceAmount,ValidationStatus,ApprovalStatus,PaidStatus")` |
| Invoice lines | `fusion_get("invoices/<InvoiceId>/child/invoiceLines", limit=25)` - add `fields=` after checking `invoices/describe` |
| Invoice installments (due dates) | `fusion_get("invoices/<InvoiceId>/child/invoiceInstallments")` |
| Invoices not validated | `fusion_get("invoices", q="ValidationStatus='Needs revalidation'", fields="InvoiceNumber,Supplier,InvoiceAmount,ValidationStatus", limit=25)` |
| Invoices on hold | `fusion_get("invoiceHolds", fields="HoldId,InvoiceNumber,Supplier,HoldName,HoldReason,HoldDate,LineHeld", limit=25)`; add `q="ReleaseName IS NULL"` for unreleased holds |
| Open POs for a supplier | `fusion_get("purchaseOrders", q="Supplier='<SUPPLIER>' and StatusCode='OPEN'", fields="POHeaderId,OrderNumber,Supplier,SupplierSite,ProcurementBU,Status,Ordered,Total,CurrencyCode", limit=25)` |
| PO lines | `fusion_get("purchaseOrders/<POHeaderId>/child/lines", limit=50)` |
| Supplier details | `fusion_get("suppliers", q="Supplier LIKE '%<NAME>%'", limit=10)` - check `suppliers/describe` for field names |
| Requisitions | `fusion_get("purchaseRequisitions", limit=10)` with `fields=` from `purchaseRequisitions/describe` |
| Payments | `fusion_get("payablesPayments", limit=10)` with `fields=` from describe |

## Order-to-Cash

| Question | Call |
|---|---|
| Sales order by number | `fusion_get("salesOrdersForOrderHub", finder="findByOrderNumber;OrderNumber=<NUMBER>", fields="OrderKey,HeaderId,OrderNumber,SourceTransactionSystem,SourceTransactionId,StatusCode,OnHoldFlag,BuyingPartyName,TransactionalCurrencyCode")` |
| Order lines | `fusion_get("salesOrdersForOrderHub/<OrderKey>/child/lines", limit=50)` |
| Orders on hold | `fusion_get("salesOrdersForOrderHub", q="OnHoldFlag='true'", fields="OrderNumber,StatusCode,BuyingPartyName", limit=25)` (check the flag value with describe) |
| Customer open balance | `fusion_get("receivablesCustomerAccountActivities", finder="CustomerAccountActivitiesFinder;AccountNumber=<ACCOUNT>", fields="AccountId,AccountNumber,CustomerName,TotalOpenReceivablesForAccount")` |
| Open installments for that account | `fusion_get("receivablesCustomerAccountActivities/<AccountId>/child/transactionPaymentSchedules", q="InstallmentStatus='Open'", limit=50)` |
| AR invoices for a customer | `fusion_get("receivablesInvoices", finder="invoiceSearch;BillToCustomerNumber=<ACCOUNT>,InvoiceStatus=Complete", limit=25)` - read `InvoiceBalanceAmount` |
| Receipt by number | `fusion_get("standardReceipts", finder="StandardReceiptsFinder;ReceiptNumber=<NUMBER>")` |
| Customers (CRM API) | `fusion_get("accounts", api="crm", limit=10)` or `fusion_get("hubOrganizations", api="crm", limit=10)` |

## Shared

| Question | Call |
|---|---|
| Scheduled process status | `fusion_get("erpintegrations", finder="ESSJobStatusRF;requestId=<REQUEST_ID>")` |
| Journal batches | `fusion_get("journalBatches", limit=10)` with `fields=` from describe |
| What can a resource do? | `fusion_get("<resource>/describe")` - attributes, finders, children |
