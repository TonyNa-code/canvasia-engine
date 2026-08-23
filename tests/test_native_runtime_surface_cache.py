from __future__ import annotations

import unittest
from types import SimpleNamespace

from native_runtime.runtime_surface_cache import (
    NativeSurfaceCache,
    build_surface_transform_cache_key,
    get_cached_transformed_surface,
    get_native_surface_cache_limits,
    get_runtime_surface_cache,
)


class FakeSurface:
    def __init__(self, size: tuple[int, int], label: str = "surface") -> None:
        self._size = size
        self.label = label

    def get_size(self) -> tuple[int, int]:
        return self._size


class FakeTransform:
    def __init__(self) -> None:
        self.smoothscale_calls = 0
        self.flip_calls = 0
        self.rotate_calls = 0

    def smoothscale(self, surface: FakeSurface, size: tuple[int, int]) -> FakeSurface:
        self.smoothscale_calls += 1
        return FakeSurface(size, f"{surface.label}:scaled")

    def flip(self, surface: FakeSurface, _x: bool, _y: bool) -> FakeSurface:
        self.flip_calls += 1
        return FakeSurface(surface.get_size(), f"{surface.label}:flipped")

    def rotate(self, surface: FakeSurface, degrees: float) -> FakeSurface:
        self.rotate_calls += 1
        return FakeSurface(surface.get_size(), f"{surface.label}:rotated:{degrees}")


class NativeRuntimeSurfaceCacheTests(unittest.TestCase):
    def test_cache_reuses_recent_surface_and_reports_hits(self) -> None:
        cache = NativeSurfaceCache(max_entries=4, max_pixels=1_000)
        surface = FakeSurface((10, 10))
        builds = 0

        def factory() -> FakeSurface:
            nonlocal builds
            builds += 1
            return surface

        first = cache.get_or_create(("panel", 1), factory)
        second = cache.get_or_create(("panel", 1), factory)

        self.assertIs(first, second)
        self.assertEqual(builds, 1)
        self.assertEqual(cache.snapshot()["hits"], 1)
        self.assertEqual(cache.snapshot()["hitRatePercent"], 50)

    def test_cache_evicts_least_recent_surface_by_pixel_budget(self) -> None:
        cache = NativeSurfaceCache(max_entries=8, max_pixels=200)
        cache.put("first", FakeSurface((10, 10), "first"))
        cache.put("second", FakeSurface((10, 10), "second"))
        self.assertEqual(cache.get("first").label, "first")

        cache.put("third", FakeSurface((10, 10), "third"))

        self.assertIsNone(cache.get("second"))
        self.assertEqual(cache.get("first").label, "first")
        self.assertEqual(cache.get("third").label, "third")
        self.assertEqual(cache.snapshot()["evictions"], 1)

    def test_cache_does_not_retain_single_surface_over_budget(self) -> None:
        cache = NativeSurfaceCache(max_entries=4, max_pixels=64)
        surface = FakeSurface((20, 20))

        self.assertIs(cache.put("large", surface), surface)
        self.assertEqual(cache.snapshot()["entryCount"], 0)
        self.assertEqual(cache.snapshot()["oversizedBypasses"], 1)

    def test_cache_measures_successful_surface_builds_without_recounting_hits(self) -> None:
        times = iter((1.0, 1.004))
        cache = NativeSurfaceCache(
            max_entries=4,
            max_pixels=1_000,
            timer=lambda: next(times),
        )

        first = cache.get_or_create("panel", lambda: FakeSurface((10, 10)))
        second = cache.get_or_create("panel", lambda: FakeSurface((20, 20)))
        snapshot = cache.snapshot()

        self.assertIs(first, second)
        self.assertEqual(snapshot["buildCount"], 1)
        self.assertEqual(snapshot["buildTimeMs"], 4.0)
        self.assertEqual(snapshot["averageBuildTimeMs"], 4.0)
        self.assertEqual(snapshot["maxBuildTimeMs"], 4.0)
        self.assertEqual(snapshot["hits"], 1)

    def test_transform_cache_skips_duplicate_scale_flip_and_rotation(self) -> None:
        transform = FakeTransform()
        pygame_module = SimpleNamespace(transform=transform)
        cache = NativeSurfaceCache(max_entries=8, max_pixels=100_000)
        source = FakeSurface((100, 200), "portrait")

        first = get_cached_transformed_surface(
            cache,
            pygame_module,
            source,
            (50, 100),
            namespace="character",
            flip_x=True,
            rotation_degrees=-4,
        )
        second = get_cached_transformed_surface(
            cache,
            pygame_module,
            source,
            (50, 100),
            namespace="character",
            flip_x=True,
            rotation_degrees=-4,
        )

        self.assertIs(first, second)
        self.assertEqual(transform.smoothscale_calls, 1)
        self.assertEqual(transform.flip_calls, 1)
        self.assertEqual(transform.rotate_calls, 1)

    def test_transform_key_changes_for_geometry_and_source(self) -> None:
        first_source = FakeSurface((10, 10))
        second_source = FakeSurface((10, 10))
        base = build_surface_transform_cache_key("sprite", first_source, (20, 20))

        self.assertNotEqual(base, build_surface_transform_cache_key("sprite", first_source, (21, 20)))
        self.assertNotEqual(base, build_surface_transform_cache_key("sprite", second_source, (20, 20)))
        self.assertNotEqual(
            base,
            build_surface_transform_cache_key("sprite", first_source, (20, 20), flip_x=True),
        )

    def test_profile_limits_reduce_memory_for_low_power_targets(self) -> None:
        mobile = get_native_surface_cache_limits("mobile_low")
        standard = get_native_surface_cache_limits("standard")
        high_quality = get_native_surface_cache_limits("high_quality_pc")

        self.assertLess(mobile["max_pixels"], standard["max_pixels"])
        self.assertLess(standard["max_pixels"], high_quality["max_pixels"])
        self.assertEqual(get_native_surface_cache_limits("invalid"), standard)

    def test_runtime_helper_attaches_cache_for_lightweight_render_harnesses(self) -> None:
        runtime = SimpleNamespace()
        first = get_runtime_surface_cache(runtime)
        second = get_runtime_surface_cache(runtime)

        self.assertIs(first, second)
        self.assertIs(runtime.surface_cache, first)


if __name__ == "__main__":
    unittest.main()
