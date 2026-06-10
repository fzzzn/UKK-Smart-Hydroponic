import network
import socket
import json
import time
from machine import Pin

WIFI_CONFIG_FILE = 'wifi_config.json'
AP_SSID = 'Fauzan Smart Hydroponic'
AP_PASSWORD = None

class WiFiManager:
    def __init__(self):
        self.sta = network.WLAN(network.STA_IF)
        self.ap = network.WLAN(network.AP_IF)

    def is_configured(self):
        try:
            with open(WIFI_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return 'ssid' in config and 'password' in config
        except:
            return False

    def get_saved_credentials(self):
        try:
            with open(WIFI_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return None

    def save_credentials(self, ssid, password):
        with open(WIFI_CONFIG_FILE, 'w') as f:
            json.dump({'ssid': ssid, 'password': password}, f)

    def connect_saved(self, timeout=15):
        if not self.is_configured():
            return False

        creds = self.get_saved_credentials()
        if not creds:
            return False

        self.sta.active(True)
        self.sta.connect(creds['ssid'], creds['password'])

        start = time.time()
        while not self.sta.isconnected():
            if time.time() - start > timeout:
                print("WiFi connection timeout")
                return False
            time.sleep(0.5)

        print("WiFi connected:", self.sta.ifconfig())
        return True

    def start_ap(self):
        self.ap.active(True)
        if AP_PASSWORD:
            self.ap.config(ssid=AP_SSID, password=AP_PASSWORD, authmode=network.AUTH_WPA2_PSK)
        else:
            self.ap.config(ssid=AP_SSID, authmode=network.AUTH_OPEN)

        while not self.ap.active():
            time.sleep(0.5)

        print("AP started:", AP_SSID)
        print("IP:", self.ap.ifconfig()[0])

    def stop_ap(self):
        self.ap.active(False)

    def start_captive_portal(self):
        self.start_ap()
        self._run_web_server()

    def _run_web_server(self):
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        print("Web server listening on port 80")

        while True:
            cl, addr = s.accept()
            try:
                request = cl.recv(1024).decode('utf-8')

                if 'POST /save' in request:
                    self._handle_save(cl, request)
                else:
                    self._send_config_page(cl)
            except Exception as e:
                print("Web server error:", e)
            finally:
                cl.close()

    def _handle_save(self, cl, request):
        lines = request.split('\r\n')
        for line in lines:
            if line.startswith('ssid='):
                data = line.split('HTTP')[0]
                params = {}
                for pair in data.split('&'):
                    if '=' in pair:
                        key, val = pair.split('=', 1)
                        params[key] = val.replace('+', ' ')

                ssid = params.get('ssid', '')
                password = params.get('password', '')

                if ssid:
                    self.save_credentials(ssid, password)
                    response = self._success_page()
                else:
                    response = self._error_page()

                cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                cl.send(response)
                time.sleep(2)
                import machine
                machine.reset()
                return

        cl.send('HTTP/1.1 400 Bad Request\r\n\r\n')

    def _send_config_page(self, cl):
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Smart Hydroponic - WiFi Setup</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 20px; background: #1a1a2e; color: #eee; }
        h1 { color: #00d4aa; }
        form { max-width: 300px; margin: 0 auto; }
        input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #333; border-radius: 5px; box-sizing: border-box; background: #16213e; color: #eee; }
        button { width: 100%; padding: 12px; background: #00d4aa; color: #000; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #00b894; }
    </style>
</head>
<body>
    <h1>Smart Hydroponic</h1>
    <h2>WiFi Configuration</h2>
    <form method="POST" action="/save">
        <input type="text" name="ssid" placeholder="WiFi SSID" required>
        <input type="password" name="password" placeholder="WiFi Password">
        <button type="submit">Save & Connect</button>
    </form>
</body>
</html>'''
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
        cl.send(html)

    def _success_page(self):
        return '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Saved</title>
<style>body{font-family:Arial;text-align:center;padding:50px;background:#1a1a2e;color:#eee;}h1{color:#00d4aa;}</style>
</head>
<body><h1>WiFi Saved!</h1><p>Reconnecting...</p></body>
</html>'''

    def _error_page(self):
        return '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Error</title>
<style>body{font-family:Arial;text-align:center;padding:50px;background:#1a1a2e;color:#eee;}h1{color:#ff6b6b;}</style>
</head>
<body><h1>Error</h1><p>Invalid SSID</p><a href="/">Try Again</a></body>
</html>'''
