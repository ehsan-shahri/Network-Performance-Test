import socket
import time
import csv
import sys

# Ensure correct number of arguments
if len(sys.argv) != 5:
    print("Usage: python server_script.py <PC_WiFi_IP> <PC_Ethernet_IP> <OP5_Ethernet_IP> <PORT>")
    sys.exit(1)

# Extract network interface IPs from command line arguments
PC_WIFI_IP = sys.argv[1]   # PC's Wi-Fi IP (Receives from OP5)
PC_ETH_IP = sys.argv[2]    # PC's Ethernet IP (Sends back to OP5)
OP5_ETH_IP = sys.argv[3]   # OP5's Ethernet IP (Target for returning packets)
PORT = int(sys.argv[4])    # UDP Port

# CSV file to store received packet details
CSV_FILE = r"\home\ehsan\Desktop\scenario_01\Perf_uplink_1ms_1.csv"

def main():
    """ Server listens on Wi-Fi (PC) and sends packets back via Ethernet. """
    duration_minutes = float(input("Enter the duration of the test in minutes: "))
    duration_seconds = duration_minutes * 60  # Convert minutes to seconds
    print(f"Test will run for {duration_minutes} minutes ({duration_seconds} seconds)...")

    # Create sockets
    wifi_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # For receiving packets
    eth_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # For sending packets

    # Bind Wi-Fi socket to receive packets from OP5
    wifi_socket.bind((PC_WIFI_IP, PORT))
    #  wifi_socket.bind(("0.0.0.0", PORT))  # Listen on all interfaces
    print(f"Server listening on Wi-Fi: {PC_WIFI_IP}:{PORT}")

    # Open CSV file to log received packets
    with open(CSV_FILE, mode="w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Packet ID", "Packet Length (bytes)", "Reception Time (seconds)"])  # CSV header

        start_time = time.time()
        packet_count = 0
        total_received_bytes = 0

        try:
            while True:
                elapsed_time = time.time() - start_time
                if elapsed_time > duration_seconds:
                    print("Test duration completed.")
                    break

                # Receive packet from OP5 over Wi-Fi
                data, addr = wifi_socket.recvfrom(4096)

                packet_length = len(data)
                reception_time = time.time() - start_time  # Relative time since start

                # Extract Packet ID and original send timestamp
                if len(data) >= 12:
                    packet_id = int.from_bytes(data[-12:-8], byteorder='big')  # Extract Packet ID
                    t_send = int.from_bytes(data[-8:], byteorder='big')  # Extract send timestamp
                else:
                    packet_id = packet_count + 1  # Fallback Packet ID
                    t_send = 0  # Fallback timestamp

                # Log reception
                packet_count += 1
                total_received_bytes += packet_length
                print(f"Packet #{packet_id} received: {packet_length} bytes at {reception_time:.3f} seconds")
                

                # Write to CSV
                csv_writer.writerow([packet_id, packet_length, round(reception_time, 3)])

                # Send the same packet back to OP5 via Ethernet
                #  eth_socket.sendto(data, (OP5_ETH_IP, PORT))
                print(f"Sending packet back to OP5 via Ethernet: {OP5_ETH_IP}:{PORT}")
                eth_socket.sendto(data, (OP5_ETH_IP, PORT))


        except KeyboardInterrupt:
            print("\nTest interrupted by user.")

        finally:
            wifi_socket.close()
            eth_socket.close()
            print(f"Server stopped. Total packets received: {packet_count}, Total bytes received: {total_received_bytes}")

if __name__ == "__main__":
    main()
