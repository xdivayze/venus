#include <libpynq.h>

float get_color_frequency(pulsecounter_index_t pci) {
    uint32_t t1, t2;
    uint32_t c1, c2;

    c1 = pulsecounter_get_count(pci, &t1);
    sleep_msec(20);
    c2 = pulsecounter_get_count(pci, &t2);

    uint32_t pulses = c2 - c1;
    uint32_t cycles = t2 - t1;

    return ((float)pulses / cycles) * 1000000;
}	

void colour_loop();

int main(void) {
  pynq_init();
  buttons_init();
  gpio_init();
  pulsecounter_init(0);
  switchbox_init();

  gpio_set_direction(IO_AR4, GPIO_DIR_OUTPUT);
  gpio_set_direction(IO_AR5, GPIO_DIR_OUTPUT);
  gpio_set_direction(IO_AR6, GPIO_DIR_OUTPUT);
  gpio_set_direction(IO_AR7, GPIO_DIR_OUTPUT);

  switchbox_set_pin(IO_AR8, SWB_TIMER_IC0);

  gpio_set_level(IO_AR4, GPIO_LEVEL_HIGH);
  gpio_set_level(IO_AR5, GPIO_LEVEL_LOW);

  colour_loop();

  switchbox_destroy();
  pulsecounter_destroy(0);
  gpio_destroy();
  buttons_destroy();
  pynq_destroy();
  return EXIT_SUCCESS;
}

void colour_loop() {
  while (!get_button_state(BUTTON1)) {
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
      
      if (clear > 500){
        fprintf(stdout, "BLOCK IS WHITE\n");
      }
      else if (clear < 120){
        fprintf(stdout, "BLOCK IS BLACK\n");
      }
      else if ((red > (2*blue)) && (red > (2*green))){
        fprintf(stdout, "BLOCK IS RED\n");
      }
      else if ((blue > red) && (blue > green)){
        fprintf(stdout, "BLOCK IS BLUE\n");
      }
      else if ((green > red) && (green > blue)){
        fprintf(stdout, "BLOCK IS GREEN\n");
      }

      sleep_msec(100);
  }
}