#include <arpa/inet.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#include "move_utils.h"
#define PORT 8080

int main() {

  int status, valread, client_fd;
  struct sockaddr_in serv_addr;

  if ((client_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    return -1;
  }

  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(PORT);

  if (inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr) <= 0)
    return -1;

  if (connect(client_fd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
    return -1;

  char buffer[1024] = {0};

  while (1) {
    read(client_fd, buffer, 1024 - 1);
    char* payload = strtok(buffer, ":");
    int command = atoi(buffer);
    switch (command) {
        case 100:
            int nr_steps = ;
            step(nr_steps);
            
    }

    

  }

  send(client_fd, hello, strlen(hello), 0);
  printf("sent\n");

  valread = read(client_fd, buffer, 1024 - 1);

  printf("%s\n", buffer);
}