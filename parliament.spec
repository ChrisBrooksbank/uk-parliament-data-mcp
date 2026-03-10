# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the parliament CLI.

Produces a single standalone executable that bundles the CLI and its
dependencies — no Python installation required on the target machine.

Usage:
    python scripts/build-exe.py          # recommended wrapper
    pyinstaller parliament.spec          # direct invocation
"""

import sys
from pathlib import Path

block_cipher = None

# Paths
SRC = Path("src")
CLI_PKG = SRC / "uk_parliament_mcp" / "cli"

a = Analysis(
    [str(CLI_PKG / "main.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[
        # Bundle the API metadata JSON so cli/api.py can find it at runtime
        (str(CLI_PKG / "api_metadata.json"), "uk_parliament_mcp/cli"),
    ],
    hiddenimports=[
        # Typer / Click need these at runtime
        "typer",
        "click",
        "rich",
        "httpx",
        "httpx._transports",
        "httpx._transports.default",
        # Our own CLI sub-modules (imported dynamically by Typer)
        "uk_parliament_mcp.cli.api",
        "uk_parliament_mcp.cli.bills",
        "uk_parliament_mcp.cli.committees",
        "uk_parliament_mcp.cli.composite",
        "uk_parliament_mcp.cli.digest",
        "uk_parliament_mcp.cli.guide",
        "uk_parliament_mcp.cli.hansard",
        "uk_parliament_mcp.cli.interests",
        "uk_parliament_mcp.cli.legislation",
        "uk_parliament_mcp.cli.live",
        "uk_parliament_mcp.cli.members",
        "uk_parliament_mcp.cli.procedures",
        "uk_parliament_mcp.cli.questions",
        "uk_parliament_mcp.cli.try_it",
        "uk_parliament_mcp.cli.votes",
        "uk_parliament_mcp.cli.watch",
        "uk_parliament_mcp.cli.formatters",
        "uk_parliament_mcp.cli.pagination",
        "uk_parliament_mcp.cli.renderers",
        "uk_parliament_mcp.cli.utils",
        "uk_parliament_mcp.http_client",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # MCP server components (not needed for CLI)
        "uk_parliament_mcp.server",
        "uk_parliament_mcp.__main__",
        "uk_parliament_mcp.tools",
        "mcp",
        "anyio",
        "starlette",
        "uvicorn",
        # Test frameworks
        "pytest",
        "pytest_asyncio",
        "pytest_httpx",
        "pytest_cov",
        # GUI toolkits
        "tkinter",
        "_tkinter",
        "turtle",
        # Other unused stdlib / heavy modules
        "unittest",
        "doctest",
        "pdb",
        "lib2to3",
        "xmlrpc",
        "multiprocessing",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    a.zipfiles,
    [],
    name="parliament",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
