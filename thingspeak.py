# ============================================================
# THINGSPEAK CLIENT MODULE
# Sends sensor data to ThingSpeak for cloud visualization
# ============================================================

import usocket


class ThingSpeak:
    """Lightweight ThingSpeak HTTP client using raw sockets
    Memory-efficient alternative to urequests for ESP8266
    """
    
    def __init__(self, api_key):
        """Initialize ThingSpeak client
        api_key: Write API key from ThingSpeak channel
        """
        self.api_key = api_key
        self.host = 'api.thingspeak.com'
        self.port = 80
        self.ok = False  # Last send status

    def send(self, temp, hum, dist, pump, mode):
        """Send sensor data to ThingSpeak
        temp: temperature in Celsius
        hum: humidity in percentage
        dist: water level distance in cm
        pump: pump state (0=off, 1=on)
        mode: system mode (0=auto, 1=manual)
        Returns: True on success, False on failure
        
        Field mapping:
        - Field 1: Temperature
        - Field 2: Humidity
        - Field 3: Distance
        - Field 4: Pump state
        - Field 5: Mode
        """
        try:
            # Build URL-encoded POST data
            data = 'api_key={}&field1={}&field2={}&field3={}&field4={}&field5={}'.format(
                self.api_key, temp, hum, dist, pump, mode
            )
            
            # Resolve DNS and create socket connection
            addr = usocket.getaddrinfo(self.host, self.port)[0][-1]
            s = usocket.socket()
            s.settimeout(5)  # 5 second timeout
            
            try:
                s.connect(addr)
                # Build HTTP POST request
                req = 'POST /update HTTP/1.1\r\n'
                req += 'Host: {}\r\n'.format(self.host)
                req += 'Content-Type: application/x-www-form-urlencoded\r\n'
                req += 'Content-Length: {}\r\n'.format(len(data))
                req += 'Connection: close\r\n\r\n'
                req += data
                
                s.send(req.encode())
                
                # Read response and check for success
                resp = s.recv(128)
                self.ok = b'200 OK' in resp
                return self.ok
            finally:
                s.close()  # Always close socket
                
        except Exception as e:
            print('TS err:', e)
            self.ok = False
            return False
