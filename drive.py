import asyncio, pickle, sys, termios, tty
from roborock import RoborockCommand
from roborock.devices.device_manager import create_device_manager, UserParams
from config import EMAIL, DEFAULT_ROBOT, VELOCITY, OMEGA, DURATION

TARGET = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROBOT

def read_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(seq, "esc")
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

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
        print(f"Driving: {target.name}")
        print("  arrows or WASD = move | space = stop | q = quit")
        await cmd.send(RoborockCommand.APP_RC_START)
        seq = 0
        loop = asyncio.get_event_loop()
        while True:
            key = await loop.run_in_executor(None, read_key)
            if key in ("q", "esc"):
                break
            vel, omg = 0.0, 0.0
            if   key in ("up", "w"):    vel =  VELOCITY
            elif key in ("down", "s"):  vel = -VELOCITY
            elif key in ("left", "a"):  omg =  OMEGA
            elif key in ("right", "d"): omg = -OMEGA
            elif key == " ":            pass
            else:                       continue
            seq += 1
            await cmd.send(
                RoborockCommand.APP_RC_MOVE,
                [{"omega": omg, "velocity": vel, "seqnum": seq, "duration": DURATION}],
            )
            print(f"\r{key:>6}  vel={vel:+.2f} omega={omg:+.2f} seq={seq}   ", end="", flush=True)
    finally:
        if target is not None:
            try:
                await target.v1_properties.command.send(RoborockCommand.APP_RC_END)
            except Exception:
                pass
        for d in devices:
            close = getattr(d, "close", None)
            if close:
                res = close()
                if asyncio.iscoroutine(res): await res
        dm_close = getattr(dm, "close", None)
        if dm_close:
            res = dm_close()
            if asyncio.iscoroutine(res): await res
    print("\nDone. RC mode ended.")

asyncio.run(main())
