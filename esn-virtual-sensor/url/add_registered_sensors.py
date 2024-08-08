"""
This module reads gateway_model.tflite and POST it to 
http://localhost:8000/api/v1/sensor/command/set/sensor-model

like this

curl -X 'POST' \
  'http://localhost:8000/api/v1/gateway/command/add/registered-sensors?gateway_name=gateway_1' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "device_name": "ESP32_9543CB",
    "device_address": "1"
  },
  {
    "device_name": "ESP32_2CED4A",
    "device_address": "2"
  },
  {
    "device_name": "ESP32_5798DA",
    "device_address": "3"
  },
  {
    "device_name": "ESP32_E3CC76",
    "device_address": "4"
  },
  {
    "device_name": "ESP32_93D33D",
    "device_address": "5"
  }
]'

the device names come from devices.json where they are stored in an array.
the device_address can be a random number.
"""
import requests
import os
import json
import random

def add_registered_sensors():
    # Load the device names from devices.json
    with open('../devices.json', 'r') as f:
        devices = json.load(f)
        device_names = devices

    # Prepare the request
    url = 'http://localhost:8000/api/v1/gateway/command/add/registered-sensors'
    params = {'gateway_name': 'gateway_1'}
    data = []
    for i in range(len(device_names)):
        data.append({"device_name": device_names[i], "device_address": str(i)})

    # Send the request
    response = requests.post(url, params=params, json=data)

    # Check the response
    if response.status_code == 200:
        print("Sensors added successfully")
    else:
        print(response.text)
        print("Failed to add sensors")

if __name__ == '__main__':
    add_registered_sensors()