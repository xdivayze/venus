#include "sensors.h"
#include "libpynq.h"
#include <stddef.h>
#include <stdio.h>

#define ADC_MAX 65535
#define ADC_CHANNEL ADC0

#define R_ADC 3250.0 // measured pull-down at the ADC pin (calibrate)

static inline double read_voltage() {
  size_t raw = adc_read_channel_raw(ADC_CHANNEL);
  double actual = (double)raw / ADC_MAX;
  return actual;
}

double read_temperature() {
  double v = read_voltage();
  // double v = adc_read_channel(ADC_CHANNEL); //substitute if the code above is not working

  double r_parallel = R_0 * (v / (NOMINAL_V - v));
  double r = (r_parallel * R_ADC) / (R_ADC - r_parallel);

  printf("v: %f r: %f\n", v, r);

  return r_to_t(r);
}

bool tof_initialized = false;
static vl53x dev_ptr_;

int init_tof(uint8_t addr, iic_index_t iic_index, int long_distance) {
  if (tofInit(&dev_ptr_, iic_index, addr, long_distance))
    return -1;
  tof_initialized = true;
  return 0;
}

uint32_t read_tof() {
  if (!tof_initialized)
    return 1;
  return tofReadDistance(&dev_ptr_);
}

static float get_color_frequency(pulsecounter_index_t pci) {
  uint32_t t1, t2;
  uint32_t c1, c2;

  c1 = pulsecounter_get_count(pci, &t1);
  sleep_msec(20);
  c2 = pulsecounter_get_count(pci, &t2);

  uint32_t pulses = c2 - c1;
  uint32_t cycles = t2 - t1;

  return ((float)pulses / cycles) * 1000000;
}

enum color_sensor_colors get_color() {
  gpio_set_level(IO_AR6, GPIO_LEVEL_LOW);
  gpio_set_level(IO_AR7, GPIO_LEVEL_LOW);
  sleep_msec(5);
  float red = get_color_frequency(0);

  gpio_set_level(IO_AR6, GPIO_LEVEL_LOW);
  gpio_set_level(IO_AR7, GPIO_LEVEL_HIGH);
  sleep_msec(5);
  float blue = get_color_frequency(0);

  gpio_set_level(IO_AR6, GPIO_LEVEL_HIGH);
  gpio_set_level(IO_AR7, GPIO_LEVEL_LOW);
  sleep_msec(5);
  float clear = get_color_frequency(0);

  gpio_set_level(IO_AR6, GPIO_LEVEL_HIGH);
  gpio_set_level(IO_AR7, GPIO_LEVEL_HIGH);
  sleep_msec(5);
  float green = get_color_frequency(0);

  if (clear > 500) {
    return WHITE;
  } else if (clear < 120) {
    return BLACK;
  } else if ((red > (2 * blue)) && (red > (2 * green))) {
    return RED;
  } else if ((blue > red) && (blue > green)) {
    return BLUE;
  } else if ((green > red) && (green > blue)) {
    return GREEN;
  }

  return DEFAULT;
}