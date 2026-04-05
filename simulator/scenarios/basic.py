"""Basic scenario: BootNotification followed by periodic Heartbeats."""

from __future__ import annotations

import asyncio

from simulator.client import ChargerClient
from simulator.config import Config
from simulator.ocpp.messages import boot_notification, heartbeat


async def run(client: ChargerClient, config: Config) -> None:
    """Connect, register, then send three Heartbeats.

    Steps
    -----
    1. BootNotification  — register the charger with the server.
    2. Heartbeat × 3     — demonstrate the charger is alive.
    """
    # 1. BootNotification
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
    heartbeat_interval = resp.get("interval", 300)
    client.logger.info(
        f"BootNotification → status={status}, server heartbeat interval={heartbeat_interval}s"
    )

    if status == "Rejected":
        client.logger.error("Server rejected boot — stopping scenario")
        return

    # 2. Heartbeats
    for i in range(1, 4):
        await asyncio.sleep(config.message_delay)
        resp = await client.send_call("Heartbeat", heartbeat())
        server_time = resp.get("currentTime", "N/A")
        client.logger.info(f"Heartbeat #{i} → server time: {server_time}")

    client.logger.info("Basic scenario complete")
