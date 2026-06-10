from machine import Pin, I2C
import ssd1306
import time

class Display:
    def __init__(self, scl, sda, w, h, addr):
        self.w = w
        self.h = h
        self.oled = ssd1306.SSD1306_I2C(w, h, I2C(scl=Pin(scl), sda=Pin(sda)), addr)
        self.page = 0
        self.notif = None
        self.nt = 0
        self.ncd = 0

    def loading(self, msg):
        self.oled.fill(0)
        self.oled.text("LOADING", 32, 20, 1)
        self.oled.text(msg, 0, 40, 1)
        self.oled.show()

    def render(self, s):
        self.oled.fill(0)
        if self.page == 0:
            self._p1(s)
        else:
            self._p2(s)
        if self.notif:
            self.oled.fill_rect(14, 16, 100, 32, 0)
            self.oled.rect(14, 16, 100, 32, 1)
            self.oled.text(self.notif[0], 20, 22, 1)
            self.oled.text(self.notif[1], 20, 36, 1)
        self.oled.show()

    def _p1(self, s):
        self.oled.text("STATUS", 0, 0, 1)
        self.oled.hline(0, 9, 128, 1)
        self.oled.text("M:" + ("AUTO" if s['a'] else "MANUAL"), 0, 14, 1)
        self.oled.text("P:" + ("ON" if s['r'] else "OFF"), 88, 14, 1)
        self.oled.text("T:{:.1f}C".format(s['t']), 0, 26, 1)
        self.oled.text("H:{:.1f}%".format(s['h']), 0, 38, 1)
        d = s['d']
        self.oled.text("D:" + ("ERR" if d < 0 else "{:.1f}cm".format(d)), 0, 50, 1)

    def _p2(self, s):
        self.oled.text("NETWORK", 0, 0, 1)
        self.oled.hline(0, 9, 128, 1)
        self.oled.text("WIFI:" + ("OK" if s['w'] else "OFF"), 0, 14, 1)
        self.oled.text("MQTT:" + ("OK" if s['m'] else "OFF"), 0, 26, 1)
        self.oled.text("INT:{}s".format(s['i']), 0, 38, 1)

    def notif_show(self, l1, l2, cd=5000):
        n = time.ticks_ms()
        if time.ticks_diff(n, self.ncd) < 0:
            return
        self.notif = (l1, l2)
        self.nt = n
        self.ncd = time.ticks_add(n, cd)

    def notif_check(self, dur):
        if self.notif and time.ticks_diff(time.ticks_ms(), self.nt) >= dur:
            self.notif = None
            return True
        return False

    def toggle(self):
        self.page = 1 - self.page
