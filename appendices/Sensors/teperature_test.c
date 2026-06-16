#include "sensors.h"
#include <stddef.h>
#include <stdio.h>
#include "libpynq.h"

#define ADC_MAX 65535
#define ADC_CHANNEL ADC0

#define R_ADC      3550.0     // measured pull-down at the ADC pin

static inline double read_voltage() {
  size_t raw = adc_read_channel_raw(ADC_CHANNEL);
  double actual = (double)raw / ADC_MAX;
  return actual;
}

double read_temperature() {
  double v = read_voltage();

  double r_parallel = R_0 * (v / (NOMINAL_V - v));
double r = (r_parallel * R_ADC) / (R_ADC - r_parallel);

  printf("v: %f r: %f\n", v, r);

  return r_to_t(r);
}