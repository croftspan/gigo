---
id: L3-requests-to-httpx
task_type: code
size_bucket: L
spec_sentence: |
  Port the module below from `requests` to `httpx` (sync API). Preserve all public function signatures and behaviour. Do not switch to async.
role: |
  You are porting a Python module from the `requests` library to `httpx` (sync API only — do not switch to async).
spec: |
  The module below uses `requests.get`, `requests.post`, and `requests.Session()`
  across five call sites. Port every one to the equivalent `httpx` sync API.

  Mapping:
  - `import requests` → `import httpx`
  - `requests.get(url, ...)` → `httpx.get(url, ...)`
  - `requests.post(url, json=..., headers=...)` → `httpx.post(url, json=..., headers=...)`
  - `requests.Session()` → `httpx.Client()`; `.get`, `.post`, `.close` all carry over
  - `response.json()`, `response.status_code`, `response.text`, `response.raise_for_status()` are identical in httpx — no code change inside these calls

  Constraints:
  - Keep every public function signature exactly as-is.
  - Keep behaviour identical for successful calls (same return shape, same error propagation on non-2xx).
  - Do NOT switch to `httpx.AsyncClient` — this is sync only.
  - Do NOT add a context manager around `httpx.Client()` unless the original
    used one with `requests.Session()` (it doesn't — preserve the explicit `.close()` pattern).
  - Remove the `import requests` line. Add `import httpx`.

  ```python
  # http_client.py
  import json
  import time
  from typing import Any

  import requests

  DEFAULT_TIMEOUT = 10.0


  def fetch_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
      """GET a URL, return parsed JSON. Raise for non-2xx."""
      resp = requests.get(url, timeout=timeout)
      resp.raise_for_status()
      return resp.json()


  def fetch_text(url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
      """GET a URL, return .text. Raise for non-2xx."""
      resp = requests.get(url, timeout=timeout)
      resp.raise_for_status()
      return resp.text


  def post_json(
      url: str,
      payload: dict[str, Any],
      headers: dict[str, str] | None = None,
      timeout: float = DEFAULT_TIMEOUT,
  ) -> dict[str, Any]:
      """POST a JSON body, return parsed JSON response."""
      resp = requests.post(
          url,
          json=payload,
          headers=headers or {"Content-Type": "application/json"},
          timeout=timeout,
      )
      resp.raise_for_status()
      return resp.json()


  class ApiClient:
      """Thin wrapper around requests.Session for a single base URL + auth token."""

      def __init__(self, base_url: str, token: str, timeout: float = DEFAULT_TIMEOUT):
          self.base_url = base_url.rstrip("/")
          self.timeout = timeout
          self._session = requests.Session()
          self._session.headers.update({"Authorization": f"Bearer {token}"})

      def get(self, path: str) -> dict[str, Any]:
          resp = self._session.get(
              f"{self.base_url}{path}",
              timeout=self.timeout,
          )
          resp.raise_for_status()
          return resp.json()

      def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
          resp = self._session.post(
              f"{self.base_url}{path}",
              json=payload,
              timeout=self.timeout,
          )
          resp.raise_for_status()
          return resp.json()

      def close(self) -> None:
          self._session.close()


  def retry_get(
      url: str,
      attempts: int = 3,
      backoff: float = 0.5,
      timeout: float = DEFAULT_TIMEOUT,
  ) -> str:
      """GET with simple exponential backoff. Returns response text on success."""
      last_err: Exception | None = None
      for i in range(attempts):
          try:
              resp = requests.get(url, timeout=timeout)
              resp.raise_for_status()
              return resp.text
          except Exception as e:
              last_err = e
              time.sleep(backoff * (2 ** i))
      raise RuntimeError(f"all {attempts} attempts failed: {last_err}")
  ```
acceptance: |
  - No `import requests` remains
  - `import httpx` is present
  - No occurrence of the string `requests.` anywhere in code (comments OK, but preferably gone too)
  - `httpx.get`, `httpx.post`, `httpx.Client` (or their instance-method equivalents) replace every prior call site — at least five substitutions
  - `fetch_json`, `fetch_text`, `post_json`, `retry_get` keep their existing signatures
  - `ApiClient` keeps its existing public signatures: `__init__(self, base_url, token, timeout)`, `get(self, path)`, `post(self, path, payload)`, `close(self)`
  - `ApiClient._session` is assigned an `httpx.Client(...)` instance (field name may change, but the session-like object is httpx-based)
  - Code parses as valid Python 3.12
  - No `AsyncClient` or `async def` anywhere
output_format: |
  - ONLY the ported module inside a single ```python fence
  - No preamble, no trailing prose
mode_hint: |
  httpx sync API is near-drop-in for requests. The one gotcha: `httpx.Client()` takes an optional `headers=...` kwarg, just like `requests.Session.headers.update(...)` — either approach is fine.
verifier: L3.py
---
