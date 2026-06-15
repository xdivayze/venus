import os
from socket import socket
import sys

import numpy as np
from matplotlib.backend_bases import MouseEvent
import matplotlib.pyplot as plt
import cv2 as cv

from dataclasses import dataclass

from robot import RobotPhy

def show_edge_distance_histogram(edges: cv.typing.MatLike ):
    edge_points = np.column_stack(np.where(edges > 0))
    origin = np.array([img.shape[0] // 2, img.shape[1] // 2])
    distances = np.linalg.norm(edge_points - origin, axis=1)
    
    plt.hist(distances, bins=50);
    plt.axvline(distances.mean(), color="r", label="mean");
    plt.show();
    exit();
    
clicked_points = np.empty((0, 2), dtype=int)
measurement_points = np.empty((0, 2), dtype=int)
dist: float = 0

def on_click(event: MouseEvent):
    if event.inaxes is None:
        return

    point = np.array([[int(event.xdata), int(event.ydata)]])

    if event.button == 1:
        global clicked_points
        clicked_points = np.vstack([clicked_points, point])
        x, y = point[0]

        ax.plot(x, y, "r+", markersize=12, markeredgewidth=2)
        ax.annotate(f"{len(clicked_points)}: ({x}, {y})", (x, y),
                    textcoords="offset points", xytext=(6, 6),
                    color="red", fontsize=8)

        if len(clicked_points) > 1:
            p1, p2 = clicked_points[-2], clicked_points[-1]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'r-', linewidth=1.5)

    elif event.button == 3:
        global measurement_points, dist
        if len(measurement_points) >= 2:
            return

        measurement_points = np.vstack([measurement_points, point])
        x, y = point[0]

        ax.plot(x, y, "g+", markersize=12, markeredgewidth=2)
        ax.annotate(f"{len(measurement_points)}: ({x}, {y})", (x, y),
                    textcoords="offset points", xytext=(6, 6),
                    color="green", fontsize=8)

        if len(measurement_points) > 1:
            dist = int(input("measured length between the 2 points (cm): ").strip())
            p1, p2 = measurement_points[-2], measurement_points[-1]
            mid = (p1 + p2) / 2                        # numpy midpoint

            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'g-', linewidth=1.5)
            ax.annotate(f"real len: {dist}cm", (mid[0], mid[1]),
                        textcoords="offset points", xytext=(6, 6),
                        color="green", fontsize=8)

    fig.canvas.draw()

INSTRUCTION_ROTATE = 1
INSTRUCTION_STEP = 0

@dataclass
class Instruction:
    #0 step; 1 rotate
    operation: int
    #radians, + for ccw rotation
    payload: float 
    
    
    
def calculate_signed_angle(v1:np.typing.NDArray[np.float64], v2: np.typing.NDArray[np.float64]):
    cross =np.cross(v1, v2);
    dot = np.dot(v1, v2);
    return np.arctan2(cross, dot);

def point_array_to_instructions(clicked_points:np.typing.NDArray[np.float64], initial_heading: np.typing.NDArray[np.float64]):
    vectors = clicked_points[1:] - clicked_points[:-1];
    vectors = vectors * np.array([1.0, -1.0]); #correction for y down image space
    n_instructions = 2 * len(vectors)
    instructions = [None] * n_instructions
    initial_rot = calculate_signed_angle(initial_heading, vectors[0]);
    instructions[0] = Instruction(INSTRUCTION_ROTATE, initial_rot );
    
    for i in range (1, len(vectors)):
        idx = 1 + (i - 1) * 2
        instructions[idx]     = Instruction(INSTRUCTION_STEP,   np.linalg.norm(vectors[i-1]))
        instructions[idx + 1] = Instruction(INSTRUCTION_ROTATE, calculate_signed_angle(vectors[i-1], vectors[i]))
        
    instructions[-1] = Instruction(INSTRUCTION_STEP, np.linalg.norm(vectors[-1]))
    return instructions

def robot_do_instructions(instructions: list[Instruction]):
    HOST = "127.0.0.1"
    PORT = 8080
    
    here = os.path.dirname(os.path.abspath(__file__))
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"waiting for robot to connect on {HOST}:{PORT} ...")
    connection, client_addr = server.accept()
    print(f"robot connected from {client_addr}")
    robot = RobotPhy(1, 128, connection)
    
    for instruction in instructions:
        try:
            if instruction.operation == INSTRUCTION_STEP:
                robot.step(instruction.payload)
            else:  # INSTRUCTION_ROTATE
                robot.turn(instruction.payload)
        except ConnectionError:
            print("connection error occured, exiting", file=sys.stderr);
            break
    try:
        connection.sendall("999".encode())
    except OSError:
            pass
    connection.close()
    server.close()
        

if __name__ == "__main__":
    if (len(sys.argv) < 7): 
        #normalized locations are specified 0 to 1 relative to the shape of the image
        #initial heading is angle of the robot measured from +x in degrees CCW POS
        raise "usage: file.py image_path output_path normalized_start_location_x normalized_start_location_y initial_heading_deg dump_mode"
    abs_outpath = os.path.abspath(sys.argv[2]);
    dump_mode = int(sys.argv[6])
    if (dump_mode):
        abs_impath = os.path.abspath(sys.argv[1]);
        
        img = cv.imread(abs_impath, cv.IMREAD_GRAYSCALE);
        img = cv.GaussianBlur(img, (0,0), 1.6);
        edges = cv.Canny(img, 150, 200);
        
        loc = (round(float(sys.argv[3]) * img.shape[1]) , round(float(sys.argv[4]) * img.shape[0]));
        
        clicked_points = np.vstack([clicked_points, loc]);
        
        fig, ax = plt.subplots();
        ax.imshow(edges, cmap="gray");
        ax.set_title("click to log points");
        
        fig.canvas.mpl_connect("button_press_event", on_click);
        
        plt.tight_layout();
        plt.show();
        
        px_per_cm = np.linalg.norm(measurement_points[-1] - measurement_points[0]) / dist
        
        clicked_points_real = clicked_points / px_per_cm;
        
        # initial heading as a +x-CCW angle (deg) -> unit direction vector, since
        # point_array_to_instructions / calculate_signed_angle operate on vectors.
        initial_theta = np.radians( float(sys.argv[5]));
        initial_heading = np.array([np.cos(initial_theta), np.sin(initial_theta)]);

        instructions: list[Instruction] = point_array_to_instructions(clicked_points_real, initial_heading);
        
        with open(abs_outpath, "w") as f:
            for v in instructions:
                f.write(f"{v.operation}:{v.payload}\n");
                
    else:
        instructions: list[Instruction] = [];
        with open(abs_outpath, "r") as f:
            for line in f.readlines():
                tokens = line.strip().split(":")
                instructions.append(Instruction(int(tokens[0]), float(tokens[1])));
        
        print(instructions) 
           
        #robot_do_instructions(instructions);
    
    
    
    
    
    
    
    