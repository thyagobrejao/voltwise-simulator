# VoltWise Simulator

A CLI-based OCPP 1.6 charge point simulator built to test and develop EV charging platforms like VoltWise.

---

## Overview

VoltWise Simulator emulates real EV chargers (Charge Points) communicating with an OCPP server over WebSocket.

It allows developers to:

* simulate real charging sessions
* test OCPP servers
* debug message flows
* run multiple chargers concurrently

---

## Features

* OCPP 1.6 JSON support over WebSocket (`ocpp1.6` subprotocol)
* Multiple concurrent chargers via asyncio tasks
* Staggered connection start to avoid thundering-herd
* Automatic retry with exponential back-off
* Graceful shutdown on SIGINT / SIGTERM
* Rich structured logging per charger
* Extensible scenario system

---

## Supported OCPP Actions

| Action | Direction |
|---|---|
| BootNotification | Charger to Server |
| Heartbeat | Charger to Server |
| StatusNotification | Charger to Server |
| StartTransaction | Charger to Server |
| MeterValues | Charger to Server |
| StopTransaction | Charger to Server |

---

## Scenarios

### `basic`

Minimal connection flow: register the charger and send periodic heartbeats.

1. BootNotification
2. Heartbeat x3

### `full_charge`

Complete end-to-end charging session lifecycle:

1. BootNotification
2. StatusNotification -- Available
3. StatusNotification -- Preparing (simulated RFID tap)
4. StartTransaction
5. StatusNotification -- Charging
6. MeterValues loop (configurable samples & interval)
7. StatusNotification -- Finishing
8. StopTransaction
9. StatusNotification -- Available

---

## Project Structure

```
voltwise-simulator/
  simulator/
    __init__.py
    config.py           # Runtime configuration dataclass
    client.py           # ChargerClient -- WebSocket + OCPP framing
    charger.py          # Charger -- orchestrates one simulated charger
    cli.py              # Typer CLI application
    ocpp/
      enums.py          # OCPP 1.6 enumerations
      messages.py       # Message payload builders
    scenarios/
      __init__.py       # Scenario registry
      basic.py          # Basic scenario
      full_charge.py    # Full charging session scenario
    utils/
      logger.py         # Rich-based structured logger
  main.py               # Script entry point
  pyproject.toml
```

---

## Installation

```bash
cd voltwise-simulator
pip install -e .
```

Requires Python 3.11+.

---

## Usage

### Show help

```bash
voltwise-simulator --help
voltwise-simulator list-scenarios
```

### Single charger -- basic scenario

```bash
voltwise-simulator run
```

### Custom server URL

```bash
voltwise-simulator run --url ws://localhost:8080/ocpp
```

### Full charge scenario

```bash
voltwise-simulator run --scenario full_charge
```

### Multiple concurrent chargers

```bash
voltwise-simulator run --count 5
```

### Combined example

```bash
voltwise-simulator run \
  --url ws://localhost:8080/ocpp \
  --count 10 \
  --scenario full_charge \
  --delay 0.5 \
  --prefix EV \
  --meter-samples 8 \
  --meter-interval 3.0 \
  --connect-delay 0.2
```

### All options

| Flag | Default | Description |
|---|---|---|
| `--url` | `ws://localhost:8080/ocpp` | Base WebSocket URL |
| `--count` | `1` | Concurrent chargers |
| `--scenario` | `basic` | Scenario to run |
| `--delay` | `1.0` | Seconds between messages |
| `--prefix` | `SIM` | Charger ID prefix |
| `--meter-samples` | `5` | MeterValues samples (full_charge) |
| `--meter-interval` | `5.0` | Seconds between meter samples |
| `--connect-delay` | `0.5` | Stagger between charger starts |
| `--retry-attempts` | `3` | Connection retry limit |

---

## How It Works

Each simulated charger:

1. Waits `index x connect-delay` seconds (stagger) before connecting.
2. Opens a WebSocket to `{url}/{charger-id}` with the `ocpp1.6` subprotocol.
3. Retries on connection failure (exponential back-off, up to `retry-attempts`).
4. Runs the selected scenario (a coroutine function that drives OCPP calls).
5. Disconnects cleanly when the scenario completes or on shutdown signal.

All chargers run as independent `asyncio.Task` instances inside a single event loop.

---

## Adding a Custom Scenario

1. Create `simulator/scenarios/my_scenario.py`:

```python
from simulator.client import ChargerClient
from simulator.config import Config

async def run(client: ChargerClient, config: Config) -> None:
    await client.send_call("BootNotification", {...})
    # custom flow
```

2. Register it in `simulator/scenarios/__init__.py`:

```python
from simulator.scenarios.my_scenario import run as _my_scenario
_REGISTRY["my_scenario"] = _my_scenario
```

3. Run it:

```bash
voltwise-simulator run --scenario my_scenario
```

---

## Integration

Designed to work with `voltwise-ocpp` (the VoltWise OCPP Central System):

```bash
# Terminal 1 -- start the OCPP server
cd voltwise-ocpp && go run ./cmd/voltwise-ocpp

# Terminal 2 -- start the simulator
voltwise-simulator run --scenario full_charge
```

Also compatible with any OCPP 1.6 JSON compliant backend.

---

## Tech Stack

* Python 3.11+
* asyncio
* websockets >= 12.0
* Typer >= 0.12
* Rich >= 13.0

---

## Use Cases

* local development without physical hardware
* backend integration testing
* load and stress testing
* QA and demo traffic generation
* debugging OCPP message flows

---

## Roadmap

* OCPP 2.0.1 support
* advanced fault simulation
* authentication support
* scenario customization via config file
* metrics and reporting

---

## Contributing

Contributions are welcome. Feel free to open an issue for bugs, missing features, or ideas.

---

## License

AGPL v3

---

## About VoltWise

VoltWise is an open-source platform aiming to simplify EV charging by unifying infrastructure, users, and services.
