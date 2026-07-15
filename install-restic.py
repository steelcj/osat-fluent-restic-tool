#!/usr/bin/env python3
# install-restic.py
"""
install-restic.py — Manage user-space installations of restic.

This manager owns the full lifecycle of restic installations: acquisition,
placement, activation, and removal. It installs versioned, self-contained
binaries side by side and never touches restic's own runtime domain
(~/.config/restic/, ~/.cache/restic/, repositories, or credentials).

Acquisition follows the Archetype 5 (self-contained binary) pattern:
upstream publishes single-binary release assets on GitHub with a SHA256SUMS
file, every download is verified against the published checksum before the
filesystem is touched, and every verified binary is copied to a local
archive so reinstall and rollback work offline (archive-first resolution).

Usage:
    install-restic.py --install [VERSION]  Install a version (default: latest)
    install-restic.py --switch VERSION     Point the env file at an installed version
    install-restic.py --status             Show installed, archived, and active versions
    install-restic.py --remove VERSION     Remove an installed version (archive is kept)
    install-restic.py --version            Show this manager's version

What this manager owns (the restic-tool management identifier):
    ~/.local/share/restic-tool/<version>/     Installed binaries, one per version
    ~/.local/share/restic-tool/archive/       Verified binaries, permanent local archive
    ~/.config/restic-tool/restic-tool.env     Active-version pointer, sourced by the wrapper
    ~/.local/state/restic-tool/               Manager state
    ~/.private/restic-tool/                   Credential directory (created, never populated)
    ~/.local/bin/restic                       Generated wrapper script

What this manager does not touch:
    ~/.config/restic-tool/env                 Operator environment (RESTIC_REPOSITORY etc.)
    ~/.config/restic/, ~/.cache/restic/       restic's own runtime domain
    Any restic repository or credential file

Requires: Python 3.8+ (standard library only) and network access when a
requested version is not already in the local archive.

Explicit versions install without querying the GitHub API; only latest-version
detection requires it.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

MANAGER_NAME = "osat-fluent-restic-tool"
TOOL_ID      = "restic-tool"          # management identifier (spec 10.8)
COMMAND      = "restic"               # wrapped command name

API_URL      = "https://api.github.com/repos/restic/restic/releases/latest"
RELEASE_BASE = "https://github.com/restic/restic/releases/download"
USER_AGENT   = f"{MANAGER_NAME}-installer"

_HERE         = Path(__file__).resolve().parent
_VERSION_FILE = _HERE / "VERSION"

DIR_MODE  = 0o700
FILE_MODE = 0o600
EXEC_MODE = 0o700

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

# (system, machine) -> (os_fragment, arch_fragment, archive_ext, binary_name)
# Asset filenames follow: restic_<version>_<os>_<arch>.<ext>  (no "v" prefix,
# unlike the git tag). The bz2 assets are compressed single files, not
# tarballs; Windows uses zip.
ASSET_PLATFORMS = {
    ("Linux",   "x86_64"):  ("linux",   "amd64", "bz2", "restic"),
    ("Linux",   "aarch64"): ("linux",   "arm64", "bz2", "restic"),
    ("Darwin",  "x86_64"):  ("darwin",  "amd64", "bz2", "restic"),
    ("Darwin",  "arm64"):   ("darwin",  "arm64", "bz2", "restic"),
    ("Windows", "AMD64"):   ("windows", "amd64", "zip", "restic.exe"),
}


# ── Small helpers ─────────────────────────────────────────────────────────────

def log(message: str) -> None:
    print(f"[RESTIC-TOOL] {message}")


def fail(message: str) -> None:
    print(f"[RESTIC-TOOL ERROR] {message}", file=sys.stderr)
    sys.exit(1)


def manager_version() -> str:
    try:
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "unknown"


def _tilde(path: Path) -> str:
    home = str(Path.home())
    s = str(path)
    return s.replace(home, "~", 1) if s.startswith(home) else s


def is_windows() -> bool:
    return platform.system() == "Windows"


# ── Platform paths ────────────────────────────────────────────────────────────

def platform_paths() -> dict:
    """Resolve every path once, at the boundary (archetype 5, section 4.2).

    Manager-owned directories carry the restic-tool management identifier;
    the plain name restic is reserved for the tool's own runtime domain and
    for the wrapper command (spec 10.8).
    """
    home = Path.home()

    if is_windows():
        local   = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        appdata = Path(os.environ.get("APPDATA",      home / "AppData" / "Roaming"))
        share   = local / TOOL_ID
        return {
            "share_dir":   share,
            "archive_dir": share / "archive",
            "config_dir":  appdata / TOOL_ID,
            "state_dir":   local / TOOL_ID / "logs",
            "private_dir": home / ".private" / TOOL_ID,
            "wrapper_dir": local / "Programs",
            "wrapper_cmd": local / "Programs" / f"{COMMAND}.cmd",
            "wrapper_ps1": local / "Programs" / f"{COMMAND}.ps1",
            "env_cmd":     appdata / TOOL_ID / f"{TOOL_ID}.env.cmd",
            "env_ps1":     appdata / TOOL_ID / f"{TOOL_ID}.env.ps1",
        }

    data  = Path(os.environ.get("XDG_DATA_HOME",   home / ".local" / "share"))
    bins  = Path(os.environ.get("XDG_BIN_HOME",    home / ".local" / "bin"))
    cfg   = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    state = Path(os.environ.get("XDG_STATE_HOME",  home / ".local" / "state"))
    share = data / TOOL_ID
    return {
        "share_dir":   share,
        "archive_dir": share / "archive",
        "config_dir":  cfg / TOOL_ID,
        "state_dir":   state / TOOL_ID,
        "private_dir": home / ".private" / TOOL_ID,
        "wrapper_dir": bins,
        "wrapper":     bins / COMMAND,
        "env_file":    cfg / TOOL_ID / f"{TOOL_ID}.env",
    }


# ── Permissions ───────────────────────────────────────────────────────────────

def ensure_dir(path: Path) -> None:
    """Create a manager-owned directory with owner-only permissions, and fail
    explicitly if an existing directory is broader than specified (spec §4).

    Windows ACL verification is a ROADMAP item; directories are created and
    inherit the profile's default owner-only ACLs.
    """
    created = not path.exists()
    path.mkdir(parents=True, exist_ok=True)
    if is_windows():
        # POSIX modes are advisory on Windows; NTFS ACLs inherit owner-only
        # from %USERPROFILE%. Explicit ACL verification is a ROADMAP item.
        return
    if created:
        path.chmod(DIR_MODE)          # set on creation
        return
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:                  # verify on subsequent runs
        fail(
            f"{_tilde(path)} has permissions {oct(mode)}, broader than the "
            f"owner-only {oct(DIR_MODE)} this collection requires; "
            "fix the permissions and rerun"
        )


def owner_only_file(path: Path, executable: bool = False) -> None:
    if is_windows():
        return
    path.chmod(EXEC_MODE if executable else FILE_MODE)


# ── Acquisition ───────────────────────────────────────────────────────────────

def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except (urllib.error.URLError, OSError) as error:
        fail(f"download failed for {url}: {error}")
    raise AssertionError("unreachable")


def latest_version() -> str:
    log("querying GitHub for the latest stable release")
    try:
        release = json.loads(fetch(API_URL))
    except json.JSONDecodeError as error:
        fail(f"could not parse the GitHub API response: {error}")
    tag = release.get("tag_name", "")
    if not tag.startswith("v") or len(tag) < 2:
        hint = release.get("message", "")
        extra = f" (API said: {hint})" if hint else ""
        fail(
            f"unexpected tag_name in API response: {tag!r}{extra}; "
            "pass an explicit version to --install to proceed without the API"
        )
    return tag[1:]


def asset_name(version: str, os_frag: str, arch_frag: str, ext: str) -> str:
    return f"restic_{version}_{os_frag}_{arch_frag}.{ext}"


def expected_checksum(checksums_text: str, name: str) -> str:
    for line in checksums_text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == name:
            return parts[0]
    fail(f"{name} is not listed in SHA256SUMS")
    raise AssertionError("unreachable")


def extract_binary(archive_bytes: bytes, name: str, ext: str,
                   binary_name: str, workdir: Path) -> Path:
    if ext == "bz2":
        # A compressed single file, not a tarball.
        extracted = workdir / binary_name
        extracted.write_bytes(bz2.decompress(archive_bytes))
        return extracted
    if ext == "zip":
        archive_path = workdir / name
        archive_path.write_bytes(archive_bytes)
        with zipfile.ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            if binary_name not in names:
                fail(f"the archive does not contain {binary_name!r}; found: {names}")
            zf.extract(binary_name, path=workdir)
        return workdir / binary_name
    fail(f"unsupported archive extension: {ext}")
    raise AssertionError("unreachable")


def binary_ok(binary_path: Path, version: str) -> bool:
    """True if the binary exists, is executable, and reports the expected
    version. restic outputs: 'restic X.Y.Z compiled with goX.Y on os/arch'."""
    if not (binary_path.is_file() and os.access(binary_path, os.X_OK)):
        return False
    try:
        result = subprocess.run(
            [str(binary_path), "version"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and version in result.stdout


# ── Env file and wrappers ─────────────────────────────────────────────────────

def active_version(paths: dict) -> str:
    env_file = paths["env_cmd"] if is_windows() else paths["env_file"]
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "RESTIC_TOOL_ROOT" in line and "=" in line:
            value = line.split("=", 1)[1].strip().strip('"')
            return Path(value).name
    return ""


def write_env_file(version: str, paths: dict) -> None:
    ensure_dir(paths["config_dir"])
    root = paths["share_dir"] / version

    if is_windows():
        # Explicit newline control: text mode would translate an embedded
        # \r\n to \r\r\n on Windows. Write \n and let open() render CRLF.
        with paths["env_cmd"].open("w", encoding="utf-8", newline="\r\n") as f:
            f.write(
                f'rem {paths["env_cmd"]}\n'
                f'rem Generated by {MANAGER_NAME}. Called by the cmd wrapper at runtime.\n'
                f'set "RESTIC_TOOL_ROOT={root}"\n'
            )
        with paths["env_ps1"].open("w", encoding="utf-8", newline="\r\n") as f:
            f.write(
                f'# {paths["env_ps1"]}\n'
                f'# Generated by {MANAGER_NAME}. Sourced by the PowerShell wrapper at runtime.\n'
                f'$env:RESTIC_TOOL_ROOT = "{root}"\n'
            )
        print(f"  env files written: {_tilde(paths['env_cmd'])}, {_tilde(paths['env_ps1'])}  ✓")
        return

    env_file = paths["env_file"]
    env_file.write_text(
        f'# {_tilde(env_file)}\n'
        f'# Generated by {MANAGER_NAME}. Sourced by the wrapper at runtime.\n'
        f'# Operator environment belongs in {_tilde(paths["config_dir"] / "env")},\n'
        f'# which this manager never touches.\n'
        f'RESTIC_TOOL_ROOT="{root}"\n',
        encoding="utf-8",
    )
    owner_only_file(env_file)
    print(f"  env file written: {_tilde(env_file)}  ✓")


def read_template(relpath: str) -> str:
    template_path = _HERE / "scripts" / relpath
    if not template_path.is_file():
        fail(f"wrapper template not found at {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_wrapper(relpath: str, comment: str) -> str:
    """Render a wrapper from its template. Convention: the template declares
    `generates`; the written wrapper records `generated`, stamped with its
    maker. `comment` is the line prefix for the target syntax (#, rem)."""
    rendered = read_template(relpath)
    rendered = rendered.replace(f"{comment} generates\n", f"{comment} generated\n", 1)
    marker = f"{comment}   path: "
    at = rendered.find(marker, rendered.find(f"{comment} generated\n"))
    if at != -1:
        line_end = rendered.find("\n", at) + 1
        rendered = (rendered[:line_end]
                    + f"{comment}   by: install-restic.py\n"
                    + rendered[line_end:])
    return rendered


def write_wrappers(paths: dict) -> None:
    # The wrapper directory (~/.local/bin, %LOCALAPPDATA%\Programs) is shared
    # infrastructure: distros and other tools create it and expect it
    # traversable. The manager owns the wrapper *file* inside it, never the
    # directory, so no owner-only enforcement here — only creation if absent.
    paths["wrapper_dir"].mkdir(parents=True, exist_ok=True)
    if is_windows():
        for key, relpath, comment in (
                ("wrapper_cmd", "windows/restic.cmd.template", "rem"),
                ("wrapper_ps1", "windows/restic.ps1.template", "#")):
            wrapper = paths[key]
            with wrapper.open("w", encoding="utf-8", newline="\r\n") as f:
                f.write(render_wrapper(relpath, comment))
            print(f"  wrapper written:  {_tilde(wrapper)}  ✓")
        return
    wrapper = paths["wrapper"]
    wrapper.write_text(render_wrapper("nix/wrapper.template", "#"),
                       encoding="utf-8")
    owner_only_file(wrapper, executable=True)
    print(f"  wrapper written:  {_tilde(wrapper)}  ✓")


def wrappers_current(paths: dict) -> bool:
    if is_windows():
        return (
            paths["wrapper_cmd"].is_file()
            and paths["wrapper_cmd"].read_text(encoding="utf-8")
                == render_wrapper("windows/restic.cmd.template", "rem")
            and paths["wrapper_ps1"].is_file()
            and paths["wrapper_ps1"].read_text(encoding="utf-8")
                == render_wrapper("windows/restic.ps1.template", "#")
        )
    return (
        paths["wrapper"].is_file()
        and paths["wrapper"].read_text(encoding="utf-8")
            == render_wrapper("nix/wrapper.template", "#")
    )


# ── Provenance ────────────────────────────────────────────────────────────────

def write_provenance(install_root: Path, name: str, sha256: str,
                     source: str) -> None:
    (install_root / "PROVENANCE").write_text(
        f"manager: {MANAGER_NAME} {manager_version()}\n"
        f"asset: {name}\n"
        f"sha256: {sha256}\n"
        f"source: {source}\n"
        f"installed: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n",
        encoding="utf-8",
    )
    owner_only_file(install_root / "PROVENANCE")


# ── Lifecycle: install ────────────────────────────────────────────────────────

def installed_versions(paths: dict):
    """Installed version strings, newest first (dotted-numeric sort).
    The archive/ directory is excluded by the digits-only test."""
    share = paths["share_dir"]
    if not share.is_dir():
        return []
    found = []
    for entry in share.iterdir():
        parts = entry.name.split(".")
        if entry.is_dir() and all(p.isdigit() for p in parts):
            found.append(tuple(int(p) for p in parts))
    return [".".join(str(n) for n in v) for v in sorted(found, reverse=True)]


def archived_versions(paths: dict):
    archive = paths["archive_dir"]
    if not archive.is_dir():
        return []
    found = []
    for entry in archive.iterdir():
        parts = entry.name.split(".")
        if entry.is_dir() and all(p.isdigit() for p in parts):
            found.append(tuple(int(p) for p in parts))
    return [".".join(str(n) for n in v) for v in sorted(found, reverse=True)]


def acquire_binary(version: str, binary_name: str, os_frag: str,
                   arch_frag: str, ext: str, paths: dict) -> tuple[Path, str, str]:
    """Archive-first resolution: restore a verified binary from the local
    archive when present; otherwise download, verify against SHA256SUMS,
    extract, and archive. Returns (binary_source_path, sha256, source_label).
    The returned path lives either in the archive or in a caller-owned
    tempdir recorded in paths['_workdir']."""
    archived = paths["archive_dir"] / version / binary_name
    if binary_ok(archived, version):
        sha256 = hashlib.sha256(archived.read_bytes()).hexdigest()
        log(f"restoring v{version} from the local archive (no network needed)")
        return archived, sha256, f"local archive ({_tilde(archived)})"

    name = asset_name(version, os_frag, arch_frag, ext)
    base = f"{RELEASE_BASE}/v{version}"

    log(f"downloading {base}/{name}")
    archive_bytes = fetch(f"{base}/{name}")

    log("downloading SHA256SUMS")
    checksums_text = fetch(f"{base}/SHA256SUMS").decode("utf-8")

    log("verifying SHA-256 checksum against the published SHA256SUMS")
    expected = expected_checksum(checksums_text, name)
    actual = hashlib.sha256(archive_bytes).hexdigest()
    if actual != expected:
        fail(f"checksum verification failed for {name}; refusing to install")

    workdir = Path(tempfile.mkdtemp(prefix=f"{TOOL_ID}-"))
    paths["_workdir"] = workdir
    log(f"extracting {binary_name}")
    extracted = extract_binary(archive_bytes, name, ext, binary_name, workdir)
    owner_only_file(extracted, executable=True)

    # No claim without a verification behind it: prove the binary executes
    # and reports the requested version before it enters the permanent
    # archive. The archive holds only proven binaries.
    if not binary_ok(extracted, version):
        fail(
            f"the downloaded binary does not execute or does not report "
            f"v{version}; refusing to archive or install it"
        )
    print(f"  binary verified:  executes and reports v{version}  ✓")

    binary_sha = hashlib.sha256(extracted.read_bytes()).hexdigest()

    # Archive the verified binary before placing it (archetype 5, 4.10).
    archive_root = paths["archive_dir"] / version
    ensure_dir(paths["share_dir"])
    ensure_dir(paths["archive_dir"])
    ensure_dir(archive_root)
    shutil.copyfile(extracted, archive_root / binary_name)
    owner_only_file(archive_root / binary_name, executable=True)
    print(f"  archived:         {_tilde(archive_root / binary_name)}  ✓")

    return extracted, binary_sha, f"{base}/{name}"


def cmd_install(version_arg: str) -> int:
    paths = platform_paths()

    sys_key = (platform.system(), platform.machine())
    if sys_key not in ASSET_PLATFORMS:
        fail(
            f"platform {sys_key[0]}/{sys_key[1]} is not supported; "
            "see ROADMAP.md for planned platform bringup"
        )
    os_frag, arch_frag, ext, binary_name = ASSET_PLATFORMS[sys_key]

    if version_arg:
        if not SEMVER.match(version_arg):
            fail(f"expected a version like 0.19.1, got {version_arg!r}")
        version = version_arg
    else:
        version = latest_version()
        log(f"latest stable version is v{version}")

    install_root = paths["share_dir"] / version
    binary_path  = install_root / binary_name

    # Idempotency: already installed, active, and wrappers current.
    if (binary_ok(binary_path, version)
            and active_version(paths) == version
            and wrappers_current(paths)):
        log(f"restic v{version} is already installed and active; nothing to do")
        return 0

    if binary_ok(binary_path, version):
        ensure_dir(paths["share_dir"])   # verify permissions on this path too
        log(f"v{version} is already installed at {_tilde(install_root)}; activating it")
        write_env_file(version, paths)
        write_wrappers(paths)
        post_install_notes(version, paths)
        return 0

    if install_root.exists():
        fail(
            f"{_tilde(install_root)} exists but does not contain a healthy "
            f"v{version} binary; remove it with --remove {version} and rerun"
        )

    log(f"installing restic v{version}")
    source_path, sha256, source = acquire_binary(
        version, binary_name, os_frag, arch_frag, ext, paths)

    try:
        ensure_dir(paths["share_dir"])
        ensure_dir(install_root)
        shutil.copyfile(source_path, binary_path)
        owner_only_file(binary_path, executable=True)
    finally:
        workdir = paths.pop("_workdir", None)
        if workdir is not None:
            shutil.rmtree(workdir, ignore_errors=True)

    if not binary_ok(binary_path, version):
        # Refuse-and-remove: never leave a broken artifact where a later
        # --switch could activate it.
        shutil.rmtree(install_root, ignore_errors=True)
        fail(
            f"the placed binary does not report v{version}. Refusing to "
            "activate a broken artifact; removed it. The archive copy, if "
            "any, was verified before archiving and remains available."
        )
    write_provenance(install_root, asset_name(version, os_frag, arch_frag, ext),
                     sha256, source)
    print(f"  binary placed:    {_tilde(binary_path)}  ✓  (restic v{version})")

    # Remaining manager-owned directories, created and permission-checked.
    ensure_dir(paths["state_dir"])
    ensure_dir(paths["private_dir"].parent)
    ensure_dir(paths["private_dir"])

    write_env_file(version, paths)
    write_wrappers(paths)

    print()
    log(f"restic {version} installed and active.")
    post_install_notes(version, paths)
    return 0


def post_install_notes(version: str, paths: dict) -> None:
    print("  Verify with:  restic version")
    wrapper_dir = paths["wrapper_dir"]
    if str(wrapper_dir) not in os.environ.get("PATH", "").split(os.pathsep):
        print()
        print(f"  Note: {_tilde(wrapper_dir)} is not on your PATH.")
        if is_windows():
            print(f"    Add {wrapper_dir} to your user PATH (see README).")
        else:
            print('    Add it with:  export PATH="$HOME/.local/bin:$PATH"')
    if not is_windows():
        resolved = shutil.which(COMMAND)
        if resolved and Path(resolved) != paths["wrapper"]:
            print()
            print(f"  WARNING: the shell currently resolves restic to {resolved};")
            print(f"    adjust PATH so {_tilde(paths['wrapper'])} takes precedence.")


# ── Lifecycle: switch, status, remove ─────────────────────────────────────────

def cmd_switch(version: str) -> int:
    paths = platform_paths()
    if not (paths["share_dir"] / version).is_dir():
        print(f"[RESTIC-TOOL ERROR] {version} is not installed. Installed versions:",
              file=sys.stderr)
        for v in installed_versions(paths):
            print(f"  {v}", file=sys.stderr)
        archived_only = [v for v in archived_versions(paths)
                         if v not in installed_versions(paths)]
        if archived_only:
            print("  In the local archive (reinstall with --install VERSION):",
                  file=sys.stderr)
            for v in archived_only:
                print(f"  {v}", file=sys.stderr)
        return 1
    write_env_file(version, paths)
    write_wrappers(paths)
    log(f"Active version is now {version}.")
    return 0


def cmd_status() -> int:
    paths = platform_paths()
    active = active_version(paths)
    versions = installed_versions(paths)
    archived = archived_versions(paths)
    env_file = paths["env_cmd"] if is_windows() else paths["env_file"]

    log(f"{MANAGER_NAME} {manager_version()}")
    print(f"  install root:  {_tilde(paths['share_dir'])}")
    print(f"  archive:       {_tilde(paths['archive_dir'])}")
    print(f"  env file:      {_tilde(env_file)}"
          + ("" if env_file.exists() else "  (absent)"))
    if not versions:
        print("  installed:     none")
    else:
        print("  installed:")
        for v in versions:
            print(f"    {v}" + ("  ← active" if v == active else ""))
    if archived:
        print("  archived:      " + ", ".join(archived))
    if active and active not in versions:
        print(f"  [WARNING] env file points at {active}, which is not installed.")
    return 0


def cmd_remove(version: str) -> int:
    paths = platform_paths()
    install_root = paths["share_dir"] / version
    if not install_root.is_dir():
        print(f"[RESTIC-TOOL ERROR] {version} is not installed.", file=sys.stderr)
        return 1
    if version == active_version(paths):
        print(f"[RESTIC-TOOL ERROR] {version} is the active version. Switch to",
              file=sys.stderr)
        print("  another version first, then remove this one.", file=sys.stderr)
        return 1
    shutil.rmtree(install_root)
    log(f"{version} removed.")
    if (paths["archive_dir"] / version).is_dir():
        print(f"  The verified binary remains in the archive; reinstall offline")
        print(f"  at any time with:  --install {version}")
    return 0


# ── Entry point ───────────────────────────────────────────────────────────────

def root_guard() -> None:
    """Refuse to mutate the filesystem as root. Read-only commands
    (--status, --version, --help) are permitted in any context."""
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        fail(
            "this manager writes to the invoking user's home directory; "
            "do not run with sudo"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="install-restic.py",
        description="Manage user-space installations of restic.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  install-restic.py --install            install the latest stable release\n"
            "  install-restic.py --install 0.19.1     install a pinned version (no API call)\n"
            "  install-restic.py --switch 0.18.1      activate an installed version\n"
            "  install-restic.py --status             show installed, archived, active\n"
            "  install-restic.py --remove 0.18.1      remove a non-active version\n"
        ),
    )
    parser.add_argument("--install", nargs="?", const="", metavar="VERSION",
                        help="Install VERSION (default: latest stable from GitHub).")
    parser.add_argument("--switch", metavar="VERSION",
                        help="Point the env file at an already-installed version.")
    parser.add_argument("--status", action="store_true",
                        help="Show installed, archived, and active versions.")
    parser.add_argument("--remove", metavar="VERSION",
                        help="Remove an installed version (its archive copy is kept).")
    parser.add_argument("--version", action="store_true",
                        help="Show this manager's version and exit.")
    args = parser.parse_args()

    if args.version:
        print(f"{MANAGER_NAME} {manager_version()}")
        return 0
    if args.install is not None:
        root_guard()
        return cmd_install(args.install)
    if args.switch:
        root_guard()
        return cmd_switch(args.switch)
    if args.status:
        return cmd_status()
    if args.remove:
        root_guard()
        return cmd_remove(args.remove)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
