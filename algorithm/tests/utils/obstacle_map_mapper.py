import cv2 as cv
import sys
import os

OUT_RED = 4
OUT_BLUE = 2;
OUT_BLACK = 0;
OUT_WHITE = 1
OUT_GREEN = 3;

COLOR_MAP = {
    (0, 0, 255):   OUT_RED,
    (255, 0, 0):   OUT_BLUE,
    (0, 0, 0):     OUT_BLACK,
    (255, 255, 255): OUT_WHITE,
    (0, 255, 0):   OUT_GREEN,
}

def main():
    if (len(sys.argv) < 3): 
        raise "usage: file.py image_path output_path"
    abs_impath = os.path.abspath(sys.argv[1]);
    abs_outpath = os.path.abspath(sys.argv[2]);
    
    
    
    img = cv.imread(abs_impath);
    
    rows, cols = img.shape[:2];
    with open(abs_outpath, "a") as f:
        for i in range (0, rows):
            for j in range(0, cols):
                key = tuple(int(c) for c in img[i][j])
                f.write(str(COLOR_MAP.get(key, -1)))
        f.close();
        
    
    
    
    
if __name__ == "__main__":
    main()