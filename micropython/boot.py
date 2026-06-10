import gc
gc.threshold(50000)

import esp
esp.osdebug(None)

import webrepl
try:
    webrepl.start()
except:
    pass
