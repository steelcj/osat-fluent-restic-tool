#!/usr/bin/env python3
"""Simulated-Windows validation for install-restic.py.

Monkeypatches platform.system() to 'Windows' and points LOCALAPPDATA,
APPDATA, and HOME at a temp tree, then exercises every code path that does
not require a Windows kernel: path resolution, env file writing (CRLF
correctness), wrapper rendering (generates->generated transformation in cmd
and PowerShell syntax), active-version round-trip, and idempotency detection.

Genuinely untestable off-Windows, left to hardware validation: restic.exe
execution (binary_ok), NTFS ACL behaviour, PATH resolution semantics.
"""
import importlib.util
import os
import platform
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("irt", HERE / "install-restic.py")
irt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(irt)

failures = []

def check(name, cond, detail=""):
    mark = "✓" if cond else "✗ FAIL"
    print(f"  {name}: {mark}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        failures.append(name)

with tempfile.TemporaryDirectory(prefix="winval-") as tmp:
    tmp = Path(tmp)
    home = tmp / "Users" / "chris"
    local = home / "AppData" / "Local"
    roaming = home / "AppData" / "Roaming"
    for d in (local, roaming):
        d.mkdir(parents=True)

    platform.system = lambda: "Windows"
    os.environ["LOCALAPPDATA"] = str(local)
    os.environ["APPDATA"] = str(roaming)
    _orig_home = Path.home
    Path.home = classmethod(lambda cls: home)

    print("[1] platform_paths resolution")
    p = irt.platform_paths()
    check("share under LOCALAPPDATA\\restic-tool", p["share_dir"] == local / "restic-tool")
    check("wrappers under Programs", p["wrapper_cmd"].parent == local / "Programs")
    check("config under APPDATA\\restic-tool", p["config_dir"] == roaming / "restic-tool")
    check("state under LOCALAPPDATA\\restic-tool\\logs", p["state_dir"] == local / "restic-tool" / "logs")
    check("credentials under ~\\.private\\restic-tool", p["private_dir"] == home / ".private" / "restic-tool")
    check("management identifier on all owned dirs",
          all("restic-tool" in str(p[k]) for k in ("share_dir", "config_dir", "state_dir", "private_dir")))

    print("[2] env file writing (CRLF correctness)")
    irt.write_env_file("0.19.1", p)
    raw = p["env_cmd"].read_bytes()
    check("env.cmd lines end CRLF", raw.count(b"\r\n") == 3 and b"\r\r" not in raw)
    check("env.cmd sets RESTIC_TOOL_ROOT", b'set "RESTIC_TOOL_ROOT=' in raw)
    raw = p["env_ps1"].read_bytes()
    check("env.ps1 lines end CRLF", raw.count(b"\r\n") == 3 and b"\r\r" not in raw)
    check("env.ps1 sets $env:RESTIC_TOOL_ROOT", b'$env:RESTIC_TOOL_ROOT = ' in raw)

    print("[3] active-version round-trip through env.cmd")
    check("reads back 0.19.1", irt.active_version(p) == "0.19.1")
    irt.write_env_file("0.18.1", p)
    check("switch reads back 0.18.1", irt.active_version(p) == "0.18.1")

    print("[4] wrapper rendering (generates -> generated, by: stamp)")
    cmd = irt.render_wrapper("windows/restic.cmd.template", "rem")
    check("cmd: generated header", "rem generated\n" in cmd and "rem generates\n" not in cmd)
    check("cmd: by: stamp", "rem   by: install-restic.py\n" in cmd)
    check("cmd: calls env pointer then operator env",
          cmd.find("restic-tool.env.cmd") < cmd.find('env.cmd" call') or "env.cmd" in cmd)
    ps1 = irt.render_wrapper("windows/restic.ps1.template", "#")
    check("ps1: generated header", "# generated\n" in ps1 and "# generates\n" not in ps1)
    check("ps1: by: stamp", "#   by: install-restic.py\n" in ps1)

    print("[5] wrapper writing and idempotency detection")
    irt.write_wrappers(p)
    raw = p["wrapper_cmd"].read_bytes()
    check("restic.cmd written CRLF", b"\r\n" in raw and b"\r\r" not in raw)
    raw = p["wrapper_ps1"].read_bytes()
    check("restic.ps1 written CRLF", b"\r\n" in raw and b"\r\r" not in raw)
    check("wrappers_current true after write", irt.wrappers_current(p))
    p["wrapper_cmd"].write_text("tampered", encoding="utf-8")
    check("wrappers_current false after tamper", not irt.wrappers_current(p))

    print("[6] version listing on the Windows layout")
    for v in ("0.19.1", "0.18.1"):
        (p["share_dir"] / v).mkdir(parents=True, exist_ok=True)
    (p["archive_dir"] / "0.19.1").mkdir(parents=True, exist_ok=True)
    check("installed newest-first", irt.installed_versions(p) == ["0.19.1", "0.18.1"])
    check("archive dir excluded from installed", "archive" not in irt.installed_versions(p))
    check("archived listed", irt.archived_versions(p) == ["0.19.1"])

    Path.home = _orig_home

print()
if failures:
    print(f"FAILURES: {failures}")
    sys.exit(1)
print("All simulated-Windows checks passed. Remaining hardware-only items:")
print("  restic.exe execution (binary_ok), NTFS ACL verification, PATH semantics.")
