#!/usr/bin/env python3
"""Cliente hub: INPUT → Limbo → OUTPUT para Sofia ou BodyVision."""

import argparse
import json
import urllib.request

DEFAULT_LIMBO = "http://localhost:8000"


def fetch_json(url, method="GET", data=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers={"Content-Type": "application/json"} if data else {},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    p = argparse.ArgumentParser(description="Hub client INPUT/OUTPUT")
    p.add_argument("app_key", choices=["sofia-education", "bodyvision"])
    p.add_argument("--limbo-url", default=DEFAULT_LIMBO)
    p.add_argument("--action", choices=["input", "output", "sample"], default="output")
    p.add_argument("--file", help="JSON file for input (optional, uses sample if omitted)")
    args = p.parse_args()

    base = args.limbo_url.rstrip("/")

    if args.action == "sample":
        print(json.dumps(fetch_json(f"{base}/api/v1/hub/samples/{args.app_key}"), indent=2, ensure_ascii=False))
        return

    if args.action == "input":
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                payload = json.load(f)
        else:
            payload = fetch_json(f"{base}/api/v1/hub/samples/{args.app_key}")
        result = fetch_json(f"{base}/api/v1/hub/{args.app_key}/input", "POST", payload)
        print("INPUT OK:", json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.action == "output":
        result = fetch_json(f"{base}/api/v1/hub/{args.app_key}/output")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        fetch_json(f"{base}/api/v1/hub/{args.app_key}/output/ack", "POST", {})
        print("\n[ack] OUTPUT consumido pela app.")


if __name__ == "__main__":
    main()
