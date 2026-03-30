# VoltWise Simulator 🔌⚡

A CLI-based OCPP 1.6 charge point simulator built to test and develop EV charging platforms like VoltWise.

Because not everyone has a real charger sitting at home (I definitely don’t 😅).

---

## 💡 Overview

VoltWise Simulator emulates real EV chargers (Charge Points) communicating with an OCPP server over WebSocket.

It allows developers to:

* simulate real charging sessions
* test OCPP servers
* debug message flows
* run multiple chargers concurrently

---

## 🚀 Features

* OCPP 1.6 JSON support
* WebSocket client simulation
* Multiple concurrent chargers
* Predefined scenarios
* CLI interface
* Structured logging

---

## 🔌 Supported OCPP Actions

* BootNotification
* Heartbeat
* StatusNotification
* StartTransaction
* MeterValues
* StopTransaction

---

## 🧪 Scenarios

### basic

Minimal connection flow:

* connect
* BootNotification
* Heartbeat

---

### full_charge

Simulates a real charging session:

1. BootNotification
2. StatusNotification (Available)
3. StartTransaction
4. MeterValues loop
5. StopTransaction

---

## ⚙️ Installation

```bash
git clone https://github.com/YOUR_USERNAME/voltwise-simulator.git
cd voltwise-simulator
pip install -e .
```

---

## ▶️ Usage

### Run a single charger

```bash
voltwise-simulator run --url ws://localhost:8080/ocpp/charger-1
```

---

### Run multiple chargers

```bash
voltwise-simulator run --count 5
```

---

### Select scenario

```bash
voltwise-simulator run --scenario full_charge
```

---

## 🧠 How It Works

Each simulated charger:

* opens a WebSocket connection
* sends OCPP messages
* receives responses from the server
* follows a defined scenario

All chargers run concurrently using asyncio.

---

## 🔗 Integration

This simulator is designed to work with:

* VoltWise OCPP server
* Any OCPP 1.6 compliant backend

---

## 🛠️ Tech Stack

* Python 3.11+
* asyncio
* websockets
* typer
* rich

---

## 🎯 Use Cases

* local development
* backend testing
* load simulation
* debugging OCPP flows

---

## 🚧 Roadmap

* OCPP 2.0.1 support
* advanced fault simulation
* authentication support
* scenario customization via config
* metrics & reporting

---

## 🤝 Contributing

Contributions are welcome.

If you find bugs, missing features, or have ideas, feel free to open an issue.

---

## 📄 License

AGPL v3

---

## ⚡ About VoltWise

VoltWise is an open-source platform aiming to simplify EV charging by unifying infrastructure, users, and services.

---

If you're building EV infrastructure and you're tired of downloading 10 different apps just to charge your car...

you're not alone 😄
