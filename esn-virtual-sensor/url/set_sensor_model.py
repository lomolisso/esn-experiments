"""
This module reads gateway_model.tflite and POST it to 
http://localhost:8000/api/v1/sensor/command/set/sensor-model

like this

curl -X 'POST' \
  'http://localhost:8000/api/v1/sensor/command/set/sensor-model?gateway_name=gateway_1' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'device_names=ESP32_9543CB,ESP32_2CED4A,ESP32_5798DA,ESP32_E3CC76,ESP32_93D33D' \
  -F 'tf_model_file=@gateway_model.tflite'

the device names come from devices.json where they are stored in an array
"""

import requests
import os
import json

def send_model():
    # Load the device names from devices.json
    with open('../devices.json', 'r') as f:
        devices = json.load(f)

    # Load the TFLite model
    model_file = '../gateway_model.tflite'
    tf_model = open(model_file, 'rb')

    # Prepare the request
    url = 'http://localhost:8000/api/v1/sensor/command/set/sensor-model'
    params = {'gateway_name': 'gateway_1'}
    files = {'tf_model_file': (model_file, tf_model)}
    data = {'device_names': devices}

    # Send the request
    response = requests.post(url, params=params, files=files, data=data)

    # Check the response
    if response.status_code == 200:
        print("Model sent successfully")
    else:
        print(response.text)
        print("Failed to send model")

if __name__ == '__main__':
    send_model()