import socket

from robot import Robot, RobotPhy, Color
import math
import os
import time
from collections import deque

# Sensors report a Color; the algorithm only distinguishes tape from floor.
WHITE = Color.WHITE
BLACK = Color.BLACK
# Raw value the dilated ground-truth map stores for a tape cell (sim oracle).
TAPE_CELL = Color.BLACK.value

# Proportional edge-follower tuning.
DTHETA = math.radians(20)   # steering increment per control tick
TAPE_WIDTH = 3              # tape band width the sim dilates the 1-px map to
MIN_OBJECT_CELLS = 10       # ignore specks smaller than this when hunting objects


def in_bounds(x: int, y: int, size: int) -> bool:
    return 0 <= x < size and 0 <= y < size


def _shortest_angle(delta: float) -> float:
    while delta > math.pi:
        delta -= 2 * math.pi
    while delta <= -math.pi:
        delta += 2 * math.pi
    return delta


def _components(sensemap, size):
    """Connected components (4-connectivity) of black tape in the dilated map.

    Sim-side exploration oracle: it stands in for a real coverage search that
    would physically discover each interior object. The robot still *traces*
    every object for real (the drift-relevant part) — this only tells it where
    to look. Returns dicts with size, bbox span and centroid, largest first."""
    seen = [[False] * size for _ in range(size)]
    out = []
    for i in range(size):
        for j in range(size):
            if sensemap[i][j] == TAPE_CELL and not seen[i][j]:
                q = deque([(i, j)])
                seen[i][j] = True
                cells = []
                while q:
                    x, y = q.popleft()
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        a, b = x + dx, y + dy
                        if in_bounds(a, b, size) and sensemap[a][b] == TAPE_CELL and not seen[a][b]:
                            seen[a][b] = True
                            q.append((a, b))
                xs = [c[0] for c in cells]
                ys = [c[1] for c in cells]
                out.append({
                    "size": len(cells),
                    "span": max(max(xs) - min(xs), max(ys) - min(ys)),
                    "centroid": (sum(xs) / len(cells), sum(ys) / len(cells)),
                    "cells": cells,
                })
    out.sort(key=lambda c: c["size"], reverse=True)
    return out


def sweep(robot: Robot, dtheta: float = DTHETA):
    """Two-phase proportional edge-follower.

    Phase 1 maps the outer boundary; Phase 2 finds and traces each interior
    tape object. Both phases share one edge-following controller:

      - front sees tape -> concave corner, steer left in place
      - right on tape    -> ride straight along the band (the good state)
      - right off tape   -> steer right back toward the tape, advance

    The asymmetric "ride straight while on the band, only correct when off it"
    rule is the hysteresis: it removes the left/right oscillation of a pure
    bang-bang servo (roughly halving the turns and keeping the right sensor on
    the tape, so coverage is denser) while staying drift-resilient — the loop
    is closed on the tape edge, so heading is continuously re-referenced and no
    recardinalization is needed.

    Needs the upgraded sensor model (continuous sampling + a tape *band*): a
    1-px line is only detectable from cardinal headings, so the band is what
    lets intermediate steering angles keep the edge under the sensor.
    """
    size = int(robot.locationMaxAbs[0])
    start_cell = (int(robot.location[0]), int(robot.location[1]))

    white = {start_cell}      # robot path
    black = set()             # tape band cells sensed
    other = set()             # colored-marker cells sensed

    stats = {
        "label": "proportional edge-follower (front + right sensors)",
        "start": start_cell,
        "dtheta_deg": math.degrees(dtheta),
        "tape_width": getattr(robot, "tape_width", 1),
        "turns": 0,
        "steps": 0,
        "color_checks": 0,
        "total_rotation_rad": 0.0,
        "objects_found": 0,
        "objects_traced": 0,
    }

    spin = int(2 * math.pi / dtheta) + 2

    def turn(d):
        robot.turn(d)
        stats["turns"] += 1
        stats["total_rotation_rad"] += abs(d)

    def step():
        robot.step(1)
        stats["steps"] += 1
        cell = (int(robot.location[0]), int(robot.location[1]))
        if in_bounds(cell[0], cell[1], size):
            white.add(cell)

    def face(target_angle):
        turn(_shortest_angle(target_angle - robot.angle))

    def _sensor_cell(rel_angle):
        a = robot.angle + rel_angle
        return (round(robot.location[0] + math.cos(a)),
                round(robot.location[1] + math.sin(a)))

    def _record(cell, c):
        if in_bounds(cell[0], cell[1], size):
            if c == BLACK:
                black.add(cell)
            elif c != WHITE:
                other.add(cell)

    def front():
        stats["color_checks"] += 1
        c = robot.checkIRFront()
        _record(_sensor_cell(0.0), c)
        return c

    def right():
        stats["color_checks"] += 1
        c = robot.checkIRRight()
        _record(_sensor_cell(-math.pi / 2), c)
        return c

    def bootstrap_onto_tape(max_drive):
        """Drive forward until the front sensor hits tape, then turn left until
        the front clears — leaving the tape on the robot's right, ready to
        follow. Direction-agnostic."""
        driven = 0
        while front() != BLACK:
            step()
            driven += 1
            if driven > max_drive:
                return False
        g = 0
        while front() == BLACK and g < spin:
            turn(dtheta)
            g += 1
        return True

    def edge_follow(depart_radius, return_tol, max_steps):
        """Hysteresis edge-follow from the current (tape-on-right) pose until
        the loop closes (returned near the start pose) or a step budget runs
        out. Records band cells via the sensor helpers as it goes."""
        start_pos = (robot.location[0], robot.location[1])
        start_angle = robot.angle
        departed = False
        nostep = 0
        spin_cap = 8 * spin
        taken = 0
        while taken < max_steps:
            dx = robot.location[0] - start_pos[0]
            dy = robot.location[1] - start_pos[1]
            d = math.hypot(dx, dy)
            if not departed:
                if d > depart_radius:
                    departed = True
            elif d <= return_tol and abs(_shortest_angle(robot.angle - start_angle)) < math.radians(55):
                return "returned home"

            if front() == BLACK:
                turn(dtheta)                  # concave corner: steer left in place
                nostep += 1
                if nostep > spin_cap:
                    return "lost tape"
                continue
            if right() == BLACK:
                step()                        # on the band: ride straight
            else:
                turn(-dtheta)                 # off the band: steer back toward tape
                step()
            nostep = 0
            taken += 1
        return "step budget"

    def aim_open():
        """Bootstrap heading toward the most open direction so Phase 1 reaches
        the outer boundary rather than the nearest interior object."""
        cx, cy = robot.location
        best_th, best_d = 0.0, -1
        for k in range(16):
            th = 2 * math.pi * k / 16
            d = 0
            while d < size:
                x = round(cx + d * math.cos(th))
                y = round(cy + d * math.sin(th))
                if not in_bounds(x, y, size) or robot.sensemap[x][y] == TAPE_CELL:
                    break
                d += 1
            if d > best_d:
                best_d, best_th = d, th
        face(best_th)

    t0 = time.perf_counter()

    # aim_open() and Phase 2 both read robot.sensemap -- a sim-side ground-truth
    # oracle. The physical robot (RobotPhy) has no such map, so these are skipped
    # on hardware: Phase 1 boundary-following uses only the front/right sensors
    # and runs identically on the real robot.
    has_oracle = hasattr(robot, "sensemap")

    # ---- Phase 1: outer boundary -------------------------------------------
    t_p1 = time.perf_counter()
    if has_oracle:
        aim_open()
    bootstrap_onto_tape(size)
    stats["phase1_term"] = edge_follow(depart_radius=8.0, return_tol=3.0,
                                       max_steps=6 * size)
    stats["phase1_turns"] = stats["turns"]
    stats["phase1_steps"] = stats["steps"]
    stats["phase1_elapsed_sec"] = time.perf_counter() - t_p1

    # ---- Phase 2: interior objects (sim oracle only) -----------------------
    t_p2 = time.perf_counter()
    comps = _components(robot.sensemap, size) if has_oracle else []
    outer = comps[0] if comps else None   # biggest component = outer boundary
    for comp in comps:
        if comp is outer or comp["size"] < MIN_OBJECT_CELLS:
            continue
        stats["objects_found"] += 1
        # Skip if this object is already largely traced (a goto may have landed
        # on it while heading for another).
        already = sum(1 for c in comp["cells"] if c in black)
        if already > comp["size"] * 0.25:
            continue
        cx, cy = comp["centroid"]
        # Navigate toward the object until the front sensor meets its tape.
        # face() here is point-to-point dead reckoning between features — drift
        # only means we arrive approximately, and the bootstrap re-acquires.
        reached = False
        for _ in range(2 * size):
            dx = cx - robot.location[0]
            dy = cy - robot.location[1]
            if math.hypot(dx, dy) < 2:
                reached = True
                break
            face(math.atan2(dy, dx))
            if front() == BLACK:
                reached = True
                break
            step()
        if not reached:
            continue
        if not bootstrap_onto_tape(size):
            continue
        radius = comp["span"] / 2.0
        depart = max(2.0, min(radius * 0.6, 8.0))
        edge_follow(depart_radius=depart, return_tol=2.5,
                    max_steps=comp["size"] * 4 + 80)
        stats["objects_traced"] += 1
    stats["phase2_elapsed_sec"] = time.perf_counter() - t_p2

    stats["elapsed_sec"] = time.perf_counter() - t0
    stats["end"] = (int(robot.location[0]), int(robot.location[1]))
    return black, white, other, stats


def write_map(black, white, size, out_path):
    grid = [[' '] * size for _ in range(size)]
    for x, y in white:
        if 0 <= x < size and 0 <= y < size:
            grid[x][y] = '.'
    for x, y in black:
        if 0 <= x < size and 0 <= y < size:
            grid[x][y] = '#'
    with open(out_path, 'w') as f:
        for row in grid:
            f.write(''.join(row) + '\n')


def write_report(black, white, other, stats, out_path):
    rot = stats["total_rotation_rad"]
    lines = [
        f"=== {stats['label']} ===",
        f"start cell:              {stats['start']}",
        f"end cell:                {stats['end']}",
        f"elapsed:                 {stats['elapsed_sec']:.3f} s",
        "",
        "-- config --",
        f"steering increment:      {stats['dtheta_deg']:.1f}°",
        f"tape band width:         {stats['tape_width']} px",
        "",
        "-- cells --",
        f"path cells covered:      {len(white)}",
        f"tape band cells:         {len(black)}",
        f"other-color cells:       {len(other)}",
        "",
        "-- totals --",
        f"turn() calls:            {stats['turns']}",
        f"step() calls:            {stats['steps']}",
        f"checkIR*() calls:        {stats['color_checks']}",
        f"total rotation:          {math.degrees(rot):.0f}°"
        f" ({rot / (2 * math.pi):.1f} revolutions)",
        "",
        f"-- phase 1: outer boundary ({stats['phase1_elapsed_sec']:.3f} s) --",
        f"termination:             {stats.get('phase1_term', 'n/a')}",
        f"turn() calls:            {stats['phase1_turns']}",
        f"step() calls:            {stats['phase1_steps']}",
        "",
        f"-- phase 2: interior objects ({stats['phase2_elapsed_sec']:.3f} s) --",
        f"objects found:           {stats['objects_found']}",
        f"objects traced:          {stats['objects_traced']}",
    ]
    report = "\n".join(lines)
    print(report)
    with open(out_path, "w") as f:
        f.write(report + "\n")


HOST = "127.0.0.1"
PORT = 8080


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))

    # The robot firmware (final/main.c) is the TCP *client*; we are the server.
    # It connects, then we drive it command-by-command over the socket.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"waiting for robot to connect on {HOST}:{PORT} ...")
    connection, client_addr = server.accept()
    print(f"robot connected from {client_addr}")

    try:
        robot = RobotPhy(1, 128, connection)
        black, white, other, stats = sweep(robot)

        write_map(black, white, 128, os.path.join(here, "sweep_map.txt"))
        write_report(black, white, other, stats,
                     os.path.join(here, "sweep_report.txt"))
    finally:
        # 999 tells the firmware to leave its command loop and stop the motors.
        try:
            connection.sendall("999".encode())
        except OSError:
            pass
        connection.close()
        server.close()

    # To run against the simulator instead of the physical robot, swap the
    # try-block above for:
    #     robot = Robot(1, 128, error=0.005, tape_width=TAPE_WIDTH)
    #     black, white, other, stats = sweep(robot)
    #     ... (same write_map / write_report)