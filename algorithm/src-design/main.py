import socket

from robot import Robot
import math
import os
import time

WHITE = 1
BLACK = 0


def in_bounds(x: int, y: int, size: int) -> bool:
    return 0 <= x < size and 0 <= y < size


def sweep(robot: Robot):
    """Right-hand wall follower for tracing the black-tape boundary.

    Uses only the front and right color sensors plus relative quarter-turns,
    so the algorithm never reads or aims at an absolute heading after the
    bootstrap step. On hardware this keeps accumulated gyro/encoder error
    small: every decision is local ("is right black?", "is front black?")
    instead of "am I facing exactly east?".

    Per iteration (right-hand rule reformulated for two ground sensors):
      - If right is not BLACK: the wall on our right has receded
        (convex corner of the tape) — turn right once and step to wrap it.
      - Else if front is not BLACK: wall continues on right, path is open
        — step forward.
      - Else: concave corner — turn left until the front clears.

    Termination: (cell, heading_index) state repeats, meaning we've come
    back to the same place pointing the same way → full loop closed.
    """
    size = int(robot.locationMaxAbs[0])
    start = (int(robot.location[0]), int(robot.location[1]))

    white = {start}
    black = set()
    other = set()
    heading = 0  # 0=initial, increments left, decrements right (mod 4)

    stats = {
        "label": "wall follower (front + right sensors, relative turns)",
        "start": start,
        "turns": 0,
        "steps": 0,
        "color_checks": 0,
        "right_turns": 0,
        "left_turns": 0,
    }

    def turn_right():
        nonlocal heading
        robot.turn(-math.pi / 2)
        heading = (heading - 1) % 4
        stats["turns"] += 1
        stats["right_turns"] += 1

    def turn_left():
        nonlocal heading
        robot.turn(math.pi / 2)
        heading = (heading + 1) % 4
        stats["turns"] += 1
        stats["left_turns"] += 1

    def cell_front():
        nx = round(robot.location[0] + round(math.cos(robot.angle)))
        ny = round(robot.location[1] + round(math.sin(robot.angle)))
        return (nx, ny)

    def cell_right():
        a = robot.angle - math.pi / 2
        nx = round(robot.location[0] + round(math.cos(a)))
        ny = round(robot.location[1] + round(math.sin(a)))
        return (nx, ny)

    def record(target, color):
        if not in_bounds(target[0], target[1], size):
            return
        if color == BLACK:
            black.add(target)
        elif color != WHITE:
            other.add(target)

    def check_front():
        t = cell_front()
        if not in_bounds(t[0], t[1], size):
            return -2, t
        c = robot.checkColorFront()
        stats["color_checks"] += 1
        record(t, c)
        return c, t

    def check_right():
        t = cell_right()
        if not in_bounds(t[0], t[1], size):
            return -2, t
        c = robot.checkColorRight()
        stats["color_checks"] += 1
        record(t, c)
        return c, t

    def step():
        robot.step(1)
        stats["steps"] += 1
        cell = (int(robot.location[0]), int(robot.location[1]))
        if in_bounds(cell[0], cell[1], size):
            white.add(cell)

    t0 = time.perf_counter()

    # Bootstrap: drive forward in the robot's initial heading until we hit
    # something non-white, then turn left once so that tape ends up on the
    # right. Direction-agnostic — no absolute angle target needed.
    while True:
        c, _ = check_front()
        if c != WHITE:
            break
        step()
    turn_left()

    visited = set()
    max_iters = 4 * size * size
    for _ in range(max_iters):
        state = (int(robot.location[0]), int(robot.location[1]), heading)
        if state in visited:
            break
        visited.add(state)

        rc, _ = check_right()
        if rc != BLACK:
            # Right sensor lost the tape — wrap a convex corner.
            turn_right()
            fc, _ = check_front()
            if fc != BLACK and fc != -2:
                step()
        else:
            fc, _ = check_front()
            if fc != BLACK and fc != -2:
                # Wall on right, path clear — march along the wall.
                step()
            else:
                # Concave corner: keep turning left until the front opens
                # up (capped so we can't spin in place forever).
                turn_left()
                tries = 0
                while tries < 3:
                    fc2, _ = check_front()
                    if fc2 != BLACK and fc2 != -2:
                        break
                    turn_left()
                    tries += 1

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
        f"checkColor*() calls:     {stats['color_checks']}",
        f"  right turns:           {stats['right_turns']}",
        f"  left turns:            {stats['left_turns']}",
    ]
    report = "\n".join(lines)
    print(report)
    with open(out_path, "w") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    socket_path = "/tmp/robot_sock";
    try:
        os.unlink(socket_path);
    except OSError:
        if (os.path.exists(socket_path)):
            raise
    
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM);
    server.bind(socket_path);
    
    server.listen(1);
    
    connection, client_addr = server.accept();
    
    
    here = os.path.dirname(os.path.abspath(__file__))

    robot = Robot(1, 128)
    black, white, other, stats = sweep(robot)

    write_map(black, white, 128, os.path.join(here, "sweep_map.txt"))
    write_report(black, white, other, stats,
                 os.path.join(here, "sweep_report.txt"))
