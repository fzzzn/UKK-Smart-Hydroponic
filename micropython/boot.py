import webrepl
import esp
import gc

gc.threshold(50000)

esp.osdebug(None)

try:
    webrepl.start()
except:
    pass
