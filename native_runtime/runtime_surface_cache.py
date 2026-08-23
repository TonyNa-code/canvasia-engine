from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Hashable
from time import perf_counter


DEFAULT_SURFACE_CACHE_MAX_ENTRIES = 128
DEFAULT_SURFACE_CACHE_MAX_PIXELS = 24_000_000
SURFACE_CACHE_PROFILE_LIMITS = {
    "mobile_low": {"max_entries": 56, "max_pixels": 8_000_000},
    "web": {"max_entries": 80, "max_pixels": 14_000_000},
    "standard": {"max_entries": 128, "max_pixels": 24_000_000},
    "high_quality_pc": {"max_entries": 180, "max_pixels": 40_000_000},
}


def _surface_pixel_count(surface) -> int:
    try:
        width, height = surface.get_size()
    except (AttributeError, TypeError, ValueError):
        return 0
    return max(0, int(width)) * max(0, int(height))


class NativeSurfaceCache:
    """Bounded LRU cache for expensive, immutable Pygame render surfaces."""

    def __init__(
        self,
        *,
        max_entries: int = DEFAULT_SURFACE_CACHE_MAX_ENTRIES,
        max_pixels: int = DEFAULT_SURFACE_CACHE_MAX_PIXELS,
        timer: Callable[[], float] = perf_counter,
    ) -> None:
        self.max_entries = max(1, int(max_entries))
        self.max_pixels = max(1, int(max_pixels))
        self._entries: OrderedDict[Hashable, tuple[object, int]] = OrderedDict()
        self._pixel_count = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._build_count = 0
        self._build_time_ms = 0.0
        self._max_build_time_ms = 0.0
        self._oversized_bypasses = 0
        self._timer = timer

    def get(self, key: Hashable):
        entry = self._entries.get(key)
        if entry is None:
            self._misses += 1
            return None
        self._entries.move_to_end(key)
        self._hits += 1
        return entry[0]

    def put(self, key: Hashable, surface):
        pixel_count = _surface_pixel_count(surface)
        if pixel_count <= 0:
            return surface
        if pixel_count > self.max_pixels:
            self._oversized_bypasses += 1
            return surface

        previous = self._entries.pop(key, None)
        if previous is not None:
            self._pixel_count -= previous[1]
        self._entries[key] = (surface, pixel_count)
        self._pixel_count += pixel_count
        self._entries.move_to_end(key)
        self._trim()
        return surface

    def get_or_create(self, key: Hashable, factory: Callable[[], object]):
        cached = self.get(key)
        if cached is not None:
            return cached
        started_at = self._timer()
        surface = factory()
        elapsed_ms = max(0.0, (self._timer() - started_at) * 1000)
        self._build_count += 1
        self._build_time_ms += elapsed_ms
        self._max_build_time_ms = max(self._max_build_time_ms, elapsed_ms)
        return self.put(key, surface)

    def clear(self) -> None:
        self._entries.clear()
        self._pixel_count = 0

    def snapshot(self) -> dict:
        requests = self._hits + self._misses
        return {
            "entryCount": len(self._entries),
            "pixelCount": self._pixel_count,
            "estimatedBytes": self._pixel_count * 4,
            "maxEntries": self.max_entries,
            "maxPixels": self.max_pixels,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "buildCount": self._build_count,
            "buildTimeMs": round(self._build_time_ms, 2),
            "averageBuildTimeMs": round(self._build_time_ms / self._build_count, 2) if self._build_count else 0.0,
            "maxBuildTimeMs": round(self._max_build_time_ms, 2),
            "oversizedBypasses": self._oversized_bypasses,
            "hitRatePercent": round(self._hits / requests * 100) if requests else 0,
        }

    def _trim(self) -> None:
        while len(self._entries) > self.max_entries or self._pixel_count > self.max_pixels:
            _, (_, pixel_count) = self._entries.popitem(last=False)
            self._pixel_count -= pixel_count
            self._evictions += 1


def get_native_surface_cache_limits(performance_profile: object) -> dict:
    profile = str(performance_profile or "standard").strip().lower()
    limits = SURFACE_CACHE_PROFILE_LIMITS.get(profile, SURFACE_CACHE_PROFILE_LIMITS["standard"])
    return dict(limits)


def get_runtime_surface_cache(runtime) -> NativeSurfaceCache:
    cache = getattr(runtime, "surface_cache", None)
    if isinstance(cache, NativeSurfaceCache):
        return cache
    cache = NativeSurfaceCache()
    runtime.surface_cache = cache
    return cache


def build_surface_transform_cache_key(
    namespace: str,
    source_surface,
    size: tuple[int, int],
    *,
    flip_x: bool = False,
    rotation_degrees: float = 0.0,
) -> tuple:
    width = max(1, int(size[0]))
    height = max(1, int(size[1]))
    return (
        str(namespace or "surface"),
        id(source_surface),
        width,
        height,
        bool(flip_x),
        round(float(rotation_degrees or 0.0), 3),
    )


def get_cached_transformed_surface(
    cache: NativeSurfaceCache,
    pygame_module,
    source_surface,
    size: tuple[int, int],
    *,
    namespace: str = "transform",
    flip_x: bool = False,
    rotation_degrees: float = 0.0,
):
    safe_size = (max(1, int(size[0])), max(1, int(size[1])))
    key = build_surface_transform_cache_key(
        namespace,
        source_surface,
        safe_size,
        flip_x=flip_x,
        rotation_degrees=rotation_degrees,
    )

    def build_surface():
        transformed = source_surface
        if transformed.get_size() != safe_size:
            transformed = pygame_module.transform.smoothscale(transformed, safe_size)
        if flip_x:
            transformed = pygame_module.transform.flip(transformed, True, False)
        if rotation_degrees:
            transformed = pygame_module.transform.rotate(transformed, float(rotation_degrees))
        return transformed

    return cache.get_or_create(key, build_surface)


__all__ = [
    "DEFAULT_SURFACE_CACHE_MAX_ENTRIES",
    "DEFAULT_SURFACE_CACHE_MAX_PIXELS",
    "NativeSurfaceCache",
    "SURFACE_CACHE_PROFILE_LIMITS",
    "build_surface_transform_cache_key",
    "get_cached_transformed_surface",
    "get_native_surface_cache_limits",
    "get_runtime_surface_cache",
]
