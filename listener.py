import zmq
import json
import time

def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    node1_ip = "192.168.50.29"
    print(f"Connecting to {node1_ip}:5555...")
    subscriber.connect(f"tcp://{node1_ip}:5555")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    # Wait a second for the connection to stabilize
    time.sleep(1)

    print(f"--- Genesis Intelligence Listener Active ---")

    count = 0
    while count < 10:
        try:
            # Add a timeout to recv so we can see if it's just waiting
            if subscriber.poll(5000): # 5 second timeout
                message = subscriber.recv_string()
                data = json.loads(message)
                print(f"[{count}] Received: Tick {data['tick']} from {data['node_name']}")
                count += 1
            else:
                print("No message received in 5 seconds...")
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == '__main__':
    main()