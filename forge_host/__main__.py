"""CLI entry point for the Forge host.

Usage:
    forge --list
    forge run --seed 42 --party-size 4
    forge plugin new my_generator
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from forge_config.loader import load_config
from forge_host.bootstrap import bootstrap_host
from forge_plugins.registry import PluginRegistry

app = typer.Typer(add_completion=False, help="AI D&D campaign forge.")
console = Console()


@app.command("list")
def list_plugins(
    plugin_dir: Path = typer.Option(Path("forge_plugins/community"), "--plugin-dir"),
) -> None:
    """List every plugin the registry can see."""
    registry = PluginRegistry(plugin_dir)
    registry.discover()
    for meta in registry.describe():
        console.print(f"[bold]{meta.id}[/bold]  v{meta.version}  {meta.summary}")


@app.command("run")
def run(
    seed: int = typer.Option(6767, "--seed"),
    party_size: int = typer.Option(4, "--party-size"),
    plugin_dir: Path = typer.Option(Path("forge_plugins/community"), "--plugin-dir"),
) -> None:
    """Forge a campaign and print the session summary."""
    config = load_config()
    host = bootstrap_host(config, plugin_dir)
    session = asyncio.run(host.forge_campaign(seed=seed, party_size=party_size))
    console.print(f"[green]campaign forged:[/green] {session.campaign_id} ({len(session.scenes)} scenes)")


@app.command("plugin")
def plugin_cmd(action: str = typer.Argument(..., help="new|validate")) -> None:
    """Scaffold or validate a plugin."""
    console.print(f"[yellow]plugin {action}: not wired in this build[/yellow]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()