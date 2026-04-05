"""OCPP 1.6 WebSocket client for a single simulated charger.

ChargerClient manages:
  - WebSocket lifecycle (connect, send, receive, disconnect)
  - OCPP frame encoding / decoding
  - Pending-request tracking by UniqueId
  - Retry logic with exponential back-off
  - Graceful shutdown

Wire format (OCPP 1.6J):
  Call       [2, uniqueId, action, payload]
  CallResult [3, uniqueId, payload]
  CallError  [4, uniqueId, errorCode, description, details]
"""

from __future__ import annotations

import asyncio
import base64
import json
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from simulator.config import Config
from simulator.utils.logger import SimulatorLogger

# OCPP message type identifiers
_CALL = 2
_CALL_RESULT = 3
_CALL_ERROR = 4


class OCPPError(Exception):
    """Raised when the server returns a CallError frame."""

    def __init__(self, error_code: str, description: str = "") -> None:
        self.error_code = error_code
        self.description = description
        super().__init__(f"{error_code}: {description}" if description else error_code)


class ChargerClient:
    """Async OCPP 1.6 WebSocket client for one simulated charger.

    Typical usage::

        async with ChargerClient(charger_id, url, config, logger) as client:
            await client.send_call("BootNotification", {...})

    Or manually::

        client = ChargerClient(...)
        await client.connect()
        result = await client.send_call("Heartbeat", {})
        await client.disconnect()
    """

    def __init__(
        self,
        charger_id: str,
        url: str,
        config: Config,
        logger: SimulatorLogger,
    ) -> None:
        self.charger_id = charger_id
        self.url = url
        self.config = config
        self.logger = logger

        self._ws: Optional[ClientConnection] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._pending: dict[str, asyncio.Future] = {}
        self._connected: bool = False

    # ── Auth helpers ──────────────────────────────────────────────────────

    def _auth_headers(self) -> dict[str, str]:
        """Build HTTP Basic Auth headers for the WebSocket upgrade."""
        credentials = base64.b64encode(
            f"{self.charger_id}:{self.config.api_key}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}

    # ── Connection lifecycle ──────────────────────────────────────────────────

    async def connect(self) -> None:
        """Open the WebSocket connection, retrying with exponential back-off."""
        delay = self.config.retry_delay

        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                self.logger.info(
                    f"Connecting (attempt {attempt}/{self.config.retry_attempts}) → {self.url}"
                )
                self._ws = await connect(
                    self.url,
                    subprotocols=["ocpp1.6"],
                    additional_headers=self._auth_headers(),
                    open_timeout=10,
                    ping_interval=30,
                    ping_timeout=10,
                )
                self._connected = True
                self._reader_task = asyncio.create_task(
                    self._reader_loop(), name=f"reader-{self.charger_id}"
                )
                self.logger.connected(self.url)
                return

            except OSError as exc:
                self.logger.error(f"Connection failed: {exc}")
                if attempt < self.config.retry_attempts:
                    self.logger.info(f"Retrying in {delay:.1f}s…")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 30.0)
                else:
                    raise ConnectionError(
                        f"Could not connect to {self.url} after "
                        f"{self.config.retry_attempts} attempts"
                    ) from exc

    async def disconnect(self) -> None:
        """Gracefully close the WebSocket connection."""
        self._connected = False

        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        # Resolve any still-pending requests with a connection error.
        for future in self._pending.values():
            if not future.done():
                future.set_exception(ConnectionError("Connection closed"))
        self._pending.clear()

        if self._ws:
            await self._ws.close()
            self._ws = None

        self.logger.disconnected()

    # ── Message sending ───────────────────────────────────────────────────────

    async def send_call(
        self, action: str, payload: dict, timeout: float = 30.0
    ) -> dict:
        """Send an OCPP Call and block until the matching CallResult arrives.

        Args:
            action:  OCPP action name (e.g. ``"BootNotification"``).
            payload: Dict to serialise as the message payload.
            timeout: Seconds to wait for a response before raising TimeoutError.

        Returns:
            The response payload dict from the CallResult.

        Raises:
            RuntimeError:   When called while not connected.
            OCPPError:      When the server responds with a CallError.
            TimeoutError:   When no response arrives within *timeout* seconds.
        """
        if not self._connected or self._ws is None:
            raise RuntimeError(f"[{self.charger_id}] Not connected")

        unique_id = uuid.uuid4().hex[:8].upper()
        frame = json.dumps([_CALL, unique_id, action, payload])

        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict] = loop.create_future()
        self._pending[unique_id] = future

        try:
            self.logger.outgoing(action, payload)
            await self._ws.send(frame)
            result = await asyncio.wait_for(asyncio.shield(future), timeout=timeout)
            self.logger.incoming(action, result)
            return result

        except asyncio.TimeoutError:
            self._pending.pop(unique_id, None)
            raise TimeoutError(f"No response for {action} within {timeout}s")

        except Exception:
            self._pending.pop(unique_id, None)
            raise

    # ── Async context manager ─────────────────────────────────────────────────

    async def __aenter__(self) -> "ChargerClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    # ── Internal reader loop ──────────────────────────────────────────────────

    async def _reader_loop(self) -> None:
        """Background task: read incoming frames and resolve pending futures."""
        try:
            async for raw in self._ws:  # type: ignore[union-attr]
                await self._dispatch(raw)
        except ConnectionClosed as exc:
            self.logger.error(f"Connection closed: {exc}")
            self._connected = False
            self._fail_pending(ConnectionError(f"Connection closed: {exc}"))
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self.logger.error(f"Reader error: {exc}")
            self._connected = False
            self._fail_pending(exc)

    async def _dispatch(self, raw: str | bytes) -> None:
        """Parse one incoming frame and route it to the right pending future."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self.logger.error(f"Malformed JSON frame: {exc}")
            return

        if not isinstance(data, list) or len(data) < 3:
            self.logger.error(f"Unexpected frame shape: {data!r}")
            return

        msg_type: int = data[0]
        unique_id: str = data[1]

        if msg_type == _CALL_RESULT:
            payload = data[2] if len(data) > 2 else {}
            self._resolve(unique_id, payload)

        elif msg_type == _CALL_ERROR:
            error_code = data[2] if len(data) > 2 else "UnknownError"
            description = data[3] if len(data) > 3 else ""
            self._reject(unique_id, OCPPError(error_code, description))

        elif msg_type == _CALL:
            # Server-initiated calls (e.g. RemoteStartTransaction).
            # The simulator does not implement server-side commands; just log.
            action = data[2] if len(data) > 2 else "Unknown"
            self.logger.info(f"Server-initiated call ignored: {action}")

        else:
            self.logger.error(f"Unknown message type {msg_type}")

    def _resolve(self, unique_id: str, payload: dict) -> None:
        future = self._pending.pop(unique_id, None)
        if future and not future.done():
            future.set_result(payload)

    def _reject(self, unique_id: str, exc: Exception) -> None:
        future = self._pending.pop(unique_id, None)
        if future and not future.done():
            future.set_exception(exc)

    def _fail_pending(self, exc: Exception) -> None:
        for future in self._pending.values():
            if not future.done():
                future.set_exception(exc)
        self._pending.clear()
