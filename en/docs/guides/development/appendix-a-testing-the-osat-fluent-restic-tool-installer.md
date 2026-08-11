# Appendix A — Testing the osat-fluent-restic-tool installer

This appendix records manual test sessions of the installer tool itself. It's a reference for tool development, not part of the standard backup procedure above.

Test plain installation

    python3 install-restic.py --install

First-time installation output:

    python3 install-restic.py
    usage: install-restic.py [-h] [--install [VERSION]] [--switch VERSION] [--status] [--remove VERSION] [--version]
    Manage user-space installations of restic.
    options:
      -h, --help           show this help message and exit
      --install [VERSION]  Install VERSION (default: latest stable from GitHub).
      --switch VERSION     Point the env file at an already-installed version.
      --status             Show installed, archived, and active versions.
      --remove VERSION     Remove an installed version (its archive copy is kept).
      --version            Show this manager's version and exit.
    Examples:
      install-restic.py --install            install the latest stable release
      install-restic.py --install 0.19.1     install a pinned version (no API call)
      install-restic.py --switch 0.18.1      activate an installed version
      install-restic.py --status             show installed, archived, active
      install-restic.py --remove 0.18.1      remove a non-active version

Output example when the tool is already installed:

    [RESTIC-TOOL] querying GitHub for the latest stable release
    [RESTIC-TOOL] latest stable version is v0.19.1
    [RESTIC-TOOL] v0.19.1 is already installed at ~/.local/share/restic-tool/0.19.1; activating it
      env file written: ~/.config/restic-tool/restic-tool.env  ✓
      wrapper written:  ~/.local/bin/restic  ✓
      Verify with:  restic version

Install a different restic version

    python3 install-restic.py --install 0.18.1

Output example:

    [RESTIC-TOOL] installing restic v0.18.1
    [RESTIC-TOOL] downloading https://github.com/restic/restic/releases/download/v0.18.1/restic_0.18.1_linux_amd64.bz2
    [RESTIC-TOOL] downloading SHA256SUMS
    [RESTIC-TOOL] verifying SHA-256 checksum against the published SHA256SUMS
    [RESTIC-TOOL] extracting restic
      binary verified:  executes and reports v0.18.1  ✓
      archived:         ~/.local/share/restic-tool/archive/0.18.1/restic  ✓
      binary placed:    ~/.local/share/restic-tool/0.18.1/restic  ✓  (restic v0.18.1)
      env file written: ~/.config/restic-tool/restic-tool.env  ✓
      wrapper written:  ~/.local/bin/restic  ✓
    [RESTIC-TOOL] restic 0.18.1 installed and active.
      Verify with:  restic version

Verify

    restic version

Output example:

    restic 0.19.1 compiled with go1.26.4 on linux/amd64

This shows the previously installed version, not 0.18.1 — see Roadmap and known issues below.

Activate a different installed restic version

    python3 install-restic.py --switch 0.18.1

Expected output:

      env file written: ~/.config/restic-tool/restic-tool.env  ✓
      wrapper written:  ~/.local/bin/restic  ✓
    [RESTIC-TOOL] Active version is now 0.18.1.

Switch back to the latest version

    python3 install-restic.py --switch 0.19.1

Expected output:

      env file written: ~/.config/restic-tool/restic-tool.env  ✓
      wrapper written:  ~/.local/bin/restic  ✓
    [RESTIC-TOOL] Active version is now 0.19.1.

Remove an older restic version

In this test, version 0.18.1 was never actually used, so it can be removed:

    python3 install-restic.py --remove 0.18.1

Output example:

    [RESTIC-TOOL] 0.18.1 removed.
      The verified binary remains in the archive; reinstall offline
      at any time with:  --install 0.18.1