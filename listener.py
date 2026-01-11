import zmq
import struct
import time
import socket

# Configuration
NODE1_IP = "192.168.50.29"
CONTROLLER_IP = "192.168.50.126" # Laptop
ZMQ_ADDR = f"tcp://{NODE1_IP}:5555"
PRESENCE_PORT = 5558
MAGIC_BYTE = 0xDEADBEEF

def main():
    # 0. Initialize ZMQ
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.CONFLATE, 1)
    subscriber.connect(ZMQ_ADDR)
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    # 1. Initialize UDP Heartbeat
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"--- Genesis Intelligence Hub: Active ---")
    print(f"Listening to Core at {ZMQ_ADDR}")
    print(f"Sending Presence to {CONTROLLER_IP}:{PRESENCE_PORT}")

    try:
        while True:
            # A. Send Presence Heartbeat
            udp_socket.sendto(b"PRESENCE", (CONTROLLER_IP, PRESENCE_PORT))

            # B. Receive Binary World State
            if subscriber.poll(100):
                packet = subscriber.recv()
                
                # Basic Binary Validation
                if len(packet) >= 40:
                    magic = struct.unpack("<I", packet[0:4])[0]
                    if magic == MAGIC_BYTE:
                        tick = struct.unpack("<Q", packet[8:16])[0]
                        if tick % 60 == 0:
                            print(f"[Intelligence] Synchronized at Tick {tick}")
            
            time.sleep(1) # Presence every second

    except KeyboardInterrupt:
        print("Stopping Intelligence Hub...")
    finally:
        udp_socket.close()

if __name__ == '__main__':
    main()
