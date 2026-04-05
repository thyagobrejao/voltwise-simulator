"""CLI entry point for the VoltWise simulator.

Usage examples::

    # Single charger, basic scenario
    voltwise-simulator run

    # Point at a specific server
    voltwise-simulator run --url ws://localhost:8080/ocpp

    # Five concurrent chargers
    voltwise-simulator run --count 5

    # Full charging session scenario
    voltwise-simulator run --scenario full_charge

    # Combined
    voltwise-simulator run --url ws://staging.voltwise.io/ocpp --count 10 --scenario full_charge
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Load .env from the project root (if present) before Typer reads envvars.
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.is_file():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

from simulator.charger import Charger
from simulator.config import Config
from simulator.scenarios import available_scenarios

app = typer.Typer(
    name="voltwise-simulator",
    help="OCPP 1.6 Charge Point simulator for the VoltWise platform.",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


@app.command()
def run(
    url: str = typer.Option(
        "ws://localhost:8080/ocpp",
        "--url",
        help=(
            "Base WebSocket URL of the OCPP Central System.  "
            "Each charger appends its ID automatically: {url}/{charger-id}."
        ),
        show_default=True,
    ),
    count: int = typer.Option(
        1,
        "--count",
        min=1,
        max=500,
        help="Number of chargers to simulate concurrently.",
        show_default=True,
    ),
    scenario: str = typer.Option(
        "basic",
        "--scenario",
        help="Scenario to execute. Use 'list-scenarios' to see all options.",
        show_default=True,
    ),
    delay: float = typer.Option(
        1.0,
        "--delay",
        min=0.0,
        help="Pause between successive OCPP messages within a scenario (seconds).",
        show_default=True,
    ),
    prefix: str = typer.Option(
        "SIM",
        "--prefix",
        help="Charger ID prefix.  Results in SIM-001, SIM-002, … by default.",
        show_default=True,
    ),
    meter_samples: int = typer.Option(
        5,
        "--meter-samples",
        min=1,
        help="MeterValues samples per session (full_charge scenario only).",
        show_default=True,
    ),
    meter_interval: float = typer.Option(
        5.0,
        "--meter-interval",
        min=0.1,
        help="Seconds between MeterValues samples.",
        show_default=True,
    ),
    connect_delay: float = typer.Option(
        0.5,
        "--connect-delay",
        min=0.0,
        help=(
            "Stagger delay between charger start times "
            "(charger N waits N × connect-delay seconds)."
        ),
        show_default=True,
    ),
    retry_attempts: int = typer.Option(
        3,
        "--retry-attempts",
        min=1,
        help="Number of connection attempts before giving up.",
        show_default=True,
    ),
    api_key: str = typer.Option(
        "internal-dev-key",
        "--api-key",
        envvar="INTERNAL_API_KEY",
        help="Shared secret for OCPP server authentication (reads INTERNAL_API_KEY env var).",
        show_default=False,
    ),
) -> None:
    """Simulate one or more OCPP 1.6 chargers connecting to a Central System."""

    if scenario not in available_scenarios():
        console.print(
            f"[bold red]Unknown scenario '{scenario}'.[/bold red]\n"
            f"Available: {', '.join(available_scenarios())}"
        )
        raise typer.Exit(code=1)

    config = Config(
        url=url,
        api_key=api_key,
        count=count,
        scenario=scenario,
        message_delay=delay,
        charger_prefix=prefix,
        meter_samples=meter_samples,
        meter_interval=meter_interval,
        connect_delay=connect_delay,
        retry_attempts=retry_attempts,
    )

    _print_banner(config)

    try:
        asyncio.run(_run_simulation(config))
    except KeyboardInterrupt:
        pass  # Graceful shutdown message already printed inside the coroutine.


@app.command(name="list-scenarios")
def list_scenarios() -> None:
    """List all available simulation scenarios."""
    console.print("\n[bold]Available scenarios:[/bold]\n")
    descriptions = {
        "basic": "BootNotification + three Heartbeats",
        "full_charge": (
            "BootNotification → StatusNotification (Available/Preparing/Charging/Finishing) "
            "→ StartTransaction → MeterValues loop → StopTransaction"
        ),
    }
    for name in available_scenarios():
        desc = descriptions.get(name, "")
        console.print(f"  [cyan]{name:<16}[/cyan]  {desc}")
    console.print()


# ── Internal ─────────────────────────────────────────────────────────────────


async def _run_simulation(config: Config) -> None:
    """Spawn all charger tasks and coordinate graceful shutdown."""
    charger_ids = [f"{config.charger_prefix}-{i + 1:03d}" for i in range(config.count)]
    chargers = [Charger(cid, config, index=i) for i, cid in enumerate(charger_ids)]

    tasks: list[asyncio.Task] = [
        asyncio.create_task(c.run(), name=cid) for c, cid in zip(chargers, charger_ids)
    ]

    # Register OS signal handlers for graceful shutdown.
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _on_signal() -> None:
        console.print("\n[bold yellow]Shutdown signal received — stopping chargers…[/bold yellow]")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError, OSError):
            loop.add_signal_handler(sig, _on_signal)

    try:
        # Wait for all chargers to finish OR a shutdown signal.
        sentinel = asyncio.create_task(shutdown_event.wait(), name="shutdown-sentinel")
        done, _pending = await asyncio.wait(
            [sentinel, *tasks], return_when=asyncio.FIRST_COMPLETED
        )

        if sentinel in done:
            # Signal received — cancel charger tasks gracefully.
            for task in tasks:
                if not task.done():
                    task.cancel()

    finally:
        # Always wait for all tasks to finish (or be cancelled).
        await asyncio.gather(*tasks, return_exceptions=True)

        console.print("[bold green]Simulation finished.[/bold green]")


def _print_banner(config: Config) -> None:
    masked_key = config.api_key[:4] + "****" if len(config.api_key) > 4 else "****"
    body = Text.assemble(
        ("  Server      ", "dim"), (config.url + "\n", "green"),
        ("  API Key     ", "dim"), (masked_key + "\n", "green"),
        ("  Chargers    ", "dim"), (str(config.count) + "\n", "green"),
        ("  Scenario    ", "dim"), (config.scenario + "\n", "green"),
        ("  Msg delay   ", "dim"), (f"{config.message_delay}s\n", "green"),
        ("  Prefix      ", "dim"), (config.charger_prefix + "\n", "green"),
    )
    if config.scenario == "full_charge":
        body.append("  Meter       ", style="dim")
        body.append(
            f"{config.meter_samples} samples × {config.meter_interval}s\n",
            style="green",
        )

    console.print(
        Panel(body, title="[bold cyan]VoltWise Simulator[/bold cyan]", border_style="cyan")
    )
