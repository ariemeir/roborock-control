import asyncio, pickle, sys, os
from roborock.web_api import RoborockApiClient
from config import EMAIL

DEVICE_ID_FILE = "device_id.txt"

def get_client():
    api = RoborockApiClient(username=EMAIL)
    # Emailed code is bound to this identifier; keep it stable across runs.
    if os.path.exists(DEVICE_ID_FILE):
        with open(DEVICE_ID_FILE) as f:
            api._device_identifier = f.read().strip()
    else:
        with open(DEVICE_ID_FILE, "w") as f:
            f.write(api._device_identifier)
    return api

async def main():
    api = get_client()
    if "--request" in sys.argv:
        await api.request_code()
        print("Code sent. Check email, then: python login.py <code>")
        return
    if len(sys.argv) < 2:
        print("Usage:\n  python login.py --request\n  python login.py <code>")
        return
    user_data = await api.code_login(sys.argv[1])
    with open("user_data.pkl", "wb") as f:
        pickle.dump(user_data, f)
    print("Logged in. Cached to user_data.pkl")

asyncio.run(main())
