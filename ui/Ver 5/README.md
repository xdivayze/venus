# Venus Map — Message Format Specification

## Architecture

```
Robots  →  MQTT Broker  →  main.py (WebSocket bridge)  →  front.html (canvas map)
```

## MQTT Broker

| Property | Value |
|----------|-------|
| Host | `mqtt.ics.ele.tue.nl` |
| Topic pattern | `/pynqbridge/{robot_id}/{event}` |
| Robot IDs | `58`, `26` |

---

## Supported Message Formats

There are two ways to publish messages — both are supported simultaneously.

### Format A — Via `/send` topic (new)

Publish a single message to `/pynqbridge/{robot_id}/send` with the event name as a prefix followed by the JSON payload. The backend parses the prefix and routes it to the correct event internally.

```
"event: {\"key\": value, ...}"
```

### Format B — Direct to event topic (legacy)

Publish directly to the specific event topic with a plain JSON payload.

```
topic:   /pynqbridge/{robot_id}/{event}
payload: {"key": value, ...}
```

---

## Events & Payloads

### `positions`
Robot position and heading.
```json
{"x": 5, "y": 3, "heading": 90.0}
```
| Field | Type | Description |
|-------|------|-------------|
| `x`, `y` | int | Grid cell (1 cell = 5 cm) |
| `heading` | float | Degrees |

### `sample`
Detected rock sample.
```json
{"x": 4, "y": 3, "color": "red", "size": "large", "temp": 462.0}
```
| Field | Type | Description |
|-------|------|-------------|
| `x`, `y` | int | Grid cell |
| `color` | string | e.g. `red`, `blue` |
| `size` | string | `large` or `small` |
| `temp` | float | Surface temperature in °C |

### `cliff`
Detected cliff edge (black tape).
```json
{"x": 6, "y": 5, "side": "top"}
```
| Field | Type | Description |
|-------|------|-------------|
| `x`, `y` | int | Grid cell |
| `side` | string | `top`, `bottom`, `left`, or `right` |

### `hill`
Detected hill obstacle.
```json
{"x": 3, "y": 7}
```
| Field | Type | Description |
|-------|------|-------------|
| `x`, `y` | int | Grid cell |

---

## Testing with mosquitto_pub

Replace `-t /pynqbridge/26/send` with `-t /pynqbridge/58/send` and update credentials for robot 58.

### Format 1 - all events via `/send`

```
"sample: {\"x\": 4, \"y\": 3, \"color\": \"red\", \"size\": \"large\", \"temp\": 462.0}"

"positions: {\"x\": 5, \"y\": 3, \"heading\": 90.0}"

"hill: {\"x\": 3, \"y\": 7}"

"cliff: {\"x\": 6, \"y\": 5, \"side\": \"top\"}"

"sample: {\"x\": 7, \"y\": 5, \"color\": \"blue\", \"size\": \"small\", \"temp\": 210.0}"
```

### Format 2 - Direct topics (legacy)

```
/pynqbridge/26/sample: "{\"x\": 4, \"y\": 3, \"color\": \"red\", \"size\": \"large\", \"temp\": 462.0}"

/pynqbridge/26/positions: "{\"x\": 5, \"y\": 3, \"heading\": 90.0}"

/pynqbridge/26/hill: "{\"x\": 3, \"y\": 7}"

/pynqbridge/26/cliff: "{\"x\": 6, \"y\": 5, \"side\": \"top\"}"
```

---
