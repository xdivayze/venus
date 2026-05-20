#include <libpynq.h>
#include <stdio.h>
#include <stepper.h>
#include "communication.h"

#define M_PI 3.14159265


#define FULL_ROTATION_CYCLE 1600

#define WHEEL_RADIUS 4
#define AXIS_RADIUS 13

static int clockwise = 0;

static void set_rotation_clockwise() {
	clockwise = 1;
	send_msg("SUCCESS: ROTATE SET CLOCKWISE");
}

static void set_rotation_cclockwise() {
	clockwise = 0;
	send_msg("SUCCESS: ROTATE SET COUNTER CLOCKWISE");
}

static void move_one_rotation() {
		float axis_circumference =2* AXIS_RADIUS * M_PI;
		float wheel_circumference =2* WHEEL_RADIUS * M_PI;

		int step = (int)(FULL_ROTATION_CYCLE * (axis_circumference / wheel_circumference));
		printf("step nr: %i", step);


		if (!clockwise){
			stepper_steps(step,0);
		} else {
			stepper_steps(0, step);
		}

		send_msg("SUCCESS: ROTATE");
}

int main(void) {
  pynq_init();

  printf("Hello there \n");

  switchbox_set_pin(IO_AR0, SWB_UART0_RX);
    switchbox_set_pin(IO_AR1, SWB_UART0_TX);

    uart_init(UART0);



  stepper_init();
  // Apply power to the stepper motors.
  stepper_enable();
  stepper_set_speed(20000, 20000);


	
	command_descriptor_t *desc = malloc(sizeof(command_descriptor_t));
	desc->trigger_str = strdup("ROTATE");
	desc->callback_fn = move_one_rotation;
	register_new_command(desc);

	desc = malloc(sizeof(command_descriptor_t));
	desc->trigger_str = strdup("SET ROTATION CLOCKWISE");
	desc->callback_fn = set_rotation_clockwise;
	register_new_command(desc);

	desc = malloc(sizeof(command_descriptor_t));
	desc->trigger_str = strdup("SET ROTATION COUNTERCLOCKWISE");
	desc->callback_fn = set_rotation_cclockwise;
	register_new_command(desc);


  command_listen_loop();

  uart_destroy(UART0);

  //stepper_destroy();
  pynq_destroy();
  return EXIT_SUCCESS;
}
