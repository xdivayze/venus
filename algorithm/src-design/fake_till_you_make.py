import os
import sys

import numpy as np
from matplotlib.backend_bases import MouseEvent
import matplotlib.pyplot as plt
import cv2 as cv

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
px_per_cm: float = 0;

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
    
    

if __name__ == "__main__":
    if (len(sys.argv) < 5): 
        raise "usage: file.py image_path output_path normalized_start_location_x normalized_start_location_y"
    abs_impath = os.path.abspath(sys.argv[1]);
    abs_outpath = os.path.abspath(sys.argv[2]);
    
    img = cv.imread(abs_impath, cv.IMREAD_GRAYSCALE);
    img = cv.GaussianBlur(img, (0,0), 1.6);
    edges = cv.Canny(img, 150, 200);
    loc = (round(float(sys.argv[3]) * img.shape[1]) , round(float(sys.argv[4]) * img.shape[0]));
    
    np.vstack([clicked_points, loc]);
    
    fig, ax = plt.subplots();
    ax.imshow(edges, cmap="gray");
    ax.set_title("click to log points");
    
    fig.canvas.mpl_connect("button_press_event", on_click);
    
    plt.tight_layout();
    plt.show();
    
    px_per_cm = np.linalg.norm(measurement_points[-1] - measurement_points[0]) / dist
    
    
    
    