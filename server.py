import asyncio, pickle, os
from aiohttp import web
from roborock import RoborockCommand
from roborock.devices.device_manager import create_device_manager, UserParams
from config import EMAIL, RTSP_URL, HOST, PORT, VELOCITY, OMEGA, DURATION

HLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hls")
os.makedirs(HLS_DIR, exist_ok=True)

MOVES = {"forward": (VELOCITY, 0.0), "back": (-VELOCITY, 0.0),
         "left": (0.0, OMEGA), "right": (0.0, -OMEGA), "stop": (0.0, 0.0)}

async def send(device, command, params=None):
    if params is None:
        return await device.v1_properties.command.send(command)
    return await device.v1_properties.command.send(command, params)

def find(app, name):
    return next((d for d in app["devices"] if d.name == name), None)

async def on_startup(app):
    with open("user_data.pkl", "rb") as f:
        user_data = pickle.load(f)
    dm = await create_device_manager(UserParams(username=EMAIL, user_data=user_data))
    app["dm"] = dm
    app["devices"] = [d for d in await dm.get_devices() if d.v1_properties]
    app["seq"] = {d.name: 0 for d in app["devices"]}
    app["ffmpeg"] = None
    print("Ready. Devices:", [d.name for d in app["devices"]])

async def stop_ffmpeg(app):
    proc = app.get("ffmpeg")
    if proc and proc.returncode is None:
        proc.terminate()
        try: await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError: proc.kill()
    app["ffmpeg"] = None

async def on_cleanup(app):
    await stop_ffmpeg(app)
    for d in app["devices"]:
        c = getattr(d, "close", None)
        if c:
            r = c()
            if asyncio.iscoroutine(r): await r
    dc = getattr(app["dm"], "close", None)
    if dc:
        r = dc()
        if asyncio.iscoroutine(r): await r

async def devices_h(req):
    return web.json_response([{"name": d.name} for d in req.app["devices"]])

async def simple(req, command, pre_end=False):
    d = find(req.app, req.query.get("device", ""))
    if not d: return web.json_response({"error": "no device"}, status=404)
    if pre_end:
        try: await send(d, RoborockCommand.APP_RC_END)
        except Exception: pass
    await send(d, command)
    return web.json_response({"ok": True})

async def find_h(req):     return await simple(req, RoborockCommand.FIND_ME)
async def dock_h(req):     return await simple(req, RoborockCommand.APP_CHARGE, pre_end=True)
async def rc_start_h(req): return await simple(req, RoborockCommand.APP_RC_START)
async def rc_end_h(req):   return await simple(req, RoborockCommand.APP_RC_END)

async def rc_move_h(req):
    app = req.app
    d = find(app, req.query.get("device", ""))
    if not d: return web.json_response({"error": "no device"}, status=404)
    vel, omg = MOVES.get(req.query.get("dir", "stop"), (0.0, 0.0))
    app["seq"][d.name] += 1
    await send(d, RoborockCommand.APP_RC_MOVE,
               [{"omega": omg, "velocity": vel, "seqnum": app["seq"][d.name], "duration": DURATION}])
    return web.json_response({"ok": True})

async def video_start_h(req):
    app = req.app
    await stop_ffmpeg(app)
    for f in os.listdir(HLS_DIR):
        try: os.remove(os.path.join(HLS_DIR, f))
        except OSError: pass
    m3u8 = os.path.join(HLS_DIR, "stream.m3u8")
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-rtsp_transport", "tcp", "-i", RTSP_URL,
        "-an", "-c:v", "copy",
        "-f", "hls", "-hls_time", "1", "-hls_list_size", "4",
        "-hls_flags", "delete_segments+omit_endlist", m3u8,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    app["ffmpeg"] = proc
    return web.json_response({"ok": True})

async def video_stop_h(req):
    await stop_ffmpeg(req.app)
    return web.json_response({"ok": True})

app = web.Application()
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)
app.router.add_get("/devices", devices_h)
app.router.add_post("/find", find_h)
app.router.add_post("/dock", dock_h)
app.router.add_post("/rc/start", rc_start_h)
app.router.add_post("/rc/end", rc_end_h)
app.router.add_post("/rc/move", rc_move_h)
app.router.add_post("/video/start", video_start_h)
app.router.add_post("/video/stop", video_stop_h)
app.router.add_static("/hls/", HLS_DIR)

if __name__ == "__main__":
    web.run_app(app, host=HOST, port=PORT)
