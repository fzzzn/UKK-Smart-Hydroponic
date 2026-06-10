import time
import gc
from machine import Pin
from config import *
from wifi_manager import WiFiManager
from sensors import DHTSensor, Ultrasonic
from display import Display
from mqtt_client import MQTT
from hydroponic import Hydro

gc.collect()
gc.threshold(8000)

disp = Display(PINS[0], PINS[1], D_W, D_H, D_ADDR)
disp.loading("WiFi...")

wm = WiFiManager()
if not wm.is_configured():
    disp.loading("AP Mode")
    wm.start_captive_portal()
elif not wm.connect_saved():
    disp.loading("AP Mode")
    wm.start_captive_portal()

disp.loading("MQTT...")

btn = Pin(PINS[2], Pin.IN)
btn_last = btn.value()

dht = DHTSensor(PINS[3])
us = Ultrasonic(PINS[4], PINS[5])

hydro = Hydro(PINS[6], D_MIN, D_MAX)

def mqtt_cb(topic, msg):
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

mqtt = MQTT(MQTT_CFG, mqtt_cb)
mqtt.connect()

t_pub = 0
t_dht = 0
t_dist = 0
lc = 0

def upd():
    s = hydro.state()
    s['w'] = wm.sta.isconnected()
    s['m'] = mqtt.ok
    s['i'] = T_PUB // 1000
    disp.render(s)

print("Ready!")
disp.page = 0
upd()

while True:
    try:
        if not mqtt.ok:
            mqtt.reconnect()
        mqtt.check()

        b = btn.value()
        if b == 1 and btn_last == 0:
            disp.toggle()
            upd()
            time.sleep_ms(250)
        btn_last = b

        n = time.ticks_ms()

        if disp.notif_check(T_NOTIF):
            upd()

        if time.ticks_diff(n, t_dist) >= T_DIST:
            t_dist = n
            hydro.d = us.read()
            hydro.logic()
            upd()

        if time.ticks_diff(n, t_dht) >= T_DHT:
            t_dht = n
            hydro.t, hydro.h = dht.read()
            upd()

        if time.ticks_diff(n, t_pub) >= T_PUB:
            t_pub = n
            mqtt.pub(hydro.payload())

        lc += 1
        if lc >= 50:
            gc.collect()
            lc = 0

        time.sleep_ms(10)
    except Exception as e:
        print("Err:", e)
        gc.collect()
        time.sleep_ms(500)
