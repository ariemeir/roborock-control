import asyncio, pickle, sys
from roborock import RoborockCommand
from roborock.devices.device_manager import create_device_manager, UserParams
from config import EMAIL, DEFAULT_ROBOT

TARGET = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROBOT

async def main():
    with open("user_data.pkl", "rb") as f:
        user_data = pickle.load(f)
    dm = await create_device_manager(UserParams(username=EMAIL, user_data=user_data))
    devices = await dm.get_devices()
    target = next((d for d in devices if d.name == TARGET), None)
    try:
        if target is None:
            print("No match for", repr(TARGET), "- available:", [d.name for d in devices])
            return
        cmd = target.v1_properties.command
        try:
            await cmd.send(RoborockCommand.APP_RC_END)
        except Exception:
            pass
        await cmd.send(RoborockCommand.APP_CHARGE)
        print(f"{target.name}: heading back to the dock.")
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
