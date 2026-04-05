"""Structured logger for the VoltWise simulator using Rich."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from rich.console import Console
from rich.text import Text

# Single shared console so concurrent chargers don't interleave lines.
_console = Console(highlight=False)


class SimulatorLogger:
    """Per-charger structured logger backed by Rich.

    All output lines share a common format::

        HH:MM:SS.mmm  [CHARGER-ID]  <message>

    Arrow conventions:
      → (green)  outgoing OCPP Call
      ← (blue)   incoming OCPP CallResult / CallError
      ℹ (yellow) informational event
      ✗ (red)    error
    """

    def __init__(self, charger_id: str) -> None:
        self.charger_id = charger_id

    # ── Public helpers ────────────────────────────────────────────────────────

    def outgoing(self, action: str, payload: dict) -> None:
        """Log an outgoing OCPP Call."""
        self._print(
            f"[bold green]→ {action}[/bold green]  "
            f"[dim]{_compact(payload)}[/dim]"
        )

    def incoming(self, action: str, payload: dict) -> None:
        """Log an incoming OCPP CallResult."""
        self._print(
            f"[bold blue]← {action}[/bold blue]  "
            f"[dim]{_compact(payload)}[/dim]"
        )

    def info(self, message: str) -> None:
        """Log an informational event."""
        self._print(f"[yellow]{message}[/yellow]")

    def error(self, message: str) -> None:
        """Log an error."""
        self._print(f"[bold red]✗ {message}[/bold red]")

    def connected(self, url: str) -> None:
        """Log a successful WebSocket connection."""
        self._print(f"[bold green]✓ Connected →[/bold green] [dim]{url}[/dim]")

    def disconnected(self) -> None:
        """Log a WebSocket disconnection."""
        self._print("[dim]Disconnected[/dim]")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _print(self, message: str) -> None:
        ts = _timestamp()
        _console.print(
            f"[dim]{ts}[/dim]  [cyan]\\[{self.charger_id}][/cyan]  {message}"
        )


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]


def _compact(payload: dict) -> str:
    """Serialise payload as compact JSON, truncated for readability."""
    text = json.dumps(payload, separators=(",", ":"))
    if len(text) > 120:
        return text[:117] + "…"
    return text
