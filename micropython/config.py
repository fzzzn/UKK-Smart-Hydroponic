PIN_CONFIG = {
    'OLED_SCL': 5,
    'OLED_SDA': 4,
    'BUTTON': 2,
    'DHT': 14,
    'TRIG': 12,
    'ECHO': 13,
    'RELAY': 16,
}

MQTT_CONFIG = {
    'server': '103.210.35.166',
    'port': 1883,
    'user': 'mqtt',
    'password': 'mqtt',
    'topics': {
        'status': 'fauzan/status',
        'mode': 'fauzan/mode',
        'relay': 'fauzan/relay',
    }
}

TIMING = {
    'publish_interval': 60000,
    'dht_interval': 2000,
    'dist_interval': 1000,
    'notification_duration': 2000,
}

THRESHOLDS = {
    'distance_min': 10.0,
    'distance_max': 20.0,
}

DISPLAY_CONFIG = {
    'width': 128,
    'height': 64,
    'i2c_address': 0x3C,
}
