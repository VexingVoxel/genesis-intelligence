#!/usr/bin/env python3
import zmq
import struct
import time
import socket
import threading
import ollama
import math

# Configuration
NODE1_IP = "192.168.50.29"
CONTROLLER_IP = "192.168.50.126" # Laptop
ZMQ_SUB_ADDR = f"tcp://{NODE1_IP}:5555"
ZMQ_CMD_ADDR = f"tcp://{NODE1_IP}:5556"
PRESENCE_PORT = 5558
MAGIC_BYTE = 0xDEADBEEF

# Shared State
last_world_slice = None
agent_0_pos = (0, 0)
state_lock = threading.Lock()

def presence_heartbeat():
    """Thread to send UDP presence packets independently."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            udp_socket.sendto(b"PRESENCE", (CONTROLLER_IP, PRESENCE_PORT))
        except:
            pass
        time.sleep(1)

def cognitive_loop(cmd_socket):
    """Thread to perform Ollama inference and send movement intents."""
    print("[*] Cognitive Loop Active using llama3.2:3b", flush=True)
    
    while True:
        time.sleep(5) # Inference every 5 seconds to prevent saturation
        
        with state_lock:
            if last_world_slice is None:
                continue
            
            # 1. Capture Agent 0's neighborhood
            ax, ay = int(agent_0_pos[0]), int(agent_0_pos[1])
            neighborhood = []
            for dy in range(-1, 2):
                row = []
                for dx in range(-1, 2):
                    nx, ny = (ax + dx) % 128, (ay + dy) % 128
                    # last_world_slice is 128x128 1D array of u32
                    voxel = last_world_slice[ny * 128 + nx]
                    v_id = voxel & 0xFF
                    row.append("Grass" if v_id == 2 else "Dirt")
                neighborhood.append(row)

        # 2. Query Ollama
        prompt = f"""You are an autonomous agent in a voxel world.
Your current position is ({ax}, {ay}).
Your 3x3 surroundings (rows top-to-bottom):
Row 1: {neighborhood[0]}
Row 2: {neighborhood[1]}
Row 3: {neighborhood[2]}

You are hungry. Grass is food. Dirt is empty ground.
Choose a direction to move: North, South, East, West, NorthEast, NorthWest, SouthEast, SouthWest.
Response format: JSON only. Example: {{"direction": "North", "reason": "I see grass there"}}
"""
        try:
            response = ollama.chat(model='llama3.2:3b', messages=[
                {'role': 'system', 'content': 'You are a survival-driven agent. Answer in valid JSON only.'},
                {'role': 'user', 'content': prompt},
            ], format='json')
            
            import json
            res_data = json.loads(response['message']['content'])
            direction = res_data.get('direction', 'North')
            print(f"[Cognition] Agent 0 decision: {direction} | Reason: {res_data.get('reason')}", flush=True)

            # 3. Map Direction to Radians
            dirs = {
                "North": -math.pi/2, "South": math.pi/2, "East": 0, "West": math.pi,
                "NorthEast": -math.pi/4, "NorthWest": -3*math.pi/4,
                "SouthEast": math.pi/4, "SouthWest": 3*math.pi/4
            }
            target_angle = dirs.get(direction, 0.0)
            
            # 4. Send Command: [0-7] Brain ID (0) | [8-11] Angle (f32) | [12-15] Speed (f32)
            cmd_packet = struct.pack("<Qff", 0, target_angle, 0.08)
            cmd_socket.send(cmd_packet)

        except Exception as e:
            print(f"[!] Cognition Error: {e}", flush=True)

def main():
    print(f"--- Genesis Intelligence Hub v3.5 ---", flush=True)
    
    # 0. Initialize ZMQ
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.CONFLATE, 1)
    subscriber.connect(ZMQ_SUB_ADDR)
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    command_sender = context.socket(zmq.PUSH)
    command_sender.connect(ZMQ_CMD_ADDR)

    # 1. Start Threads
    threading.Thread(target=presence_heartbeat, daemon=True).start()
    threading.Thread(target=cognitive_loop, args=(command_sender,), daemon=True).start()

    global last_world_slice, agent_0_pos
    
    try:
        while True:
            if subscriber.poll(500):
                packet = subscriber.recv()
                if len(packet) >= 48:
                    # Parse Header
                    # agent_count = struct.unpack("<H", packet[36:38])[0]
                    
                    # Extract World Slice (128x128x4 bytes starting at offset 48)
                    voxel_bytes = packet[48:48 + (128*128*4)]
                    # Cast to u32 array
                    v_slice = struct.unpack(f"<{128*128}I", voxel_bytes)
                    
                    # Extract Agent 0 Position (First 12 bytes of agent payload)
                    agent_offset = 48 + (128*128*4)
                    a0_pos = struct.unpack("<fff", packet[agent_offset:agent_offset+12])
                    
                    with state_lock:
                        last_world_slice = v_slice
                        agent_0_pos = (a0_pos[0], a0_pos[1])
            
    except KeyboardInterrupt:
        print("Stopping...", flush=True)

if __name__ == '__main__':
    main()
