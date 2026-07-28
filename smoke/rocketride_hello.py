"""Smoke test: RocketRide Cloud — run a minimal webhook->response pipeline remotely.

PASS means: Cloud auth works and a pipeline executes end-to-end on their runtime.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

URI = os.environ.get("ROCKETRIDE_URI", "https://api.rocketride.ai")
AUTH = os.environ.get("ROCKETRIDE_AUTH") or os.environ.get("ROCKETRIDE_APIKEY")
if not AUTH:
    sys.exit("FAIL: no ROCKETRIDE_AUTH in .env (generate token at cloud.rocketride.ai)")

from rocketride import RocketRideClient  # noqa: E402

PIPELINE = {
    "components": [
        {
            "id": "webhook_1",
            "provider": "webhook",
            "config": {"hideForm": True, "mode": "Source", "parameters": {}, "type": "webhook"},
        },
        {
            "id": "response_text_1",
            "provider": "response_text",
            "config": {"laneName": "text"},
            "input": [{"lane": "text", "from": "webhook_1"}],
        },
    ],
    "version": 1,
}


async def main():
    async with RocketRideClient(uri=URI, auth=AUTH) as client:
        result = await client.use(pipeline=PIPELINE)
        token = result["token"]
        out = await client.send(
            token, "Hello from KEPT!", objinfo={"name": "input.txt"}, mimetype="text/plain"
        )
        print("pipeline output:", out)
        await client.terminate(token)


asyncio.run(main())
print("PASS: RocketRide Cloud pipeline ran end-to-end")
