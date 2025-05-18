# disc_read_worker.py
import libdiscid
import json

try:
    disc = libdiscid.read('/dev/sr0') # libdiscid.read 会阻塞线程，所以需要使用subprocess.run
    print(json.dumps({
        "id": disc.id,
        "toc": disc.toc,
    }))
except Exception as e:
    print(json.dumps({"error": str(e)}))