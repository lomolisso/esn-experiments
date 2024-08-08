import os
import json
from dotenv import load_dotenv

load_dotenv(override=True)

# Define the MQTT broker details
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))

# Define the device details
DEVICE_NAME = os.getenv('DEVICE_NAME', 'ESP32_123456')

LABELS = {
    "Good": 0,
    "Acceptable": 1,
    "Unacceptable": 2,
    "Bad": 3
}

# non-adaptive inference
CLOUD_INFERENCE_LAYER = 2
GATEWAY_INFERENCE_LAYER = 1
SENSOR_INFERENCE_LAYER = 0
FALLBACK_INFERENCE_LAYER = int(os.getenv("FALLBACK_INFERENCE_LAYER", SENSOR_INFERENCE_LAYER))

# adaptive inference
ADAPTIVE_INFERENCE = bool(int(os.getenv("ADAPTIVE_INFERENCE", 0)))
DEVICE_BATTERY_LIFETIME_IN_CYCLES = int(os.getenv("DEVICE_BATTERY_LIFETIME_IN_CYCLES", 1000))
LOW_BATTERY_THRESHOLD = float(os.getenv("LOW_BATTERY_THRESHOLD", 0.3))

PREDICTION_HISTORY_LENGTH = int(os.getenv("PREDICTION_HISTORY_LENGTH", 10))
ABNORMAL_LABELS = json.loads(os.getenv("ABNORMAL_LABELS", "[2, 3]"))
ABNORMAL_PREDICTION_THRESHOLD: int = min(
    int(os.getenv("ABNORMAL_PREDICTION_THRESHOLD", 5)),
    PREDICTION_HISTORY_LENGTH,
)


# dataset consumption
PATH_TO_DATASET = "dataset/"
SEQ_LENGTH = 50
