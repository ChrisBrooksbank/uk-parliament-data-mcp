#!/usr/bin/env python3
"""The session recorded by scripts/record-mcp-demo.sh.

Asks Claude Code a question with only this repo's MCP server attached, and
shows the run as it happens: the question, each MCP tool call with the
Parliament API URL it hit, and the final answer. Nothing is scripted except the
question; tool calls and the answer are whatever the model actually does, read
live from `claude -p --output-format stream-json`.

    python scripts/mcp-demo-session.py "Who is the MP for SW1A 1AA?"
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text

SERVER = "uk-parliament"
console = Console(highlight=False)


def type_out(prefix: str, text: str, delay: float = 0.03) -> None:
    # Wrap at word boundaries ourselves; the terminal would break mid-word
    lines = textwrap.wrap(text, width=console.width - 3)
    console.print(prefix, end="")
    for i, line in enumerate(lines):
        if i:
            console.print("\n  ", end="")
        for ch in line:
            console.print(ch, end="", style="bold")
            time.sleep(delay)
    console.print()
    time.sleep(0.6)


def result_urls(content: Any) -> list[str]:
    """Pull the Parliament API URLs out of a tool result, if it reports them."""
    texts = [c.get("text", "") for c in content] if isinstance(content, list) else [str(content)]
    urls: list[str] = []
    for text in texts:
        try:
            payload = json.loads(text)
            if isinstance(payload, dict) and "result" in payload:
                payload = json.loads(payload["result"])
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("url"), str):
            urls.append(payload["url"])
    return urls


def show_tool_call(name: str, args: dict[str, Any]) -> None:
    tool = name.removeprefix(f"mcp__{SERVER}__")
    arg_text = ", ".join(f"{k}={json.dumps(v)}" for k, v in args.items())
    line = Text("● ", style="cyan")
    line.append(f"{SERVER} · ", style="dim")
    line.append(tool, style="bold cyan")
    line.append(f"({arg_text})", style="cyan")
    console.print(line)


def main() -> int:
    question = sys.argv[1]
    config = {
        "mcpServers": {SERVER: {"command": sys.executable, "args": ["-m", "uk_parliament_mcp"]}}
    }

    console.print("[dim]Claude Code with only the uk-parliament MCP server attached[/dim]\n")
    type_out("[bold green]>[/bold green] ", question)
    console.print()

    with tempfile.TemporaryDirectory() as workdir:
        config_path = Path(workdir) / "mcp.json"
        config_path.write_text(json.dumps(config))
        proc = subprocess.Popen(
            [
                "claude",
                "-p",
                question,
                "--mcp-config",
                str(config_path),
                "--strict-mcp-config",
                "--allowedTools",
                f"mcp__{SERVER}",
                "--max-turns",
                "15",
                "--output-format",
                "stream-json",
                "--verbose",
            ],
            cwd=workdir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        assert proc.stdout is not None
        texts: list[str] = []
        ours: set[str] = set()  # ids of this server's tool calls
        status = console.status("[dim]Working…[/dim]", spinner="dots")
        status.start()
        for line in proc.stdout:
            event = json.loads(line)
            if event.get("type") not in ("assistant", "user"):
                continue
            content = event["message"]["content"]
            if not isinstance(content, list):
                continue
            for block in content:
                kind = block.get("type")
                if kind == "tool_use" and block["name"].startswith(f"mcp__{SERVER}__"):
                    ours.add(block["id"])
                    if texts:
                        console.print(Text(texts.pop(), style="dim italic"))
                    show_tool_call(block["name"], block["input"])
                elif kind == "tool_result" and block.get("tool_use_id") in ours:
                    urls = result_urls(block.get("content"))
                    for url in urls:
                        console.print(Text(f"  ⎿ {url}", style="dim"))
                    if not urls:
                        size = len(json.dumps(block.get("content"))) / 1024
                        console.print(
                            Text(f"  ⎿ {size:.1f} KB from several Parliament APIs", style="dim")
                        )
                elif kind == "text" and block["text"].strip():
                    texts.append(block["text"].strip())
        proc.wait()
        status.stop()

    # The last text block is the answer; earlier ones were interim notes.
    if texts:
        console.print()
        console.print(Markdown(texts[-1]))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
