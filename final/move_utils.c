#include "move_utils.h"
#include <math.h>
#include <stepper.h>
#include <libpynq.h>
static int clockwise = 0;

static float angle_counter = 0.0f;

void do_circle() { rotate_angle(360.0f); }

void rotate_angle(float angle) {
  float axis_circumference = AXIS_RADIUS * M_PI * angle / 360; //rotation around own axis
  float wheel_circumference = 2 * WHEEL_RADIUS * M_PI;

  int step =
      (int)(FULL_ROTATION_CYCLE * (axis_circumference / wheel_circumference));

  if (!clockwise) {
    stepper_steps(step, -step);
  } else {
    stepper_steps(-step, step);
  }

  angle = clockwise ? angle * -1 : angle;
  angle_counter = fmod((angle + angle_counter), 360.0f);

  while (1) {
    sleep_msec(100);
    if (stepper_steps_done())
      return;
  }
}

void set_circle_clockwise() { clockwise = 1; }
void set_circle_cclockwise() { clockwise = 0; }

void step(size_t cm) {
  float wheel_circumference = 2 * WHEEL_RADIUS * M_PI;
  size_t steps = FULL_ROTATION_CYCLE * cm / wheel_circumference  
  stepper_steps(steps, steps);
  while (1) {
    sleep_msec(100);
    if (stepper_steps_done())
      return;
  }
}

