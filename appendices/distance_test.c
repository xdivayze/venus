#include <libpynq.h>
#include "sensors.h"
int main(void) {
  pynq_init();

  switchbox_set_pin(IO_AR_SCL, SWB_IIC0_SCL);
  switchbox_set_pin(IO_AR_SDA, SWB_IIC0_SDA);
  iic_init(IIC0);

  bool s = init_tof(0x29, IIC0, 0);
  if (s) printf("error");
        if (tofPing(IIC0, 0x29)) printf("error iic");

  while (1) {
        uint32_t val = read_tof();
        printf("%d mm\n", val);
  }

  iic_destroy(IIC0);
  pynq_destroy();
  return EXIT_SUCCESS;
}