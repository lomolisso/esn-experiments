import time
import json
from virtual_device import EdgeSensor
from mqtt_client import MQTTClient
from mqtt_client.export import SensorDataExport, InferenceDescriptor, SensorReading
from config import MQTT_BROKER_HOST, MQTT_BROKER_PORT, DEVICE_NAME, SENSOR_INFERENCE_LAYER

SLEEP_INTERVAL_MS = 30000 # 30 seconds
MICROSECOND_CONVERSION_FACTOR = 1000000 # 1 second = 1,000,000 microseconds

def device_predict(device, measurement):
    send_timestamp = int(time.time() * MICROSECOND_CONVERSION_FACTOR)
    prediction = device.predict(measurement)
    recv_timestamp = int(time.time() * MICROSECOND_CONVERSION_FACTOR)
    return InferenceDescriptor(
        inference_layer=SENSOR_INFERENCE_LAYER,
        send_timestamp=send_timestamp,
        recv_timestamp=recv_timestamp,
        prediction=prediction
    )

def device_mqtt_payload(device, measurement, inference_descriptor):
    sensor_reading = SensorReading(
        values=measurement
    )
    sensor_data_export = SensorDataExport(
        low_battery=device.is_device_low_battery(),
        sensor_reading=sensor_reading,
        inference_descriptor=inference_descriptor
    )
    return json.dumps(sensor_data_export.model_dump())


def device_deep_sleep(mqtt_client):
    device: EdgeSensor = mqtt_client.device
    device.set_sleeping(True)
    mqtt_client.loop_stop()  # Stop the network loop
    mqtt_client.disconnect()  # Disconnect from the broker
    sleep_time = device.get_sleep_interval_ms()
    print(f"Entering deep sleep... [{sleep_time} ms]")
    print(f"Cycle {device.get_cycle_counter()} completed.")
    
    time.sleep(sleep_time / 1000)  # Simulate deep sleep duration
    device.set_sleeping(False)
    print("Waking up from deep sleep...")
    device.update_cycle_counter()
    print(f"Starting cycle {device.get_cycle_counter()}...")
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)  # Reconnect to the broker
    mqtt_client.loop_start()  # Start the network loop


if __name__ == "__main__":
    device = EdgeSensor(DEVICE_NAME)
    mqtt_client = MQTTClient(device=device)
    mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    mqtt_client.loop_start()

    try:
        while True:
            # wait for mqtt_client to connect
            while not mqtt_client.client.is_connected():
                time.sleep(1)
            
            match device.get_state():
                case "initial":
                    device.trigger_startup_event()
                case "error":
                    device.trigger_sensor_reset_event()
                case "working":
                    inference_descriptor = None
                    measurement = device.measure()
                    
                    inference_layer = device.get_inference_layer()
                    if inference_layer == SENSOR_INFERENCE_LAYER:
                        inference_descriptor = device_predict(device, measurement)
                    else:
                        inference_descriptor = InferenceDescriptor(
                            inference_layer=inference_layer,
                            send_timestamp=int(time.time() * MICROSECOND_CONVERSION_FACTOR),
                        )
                    
                    topic = f"export/{DEVICE_NAME}/sensor-data"
                    payload = device_mqtt_payload(device, measurement, inference_descriptor)
                    print("Publishing sensor data to broker...")
                    mqtt_client.publish(topic, payload, qos=0)
                    
                case _:
                    print(f"Device is in state {device.get_state()}. Skipping...")
            
            device_deep_sleep(mqtt_client)

    except KeyboardInterrupt:
        print("Exiting simulation...")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

