from transitions import Machine


# Define the states
states = ['initial', 'unlocked', 'locked', 'working', 'idle', 'error']

# Define the transitions with callbacks
transitions = [
    {'trigger': 'startup_event', 'source': 'initial', 'dest': 'unlocked', 'before': 'on_startup_event'},
    {'trigger': 'settings_locked_event', 'source': 'unlocked', 'dest': 'locked', 'before': 'on_lock_settings_event'},
    {'trigger': 'settings_unlocked_event', 'source': 'locked', 'dest': 'unlocked', 'before': 'on_unlock_settings_event'},
    {'trigger': 'sensor_started_event', 'source': 'locked', 'dest': 'working', 'before': 'on_start_sensor_event'},
    {'trigger': 'sensor_stopped_event', 'source': 'working', 'dest': 'idle', 'before': 'on_stop_sensor_event'},
    {'trigger': 'sensor_error_event', 'source': '*', 'dest': 'error', 'before': 'on_error_sensor_event'},
    {'trigger': 'sensor_reset_event', 'source': '*', 'dest': 'initial', 'before': 'on_reset_sensor_event'}
]

# Define a class to hold the state machine
class StateMachine(object):
    def __init__(self):
        self.machine = Machine(model=self, states=states, transitions=transitions, initial='initial')

    def on_startup_event(self):
        assert self.state == 'initial'
        print(f"Startup event triggered: {self.state} -> unlocked")

    def on_lock_settings_event(self):
        assert self.state == 'unlocked'
        print(f"Settings locked event triggered: {self.state} -> locked")
    
    def on_unlock_settings_event(self):
        assert self.state == 'locked'
        print(f"Settings unlocked event triggered: {self.state} -> unlocked")
    
    def on_start_sensor_event(self):
        assert self.state == 'locked'
        print(f"Sensor started event triggered: {self.state} -> working")
    
    def on_stop_sensor_event(self):
        assert self.state == 'working'
        print(f"Sensor stopped event triggered: {self.state} -> idle")
    
    def on_error_sensor_event(self):
        print(f"Sensor error event triggered: {self.state} -> error")

    def on_reset_sensor_event(self):
        print(f"Sensor reset event triggered: {self.state} -> initial")
        

