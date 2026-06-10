import dht
import time
from machine import Pin

class DHTSensor:
    def __init__(self, pin):
        self.s = dht.DHT22(Pin(pin))
        self.t = 0.0
        self.h = 0.0

    def read(self):
        try:
            self.s.measure()
            self.t = self.s.temperature()
            self.h = self.s.humidity()
        except:
            pass
        return self.t, self.h

class Ultrasonic:
    def __init__(self, trig, echo):
        self.trig = Pin(trig, Pin.OUT)
        self.echo = Pin(echo, Pin.IN)
        self.trig.value(0)
        self.d = 0.0

    def read(self):
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)
        
        t = time.ticks_us()
        while not self.echo.value():
            if time.ticks_diff(time.ticks_us(), t) > 30000:
                self.d = -1
                return self.d
        
        s = time.ticks_us()
        while self.echo.value():
            if time.ticks_diff(time.ticks_us(), s) > 30000:
                self.d = -1
                return self.d
        
        self.d = time.ticks_diff(time.ticks_us(), s) * 0.0343 / 2
        return self.d
