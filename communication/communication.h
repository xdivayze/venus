#pragma once

#include <stddef.h>

typedef void (*command_callback_t)(void *args);

typedef struct {
  char *trigger_str;
  command_callback_t callback_fn;
} command_descriptor_t;

// -2 commands array full
// -1 command trigger word already registered
// consumes command and trigger str: takes ownership of both the descriptor and
// trigger_str (caller must not free either after a successful call)
int register_new_command(command_descriptor_t *command);

//-1 not found
int remove_command(const char *trigger_str);

int send_msg(const char *msg);

int command_listen_loop();

void start_message_loop();
void stop_message_loop();

void pause_message_loop();
void resume_message_loop();

// msg must point to a buffer of at least MSG_LEN_MAX + 1 (256) bytes.
// 0 success, -1 no data available, -2 size exceeds MSG_LEN_MAX,
// -3 timed out waiting for a byte mid-message.
int read_msg(char *msg);