# Pin config: SCL, SDA, BUTTON, DHT, TRIG, ECHO, RELAY
PINS = (5, 4, 2, 14, 12, 13, 16)

# MQTT: server, port, user, pass
MQTT_CFG = ('103.210.35.166', 1883, 'mqtt', 'mqtt')

# Topics
T_STATUS = 'fauzan/status'
T_MODE = 'fauzan/mode'
T_RELAY = 'fauzan/relay'

# Timing (ms)
T_PUB = 15000
T_DHT = 2000
T_DIST = 1000
T_NOTIF = 2000

# Thresholds (cm)
D_MIN = 10.0
D_MAX = 20.0

# Display
D_W = 128
D_H = 64
D_ADDR = 0x3C
