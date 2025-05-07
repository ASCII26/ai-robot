import time

from roonapi import RoonApi, RoonDiscovery

appinfo = {
    "extension_id": "Muspi_Extension",
    "display_name": "Muspi Roon Extension",
    "display_version": "1.0",
    "publisher": "Muspi",
    "email": "puterjam@gmail.com",
}

need_auth = False
try:
    core_id = open("config/roon_core_id").read()
    token = open("config/roon_token").read()
except OSError:
    print("Please authorise first in roon app")
    core_id = None
    token = None
    need_auth = True



# RoonDiscovery
if need_auth:
    discover = RoonDiscovery(core_id)
    servers = discover.all()
    discover.stop()

    apis = [RoonApi(appinfo, None, server[0], server[1], False) for server in servers]
    auth_api = []
    while len(auth_api) == 0:
        print("Waiting for authorisation")
        time.sleep(1)
        auth_api = [api for api in apis if api.token is not None]

    api = auth_api[0]
    print("Got authorisation.")
    for api in apis:
        api.stop()

    # This is what we need to reconnect
    core_id = api.core_id
    token = api.token

    # Save the token for next time
    with open("config/roon_core_id", "w") as f:
        f.write(core_id)
    with open("config/roon_token", "w") as f:
        f.write(token)


# RoonApi
discover = RoonDiscovery(core_id)
server = discover.first()
discover.stop()

roonapi = RoonApi(appinfo, token, host=server[0], port=server[1])


def my_state_callback(event, changed_ids):
    """Call when something changes in roon."""
    print("my_state_callback event:%s changed_ids: %s" % (event, changed_ids))
    for zone_id in changed_ids:
        zone = roonapi.zones[zone_id]
        print("zone_id:%s zone_info: %s" % (zone_id, zone))


# receive state updates in your callback
roonapi.register_state_callback(my_state_callback)

time.sleep(60)

# save the token for next time
# with open("mytokenfile", "w") as f:
#     f.write(roonapi.token)