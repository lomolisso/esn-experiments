from pydantic import BaseModel
from typing import Optional

# --- Export Payloads ---
class SensorReading(BaseModel):
    uuid: Optional[str] = None
    values: list[list[float]]

class InferenceDescriptor(BaseModel):
    inference_layer: int # 0: cloud, 1: gateway, 2: sensor
    send_timestamp: int
    recv_timestamp: Optional[int] = None
    prediction: Optional[int] = None

class SensorDataExport(BaseModel):
    low_battery: bool
    sensor_reading: SensorReading
    inference_descriptor: InferenceDescriptor

class InferenceLatencyBenchmarkExport(BaseModel):
    reading_uuid: str
    send_timestamp: int
    recv_timestamp: int
    inference_latency: int
