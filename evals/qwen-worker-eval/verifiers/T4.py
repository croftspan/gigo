#!/usr/bin/env python3
"""T4 verifier — JSON to YAML round-trip equality."""

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin

EXPECTED = {
    "service": {
        "name": "auth-api",
        "port": 8080,
        "enabled": True,
        "replicas": 3,
        "tags": ["prod", "eu-west-1", "v2"],
        "env": {
            "LOG_LEVEL": "info",
            "FEATURE_X": False,
            "RETRY_BACKOFF_MS": 250,
        },
        "healthcheck": None,
    }
}


def main() -> None:
    body = extract_fenced(read_stdin(), lang="yaml")
    try:
        parsed = yaml.safe_load(body)
    except yaml.YAMLError as e:
        fail(f"yaml parse error: {e}")
    if parsed != EXPECTED:
        fail(
            f"parsed YAML not equal to expected dict.\n"
            f"got: {json.dumps(parsed, sort_keys=True)}\n"
            f"expected: {json.dumps(EXPECTED, sort_keys=True)}"
        )
    ok("yaml parses and round-trips to the expected JSON")


if __name__ == "__main__":
    main()
