import paho.mqtt.client as mqtt
from mqtt_client.command import InferenceLatencyBenchmarkCommand, CommandFactory, Method
import mqtt_client.export as export
from virtual_device import EdgeSensor
import json


def _handle_inference_latency_benchmark(mqtt_client, uuid, mqtt_payload):
    print(f"Received inference latency benchmark with UUID {uuid}")
    resource_value = mqtt_payload["inf-latency-bench"]
    topic, data = InferenceLatencyBenchmarkCommand(resource_value=resource_value).handle(
        device=mqtt_client.device, uuid=uuid
    )
    payload = json.dumps(data)
    print(f"Sending inference latency benchmark export to topic {topic}")
    mqtt_client.publish(topic, payload, qos=1)

def _handle_command(mqtt_client, uuid, method, resource_name, mqtt_payload):
    print(f"Received command with UUID {uuid}")
    response = CommandFactory.create_command(method, resource_name, mqtt_payload).handle(
        device=mqtt_client.device, uuid=uuid
    )
    if method == Method.GET:
        topic, payload = response.topic, json.dumps(response.payload)
        print(f"Sending GET response to topic {topic}")
        mqtt_client.publish(topic, payload, qos=1)





class MQTTClient:
    def __init__(
        self,
        device: EdgeSensor,
        clean_session=False,
        userdata=None,
        protocol=mqtt.MQTTv311,
        transport="tcp",
    ):
        self.device = device
        self.client = mqtt.Client(
            client_id=device.name,
            clean_session=clean_session,
            userdata=userdata,
            protocol=protocol,
            transport=transport
        )

        # Set the callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully")
            device_name = self.device.name
            # cmd_topic: command/<device_name>/<resource_name>/<method>/<uuid>
            self.client.subscribe(f"command/{device_name}/+/+/#", qos=1)
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        topic, payload = msg.topic, json.loads(msg.payload.decode())
        _, resource_name, method, uuid = topic.split("/")[1:]
        if resource_name == "inf-latency-bench":
            _handle_inference_latency_benchmark(self, uuid, payload)
        else:
            _handle_command(self, uuid, method, resource_name, payload)
        
    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from broker")

    def connect(self, host, port=1883, keepalive=60):
        self.client.connect(host, port, keepalive)

    def disconnect(self):
        self.client.disconnect()

    def loop_start(self):
        self.client.loop_start()
    
    def loop_stop(self):
        self.client.loop_stop()

    def publish(self, topic, payload, qos=1):
        self.client.publish(topic, payload, qos=qos)
    
    