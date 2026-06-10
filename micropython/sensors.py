import dht
import time
from machine import Pin

class DHTSensor:
    def __init__(self, pin):
        self.sensor = dht.DHT22(Pin(pin))
        self.temperature = 0.0
        self.humidity = 0.0

    def read(self):
        try:
            self.sensor.measure()
            self.temperature = self.sensor.temperature()
            self.humidity = self.sensor.humidity()
        except OSError as e:
            print("DHT read error:", e)
        return self.temperature, self.humidity

class UltrasonicSensor:
    def __init__(self, trig_pin, echo_pin):
        self.trig = Pin(trig_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.trig.value(0)
        self.distance = 0.0

    def read(self):
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        pulse_time = self._pulse_in(30000)

        if pulse_time == 0:
            self.distance = -1
        else:
            self.distance = pulse_time * 0.0343 / 2

        return self.distance

    def _pulse_in(self, timeout_us):
        start = time.ticks_us()

        while self.echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), start) > timeout_us:
                return 0

        pulse_start = time.ticks_us()

        while self.echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), pulse_start) > timeout_us:
                return 0

        return time.ticks_diff(time.ticks_us(), pulse_start)
