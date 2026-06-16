#pragma once

#include <stddef.h>
#define M_PI 3.14159265

#define FULL_ROTATION_CYCLE 1600

#define WHEEL_RADIUS 4
#define AXIS_RADIUS 13 //interwheel distance

void do_circle();
//angle in degrees
void rotate_angle(float angle);

void set_circle_clockwise();
void set_circle_cclockwise();

void step(size_t nr_steps);