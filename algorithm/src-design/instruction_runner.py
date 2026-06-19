from dataclasses import dataclass
import os
import socket
import sys
from robot import RobotPhy

INSTRUCTION_ROTATE = 1
INSTRUCTION_STEP = 0

@dataclass
class Instruction:
    #0 step; 1 rotate
    operation: int
    #radians, + for ccw rotation
    payload: float
    #object/type to transmit via sendDataMQTT once this instruction
    #completes; empty string means nothing to send
    send_payload: str = ""


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
                # an object was recorded at the waypoint this step arrives at;
                # transmit it to the satellite now that we're there.
                if instruction.send_payload:
                    robot.sendDataMQTT(instruction.send_payload)
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

    abs_outpath = os.path.abspath(sys.argv[2]);
    instructions: list[Instruction] = [];
    with open(abs_outpath, "r") as f:
        for line in f.readlines():
            # maxsplit=2 keeps any ':' inside the object name intact as the 3rd field
            tokens = line.strip().split(":", 2)
            if len(tokens) < 2:
                continue
            send_payload = tokens[2].strip() if len(tokens) > 2 else ""
            instructions.append(Instruction(int(tokens[0]), float(tokens[1]), send_payload));
        f.close()
    robot_do_instructions(instructions)