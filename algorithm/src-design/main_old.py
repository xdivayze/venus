from robot_old import Robot
import math
import os
import time

WHITE = 1
BLACK = 0

EAST = 0.0
NORTH = math.pi / 2
WEST = math.pi
SOUTH = -math.pi / 2


def in_bounds(x: int, y: int, size: int) -> bool:
    return 0 <= x < size and 0 <= y < size


def _shortest_angle(delta: float) -> float:
    while delta > math.pi:
        delta -= 2 * math.pi
    while delta <= -math.pi:
        delta += 2 * math.pi
    return delta


def _angle_idx(a: float) -> int:
    """Map any angle to one of {0=E, 1=N, 2=W, 3=S}. Used for state-tracked
    termination of the wall follower."""
    a = math.fmod(a, 2 * math.pi)
    if a < 0:
        a += 2 * math.pi
    if a < math.pi / 4 or a >= 7 * math.pi / 4:
        return 0
    if a < 3 * math.pi / 4:
        return 1
    if a < 5 * math.pi / 4:
        return 2
    return 3


def sweep(robot: Robot):
    """Two-phase sweep:

    Phase 1 — wall follower. Drive south until non-white, then right-hand-
    follow the wall until the (position, heading) state repeats. Maps the
    outer boundary tape.

    Phase 2 — interior grid sweep. Bidirectional row sweep, advancing one
    row north between rows (with east-backup if direct north is blocked).
    Whenever the grid probe hits a non-white cell that hasn't been wall-
    followed yet, fire off another wall-follow on it to trace its full
    perimeter, then return to the original heading and continue the row.

    Both phases share one wall_follow helper; Phase 1 bootstraps by driving
    south+facing east, Phase 2's marker traces bootstrap by turning 90° left
    so the obstacle ends up on the robot's right.
    """
    size = int(robot.locationMaxAbs[0])
    start = (int(robot.location[0]), int(robot.location[1]))

    white = {start}
    black = set()
    other = set()
    wall_followed = set()  # cells of obstacles whose perimeter is already traced

    stats = {
        "label": "wall follower + interior grid + marker trace",
        "start": start,
        "turns": 0,
        "steps": 0,
        "color_checks": 0,
        "total_rotation_rad": 0.0,
        "phase1_turns": 0, "phase1_steps": 0, "phase1_checks": 0,
        "phase2_turns": 0, "phase2_steps": 0, "phase2_checks": 0,
        "phase2_rows": 0,
        "markers_traced": 0,
    }

    def face(target_angle):
        delta = _shortest_angle(target_angle - robot.angle)
        robot.turn(delta)
        stats["turns"] += 1
        stats["total_rotation_rad"] += abs(delta)

    def cell_ahead():
        nx = round(robot.location[0] + round(math.cos(robot.angle)))
        ny = round(robot.location[1] + round(math.sin(robot.angle)))
        return (nx, ny)

    def probe():
        """Probe ahead. Returns (color, target). target is None if OOB.
        Records non-white cells into black/other (but not wall_followed)."""
        target = cell_ahead()
        if not in_bounds(target[0], target[1], size):
            return -2, None
        color = robot.checkColor()
        stats["color_checks"] += 1
        if color == BLACK:
            black.add(target)
        elif color != WHITE:
            other.add(target)
        return color, target

    def step():
        robot.step(1)
        stats["steps"] += 1
        white.add((int(robot.location[0]), int(robot.location[1])))

    def wall_follow():
        """Right-hand wall-follow until (cell, heading) state repeats. The
        caller is responsible for bootstrapping into a state with the wall
        on the robot's right. Every blocked probe gets added to
        wall_followed so we don't re-trace the same obstacle."""
        visited = set()
        max_iters = 4 * size * size
        for _ in range(max_iters):
            state = (int(robot.location[0]), int(robot.location[1]),
                     _angle_idx(robot.angle))
            if state in visited:
                return
            visited.add(state)

            forward = robot.angle
            face(forward - math.pi / 2)
            color, target = probe()
            if color == WHITE:
                step()
                continue
            if target is not None:
                wall_followed.add(target)
            face(forward)
            color, target = probe()
            if color == WHITE:
                step()
                continue
            if target is not None:
                wall_followed.add(target)
            face(forward + math.pi / 2)

    def grid_probe():
        """Probe ahead. If we find an obstacle we haven't traced yet, fire
        off a wall-follow on it and restore the original heading."""
        color, target = probe()
        if color == WHITE or target is None or target in wall_followed:
            return color
        wall_followed.add(target)
        stats["markers_traced"] += 1
        original_angle = robot.angle
        face(original_angle + math.pi / 2)  # left 90° puts the obstacle on our right
        wall_follow()
        face(original_angle)
        return color

    t0 = time.perf_counter()

    # ---- Phase 1: outer boundary ----
    t_p1 = time.perf_counter()
    face(SOUTH)
    while True:
        color, _ = probe()
        if color != WHITE:
            if color == BLACK and _ is not None:
                wall_followed.add(_)
            break
        step()
    face(EAST)
    wall_follow()
    stats["phase1_elapsed_sec"] = time.perf_counter() - t_p1
    stats["phase1_turns"] = stats["turns"]
    stats["phase1_steps"] = stats["steps"]
    stats["phase1_checks"] = stats["color_checks"]

    # ---- Phase 2: interior grid sweep ----
    t_p2 = time.perf_counter()

    def try_advance_north():
        face(NORTH)
        if grid_probe() == WHITE:
            step()
            return True
        for _ in range(size):
            face(EAST)
            if grid_probe() != WHITE:
                return False
            step()
            face(NORTH)
            if grid_probe() == WHITE:
                step()
                return True
        return False

    while True:
        face(EAST)
        while grid_probe() == WHITE:
            step()
        face(WEST)
        while grid_probe() == WHITE:
            step()
        stats["phase2_rows"] += 1

        if not try_advance_north():
            break

    stats["phase2_elapsed_sec"] = time.perf_counter() - t_p2
    stats["phase2_turns"] = stats["turns"] - stats["phase1_turns"]
    stats["phase2_steps"] = stats["steps"] - stats["phase1_steps"]
    stats["phase2_checks"] = stats["color_checks"] - stats["phase1_checks"]

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
    lines = [
        f"=== {stats['label']} ===",
        f"start cell:              {stats['start']}",
        f"end cell:                {stats['end']}",
        f"elapsed:                 {stats['elapsed_sec']:.3f} s",
        "",
        "-- cells --",
        f"white cells covered:     {len(white)}",
        f"black tape cells:        {len(black)}",
        f"other-color cells:       {len(other)}",
        "",
        "-- totals --",
        f"turn() calls:            {stats['turns']}",
        f"step() calls:            {stats['steps']}",
        f"checkColor() calls:      {stats['color_checks']}",
        f"total rotation:          {math.degrees(stats['total_rotation_rad']):.1f}°"
        f" ({stats['total_rotation_rad'] / (2 * math.pi):.1f} full revolutions)",
        "",
        f"-- phase 1: wall follower ({stats['phase1_elapsed_sec']:.3f} s) --",
        f"turn() calls:            {stats['phase1_turns']}",
        f"step() calls:            {stats['phase1_steps']}",
        f"checkColor() calls:      {stats['phase1_checks']}",
        "",
        f"-- phase 2: interior grid ({stats['phase2_elapsed_sec']:.3f} s) --",
        f"turn() calls:            {stats['phase2_turns']}",
        f"step() calls:            {stats['phase2_steps']}",
        f"checkColor() calls:      {stats['phase2_checks']}",
        f"rows swept:              {stats['phase2_rows']}",
        f"markers traced:          {stats['markers_traced']}",
    ]
    report = "\n".join(lines)
    print(report)
    with open(out_path, "w") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))

    robot = Robot(1, 128)
    black, white, other, stats = sweep(robot)

    write_map(black, white, 128, os.path.join(here, "sweep_map.txt"))
    write_report(black, white, other, stats,
                 os.path.join(here, "sweep_report.txt"))
