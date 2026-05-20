#pragma once 
#include <stddef.h>
#include <stdint.h>
int uart_has_data(int uart);
uint8_t uart_recv(int uart);
int uart_send(int uart, uint8_t msg);

void sleep_msec(size_t sleep_msec);
