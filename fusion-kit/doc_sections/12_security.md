## 12. Security, roles and controls for P2P and O2C

This section covers who can do what on which data in P2P and O2C, the predefined roles for each step, roles for integration and reporting users, segregation of duties (SoD), audit evidence, and security for AI agents. Role names come from the 26D Security Reference guides (Financials, Procurement, Order Management, SCM, Common). Role hierarchies change with each update, so check a role on the Security Console before you copy it.

### 12.1 Fusion security model in brief

Fusion grants nothing by default. Oracle: "By default, users are denied access to all data", and data security policies express "Who can do what on which set of data" ([Data Security, 26B](https://docs.oracle.com/en/cloud/saas/applications-common/26b/facsa/data-security.html)).

| Building block | Definition (Oracle) | What it means in P2P and O2C |
|---|---|---|
| Job role | "Represent the jobs that users perform in an organization" ([Role Types, 26D](https://docs.oracle.com/en/cloud/saas/applications-common/26d/facsa/role-types.html)) | Buyer, Accounts Payable Specialist, Order Entry Specialist. You assign job roles to users. |
| Abstract role | "Represent users in the enterprise independent of the jobs they perform" | Employee, Line Manager, Procurement Requester, Supplier Administrator |
| Duty role | "A logical collection of privileges that grant access to tasks that someone performs as part of a job" | Payables Invoice Creation, Purchase Order Authoring, Billing Management. You never assign a duty role straight to a user. |
| Aggregate privilege | Roles that "combine the functional privilege for an individual task or duty with the relevant data security policies" | Example: Review Accounts Payable Accounting Period Status |
| Function privilege | Grants access to a page, task, REST method or scheduled process | Force Approve Payables Invoice; Manage Scheduled Processes ([FAQ](https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/which-role-gives-me-access-to-the-scheduled-processes-work-area.html)) |
| Data security policy | "A grant of a set of privileges to a principal on an object or attribute group for a given condition". Conditions are "WHERE clauses that specify access within a particular dimension, such as by business unit" | Example: "An Accounts Payable Specialist can manage payables invoice for the business units for which they are authorized" ([AP Specialist, 26D](https://docs.oracle.com/en/cloud/saas/financials/26d/oafrm/Accounts_Payable_Specialist_job_roles.html)) |
| Security context (data access) | The "which" in "who can do what on which data". Financials contexts include Business Unit, Data Access Set, Ledger, Asset Book, Control Budget, Intercompany Organization, Reference Data Set and Legal Entity. SCM contexts include Inventory Organization, Cost Organization and Manufacturing Plant ([Data Access, 25C](https://docs.oracle.com/en/cloud/saas/applications-common/25c/facsa/data-access.html)) | You grant data access per user and job role with the Manage Data Access for Users task. It's stored in `FUN_USER_ROLE_DATA_ASGNMNTS` (columns `ORG_ID`, `LEDGER_ID`, `ACCESS_SET_ID`, `INV_ORGANIZATION_ID`, `DATASEC_CONTEXT_TYPE_CODE`) |
| Data access set | Grants "access to a ledger, ledger set, or specific primary balancing segment values", either read-only or read and write ([GL security, 26B](https://docs.oracle.com/en/cloud/saas/financials/26b/faigl/overview-of-general-ledger-security.html)) | GL users get data access sets through Manage Data Access Set Data Access for Users. Tables: `GL_ACCESS_SETS`, `GL_ACCESS_SET_ASSIGNMENTS` |
| Procurement agent | Users with "procurement job responsibilities" must be set up as procurement agents for a procurement BU ([agent security, 26D](https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-manage-procurement-agent-security.html)) | Task Manage Procurement Agents. Tables: `PO_AGENT_ASSIGNMENTS`, `PO_AGENT_ACCESSES`. REST: `/fscmRestApi/resources/11.13.18.05/procurementAgents` |

How a user gets access ([Data Access, 25C](https://docs.oracle.com/en/cloud/saas/applications-common/25c/facsa/data-access.html); [Assign Data Access, 26B](https://docs.oracle.com/en/cloud/saas/applications-common/26b/facsa/assign-data-access-to-users.html)):

1. Create the user on the Security Console or with the Manage Users task.
2. Assign job roles, either by hand or with role provisioning rules based on the work assignment.
3. Run Retrieve Latest LDAP Changes (a prerequisite in the 26B topic), then assign data access for each job role in Manage Data Access for Users, or define Data Provisioning Rules based on work assignments. To do this for many users at once, use the Authorize Data Access button, which exports the search results to an Excel spreadsheet that you fill in and upload, or REST `/fscmRestApi/resources/11.13.18.05/dataSecurities`. The REST attributes are `UserName`, `RoleNameCr`, `RoleCommonName`, `SecurityContext`, `SecurityContextValue` (and Value2, Value3) and `ActiveFlag`. "The role must be assigned to the user separately" ([POST dataSecurities, 26D](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-datasecurities-post.html)).
4. For procurement roles, also create the procurement agent with its actions and access levels for each procurement BU (table below).

Procurement agent access ([Procurement Agents, 26D](https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/procurement-agents.html)):

| Access actions (one set for each procurement BU) | Access to other agents' documents |
|---|---|
| Manage Requisitions; Manage Purchase Orders; Manage Purchase Agreements; Manage Negotiations; Manage Sourcing Programs; Manage Catalog Content; Manage Suppliers; Manage Supplier Qualifications; Manage Approved Supplier List Entries; Analyze Spend | None; View ("search and view"); Modify ("view, modify, delete, and withdraw"); Full (also "freeze, hold, close, cancel, and finally close"). An agent can always act on their own documents if they have access to the procurement BU. |

A buyer needs three things: the Buyer job role, business unit data access, and an agent record. If any one is missing, the user sees the work area but can't open documents.

### 12.2 Predefined job roles per P2P and O2C step

The descriptions are quoted or condensed from each role's page in the 26D Security Reference: [Financials](https://docs.oracle.com/en/cloud/saas/financials/26d/oafrm/overview-of-security-reference.html), [Procurement](https://docs.oracle.com/en/cloud/saas/procurement/26d/oapcm/overview-of-security-reference.html), [Order Management](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/farom/overview-of-security-reference.html), [SCM](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fammm/overview-of-security-reference.html) and [Common](https://docs.oracle.com/en/cloud/saas/applications-common/26d/oacsm/overview-of-security-reference.html). Duty names in the third column are directly inherited duties. Roles without a quoted description were not opened for this section, so review their hierarchy before you use them.

#### P2P

| Step | Role (guide) | What it can do in the cycle | Typical SoD caution |
|---|---|---|---|
| Requisition | Procurement Requester (Abstract Role, proc) | "Prepares requisitions for themselves". Requisition Self Service User, Receiving Management Requester, Payables Invoice Inquiry | It also allows self-service receiving. Don't combine it with Buyer for the same spend without approval rules. |
| Supplier onboarding | Supplier Administrator (Abstract Role, proc/fin) | "Manages supplier profile and user provisioning". Supplier Profile Management, Supplier Registration Management, Upload data for Supplier Import | Supplier maintenance plus invoice entry or payment is the classic fictitious-supplier risk |
| Sourcing and ordering | Buyer (Job Role, proc) | "Procurement professional responsible for transactional aspects of the procurement processes". Purchase Order Authoring and Control, Purchase Agreement Authoring and Control, Requisition Line Processing | The buyer should not approve their own PO, receive against it or maintain the supplier |
| Sourcing and ordering | Procurement Manager (Job Role, proc) | "Responsible managing a group of buyers". Inherits Buyer, Contract Terms and Conditions Override Controls and transaction analysis duties | Combines buying with override controls. Use agent access level Full only where it's needed. |
| Receiving | Receiving Agent (Job Role, scm) | "Receiving expected shipment lines, inspecting received lines, correcting received lines, and managing returns" | Receiving plus buying or invoicing lets one person confirm goods that were never delivered |
| Invoice | Accounts Payable Specialist (Job Role, fin) | "Enters invoices" and matches them to POs or receipts. Payables Invoice Creation, Import Payable Invoice Batch, Upload data for Payables Import, Supplier Profile Inquiry | Keep it apart from supplier maintenance and from payments |
| Invoice | Accounts Payable Invoice Supervisor (Job Role, fin) | "Responsible for creating accounts payable invoices". Payables Invoice Creation and Payables Invoice Processing (holds and approval) | Entering and releasing holds on the same invoice |
| Invoice and payment | Accounts Payable Supervisor (Job Role, fin) | Oversees specialists, "initiates and manages pay runs". Payables Invoice Creation, Payables Payment Creation, Payee Bank Account Management, Functional Setups | One predefined role holds invoice entry, payment creation and payee bank accounts. Split it into custom roles if SoD matters. |
| Payment | Accounts Payable Payment Supervisor (Job Role, fin) | "Managing accounts payable payments". Payables Payment Creation, Payables Payment Processing, Disbursement Process Management | Don't combine it with invoice entry or supplier bank maintenance |
| Payment | Payment Specialist (Job Role, fin) | Payment program eligibility, supplier offers, remittances. Payment Execution Management, Payment Options Management, Supplier Offers Management | Agent-assisted payments still need payment approval (section 10) |
| Payment and close | Accounts Payable Manager (Job Role, fin) | "Overrides exceptions" and analyzes balances. Payables Invoice Processing, Payables Payment Processing, Payables Period Close, Payee Bank Account Management | Oracle's own example: it holds Force Approve Payables Invoice (granted through its Payables Period Close duty) and payment privileges, so consider removing force approve ([Financials security considerations](https://docs.oracle.com/en/cloud/saas/financials/26d/facsf/other-financials-security-considerations.html)) |
| Bank reconciliation | Cash Manager (Job Role, fin) | Cash positioning, Bank Statement and Reconciliation, Import Bank Statement, Payments Disbursement Administration | Reconciling payments you also created or administer |
| Accounting, accruals | Cost Accountant (Job Role, scm) | "Performs cost and management accounting functions". Receipt Accounting Transaction Analysis, Cost Management Administration | Cost setup plus receipt or inventory adjustments |
| GL | General Accountant (Job Role, fin) | Records adjustments, accruals and revaluations. Journal Management, Import Journal, Intercompany Transactions Entry | Journal entry plus approval of the same journal |
| Supplier side | Supplier Sales Representative, Supplier Accounts Receivable Specialist (Job Roles, proc) | Supplier Portal users. You provision them through supplier user roles (REST `/fscmRestApi/resources/11.13.18.05/supplierUserRoles`) | Supplier users should only see their own supplier |

Other predefined P2P roles whose hierarchies were not reviewed here: Advanced Procurement Requester and Supplier Manager (Abstract Roles, proc); Category Manager and Procurement Contract Administrator (Job Roles, proc); Receiving Specialist (Job Role, scm); Tax Specialist and Tax Accountant (Job Roles, fin).

#### O2C

| Step | Role (guide) | What it can do in the cycle | Typical SoD caution |
|---|---|---|---|
| Credit | Credit Manager (Job Role, fin) | Defines "credit management policies and controls, and establishing credit limits" and authorizes credit exceptions. In 26D its only directly inherited duty is FSCM Load Interface Administration, so check its privilege list before you build on it. | Credit limit changes plus order entry or cash application for the same customer |
| Order capture | Order Entry Specialist (Job Role, om) | "Creating new orders, updating existing orders, and creating order returns". Upload data for Source Sales Order Import | Order entry plus pricing setup, credit release or billing |
| Fulfillment | Order Manager (Job Role, om) | Expedites fulfillment and "manages exceptions". Inherits Order Entry Specialist and the orchestration duties | Hold release on orders you entered yourself |
| Shipping | Shipping Agent (Job Role, om/scm) | "Records and processes outbound shipments including packing and labeling". Shipment Processing | Shipping plus inventory adjustments or billing |
| Billing | Billing Specialist Segregated Role (Job Role, fin) | "Managing customer billing". Billing Management, Payment Management Segregated ("except the creation and management of receipts"), Customer Maintenance Segregated ("except the creation and management of customers") | Oracle delivers it as the billing half of a split |
| Receipts | Accounts Receivable Specialist Segregated Role (Job Role, fin) | "Managing accounts receivable payments". Payment Management, Bill Management Segregated ("billing activities except the creation and management of invoices") | The cash half of the split |
| Billing and receipts | Accounts Receivable Specialist (Job Role, fin) | Customer payments and cash application, plus Billing Management, Customer Maintenance and Upload data for Receivables Import | It holds both invoicing and cash. Use the two Segregated roles where you need SoD. |
| AR oversight | Accounts Receivable Manager (Job Role, fin) | "Manages all accounts receivable activities, including defining policy and controls". Accounts Receivable Setup Maintenance, Billing Management, Customer Maintenance | It combines setup and transactions. An Accounts Receivable Manager Segregated Role also exists. |
| Collections | Collections Agent (Job Role, fin) | "The agent user in Collections". Collections Management Basic, Payment Settlement Management | Disputes or adjustments raised and approved by the same collector |
| Collections | Collections Manager (Job Role, fin) | "The management user in Collections". Collections Administration, Collections Management Advanced | Policy setup plus collector work |
| Revenue | Revenue Analyst (Job Role, fin) | Revenue adjustments, recognition, period open and close, transfer to GL | Adjusting revenue plus closing the period |
| COGS | Cost Accountant (Job Role, scm) | COGS and Gross Margin Transaction Analysis, Cost Accounting Close Workspace | As in P2P |

Other predefined O2C roles whose hierarchies were not reviewed here: Pricing Administrator, Pricing Manager and Pricing Analyst (Job Roles, om), where pricing setup combined with order entry is the risk; Shipping Manager and Warehouse Manager (Job Roles, scm); Billing Manager Segregated Role, Revenue Manager and Intercompany Accountant (Job Roles, fin).

#### Administration and oversight roles

| Role (guide) | Use | Caution |
|---|---|---|
| Financial Application Administrator, Procurement Application Administrator, Supply Chain Application Administrator (Job Roles) | Product setup | Keep them apart from transactional roles in production |
| Application Implementation Consultant (Job Role, common) | Full setup access | For implementation only. Remove it after go-live. |
| IT Security Manager (Job Role, common) | "Protects assets". Security Management, Manage Users, Payments Data Security Administration, Risk Administrator ([role](https://docs.oracle.com/en/cloud/saas/applications-common/26d/oacsm/IT_Security_Manager_job_roles.html)) | Never combine it with transactional roles |
| Internal Auditor (Job Role, common) | Audit History Viewer (View Audit History), Payables Administration, Receivables Administration, Receiving Administration ([role](https://docs.oracle.com/en/cloud/saas/applications-common/26d/oacsm/Internal_Auditor_job_roles.html)) | It inherits administration duties. A read-only custom role with Audit History Viewer only is often safer. |
| IT Auditor (Job Role, common) | Security Reporting, including Separation of Duties Role Analysis ([role](https://docs.oracle.com/en/cloud/saas/applications-common/26d/oacsm/IT_Auditor_job_roles.html)) | Good fit for SoD evidence |

### 12.3 Roles for integrations and reporting

#### Predefined roles and privileges

| Channel | Predefined role or privilege | Source |
|---|---|---|
| REST resources (general) | "You must have the necessary security roles and privileges to use the GET, POST, PATCH, and DELETE methods on your parent and child resources". "Authorization enforces access privileges by service role." | [Financials REST Quick Start, 26D](https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/Quick_Start.html) |
| REST resources (Procurement) | The Procurement REST privileges page lists, per resource and method, the function security privilege (for example View Purchase Order for GET purchaseOrders, Create Purchase Order for POST draftPurchaseOrders, View Supplier and Maintain Supplier for suppliers, Manage Procurement Agent by Web Service for procurementAgents) and the data security condition (for example "User is an active agent for the procurement business unit with access to manage purchase orders"). A 403 means a missing privilege. | [Procurement REST Roles and Privileges, 26D](https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/Roles_and_Privileges.html) |
| Procurement REST Service Duty | Oracle: it and its aggregate privileges "should not be given to user-defined, duty, or abstract roles that are assigned to end users", because they are for application-to-application integration "and give access to all data" | Same page |
| FBDI and ERP Integration Service | Duty FSCM Load Interface Administration ("Manages load interface file for import"). Its privileges: Access FSCM Integration Rest Service, Load File to Interface, Load Interface File for Import, Manage File Import and Export, Transfer File. You also need the "Upload data for <object> Import" duty and the import privilege for the object, for example Payables Invoice Import Submission. | [Financial Integration Specialist](https://docs.oracle.com/en/cloud/saas/financials/26d/oafrm/Financial_Integration_Specialist_job_roles.html) |
| Integration job roles | Financial Integration Specialist, Procurement Integration Specialist, Supply Chain Integration Specialist. Integration Specialist (common) inherits all three, plus the HCM, Project and Incentive Compensation integration specialist roles. Order Manager inherits Order Management Integration Specialist. | [Integration Specialist](https://docs.oracle.com/en/cloud/saas/applications-common/26d/oacsm/Integration_Specialist_job_roles.html), [Procurement](https://docs.oracle.com/en/cloud/saas/procurement/26d/oapcm/Procurement_Integration_Specialist_job_roles.html), [SCM](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/farom/Supply_Chain_Integration_Specialist_job_roles.html) |
| App-to-app access | ERP Application Integrator (Abstract Role). It "allows appropriate access between ERP and other target systems" and inherits the Attachments Administrator and Shared Attachments Administrator content roles. Oracle: "End users or automated jobs should not be allowed to use this role for accessing ERP objects and data". | [role](https://docs.oracle.com/en/cloud/saas/financials/26d/oafrm/ERP_Application_Integrator_job_roles.html) |
| ESS jobs | Manage Scheduled Processes privilege plus the privilege for each process | [FAQ](https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/which-role-gives-me-access-to-the-scheduled-processes-work-area.html) |
| OTBI | Transaction Analysis duties (for example Payables Invoice Transaction Analysis) inherit BI Consumer Role. BI Author Role "Creates and edits reports". BI Administrator Role is a "superuser role". | [BI roles](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fassc/business-intelligence-roles-explained.html); section 8.1.3 |
| BI Publisher | A SQL data model that reads base tables isn't filtered by data security (section 8.2.6). Treat BI Publisher Data Model Developer Role as privileged. | section 8.2.6 |
| BICC | A custom role (for example BIACM_ADMIN) that inherits both ORA_ASM_APPLICATION_IMPLEMENTATION_ADMIN_ABSTRACT ("access to global offerings and data stores or jobs") and ESS Administrator Role (schedules); or, instead, BI Administrator Role. Extract files on UCM need a role with OBIA_EXTRACTTRANSFORMLOAD_RWD (8.3.1) | [BICC provisioning, 26D](https://docs.oracle.com/en/cloud/saas/applications-common/26d/biacc/provision-a-user-with-access-to-bicc.html); [BICC provisioning, 26C](https://docs.oracle.com/en/cloud/saas/applications-common/26c/biacc/provision-a-user-with-access-to-bicc.html) |

#### Designing a least-privilege integration role

Oracle's Access Governance guidance offers default roles or a custom role for a service user, and calls the custom role the one that "follows the principle of least privilege because it grants only the fine-grained privileges required" ([Access Governance](https://docs.oracle.com/en-us/iaas/Content/access-governance/prepare-fusion-cloud-apps-for-integration.htm)).

| Rule | How |
|---|---|
| One user per integration | Name it `<SYSTEM>_<FLOW>_INT` and record its owner. Never share it with people or other agents. |
| Start empty | Create a custom job role with no inherited job roles. Don't copy Integration Specialist, which inherits every integration specialist role. |
| Add only the duties for the flow | Example for an AP invoice inbound flow: FSCM Load Interface Administration, Upload data for Payables Import, Payables Invoice Import Submission, Payables Invoice Inquiry. Leave out Payee Bank Account Management even though Financial Integration Specialist includes it. |
| Read-only flows | Add only the inquiry duties (for example Payables Invoice Inquiry, Purchase Order Inquiry, Receivables Inquiry) or Transaction Analysis duties |
| Data access | Grant only the business units, ledgers (data access sets) and inventory organizations the flow needs, through `dataSecurities` or Manage Data Access for Users. For procurement objects, add an agent record that includes only the access actions you need. |
| Authentication | Use OAuth tokens from the OCI IAM identity domain, not shared passwords. Fusion REST paths take user-based grants (Authorization Code, JWT User Assertion); Client Credentials works only for the Spectra `/api/...` resources (section 6.1). Rotate and vault the secrets. |
| Separate write from read | Use separate users for inbound loads and for extracts, so that someone who can read every BU can't also load data |
| Test with a real user | Check the access with the custom role and its data assignments on a test pod. A missing data security grant does not fail loudly: "The API calls return a 200 OK response, but the count is 0" ([Access Governance](https://docs.oracle.com/en-us/iaas/Content/access-governance/prepare-fusion-cloud-apps-for-integration.htm)). Oracle also warns that "using predefined roles might account for subscription consumption" ([AI Agent Studio access, 26B](https://docs.oracle.com/en/cloud/saas/fusion-ai/26b/aiaas/access-ai-agent-studio.html)) |

### 12.4 Segregation-of-duties conflicts in P2P and O2C

Oracle's example of a conflict is a user who has Create Payments and Approve Invoice. The predefined Accounts Payable Manager has Force Approve Invoices and Create Payments ([Financials security considerations](https://docs.oracle.com/en/cloud/saas/financials/26d/facsf/other-financials-security-considerations.html)). The table below lists the typical conflicts. The duties are taken from the role pages in 12.2.

| # | Conflict | Duties or privileges in conflict | Predefined roles that already combine them | Risk |
|---|---|---|---|---|
| 1 | Maintain supplier or bank account vs enter invoice | Supplier Profile Management or Payee Bank Account Management vs Payables Invoice Creation | Accounts Payable Supervisor (Payee Bank Account Management plus invoice creation) | Fictitious supplier, diverted payment |
| 2 | Enter invoice vs pay | Payables Invoice Creation vs Payables Payment Creation | Accounts Payable Supervisor | Pay your own invoice |
| 3 | Approve or force approve invoice vs pay | Force Approve Payables Invoice vs payment privileges | Accounts Payable Manager | Bypassing approval |
| 4 | Create PO vs receive | Purchase Order Authoring vs Receive Goods Using Responsive Receiving | None (Buyer plus Receiving Agent) | Payment for goods that were never delivered |
| 5 | Create PO vs enter invoice | Purchase Order Authoring vs Payables Invoice Creation | None | Matching to your own PO |
| 6 | Requisition vs buy | Requisition Self Service User vs Purchase Order Authoring | None (Procurement Requester plus Buyer) | Uncontrolled spend |
| 7 | Payments vs bank reconciliation | Payables Payment Processing vs Bank Statement and Reconciliation | None (Payment Supervisor plus Cash Manager) | Hiding an unauthorized payment |
| 8 | Billing vs cash application | Billing Management vs Payment Management | Accounts Receivable Specialist, Accounts Receivable Manager | Lapping, write-offs that hide theft. Oracle delivers the Segregated roles for this split. |
| 9 | Credit limits vs order entry | Credit management vs order entry | None (Credit Manager plus Order Entry Specialist) | Orders released beyond the risk policy |
| 10 | Pricing setup vs order entry | Pricing administration vs order entry | None | Unauthorized discounts |
| 11 | Shipping vs billing or inventory adjustment | Shipment Processing vs billing or inventory duties | None | Shipping without billing |
| 12 | Revenue adjustment vs period close | Revenue adjustments vs Review Revenue Management Accounting Period Status | Revenue Analyst | Moving revenue between periods |
| 13 | Security administration vs any transaction role | Security Management, Manage Users vs any P2P or O2C duty | None | Granting yourself access |
| 14 | Broad integration user | Upload data for many imports, Payee Bank Account Management, receipt imports | Financial Integration Specialist | One credential can create suppliers' bank accounts, invoices and receipts |

Monitoring with Oracle Risk Management ([Overview of Advanced Controls, 26A](https://docs.oracle.com/en/cloud/saas/risk-management-and-compliance/26a/faacm/overview-of-oracle-advanced-controls.html)):

| Component | What it does |
|---|---|
| Advanced Access Controls | "Identifies users with sensitive-access and separation-of-duties conflicts". In access models, filters "designate roles or privileges that, individually or in combination, would allow an individual user to complete risky behaviors" |
| Advanced Financial Controls | "Detects fraud, error, and other risk in transactions", or in change tracking from the Oracle Cloud audit framework (12.5). Example: a supplier bank account changed shortly before a payment (verify which models your content library delivers). |
| Models vs controls | A model returns temporary results. A control returns violations that persist as incidents, and each incident has a result investigator. |
| Preventive checks | Provisioning rules "identify pairs of conflicting roles". Advanced Access Requests runs SoD and sensitive-access analysis in the role-request workflow, "only if one or more access controls are active", and skips it for temporary-access requests. The reviewer's judgment "isn't binding"; the approver decides ([Advanced Access Requests, 26B](https://docs.oracle.com/en/cloud/saas/risk-management-and-compliance/26b/faacm/overview-of-advanced-access-requests.html)) |

Procurement has a special case: "For certain privileges to grant functional access, a user must have the privilege and a corresponding 'action' as a 'procurement agent' for a business unit. Access models and controls exclude users granted these privileges without corresponding procurement-agent actions." Example: Create Purchase Agreement works only with the Manage Purchase Agreements action in that BU; Generate Purchase Order needs Manage Purchase Orders and Manage Requisitions ([Exclusions Involving Procurement Agents, 25C](https://docs.oracle.com/en/cloud/saas/risk-management-and-compliance/25c/faacm/exclusions-involving-procurement-agents.html)). So the agent setup in 12.1 is part of every procurement SoD analysis. Advanced Controls is a separate subscription (verify your license). If you don't have it, use the IT Auditor role's Separation of Duties Role Analysis and the evidence queries in 12.5.

### 12.5 Audit and evidence

#### Business object audit setup

| Item | Fact |
|---|---|
| Enable | Setup and Maintenance > Manage Audit Policies. Set the audit level for Oracle Fusion Applications to Auditing, then Configure Business Object Attributes for a product, for example Payables or Supplier Model ([Supplier audit, 26D](https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/supplier-profile-audit-history-setup-and-reporting.html)) |
| Privilege to configure | Manage Audit Policies ([Audit Policies](https://docs.oracle.com/en/cloud/saas/human-resources/faucf/audit-policies.html)). The supplier guide says the setup page is available to the Application Administrator job role. |
| View | Navigator > Tools > Audit Reports. You need the View Audit History privilege ([Audit reports FAQ](https://docs.oracle.com/en/cloud/saas/sales/fasqa/how-do-i-view-audit-reports.html)), which Internal Auditor has through Audit History Viewer (it also grants View Audit Setup). The supplier guide states that only users with the Internal Auditor job role can access the Audit Reports page, so a custom role needs View Audit History. Show Attribute Details shows old and new values. PII attributes only appear for users with PII privileges. Oracle notes that searching periods longer than a month may affect performance. |
| What's recorded | Payables: "update and delete operations performed by the user". Data updated by a scheduled process isn't recorded. By default only `VENDOR_ID` and `VENDOR_SITE_ID` on invoices are audited ([Payables transaction business objects, 26B](https://docs.oracle.com/en/cloud/saas/financials/26b/faipp/payables-transaction-business-objects.html)). Changes are only recorded after you enable auditing. |
| P2P objects | Payables: Invoice, Invoice Lines, Invoice Distributions, Invoice Installments, Payment Process Request Templates and others. Supplier Model: supplier, addresses, contacts, sites, site assignments, and supplier bank accounts at supplier, address and site level (Country, Bank Name, Account Number, IBAN and other attributes; account owners, intermediate accounts and attachments are excluded). If masking is enabled, Bank Account Number and IBAN show only masked values in audit history. |
| Changes to the setup | Disabling an object or attribute is "prospective and not retrospective"; history for periods when it was enabled stays reportable ([Supplier audit, 26D](https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/supplier-profile-audit-history-setup-and-reporting.html)) |
| Retention | Oracle: "there's no specified retention period for the audited data or the logs. Follow your company policy for retaining or removing such data" ([Audit Policies, Using Common Features for HCM](https://docs.oracle.com/en/cloud/saas/human-resources/faucf/audit-policies.html)). Export the evidence (Audit Reports to Excel, or REST) for each audit period. |

Audit shadow tables: an audit table has the same name as its base table plus a trailing underscore. The 26D catalogs list 1,126 of them. Examples in scope: `AP_INVOICES_ALL_`, `AP_INVOICE_LINES_ALL_`, `AP_INVOICE_DISTRIBUTIONS_ALL_`, `AP_PAYMENT_SCHEDULES_ALL_`, `POZ_SUPPLIERS_`, `POZ_SUPPLIER_SITES_ALL_M_`, `IBY_EXT_BANK_ACCOUNTS_`, `CE_BANK_ACCOUNTS_`, `HZ_PARTIES_`, `HZ_CUST_ACCOUNTS_`, `HZ_CUST_ACCT_SITES_ALL_`, `FUN_USER_ROLE_DATA_ASGNMNTS_` (data access changes), `GL_ACCESS_SETS_`, `FND_GRANTS_`. Their columns aren't in the companion workbook. Read them through Audit Reports or the REST service, and check the columns in your pod before you write SQL against them.

Audit REST service (REST API for Common Features, 26D):

| Operation | Path |
|---|---|
| Get an audit report | `POST /fscmRestApi/fndAuditRESTService/audittrail/getaudithistory` ([doc](https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/op-fscmrestapi-fndauditrestservice-audittrail-getaudithistory-post.html)). Inputs are path and query parameters, not a documented body: paging `pageNumber` and `pageSize`; required `fromDate`, `toDate` (`yyyy-MM-dd` or `yyyy-MM-dd HH:mm:ss`) and `product` (a predefined value listed in `FND_AUDIT_WEBAPP_AM`); optional `businessObjectType` (fully qualified view object name), `user`, `eventType`, `attributeDetailMode`, `includeAttributes`, `includeChildObjects`, `timeZone`. "You can retrieve audit history for up to one month" per call. The doc example sends the values as JSON, so test both forms in your pod. |
| Audit setup and level | `POST .../audittrail/get-auditsetup`, `get-auditlevel`, `set-auditlevel`, `check-auditstatus`, `update-auditstatus` |

#### Approval, action and history tables

| Table | Evidence it holds (catalog description) |
|---|---|
| `PO_ACTION_HISTORY` | One row for each approval or control action on a PO, agreement, release or requisition. `ROLE_CODE` is BUYER, REQUESTER, APPROVER, CAT_ADMIN or SUPPLIER. `PERFORMER_ID` is a person ID, or a party ID for suppliers. |
| `POZ_APPROVAL_HISTORY` | Approvals of supplier registrations, spend authorizations and profile changes. Kept "even after SOA approval data is purged". |
| `PON_ACTION_HISTORY`, `PON_NEG_AUDIT_ACTIVITIES` | Buyer actions on negotiations and the negotiation life cycle |
| `AP_INV_APRVL_HIST_ALL` | Invoice approval and rejection history, one row for each approver. `APPROVER_ID` is the login user name. |
| `AP_DOC_SEQUENCE_AUDIT`, `AR_DOC_SEQUENCE_AUDIT` | Document sequence numbers assigned. Use them to prove there are no gaps. |
| `AP_PAYMENT_HISTORY_ALL` | Clearing and maturity history of payments |
| `CE_RECON_HISTORY` | Bank reconciliation history |
| `AR_APPROVAL_ACTION_HISTORY` | Each status change of a pending adjustment |
| `AR_CMGT_APPROVAL_HISTORY` | Approval history of credit case folders |
| `AR_CASH_RECEIPT_HISTORY_ALL`, `AR_DISPUTE_HISTORY`, `AR_TRANSACTION_HISTORY_ALL` | Receipt life cycle, dispute amount changes, bills receivable events |
| `VRM_CUSTOMER_CONTRACT_AUDIT`, `VRM_MEA_DOC_ACTION_HISTORY` | Revenue contract attribute changes (old and new values) and arrangement actions |
| `DOO_TASK_STATUS_HISTORY`, `DOO_AGENT_ACTION_HISTORY` | Order task status transitions, and "audit records for agent action requests across object types" (12.6) |
| `FUN_WF_HISTORY` | Approval history of Financials common workflow submissions |
| `PO_AGENT_ACCESSES`, `FUN_USER_ROLE_DATA_ASGNMNTS` | Current agent access and data access, used for access reviews |

#### Evidence queries

Run these read-only queries in a BI Publisher data model owned by audit (section 8.2). They read base tables, so they ignore data security. Restrict the report to auditors.

Invoices approved by the user who created them:

```sql
SELECT inv.INVOICE_NUM, inv.ORG_ID, inv.INVOICE_AMOUNT, inv.CREATED_BY,
       h.APPROVER_ID, h.RESPONSE, h.ACTION_DATE
FROM   AP_INVOICES_ALL inv
JOIN   AP_INV_APRVL_HIST_ALL h ON h.INVOICE_ID = inv.INVOICE_ID
WHERE  UPPER(h.APPROVER_ID) = UPPER(inv.CREATED_BY)
AND    UPPER(h.RESPONSE) LIKE '%APPROV%'      -- check RESPONSE values in your pod
AND    inv.CREATION_DATE >= :p_from_date;
```

Purchase orders approved by their own buyer:

```sql
SELECT ph.SEGMENT1 AS po_number, ph.PRC_BU_ID, ph.AGENT_ID,
       ah.ACTION_CODE, ah.ACTION_DATE, ah.SEQUENCE_NUM
FROM   PO_HEADERS_ALL ph
JOIN   PO_ACTION_HISTORY ah ON ah.OBJECT_ID = ph.PO_HEADER_ID
WHERE  ah.OBJECT_TYPE_CODE = :p_po_object_type   -- purchase order document type value; check in your pod
AND    ah.ROLE_CODE = 'APPROVER'
AND    ah.PERFORMER_ID = ph.AGENT_ID;
```

Data access review (for each user GUID, role and context):

```sql
SELECT d.USER_GUID, d.ROLE_NAME, d.DATASEC_CONTEXT_TYPE_CODE,
       d.ORG_ID, d.LEDGER_ID, d.ACCESS_SET_ID, d.INV_ORGANIZATION_ID,
       d.LAST_UPDATED_BY, d.LAST_UPDATE_DATE
FROM   FUN_USER_ROLE_DATA_ASGNMNTS d
WHERE  d.ACTIVE_FLAG = 'Y'
ORDER  BY d.USER_GUID, d.ROLE_NAME;
```

To resolve user names, use the Security Console or `GET /fscmRestApi/resources/11.13.18.05/dataSecurities`, which returns `UserName`.

Procurement agents with both supplier and PO actions in the same BU (pass the two action codes from the Purchasing lookup named in the `ACCESS_ACTION_CODE` column comment):

```sql
SELECT a.AGENT_ID, a.PRC_BU_ID,
       LISTAGG(a.ACCESS_ACTION_CODE, ', ') WITHIN GROUP (ORDER BY a.ACCESS_ACTION_CODE) AS actions,
       MAX(a.ACCESS_OTHERS_LEVEL_CODE) AS others_level
FROM   PO_AGENT_ACCESSES a
WHERE  a.ALLOWED_FLAG = 'Y'
AND    a.ACTIVE_FLAG = 'Y'
GROUP  BY a.AGENT_ID, a.PRC_BU_ID
HAVING SUM(CASE WHEN a.ACCESS_ACTION_CODE IN (:p_supplier_action, :p_po_action) THEN 1 ELSE 0 END) = 2;
```

### 12.6 Securing AI agents

#### Oracle agents run under the user's security

| Statement | Source |
|---|---|
| "AI agents adhere to the native security and role-based access controls of Fusion Applications". You can limit an agent to selected business objects and fields. | [Get Started with AI Agent Studio, 26C](https://docs.oracle.com/en/cloud/saas/fusion-ai/26c/aiaas/get-started.html) |
| Payments Agent "respects Oracle Fusion Cloud Financials security and data access controls". Users only see their authorized BUs. | [Payments Agent FAQ](https://docs.oracle.com/en/cloud/saas/financials/fappa/does-payments-agent-respect-business-unit-security.html) |
| Payables Agent: "Don't assume page access is enough for users to see invoice data", "Don't assume classic Payables role inheritance applies to Payables Agent pages", and run permission-group processing after role or BU changes | [Payables Agent best practices](https://docs.oracle.com/en/cloud/saas/financials/fafpa/follow-security-best-practices.html) |
| Payables Agent duties come in Processing and Inquiry pairs: Payables Invoice Documents Processing Duty and Inquiry Duty, Payables Invoice Configuration Processing Duty and Inquiry Duty, Payables Invoice Processing Duty and Inquiry Duty; plus Payables Agent Insights Duty and Payables Agent Monitoring Prompt Management Duty. Note the name overlap with the classic Payables Invoice Inquiry duty in 12.2. | [Payables Agent duty roles](https://docs.oracle.com/en/cloud/saas/financials/fafpa/payables-agent-duty-roles.html); codes in section 10 |
| Users of agents built in AI Agent Studio (path for HCM, Procurement, Sales, Service and SCM users without SCM job roles): a custom role with permission groups enabled, Access Intelligent Agent Chat (HRC_ACCESS_AI_AGENT_CHAT_PRIV) and Fai Genai Agent Runtime Duty (ORA_DR_FAI_GENERATIVE_AI_AGENT_RUNTIME_DUTY). Add the role on the workflow's Settings > Security tab and the application's Security Roles list, then publish both. Users with predefined SCM job roles (the FAQ lists, among others, ORA_DOO_ORDER_MANAGER_JOB, ORA_FOM_ORDER_ENTRY_SPECIALIST_JOB, ORA_RCV_RECEIVING_AGENT_JOB, ORA_WSH_SHIPPING_AGENT_JOB, ORA_CST_COST_ACCOUNTANT_JOB, ORA_QP_PRICING_ADMINISTRATOR_JOB) need permission groups enabled on those roles and the roles added to the workflow and application. All paths need the site-level profile option ORA_HCM_VBCS_PWA_ENABLED set to Y. | [Access FAQ](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiaqa/how-can-i-give-users-access-to-ai-agents.html) |
| External REST tools need Create and Edit Backends for Visual Builder Studio (ORA_FND_TRAP_PRIV). Workflow scheduling needs Fai Batch Job Manager Duty (ORA_DR_FAI_BATCH_JOB_MANAGER_DUTY). Monitoring needs read:Generative AI Workflow Execution. | [Access AI Agent Studio, 26B](https://docs.oracle.com/en/cloud/saas/fusion-ai/26b/aiaas/access-ai-agent-studio.html) |
| Human in the loop: a review step "for oversight and control over key actions, such as sending an email or updating a record". Payments Agent: actions that create or modify transactions "require user confirmation". | [Get Started](https://docs.oracle.com/en/cloud/saas/fusion-ai/26c/aiaas/get-started.html); section 10 |

Oracle agents therefore can't widen a user's access. The SoD conflicts in 12.4 still apply, because an agent can act on everything the user's roles allow. Even the predefined Accounts Payable Specialist role includes view-only data security on the AI Agent, AI Agent Tool and AI Agent Workflow objects for Financials agents, through the Financials Intelligent Agent Runtime role ([AP Specialist](https://docs.oracle.com/en/cloud/saas/financials/26d/oafrm/Accounts_Payable_Specialist_job_roles.html)).

Agent actions in Order Management leave their own audit trail in `DOO_AGENT_ACTION_HISTORY` ("audit records for agent action requests across object types"). Its column comments describe `AGENT_CODE`, `AGENT_EXECUTION_MODE` (for example HUMAN_ASSIST, AUTO), `USER_ACTION_CODE`, `OBJECT_TYPE`, `CONVERSATION_ID`, `TRACE_ID`, `JOB_ID` and `CHANGE_DETAIL_JSON` (before and after values), plus the Who columns. Which agents write to it is not documented; check in your pod.

#### External agents (Claude Code, MCP servers, scripts)

An external agent has no Fusion session of its own. It calls REST, the ERP Integration Service or BI reports as an integration user (section 11), so the controls are the controls on that user.

| Control | Practice |
|---|---|
| Identity | One integration user for each agent and environment, for example `<AGENT>_<ENV>_INT`. Authenticate with OAuth from the OCI IAM identity domain. Never use a person's account and never use ERP Application Integrator (Oracle says it's not for "automated jobs"). |
| Function security | A custom role built as in 12.3. Start with inquiry and Transaction Analysis duties. Add write duties for one flow at a time. Never give it Procurement REST Service Duty, which gives access to all data (12.3). |
| Data security | Only the BUs, ledgers and inventory organizations the use case needs. For procurement, add an agent record with View access to others' documents unless writes are required. |
| SoD | Check the integration user's role against the conflict table in 12.4 like any other user. Never give one agent user both the "create" and the "approve or pay" side. |
| Write gate | Writes (POST, PATCH, actions such as invoice validation or receipt application) only after human confirmation in the agent client. Use FBDI loads to test pods first. Keep approvals in Fusion workflow. Don't use force approve. |
| Read gate | Prefer secured paths: REST, OTBI (`/fscmRestApi/resources/11.13.18.05/analytics`, section 8.1.4) or parameterized BI reports. Never give an agent a free-form SQL data model (section 8.2.6). |
| Secrets | Keep tokens in a vault or the OS keychain, never in prompts, MCP configuration committed to Git, or log files |
| Evidence | The Who columns (`CREATED_BY`, `LAST_UPDATED_BY`) record "the user who created the row" or last updated it, so the integration user's name appears on what it writes. Whether REST and import changes reach the audit trail depends on the object (Payables auditing excludes data changed by scheduled processes, 12.5); verify in your pod. Keep the agent's own tool-call log with the Fusion request IDs so that you can tie each change to a prompt. |
| Review | Include agent users in quarterly access certification. Disable the user when the agent is retired. |
