"""OCPP 1.6 message payload builders.

Each function returns a plain dict that can be directly serialised into the
payload element of an OCPP Call frame:  [2, uniqueId, Action, <payload>]

Builders only include fields that are non-None / non-empty so the resulting
JSON stays minimal and strictly spec-compliant.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def _utcnow() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ── BootNotification ─────────────────────────────────────────────────────────

def boot_notification(
    vendor: str = "VoltWise",
    model: str = "Simulator-1",
    serial: str = "",
    firmware: str = "1.0.0-sim",
) -> dict:
    """Build a BootNotification request payload."""
    payload: dict = {
        "chargePointVendor": vendor,
        "chargePointModel": model,
    }
    if serial:
        payload["chargePointSerialNumber"] = serial
    if firmware:
        payload["firmwareVersion"] = firmware
    return payload


# ── Heartbeat ────────────────────────────────────────────────────────────────

def heartbeat() -> dict:
    """Build a Heartbeat request payload (empty by spec)."""
    return {}


# ── StatusNotification ───────────────────────────────────────────────────────

def status_notification(
    status: str,
    connector_id: int = 1,
    error_code: str = "NoError",
    timestamp: Optional[str] = None,
) -> dict:
    """Build a StatusNotification request payload."""
    return {
        "connectorId": connector_id,
        "errorCode": error_code,
        "status": status,
        "timestamp": timestamp or _utcnow(),
    }


# ── StartTransaction ─────────────────────────────────────────────────────────

def start_transaction(
    connector_id: int,
    id_tag: str,
    meter_start: int = 0,
    timestamp: Optional[str] = None,
) -> dict:
    """Build a StartTransaction request payload."""
    return {
        "connectorId": connector_id,
        "idTag": id_tag,
        "meterStart": meter_start,
        "timestamp": timestamp or _utcnow(),
    }


# ── StopTransaction ──────────────────────────────────────────────────────────

def stop_transaction(
    transaction_id: int,
    meter_stop: int,
    id_tag: str = "",
    reason: str = "Local",
    timestamp: Optional[str] = None,
) -> dict:
    """Build a StopTransaction request payload."""
    payload: dict = {
        "transactionId": transaction_id,
        "meterStop": meter_stop,
        "timestamp": timestamp or _utcnow(),
        "reason": reason,
    }
    if id_tag:
        payload["idTag"] = id_tag
    return payload


# ── MeterValues ──────────────────────────────────────────────────────────────

def meter_values(
    energy_wh: int,
    *,
    transaction_id: Optional[int] = None,
    connector_id: int = 1,
    power_w: Optional[float] = None,
    context: str = "Sample.Periodic",
    timestamp: Optional[str] = None,
) -> dict:
    """Build a MeterValues request payload.

    Always includes Energy.Active.Import.Register (Wh).
    Optionally includes Power.Active.Import (W) when *power_w* is provided.
    """
    sampled_values: list[dict] = [
        {
            "value": str(energy_wh),
            "measurand": "Energy.Active.Import.Register",
            "unit": "Wh",
            "context": context,
        }
    ]
    if power_w is not None:
        sampled_values.append(
            {
                "value": str(round(power_w, 2)),
                "measurand": "Power.Active.Import",
                "unit": "W",
                "context": context,
            }
        )

    payload: dict = {
        "connectorId": connector_id,
        "meterValue": [
            {
                "timestamp": timestamp or _utcnow(),
                "sampledValue": sampled_values,
            }
        ],
    }
    if transaction_id is not None:
        payload["transactionId"] = transaction_id
    return payload
