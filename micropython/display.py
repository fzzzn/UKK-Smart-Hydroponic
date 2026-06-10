from machine import Pin, I2C
import ssd1306
import time

class Display:
    def __init__(self, scl_pin, sda_pin, width, height, i2c_addr):
        self.width = width
        self.height = height
        self.i2c = I2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.oled = ssd1306.SSD1306_I2C(width, height, self.i2c, i2c_addr)
        self.page = 0
        self.notification = None
        self.notification_time = 0

    def clear(self):
        self.oled.fill(0)

    def show(self):
        self.oled.show()

    def draw_line(self, x1, y1, x2, y2):
        self.oled.hline(x1, y1, x2 - x1, 1) if y1 == y2 else self.oled.vline(x1, y1, y2 - y1, 1)

    def draw_rect(self, x, y, w, h):
        self.oled.rect(x, y, w, h, 1)

    def fill_rect(self, x, y, w, h):
        self.oled.fill_rect(x, y, w, h, 0)

    def text(self, text, x, y):
        self.oled.text(text, x, y, 1)

    def trigger_notification(self, line1, line2):
        self.notification = (line1, line2)
        self.notification_time = time.ticks_ms()

    def check_notification(self, duration):
        if self.notification:
            if time.ticks_diff(time.ticks_ms(), self.notification_time) >= duration:
                self.notification = None
                return True
        return False

    def render(self, state):
        self.clear()

        if self.page == 0:
            self._render_sensor_page(state)
        else:
            self._render_network_page(state)

        if self.notification:
            self._render_notification()

        self.show()

    def _render_sensor_page(self, state):
        mode_text = "Mode: Auto" if state['is_auto'] else "Mode: Man"
        pump_text = "Pump: On" if state['relay'] else "Pump: Off"

        self.text(mode_text, 0, 0)
        self.text(pump_text, 74, 0)
        self.draw_line(0, 10, 128, 10)

        self.text("Temperature: {:.1f}C".format(state['temp']), 0, 15)
        self.text("Humidity:  {:.1f}%".format(state['hum']), 0, 30)

        if state['dist'] == -1:
            dist_text = "Distance: ERR"
        else:
            dist_text = "Distance: {:.1f}cm".format(state['dist'])
        self.text(dist_text, 0, 45)

    def _render_network_page(self, state):
        self.text("Network Config", 15, 0)
        self.draw_line(0, 10, 128, 10)

        wifi_status = "Connected" if state['wifi'] else "Offline"
        mqtt_status = "Connected" if state['mqtt'] else "Offline"

        self.text("WIFI: " + wifi_status, 0, 15)
        self.text("MQTT: " + mqtt_status, 0, 30)
        self.text("Interval: {}s".format(state['interval']), 0, 45)

    def _render_notification(self):
        self.fill_rect(14, 16, 100, 32)
        self.draw_rect(14, 16, 100, 32)

        line1, line2 = self.notification
        self.text(line1, 20, 22)
        self.text(line2, 20, 36)

    def toggle_page(self):
        self.page = 1 - self.page
