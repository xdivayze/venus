# Venus

Software for the **Venus** rover challenge: an autonomous robot that drives across
a Mars/Venus-style arena, follows tape edges, discovers rock samples, cliffs and
hills, and streams what it finds to a live web map.

The system is split into four cooperating parts:

```
┌─────────────┐   TCP :8080    ┌──────────────┐    MQTT     ┌──────────────────┐   WebSocket   ┌────────────┐
│  algorithm/ │ ◄────────────► │    final/    │ ──────────► │   ui/main.py     │ ────────────► │ ui/Front   │
│  (planner,  │   commands /   │  (firmware   │  broker     │ (MQTT→WS bridge) │   live map    │ .html      │
│   Python)   │   sensor data  │   on robot)  │             │                  │               │ (browser)  │
└─────────────┘                └──────────────┘             └──────────────────┘               └────────────┘
```

The robot runs the C **firmware** (`final/`) and connects back as a TCP client to
the Python **algorithm** (`algorithm/`), which makes all the decisions and sends
motion/sensor commands over the socket. Discoveries are published over MQTT and
rendered live in the browser by the **UI** (`ui/`). Design documents, test code
and datasheets live in `appendices/`.

---

## Repository layout

| Directory | What it is |
|-----------|------------|
| [`algorithm/`](#algorithm--planning--simulation-python) | The decision-making code (Python): the live planner, the robot abstraction, and offline map/stability testing tools. |
| [`final/`](#final--robot-firmware-c) | The robot's onboard firmware (C, runs on the PYNQ board): motors, sensors, and the TCP/MQTT link. |
| [`ui/`](#ui--live-map-mqtt--websocket) | The live map: an MQTT→WebSocket bridge plus a browser canvas that draws the arena in real time. |
| `appendices/` | Supporting material: design docs (V-model, Gantt), simulation prototypes, per-module test programs, sensor circuits and datasheets. |

> Other top-level folders (`communication/`, `sensors/`, `testing_scripts/`,
> `venus_challenge/`) hold earlier prototypes and scratch work that fed into the
> four components above.

---

## algorithm/ — planning & simulation (Python)

Located in `algorithm/src-design/`. This is where the robot's behaviour is
defined. The same algorithm runs against either the real robot or a software
simulation, because both expose the same interface.

| File | Role |
|------|------|
| `main.py` | **The actual algorithm.** Drives the physical robot: opens a TCP server on `127.0.0.1:8080`, waits for the firmware to connect, then runs the edge-following / sweep logic command-by-command and writes out the discovered map (`sweep_map.txt`) and a report (`sweep_report.txt`). |
| `robot.py` | **The robot abstraction.** Defines two interchangeable classes: `Robot`, a pure-Python simulation that models wheel slip and gyro drift, and `RobotPhy`, which talks to the real firmware over the socket. `RobotPhy` is the socket-communication layer to the C code — `step`/`turn`/`sendDataMQTT`/sensor reads are encoded as small text commands (see the protocol below) and sent to `final/main.c`. |
| `fake_till_you_make.py` | **Map & stability testing tool.** Loads a photo/scan of an arena, lets you click waypoints (and tag objects) on the detected edges, calibrates pixels→cm from a reference measurement, and turns the path into a list of rotate/step instructions. Use it to test maps and check the robot's stability/repeatability on a known route before running the real algorithm. |
| `instruction_runner.py` | Replays a saved instruction list (`operation:payload:send_payload` lines) against the real robot via `RobotPhy`, e.g. a path produced by `fake_till_you_make.py`. |

The `Robot`/`RobotPhy` split means you can develop and debug the algorithm
entirely in simulation (no hardware), then point it at the real robot by swapping
the class — see the commented block at the bottom of `main.py`.

### Setup & running

```bash
cd algorithm
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Run against the **real robot** (start this first; it waits for the robot to
connect, then power on the firmware which dials back in):

```bash
cd src-design
python main.py
```

Plan/test a route from an arena image with the **testing tool**:

```bash
cd src-design
python fake_till_you_make.py <image_path> <output_path> <initial_heading_deg>
# left/middle click: add waypoints (middle click prompts for an object name)
# right click x2:     mark a reference segment, then enter its real length for px→cm scaling
```

Tests live in `algorithm/tests/`.

---

## final/ — robot firmware (C)

The **firmware** that runs on the robot (PYNQ / `libpynq`). It is the TCP
*client*: on start-up it connects to the algorithm at `127.0.0.1:8080`, then sits
in a command loop reading instructions, driving the stepper motors, reading the
sensors, and forwarding discoveries to MQTT.

| File | Role |
|------|------|
| `main.c` | Entry point: initialises the board and stepper motors, connects the socket, and dispatches incoming commands. |
| `move_utils.{c,h}` | Motion primitives — `step()`, `rotate_angle()`, circle driving — with the wheel/axis geometry constants. |
| `sensors.{c,h}` | Sensor drivers: time-of-flight distance (VL53L0X), colour sensor (TCS3200), IR edge sensors (CNY70), and thermistor temperature (with the Beta-equation conversion). |
| `communication.{c,h}` | Message loop and a small command-registry (`register_new_command`, `send_msg`, `read_msg`) for the socket link. |
| `main.c.old` | Previous iteration, kept for reference. |

### Building

Build against `libpynq` on the target board (the included `main` is a compiled
binary). Roughly:

```bash
cd final
gcc main.c move_utils.c sensors.c communication.c -o main -lpynq -lm
```

(Adjust include/lib paths to your `libpynq` install.)

### Wire protocol (algorithm ↔ firmware)

The Python `RobotPhy` sends short `code[:arg]` strings; the firmware ACKs by
echoing the code. Commands:

| Code | Direction | Meaning |
|------|-----------|---------|
| `100:<steps>` | → robot | Drive forward `steps`; ACK `100` |
| `101:<radians>` | → robot | Turn by angle (+ = CCW); ACK `101` |
| `102:<payload>` | → robot | Forward `payload` to MQTT; ACK `102` |
| `200` | → robot | Read ToF distance (mm) |
| `201` | → robot | Read front colour |
| `202` / `203` | → robot | Read front / right IR value |
| `999` | → robot | Leave the command loop and stop motors |

---

## ui/ — live map (MQTT → WebSocket)

The operator-facing live map. Robots publish discoveries to the TU/e MQTT broker;
`ui/main.py` subscribes, normalises the messages, and rebroadcasts them over a
WebSocket; `ui/Front.html` draws the arena grid, robot positions, samples,
cliffs and hills in the browser as they arrive.

```bash
cd ui
pip install websockets paho-mqtt
python main.py          # starts the MQTT subscriber + WebSocket server
# then open Front.html in a browser
```

The full message-format specification (broker host, topics, event payloads, and
`mosquitto_pub` testing examples) is documented in **[`ui/README.md`](ui/README.md)**.

---

## appendices/

Reference material and intermediate work supporting the final system:

- `V-model.png`, `Gantt Chart Venus plan.png` — project design & planning docs.
- `Algorithm/` — the earlier simulation prototype and its results.
- `Communication/` — MQTT publisher/listener scripts and the communication architecture diagram (see `appendices/Communication/README.md`).
- `Sensors/` — per-sensor test programs, circuit diagrams, and component datasheets (thermistor, CNY70, TCS3200, VL53L0X).
- `Integration/` — multi-module integration test programs.
- `UI/` — UI prototype and sample mapping screenshots.
