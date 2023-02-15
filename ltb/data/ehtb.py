"""
Emulater of HTB for test data IO.

Counter updated from 11 to 199, then reset to 11.
"""

import os
import time
import logging

logger = logging.getLogger(__name__)

# --- set file path ---
path = os.path.dirname(os.path.abspath(__file__))
path_file = os.path.join(path, 'tdatar.txt')

T_htb = 0.05  # HTB period

try:
    os.remove(path_file)
    logger.warning("Successfully remove file %s" % path_file)
except FileNotFoundError:
    pass

time.sleep(3)

# --- emulated data IO ---
msg = 'Emulated data IO start, period = %f' % T_htb
logger.warning(msg)
for j in range(3):
    logger.warning("eHTB: Counter base Updated to %d" % j)
    for i in range(11, 200):
        # time.sleep(0.049)
        time.sleep(T_htb)
        scsv = open(path_file, "w")
        with scsv as f:
            f.write(f'{i:x}\n122\n122\n')
            scsv.close()
logger.warning('Emulated data IO end!')

# --- remove file ---
# try:
#     os.remove(path_file)
#     logger.warning("Successfully remove file %s" % path_file)
# except:
#     pass
