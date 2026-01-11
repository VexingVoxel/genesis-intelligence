#!/usr/bin/env python3
import zmq
import struct
import time
import socket
import threading

# Configuration
NODE1_IP = "192.168.50.29"
CONTROLLER_IP = "192.168.50.126" # Laptop
ZMQ_ADDR = f"tcp://{NODE1_IP}:5555"
PRESENCE_PORT = 5558
MAGIC_BYTE = 0xDEADBEEF

def presence_heartbeat():
    """Thread to send UDP presence packets independently of ZMQ load."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[*] Heartbeat Thread: Targeting {CONTROLLER_IP}:{PRESENCE_PORT}", flush=True)
    while True:
        try:
            udp_socket.sendto(b"PRESENCE", (CONTROLLER_IP, PRESENCE_PORT))
        except Exception as e:
            print(f"[!] Heartbeat Error: {e}", flush=True)
        time.sleep(1)

def main():
    print(f"--- Genesis Intelligence Hub: HIFI Version ---", flush=True)
    
    # Start Heartbeat Thread
    hb_thread = threading.Thread(target=presence_heartbeat, daemon=True)
    hb_thread.start()

    # Initialize ZMQ
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.CONFLATE, 1)
    subscriber.connect(ZMQ_ADDR)
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    print(f"[*] ZMQ Thread: Listening to Core at {ZMQ_ADDR}", flush=True)

    try:
        while True:
            if subscriber.poll(500):
                packet = subscriber.recv()
                if len(packet) >= 40:
                    magic = struct.unpack("<I", packet[0:4])[0]
                    if magic == MAGIC_BYTE:
                        tick = struct.unpack("<Q", packet[8:16])[0]
                        if tick % 600 == 0:
                            print(f"[Intelligence] Active. World Tick: {tick}", flush=True)
            else:
                # print("[!] No data from Core...", flush=True)
                pass
    except KeyboardInterrupt:
        print("Stopping...", flush=True)

if __name__ == '__main__':
    main()