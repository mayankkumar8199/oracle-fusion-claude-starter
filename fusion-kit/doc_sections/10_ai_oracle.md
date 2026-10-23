## 10. Oracle's agentic AI for P2P and O2C

Status 2026-10-21, update 26D. An update label (25C to 26D) is the update in which Oracle's What's New or the guide *Which Fusion Applications features use AI?* ([ERP](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiafl/ai-erp.html), [SCM](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiafl/ai-scm.html)) first documents a capability. Oracle delivers three layers: prebuilt agents and agentic apps, the AI Agent Studio platform, and embedded predictive or generative features. Default-on agents can still depend on Oracle-managed components: if a page says access "requires technology components managed by Oracle", log a service request that names the agent ([Payables 26B](https://docs.oracle.com/en/cloud/saas/readiness/erp/26b/fins26b/26B-fin-wn-f43769.htm)). Roles and SoD are in section 12; Claude Code is in section 11.

### 10.1 Oracle AI Agent Studio for Fusion Applications

AI Agent Studio is "a design-time environment" to "create, configure, validate, and deploy AI agents". It is integrated with Fusion knowledge stores, tools and APIs and applies Fusion security (Navigator > Tools > AI Agent Studio). Facts in 10.1 come from *How do I use AI Agent Studio?* 26D, G59779-03 ([PDF](https://docs.oracle.com/en/cloud/saas/fusion-ai/26d/aiaas/how-do-i-use-ai-agent-studio.pdf)) unless another link is given.

#### 10.1.1 Building blocks

| Artifact | Purpose and notes |
|---|---|
| Workflow | Deployable unit of agents and nodes; embedded in pages or started by webhook, email, schedule or signal |
| Agent | LLM worker of type user-proxy, supervisor or specialist; an agent created inside a workflow can't be reused |
| Topic | Reusable instructions and guardrails; Oracle prefers editing topics over system prompts |
| Agentic application | Workspace that bundles workflows, knowledge and controls, for example Collector Workspace |
| Fusion Claw (26D) | Execution layer for outcome-driven apps; modes Research (no data changes) and Full Auto; asks for approval where configured and keeps an auditable record of each run |
| Supporting resources | Approvals (approval processes), Signals (event contracts), Functions (JavaScript for Code nodes), Credentials (LLMs, mailboxes, data source applications, CLI) |

Seeded workflows and apps can't be edited; use Duplicate. Product agent templates are instantiated with Copy Template (suffix on every artifact) or Use Template (step by step) ([PO Status Advisor 26B](https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/proc26b/26B-procurement-wn-f42955.htm)).

#### 10.1.2 Tools, nodes and triggers

| Tool | Use | Notes |
|---|---|---|
| Business Object | Read, create, update or delete Fusion records; you choose objects and fields | Fusion role and data security apply; the guide's examples define business objects over REST resources and finders (section 6) |
| Document (RAG) | Search uploaded documents | Ready to Publish starts Process Agent Documents, then status Published; 25 MB per file, about 20 files per document |
| Email; Deep Link | Send templated email; open the Fusion page that performs an update | Email supports Require Human Approval |
| External REST | Call HTTPS APIs with authentication, endpoints and headers | Privilege Create and Edit Backends for Visual Builder Studio (ORA_FND_TRAP_PRIV) |
| MCP | Use tools on an external MCP server | Transport SSE or StreamableHTTP; since 26A ([26A](https://docs.oracle.com/en/cloud/saas/readiness/common/26a/common26a/26A-common-wn-f42183.htm)) |
| Connector | SharePoint, web pages, Microsoft Teams, Slack | Teams and Slack need ORA_DR_FAI_GENERATIVE_AI_AGENT_COLLAB_TOOLS_DUTY |

Nodes come in five groups: AI (Agent, LLM, Multi Agent, RAG Document Tool, Workflow), Communication (Send Email, Publish Signal), Data (Business Object Function, Document Processor, External REST, Vector DB Reader and Writer, and others), Logic (Code, Set Variables, Policy Nodes) and Workflow Control (Human Approval, If Condition, Switch, Parallel, loops, Wait, Return). Triggers: Webhook, Email (one inbound mailbox per workflow), Schedule (needs ORA_DR_FAI_BATCH_JOB_MANAGER_DUTY) and Signals.

#### 10.1.3 Models

| Item | 26D position |
|---|---|
| Oracle-provided | Basic: GPT-OSS 120B. Balanced: GPT-5.6 Luna (default), Gemini 3.1 Flash-Lite, GPT-4o speech models. GPT-4.1 mini and GPT-5 mini are deprecated and retire in 27B. A Frontier type is defined but no Frontier model is listed (check the LLM subtab in your pod) |
| Bring your own LLM | OpenAI (Azure or direct API), Gemini Enterprise Agent Platform (Vertex AI), Google Gemini (direct API), Anthropic (Google Vertex AI), OCI; add under Credentials > LLM; other models by service request (two to four weeks). Provider credentials, cost and model lifecycle are yours |
| Scope | Workflow Settings > LLM, or per LLM, Agent and Document Processor node |

Embedded features outside the studio use LLMs from providers such as Cohere, Meta and OpenAI; Oracle points to KB796229 on My Oracle Support for the current list ([LLM FAQ 26C](https://docs.oracle.com/en/cloud/saas/fusion-ai/26c/aiaas/which-large-language-models-llms-are-currently-used-or-supported-for-ai-agents.html)).

#### 10.1.4 Human in the loop and monitoring

| Control | How it works |
|---|---|
| Require Human Approval | Tool flag (External REST, Email, Document): a reviewer approves before the tool runs |
| Human Approval node | Routes through a published approval process (levels, approver types, rules written in plain language); the workflow pauses until the outcome |
| Monitoring and Evaluation tab | Session traces with every tool call and token count, drafts included; evaluation sets with pass/fail thresholds and run comparison; inbound email and schedule activity; Value dashboard. Metrics include error rate, P50 and P99 latency, tokens, AI Units, correctness, groundedness and relevance |
| Prerequisites | Schedule Aggregate AI Agent Usage and Metrics; to see records, grant the permission group read:Generative AI Workflow Execution with security view AllRowsRestrictedFields |
| Build and release | Debugger (breakpoints, step-through, pinned node output) and Playground; migration of workflows, apps and supervisor agents between instances; CI/CD; AI Studio CLI |

#### 10.1.5 Who can build and who can use

| Purpose | Roles (codes) |
|---|---|
| Build in all families | Family administrator duties (`ORA_DR_FAI_GENERATIVE_AI_AGENT_<FAMILY>_ADMINISTRATOR_DUTY`, for example FIN, PRC, SCM) plus Manage All Intelligent Agents (ORA_FAI_MANAGE_ALL_AI_AGENTS) |
| Build Financials agents | ORA_FUN_MANAGE_FIN_AI_AGENT, ORA_FUN_MANAGE_FIN_AI_AGENT_HCM, ORA_CSO_CONNECTORS_AI_AGENT_MANAGEMENT_DUTY and the FIN administrator duty; or permission groups on ORA_FUN_FINANCIAL_APPLICATION_ADMINISTRATOR_JOB |
| Build Procurement agents | ORA_PO_PRC_AI_AGENT_MANAGEMENT_DUTY, ORA_PO_PRC_AI_AGENT_MANAGEMENT_DUTY_HCM and the PRC administrator duty; or permission groups on ORA_PO_PROCUREMENT_APPLICATION_ADMIN_JOB |
| Build SCM agents | ORA_RCS_SCM_AI_AGENT_MANAGEMENT_DUTY, ORA_RCS_SCM_AI_AGENT_MANAGEMENT_DUTY_HCM and the SCM administrator duty; or permission groups on ORA_RCS_SUPPLY_CHAIN_APPLICATION_ADMINISTRATOR_JOB |
| Use Studio-built agents | Access Intelligent Agent Chat (HRC_ACCESS_AI_AGENT_CHAT_PRIV) and Fai Genai Agent Runtime Duty (ORA_DR_FAI_GENERATIVE_AI_AGENT_RUNTIME_DUTY); add the role on the workflow Security tab and the app Security Roles list ([access FAQ](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiaqa/how-can-i-give-users-access-to-ai-agents.html)). Prebuilt finance agents use assistant duty roles (10.2) |

Oracle warns that "using predefined roles might account for subscription consumption".

#### 10.1.6 Data handling and cost

| Topic | Oracle's statement |
|---|---|
| Isolation | Partitioned platform instance per customer; "your information won't be persisted or used to train models" ([AI Q&A, G22516-32](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiaqa/questions-and-answers.pdf)) |
| Location | GenAI input and output may be processed "outside of the local OCI region"; each data center maps to OpenAI endpoints in the USA or in Europe (EEA + Switzerland) ([endpoint table](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiaqa/where-are-the-locations-of-the-openai-endpoints-for-ai-agents-in-fusion-applications.html)). The 26B finance agent pages say GenAI services are available in the commercial realm (OC1) and reach other regions as they roll out |
| Retention | Profile option Retention period for Generative AI Data (ORA_FAI_DATA_RETENTION_DAYS), Site level, 90 to 365 days, default 90; older data is deleted automatically ([AI Q&A](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiaqa/questions-and-answers.pdf)) |
| Cost | AI Agent Studio is "Available at no additional cost" ([2026-07-14](https://www.prnewswire.com/news-releases/oracle-introduces-ai-native-builder-experience-to-create-and-run-agentic-applications-in-oracle-fusion-applications-302824977.html)); token consumption is measured for premium LLMs ([2025-10-15](https://www.prnewswire.com/news-releases/oracle-expands-ai-agent-studio-for-fusion-applications-with-new-marketplace-llms-and-vast-partner-network-302584282.html)) and shown as AI Units; BYOLLM and code-assistant subscriptions are separate. No price for the prebuilt finance agents was found (verify with Oracle) |

### 10.2 Prebuilt agents for P2P and O2C (status 2026-10-21)

The 26D Financials What's New lists the finance agents under ERP Agents ([26D contents](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/toc.htm)); adoption guides are on the [Financials 26D AI Agents page](https://docs.oracle.com/en/cloud/saas/financials/26d/agents.html). On 2026-04-09 Oracle called Collectors Workspace, Sales Order Command Center, Sourcing Command Center, Claims Settlement Workspace and Cost Accounting Close Workspace "available now" ([press release](https://www.prnewswire.com/news-releases/oracle-introduces-fusion-agentic-applications-for-finance-and-supply-chain-302738193.html)).

#### 10.2.1 Financials agents and agentic apps

| Agent or app (exact name) | Step | What it does | UI surface | Availability and setup | Source |
|---|---|---|---|---|---|
| Payables Agent for invoice ingestion, compliance and control | Invoice capture to import | Document IO capture, layout training, invoice completion, anomaly controls, insights, chat-assisted Invoice List | ERP Agents menu; invoice mailbox; Ask Payables Agent | 26A: Document IO image processing ("GenAI Driven Image Documents Processing") only through Oracle's early adoption program; 26B: enabled by default, usable after security setup; enhanced 26C, 26D | [26A](https://docs.oracle.com/en/cloud/saas/readiness/erp/26a/fins26a/26A-fin-wn-f44034.htm), [26B](https://docs.oracle.com/en/cloud/saas/readiness/erp/26b/fins26b/26B-fin-wn-f43769.htm), [26C](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f49574.htm), [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51289.htm) |
| Payables Period Close Workspace | Payables close | Close posture per ledger and period, blockers, Priority Actions, Notify | Workspace; Ask Oracle | 26D; nothing to enable; privileges Manage or View Payables Period Close Workspace | [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51249.htm) |
| Payments Agent for Payment Options, Offers, and Execution | Payments and financing | Insights; Payment Execution, Payment Options, Supplier Offers and (26D) Buyer Onboarding assistants | 26B: Navigator > Payments Agent group; 26C: ERP Agents root menu; Ask Oracle | Listed 26A; 26B Navigator link available by default; enhanced 26C, 26D | [26B](https://docs.oracle.com/en/cloud/saas/readiness/erp/26b/fins26b/26B-fin-wn-f43659.htm), [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51180.htm) |
| Customer Billing Agent | Billing inquiry | Invoice details, payment status, balances | ERP Agents | 26C; available by default, roles needed | [26C](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f50502.htm) |
| Billing Operations Workspace for billing readiness and dispute resolution | Billing readiness, disputes | Escalates project invoice approvals, finds held bill transactions and failed deliveries (resends when policy permits), approves or rejects eligible disputes or routes them with a recommendation, prepares customer replies | ERP Agents work area; Ask Oracle | 26D; custom job role with the duty, Grant on Business Unit and Grant on Customer Account data security policies; Project Billing Readiness Policy; mailbox through the Collections Email Response Assistant | [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51329.htm) |
| Cash Processing Agent for receipt processing and cash application | Receipts, cash application | Receipt and remittance exceptions; finds customers and invoices; applies (full, partial, multi-transaction), assigns customers, refunds, each after user confirmation | Navigator > ERP Agents > Cash Processing Agent ([26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51246.htm)); Insights | 26C default on; enhanced 26D | [26C](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f50544.htm), [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51477.htm) |
| Cash Processing Agent for bank statement reconciliation | Bank reconciliation | Unreconciled lines, suggested matching rules, reconciliation actions | Same agent | 26D default on | [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51246.htm) |
| Cash Processing Agent for cash positioning and improved liquidity | Cash position | Shortfalls and anomalies; bank transfers after user acceptance | Same agent | 26C; enhanced 26D | [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51245.htm) |
| Collector Workspace (26C: Collector Workspace Agent for Prioritized Work Queue and Guided Resolution; 26D: Collector Workspace Agentic Application for enhanced collections actions) | Collections | Ranked worklist, next-best actions, email intelligence, drafts, promise-to-pay capture; dunning letters out of scope | 26C: AI Agents page, Apps tab; 26D: ERP Agents > Collector Workspace | 26C; 26D Fusion Claw features "starting 13th Nov CWB" (read as 2026-11-13), so not yet available on 2026-10-21 | [26C](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f49306.htm), [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51379.htm) |
| Ledger Agentic Application | GL, accounting exceptions, close | Monitoring prompts, inquiry, outcomes with evidence, journal import and posting exception resolution | Ledger Workspace; Ask Oracle | "Ledger Agent for Agentic AI-Powered General Ledger Experience" 26A and 26B; app 26C; Fusion Claw 26D; conversations in English | [26B](https://docs.oracle.com/en/cloud/saas/readiness/erp/26b/fins26b/26B-fin-wn-f43814.htm), [26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51915.htm) |
| Expenses Agent (adjacent to P2P) | Employee spend | Receipt capture, card matching, cited policy answers, scheduled automatic submission of compliant reports | Company email alias; Oracle Expenses for exceptions | Default on from 26C (opt-in before 26C); per business unit through Manage Expenses System Options (readiness check, Enable Touchless Expenses) | [enable](https://docs.oracle.com/en/cloud/saas/financials/faeac/how-do-i-enable-expenses-agent.html), [overview](https://docs.oracle.com/en/cloud/saas/financials/faeac/overview-of-expenses-agent.html) |

#### 10.2.2 Procurement, receiving, costing and order management agents

Most of these are templates: copy the template in AI Agent Studio, publish it, then attach it to a page through a guided journey or page property.

| Agent or app | What it does; where | Since | Source |
|---|---|---|---|
| Procurement Request Concierge | Routes requester intent to the right assistant; Ask AI on the Self Service Procurement home page | 26D | [26D](https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/ssproc26d/26D-ssproc-wn-f50397.htm) |
| Purchase Requisition Creation Guide | Creates and submits catalog or noncatalog requisitions by chat; seeded agent (can't be modified) set as the Self Service Procurement AI Agent Code page property `ORA_REQUISITION_CREATION_GUIDE`; needs the category model and a vector index workflow | 26B; enhanced 26C, 26D | [26B](https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/ssproc26b/26B-ssproc-wn-f42072.htm) |
| Purchase Requisition Status Advisor | Requisition status and deep links | 25C | [25C](https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/ssproc25c/25C-ssproc-wn-f39723.htm) |
| Quote to Purchase Requisition Assistant | Emailed text-based PDF quote to draft requisition; scheduled process Process Emails for Procurement Transactions | 25D | [25D](https://docs.oracle.com/en/cloud/saas/readiness/scm/25d/ssproc25d/25D-ssproc-wn-f40074.htm) |
| Procurement Policy Advisor | Answers from your published policy documents | 25C | [25C](https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/ssproc25c/25C-ssproc-wn-f39721.htm) |
| Intake Request Creation Assistant | Conversational intake requests with optional AI summary | 26C intake requests; enhanced 26D | [26D](https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f50312.htm) |
| Purchase Order Status Advisor | Buyer PO status, current approver, rejection cause | 26B | [26B](https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/proc26b/26B-procurement-wn-f42955.htm) |
| Autonomous Sourcing Assistant; Supplier Negotiation Award Assistant | Requisition lines to negotiations and awards through scheduled processes; the negotiation owner is first approver | 26A | [26A](https://docs.oracle.com/en/cloud/saas/readiness/scm/26a/proc26a/26A-procurement-wn-f41767.htm) |
| Sourcing Command Center | Workload, In Progress and Pending Award panels; AI-recommended award actions | 26B early access; 26D award and purchase document creation, award scenario simulation | [26B](https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/proc26b/26B-procurement-wn-f42881.htm), [SCM list](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiafl/ai-scm.html) |
| Supplier Qualification Workspace | Qualification gaps, initiatives, supplier site holds; up to 500 strategic suppliers | 26C | [26C](https://docs.oracle.com/en/cloud/saas/readiness/scm/26c/proc26c/26C-procurement-wn-f46293.htm) |
| Supplier Portal Advisor | Answers supplier how-to questions on Supplier Portal pages | 25C | [25C](https://docs.oracle.com/en/cloud/saas/readiness/scm/25c/proc25c/25C-procurement-wn-f39460.htm) |
| Procurement Spend Command Center | Fusion Claw outcomes on maverick spend and agreement leakage, agreement redirection and supplier-item price variance for last-quarter invoice lines; duty ORA_PO_SPEND_ANALYSIS_COMMAND_CENTER_APP_DUTY | 26D | [26D](https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f51649.htm) |
| ASN Creation Assistant; Receipt Creation Assistant | ASN or receipt from pasted email text; creation through email added in 26B for both | 25D; 26A | [25D](https://docs.oracle.com/en/cloud/saas/readiness/scm/25d/inv25d/25D-inventory-wn-f39927.htm), [26A](https://docs.oracle.com/en/cloud/saas/readiness/scm/26a/inv26a/26A-inventory-wn-f41429.htm) |
| Supplier Accruals Assistant | Reviews receipt accruals against policy thresholds (RAG); marks accruals for review; clearing stays on the Open Accruals page (deep link) | 26A | [26A](https://docs.oracle.com/en/cloud/saas/readiness/scm/26a/inv26a/26A-inventory-wn-f42406.htm) |
| Cost Accounting Close Workspace | Cost close exceptions and next-best actions | 26B | [SCM list](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiafl/ai-scm.html), [press release](https://www.prnewswire.com/news-releases/oracle-introduces-fusion-agentic-applications-for-finance-and-supply-chain-302738193.html) |
| Sales Order Command Center | Backorders, reservation failures and holds; cancel, return and hold actions; Order Management > Show More | 26B, 26C | [26C](https://docs.oracle.com/en/cloud/saas/readiness/scm/26c/order26c/26C-order-mgmt-wn-f46432.htm) |
| Purchase Orders to Sales Orders Converter; Purchase Order to Sales Order Converter via email | Customer PO PDF to sales order: upload on Sales Orders > Create Sales Orders from Purchase Orders, or by email; redesigned Order Management pages required | 25D, 26A; email 26C | [25D](https://docs.oracle.com/en/cloud/saas/readiness/scm/25d/order25d/25D-order-mgmt-wn-f42608.htm), [26C](https://docs.oracle.com/en/cloud/saas/readiness/scm/26c/order26c/26C-order-mgmt-wn-f49506.htm) |
| Sales Order Correction Assistant | Fixes failed order imports (Smart Match above 80% confidence) and reruns the import | 26C | [26C](https://docs.oracle.com/en/cloud/saas/readiness/scm/26c/order26c/26C-order-mgmt-wn-f46414.htm) |
| Order Exception Assistant | Extensions running over two seconds, Groovy suggestions ("only guidelines"), cleanup of non-transaction data and unclosed fulfilled orders; can run the cleanup scheduled processes itself | 25D; enhanced 26A, 26C | [25D](https://docs.oracle.com/en/cloud/saas/readiness/scm/25d/order25d/25D-order-mgmt-wn-f40733.htm) |
| Sales Order Assistant | Draft orders from natural language. In 25D Oracle wrote "Oracle recommends to not use Sales Order Assistant agent for this release"; the supervisor version was superseded by Sales Order Assistant (Single Agent) | 25D | [25D](https://docs.oracle.com/en/cloud/saas/readiness/scm/25d/order25d/25D-order-mgmt-wn-f39928.htm) |
| Price Administration Assistant | Adds, updates or end-dates list prices on price lists after user (chat) or approver (email) approval; guided journey on the Price Lists page; models and coverage items not supported | 26C | [26C](https://docs.oracle.com/en/cloud/saas/readiness/scm/26c/order26c/26C-order-mgmt-wn-f49469.htm) |
| Gross Margin Analyst | Order or item gross margin with cost-element COGS breakdown; the template agent is named Gross Margin Estimator Agent; schedule Cost Accounting Report Processor; complex configured items out of scope | 26B; configured items 26C | [26B](https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/inv26b/26B-inventory-wn-f42401.htm) |

#### 10.2.3 Payables Agent in depth

Source: *Detailed Adoption Guidance: Payables Agent* ([guide](https://docs.oracle.com/en/cloud/saas/financials/fafpa/what-is-payables-agent.html)). It is "an AI-driven Accounts Payable assistant" for touchless payables and "doesn't replace the standard Payables invoice lifecycle". Document IO is the recognition engine; existing IDR customers keep mailboxes and adaptive learning, and the switch is automatic ([adoption path](https://docs.oracle.com/en/cloud/saas/financials/fafpa/availability-and-adoption-path.html)).

| Area | Scope ([implementation scope](https://docs.oracle.com/en/cloud/saas/financials/fafpa/implementation-scope.html), [26C](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f49574.htm)) |
|---|---|
| Ingestion | Email, e-invoice integrations, partner e-invoices (Thomson Reuters), Supplier Portal, mass imports and manual invoices, sorted into streams; XML (UBL, OAG, custom) and custom CSV from 26C |
| Recognition | Layout-aware extraction; annotation training including flexfields and logo-based supplier recognition; adaptive learning by invoice fingerprint, shareable between environments |
| Compliance and Control | Invoice Completion fills blank accounting, tax, project, asset, payment and localization attributes at import. Anomaly Controls: Invoice Currency, Remittance Bank Account, High Invoice Amount, Fraudulent Invoice, Duplicate Invoice. 26D adds Matching Controls (policies by business unit, purchasing category, legal entity and currency) and Exceptions (predefined resolution for Amount Precision, Invalid Attribute Values, and Attribute Name and Value Conflict) ([26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51289.htm)) |
| 26D additions | Actionable Insights, a Document IO Integration Service endpoint under Document Receiving Endpoints, Domain Value Mappings with bulk upload and download, Document Training Data Migration between environments, new Invoice List query attributes (Paid Status, Workflow Approval Status, Account Coding Status, Fund Status, Validation Status). No extra setup if the agent is already enabled ([26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51289.htm)) |
| Experience | Home (Ask Payables Agent, suggested prompts, Top Insights), Insights, Capture, Invoice Document Streams, Invoice Document Training, Invoice List (chat plus data canvas), Compliance & Control (Equalizer icon) ([user experience](https://docs.oracle.com/en/cloud/saas/financials/fafpa/review-payables-agent-user-experience.html)). Recognition is measured with the scheduled reports Invoice Documents Recognition Tracking Report and Invoice Documents Recognition Rate Report ([rate report](https://docs.oracle.com/en/cloud/saas/financials/26b/fappp/invoice-documents-recognition-rate-report.html)) |

Setup steps, in order:

1. Prerequisites: business units, suppliers and sites, PO formats and working Payables. Supplier names, addresses and PO numbers on invoices must match Fusion exactly ([26B tips](https://docs.oracle.com/en/cloud/saas/readiness/erp/26b/fins26b/26B-fin-wn-f43769.htm)).
2. Setup and Maintenance > Financials > Payables > Manage Intelligent Document Recognition Options > Activate. Expect status Active and a generated email endpoint; supplier and PO-format synchronization starts automatically, so wait 24 hours before testing ([enable](https://docs.oracle.com/en/cloud/saas/financials/fafpa/enable-payables-agent.html)). In the same task set options such as Recognize Tax Amount, Recognize Freight Amount and Always Create Invoices in Incomplete Status ([options](https://docs.oracle.com/en/cloud/saas/financials/fafpa/configure-document-recognition-and-processing-options.html)).
3. Business unit derivation and channels: a corporate alias that forwards to the Oracle endpoint and keeps attachments; optional Thomson Reuters e-invoicing through a service request and Navigator > My Enterprise > Manage Thomson Reuters Services ([channels](https://docs.oracle.com/en/cloud/saas/financials/fafpa/configure-invoice-submission-channels.html), [Thomson Reuters](https://docs.oracle.com/en/cloud/saas/financials/fafpa/configure-partner-e-invoicing-with-thomson-reuters.html)).
4. Compliance and Control: one natural-language policy per target attribute (for example "Set Pay Group to Standard when Requester is `<REQUESTER>`"); review the generated rule on the canvas. Under Payables > Configuration > Compliance and Control > Policy Details, download the details to Excel, complete the target values, upload, repeat validation until clean, then activate: activation promotes the draft to the active version, and only active policies apply. Enable only the anomaly controls you need and tune Time Period (days) and Amount Variation (%). Users need the Manage Payables Compliance and Control or View Payables Compliance and Control privilege ([policies](https://docs.oracle.com/en/cloud/saas/financials/fafpa/configure-compliance-and-control-policies.html), [completion](https://docs.oracle.com/en/cloud/saas/financials/fafpa/configure-invoice-completion-policies.html), [anomalies](https://docs.oracle.com/en/cloud/saas/financials/fafpa/configure-anomaly-controls.html), [readiness](https://docs.oracle.com/en/cloud/saas/financials/fafpa/confirm-environment-readiness.html)).
5. Schedule Import Invoices with Ledger = `<LEDGER>`, Source = Invoice Image and Business Unit blank; Oracle says organizations typically run it once or twice a day ([schedule](https://docs.oracle.com/en/cloud/saas/financials/fafpa/schedule-invoice-import-processing.html)).
6. Grant the duty roles and Business Unit data access (Manage Business Unit Data Access for Users), run Process Permission Group Policies, and test with representative invoice samples before rollout.

Duty roles (names from [duty roles](https://docs.oracle.com/en/cloud/saas/financials/fafpa/payables-agent-duty-roles.html), codes from [26C](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f49574.htm); add each under both Roles and Privileges and Roles and Permission Groups):

| Duty role | Code | Grants |
|---|---|---|
| Payables Invoice Documents Processing Duty / Inquiry Duty | ORA_INVOICE_DOCUMENTS_PROCESSING_DUTY / ORA_INVOICE_DOCUMENTS_INQUIRY_DUTY | Streams, Training; the inquiry duty can't open the source file attachment |
| Payables Invoice Configuration Processing Duty / Inquiry Duty | ORA_INVOICE_CONFIGURATION_PROCESSING_DUTY / ORA_INVOICE_CONFIGURATION_INQUIRY_DUTY | Capture, Compliance and Control |
| Payables Invoice Processing Duty / Inquiry Duty | ORA_AP_PAYABLES_INVOICE_PROCESSING_DUTY / ORA_AP_PAYABLES_INVOICE_INQUIRY_DUTY | Invoice List (limited actions) and the classic invoice page |
| Payables Agent Insights Duty | ORA_AP_PAYABLES_AGENT_INSIGHTS_DUTY | Insights |
| Payables Agent Monitoring Prompt Management Duty | ORA_AP_PAYABLES_AGENT_MONITORING_PROMPT_MGT_DUTY | Insights monitoring prompts |

Outcomes: Oracle lists less manual entry, better recognition across supplier layouts, faster exception resolution, more straight-through processing and earlier anomaly detection, without numeric targets ([outcomes](https://docs.oracle.com/en/cloud/saas/financials/fafpa/business-processes-impacted-and-expected-outcomes.html)). Operating rules ([Invoice List](https://docs.oracle.com/en/cloud/saas/financials/fafpa/use-the-conversational-invoice-list.html), [Insights](https://docs.oracle.com/en/cloud/saas/financials/fafpa/review-payables-agent-insights.html)):

- The Invoice List shows active and import-rejected invoices, not interface rows waiting for import. Its actions are Validate Invoice, Cancel Invoice, Override Anomaly and Release Hold; overrides and releases go to the invoice audit trail with the user. Oracle says not to clear exceptions in bulk. Fix import rejections with Open Correction Spreadsheet (Oracle Visual Builder Add-in for Excel), then import again.
- Insights come from monitoring prompts. Predefined monitoring conditions are read-only; enable, disable or clone a prompt to change frequency, time frame or priority. Creating entirely new prompts isn't supported in the documented 26C experience. Users Mark as Reviewed, Dismiss or Reopen; Obsolete is a terminal status that the application assigns.

#### 10.2.4 Payments Agent in depth

Source: *Detailed Adoption Guidance: Payments Agent* ([guide](https://docs.oracle.com/en/cloud/saas/financials/fappa/overview-of-payments-agent.html)); it works "within existing Oracle Fusion Cloud Financials security and approval controls".

| Component | What it does | Example prompt |
|---|---|---|
| Insights | Nine predefined insights, for example payment runs requiring attention, approvals pending more than 5 days, unresolved acknowledgments or rejections, unsettled or unreconciled payments ([insights](https://docs.oracle.com/en/cloud/saas/financials/fappa/identify-and-prioritize-payment-actions-with-insights.html)) | - |
| Payment Execution Assistant | Queries PPRs, payment files and payments; diagnoses supported failures (26D); schedules PPRs from templates; submits supplier remittance advice (26D) | "Show PPRs requiring attention" |
| Payment Options Assistant | Compares dynamic discounting, virtual card and (26D, analysis only) supply chain financing; spend analysis; draft offers | "Compare DD and VC benefits for my top suppliers in USD for `<BU>`" |
| Supplier Offers Assistant | Reviews, confirms and tracks offers; 26D adds one-time virtual card offers and standing dynamic discounting offers | "Show offers expiring in the next 7 days" |
| Buyer Onboarding assistant (26D) | Payment program setup; customer-defined role with ORA_AP_BUYER_ASSISTANT_MANAGEMENT_DUTY | - |

Setup steps, in order ([security setup](https://docs.oracle.com/en/cloud/saas/financials/fappa/payments-agent-security-setup.html), [roles](https://docs.oracle.com/en/cloud/saas/financials/fappa/required-roles-and-access.html), [RAG documents](https://docs.oracle.com/en/cloud/saas/financials/fappa/configure-payment-program-rag-documents.html)):

1. Complete payment setup: dynamic discounting and virtual card programs, supplier onboarding, bank integrations, PPR templates. Enablement is per business unit ([before you start](https://docs.oracle.com/en/cloud/saas/financials/fappa/before-you-start.html)).
2. Site profile options ORA_HCM_VBCS_PWA_ENABLED = Y and ORA_ASE_SAS_INTEGRATION_ENABLED = Yes.
3. Admin role with ORA_FUN_MANAGE_FIN_AI_AGENT, ORA_FUN_MANAGE_FIN_AI_AGENT_HCM and the permission group ORA_DR_FAI_GENERATIVE_AI_AGENT_FIN_ADMINISTRATOR_DUTY.
4. Runtime: enable permission groups on Payment Specialist (ORA_AP_PAYMENT_SPECIALIST_JOB) and add a role with ORA_FUN_FIN_AI_AGENT_RUNTIME_DUTY and ORA_FUN_FIN_AI_AGENT_RUNTIME_DUTY_HCM. Assistant duties are ORA_AP_PAYMENT_EXECUTION_MANAGEMENT_DUTY, ORA_AP_PAYMENT_OPTIONS_MANAGEMENT_DUTY and ORA_AP_SUPPLIER_OFFERS_MANAGEMENT_DUTY ([26C](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f49623.htm)).
5. Run Import Resource Application Security Data, Import User and Role Application Security Data and Retrieve Latest LDAP Changes, in that order; grant Payment Specialist business unit access in Manage Data Access for Users (Security Context Business Unit) and run Process Permission Group Policies. If that button is missing, use Manage Standard Lookups, search lookup type `ORA_ERP_CONTROLLED%` and add lookup code MDA_36604437 (meaning Show Button for Process Permission Group Policies).
6. Upload text documents with program terms (market short-term investment rate; virtual card program code, borrowing rate, RCN alias, rebate rate) to the Financing Programs RAG tool (ORA_FIN_AP_FINANCINGPROGRAMSRAG), run Process Agent Documents and confirm status Published. Without them the assistant uses system defaults ([26B](https://docs.oracle.com/en/cloud/saas/readiness/erp/26b/fins26b/26B-fin-wn-f43659.htm)).

"Actions that create or modify business transactions require user confirmation" ([FAQ](https://docs.oracle.com/en/cloud/saas/financials/fappa/does-payments-agent-perform-actions-automatically.html)). In 26D a draft offer reserves its installments until discarded, virtual card credit limits aren't checked, and existing payment security, approvals and validations "remain authoritative" ([26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51180.htm)).

#### 10.2.5 Notes on the other finance agents

- Cash Processing Agent: enable Create Receipts from Bank Statement on the bank account, forward remittance emails to the pod address shown in the agent, and schedule Apply Receipts Using AutoMatch with Include Remittance = Yes. Insights refresh every four hours; receipts are applied only after user confirmation. Duties: ORA_AR_CASH_RECEIPT_GENERATION_ASSISTANT_DUTY, ORA_AR_CASH_APPLICATION_ASSISTANT_DUTY, ORA_AR_CASH_RECEIPTS_INQUIRY_ASSISTANT_DUTY, ORA_AR_CASH_PROCESSING_INSIGHTS_DUTY. Bank reconciliation uses Cash Manager (ORA_CE_CASH_MANAGER) or ORA_CE_BANK_STATEMENT_RECONCILIATION_ASSISTANT_DUTY.
- Collector Workspace: publish your collections policy through Policy Node > Policies (Customize, Generate, Publish) and copy the Collections Email Response Assistant template once per mailbox. Access: Collections Workspace Assistant duty role on custom roles, or the predefined Collections Agent job role. Collectors see only their assigned accounts; Ask Oracle "supports read-only inquiries". The Collections Policy Execution Assistant "is no longer available starting with 26D"; policies published with it carry forward ([26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51379.htm)).
- Billing: the Customer Billing Agent needs ORA_AR_BILLING_INQUIRY_ASSISTANT_DUTY; the Billing Operations Workspace needs ORA_AR_BILLING_OPERATIONS_WORKSPACE_DUTY, and its dispute scope is incorrect price and duplicate invoices only.
- Ledger Agentic Application: in 26B the Ledger Agent page needed the Ledger Inquiry Assistant discretionary job role ([26B](https://docs.oracle.com/en/cloud/saas/readiness/erp/26b/fins26b/26B-fin-wn-f43814.htm)). In 26D, new users follow the Ledger Workspace message to raise a service request for the Oracle-managed prerequisites, then get the Ledger Agentic Application Assistant role, which also enables Accounting Exception Resolution for existing users. Exception resolution covers Journal Import and Posting exceptions; automatic resolution covers missing currency rates and inactive or end-dated segment values, when policy allows ([26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51915.htm)).

### 10.3 Embedded (non-agent) AI in P2P and O2C

| Capability | Module | Type | Since | Enablement and limits | Source |
|---|---|---|---|---|---|
| Document IO replacing the IDR backend; IDR adaptive learning | Payables; Document IO also ingests bank files and remittance advices | Generative, predictive | Document IO default from 26B; adaptive learning 25A | Automatic for IDR customers | [26B](https://docs.oracle.com/en/cloud/saas/readiness/erp/26b/fins26b/26B-fin-wn-f43769.htm), [26C cash](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f50544.htm), [ERP list](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiafl/ai-erp.html) |
| Intelligent Account Combination Defaulting for Invoices | Payables | Predictive | 22D | Defaults segment values on no-PO invoice lines when each segment exceeds its dynamically calculated confidence threshold; at least 3 months of history recommended; enable permission groups on the Adaptive Intelligence Applications Administrator role, activate, train, then opt in with the promotion code from the evaluation report | [26D guide](https://docs.oracle.com/en/cloud/saas/financials/26d/fappp/intelligent-account-combination-defaulting.html), [ERP list](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiafl/ai-erp.html) |
| Oracle AI Apps discounts | Payables payments | Predictive | Not stated | "AI Apps is a separate application" that calculates discounts | [26D guide](https://docs.oracle.com/en/cloud/saas/financials/26d/fappp/what-s-adaptive-intelligent-applications.html) |
| Predictive Cash Forecasting | Cash Management with EPM | Predictive | 25C | Controlled release for early adopters; service request and EPM Enterprise subscription | [25C](https://docs.oracle.com/en/cloud/saas/readiness/erp/25c/fins25c/25C-fin-wn-f38827.htm) |
| Customer Collections Date Prediction | Oracle Fusion ERP Analytics | Predictive | Analytics 26R2 | Predicted payment date and delay days in the Financials - AR Transaction and Financials - AR Aging subject areas; 24 months of training data | [doc](https://docs.oracle.com/en/cloud/saas/analytics/26r2/faiae/customer-collections-date-prediction.html) |
| Create Negotiation Cover Page with Generative AI; Create Negotiation Synopsis with Generative AI | Sourcing | Generative | 24B; 24C | Cover page: Manage Negotiation Styles, edit a custom style (predefined styles can't be edited), select AI Assist under Cover Page in Controls (still documented in the 26B guide); output "may contain inaccuracies" | [26B setup](https://docs.oracle.com/en/cloud/saas/procurement/26b/oapro/setup-tasks-to-use-generative-ai-for-negotiation-cover-page.html), [24B](https://docs.oracle.com/en/cloud/saas/readiness/scm/24b/proc24b/24B-procurement-wn-f31739.htm), [24C](https://docs.oracle.com/en/cloud/saas/readiness/scm/24c/proc24c/24C-procurement-wn-f32923.htm) |
| Summarize Supplier Registration Attachments With Generative AI | Supplier registration | Generative | In the 26D guide | Summaries of PDF and text attachments in Company Details, shown in approval emails and worklist notifications; English only; "may contain inaccuracies" | [26D guide](https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/summarize-supplier-registration-attachments-with-generative-ai.html) |
| Category and supplier suggestions | Self Service Procurement, Purchasing | Predictive | 25D to 26C | Category model from Prepare the Purchasing Category Suggestion Model | [SCM list](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiafl/ai-scm.html), [26B](https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/ssproc26b/26B-ssproc-wn-f42072.htm) |
| Oracle Digital Assistant prepackaged SaaS skills | All Fusion | Conversational | Maintenance mode since 25.10 | Discontinued 2026-11-21; migrate to AI Agent Studio | [ODA](https://docs.oracle.com/en/cloud/paas/digital-assistant/skills.html) |

### 10.4 Switching on, governing and invoking Oracle agents

#### 10.4.1 Enablement checklist

| Step | Task | Notes |
|---|---|---|
| 1 Profile options (Site) | ORA_ASE_SAS_INTEGRATION_ENABLED = Yes; ORA_HCM_VBCS_PWA_ENABLED = Y | App switches: ORA_FOM_COMMAND_CENTER_AGENTIC_APP_ENABLED, ORA_PON_SOURCING_AGENTIC_APP_ENABLED, ORA_PO_SPEND_ANALYSIS_COMMAND_CENTER_AGENTIC_APP_ENABLED; ORA_POQ_SUPPLIER_QUALIFICATION_AGENTIC_APP_ENABLED is already on by default |
| 2 Roles | Enable permission groups on every job role that carries agent duties; add assistant duties under Roles and Privileges and Roles and Permission Groups | 10.1.5, 10.2 |
| 3 Data access | Manage Data Access for Users, then Process Permission Group Policies | Page access alone shows no data |
| 4 Security sync | Import Resource Application Security Data, Import User and Role Application Security Data, Retrieve Latest LDAP Changes | Cash Processing Agent insights can take up to four hours to appear after role assignment |
| 5 Instantiate | Copy Template or Use Template, publish, then attach through a guided journey task of type Workflow Agent or a Visual Builder Studio page property | Prebuilt finance agents need no template copy, except the Collections Email Response Assistant used for collections and billing mailboxes |
| 6 Knowledge | Document tool Ready to Publish, then Process Agent Documents; policy models through Policy Node > Policies | Payables, Payments, collections, billing, sourcing |
| 7 Schedules | Import Invoices (source Invoice Image), Apply Receipts Using AutoMatch, Process Requisition Lines with Autonomous Sourcing Assistant, Aggregate AI Agent Usage and Metrics | Run as least-privilege users |
| 8 Test and retain | Evaluation sets, pilot by business unit, migrate published workflows; set ORA_FAI_DATA_RETENTION_DAYS | Rerun evaluations after model changes |

#### 10.4.2 Where users invoke agents

| Surface | Path or channel | Used by |
|---|---|---|
| ERP Agents root menu (26C+) | Navigator > ERP Agents | Payables, Payments, Cash Processing, Customer Billing, Billing Operations, Collector Workspace |
| Ask Oracle | Chat bar in workspaces and pages; suggested prompts with parameters | Finance agents, command centers |
| AI Agents and Applications page | Me > Quick Actions > Show More > AI Agent Studio > AI Agents ([AI Q&A](https://docs.oracle.com/en/cloud/saas/fusion-ai/aiaqa/questions-and-answers.pdf)) | Any agent the user can access |
| Embedded Ask AI, guided journeys, Quick Actions | Self Service Procurement home; Purchase Orders, Supplier Portal, Price Lists and Order Management pages; Procurement Quick Actions | Procurement, receiving, pricing and order agents |
| Email | Payables endpoint behind a corporate alias; quote, customer PO, collections and remittance mailboxes | Payables, Quote to Purchase Requisition, PO to SO, Collector Workspace, Cash Processing |
| Background | Scheduled processes and workflow schedules | Autonomous sourcing, Sales Order Correction Assistant |

#### 10.4.3 Logging, audit and the data footprint

Oracle-side evidence includes Monitoring and Evaluation traces, the invoice audit trail for overrides and hold releases, insight comments and each Fusion Claw execution record. The 26D *Tables and Views* guides also hold the tables below. Where no foreign key is documented, the link to a specific agent is inferred from the table description (verify in your pod).

| Table | Official description (abridged) |
|---|---|
| AP_IDR_OPTIONS, AP_IDR_OPTION_EXTENSIONS | Options of the Manage Intelligent Document Recognition Options task |
| AP_DOCIO_STREAM_DETAILS | Summary and status of all Payables documents ingested through any channel |
| FUN_DOCIO_INCOMING_DOCUMENTS, FUN_DOCIO_TRANSFORM_DOCUMENTS, FUN_DOCIO_AL_MAPPINGS | Incoming documents, their transformed documents and adaptive-learning mappings; AR_REMITTANCE_ADVICES_ALL, AR_TRANSMISSIONS_ALL and IBY_INBOUND_FILE have documented foreign keys to FUN_DOCIO_INCOMING_DOCUMENTS |
| FUN_SENSOR_SIGNALS, FUN_SENSOR_INSIGHT_RECIPIENTS, FUN_SENSOR_INSIGHT_ACTN_HIST | Signals raised when a monitoring rule is met; insight recipients and status (Open, Dismissed, Reviewed, Obsoleted); every action on an insight |
| FND_BOSS_AI_TELEMETRY | Natural-language question and generated BQL query per BOSS AI request (holds user prompts) |
| DOO_AGENT_SIGNALS, DOO_AGENT_SIGNAL_INTERACTIONS, DOO_AGENT_ACTION_HISTORY | Order Management agent signals, recommendation decisions and outcomes, and the audit of agent actions with execution mode (for example HUMAN_ASSIST or AUTO) |
| POR_AGENT_DOCUMENT_REQUESTS; POZ_SUPP_RISK_PROFILE | Document requests processed by procurement agents; one row per Supplier Risk Analyst run version with the agent response JSON (no matching feature page found) |
| PO_GEN_AI_SUMMARY; PO_AI_HEADER_RECOMMENDATIONS; AR_CASH_RECOS_ALL; AR_PMT_SCHEDULE_PREDICTIONS | GenAI summaries; AI supplier recommendations; receipt match recommendations with scores; predicted payment date and amount per payment schedule |

Audit queries for a BI Publisher data model (section 9):

```sql
-- Payables Agent ingestion by stream and status, last 7 days
SELECT sd.stream_definition_code,
       sd.ingestion_source,
       sd.status_code,
       COUNT(*)              AS documents,
       MIN(sd.creation_date) AS oldest_document
FROM   ap_docio_stream_details sd
WHERE  sd.creation_date >= SYSDATE - 7
GROUP  BY sd.stream_definition_code, sd.ingestion_source, sd.status_code
ORDER  BY oldest_document;
```

```sql
-- Order Management agent actions, last 7 days
SELECT oa.request_time, oa.agent_code, oa.agent_execution_mode, oa.user_action_code,
       oa.object_type, oa.object_user_key_1, oa.created_by, oa.trace_id
FROM   doo_agent_action_history oa
WHERE  oa.request_time >= SYSDATE - 7
ORDER  BY oa.request_time DESC;
```

### 10.5 Interoperability with external agents

| Direction | Mechanism | Since | Notes |
|---|---|---|---|
| Oracle agent to external API | External REST tool | Documented by 26B | HTTPS only; optional human approval |
| Oracle agent to external tools | MCP tool | 26A | An Oracle Integration project can be the MCP server: one URL per project, integrations registered as agentic AI tools, OAuth confidential application, streamable HTTP ([OIC](https://docs.oracle.com/en/cloud/paas/application-integration/aiagents/workflow-expose-integrations-tools-mcp-server.html)) |
| Oracle agent and external agent | Agent2Agent (A2A) | 26C | Published Fusion agents "can now collaborate with AI agents in other platforms": discover through the registry, retrieve the Agent Card, authenticate, call; shared lifecycle for long-running tasks ([26C](https://docs.oracle.com/en/cloud/saas/readiness/hcm/26c/common26c/26C-common-wn-f49247.htm)). The 26D guide documents only the inbound API; Oracle describes Fusion agents calling third-party agents as a scenario, so confirm outbound A2A configuration in your pod |
| External app to a Fusion agent | Agent Team REST endpoints | 26C | `POST /orchestrator/agent/v2/{workflowCode}/invokeAsync` returns a job ID; poll `GET /orchestrator/agent/v2/{workflowCode}/status/{jobId}` ([REST](https://docs.oracle.com/en/cloud/saas/applications-common/26c/farca/api-fusion-ai-agent-team.html)). The 26D guide requires an OAuth 2.0 bearer token from OCI IAM, with a confidential application in Fusion Applications IAM that has access to the AI Agent Studio service; its detailed two-way trust setup is written for other Oracle applications, so confirm the non-Oracle client setup in your pod. Access depends on the caller's role and the workflow Security tab |
| External agent to a Fusion agent | A2A endpoints | 26D guide | `GET /orchestrator/a2a/v1/{workflowCode}/.well-known/agent.json`, `POST /orchestrator/a2a/v1/agents/search`, `POST /orchestrator/a2a/v1/{workflowCode}`; discover, call, poll and stream (snapshot-based over SSE); every endpoint needs a Bearer token; discovery doesn't grant permission to run, and status retrieval is user-scoped |
| External agent to Fusion data | REST (for example `/fscmRestApi/resources/11.13.18.05/invoices`), SOAP, FBDI, BI (sections 6 to 8) or an Oracle Integration MCP server | - | No Oracle-documented MCP server that exposes Fusion business objects directly was found in the 26D sources reviewed |

The guide's CLI sample places the orchestrator under `https://<POD_HOST>/api/fusion-ai/orchestrator/`; confirm the prefix and version in your pod. Where Claude fits:

- Inside Oracle: workflows can run on Anthropic models through Google Vertex AI as a bring-your-own LLM; prompts and context then go to that provider under your contract.
- Building Oracle agents: the AI Studio CLI and its aistudio skill are meant to be driven by "a code assistant such as Codex or Claude Code"; Oracle's sample prompt tells the assistant to validate and test locally and not to save, publish or delete remote artifacts unless asked. Enable it under Credentials > AI Studio CLI with a public client in Oracle IDCS. The 2026-07-14 announcement names Claude Code among supported coding assistants (section 11).
- Claude as an external agent: call published Fusion agents through invokeAsync or A2A, or Fusion REST APIs through your own MCP server (section 11). Fusion security applies to the user behind the token, and returned data leaves Oracle's boundary.

### 10.6 Limitations and risks

| Risk | Evidence | Control |
|---|---|---|
| Wrong or invented output | GenAI output "may contain inaccuracies"; the studio FAQ lists hallucination mitigations | Ground agents in business objects and published documents; gate releases on evaluation thresholds |
| Actions without prior approval | Receipt Creation Assistant creates receipts directly; PO to SO via email creates orders; Sales Order Correction Assistant edits interface data; Order Exception Assistant can run cleanup scheduled processes; Billing Operations Workspace approves or rejects eligible disputes and resends invoices when policy permits ([26D](https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51329.htm)); autonomous sourcing relies on approvals being enabled, with the negotiation owner as first approver; Fusion Claw has Full Auto | Use Research mode or Human Approval nodes; keep approvals on and policies conservative; review the Created by Agent filter on Sales Orders; pilot in a test pod |
| Over-trust | "Don't treat the first Agent response as the final business decision"; "Don't expect Top Insights to display every open issue" ([Home](https://docs.oracle.com/en/cloud/saas/financials/fafpa/use-the-payables-agent-home-page.html)); Oracle tells buyers to "Review AI recommended priority actions for accuracy before applying" ([Sourcing Command Center](https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/proc26b/26B-procurement-wn-f42881.htm)) | Check the live transaction before acting; keep standard exception reports |
| Coverage gaps | Invoice Completion applies at import only, never to manual invoices or rows inserted into Payables base tables, and fills blank fields only; Sales Order Command Center cancels and returns standard products only, returns whole quantities, and applies or releases holds on the whole order; Billing Operations disputes cover incorrect price and duplicate invoices only; Quote to Purchase Requisition reads text-based PDFs only | Keep standard processes, reports and controls |
| Access and SoD | The Cash Processing Agent enforces "existing Receivables validations, authorizations, segregation-of-duties controls, and audit requirements" ([26C](https://docs.oracle.com/en/cloud/saas/readiness/erp/26c/fins26c/26C-fin-wn-f50544.htm)); autonomous sourcing jobs are scheduled under an integration user, and Oracle warns not to grant the Procurement REST Service Duty (ORA_PO_PROCUREMENT_REST_SERVICE_DUTY) to end-user roles ([26A](https://docs.oracle.com/en/cloud/saas/readiness/scm/26a/proc26a/26A-procurement-wn-f41767.htm)) | Least privilege; add agent duties to SoD analysis (section 12) |
| Residency and retention | Processing may leave the local region; GenAI data is purged after 90 to 365 days | Confirm region mapping and contract terms; export evidence you must keep |
| Model lifecycle and language | GPT-4.1 mini and GPT-5 mini retire in 27B; studio configuration and Ledger conversations are English only | Watch deprecation warnings; rerun evaluations; plan for other languages |
| Cost | Token consumption is measured for premium LLMs; predefined role assignment may count toward subscription consumption | Track AI Units; align roles with entitlements |
| Deprecations | Digital Assistant SaaS skills end 2026-11-21 | Migrate to AI Agent Studio agents |
