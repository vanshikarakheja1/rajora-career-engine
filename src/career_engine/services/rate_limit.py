import json
import logging
from time import monotonic, time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)
local_request_log: dict[str, list[float]] = {}


def upstash_command(rest_url: str, rest_token: str, *parts: object) -> object:
    encoded_parts = "/".join(quote(str(part), safe="") for part in parts)
    request = Request(
        f"{rest_url.rstrip('/')}/{encoded_parts}",
        method="POST",
        headers={"Authorization": f"Bearer {rest_token}"},
    )
    with urlopen(request, timeout=3) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("result")


def allow_with_upstash(
    client_key: str,
    limit: int,
    window_seconds: int,
    rest_url: str,
    rest_token: str,
) -> bool:
    bucket = int(time() // window_seconds)
    redis_key = f"career-engine:rate:{client_key}:{bucket}"
    count = int(upstash_command(rest_url, rest_token, "INCR", redis_key) or 0)
    if count == 1:
        upstash_command(rest_url, rest_token, "EXPIRE", redis_key, window_seconds + 5)
    return count <= limit


def allow_with_memory(client_key: str, limit: int, window_seconds: int) -> bool:
    now = monotonic()
    recent = [
        timestamp
        for timestamp in local_request_log.get(client_key, [])
        if now - timestamp < window_seconds
    ]
    if len(recent) >= limit:
        local_request_log[client_key] = recent
        return False

    recent.append(now)
    local_request_log[client_key] = recent
    return True


def allow_request(
    client_key: str,
    limit: int,
    window_seconds: int,
    upstash_url: str = "",
    upstash_token: str = "",
) -> bool:
    if upstash_url and upstash_token:
        try:
            return allow_with_upstash(client_key, limit, window_seconds, upstash_url, upstash_token)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            logger.warning("Shared rate limiter failed; using local fallback: %s", exc)

    return allow_with_memory(client_key, limit, window_seconds)
