import time
from collections import defaultdict, deque
from collections.abc import Callable
from functools import wraps
from threading import Lock
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class MetricsRegistry:
    """Small in-process latency registry for local quality gates and diagnostics.

    It intentionally stores bounded numeric samples only. Request bodies, SQL, tokens,
    phone numbers, and generated text never enter the registry.
    """

    def __init__(self, sample_limit: int = 500) -> None:
        self._sample_limit = sample_limit
        self._samples: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=sample_limit))
        self._counts: defaultdict[str, int] = defaultdict(int)
        self._errors: defaultdict[str, int] = defaultdict(int)
        self._lock = Lock()

    def observe(self, name: str, duration_ms: float, *, ok: bool = True, label: str | None = None) -> None:
        key = f"{name}:{label}" if label else name
        with self._lock:
            self._samples[key].append(max(duration_ms, 0.0))
            self._counts[key] += 1
            if not ok:
                self._errors[key] += 1

    @staticmethod
    def _percentile(samples: list[float], percentile: float) -> float:
        if not samples:
            return 0.0
        ordered = sorted(samples)
        index = min(len(ordered) - 1, round((len(ordered) - 1) * percentile))
        return round(ordered[index], 2)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            result: dict[str, Any] = {}
            for key, samples in self._samples.items():
                values = list(samples)
                result[key] = {
                    "count": self._counts[key],
                    "errors": self._errors[key],
                    "avg_ms": round(sum(values) / len(values), 2) if values else 0.0,
                    "p50_ms": self._percentile(values, 0.50),
                    "p95_ms": self._percentile(values, 0.95),
                    "max_ms": round(max(values), 2) if values else 0.0,
                    "sample_count": len(values),
                }
            return result

    def reset(self) -> None:
        with self._lock:
            self._samples.clear()
            self._counts.clear()
            self._errors.clear()


metrics = MetricsRegistry()


def observe_duration(name: str, label: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            started = time.perf_counter()
            ok = False
            try:
                result = function(*args, **kwargs)
                ok = True
                return result
            finally:
                metrics.observe(name, (time.perf_counter() - started) * 1000, ok=ok, label=label)

        return wrapped

    return decorator
