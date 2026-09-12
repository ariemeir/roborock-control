# Roborock, driven directly

Drive a Roborock vacuum from the keyboard, or from a phone over the local
network, without the vendor app. The robot becomes a remote-controlled camera
platform that can be sent somewhere and looked through.

## Why

The vendor app can start a clean and show a map. It cannot let you drive the
thing down the hall to see whether you left the stove on. The robot already has
the motors, the camera and a video stream; the only missing piece is a control
surface that treats it as a vehicle rather than an appliance.

## What is here

| File | What it does |
|---|---|
| [`login.py`](login.py) | Authenticates once and pickles the session, so nothing else has to hold credentials. |
| [`drive.py`](drive.py) | Raw-mode terminal driving. Arrow keys map to velocity and yaw, released on key-up, with a duration cap so a dropped connection cannot leave it running. |
| [`server.py`](server.py) | An aiohttp control server: the same movement commands over HTTP, plus an HLS stream from the robot's camera so the phone gets video and controls in one page. |
| [`home.py`](home.py) | Send it back to the dock. |
| [`beep.py`](beep.py) | Locate it by ear when it is under furniture. |
| [`status.py`](status.py) | Battery, state and current room. |

Movement is expressed as `(velocity, omega)` pairs and always released
explicitly, because the robot will happily keep executing the last command it
received.

## Setup

```
cp .env.example .env      # fill in your Roborock account email
python3 login.py          # writes user_data.pkl, once
python3 drive.py          # keyboard control
python3 server.py         # http control + HLS video on :8050
```

The session pickle and `.env` are gitignored. `DURATION` caps how long a single
movement command can run, which matters more than it sounds: a control server on
a flaky wifi link will otherwise send a move and never send the stop.

## Notes

Built against the [`python-roborock`](https://github.com/humbertogontijo/python-roborock)
library, which does the protocol work. This repo is the control surface on top of
it, not the protocol implementation.

Unofficial and unaffiliated. Roborock's cloud API is not documented for this use
and can change without notice.

---

Personal project, July 2026. Published for reference.
