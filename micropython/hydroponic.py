from machine import Pin

class Hydro:
    def __init__(self, pin, dmin, dmax):
        self.r = Pin(pin, Pin.OUT)
        self.r.value(1)
        self.dmin = dmin
        self.dmax = dmax
        self.auto = True
        self.on = False
        self.t = 0.0
        self.h = 0.0
        self.d = 0.0

    def set_r(self, v):
        self.on = v
        self.r.value(0 if v else 1)

    def logic(self):
        if self.d < 0:
            self.set_r(False)
        elif self.d <= self.dmin:
            self.set_r(False)
        elif self.auto and self.d >= self.dmax:
            self.set_r(True)

    def state(self):
        return {
            't': self.t if self.t == self.t else 0,
            'h': self.h if self.h == self.h else 0,
            'd': round(self.d * 10) / 10,
            'r': self.on,
            'a': self.auto,
        }

    def payload(self):
        s = self.state()
        return {
            'temperature': s['t'],
            'humidity': s['h'],
            'distance': s['d'],
            'relay_state': 'on' if s['r'] else 'off',
            'mode': 'auto' if s['a'] else 'manual',
        }
