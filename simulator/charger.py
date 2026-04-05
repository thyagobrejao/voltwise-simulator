"""Simulated charger — orchestrates a single charger's lifecycle."""

from __future__ import annotations

import asyncio
import random

from simulator.client import ChargerClient, OCPPError
from simulator.config import Config
from simulator.scenarios import get as get_scenario
from simulator.utils.logger import SimulatorLogger


class Charger:
    """Represents one simulated EV charger.

    Creates a :class:`~simulator.client.ChargerClient` pointed at
    ``{config.url}/{charger_id}`` and runs the configured scenario once
    the connection is established.

    The *index* parameter is used to stagger connection start times by
    ``index × config.connect_delay`` seconds, avoiding a thundering-herd
    effect when many chargers start simultaneously.
    """

    def __init__(self, charger_id: str, config: Config, index: int = 0) -> None:
        self.charger_id = charger_id
        self.config = config
        self.index = index

        self._logger = SimulatorLogger(charger_id)
        url = f"{config.url.rstrip('/')}/{charger_id}"
        self._client = ChargerClient(charger_id, url, config, self._logger)

    async def run(self) -> None:
        """Connect and execute the scenario, handling all expected exceptions."""
        # Stagger start times: charger N waits N × connect_delay seconds,
        # plus a small random jitter to spread load.
        stagger = self.index * self.config.connect_delay + random.uniform(0.0, 0.3)
        if stagger > 0:
            await asyncio.sleep(stagger)

        scenario = get_scenario(self.config.scenario)

        try:
            async with self._client:
                await scenario(self._client, self.config)
        except asyncio.CancelledError:
            self._logger.info("Simulation cancelled — shutting down")
            raise
        except OCPPError as exc:
            self._logger.error(f"OCPP error: {exc}")
        except ConnectionError as exc:
            self._logger.error(f"Connection error: {exc}")
        except TimeoutError as exc:
            self._logger.error(f"Timeout: {exc}")
        except Exception as exc:  # noqa: BLE001
            self._logger.error(f"Unexpected error: {type(exc).__name__}: {exc}")
