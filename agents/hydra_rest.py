"""Drop-in REST replacement for the HydraDB Python SDK.

The official SDK spends ~150s inside its constructor and ~20s per call. The
same operations over plain REST return in tens of milliseconds. This shim
exposes the handful of methods the seeder and coroner use, with the same
`.data` shape, so calling code doesn't change.
"""
import json
import time
import os
from types import SimpleNamespace

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE = "https://api.hydradb.com"
TIMEOUT = 90


def _obj(x):
    """dict/list -> attribute-accessible object, so r.data.results[0].id works."""
    if isinstance(x, dict):
        return SimpleNamespace(**{k: _obj(v) for k, v in x.items()})
    if isinstance(x, list):
        return [_obj(v) for v in x]
    return x


class _Resp:
    def __init__(self, payload):
        self._payload = payload
        self.data = _obj(payload.get("data", payload))

    def model_dump_json(self):
        return json.dumps(self._payload)


class HydraREST:
    def __init__(self, token=None):
        self.token = token or os.environ["HYDRA_DB_API_KEY"]
        self.h = {
            "Authorization": f"Bearer {self.token}",
            "API-Version": "2",
            "Content-Type": "application/json",
        }
        self.databases = _Databases(self)
        self.context = _Context(self)

    def _req(self, method, path, retries=4, **kw):
        """Retry on transport failures. Their API drops TLS connections under
        load, which is exactly what a room full of hackathon traffic looks like.
        A dropped connection must never be what ends the demo."""
        last = None
        for attempt in range(retries):
            try:
                r = requests.request(method, f"{BASE}{path}", headers=self.h,
                                     timeout=TIMEOUT, **kw)
                if r.status_code >= 500:
                    last = RuntimeError(f"{r.status_code} {r.text[:200]}")
                    time.sleep(1.5 * (attempt + 1))
                    continue
                if r.status_code >= 400:
                    raise RuntimeError(
                        f"{method} {path} -> {r.status_code} {r.text[:300]}")
                return _Resp(r.json())
            except (requests.exceptions.SSLError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                last = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"{method} {path} failed after {retries} tries: "
                           f"{str(last)[:200]}")

    def query(self, **body):
        return self._req("POST", "/query", json=body)


class _Databases:
    def __init__(self, c):
        self.c = c

    def list(self):
        return self.c._req("GET", "/databases")

    def create(self, database, database_metadata_schema=None):
        body = {"database": database}
        if database_metadata_schema:
            body["database_metadata_schema"] = database_metadata_schema
        return self.c._req("POST", "/databases", json=body)

    def status(self, database):
        return self.c._req("GET", f"/databases/status?database={database}")


class _Context:
    def __init__(self, c):
        self.c = c

    def ingest(self, **body):
        # /context/ingest rejects JSON: it wants multipart/form-data. Passing
        # every field as a (None, value) part makes requests build a multipart
        # body with plain form fields and no file attached.
        parts = {}
        for k, v in body.items():
            if isinstance(v, bool):
                v = "true" if v else "false"
            elif not isinstance(v, str):
                v = json.dumps(v)
            parts[k] = (None, v)
        h = {k: v for k, v in self.c.h.items() if k != "Content-Type"}
        r = requests.post(f"{BASE}/context/ingest", headers=h, files=parts,
                          timeout=TIMEOUT)
        if r.status_code >= 400:
            raise RuntimeError(f"POST /context/ingest -> {r.status_code} "
                               f"{r.text[:400]}")
        return _Resp(r.json())

    def status(self, database, ids):
        return self.c._req(
            "GET", f"/context/status?database={database}&ids={','.join(ids)}")

    def list(self, **body):
        return self.c._req("POST", "/context/list", json=body)


client = HydraREST()


if __name__ == "__main__":
    import time
    t = time.time()
    print("databases:", client.databases.list().data.databases,
          f"({time.time() - t:.2f}s)")
