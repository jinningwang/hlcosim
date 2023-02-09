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

try:
    os.remove(path_file)
    logger.warning("Successfully remove file %s" % path_file)
except FileNotFoundError:
    pass

# --- emulated data IO ---
logger.warning('Emulated data IO start!')
for j in range(3):
    logger.warning("Counter base Updated to %d" % j)
    for i in range(11, 200):
        # time.sleep(0.049)
        time.sleep(0.04)
        scsv = open(path_file, "w")
        with scsv as f:
            f.write(f'{i}\n22349\n21230\n')
            scsv.close()
logger.warning('Emulated data IO end!')

# --- remove file ---
# try:
#     os.remove(path_file)
#     logger.warning("Successfully remove file %s" % path_file)
# except:
#     pass
