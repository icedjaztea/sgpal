import queue
from core import CONFIG
from hardware import Controls
q=queue.Queue(); controls=Controls(CONFIG,q)
print('Turn and press knob; press Back and Scan. Ctrl+C to finish.',flush=True)
try:
 while True: print(q.get()[0],flush=True)
except KeyboardInterrupt: pass
finally: controls.close()
