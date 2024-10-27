"""
This module captures MQTT incoming and HTTP outgoing packets on a specified Docker network interface.
It logs the elapsed time, direction (incoming/outgoing), sender, receiver, and packet size to a CSV file.
"""

import time
import pyshark
import csv

def capture_traffic(capture_duration, interface, csv_filename):
    """
    Captures specific TCP traffic on a specified network interface and logs details to a CSV file.

    Parameters:
    - capture_duration (int): Duration to capture traffic in seconds.
    - interface (str): The network interface to capture packets on.
    - csv_filename (str): The name of the CSV file to write the packet details to.
    """

    # Open the CSV file for writing
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write the header row
        writer.writerow(['elapsed_time', 'direction', 'sender', 'receiver', 'length'])

        # Define BPF filter to capture only MQTT (port 1883) and HTTP (port 8000) traffic
        bpf_filter = 'tcp port 1883 or tcp port 8000'

        # Initialize live capture with the specified BPF filter
        capture = pyshark.LiveCapture(interface=interface, bpf_filter=bpf_filter)

        # Record the start time to calculate elapsed time for each packet
        start_time = time.time()

        def packet_handler(packet):
            try:
                # Calculate elapsed time since capture started
                elapsed_time = time.time() - start_time

                # Initialize default values
                direction = 'unknown'
                src = 'N/A'
                dst = 'N/A'

                # Check if the packet has IP layer
                if hasattr(packet, 'ip'):
                    src = packet.ip.src
                    dst = packet.ip.dst

                # Determine the direction based on destination port
                if packet.transport_layer == 'TCP':
                    dst_port = int(packet[packet.transport_layer].dstport)
                    if dst_port == 1883:
                        direction = 'incoming'
                    elif dst_port == 8000:
                        direction = 'outgoing'

                # Log only if direction is determined
                if direction in ['incoming', 'outgoing']:
                    writer.writerow([elapsed_time, direction, src, dst, packet.length])

            except AttributeError as e:
                # Handle packets that might not have expected attributes
                print(f"Packet parsing error: {e}")

        # Start capturing packets and apply the packet handler
        print(f"Starting packet capture on interface {interface} for {capture_duration} seconds...")
        capture.apply_on_packets(packet_handler, timeout=capture_duration)
        print("Packet capture completed.")

        # Close the capture to free resources
        capture.close()

if __name__ == "__main__":
    # Configuration parameters
    capture_duration = 60  # Duration in seconds
    docker_bridge_interface = 'br-7306033fe585'  # Replace with your actual bridge interface
    output_csv = 'packets.csv'

    # Start the traffic capture
    capture_traffic(capture_duration, docker_bridge_interface, output_csv)
