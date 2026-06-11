# MicroPython Smart Hydroponic System

Modular MicroPython implementation for ESP8266-based smart hydroponic system with cloud visualization.

## Features

- **Auto/Manual Mode**: Switch via MQTT `fauzan/mode`
- **Pump Control**: Auto based on water level, or manual via MQTT
- **OLED Display**: Three pages (Status / Network / Clock), toggle with button
- **Notifications**: Pop-up alerts for mode/pump changes
- **WiFi Manager**: Captive portal for easy setup
- **NTP Time Sync**: Automatic time synchronization via NTP
- **ThingSpeak Integration**: Cloud data visualization with 15s upload interval
- **MQTT Control**: Real-time remote control and monitoring
- **Environment Variables**: Secure credential storage in `.env` file
- **Decoupled Timers**: Independent intervals for sensors, display, MQTT

## Files Structure

```
micropython/
├── boot.py           # Early boot config (WebREPL)
├── main.py           # Entry point & main loop
├── config.py         # Pin mappings, settings, intervals (loads secrets from .env)
├── .env              # Environment variables (secrets) - NOT committed to git
├── env_loader.py     # Lightweight .env parser for MicroPython
├── wifi_manager.py   # Captive portal for WiFi setup
├── sensors.py        # DHT22 & ultrasonic sensor classes
├── display.py        # SSD1306 OLED driver
├── mqtt_client.py    # MQTT connection & callbacks
├── hydroponic.py     # Pump logic & state management
├── thingspeak.py     # ThingSpeak HTTP client
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

2. Configure environment variables:
   ```bash
   # Edit .env file with your credentials
   MQTT_HOST=your_broker_ip
   MQTT_PORT=1883
   MQTT_USER=your_username
   MQTT_PASS=your_password
   TS_API_KEY=your_thingspeak_api_key
   ```

3. Upload all files to ESP8266:
   ```bash
   # Using mpremote
   mpremote cp *.py :
   mpremote cp .env :
   
   # Or using ampy
   ampy -p /dev/ttyUSB0 put config.py
   ampy -p /dev/ttyUSB0 put .env
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

## Configuration

### Environment Variables (.env)

The `.env` file stores sensitive credentials and is excluded from git:

```env
# MQTT Configuration
MQTT_HOST=103.210.35.166
MQTT_PORT=1883
MQTT_USER=mqtt
MQTT_PASS=mqtt

# ThingSpeak API
TS_API_KEY=your_write_api_key_here
```

### Display Pages

The OLED display has 3 pages, cycled with the button:

1. **Status Page**: Mode, pump state, temperature, humidity, water level
2. **Network Page**: WiFi status, MQTT status, ThingSpeak status, upload interval
3. **Clock Page**: Current time (NTP synced, GMT+7) and date

## MQTT Topics

| Topic | Direction | Payload |
|-------|-----------|---------|
| `fauzan/status` | Publish | JSON with sensor data |
| `fauzan/mode` | Subscribe | `auto` or `manual` |
| `fauzan/relay` | Subscribe | `on` or `off` |

## ThingSpeak Integration

Data is sent to ThingSpeak every 15 seconds (free tier minimum):

- **Field 1**: Temperature (°C)
- **Field 2**: Humidity (%)
- **Field 3**: Water level distance (cm)
- **Field 4**: Pump state (0=off, 1=on)
- **Field 5**: Mode (0=auto, 1=manual)

## Troubleshooting

**OLED not working:**
- Check I2C address (default 0x3C)
- Verify SDA/SCL pins

**DHT22 reading errors:**
- Ensure 10k pull-up resistor on data line
- Check power supply (3.3V)

**MQTT not connecting:**
- Verify broker IP/port in `.env`
- Check WiFi connection on network page

**ThingSpeak not updating:**
- Verify API key in `.env`
- Check TS status on network page (OK/ERR)
- Free tier limit: 1 update per 15 seconds

**WiFi captive portal not starting:**
- Delete `wifi_config.json` to reset
- Power cycle the device

**Clock showing wrong time:**
- Check NTP sync on boot
- Time zone is hardcoded to GMT+7 (WIB) in display.py

## Memory Usage

System maintains ~35KB free memory for stability:
- Optimized for ESP8266's limited RAM
- Periodic garbage collection
- Lightweight HTTP client for ThingSpeak
- Efficient display rendering

## License

MIT License
