import zmq
import json

def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    # Connect to Node 1 (genesis-compute)
    node1_ip = "192.168.50.29"
    subscriber.connect(f"tcp://{node1_ip}:5555")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    print(f"--- Genesis Intelligence Listener Starting ---")
    print(f"Subscribed to {node1_ip}:5555")

    while True:
        try:
            message = subscriber.recv_string()
            data = json.loads(message)
            print(f"Received Heartbeat: Tick {data['tick']} from {data['node_name']} (Status: {data['status']})")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
