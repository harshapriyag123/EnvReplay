"""Run real requests against the service under both configuration profiles."""

import argparse
import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

from app import serve

ROOT = Path(__file__).resolve().parent


def check(profile):
    config = json.loads((ROOT / "config" / f"{profile}.json").read_text())
    base_path = config["public_base_path"]
    path = base_path + "/api/health"
    server = serve(base_path=base_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}{path}"
        try:
            with urlopen(url, timeout=3) as response:
                status = response.status
                body = response.read().decode("utf-8")
        except HTTPError as error:
            status = error.code
            body = error.read().decode("utf-8")
        print(f"profile={profile} public_base_path={base_path!r}", flush=True)
        print(f"GET {path} -> HTTP {status} {body}", flush=True)
        if status != 200 or json.loads(body).get("status") != "ok":
            print("FAIL: expected HTTP 200 with status=ok", flush=True)
            return 1
        print("PASS: health endpoint responds under this configuration", flush=True)
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("ci", "deployment"), required=True)
    args = parser.parse_args()
    raise SystemExit(check(args.profile))
