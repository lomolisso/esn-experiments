import time
import enum
from pydantic import BaseModel
from virtual_device import EdgeSensor

MICROSECOND_CONVERSION_FACTOR = 1000000 # 1 second = 1,000,000 microseconds

class Response(BaseModel):
    topic: str
    payload: dict


class Method(str, enum.Enum):
    GET = "get"
    SET = "set"

    def __eq__(self, value: object) -> bool:
        return super().__eq__(value)


class BaseCommand(BaseModel):
    method: Method = None
    target: list[str] = []
    resource_name: str
    resource_value: object


# --- Resource: Sensor State ---


class SensorState(str, enum.Enum):
    INITIAL = "initial"
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    WORKING = "working"
    IDLE = "idle"
    ERROR = "error"


class SensorStateCommand(BaseCommand):
    allowed_methods: list[Method] = [Method.GET, Method.SET]
    resource_name: str = "sensor-state"


class SetSensorState(SensorStateCommand):
    method: Method = Method.SET
    resource_value: SensorState

    def handle(self, device: EdgeSensor, **kwargs):
        state = device.get_state()
        if self.resource_value == state:
            print(f"Sensor state is already {state}")
            return
        if self.resource_value == SensorState.INITIAL:
            device.trigger_sensor_reset_event()
            return
        if self.resource_value == SensorState.ERROR:
            device.trigger_sensor_error_event()
            return

        if self.resource_value == SensorState.LOCKED:
            if state == SensorState.UNLOCKED:
                device.trigger_settings_locked_event()
            else:
                print(f"Cannot lock settings from state {state}")
        elif self.resource_value == SensorState.UNLOCKED:
            if state == SensorState.LOCKED:
                device.trigger_settings_unlocked_event()
            else:
                print(f"Cannot unlock settings from state {state}")
        elif self.resource_value == SensorState.WORKING:
            if state == SensorState.LOCKED or state == SensorState.IDLE:
                device.trigger_sensor_started_event()
            else:
                print(f"Cannot start sensor from state {state}")
        elif self.resource_value == SensorState.IDLE:
            if state == SensorState.WORKING:
                device.trigger_sensor_stopped_event()
            else:
                print(f"Cannot stop sensor from state {state}")


class GetSensorState(SensorStateCommand):
    method: Method = Method.GET
    resource_value: SensorState = None

    def handle(self, device: EdgeSensor, uuid: str):
        topic = f"response/{device.name}/{self.resource_name}/get/{uuid}"
        return Response(topic=topic, payload={"sensor-state": device.get_state()})


# --- Resource: Inference Layer ---


class InferenceLayer(int, enum.Enum):
    CLOUD = 2
    GATEWAY = 1
    SENSOR = 0


class InferenceLayerCommand(BaseCommand):
    resource_name: str = "inference-layer"


class SetInferenceLayer(InferenceLayerCommand):
    method: Method = Method.SET
    resource_value: InferenceLayer

    def handle(self, device: EdgeSensor, **kwargs):
        print(f"Setting inference layer to {self.resource_value}")
        device.set_inference_layer(self.resource_value)


class GetInferenceLayer(InferenceLayerCommand):
    method: Method = Method.GET
    resource_value: InferenceLayer = None

    def handle(self, device: EdgeSensor, uuid: str):
        topic = f"response/{device.name}/{self.resource_name}/get/{uuid}"
        return Response(topic=topic, payload={"inference-layer": device.get_inference_layer()})


# --- Resource: Sensor Config ---


class SensorConfig(BaseModel):
    sleep_interval_ms: int


class SensorConfigCommand(BaseCommand):
    allowed_methods: list[Method] = [Method.SET]
    resource_name: str = "sensor-config"


class SetSensorConfig(SensorConfigCommand):
    method: Method = Method.SET
    resource_value: SensorConfig

    def handle(self, device: EdgeSensor, **kwargs):
        device.set_sensor_config(self.resource_value.model_dump())

class GetSensorConfig(SensorConfigCommand):
    method: Method = Method.GET
    resource_value: SensorConfig = None

    def handle(self, device: EdgeSensor, uuid: str):
        topic = f"response/{device.name}/{self.resource_name}/get/{uuid}"
        return Response(topic=topic, payload={"sensor-config": {"sleep_interval_ms": device.get_sleep_interval_ms()}})


# --- Resource: Sensor Model ---


class SensorModel(BaseModel):
    tf_model_b64: str
    tf_model_bytesize: int


class SensorModelCommand(BaseCommand):
    allowed_methods: list[Method] = [Method.SET]
    resource_name: str = "sensor-model"


class SetSensorModel(SensorModelCommand):
    method: Method = Method.SET
    resource_value: SensorModel

    def handle(self, device: EdgeSensor, **kwargs):
        device.update_model(self.resource_value.tf_model_b64, self.resource_value.tf_model_bytesize)


# --- Resource: Inference Latency Benchmark ---


class InferenceLatencyBenchmark(BaseModel):
    reading_uuid: str
    send_timestamp: int


class InferenceLatencyBenchmarkCommand(BaseCommand):
    allowed_methods: list[Method] = [Method.SET]
    method: Method = Method.SET
    resource_name: str = "inf-latency-bench"
    resource_value: InferenceLatencyBenchmark

    def handle(self, device: EdgeSensor, **kwargs):
        send_timestamp = self.resource_value.send_timestamp
        recv_timestamp = int(time.time() * MICROSECOND_CONVERSION_FACTOR)
        
        export_topic = f"export/{device.name}/inf-latency-bench"
        export_data = {
            "reading_uuid": self.resource_value.reading_uuid,
            "send_timestamp": send_timestamp,
            "recv_timestamp": recv_timestamp,
            "inference_latency": recv_timestamp - send_timestamp
        }
        return export_topic, export_data



class CommandFactory:
    @staticmethod
    def create_command(method: str, resource_name: str, mqtt_payload: dict):
        # mqtt_payload needs to be a dict with only one pair key-value
        # e.g. {resource_name: resource_value}
        
        
        if len(mqtt_payload) != 1:
            raise ValueError("Invalid payload, expected only one key-value pair")

        if method not in ["get", "set"]:
            raise ValueError(f"Invalid method, expected 'get' or 'set'. Got {method}")
        
        if resource_name not in mqtt_payload.keys():
            raise ValueError("Invalid resource name, topic and payload mismatch")

        method = Method(method)
        resource_value = mqtt_payload[resource_name]

        if method == Method.SET:
            if resource_name == "sensor-state":
                return SetSensorState(resource_value=resource_value)
            elif resource_name == "inference-layer":
                return SetInferenceLayer(resource_value=resource_value)
            elif resource_name == "sensor-config":
                return SetSensorConfig(resource_value=resource_value)
            elif resource_name == "sensor-model":
                return SetSensorModel(resource_value=resource_value)
        elif method == Method.GET:
            if resource_name == "sensor-state":
                return GetSensorState()
            elif resource_name == "inference-layer":
                return GetInferenceLayer()
            elif resource_name == "sensor-config":
                return GetSensorConfig()
