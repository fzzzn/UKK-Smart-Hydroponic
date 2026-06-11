# ============================================================
# CONFIGURATION FILE
# Central configuration for Smart Hydroponic System
# ============================================================

from env_loader import load_env

# Load environment variables from .env file
_env = load_env()

# Pin config: SCL, SDA, BUTTON, DHT, TRIG, ECHO, RELAY
# GPIO pins for ESP8266 (NodeMCU)
PINS = (5, 4, 2, 14, 12, 13, 16)

# MQTT: server, port, user, pass
# MQTT broker configuration for real-time control
MQTT_CFG = (
    _env.get('MQTT_HOST', '103.210.35.166'),
    int(_env.get('MQTT_PORT', '1883')),
    _env.get('MQTT_USER', 'mqtt'),
    _env.get('MQTT_PASS', 'mqtt')
)

# ThingSpeak API key
# Write API key for cloud data visualization
TS_API = _env.get('TS_API_KEY', '')

# Topics
# MQTT topics for publishing sensor data and receiving commands
T_STATUS = 'fauzan/status'   # Publish sensor readings
T_MODE = 'fauzan/mode'       # Subscribe: auto/manual mode
T_RELAY = 'fauzan/relay'     # Subscribe: pump on/off control

# Timing (ms)
# Intervals for various operations
T_PUB = 15000    # Publish interval (15s - ThingSpeak free tier minimum)
T_DHT = 2000     # DHT22 sensor reading interval
T_DIST = 1000    # Ultrasonic distance reading interval
T_NOTIF = 2000   # Notification display duration

# Thresholds (cm)
# Water level distance thresholds for pump control
D_MIN = 10.0     # Below this = water full, pump OFF
D_MAX = 20.0     # Above this = water low, pump ON (auto mode)

# Display
# OLED display configuration (SSD1306 128x64)
D_W = 128        # Display width in pixels
D_H = 64         # Display height in pixels
D_ADDR = 0x3C    # I2C address of OLED display
