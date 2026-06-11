# ============================================================
# MQTT CLIENT MODULE
# Handles MQTT connection for real-time control and data publishing
# ============================================================

from umqtt.simple import MQTTClient
import ujson
import time
import ubinascii


class MQTT:
    """Lightweight MQTT client wrapper for ESP8266"""
    
    def __init__(self, cfg, cb):
        """Initialize MQTT client
        cfg: (server, port, user, pass) tuple
        cb: callback function for received messages
        """
        self.cfg = cfg
        self.cb = cb
        self.c = None      # MQTTClient instance
        self.ok = False    # Connection status
        self.lr = 0        # Last reconnect attempt time
        self.lp = 0        # Last ping time

    def connect(self):
        """Connect to MQTT broker and subscribe to control topics
        Returns: True on success, False on failure
        """
        try:
            # Generate unique client ID from server name
            cid = 'H-' + ubinascii.hexlify(self.cfg[0].encode())[:6].decode()
            self.c = MQTTClient(
                cid, self.cfg[0], self.cfg[1], self.cfg[2], self.cfg[3], keepalive=60)
            self.c.set_callback(self._msg)
            self.c.connect()
            # Subscribe to control topics
            self.c.subscribe('fauzan/mode')    # auto/manual mode
            self.c.subscribe('fauzan/relay')   # pump on/off
            self.ok = True
            self.lp = time.ticks_ms()
            return True
        except Exception as e:
            print("MQTT err:", e)
            self.ok = False
            return False

    def _msg(self, t, m):
        """Internal callback - decode and forward to user callback"""
        self.cb(t.decode(), m.decode().lower())

    def check(self):
        """Check for incoming messages and send keepalive ping
        Call this frequently in main loop
        """
        if not self.ok:
            return
        try:
            self.c.check_msg()  # Process incoming messages
            n = time.ticks_ms()
            # Send ping every 30 seconds to keep connection alive
            if time.ticks_diff(n, self.lp) > 30000:
                self.c.ping()
                self.lp = n
        except:
            self.ok = False

    def reconnect(self):
        """Attempt to reconnect to MQTT broker
        Rate limited to once per 5 seconds
        Returns: True on success, False on failure
        """
        n = time.ticks_ms()
        # Rate limit reconnection attempts
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
        """Publish sensor data to status topic
        data: dictionary to be JSON encoded
        """
        if not self.ok:
            return
        try:
            self.c.publish('fauzan/status', ujson.dumps(data))
        except:
            self.ok = False
