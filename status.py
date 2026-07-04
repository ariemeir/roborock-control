import asyncio, pickle
from roborock.devices.device_manager import create_device_manager, UserParams
from config import EMAIL

async def main():
    with open("user_data.pkl", "rb") as f:
        user_data = pickle.load(f)
    dm = await create_device_manager(UserParams(username=EMAIL, user_data=user_data))
    devices = await dm.get_devices()
    try:
        for device in devices:
            if not device.v1_properties:
                continue
            status = device.v1_properties.status
            await status.refresh()
            print(device.name, "->", status)
    finally:
        for d in devices:
            close = getattr(d, "close", None)
            if close:
                res = close()
                if asyncio.iscoroutine(res): await res
        dm_close = getattr(dm, "close", None)
        if dm_close:
            res = dm_close()
            if asyncio.iscoroutine(res): await res

asyncio.run(main())
