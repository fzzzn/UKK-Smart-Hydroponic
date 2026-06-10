from umqtt.simple import MQTTClient
import ujson
import time
import ubinascii

class MQTT:
    def __init__(self, cfg, cb):
        self.cfg = cfg
        self.cb = cb
        self.c = None
        self.ok = False
        self.lr = 0
        self.lp = 0

    def connect(self):
        try:
            cid = 'H-' + ubinascii.hexlify(self.cfg[0].encode())[:6].decode()
            self.c = MQTTClient(cid, self.cfg[0], self.cfg[1], self.cfg[2], self.cfg[3], keepalive=60)
            self.c.set_callback(self._msg)
            self.c.connect()
            self.c.subscribe('fauzan/mode')
            self.c.subscribe('fauzan/relay')
            self.ok = True
            self.lp = time.ticks_ms()
            return True
        except Exception as e:
            print("MQTT err:", e)
            self.ok = False
            return False

    def _msg(self, t, m):
        self.cb(t.decode(), m.decode().lower())

    def check(self):
        if not self.ok:
            return
        try:
            self.c.check_msg()
            n = time.ticks_ms()
            if time.ticks_diff(n, self.lp) > 30000:
                self.c.ping()
                self.lp = n
        except:
            self.ok = False

    def reconnect(self):
        n = time.ticks_ms()
        if time.ticks_diff(n, self.lr) < 5000:
            return False
        self.lr = n
        try:
            if self.c:
                self.c.disconnect()
        except:
            pass
        self.c = None
        self.ok = False
        return self.connect()

    def pub(self, data):
        if not self.ok:
            return
        try:
            self.c.publish('fauzan/status', ujson.dumps(data))
        except:
            self.ok = False
