# Oracle Fusion SaaS + Claude Agentic AI Starter Kit

A ready-to-use project that connects **Oracle Fusion Cloud** (Financials, Procurement, Order Management) to **Claude Code** through the Model Context Protocol (MCP). Clone the repo, add your credentials, and start querying your Fusion pod with natural language — right from VS Code or the terminal.

## What's included

| Component | Description |
|---|---|
| **Read MCP Server** (`mcp-servers/fusion-mcp/fusion_server.py`) | A read-only Python MCP server that wraps the Fusion REST API. Five tools: `connection_status`, `fusion_get`, `list_invoices`, `get_invoice`, `get_api_info`. |
| **Write MCP Server** (`mcp-servers/fusion-mcp/fusion_write_server.py`) | A separate, approval-gated server for changes: create/update/delete, custom actions (approve, cancel, validate, hold), scheduled processes (ESS), FBDI bulk import, and BI Publisher reports. Previews before executing; prompts on every call. |
| **Claude Skills** (`.claude/skills/`) | `oracle-fusion` (query recipes, REST catalog, working loop) and `oracle-fusion-write` (the confirm-first write protocol). |
| **Setup Automation** | One-click scripts for Windows (`Connect-Oracle-Fusion.cmd`) and macOS/Linux (`scripts/setup.sh`). A doctor script (`Fusion-Doctor.cmd`) diagnoses and repairs connection issues. |
| **VS Code Config** (`.vscode/`) | Editor settings and recommended extensions preconfigured. |
| **Reference Docs** (`docs/`, `fusion-kit/`) | 26D P2P/O2C reference documentation, 16,000+ table/view catalog, 26,000+ REST operation catalog, and grep-friendly indexes. |
| **MCP Pre-approval** (`.claude/settings.local.json`) | The read tools are pre-approved for no-prompt use; write tools are intentionally left to prompt on every call. |

## Prerequisites

- **Python 3.12+** — [python.org](https://www.python.org/downloads/)
- **uv** (Python package manager) — `pip install uv` or [install docs](https://docs.astral.sh/uv/getting-started/installation/)
- **Claude Code** — [claude.com/claude-code](https://claude.com/claude-code) (CLI or VS Code extension)
- **Oracle Fusion Cloud** access — a pod URL and user credentials with REST API read access

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/oracle-fusion-claude-starter.git
cd oracle-fusion-claude-starter
```

### 2. Configure your credentials

Copy the environment template and fill in your Fusion pod details:

```bash
cp .env.example .env
```

Edit `.env`:
```env
FUSION_POD_URL=https://your-pod.fa.us2.oraclecloud.com
FUSION_USER=your.user@example.com
```

### 3. Run the setup

**Windows** (double-click):
```
Connect-Oracle-Fusion.cmd
```

**macOS / Linux:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The setup script will:
1. Read your pod URL and user from `.env` (or prompt you)
2. Build the Python virtual environment with all dependencies
3. Ask for your Fusion password (typed hidden, stored in your OS credential manager — never in files)
4. Register the MCP server with Claude Code
5. Run the connection doctor to verify everything works

### 4. Start using it

Open the project in VS Code (with the Claude Code extension) or start Claude Code in the terminal:

```bash
cd oracle-fusion-claude-starter
claude
```

Try these queries:
```
Show me the 10 most recent invoices
What invoices are on hold right now?
Look up purchase orders for supplier "Acme Corp"
What's the status of sales order 12345?
Check if the Fusion connection is working
```

## Project Structure

```
oracle-fusion-claude-starter/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── CLAUDE.md                          # Workspace rules for Claude Code
├── .env.example                       # Credential template (copy to .env)
├── .gitignore                         # Excludes secrets, venv, generated files
│
├── Connect-Oracle-Fusion.cmd          # Windows: one-click setup
├── Fusion-Doctor.cmd                  # Windows: diagnose + repair connection
├── scripts/
│   └── setup.sh                       # macOS/Linux setup script
│
├── .vscode/
│   ├── settings.json                  # Editor config
│   └── extensions.json                # Recommended extensions
│
├── .claude/
│   ├── settings.local.json            # MCP tool permissions (reads allowed, writes prompt)
│   └── skills/
│       ├── oracle-fusion/             # Read skill
│       │   ├── SKILL.md               # How Claude should query Fusion
│       │   └── references/
│       │       ├── recipes.md         # Ready-to-use query recipes (P2P + O2C)
│       │       └── rest-resources.md  # All P2P/O2C REST endpoints
│       └── oracle-fusion-write/
│           └── SKILL.md               # The confirm-first write protocol
│
├── mcp-servers/fusion-mcp/
│   ├── fusion_server.py               # Read server (5 read-only tools)
│   ├── fusion_write_server.py         # Write server (create/update/delete/action/ESS/FBDI/report)
│   ├── fusion_setup_helper.py         # CLI: config, store, test, doctor
│   ├── setup-fusion.ps1               # PowerShell setup logic
│   ├── pyproject.toml                 # Python dependencies
│   ├── uv.lock                        # Locked dependency versions
│   └── .python-version                # Python 3.12
│
├── docs/
│   └── Oracle_Fusion_26D_P2P_O2C_Reference.md
│
└── fusion-kit/                        # 26D catalogs and build tools
    ├── catalog.json                   # 16,006 tables and views
    ├── tables.jsonl                   # 3,633 P2P/O2C tables with columns
    ├── rest_catalog.json              # 26,152 REST operations
    ├── guides_toc.json                # Oracle guide TOC entries
    ├── idx/                           # Grep-friendly TSV indexes
    ├── doc_sections/                  # Markdown source of the reference doc
    └── scripts/                       # Catalog scraping and doc build tools
```

## Available MCP Tools

This kit ships **two** MCP servers: a read-only server (`oracle-fusion`) and a separate, approval-gated write server (`oracle-fusion-write`).

### Read tools — `oracle-fusion` (pre-approved, no prompt)

| Tool | Description |
|---|---|
| `connection_status()` | Check if the Fusion connection is working. Always call this first when troubleshooting. |
| `fusion_get(path, q, fields, ...)` | General-purpose read on any Fusion REST resource. Supports filters, finders, field selection, paging, and child resources. Works with `fscm`, `crm`, and `hcm` APIs. |
| `list_invoices(...)` | Search Payables invoices by number, supplier, date range, or amount. |
| `get_invoice(invoice_id)` | Get a single invoice by its InvoiceId. |
| `get_api_info()` | REST API version information (works without login). |

### Write tools — `oracle-fusion-write` (gated: previews first, prompts on every call)

These change ERP data. Each tool previews with `confirm=false` and only executes with `confirm=true`, and none are pre-approved, so Claude Code prompts you before each write. See the [write protocol](#write-safety).

| Tool | Description |
|---|---|
| `fusion_write(path, method, body, api, confirm)` | Create (`POST`), update (`PATCH`) or delete (`DELETE`) any REST record. |
| `fusion_action(path, action, parameters, api, confirm)` | Run a custom action: `approve`, `cancel`, `validateInvoice`, `applyHold`, `releaseHold`, `close`, `communicate`, etc. |
| `submit_scheduled_process(job_package_name, job_definition_name, ess_parameters, confirm)` | Submit an ESS scheduled process (Validate Invoices, Import Orders, Create Accounting, ...). |
| `get_process_status(request_id)` | Read-only. Track a submitted job by request id. |
| `import_bulk_data(document_base64, file_name, document_account, job_name, parameter_list, confirm)` | FBDI: upload a ZIP, load interface tables and run the import in one call. |
| `run_report(report_absolute_path, parameters, confirm)` | Run an existing BI Publisher report (the SQL-backed reporting path). |

> **Note on SQL:** Oracle Fusion has no ad-hoc SQL over REST. The supported path is a BI Publisher report whose data model holds your SQL, deployed once in the BI catalog, then run with `run_report`. SQL patterns are in the reference doc, section 9.

### Example Queries by Business Process

**Procure-to-Pay (P2P):**
- "Show me invoices from October 2026 over $10,000"
- "Which invoices need revalidation?"
- "What holds are on invoice INV-001234?"
- "List open purchase orders for supplier XYZ"
- "Show supplier details for 'Global Parts Inc'"
- "What requisitions were submitted this week?"

**Order-to-Cash (O2C):**
- "Look up sales order number SO-5678"
- "Which sales orders are currently on hold?"
- "What's the open AR balance for customer account 12345?"
- "Show me the latest receivables invoices"
- "Find receipt number RCT-9012"

**General:**
- "Describe the purchaseOrders resource to see what fields are available"
- "What journal batches exist?"
- "Show me the accounting period status"

## How It Works

```
┌─────────────┐     MCP (stdio)     ┌──────────────────┐     HTTPS/REST    ┌─────────────────┐
│ Claude Code  │◄──────────────────►│ fusion_server.py  │◄────────────────►│ Oracle Fusion    │
│ (VS Code or  │  JSON-RPC over     │ (MCP Server)      │  Basic Auth      │ Cloud REST API   │
│  terminal)   │  stdin/stdout      │ • Read-only tools │  + TLS           │ /fscmRestApi/... │
│              │                    │ • Row/field caps   │                  │ /crmRestApi/...  │
│              │                    │ • Audit logging    │                  │                  │
└─────────────┘                    └──────────────────┘                  └─────────────────┘
```

1. Claude Code starts the MCP server as a subprocess (stdio transport)
2. When you ask about Fusion data, Claude picks the right tool and parameters
3. The server reads credentials from the OS credential store (never from files)
4. The server makes authenticated REST calls to your Fusion pod
5. Results are field-filtered, row-capped, and returned as JSON
6. Claude summarizes the data in natural language

## Security Design

- **Two servers, separated by risk** — Reads live in `oracle-fusion` (pre-approved). Writes live in the separate `oracle-fusion-write` server, which is not pre-approved.
- **No secrets in files** — Password is stored in Windows Credential Manager / macOS Keychain / Linux Secret Service. Never in `.env`, config files, or command history.
- **Field filtering** — Read tools accept explicit `fields=` parameters to limit exposed data.
- **Row caps** — Maximum 100 rows per read request (50 for convenience tools).
- **Input validation** — Paths are regex-validated, `..` is rejected, methods and actions are whitelisted, filter values are sanitized.
- **Audit log** — Every API call (reads and writes) is logged to `mcp-servers/fusion-mcp/logs/mcp-calls.jsonl` with timestamp, tool, parameters, and status.
- **TLS certificate trust** — Uses the OS certificate store via `truststore`, so it works behind corporate HTTPS-inspecting proxies.
- **ERP text is data** — The CLAUDE.md and skills instruct Claude to never treat ERP record content (supplier names, descriptions, memos) as instructions.

<a name="write-safety"></a>
### Write safety — the confirm-first protocol

Writing to an ERP has real consequences (approving invoices, creating payments, deleting records). The write server enforces three independent gates:

1. **Preview before execute** — Every write tool defaults to `confirm=false`, which returns the exact request that *would* be sent **without touching Fusion**. Claude shows you the change, and only resends with `confirm=true` after you approve.
2. **Per-call permission prompt** — The write tools are deliberately left out of the pre-approved allow-list, so Claude Code prompts you before each write. (Only the read-only `get_process_status` is pre-approved.)
3. **Forced interaction flag** — Each write tool is marked `requiresUserInteraction`, so clients prompt even in automatic modes.

The bundled `oracle-fusion-write` skill instructs Claude to preview → show you the exact change → wait for explicit approval → execute, and to never batch-approve destructive changes on your behalf.

**Want reads only?** Remove the `oracle-fusion-write` block from `.mcp.json` (and its entries from `.claude/settings.local.json`). The read server is completely independent.

**Fusion-side control is the real boundary.** The surest limit on what can be written is the Fusion user's own roles. For a read-mostly setup, give the integration user inquiry (read) duties and add write privileges only for the specific areas you intend to automate.

## Troubleshooting

### Connection not working?

1. Run the doctor: double-click `Fusion-Doctor.cmd` (Windows) or run:
   ```bash
   cd mcp-servers/fusion-mcp
   .venv/bin/python fusion_setup_helper.py doctor --fix    # macOS/Linux
   .venv\Scripts\python.exe fusion_setup_helper.py doctor --fix  # Windows
   ```
2. The doctor checks: Python environment, config file, saved password, `.mcp.json` registration, Claude Code approval, MCP handshake, and live login.

### Common issues

| Symptom | Fix |
|---|---|
| `error: not configured` | Run `Connect-Oracle-Fusion.cmd` or `scripts/setup.sh` |
| `error 401` | Password expired or wrong. Re-run the setup script to enter a new password |
| `error 403` | User's Fusion roles don't cover this resource. Ask your Fusion admin to grant the relevant inquiry duty |
| `items: []` (empty results) | Usually a data security issue — the user may lack access to that business unit. This is NOT "no data exists" |
| `error 404` | Wrong resource path. Run `fusion_get("<resource>/describe")` to check |
| Network/TLS errors | Check VPN connection. If behind a proxy, `truststore` should handle it automatically |
| MCP server won't start | Run `Fusion-Doctor.cmd` — it rebuilds the venv if needed |

### Password changed?

Just re-run `Connect-Oracle-Fusion.cmd` (or `scripts/setup.sh`). It will ask for the new password and update the credential store.

## Customization

### Adding more REST resources

The `fusion_get` tool already supports any Fusion REST resource. To add dedicated convenience tools (like `list_invoices`):

1. Check the resource schema: ask Claude to run `fusion_get("<resource>/describe")`
2. Add the tool function to `mcp-servers/fusion-mcp/fusion_server.py`
3. Add the tool name to `READ_TOOLS` in `fusion_setup_helper.py`
4. Run `Fusion-Doctor.cmd --fix` to update permissions

### Extending to other Fusion areas

The server supports three API families:
- `fscm` (default) — Financials, Procurement, SCM, Projects
- `crm` — Sales, Service, Customer Data Management
- `hcm` — Human Capital Management

Use `fusion_get(path, api="crm")` or `fusion_get(path, api="hcm")` to access CRM or HCM resources.

### Building reference docs

The `fusion-kit/` directory contains scripts to regenerate the reference documentation from Oracle's 26D docs:

```bash
cd fusion-kit
python -I scripts/check_refs.py <file.md>                         # validate references
python -I scripts/assemble.py . ../docs/Oracle_Fusion_26D_P2P_O2C_Reference.md sources.json
python -I scripts/build_skill_resources.py . ../.claude/skills/oracle-fusion/references/rest-resources.md
```

## Oracle Fusion REST Quick Reference

### Filter syntax (REST framework version 4)
```
q=Supplier='Acme Corp' and InvoiceAmount>1000
q=InvoiceDate>='2026-01-01' and InvoiceDate<='2026-12-31'
q=UPPER(Supplier) LIKE '%ACME%'
q=StatusCode IN ('OPEN','CLOSED')
q=InvoiceNumber IS NULL
```

### Key resources

| Area | Resource path | Notes |
|---|---|---|
| AP Invoices | `invoices` | Payables invoices with lines, holds, installments |
| Invoice Holds | `invoiceHolds` | Holds placed/released on invoices |
| Purchase Orders | `purchaseOrders` | POs with lines, schedules, distributions |
| Suppliers | `suppliers` | Supplier master with sites, contacts, addresses |
| Requisitions | `purchaseRequisitions` | Purchase requisitions |
| Payments | `payablesPayments` | Payment records |
| Sales Orders | `salesOrdersForOrderHub` | Order hub orders with lines, holds |
| AR Invoices | `receivablesInvoices` | Receivables invoices |
| Receipts | `standardReceipts` | Cash receipts |
| Customer Balances | `receivablesCustomerAccountActivities` | Open balances, aging |
| Journals | `journalBatches` | GL journal batches |
| Ledger Balances | `ledgerBalances` | Account balances |

See [`.claude/skills/oracle-fusion/references/rest-resources.md`](.claude/skills/oracle-fusion/references/rest-resources.md) for the full catalog with child paths and custom actions.

## Requirements for Your Oracle Fusion Pod

- **Oracle Fusion Cloud** release 21D or later (tested on 26D)
- **REST API access** enabled on the pod
- A user account with:
  - REST API login capability (Basic auth or JWT)
  - Read-only roles/duties for the areas you need (e.g., Payables Invoice Inquiry, Supplier Profile Inquiry, Customer Account Inquiry)
  - Data security policies granting access to the relevant business units and ledgers

### Recommended Fusion roles (read-only)

Start with inquiry-only duties:
- Payables Invoice Inquiry
- Supplier Profile Inquiry
- Customer Account Inquiry
- General Ledger Reporting
- Purchase Order Inquiry

**Important:** Do not use broad roles like Financial Integration Specialist or Integration Specialist — they include write privileges. Create a custom read-only job role.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-tool`)
3. Make your changes
4. Run the doctor to verify (`Fusion-Doctor.cmd` or `scripts/setup.sh`)
5. Commit and push
6. Open a Pull Request

## License

MIT — see [LICENSE](LICENSE).

## Questions or Need Help?

If you run into issues, have questions, or want to discuss agentic AI on Oracle Fusion, reach out:

- **LinkedIn:** [Mayank Kumar](https://www.linkedin.com/in/mayankkumar8199/)
- **GitHub Issues:** [Open an issue](https://github.com/mayankkumar8199/oracle-fusion-claude-starter/issues)

Happy to help you get connected.

## Disclaimer

This project is not affiliated with or endorsed by Oracle Corporation. Oracle Fusion Cloud is a trademark of Oracle. Use this tool in accordance with your Oracle license agreement and your organization's security policies. The authors are not responsible for any unauthorized access or data exposure resulting from misconfiguration.
