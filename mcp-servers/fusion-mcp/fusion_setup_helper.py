"""Setup and health tool for the oracle-fusion MCP server.

  python fusion_setup_helper.py config <pod_url> <user>   write fusion_config.json (no secrets)
  python fusion_setup_helper.py store                     ask for the password (hidden) and save it in the OS credential store
  python fusion_setup_helper.py test                      one 1-row read to check the login (prints the HTTP status only)
  python fusion_setup_helper.py doctor [--fix]            check every link in the chain; --fix repairs what it can
"""
import getpass
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))            # repo root (two levels up)
CONFIG = os.environ.get("FUSION_CONFIG", os.path.join(HERE, "fusion_config.json"))
SERVICE = "oracle-fusion"
VENV_PY = os.path.join(HERE, ".venv", "Scripts", "python.exe")
SERVER = os.path.join(HERE, "fusion_server.py")
WRITE_SERVER = os.path.join(HERE, "fusion_write_server.py")
MCP_JSON = os.path.join(PROJECT, ".mcp.json")
SETTINGS_LOCAL = os.path.join(PROJECT, ".claude", "settings.local.json")
READ_TOOLS = ["connection_status", "get_api_info", "list_invoices", "get_invoice", "fusion_get"]
WRITE_TOOLS = ["fusion_write", "fusion_action", "submit_scheduled_process", "get_process_status",
               "import_bulk_data", "run_report"]
# Only the read-only status check is pre-approved. The actual write tools are intentionally left OUT of
# the allow-list so Claude Code prompts the user before every create/update/delete/action/import.
WRITE_ALLOW = ["mcp__oracle-fusion-write__get_process_status"]
CONNECT_CMD = os.path.join(PROJECT, "Connect-Oracle-Fusion.cmd")


def load():
    with open(CONFIG, encoding="utf-8-sig") as f:
        return json.load(f)


def tls():
    try:
        import ssl, truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:
        return True


def cmd_config(pod, user):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump({"base_url": pod.rstrip("/"), "user": user}, f, indent=2)
    print(f"      Saved pod URL and user name to {CONFIG}")
    return 0


def cmd_store():
    import keyring
    c = load()
    pw = getpass.getpass(f"      Fusion password for {c['user']} (typing is hidden): ")
    if not pw:
        print("      No password entered - nothing saved.")
        return 1
    keyring.set_password(SERVICE, c["user"], pw)
    backend = type(keyring.get_keyring()).__name__
    print(f"      Password saved in OS credential store ({backend}, entry 'oracle-fusion').")
    return 0


def login_test():
    """Return (http_status_or_None, message)."""
    import httpx2, keyring
    c = load()
    pw = keyring.get_password(SERVICE, c["user"])
    if not pw:
        return None, "no saved password"
    url = f"{c['base_url']}/fscmRestApi/resources/11.13.18.05/invoices"
    try:
        r = httpx2.get(url, params={"limit": 1, "onlyData": "true", "fields": "InvoiceId"},
                       auth=httpx2.BasicAuth(c["user"], pw), headers={"Accept": "application/json"},
                       timeout=90, verify=tls())
    except httpx2.HTTPError as e:
        return None, f"cannot reach Fusion ({str(e)[:160]}) - check network/VPN"
    return r.status_code, {
        200: "login OK",
        401: "login REJECTED: wrong or expired password, or an SSO-only user. Sign in to Fusion in a browser, "
             "set/confirm the password, then run Connect-Oracle-Fusion.cmd again",
        403: "login OK, but this user cannot read Payables invoices (other areas may still work)",
    }.get(r.status_code, f"unexpected HTTP {r.status_code}")


def cmd_test():
    code, msg = login_test()
    print(f"      {msg}")
    return 0 if code in (200, 403) else (1 if code is None and msg == "no saved password" else 3)


def wanted_mcp_entry():
    return {"type": "stdio", "command": VENV_PY, "args": [SERVER], "env": {}}


def wanted_write_entry():
    return {"type": "stdio", "command": VENV_PY, "args": [WRITE_SERVER], "env": {}}


def read_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def handshake(server=SERVER):
    """Start a server exactly as Claude Code will and list its tools."""
    p = subprocess.Popen([VENV_PY, server], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8")
    try:
        def send(m):
            p.stdin.write(json.dumps(m) + "\n")
            p.stdin.flush()

        def recv():
            line = p.stdout.readline()
            if not line:
                raise RuntimeError("server exited: " + p.stderr.read()[-300:])
            return json.loads(line)

        t0 = time.time()
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "doctor", "version": "1"}}})
        recv()
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = [t["name"] for t in recv()["result"]["tools"]]
        return tools, time.time() - t0
    finally:
        try:
            p.stdin.close()
            p.wait(timeout=10)
        except Exception:
            p.kill()


def cmd_doctor(fix):
    ok = True

    def report(status, what, detail=""):
        nonlocal ok
        if status == "FAIL":
            ok = False
        print(f"  [{status:5}] {what}" + (f" - {detail}" if detail else ""))

    print(f"\nOracle Fusion connection doctor  (project: {PROJECT})\n")
    # 1 Python environment
    try:
        import mcp, httpx2, keyring, truststore  # noqa: F401
        report("OK", "Python environment", sys.executable)
    except Exception as e:
        report("FAIL", "Python environment", f"{e}; run Fusion-Doctor.cmd (it rebuilds the environment)")
        return 1
    if os.path.normcase(sys.executable) != os.path.normcase(VENV_PY):
        report("WARN", "doctor not running from the project venv", sys.executable)
    # 2 settings file
    try:
        c = load()
        assert c.get("base_url") and c.get("user")
        report("OK", "settings file", f"{c['base_url']}  user {c['user']}")
    except Exception:
        report("FAIL", "settings file missing or invalid", f"double-click {CONNECT_CMD}")
        c = None
    # 3 password
    if c:
        import keyring as kr
        if kr.get_password(SERVICE, c["user"]):
            report("OK", "password saved in OS credential store")
        else:
            report("FAIL", "no saved password", f"run the setup script ({CONNECT_CMD})")
    # 4 project MCP registration (both the read server and the write server)
    mj = read_json(MCP_JSON)
    want_servers = {"oracle-fusion": wanted_mcp_entry(), "oracle-fusion-write": wanted_write_entry()}
    outdated = [n for n, e in want_servers.items() if mj.get("mcpServers", {}).get(n) != e]
    if not outdated:
        report("OK", "both servers registered in .mcp.json", MCP_JSON)
    elif fix:
        servers = mj.setdefault("mcpServers", {})
        for n, e in want_servers.items():
            servers[n] = e
        write_json(MCP_JSON, mj)
        report("FIXED", "registered oracle-fusion and oracle-fusion-write in .mcp.json", MCP_JSON)
    else:
        report("FAIL", f"missing or outdated in .mcp.json: {outdated}", "run with --fix")
    # 5 approval + tool permissions (project-local settings)
    #   Both servers are enabled. Read tools and the read-only status check are pre-approved.
    #   The write tools are deliberately NOT allowed here, so Claude Code prompts before each write.
    st = read_json(SETTINGS_LOCAL)
    enabled = st.get("enabledMcpjsonServers", [])
    allow = st.get("permissions", {}).get("allow", [])
    want_enabled = ["oracle-fusion", "oracle-fusion-write"]
    want_allow = [f"mcp__oracle-fusion__{t}" for t in READ_TOOLS] + WRITE_ALLOW
    if all(s in enabled for s in want_enabled) and all(a in allow for a in want_allow):
        report("OK", "both servers approved; reads allowed, writes left to prompt", SETTINGS_LOCAL)
    elif fix:
        st["enabledMcpjsonServers"] = enabled + [s for s in want_enabled if s not in enabled]
        perms = st.setdefault("permissions", {})
        perms["allow"] = allow + [a for a in want_allow if a not in allow]
        write_json(SETTINGS_LOCAL, st)
        report("FIXED", "approved both servers; reads allowed, writes still prompt", SETTINGS_LOCAL)
    else:
        report("FAIL", "servers not pre-approved in .claude/settings.local.json", "run with --fix")
    # 6 both servers start like Claude Code starts them
    try:
        tools, secs = handshake(SERVER)
        missing = [t for t in READ_TOOLS if t not in tools]
        report("OK" if not missing else "FAIL", "read server starts and answers MCP",
               f"{len(tools)} tools in {secs:.1f}s" + (f"; missing {missing}" if missing else ""))
    except Exception as e:
        report("FAIL", "read server did not start", str(e)[:300])
    try:
        wtools, wsecs = handshake(WRITE_SERVER)
        wmissing = [t for t in WRITE_TOOLS if t not in wtools]
        report("OK" if not wmissing else "FAIL", "write server starts and answers MCP",
               f"{len(wtools)} tools in {wsecs:.1f}s" + (f"; missing {wmissing}" if wmissing else ""))
    except Exception as e:
        report("FAIL", "write server did not start", str(e)[:300])
    # 7 live login
    if c:
        code, msg = login_test()
        report("OK" if code in (200, 403) else "FAIL", "live login test", f"HTTP {code}: {msg}" if code else msg)
    print("\nRESULT: " + ("everything OK - start a new Claude Code chat in the project folder and use oracle-fusion."
                          if ok else "problems found - follow the hints above."))
    return 0 if ok else 2


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["config"] and len(a) == 3:
        sys.exit(cmd_config(a[1], a[2]))
    if a[:1] == ["store"]:
        sys.exit(cmd_store())
    if a[:1] == ["test"]:
        sys.exit(cmd_test())
    if a[:1] == ["doctor"]:
        sys.exit(cmd_doctor("--fix" in a))
    print(__doc__)
    sys.exit(64)
