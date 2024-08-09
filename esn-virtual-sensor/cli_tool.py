import sys
import os
import random
import json
import subprocess
import signal
import time

def generate_device_names(n):
    # case 1: devices.json exists
    if os.path.exists("devices.json"):
        with open("devices.json", "r") as f:
            device_names = json.load(f)
            if len(device_names) >= n:
                return device_names[:n]

    # case 2: devices.json does not exist or does not contain enough device names
    device_names = []
    while len(device_names) < n:
        candidate = "ESP32_" + ''.join(random.choices("0123456789ABCDEF", k=6))
        if candidate not in device_names:
            device_names.append(candidate)
    assert len(device_names) == n
    with open("devices.json", "w") as f:
        json.dump(device_names, f)
    return device_names

def signal_handler(signal, frame):
    print("\nCtrl+C detected, terminating subprocesses...")
    for proc in processes:
        proc.send_signal(signal)
    print("All subprocesses terminated.")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 cli_tool.py <n>")
        sys.exit(1)

    try:
        n = int(sys.argv[1])
    except ValueError:
        print("Please provide a valid integer for the number of subprocesses.")
        sys.exit(1)

    if n <= 0:
        print("The number of subprocesses must be greater than 0.")
        sys.exit(1)

    device_names = generate_device_names(n)
    processes = []

    signal.signal(signal.SIGINT, signal_handler)

    try:
        for device_name in device_names:
            proc = subprocess.Popen([sys.executable, "main.py", device_name])
            processes.append(proc)
        for proc in processes:
            proc.wait()
    except Exception as e:
        print(f"An error occurred: {e}")
        signal_handler(signal.SIGINT, None)
