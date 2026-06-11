# ============================================================
# SENSORS MODULE
# Handles DHT22 (temperature/humidity) and Ultrasonic (distance)
# ============================================================

import dht
import time
from machine import Pin


class DHTSensor:
    """DHT22 Temperature and Humidity Sensor"""
    
    def __init__(self, pin):
        # Initialize DHT22 sensor on specified GPIO pin
        self.s = dht.DHT22(Pin(pin))
        self.t = 0.0  # Temperature in Celsius
        self.h = 0.0  # Humidity in percentage

    def read(self):
        """Read temperature and humidity from sensor
        Returns: (temperature, humidity) tuple
        Returns last values if read fails
        """
        try:
            self.s.measure()
            self.t = self.s.temperature()
            self.h = self.s.humidity()
        except:
            pass  # Keep last values on error
        return self.t, self.h


class Ultrasonic:
    """HC-SR04 Ultrasonic Distance Sensor"""
    
    def __init__(self, trig, echo):
        # Initialize trigger (output) and echo (input) pins
        self.trig = Pin(trig, Pin.OUT)
        self.echo = Pin(echo, Pin.IN)
        self.trig.value(0)  # Ensure trigger is low initially
        self.d = 0.0  # Distance in centimeters

    def read(self):
        """Measure distance using ultrasonic pulse
        Returns: distance in cm, or -1 if timeout/error
        """
        # Send 10us trigger pulse
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        t = time.ticks_us()
        # Wait for echo to go HIGH (pulse start)
        while not self.echo.value():
            if time.ticks_diff(time.ticks_us(), t) > 30000:
                self.d = -1  # Timeout - no object detected
                return self.d

        s = time.ticks_us()
        # Wait for echo to go LOW (pulse end)
        while self.echo.value():
            if time.ticks_diff(time.ticks_us(), s) > 30000:
                self.d = -1  # Timeout - sensor error
                return self.d

        # Calculate distance: (pulse_time * speed_of_sound) / 2
        # Speed of sound = 343 m/s = 0.0343 cm/us
        # Divide by 2 for round-trip
        self.d = time.ticks_diff(time.ticks_us(), s) * 0.0343 / 2
        return self.d
