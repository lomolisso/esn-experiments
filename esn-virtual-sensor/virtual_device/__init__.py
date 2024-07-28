from inference.tf_model_manager import TFModelManager
from state_machine import StateMachine
from dataset import MeasurementHandler
from config import (
    FALLBACK_INFERENCE_LAYER,
    ADAPTIVE_INFERENCE,
    MAX_PREDICTION_HISTORY_LENGTH,
    ABNORMAL_LABELS,
    ABNORMAL_PREDICTION_THRESHOLD,
    DEVICE_BATTERY_LIFETIME_IN_CYCLES,
    LOW_BATTERY_THRESHOLD,
    SENSOR_INFERENCE_LAYER,
    GATEWAY_INFERENCE_LAYER,
)
from collections import deque
import random

import threading

# --- Config class ---
class EdgeSensorConfig:
    def __init__(self, sleep_interval_ms):
        # add a random offset of 0-50% to the sleep interval
        self.sleep_interval_ms = sleep_interval_ms + random.randint(
            0, int(sleep_interval_ms / 2)
        )

# --- Utility functions ---
def sensor_adapt_heuristic(low_battery, prediction_history):
    """
    This method computes is only called when ADAPTIVE_INFERENCE is set to True.
    """

    if low_battery:
        return GATEWAY_INFERENCE_LAYER
    else:
        if len(prediction_history) < MAX_PREDICTION_HISTORY_LENGTH:
            return SENSOR_INFERENCE_LAYER
        else:
            if sum(prediction_history) >= ABNORMAL_PREDICTION_THRESHOLD:
                return GATEWAY_INFERENCE_LAYER
            else:
                return SENSOR_INFERENCE_LAYER


class EdgeSensor:
    # thread-safe variables
    _sleeping = False
    _cycle_counter = 0
    _prediction_history = deque(maxlen=MAX_PREDICTION_HISTORY_LENGTH)
    _mh = MeasurementHandler()

    # critical section variables

    # Inference-related variables
    _inference_mutex = threading.Lock()
    _inference_layer = SENSOR_INFERENCE_LAYER
    _fallback_inference_layer = FALLBACK_INFERENCE_LAYER

    # State-related variables
    _state_mutex = threading.Lock()
    _sm = StateMachine()
    _model_manager = TFModelManager()

    # Config-related variables
    _config_mutex = threading.Lock()
    _config = EdgeSensorConfig(sleep_interval_ms=10000)

    # --- Constructor ---
    def __init__(self, name):
        self.name = name

    # --- Inference-related methods --- [MUST use the _inference_mutex]
    def update_model(self, tf_model_b64, tf_model_bytesize):
        state = self.get_state()
        if state == "unlocked" or state == "idle":
            self._model_manager.update_model(tf_model_b64, tf_model_bytesize)

    def predict(self, input_data):
        state = self.get_state()
        if state == "working":
            # perform inference
            output_label = self._model_manager.predict(input_data)

            # update prediction history
            is_abnormal = 1 if output_label in ABNORMAL_LABELS else 0
            self._prediction_history.append(is_abnormal)

            return output_label

    def _get_fallback_inference_layer(self):
        with self._inference_mutex:
            return self._fallback_inference_layer

    def _get_inference_layer(self):
        low_battery = self.is_device_low_battery()
        prediction_history = self._prediction_history

        with self._inference_mutex:
            # the heuristic is only called when the inference layer is set to SENSOR_INFERENCE_LAYER
            # as if it is set to any other value, it is assumed that the layer was already adapted
            # by the user or the heuristic of an upper network layer: gateway or cloud

            if self._inference_layer == SENSOR_INFERENCE_LAYER:
                heuristic_result = sensor_adapt_heuristic(
                    low_battery, prediction_history
                )
                if heuristic_result != SENSOR_INFERENCE_LAYER:
                    layers = ["SENSOR_INFERENCE_LAYER", "GATEWAY_INFERENCE_LAYER"]
                    self._prediction_history.clear()
                    print(f"Adapting inference layer to {layers[heuristic_result]}")
                    self._inference_layer = heuristic_result
            
            return self._inference_layer

    def get_inference_layer(self):
        if ADAPTIVE_INFERENCE:
            return self._get_inference_layer()
        else:
            return self._get_fallback_inference_layer()

    def _set_fallback_inference_layer(self, value):
        state = self.get_state()
        with self._inference_mutex:
            if state == "unlocked":
                self._fallback_inference_layer = value

    def _set_inference_layer(self, value):
        state = self.get_state()
        with self._inference_mutex:
            if state == "unlocked" or state == "working":
                layers = ["SENSOR_INFERENCE_LAYER", "GATEWAY_INFERENCE_LAYER", "CLOUD_INFERENCE_LAYER"]
                print(f"Setting inference layer to {layers[value]}")
                self._inference_layer = value

    def set_inference_layer(self, value):
        ""
        if ADAPTIVE_INFERENCE:
            self._set_inference_layer(value)
        else:
            self._set_fallback_inference_layer(value)

    # --- State-related methods --- [MUST use the _state_mutex]
    def get_state(self):
        with self._state_mutex:
            return self._sm.state

    def trigger_startup_event(self):
        with self._state_mutex:
            self._sm.startup_event()

    def trigger_settings_locked_event(self):
        with self._state_mutex:
            self._sm.settings_locked_event()

    def trigger_settings_unlocked_event(self):
        with self._state_mutex:
            self._sm.settings_unlocked_event()

    def trigger_sensor_started_event(self):
        with self._state_mutex:
            self._sm.sensor_started_event()

    def trigger_sensor_stopped_event(self):
        with self._state_mutex:
            self._sm.sensor_stopped_event()

    def trigger_sensor_error_event(self):
        with self._state_mutex:
            self._sm.sensor_error_event()

    def trigger_sensor_reset_event(self):
        with self._state_mutex:
            self._sm.sensor_reset_event()

    # --- Config-related methods [must use the _config_mutex] ---

    def get_sensor_config(self):
        with self._config_mutex:
            return self._config

    def set_sensor_config(self, value):
        state = self.get_state()
        if state == "unlocked" or state == "idle":
            with self._config_mutex:
                self._config = EdgeSensorConfig(**value)
    
    def get_sleep_interval_ms(self):
        config = self.get_sensor_config()
        return config.sleep_interval_ms


    # --- Thread Safe Methods ---
    def get_sleeping(self):
        return self._sleeping

    def set_sleeping(self, value):
        self._sleeping = value

    def get_cycle_counter(self):
        return self._cycle_counter

    def update_cycle_counter(self):
        self._cycle_counter += 1

    def is_device_low_battery(self) -> bool:
        return (DEVICE_BATTERY_LIFETIME_IN_CYCLES - self.get_cycle_counter()) < (
            DEVICE_BATTERY_LIFETIME_IN_CYCLES * LOW_BATTERY_THRESHOLD
        )

    def measure(self):
        _, measurement = self._mh.sequence()
        return measurement
