# ============================================================
# DISPLAY MODULE
# SSD1306 OLED display driver for 128x64 pixel screen
# ============================================================

from machine import Pin, I2C
import ssd1306
import framebuf
import time


class Display:
    """OLED display controller with multi-page support"""
    
    def __init__(self, scl, sda, w, h, addr):
        """Initialize OLED display
        scl, sda: I2C pins
        w, h: display dimensions (128x64)
        addr: I2C address (0x3C)
        """
        self.w = w
        self.h = h
        self.oled = ssd1306.SSD1306_I2C(
            w, h, I2C(scl=Pin(scl), sda=Pin(sda)), addr)
        self.page = 0      # Current page (0=Status, 1=Network, 2=Clock)
        self.notif = None  # Notification text tuple (line1, line2)
        self.nt = 0        # Notification start time
        self.ncd = 0       # Notification cooldown end time

    def loading(self, msg):
        """Show loading screen with message
        Used during boot sequence to show progress
        """
        self.oled.fill(0)
        self.oled.text("LOADING", 32, 20, 1)
        self.oled.text(msg, 0, 40, 1)
        self.oled.show()

    def render(self, s):
        """Render current page with state data
        s: state dictionary with sensor readings and connection status
        Shows notification overlay if active
        """
        self.oled.fill(0)
        if self.page == 0:
            self._p1(s)      # Status page
        elif self.page == 1:
            self._p2(s)      # Network page
        elif self.page == 2:
            self._p3(s)      # Clock page
        # Draw notification popup if active
        if self.notif:
            self.oled.fill_rect(14, 16, 100, 32, 0)
            self.oled.rect(14, 16, 100, 32, 1)
            self.oled.text(self.notif[0], 20, 22, 1)
            self.oled.text(self.notif[1], 20, 36, 1)
        self.oled.show()

    def _p1(self, s):
        """Page 1: Status page - shows sensor readings and pump state"""
        self.oled.text("STATUS", 0, 0, 1)
        self.oled.hline(0, 9, 128, 1)
        self.oled.text("M:" + ("AUTO" if s['a'] else "MANUAL"), 0, 14, 1)
        self.oled.text("P:" + ("ON" if s['r'] else "OFF"), 88, 14, 1)
        self.oled.text("T:{:.1f}C".format(s['t']), 0, 26, 1)
        self.oled.text("H:{:.1f}%".format(s['h']), 0, 38, 1)
        d = s['d']
        self.oled.text(
            "D:" + ("ERR" if d < 0 else "{:.1f}cm".format(d)), 0, 50, 1)

    def _p2(self, s):
        """Page 2: Network page - shows connection status"""
        self.oled.text("NETWORK", 0, 0, 1)
        self.oled.hline(0, 9, 128, 1)
        self.oled.text("WIFI:" + ("OK" if s['w'] else "OFF"), 0, 14, 1)
        self.oled.text("MQTT:" + ("OK" if s['m'] else "OFF"), 0, 26, 1)
        self.oled.text("TS:" + ("OK" if s['ts'] else "ERR"), 0, 38, 1)
        self.oled.text("INT:{}s".format(s['i']), 0, 50, 1)

    def _tb(self, txt, x, y, sc=2):
        """Draw scaled text using framebuf
        txt: text string to display
        x, y: position
        sc: scale factor (2 = double size)
        Uses framebuf to render text, then scales each pixel
        """
        fb = framebuf.FrameBuffer(
            bytearray(8 * len(txt) * 8), 8 * len(txt), 8, framebuf.MONO_HLSB)
        fb.fill(0)
        fb.text(txt, 0, 0, 1)
        # Draw each pixel scaled up (e.g., sc=2 makes each pixel 2x2)
        for py in range(8):
            for px in range(8 * len(txt)):
                if fb.pixel(px, py):
                    self.oled.fill_rect(x + px * sc, y + py * sc, sc, sc, 1)

    def _p3(self, s):
        """Page 3: Clock display with NTP time (GMT+7 WIB)"""
        t = time.localtime()
        h = (t[3] + 7) % 24  # Convert UTC to GMT+7
        m = t[4]
        self.oled.text("CLOCK", 0, 0, 1)
        self.oled.hline(0, 9, 128, 1)
        # Display time in large 2x scaled text
        self._tb("{:02d}:{:02d}:{:02d}".format(h, m, t[5]), 0, 14, 2)
        # Display date in normal text below
        self.oled.text(
            "{:02d}/{:02d}/{:04d}".format(t[2], t[1], t[0]), 0, 48, 1)

    def notif_show(self, l1, l2, cd=5000):
        """Show notification popup
        l1, l2: two lines of text
        cd: cooldown duration in ms (prevents spam)
        """
        n = time.ticks_ms()
        if time.ticks_diff(n, self.ncd) < 0:
            return  # Skip if still in cooldown
        self.notif = (l1, l2)
        self.nt = n
        self.ncd = time.ticks_add(n, cd)

    def notif_check(self, dur):
        """Check if notification should be hidden
        dur: display duration in ms
        Returns: True if notification was just hidden (triggers redraw)
        """
        if self.notif and time.ticks_diff(time.ticks_ms(), self.nt) >= dur:
            self.notif = None
            return True
        return False

    def toggle(self):
        """Switch to next display page (cycles 0->1->2->0)"""
        self.page = (self.page + 1) % 3
