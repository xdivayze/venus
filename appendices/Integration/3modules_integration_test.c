/* The following structure:

Testing sets
{x: 10, y: 10, col: WHITE, temp: 21},
{x: -7, y: 19, col: BLUE, temp: 25.5}, 
{x: 0, y: -4, col: RED, temp: 18.9}

Adapted to json format
{"x": 10, "y": 10, "color": "white", "size": "small", "temp": 21},
{"x": -7, "y": 19, "color": "blue", "size": "small", "temp": 25.5}, 
{"x": 0, "y": -4, "color": "red", "size": "large", "temp": 18.9}

Adapted to MQTT message
{\"x\": 10, \"y\": 10, \"color\": \"white\", \"size\": \"small\", \"temp\": 21}
{\"x\": -7, \"y\": 19, \"color\": \"blue\", \"size\": \"small\", \"temp\": 25.5}
{\"x\": 0, \"y\": -4, \"color\": \"red\", \"size\": \"large", \"temp\": 18.9}

Then sending via ESP32 UART Robot to UI comms receiver ('/sample' topic)

Mapping of the relevant data correctly on the UI displayed

done
*/

#include "communication.h"
#include <libpynq.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>

int send_msg(const char *msg) {
  uint32_t size = strlen(msg);

  uart_send(UART0, size & 0xFF);
  uart_send(UART0, (size >> 8) & 0xFF);
  uart_send(UART0, (size >> 16) & 0xFF);
  uart_send(UART0, (size >> 24) & 0xFF);

  for (uint32_t i = 0; i < size; i++) {
    uart_send(UART0, msg[i]);
  }

  return 0;
}

int main(void) {
  char input_buffer[256];

  uart_init(UART0); 

  printf("Enter a message to send: ");
  if (fgets(input_buffer, sizeof(input_buffer), stdin) != NULL) {
    input_buffer[strcspn(input_buffer, "\n")] = '\0';
    
    send_msg(input_buffer);
    printf("Message sent successfully.\n");
  }

  return 0;
}