#pragma once

#include_next <math.h>
#include <stdint.h>
#include "vl53l0x.h" 

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

uint32_t read_tof();
