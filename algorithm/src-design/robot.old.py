import math
import os
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
        
    def checkColor(self):
        newx = round( self.location[0] + round(self.colorWorkingDistance * math.cos(self.angle)))
        newy = round(self.location[1] + round(self.colorWorkingDistance * math.sin(self.angle)))
        return self.bytemap[newx][newy];
    
    
