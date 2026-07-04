"""Central config. Loads .env and exposes typed constants."""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# Required secrets (raise loudly if missing)
EMAIL    = os.environ["ROBOROCK_EMAIL"]
RTSP_URL = os.environ["RTSP_URL"]

# Server
HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("SERVER_PORT", "8050"))

# Default robot
DEFAULT_ROBOT = os.environ.get("DEFAULT_ROBOT", "Papa office")

# RC tuning
VELOCITY = float(os.environ.get("RC_VELOCITY", "0.2"))
OMEGA    = float(os.environ.get("RC_OMEGA", "1.0"))
DURATION = int(os.environ.get("RC_DURATION", "600"))
