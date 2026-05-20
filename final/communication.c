#include "communication.h"
#include <libpynq.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define PAUSE_SLEEP_DUR_MSEC 500
#define IDLE_SLEEP_DUR_MSEC 1
#define BYTE_TIMEOUT_MSEC 1000
#define COMMANDS_CAPACITY 64

#define MSG_LEN_MAX 255

static command_descriptor_t commands[COMMANDS_CAPACITY];
static size_t commands_size = 0;

static volatile int message_loop_stopper = 0;
static volatile int message_loop_pauser = 0;

// Returns 0 once a byte is available, -1 on timeout.
static int wait_for_byte(uint32_t timeout_msec) {
  for (uint32_t waited = 0; waited < timeout_msec; waited++) {
    if (uart_has_data(UART0))
      return 0;
    sleep_msec(1);
  }
  return uart_has_data(UART0) ? 0 : -1;
}

int read_msg(char *msg) {
  if (!uart_has_data(UART0))
    return -1;
  uint8_t size_bytes[4];

  for (uint32_t i = 0; i < 4; i++) {
    if (wait_for_byte(BYTE_TIMEOUT_MSEC) != 0)
      return -3;
    size_bytes[i] = uart_recv(UART0);
  }

  uint32_t size = ((uint32_t)size_bytes[0]) | ((uint32_t)size_bytes[1] << 8) |
                  ((uint32_t)size_bytes[2] << 16) |
                  ((uint32_t)size_bytes[3] << 24);

  if (size > MSG_LEN_MAX)
    return -2;

  for (uint32_t i = 0; i < size; i++) {
    if (wait_for_byte(BYTE_TIMEOUT_MSEC) != 0)
      return -3;
    msg[i] = (char)uart_recv(UART0);
  }

  msg[size] = '\0';
  return 0;
}

int command_listen_loop() {
  char msg[MSG_LEN_MAX + 1];

  while (!message_loop_stopper) {
    if (message_loop_pauser) {
      sleep_msec(PAUSE_SLEEP_DUR_MSEC);
      continue;
    }
    if (read_msg(msg)) {
      sleep_msec(IDLE_SLEEP_DUR_MSEC);
      continue;
    }
    for (size_t i = 0; i < commands_size; i++) {
      if (strcmp(commands[i].trigger_str, msg) == 0) {
        commands[i].callback_fn(NULL);
      }
    }
  }

  return 0;
}

void start_message_loop() {
  message_loop_stopper = 0;
  message_loop_pauser = 0;
}

void stop_message_loop() { message_loop_stopper = 1; }

void pause_message_loop() { message_loop_pauser = 1; }

void resume_message_loop() { message_loop_pauser = 0; }

int send_msg(const char *msg) {
  uint32_t size = strlen(msg);

  // Send size in little-endian format
  uart_send(UART0, size & 0xFF);
  uart_send(UART0, (size >> 8) & 0xFF);
  uart_send(UART0, (size >> 16) & 0xFF);
  uart_send(UART0, (size >> 24) & 0xFF);

  // Send payload
  for (uint32_t i = 0; i < size; i++) {
    uart_send(UART0, msg[i]);
  }

  return 0;
}

int register_new_command(command_descriptor_t *command) {
  if (commands_size >= COMMANDS_CAPACITY)
    return -2;
  for (size_t i = 0; i < commands_size; i++) {
    if (strcmp(commands[i].trigger_str, command->trigger_str) == 0) {
      return -1;
    }
  }

  commands[commands_size] = *command;
  commands_size++;
  free(command);

  return 0;
}

int remove_command(const char *trigger_str) {
  for (size_t i = 0; i < commands_size; i++) {
    if (strcmp(commands[i].trigger_str, trigger_str) == 0) {
      free(commands[i].trigger_str);
      memmove(&commands[i], &commands[i + 1],
              (commands_size - i - 1) * sizeof(command_descriptor_t));
      commands_size--;
      return 0;
    }
  }
  return -1;
}