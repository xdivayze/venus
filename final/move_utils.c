#include "move_utils.h"
#include <math.h>
#include <stepper.h>
static int clockwise = 0;

static float angle_counter = 0.0f;

void do_circle() { rotate_angle(360.0f); }

void rotate_angle(float angle) {
  float axis_circumference = 2 * AXIS_RADIUS * M_PI * angle / 360;
  float wheel_circumference = 2 * WHEEL_RADIUS * M_PI;

  int step =
      (int)(FULL_ROTATION_CYCLE * (axis_circumference / wheel_circumference));

  if (!clockwise) {
    stepper_steps(step, 0);
  } else {
    stepper_steps(0, step);
  }

  angle = clockwise ? angle * -1 : angle;
  angle_counter = fmod((angle + angle_counter), 360.0f);
}

void set_circle_clockwise() { clockwise = 1; }
void set_circle_cclockwise() { clockwise = 0; }