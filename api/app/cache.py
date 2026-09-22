"""A small cache for computed analyses.

Recomputing a takeoff is sub-millisecond, so this is not about speed on one
box: it is about not recomputing the same answer for every viewer of a shared
project, and about having one obvious place to invalidate. Redis when
`SYNAPSE_REDIS_URL` is set, an in-process dict otherwise — the API must run
with nothing else installed, so the fallback is the default, not an error.

The key carries the project's version and its `updated_at`, so an edit
invalidates by construction: nothing has to remember to purge.
"""

from __future__ import annotations

import json
import logging
from collections import OrderedDict

from .config import settings

log = logging.getLogger(__name__)
TTL_SECONDS = 900
MAX_LOCAL = 256

_local: OrderedDict[str, str] = OrderedDict()
_redis = None
_tried = False


def _client():
    global _redis, _tried
    if _tried:
        return _redis
    _tried = True
    url = settings().redis_url
    if not url:
        return None
    try:
        import redis

        _redis = redis.Redis.from_url(url, decode_responses=True, socket_timeout=0.25)
        _redis.ping()
        log.info("Analysis cache: Redis at %s", url.split("@")[-1])
    except Exception as e:                      # unreachable, wrong URL, no package
        log.warning("Redis unavailable (%s); caching in process instead.", e)
        _redis = None
    return _redis


def key_for(project) -> str:
    stamp = getattr(project, "updated_at", None)
    return f"analysis:{project.id}:{project.current_version}:{stamp.isoformat() if stamp else '0'}"


def get(key: str) -> dict | None:
    r = _client()
    if r is not None:
        try:
            raw = r.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None
    raw = _local.get(key)
    if raw is not None:
        _local.move_to_end(key)
    return json.loads(raw) if raw else None


def put(key: str, value: dict) -> None:
    raw = json.dumps(value, default=str)
    r = _client()
    if r is not None:
        try:
            r.setex(key, TTL_SECONDS, raw)
            return
        except Exception:
            pass
    _local[key] = raw
    _local.move_to_end(key)
    while len(_local) > MAX_LOCAL:
        _local.popitem(last=False)


def backend() -> str:
    return "redis" if _client() is not None else "in-process"
