# ============================================================
# WIFI MANAGER MODULE
# Handles WiFi connection and captive portal for configuration
# ============================================================

import network
import socket
import json
import time

F = 'wifi_config.json'      # WiFi credentials storage file
AP_SSID = 'Fauzan Hydro'    # Access Point SSID for setup mode


class WiFiManager:
    """WiFi connection manager with captive portal setup"""
    
    def __init__(self):
        # Initialize WiFi interfaces
        self.sta = network.WLAN(network.STA_IF)  # Station mode (client)
        self.ap = network.WLAN(network.AP_IF)    # Access Point mode (hotspot)

    def is_configured(self):
        """Check if WiFi credentials are saved
        Returns: True if config file exists with SSID
        """
        try:
            with open(F) as f:
                c = json.load(f)
                return 'ssid' in c
        except:
            return False

    def get_creds(self):
        """Load saved WiFi credentials
        Returns: dict with 'ssid' and 'password', or None
        """
        try:
            with open(F) as f:
                return json.load(f)
        except:
            return None

    def save(self, ssid, pwd):
        """Save WiFi credentials to flash storage"""
        with open(F, 'w') as f:
            json.dump({'ssid': ssid, 'password': pwd}, f)

    def connect_saved(self, timeout=15):
        """Connect to saved WiFi network
        timeout: connection timeout in seconds
        Returns: True on success, False on failure/timeout
        """
        c = self.get_creds()
        if not c:
            return False
        print("WiFi:", c['ssid'])
        if self.sta.isconnected():
            return True
        self.sta.active(True)
        self.sta.connect(c['ssid'], c.get('password', ''))
        t = time.time()
        # Wait for connection with timeout
        while not self.sta.isconnected():
            if time.time() - t > timeout:
                self.sta.active(False)
                return False
            time.sleep(0.5)
        print("IP:", self.sta.ifconfig()[0])
        return True

    def start_ap(self):
        """Start WiFi Access Point for configuration"""
        self.ap.active(True)
        time.sleep(1)
        self.ap.config(ssid=AP_SSID, authmode=network.AUTH_OPEN)
        time.sleep(2)
        print("AP:", AP_SSID)
        print("IP:", self.ap.ifconfig()[0])

    def start_captive_portal(self):
        """Start captive portal web server for WiFi setup
        Blocks until WiFi is configured and device reboots
        """
        self.start_ap()
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 80))
        s.listen(1)
        print("Web:80")
        # Main server loop
        while True:
            c, a = s.accept()
            try:
                c.settimeout(5)
                r = b''
                # Read HTTP request
                while True:
                    d = c.recv(256)
                    if not d:
                        break
                    r += d
                    if b'\r\n\r\n' in r:
                        h = r.find(b'\r\n\r\n')
                        cl = 0
                        # Parse Content-Length header
                        for l in r[:h].decode().split('\r\n'):
                            if l.lower().startswith('content-length:'):
                                cl = int(l.split(':')[1])
                                break
                        if len(r) - h - 4 >= cl:
                            break
                rs = r.decode()
                # Route requests
                if 'POST /save' in rs:
                    self._save(c, rs[rs.find('\r\n\r\n')+4:])
                else:
                    self._page(c)  # Show setup page
            except Exception as e:
                print("Web err:", e)
            finally:
                try:
                    c.close()
                except:
                    pass

    def _save(self, c, body):
        """Handle POST /save - save WiFi credentials and reboot"""
        p = {}
        # Parse URL-encoded form data
        for x in body.split('&'):
            if '=' in x:
                k, v = x.split('=', 1)
                p[k] = self._dec(v)
        ssid = p.get('ssid', '')
        if ssid:
            self.save(ssid, p.get('password', ''))
            # Send success response
            c.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            c.send('<html><body style="background:#1a1a2e;color:#eee;text-align:center;padding:50px"><h1 style="color:#00d4aa">Saved!</h1><p>Rebooting...</p></body></html>')
            time.sleep(2)
            import machine
            machine.reset()  # Reboot to connect with new credentials
        else:
            c.send('HTTP/1.1 400 Bad Request\r\n\r\n')

    def _page(self, c):
        """Serve the WiFi setup HTML page"""
        c.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
        c.send('<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>WiFi</title><style>body{font-family:Arial;text-align:center;padding:20px;background:#1a1a2e;color:#eee}h1{color:#00d4aa}form{max-width:300px;margin:0 auto}input[type=text],input[type=password]{width:100%;padding:12px;margin:8px 0;border:1px solid #333;border-radius:5px;box-sizing:border-box;background:#16213e;color:#eee}input[type=submit]{width:100%;padding:15px;background:#00d4aa;color:#000;border:none;border-radius:5px;font-size:18px;font-weight:bold;cursor:pointer;margin-top:15px}</style></head><body><h1>Smart Hydroponic</h1><h2>WiFi Setup</h2><form method="POST" action="/save"><input type="text" name="ssid" placeholder="WiFi SSID" required><br><input type="password" name="password" placeholder="Password"><br><input type="submit" value="SAVE AND CONNECT"></form></body></html>')

    def _dec(self, s):
        """URL decode form data"""
        r = ''
        i = 0
        while i < len(s):
            if s[i] == '+':
                r += ' '
                i += 1
            elif s[i] == '%' and i + 2 < len(s):
                try:
                    r += chr(int(s[i+1:i+3], 16))
                    i += 3
                except:
                    r += s[i]
                    i += 1
            else:
                r += s[i]
                i += 1
        return r
