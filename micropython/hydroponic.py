from machine import Pin

class HydroponicSystem:
    def __init__(self, config):
        self.config = config
        self.relay_pin = Pin(config['relay_pin'], Pin.OUT)
        self.relay_pin.value(1)

        self.is_auto_mode = True
        self.relay_state = False
        self.temperature = 0.0
        self.humidity = 0.0
        self.distance = 0.0

    def set_relay(self, state):
        self.relay_state = state
        self.relay_pin.value(0 if state else 1)

    def set_mode(self, mode):
        if mode == 'auto':
            self.is_auto_mode = True
        elif mode == 'manual':
            self.is_auto_mode = False

    def update_sensors(self, temp, hum, dist):
        self.temperature = temp
        self.humidity = hum
        self.distance = dist

    def run_logic(self):
        old_relay = self.relay_state
        changed = False

        if self.distance > 0 and self.distance <= self.config['thresholds']['distance_min']:
            self.set_relay(False)
        elif self.is_auto_mode:
            if self.distance >= self.config['thresholds']['distance_max']:
                self.set_relay(True)

        if old_relay != self.relay_state:
            changed = True

        return changed

    def get_state(self):
        return {
            'temp': self.temperature if not self._isnan(self.temperature) else 0,
            'hum': self.humidity if not self._isnan(self.humidity) else 0,
            'dist': round(self.distance * 10) / 10,
            'relay': self.relay_state,
            'is_auto': self.is_auto_mode,
        }

    def get_mqtt_payload(self):
        state = self.get_state()
        return {
            'temperature': state['temp'],
            'humidity': state['hum'],
            'distance': state['dist'],
            'relay_state': 'on' if state['relay'] else 'off',
            'mode': 'auto' if state['is_auto'] else 'manual',
        }

    def _isnan(self, val):
        return val != val
