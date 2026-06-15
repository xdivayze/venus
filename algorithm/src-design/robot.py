import math
import os
import random
from enum import Enum
import socket
class Robot:
    def __init__(self, colorWorkingDistance: int, maxDist: int, error: float = 0.0,
                 tape_width: int = 1):
        self.speed = 1;

        self.location = (maxDist / 2,maxDist / 2);
        self.locationMaxAbs = (maxDist, maxDist);
        self.maxDist = maxDist;

        self.angle = 0.0;
        # error >= 0 is the noise magnitude used to model real-hardware drift.
        # 0.0 => perfect actuation (reproduces the exact, snap-to-grid sim).
        #   turn(): heading gains Gaussian noise ~ N(0, error * |angle|)  (gyro drift)
        #   step(): travel distance and a lateral slip each gain Gaussian
        #           noise ~ N(0, error * nr_steps)                        (wheel slip)
        # Drift accumulates because neither turn nor step ever corrects the
        # pose back to the grid -- exactly the failure mode the wall-follower
        # (relative turns, local sensing) is meant to tolerate.
        self.error = error;
        self.bytemap = [[0] * maxDist for _ in range(maxDist)]
        with open(os.path.normpath(os.path.join(__file__, "../../tests/assets/obstacle_map_no_white_obstacle_out")), "rb") as f:
            for i in range(maxDist):
                line = f.readline(maxDist)
                self.bytemap[i] = [c - 48 for c in line.strip()]
            f.close();


        self.colorWorkingDistance = colorWorkingDistance;

        # Tape-width model. Real tape is a band several mm wide, not a 1-pixel
        # line, so its edge stays under a sensor across a range of headings.
        # The 1-px source map can't express that, so we dilate the black tape
        # into a band of width `tape_width` (only growing into white cells, so
        # colored markers are left intact). The continuous-sampling sensors
        # below then read this `sensemap`, which makes proportional, non-
        # cardinal edge-following possible.
        self.tape_width = tape_width
        if tape_width and tape_width > 1:
            R = tape_width // 2
            n = maxDist
            offsets = [(di, dj) for di in range(-R, R + 1)
                       for dj in range(-R, R + 1) if di * di + dj * dj <= R * R]
            sense = [row[:] for row in self.bytemap]
            for i in range(n):
                row = self.bytemap[i]
                for j in range(n):
                    if row[j] == 0:  # black tape pixel -> grow band into white
                        for di, dj in offsets:
                            ii, jj = i + di, j + dj
                            if 0 <= ii < n and 0 <= jj < n and sense[ii][jj] == 1:
                                sense[ii][jj] = 0
            self.sensemap = sense
        else:
            self.sensemap = self.bytemap

    def _sample(self, px: float, py: float) -> int:
        """Read the (dilated) map at a continuous floor position, snapping only
        the final lookup to the grid the map is stored on. No rounding of the
        heading direction, so intermediate headings probe the true offset
        point rather than jumping to a diagonal neighbour."""
        x = round(px); y = round(py)
        if x < 0: x = 0
        elif x >= self.maxDist: x = self.maxDist - 1
        if y < 0: y = 0
        elif y >= self.maxDist: y = self.maxDist - 1
        return self.sensemap[x][y]

    def step(self, nr_steps: int):
        if self.error <= 0:
            self.location = (self.location[0] + nr_steps * round(math.cos(self.angle)),self.location[1] + nr_steps * round(math.sin(self.angle)))
            return
        # Noisy continuous motion: travel a bit short/long, and slip sideways.
        dist = nr_steps + random.gauss(0, self.error * nr_steps)
        slip = random.gauss(0, self.error * nr_steps)
        fwd = self.angle
        side = self.angle - math.pi / 2
        self.location = (
            self.location[0] + dist * math.cos(fwd) + slip * math.cos(side),
            self.location[1] + dist * math.sin(fwd) + slip * math.sin(side),
        )
    def turn(self, angle):
        if self.error > 0:
            angle += random.gauss(0, self.error * abs(angle))
        self.angle += angle;
    def checkDistance(self):
        return -1;
    
        
    def checkColorFront(self):
        px = self.location[0] + self.colorWorkingDistance * math.cos(self.angle)
        py = self.location[1] + self.colorWorkingDistance * math.sin(self.angle)
        return self._sample(px, py)

    def checkColorRight(self):
        a = self.angle - math.pi / 2
        px = self.location[0] + self.colorWorkingDistance * math.cos(a)
        py = self.location[1] + self.colorWorkingDistance * math.sin(a)
        return self._sample(px, py)

    # IR aliases so the algorithm can talk to the sim and the physical robot
    # through the same checkIR* interface, both returning Color. The simulated
    # IR sensor is binary: tape -> BLACK, anything else -> WHITE.
    def checkIRFront(self):
        return Color.BLACK if self.checkColorFront() == Color.BLACK.value else Color.WHITE

    def checkIRRight(self):
        return Color.BLACK if self.checkColorRight() == Color.BLACK.value else Color.WHITE

class Color(Enum):
    BLACK = 0
    WHITE = 1
    DEFAULT = 7
    
    def str_to_color(s)->Color: 
        match s:
            case "BLACK":
                return Color.BLACK
            case "WHITE":
                return Color.WHITE
            case _:
                return Color.DEFAULT
    
class RobotPhy:
    IR_FRONT_THRESH = 3.0
    IR_RIGHT_THRESH = 0.2

    def __init__(self, colorWorkingDistance: int, maxDist: int, connection: socket.socket):
        self.speed = 1;
        
        self.location = (maxDist / 2,maxDist / 2);
        self.locationMaxAbs = (maxDist, maxDist);
        
        self.angle = 0.0;
        self.bytemap = [[0] * maxDist for _ in range(maxDist)]
        with open(os.path.normpath(os.path.join(__file__, "../../tests/assets/obstacle_map_no_white_obstacle_out")), "rb") as f:
            for i in range(maxDist):
                line = f.readline(maxDist)
                self.bytemap[i] = [c - 48 for c in line.strip()]
            f.close();
            
        
        self.colorWorkingDistance = colorWorkingDistance;
        self.connection = connection;
        
        """
        100 - step
        101 - turn
        200 - request distance
        201 - request color front
        202 - request ir front
        203 - request ir right
        """
        
    def _receive_and_decode(self):
        data = self.connection.recv(1024)
        if not data:
            raise ConnectionError("robot closed the connection")
        text = data.decode(errors="ignore").strip()
        return text
        
    def _request(self, code: int) -> str:
        self.connection.sendall(str(code).encode())
        text = self._receive_and_decode();
        return text.split(":", 1)[1].strip() if ":" in text else text

    def step(self, nr_steps: int):
        self.connection.sendall(("100:" + str(nr_steps)).encode());
        text = self._receive_and_decode();
        if (text != "100"):
            raise ConnectionError("NACK");
        self.location = ( #this estimate will almost always be off due to physical robot error
            self.location[0] + nr_steps * math.cos(self.angle),
            self.location[1] + nr_steps * math.sin(self.angle),
        )
        
    #angle in radians
    def turn(self, angle):
        self.connection.sendall(("101:" + str(angle)).encode());
        text = self._receive_and_decode();
        if (text != "101"):
            raise ConnectionError("NACK");
        self.angle += angle
    def checkDistance(self)->int:
        return int(self._request(200));

    def checkColorFront(self)->Color:
        return Color.str_to_color(self._request(201));

    @staticmethod
    def ir_to_color(ir: float, thresh: float)->Color:
        # Above the threshold is bare floor (WHITE); below it is tape (BLACK).
        if (ir < thresh):
            return Color.BLACK

        return Color.WHITE

    def checkIRFront(self)->Color:
        return self.ir_to_color(float(self._request(202)), self.IR_FRONT_THRESH);

    def checkIRRight(self)->Color:
        return self.ir_to_color(float(self._request(203)), self.IR_RIGHT_THRESH);

        
    
    
