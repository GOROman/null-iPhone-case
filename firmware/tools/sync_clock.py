"""Set the PaperDIY clock from this computer over USB (requires pyserial)."""
import argparse
from datetime import datetime
import time

import serial

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("port")
args = parser.parse_args()
end = time.monotonic() + 25
while time.monotonic() < end:
    try:
        with serial.Serial(port=None, baudrate=115200, timeout=1.5, write_timeout=1) as device:
            device.port = args.port
            device.dtr = True
            device.rts = False
            device.open()
            while time.monotonic() < end:
                now = datetime.now().astimezone()
                offset = int(now.utcoffset().total_seconds() / 60)
                device.write(f"TIME {int(now.timestamp())} {offset}\n".encode())
                reply = device.readline().decode(errors="replace").strip()
                if reply and not reply.startswith("TIME OK "):
                    print(reply, flush=True)
                if reply.startswith("TIME OK "):
                    print(reply)
                    raise SystemExit(0)
    except (serial.SerialException, OSError):
        time.sleep(0.5)
raise SystemExit("No clock confirmation. Wake the PaperDIY and check the USB port.")
