#!/usr/bin/python3

import os
import time
import subprocess

snapshot = subprocess.check_output("/usr/local/bin/mast c", shell=True)
while True:
    if os.path.exists(f"/.snapshots/rootfs/snapshot-chr{snapshot}"):
        time.sleep(20)
    else:
        os.system("/usr/local/bin/mast clone $(/usr/local/bin/mast c)")
        os.system("/usr/local/bin/mast auto-upgrade")
        os.system("/usr/local/bin/mast base-update")
        break

upstate = open("/.snapshots/mast/upstate")
line = upstate.readline()
upstate.close()

if "1" not in line:
    os.system("/usr/local/bin/mast deploy $(/usr/local/bin/mast c)")

