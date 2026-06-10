import time
from machine import Pin
from config import PIN_CONFIG, MQTT_CONFIG, TIMING, THRESHOLDS, DISPLAY_CONFIG
from wifi_manager import WiFiManager
from sensors import DHTSensor, UltrasonicSensor
from display import Display
from mqtt_client import MQTTClientWrapper
from hydroponic import HydroponicSystem

wifi_manager = WiFiManager()

if not wifi_manager.is_configured():
    print("No WiFi config found, starting captive portal...")
    wifi_manager.start_captive_portal()
else:
    print("Connecting to saved WiFi...")
    if not wifi_manager.connect_saved():
        print("Failed to connect, starting captive portal...")
        wifi_manager.start_captive_portal()

button = Pin(PIN_CONFIG['BUTTON'], Pin.IN)
last_button_state = 0

dht_sensor = DHTSensor(PIN_CONFIG['DHT'])
ultrasonic = UltrasonicSensor(PIN_CONFIG['TRIG'], PIN_CONFIG['ECHO'])

display = Display(
    PIN_CONFIG['OLED_SCL'],
    PIN_CONFIG['OLED_SDA'],
    DISPLAY_CONFIG['width'],
    DISPLAY_CONFIG['height'],
    DISPLAY_CONFIG['i2c_address']
)

hydro_config = {
    'relay_pin': PIN_CONFIG['RELAY'],
    'thresholds': THRESHOLDS,
}
hydro = HydroponicSystem(hydro_config)

def mqtt_callback(topic, message):
    topics = MQTT_CONFIG['topics']

    if topic == topics['mode']:
        old_mode = hydro.is_auto_mode
        hydro.set_mode(message)
        if old_mode != hydro.is_auto_mode:
            mode_text = "  TO AUTO" if hydro.is_auto_mode else " TO MANUAL"
            display.trigger_notification(" MODE CHANGED ", mode_text)

    elif topic == topics['relay'] and not hydro.is_auto_mode:
        old_relay = hydro.relay_state
        if message == 'on':
            hydro.set_relay(True)
        elif message == 'off':
            hydro.set_relay(False)
        if old_relay != hydro.relay_state:
            pump_text = "   TO ON" if hydro.relay_state else "   TO OFF"
            display.trigger_notification(" PUMP CHANGED ", pump_text)

    hydro.run_logic()
    update_display()

mqtt = MQTTClientWrapper(MQTT_CONFIG, mqtt_callback)
mqtt.connect()

last_publish = 0
last_dht = 0
last_dist = 0

def update_display():
    state = hydro.get_state()
    state['wifi'] = wifi_manager.sta.isconnected()
    state['mqtt'] = mqtt.is_connected()
    state['interval'] = TIMING['publish_interval'] // 1000
    display.render(state)

def handle_button():
    global last_button_state
    current = button.value()
    if current == 1 and last_button_state == 0:
        display.toggle_page()
        update_display()
        time.sleep_ms(250)
    last_button_state = current

print("System ready!")
update_display()

while True:
    if not mqtt.is_connected():
        mqtt.reconnect()

    mqtt.check_msg()
    handle_button()

    now = time.ticks_ms()

    if display.check_notification(TIMING['notification_duration']):
        update_display()

    if time.ticks_diff(now, last_dist) >= TIMING['dist_interval']:
        last_dist = now
        dist = ultrasonic.read()
        hydro.update_sensors(hydro.temperature, hydro.humidity, dist)
        changed = hydro.run_logic()
        if changed:
            pump_text = "   TO ON" if hydro.relay_state else "   TO OFF"
            display.trigger_notification(" PUMP CHANGED ", pump_text)
        update_display()

    if time.ticks_diff(now, last_dht) >= TIMING['dht_interval']:
        last_dht = now
        temp, hum = dht_sensor.read()
        hydro.update_sensors(temp, hum, hydro.distance)
        update_display()

    if time.ticks_diff(now, last_publish) >= TIMING['publish_interval']:
        last_publish = now
        payload = hydro.get_mqtt_payload()
        mqtt.publish_status(payload)

    time.sleep_ms(10)
