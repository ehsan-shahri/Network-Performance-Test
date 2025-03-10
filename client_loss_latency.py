""" 
Author: Ehsan Shahri
Email: ehsan.shahri@ua.pt
Date: 2024-11-05
Version: 2.0
Description: This script evaluates the performance of Wi-Fi 7 networks in case of packet loss and latency. This code runs on a client to send the maximum number of UDP packets to a server to measure the metrics. 
"""



import time
import socket
import sys
import threading
import csv
import os

# Output CSV files
OUTPUT_CSV_FILE = os.path.expanduser("path to loss csv file/client_loss.csv")
LATENCY_CSV_FILE = os.path.expanduser("path to latency csv file/client_latency.csv")

if len(sys.argv) != 7:
    print("Usage: <PC_WiFi_IP> <OP5_WiFi_IP> <PC_Ethernet_IP> <OP5_Ethernet_IP> <packet_length> <port>")
    sys.exit(1)

# Extracting parameters
PC_WIFI_IP = sys.argv[1]       # PC Wi-Fi IP (Server)
OP5_WIFI_IP = sys.argv[2]      # OP5 Wi-Fi IP (Client)
PC_ETH_IP = sys.argv[3]        # PC Ethernet IP (Server)
OP5_ETH_IP = sys.argv[4]       # OP5 Ethernet IP (Client)
PACKET_LENGTH = int(sys.argv[5])  # Packet Size
PORT = int(sys.argv[6])        # UDP Port

r = True  # Control receiver thread

# Tracking variables
received_ids = set()  # Tracks received packets
latency_data = []  # Stores Packet ID and Latency values
total_sent = 0  # Count packets sent

def receiver(s):
    """ Function to receive packets on Ethernet (PC → OP5) and calculate latency. """
    global r, latency_data
    while r:
        try:
            data, address = s.recvfrom(4096)  # Receive packet
            t_recv = int(time.time() * 1000000)  # Capture time in microseconds

            # Ensure the packet comes from the correct Ethernet IP (PC → OP5)
            if address[0] != PC_ETH_IP:
                continue  # Ignore packets from other sources

            # Extract Packet ID and original send timestamp
            packet_id = int.from_bytes(data[-12:-8], byteorder='big')
            t_send = int.from_bytes(data[-8:], byteorder='big')

            # Compute latency (Wi-Fi → PC → Back via Ethernet)
            latency = (t_recv - t_send) / 1000.0  # Convert microseconds to milliseconds
            latency_data.append([packet_id, latency])  # Store latency

            received_ids.add(packet_id)  # Mark packet as received

            print(f"Packet ID: {packet_id}, Latency: {latency:.3f} ms")
        except Exception as e:
            print("Error:", e)

def main():
    """ Main function to send packets via Wi-Fi and receive them via Ethernet. """
    global r, total_sent

    timesleep = 0.001  # Time between sending packets (adjustable)
    padding_length = PACKET_LENGTH - 12
    padd = b"\x00" * padding_length

    # Wi-Fi socket (OP5 → PC)
    wifi_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    wifi_socket.bind((OP5_WIFI_IP, PORT))  # Bind to OP5 Wi-Fi IP
    wifi_socket.settimeout(timesleep + 2)

    # Ethernet socket (PC → OP5)
    eth_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"OP5 listening for packets on Ethernet: {OP5_ETH_IP}:{PORT}")
    eth_socket.bind((OP5_ETH_IP, PORT))  # Bind to OP5 Ethernet IP
    eth_socket.settimeout(timesleep + 2)

    # Start the receiver thread on OP5's Ethernet interface
    x = threading.Thread(target=receiver, args=(eth_socket,))
    x.start()

    i = 0  # Packet counter
    start = time.time()
    end = start + 60  # Test duration (60 seconds)

    while time.time() < end:
        timestamp_ms = int(time.time() * 1000000)  # Current time in microseconds
        data = timestamp_ms.to_bytes(8, byteorder='big')  # Convert timestamp
        d = i.to_bytes(4, byteorder='big')  # Packet ID as bytes
        data = padd + d + data  # Construct packet

        # Send packet from OP5 (Wi-Fi) to PC
        wifi_socket.sendto(data, (PC_WIFI_IP, PORT))

        time.sleep(timesleep)  # Wait before next transmission

        i += 1  # Increment counter

    r = False  # Stop receiver thread
    x.join()

    total_sent = i  # Store total number of packets sent
    total_received = len(received_ids)  # Count packets successfully received

    # Print total packets sent
    print(f"\nTotal Packets Sent from OP5: {total_sent}")

    # Calculate packet loss
    packet_loss = ((total_sent - total_received) / total_sent) * 100 if total_sent > 0 else 0.0

    # Save packet loss results
    with open(OUTPUT_CSV_FILE, mode="w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Total Packets Sent", "Total Packets Received", "Packet Loss (%)"])
        csv_writer.writerow([total_sent, total_received, f"{packet_loss:.2f}%"])

    # Save latency results
    with open(LATENCY_CSV_FILE, mode="w", newline="") as latency_csv:
        latency_writer = csv.writer(latency_csv)
        latency_writer.writerow(["Packet ID", "Latency (ms)"])
        latency_writer.writerows(latency_data)

    # Print final results
    print("\nPacket Loss Summary")
    print("===================")
    print(f"Total Packets Sent: {total_sent}")
    print(f"Total Packets Received: {total_received}")
    print(f"Packet Loss Percentage: {packet_loss:.2f}%")

    # Close sockets
    wifi_socket.close()
    eth_socket.close()

if __name__ == "__main__":
    main()
