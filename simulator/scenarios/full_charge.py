"""Full charge scenario: complete EV charging session lifecycle."""

from __future__ import annotations

import asyncio
import random

from simulator.client import ChargerClient
from simulator.config import Config
from simulator.ocpp.enums import ChargePointStatus, StopReason
from simulator.ocpp.messages import (
    boot_notification,
    meter_values,
    start_transaction,
    status_notification,
    stop_transaction,
)

# Simulated charger specs
_CHARGE_RATE_W = 7_200.0   # 7.2 kW (single-phase 32 A)
_POWER_NOISE_W = 200.0     # ± variation in power readings


async def run(client: ChargerClient, config: Config) -> None:
    """Simulate a complete charging session.

    Steps
    -----
    1. BootNotification    — register charger.
    2. StatusNotification  — Available (connector ready).
    3. StatusNotification  — Preparing (user taps RFID).
    4. StartTransaction    — begin charging session.
    5. StatusNotification  — Charging.
    6. MeterValues loop    — periodic energy/power readings.
    7. StatusNotification  — Finishing.
    8. StopTransaction     — end session.
    9. StatusNotification  — Available (connector freed).
    """

    # ── 1. Boot ───────────────────────────────────────────────────────────────
    resp = await client.send_call(
        "BootNotification",
        boot_notification(
            vendor=config.charger_vendor,
            model=config.charger_model,
            serial=client.charger_id,
            firmware=config.firmware_version,
        ),
    )
    status = resp.get("status", "Rejected")
    client.logger.info(f"BootNotification → {status}")
    if status == "Rejected":
        client.logger.error("Server rejected boot — stopping scenario")
        return

    await asyncio.sleep(config.message_delay)

    # ── 2. Available ──────────────────────────────────────────────────────────
    await client.send_call(
        "StatusNotification",
        status_notification(status=ChargePointStatus.AVAILABLE, connector_id=1),
    )
    client.logger.info("Connector → Available")

    # Simulate a driver arriving (random real-world delay)
    await asyncio.sleep(config.message_delay + random.uniform(0.2, 1.0))

    # ── 3. Preparing (RFID tap) ───────────────────────────────────────────────
    await client.send_call(
        "StatusNotification",
        status_notification(status=ChargePointStatus.PREPARING, connector_id=1),
    )
    client.logger.info("Connector → Preparing  (RFID tapped)")

    await asyncio.sleep(config.message_delay)

    # ── 4. StartTransaction ───────────────────────────────────────────────────
    resp = await client.send_call(
        "StartTransaction",
        start_transaction(
            connector_id=1,
            id_tag=config.id_tag,
            meter_start=0,
        ),
    )
    transaction_id: int = resp.get("transactionId", 1)
    auth_status: str = resp.get("idTagInfo", {}).get("status", "Invalid")
    client.logger.info(
        f"StartTransaction → txId={transaction_id}, auth={auth_status}"
    )

    if auth_status not in ("Accepted", "ConcurrentTx"):
        client.logger.error(
            f"Transaction rejected: auth={auth_status} — aborting session"
        )
        await client.send_call(
            "StatusNotification",
            status_notification(status=ChargePointStatus.AVAILABLE, connector_id=1),
        )
        return

    # ── 5. Charging ───────────────────────────────────────────────────────────
    await client.send_call(
        "StatusNotification",
        status_notification(status=ChargePointStatus.CHARGING, connector_id=1),
    )
    client.logger.info("Connector → Charging")

    # ── 6. MeterValues loop ───────────────────────────────────────────────────
    energy_wh = 0
    for sample_no in range(1, config.meter_samples + 1):
        await asyncio.sleep(config.meter_interval)

        # Accumulate energy for this interval
        actual_power_w = _CHARGE_RATE_W + random.uniform(-_POWER_NOISE_W, _POWER_NOISE_W)
        energy_wh += int(actual_power_w * config.meter_interval / 3600)

        await client.send_call(
            "MeterValues",
            meter_values(
                energy_wh=energy_wh,
                transaction_id=transaction_id,
                connector_id=1,
                power_w=actual_power_w,
            ),
        )
        client.logger.info(
            f"MeterValues  [{sample_no}/{config.meter_samples}]"
            f"  energy={energy_wh} Wh  power={actual_power_w:.0f} W"
        )

    await asyncio.sleep(config.message_delay)

    # ── 7. Finishing ──────────────────────────────────────────────────────────
    await client.send_call(
        "StatusNotification",
        status_notification(status=ChargePointStatus.FINISHING, connector_id=1),
    )
    client.logger.info("Connector → Finishing")

    await asyncio.sleep(config.message_delay)

    # ── 8. StopTransaction ────────────────────────────────────────────────────
    await client.send_call(
        "StopTransaction",
        stop_transaction(
            transaction_id=transaction_id,
            meter_stop=energy_wh,
            id_tag=config.id_tag,
            reason=StopReason.LOCAL,
        ),
    )
    client.logger.info(
        f"StopTransaction → txId={transaction_id}, final energy={energy_wh} Wh"
    )

    await asyncio.sleep(config.message_delay)

    # ── 9. Available again ────────────────────────────────────────────────────
    await client.send_call(
        "StatusNotification",
        status_notification(status=ChargePointStatus.AVAILABLE, connector_id=1),
    )
    client.logger.info("Connector → Available  (session complete ✓)")
