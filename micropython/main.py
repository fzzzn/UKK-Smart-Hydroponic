# ============================================================
# SMART HYDROPONIC SYSTEM - MAIN APPLICATION
# Entry point for ESP8266 MicroPython firmware
# ============================================================
# Features:
# - WiFi connection with captive portal setup
# - NTP time synchronization
# - MQTT for real-time control (mode/pump)
# - ThingSpeak for cloud data visualization
# - OLED display with 3 pages (Status/Network/Clock)
# - Automatic pump control based on water level
# ============================================================

import time
import gc
import ntptime  # NTP client for time synchronization
from machine import Pin
from config import *
from wifi_manager import WiFiManager
from sensors import DHTSensor, Ultrasonic
from display import Display
from mqtt_client import MQTT
from hydroponic import Hydro
from thingspeak import ThingSpeak

# Optimize memory management for ESP8266
gc.collect()
gc.threshold(8000)  # Trigger GC when free memory drops below 8KB

# ============================================================
# INITIALIZATION SEQUENCE
# ============================================================

# Initialize OLED display
disp = Display(PINS[0], PINS[1], D_W, D_H, D_ADDR)
disp.loading("WiFi...")

# Connect to WiFi (or start captive portal if not configured)
wm = WiFiManager()
if not wm.is_configured():
    disp.loading("AP Mode")
    wm.start_captive_portal()
elif not wm.connect_saved():
    disp.loading("AP Mode")
    wm.start_captive_portal()

# Sync time from NTP server (UTC)
disp.loading("NTP...")
try:
    ntptime.settime()  # Sync time from NTP server (UTC)
except:
    pass  # Continue even if NTP fails

# Initialize MQTT connection
disp.loading("MQTT...")

# ============================================================
# HARDWARE INITIALIZATION
# ============================================================

# Button for page toggle
btn = Pin(PINS[2], Pin.IN)
btn_last = btn.value()

# Sensors
dht = DHTSensor(PINS[3])      # DHT22 temperature/humidity
us = Ultrasonic(PINS[4], PINS[5])  # HC-SR04 ultrasonic distance

# Hydroponic controller (relay + auto logic)
hydro = Hydro(PINS[6], D_MIN, D_MAX)

# ============================================================
# MQTT CALLBACK
# ============================================================

def mqtt_cb(topic, msg):
    """Handle incoming MQTT messages for remote control
    - fauzan/mode: 'auto' or 'manual'
    - fauzan/relay: 'on' or 'off' (manual mode only)
    """
    if topic == T_MODE:
        old = hydro.auto
        hydro.auto = msg == 'auto'
        if old != hydro.auto:
            disp.notif_show("MODE CHANGED", "TO AUTO" if hydro.auto else "TO MANUAL")
    elif topic == T_RELAY and not hydro.auto:
        if msg == 'on':
            hydro.set_r(True)
        elif msg == 'off':
            hydro.set_r(False)
    hydro.logic()
    upd()

# Initialize MQTT client and connect
mqtt = MQTT(MQTT_CFG, mqtt_cb)
mqtt.connect()

# Initialize ThingSpeak client for cloud visualization
ts = ThingSpeak(TS_API)

# ============================================================
# MAIN LOOP VARIABLES
# ============================================================

t_pub = 0    # Last publish time
t_dht = 0    # Last DHT read time
t_dist = 0   # Last distance read time
lc = 0       # Loop counter for periodic GC

def upd():
    """Update display with current state"""
    s = hydro.state()
    s['w'] = wm.sta.isconnected()  # WiFi status
    s['m'] = mqtt.ok               # MQTT status
    s['ts'] = ts.ok                # ThingSpeak status
    s['i'] = T_PUB // 1000         # Publish interval
    disp.render(s)

print("Ready!")
disp.page = 0
upd()

# ============================================================
# MAIN LOOP
# ============================================================

while True:
    try:
        # Reconnect MQTT if disconnected
        if not mqtt.ok:
            mqtt.reconnect()
        mqtt.check()  # Process incoming messages

        # Button press - toggle display page
        b = btn.value()
        if b == 1 and btn_last == 0:
            disp.toggle()
            upd()
            time.sleep_ms(250)  # Debounce
        btn_last = b

        n = time.ticks_ms()

        # Hide notification after timeout
        if disp.notif_check(T_NOTIF):
            upd()

        # Read ultrasonic distance sensor
        if time.ticks_diff(n, t_dist) >= T_DIST:
            t_dist = n
            hydro.d = us.read()
            hydro.logic()  # Update pump based on water level
            upd()

        # Read DHT22 temperature/humidity sensor
        if time.ticks_diff(n, t_dht) >= T_DHT:
            t_dht = n
            hydro.t, hydro.h = dht.read()
            upd()

        # Publish data to MQTT and ThingSpeak
        if time.ticks_diff(n, t_pub) >= T_PUB:
            t_pub = n
            payload = hydro.payload()
            mqtt.pub(payload)
            # Send to ThingSpeak for cloud visualization
            ts.send(
                payload['temperature'],
                payload['humidity'],
                payload['distance'],
                1 if payload['relay_state'] == 'on' else 0,
                1 if payload['mode'] == 'manual' else 0
            )

        # Periodic garbage collection to prevent memory fragmentation
        lc += 1
        if lc >= 50:
            gc.collect()
            lc = 0

        time.sleep_ms(10)  # Small delay to prevent watchdog issues
    except Exception as e:
        print("Err:", e)
        gc.collect()
        time.sleep_ms(500)
