"""Simulator runtime configuration."""

from dataclasses import dataclass, field


@dataclass
class Config:
    """All runtime parameters for the simulator.

    Every value has a sensible default so callers only need to override
    what they care about.  The CLI populates this from command-line flags.
    """

    # ── Connection ──────────────────────────────────────────────────────────
    url: str = "ws://localhost:8080/ocpp"
    """Base WebSocket URL.  Each charger appends /{charger_id} automatically."""

    api_key: str = "internal-dev-key"
    """Shared secret for HTTP Basic Auth on the WebSocket upgrade."""

    retry_attempts: int = 3
    """How many times to retry a failed connection before giving up."""

    retry_delay: float = 2.0
    """Initial backoff delay in seconds (doubles on each retry, capped at 30 s)."""

    connect_delay: float = 0.5
    """Seconds to stagger charger start times (index × connect_delay)."""

    # ── Simulation ───────────────────────────────────────────────────────────
    count: int = 1
    """Number of concurrent chargers."""

    scenario: str = "basic"
    """Scenario to run: 'basic' or 'full_charge'."""

    message_delay: float = 1.0
    """Pause between successive OCPP messages within a scenario (seconds)."""

    charger_prefix: str = "SIM"
    """Prefix for generated charger IDs (e.g. 'SIM' → SIM-001, SIM-002 …)."""

    # ── Meter values (full_charge scenario) ──────────────────────────────────
    meter_interval: float = 5.0
    """Seconds between MeterValues samples during a charging session."""

    meter_samples: int = 5
    """Total number of MeterValues samples to send per session."""

    # ── Charger identity ─────────────────────────────────────────────────────
    charger_vendor: str = "VoltWise"
    charger_model: str = "Simulator-1"
    firmware_version: str = "1.0.0-sim"
    id_tag: str = "VOLTWISE-TAG-001"
    """RFID tag used for StartTransaction / StopTransaction."""
