# MicroPython Smart Hydroponic System

Modular MicroPython implementation for ESP8266-based smart hydroponic system.

## Files Structure

```
micropython/
├── boot.py           # Early boot config (WebREPL)
├── main.py           # Entry point & main loop
├── config.py         # Pin mappings, MQTT settings, intervals
├── wifi_manager.py   # Captive portal for WiFi setup
├── sensors.py        # DHT22 & ultrasonic sensor classes
├── display.py        # SSD1306 OLED driver
├── mqtt_client.py    # MQTT connection & callbacks
├── hydroponic.py     # Pump logic & state management
└── wifi_config.json  # Auto-generated WiFi credentials
```

## Hardware Connections (ESP8266 D1 Mini)

| Component | Pin | GPIO |
|-----------|-----|------|
| OLED SCL  | D1  | 5    |
| OLED SDA  | D2  | 4    |
| Button    | D4  | 2    |
| DHT22     | D5  | 14   |
| Trig      | D6  | 12   |
| Echo      | D7  | 13   |
| Relay     | D0  | 16   |

## Installation

1. Flash MicroPython firmware to ESP8266:
   - Download from: https://micropython.org/download/ESP8266_GENERIC/
   - Use esptool: `esptool.py --port /dev/ttyUSB0 write_flash -fm dio 0 esp8266-*.bin`

2. Install required libraries:
   ```bash
   # Connect to REPL and install ssd1306 driver
   import upip
   upip.install('micropython-ssd1306')
   ```

3. Upload all `.py` files to ESP8266:
   ```bash
   # Using mpremote
   mpremote cp *.py :
   
   # Or using ampy
   ampy -p /dev/ttyUSB0 put config.py
   ampy -p /dev/ttyUSB0 put wifi_manager.py
   # ... repeat for all files
   ```

4. Reset the board:
   ```bash
   mpremote reset
   ```

## First-Time Setup

1. On first boot, ESP8266 creates WiFi AP: `Fauzan Smart Hydroponic`
2. Connect to this AP with your phone/laptop
3. Open browser to `192.168.4.1`
4. Enter your WiFi SSID and password
5. Device saves credentials and reboots
6. Connects to your WiFi automatically on future boots

## MQTT Topics

| Topic | Direction | Payload |
|-------|-----------|---------|
| `fauzan/status` | Publish | JSON with sensor data |
| `fauzan/mode` | Subscribe | `auto` or `manual` |
| `fauzan/relay` | Subscribe | `on` or `off` |

## Features

- **Auto/Manual Mode**: Switch via MQTT `fauzan/mode`
- **Pump Control**: Auto based on water level, or manual via MQTT
- **OLED Display**: Two pages (sensors / network), toggle with button
- **Notifications**: Pop-up alerts for mode/pump changes
- **WiFi Manager**: Captive portal for easy setup
- **Decoupled Timers**: Independent intervals for sensors, display, MQTT

## Troubleshooting

**OLED not working:**
- Check I2C address (default 0x3C)
- Verify SDA/SCL pins

**DHT22 reading errors:**
- Ensure 10k pull-up resistor on data line
- Check power supply (3.3V)

**MQTT not connecting:**
- Verify broker IP/port in `config.py`
- Check WiFi connection on network page

**WiFi captive portal not starting:**
- Delete `wifi_config.json` to reset
- Power cycle the device
