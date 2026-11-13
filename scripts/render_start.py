"""Render entrypoint for Free Claude Code.

What it does, in order:
1. Persists ANTHROPIC_AUTH_TOKEN into FCC's managed config. FCC deliberately
   ignores that variable from the process environment, so without this step the
   public default token would protect the proxy. Refuses to start without one.
2. Starts a background self-ping against the public /health URL every 120s so
   Render's free tier does not spin the service down for inactivity.
3. Runs the normal FCC server (same as ``fcc-server``).
"""

import os
import sys
import threading
import time
import urllib.request

PING_INTERVAL_SECONDS = int(os.environ.get("KEEPALIVE_INTERVAL_SECONDS", "120"))
STARTUP_DELAY_SECONDS = 20
MIN_TOKEN_LENGTH = 24


def _log(message: str) -> None:
    print(f"[render-start] {message}", flush=True)


def seed_managed_config() -> None:
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
    if len(token) < MIN_TOKEN_LENGTH:
        sys.exit(
            "ANTHROPIC_AUTH_TOKEN must be set to a random secret of at least "
            f"{MIN_TOKEN_LENGTH} characters; refusing to start an open proxy."
        )

    from free_claude_code.config.env_files import dotenv_values_from_file
    from free_claude_code.config.env_migrations import atomic_write_managed_config
    from free_claude_code.config.paths import managed_env_path

    path = managed_env_path()
    values = dict(dotenv_values_from_file(path)) if path.is_file() else {}
    values["ANTHROPIC_AUTH_TOKEN"] = token
    values["PROXY_AUTH_ENABLED"] = "true"
    atomic_write_managed_config(values, path=path)
    _log("Proxy authentication enabled with the configured token.")


def health_url() -> str:
    # The public URL routes through Render's proxy, which counts as inbound
    # traffic; a localhost ping would not keep the instance awake.
    base = os.environ.get("RENDER_EXTERNAL_URL") or (
        f"http://127.0.0.1:{os.environ.get('PORT', '8082')}"
    )
    return base.rstrip("/") + "/health"


def keepalive_loop(url: str, interval: float, startup_delay: float) -> None:
    time.sleep(startup_delay)
    while True:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "fcc-keepalive"})
            with urllib.request.urlopen(request, timeout=15) as response:
                _log(f"self-ping {url} -> {response.status}")
        except Exception as exc:  # never let the pinger die
            _log(f"self-ping {url} failed: {exc}")
        time.sleep(interval)


def main() -> None:
    seed_managed_config()
    threading.Thread(
        target=keepalive_loop,
        args=(health_url(), PING_INTERVAL_SECONDS, STARTUP_DELAY_SECONDS),
        name="fcc-keepalive",
        daemon=True,
    ).start()
    _log(f"Keep-alive pinging {health_url()} every {PING_INTERVAL_SECONDS}s.")

    from free_claude_code.cli.entrypoints import serve

    serve([])


if __name__ == "__main__":
    main()
