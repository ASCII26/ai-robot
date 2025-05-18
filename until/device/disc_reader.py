# disc_read_worker.py
# import libdiscid
import json
import subprocess
import uuid


def get_id(text):
    # 生成 UUID
    unique_id = uuid.uuid5(uuid.NAMESPACE_DNS, text)
    # 取前8位
    return str(unique_id)

try:
    # disc = libdiscid.read('/dev/sr0') # libdiscid.read 会阻塞线程，所以需要使用subprocess.run
    disc = subprocess.run(["cd-discid","--musicbrainz"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    data = disc.stdout.decode("utf-8").replace("\n", "")
    print(json.dumps({
        "id": get_id(data),
        "toc": data,
    }))
except Exception as e:
    print(json.dumps({"error": str(e)}))