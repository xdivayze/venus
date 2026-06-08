#include "move_utils.h"
#include "sensors.h"
#include <arpa/inet.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
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
  char msg[256] = {'\0'};

  while (1) {
    read(client_fd, buffer, 1024 - 1);
    char *payload = strtok(buffer, ":");
    int command = atoi(buffer);
    if (command == 100) {
      int nr_steps = atoi(payload);
      step(nr_steps);
      continue;
    }

    if (command == 101) {
      float angle_rad = atof(payload);
      float angle_deg = angle_rad * 180.0f / M_PI;
      rotate_angle(angle_deg);
      continue;
    }

    if (command == 200) {
      float distance_data = read_tof();
      sprintf(msg, "201:%i", (int)distance_data);
      send(client_fd, msg, strlen(msg), 0);
      continue;
    }

    if (command == 201) {
      color_to_str(msg, get_color());
      sprintf(msg, "201:%s", msg);
      send(client_fd, msg, strlen(msg), 0);
      continue;
    }
    if (command == 202) {
      float data = check_ir_v(false);
      sprintf(msg, "202:%.2f", data);
      send(client_fd, msg, strlen(msg), 0);
      continue;
    }

    if (command == 203) {
      float data = check_ir_v(true);
      sprintf(msg, "203:%.2f", data);
      send(client_fd, msg, strlen(msg), 0);
      continue;
    }

    if (command == 999) {
      break;
    }
  }
  strcpy(msg, "999:ROBOT_END");
  send(client_fd, msg, strlen(msg), 0);
}