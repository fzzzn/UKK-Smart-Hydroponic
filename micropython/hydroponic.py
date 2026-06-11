# ============================================================
# HYDROPONIC CONTROLLER MODULE
# Core logic for pump control based on water level
# ============================================================

from machine import Pin


class Hydro:
    """Hydroponic system controller - manages pump based on water level"""
    
    def __init__(self, pin, dmin, dmax):
        """Initialize hydroponic controller
        pin: GPIO pin for relay control
        dmin: distance threshold for water full (cm)
        dmax: distance threshold for water low (cm)
        """
        self.r = Pin(pin, Pin.OUT)
        self.r.value(1)      # Relay OFF (active LOW)
        self.dmin = dmin     # Water full threshold
        self.dmax = dmax     # Water low threshold
        self.auto = True     # Auto mode enabled by default
        self.on = False      # Pump state
        self.t = 0.0         # Temperature
        self.h = 0.0         # Humidity
        self.d = 0.0         # Distance (water level)

    def set_r(self, v):
        """Set relay/pump state
        v: True = pump ON, False = pump OFF
        Note: Relay is active LOW, so logic is inverted
        """
        self.on = v
        self.r.value(0 if v else 1)  # Invert for active LOW relay

    def logic(self):
        """Automatic pump control logic based on water level
        - Distance < 0: sensor error, pump OFF (safety)
        - Distance <= dmin: water full, pump OFF
        - Distance >= dmax: water low, pump ON (auto mode only)
        """
        if self.d < 0:
            self.set_r(False)  # Safety: turn off on sensor error
        elif self.d <= self.dmin:
            self.set_r(False)  # Water full
        elif self.auto and self.d >= self.dmax:
            self.set_r(True)   # Water low - refill

    def state(self):
        """Get current system state for display
        Returns dictionary with sensor readings and pump state
        """
        return {
            't': self.t if self.t == self.t else 0,  # Handle NaN
            'h': self.h if self.h == self.h else 0,  # Handle NaN
            'd': round(self.d * 10) / 10,  # Round to 1 decimal
            'r': self.on,    # Pump state
            'a': self.auto,  # Auto mode state
        }

    def payload(self):
        """Get data payload for MQTT/ThingSpeak publishing
        Returns dictionary with human-readable values
        """
        s = self.state()
        return {
            'temperature': s['t'],
            'humidity': s['h'],
            'distance': s['d'],
            'relay_state': 'on' if s['r'] else 'off',
            'mode': 'auto' if s['a'] else 'manual',
        }
