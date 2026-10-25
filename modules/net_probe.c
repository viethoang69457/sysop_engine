#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>

int main(int argc, char *argv[]) {
    // 1. Kiểm tra tham số đầu vào
    if (argc < 3) {
        printf("{\"error\": \"Usage: %s <IP> <PORT>\"}\n", argv[0]);
        return 1;
    }

    const char *ip = argv[1];
    int port = atoi(argv[2]);

    // 2. Khởi tạo Socket IPv4/TCP
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        printf("{\"target\": \"%s\", \"port\": %d, \"status\": \"DOWN\", \"reason\": \"Socket creation failed\"}\n", ip, port);
        return 1;
    }

    // 3. Cấu hình Timeout 2 giây cho Socket (Tránh treo hệ thống)
    struct timeval timeout;
    timeout.tv_sec = 2;
    timeout.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    struct sockaddr_in target_addr;
    memset(&target_addr, 0, sizeof(target_addr));
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(port);
    inet_pton(AF_INET, ip, &target_addr.sin_addr);

    // 4. Đo thời gian bắt đầu (Monotonic Clock)
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    // 5. Thực hiện Handshake TCP (Connect)
    if (connect(sock, (struct sockaddr *)&target_addr, sizeof(target_addr)) < 0) {
        close(sock);
        printf("{\"target\": \"%s\", \"port\": %d, \"status\": \"DOWN\"}\n", ip, port);
        return 0;
    }

    // 6. Tính toán độ trễ (Latency) theo vi giây (microseconds)
    clock_gettime(CLOCK_MONOTONIC, &end);
    close(sock);

    long latency_us = (end.tv_sec - start.tv_sec) * 1000000 + (end.tv_nsec - start.tv_nsec) / 1000;

    // 7. Xuất kết quả định dạng JSON chuẩn
    printf("{\"target\": \"%s\", \"port\": %d, \"status\": \"UP\", \"latency_us\": %ld}\n", ip, port, latency_us);
    return 0;
}
