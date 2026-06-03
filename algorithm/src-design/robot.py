import math
import os
from enum import Enum
import socket
class Robot:
    def __init__(self, colorWorkingDistance: int, maxDist: int):
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
        
    def step(self, nr_steps: int):
        self.location = (self.location[0] + nr_steps * round(math.cos(self.angle)),self.location[1] + nr_steps * round(math.sin(self.angle)))
    def turn(self, angle):
        self.angle += angle;
    def checkDistance(self):
        return -1;
        
    def checkColorFront(self):
        newx = round( self.location[0] + round(self.colorWorkingDistance * math.cos(self.angle)))
        newy = round(self.location[1] + round(self.colorWorkingDistance * math.sin(self.angle)))
        return self.bytemap[newx][newy];
    
    def checkColorRight(self):
        newx = round( self.location[0] + round(self.colorWorkingDistance * math.cos(self.angle - math.pi / 2)))
        newy = round(self.location[1] + round(self.colorWorkingDistance * math.sin(self.angle - math.pi / 2)))
        return self.bytemap[newx][newy];
    
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
        
    def step(self, nr_steps: int):
        self.connection.sendall(("ROBOT_STEP:" + str(nr_steps)).encode());
    def turn(self, angle):
        self.connection.sendall(("ROBOT_TURN: " + str(angle)).encode());
    def checkDistance(self)->int:
        self.connection.sendall(("ROBOT_REQUEST_DISTANCE"));
        data = self.connection.recv(1024);
        return int(data.split(":")[1].strip());
    
    def checkColorFront(self)->Color:
        self.connection.sendall("ROBOT_REQUEST_COLOR");
        data = self.connection.recv(1024).split(":")[1].strip();
        return Color.str_to_color(data);
    
    @staticmethod
    def ir_to_color(ir: float)->Color:
        if (ir < 0.5):
            return Color.BLACK
        
        return Color.WHITE
            
    def checkIRFront(self)->Color:
        self.connection.sendall("ROBOT_REQUEST_IRFRONT");
        data = float(self.connection.recv(1024).split(":")[1].strip());
        return self.ir_to_color(data);
    
    def checkIRRight(self)->Color:
        self.connection.sendall("ROBOT_REQUEST_IRRIGHT");
        data = float(self.connection.recv(1024).split(":")[1].strip());
        return self.ir_to_color(data);

        
    
    
