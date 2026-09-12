# Roborock, driven directly

Drive a Roborock vacuum from the keyboard, or from a phone on the local network,
without using the vendor app. This turns the robot into a remote-controlled
camera you can send to another room and look through.

## Why

The vendor app can start a cleaning run and show a map, but it cannot drive the
robot manually. The robot already has motors, a camera and a video stream. The
only missing piece is a control interface that treats it as a vehicle rather
than an appliance.

## What is here

| File | What it does |
|---|---|
| [`login.py`](login.py) | Authenticates once and pickles the session, so nothing else has to hold credentials. |
| [`drive.py`](drive.py) | Keyboard driving in the terminal. Arrow keys set forward speed and turn rate, and the command is released when you let go. A duration limit stops the robot if the connection drops. |
| [`server.py`](server.py) | An aiohttp server offering the same movement commands over HTTP, plus an HLS video stream from the robot's camera, so a phone gets video and controls on one page. |
| [`home.py`](home.py) | Send it back to the dock. |
| [`beep.py`](beep.py) | Makes the robot beep, so you can find it when it is under furniture. |
| [`status.py`](status.py) | Battery, state and current room. |

Movement is sent as `(velocity, omega)` pairs, where `omega` is the turn rate.
Every movement is explicitly released afterwards, because the robot keeps
running the last command it received until told otherwise.

## Setup

```
cp .env.example .env      # fill in your Roborock account email
python3 login.py          # writes user_data.pkl, once
python3 drive.py          # keyboard control
python3 server.py         # http control + HLS video on :8050
```

The saved session file and `.env` are both gitignored.

`DURATION` limits how long a single movement command can run. This matters: on
an unreliable wifi link, the server can send a move command and then fail to
send the stop, and without the limit the robot would keep going.

## Notes

This is built on the
[`python-roborock`](https://github.com/humbertogontijo/python-roborock) library,
which handles the protocol. This repo is the control layer on top of it, not a
protocol implementation.

This project is unofficial and not affiliated with Roborock. Their cloud API is
not documented for this purpose and may change at any time.

---

Personal project, July 2026. Published for reference.
