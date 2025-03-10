""" 
Author: Ehsan Shahri
Email: ehsan.shahri@ua.pt
Date: 2024-12-10
Version: 1.1
Description: This script evaluates the performance of Wi-Fi 7 networks in case of maximum throughput. This code runs on a client to send the maximum number of UDP packets to a server to measure the maximum throughput. 
"""



#!/usr/bin/env python3

import sys
import time
import socket

PORT = 1234

def main():
    if len(sys.argv) != 4:
        print("Usage: host_ip test_time(minutes) bytes_to_send")
        exit(0)

    host = sys.argv[1]
    delta_t = float(sys.argv[2])  # Test duration in minutes
    size_bytes = int(sys.argv[3])  # Packet size in bytes

    start = time.time()
    end = start + (delta_t * 60)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Corrected SOCK_DGRAM
    r = time.time()

    while time.time() < end:
        s.sendto(b'c' * size_bytes, (host, PORT))
        if time.time() > r + 1:
            print(f"Remaining time: {end - time.time():.2f} seconds")
            r = time.time()

    s.close()

if __name__ == "__main__":
    main()
