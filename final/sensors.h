#pragma once

#include "vl53l0x.h"
#include_next <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define R_0 10000.0
#define NOMINAL_V 3.3

static inline double r_to_t(double r_t) {
  const double T_0 = 298.15;  // Nominal room temperature in Kelvin (25°C)
  const double BETA = 4050.0; // Beta constant of the thermistor

  // Calculate temperature in Kelvin using the Beta equation
  double t_kelvin = 1.0 / ((1.0 / T_0) + (1.0 / BETA) * log(r_t / R_0));

  // Convert Kelvin to Celsius
  double t_celsius = t_kelvin - 273.15;

  return t_celsius;
}

double read_temperature();

int init_tof(uint8_t addr, iic_index_t iic_index, int long_distance);

// distance in MM
uint32_t read_tof();

enum color_sensor_colors { BLACK, WHITE, RED, BLUE, GREEN, DEFAULT };

enum color_sensor_colors get_color();

static inline void color_to_str(char *s, color_sensor_colors c) {
  switch (c) {
  case BLACK:
    strcpy(s, "BLACK");
    return;
  case WHITE:
    strcpy(s, "WHITE");
    return;
  case GREEN:
    strcpy(s, "GREEN");
    return;
  case RED:
    strcpy(s, "RED");
    return;
  case BLUE:
    strcpy(s, "BLUE");
    return;
  default:
    strcpy(s, "DEFAULT");
    return;
  }
}
float check_ir_v(bool right);