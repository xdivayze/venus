#include <stdio.h>
#include <libpynq.h>
#include <stepper.h>

int main(void) {
    pynq_init();
    stepper_init();
    stepper_enable();
    
    stepper_set_speed(20000, 20000);

    printf("Robot moving forward...\n");
    stepper_steps(800, 800);

    stepper_disable();
    stepper_destroy();
    pynq_destroy();

    return 0;
}