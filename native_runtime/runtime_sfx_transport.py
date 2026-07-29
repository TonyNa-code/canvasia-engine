from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


SFX_FADE_MAX_MS = 60 * 1000
SFX_CHANNEL_IDS = ("effect", "ambience", "ui")
SFX_STOP_CHANNEL_IDS = ("all", *SFX_CHANNEL_IDS)
SFX_RESTART_MODES = ("continue", "restart")


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _normalize_number(value: object, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float(fallback)
    if number != number:
        number = float(fallback)
    return number


def normalize_sfx_volume(value: object, fallback: int = 100) -> int:
    if value in {None, ""}:
        value = fallback
    return int(_clamp(round(_normalize_number(value, fallback)), 0, 100))


def normalize_sfx_fade_ms(value: object, fallback: int = 0) -> int:
    return int(_clamp(round(_normalize_number(value, fallback)), 0, SFX_FADE_MAX_MS))


def sanitize_sfx_channel_id(
    value: object,
    *,
    allow_all: bool = False,
    fallback: str = "effect",
) -> str:
    supported = SFX_STOP_CHANNEL_IDS if allow_all else SFX_CHANNEL_IDS
    safe_fallback = fallback if fallback in supported else ("all" if allow_all else "effect")
    candidate = str(value or "").strip().lower()
    return candidate if candidate in supported else safe_fallback


def sanitize_sfx_transport(source: dict | None = None) -> dict:
    source = source if isinstance(source, dict) else {}
    loop = source.get("loop") is True
    restart_mode = str(source.get("restartMode") or "continue") if loop else "restart"
    if restart_mode not in SFX_RESTART_MODES:
        restart_mode = "continue" if loop else "restart"
    return {
        "channelId": sanitize_sfx_channel_id(source.get("channelId")),
        "loop": loop,
        "restartMode": restart_mode,
        "volume": normalize_sfx_volume(source.get("volume")),
        "fadeInMs": normalize_sfx_fade_ms(source.get("fadeInMs")),
        "replaceFadeOutMs": normalize_sfx_fade_ms(source.get("replaceFadeOutMs")),
    }


def sanitize_sfx_stop(source: dict | None = None) -> dict:
    source = source if isinstance(source, dict) else {}
    return {
        "channelId": sanitize_sfx_channel_id(
            source.get("channelId"),
            allow_all=True,
            fallback="all",
        ),
        "fadeOutMs": normalize_sfx_fade_ms(source.get("fadeOutMs"), 600),
    }


def build_sfx_playback_key(asset_id: object, source: dict | None = None, cue_id: object = "") -> str:
    transport = sanitize_sfx_transport(source)
    parts = [str(asset_id or ""), transport["channelId"], "loop" if transport["loop"] else "once"]
    if transport["restartMode"] == "restart" or not transport["loop"]:
        parts.append(str(cue_id or "cue"))
    return ":".join(parts)


def sanitize_sfx_channel_state_map(source: dict | None = None) -> dict:
    source = source if isinstance(source, dict) else {}
    result: dict[str, dict] = {}
    for channel_id in SFX_CHANNEL_IDS:
        state = source.get(channel_id)
        if not isinstance(state, dict):
            continue
        asset_id = str(state.get("assetId") or "").strip()
        if not asset_id:
            continue
        result[channel_id] = {
            "assetId": asset_id,
            "cueId": str(state.get("cueId") or ""),
            **sanitize_sfx_transport({**state, "channelId": channel_id, "loop": True}),
            "loop": True,
        }
    return result


def apply_sfx_block_to_channel_state(
    source: dict | None,
    block: dict | None,
    *,
    cue_id: object = "",
) -> dict:
    result = sanitize_sfx_channel_state_map(source)
    block = block if isinstance(block, dict) else {}
    block_type = str(block.get("type") or "")
    if block_type == "sfx_stop":
        stop = sanitize_sfx_stop(block)
        if stop["channelId"] == "all":
            return {}
        result.pop(stop["channelId"], None)
        return result
    if block_type != "sfx_play":
        return result
    transport = sanitize_sfx_transport(block)
    asset_id = str(block.get("assetId") or "").strip()
    if not transport["loop"] or not asset_id:
        return result
    result[transport["channelId"]] = {
        "assetId": asset_id,
        "cueId": str(cue_id or block.get("id") or ""),
        **transport,
    }
    return result


@dataclass
class _ActiveSfx:
    asset_id: str
    cue_id: str
    playback_key: str
    transport: dict
    sound: object
    channel: object


class NativeSfxTransportController:
    """Owns native SFX channels without coupling transport rules to the player UI."""

    def __init__(
        self,
        load_sound: Callable[[str], object | None],
        get_master_volume: Callable[[], float] | None = None,
    ) -> None:
        self.load_sound = load_sound
        self.get_master_volume = get_master_volume or (lambda: 1.0)
        self.persistent_channels: dict[str, _ActiveSfx] = {}
        self.one_shots: list[_ActiveSfx] = []

    def _target_volume(self, transport: dict) -> float:
        master = _clamp(_normalize_number(self.get_master_volume(), 1.0), 0.0, 1.0)
        return _clamp(master * (sanitize_sfx_transport(transport)["volume"] / 100), 0.0, 1.0)

    @staticmethod
    def _is_busy(channel: object | None) -> bool:
        try:
            return bool(channel and channel.get_busy())
        except Exception:
            return False

    @staticmethod
    def _stop_channel(channel: object | None, fade_out_ms: int = 0) -> None:
        if not channel:
            return
        try:
            if fade_out_ms > 0 and hasattr(channel, "fadeout"):
                channel.fadeout(fade_out_ms)
            else:
                channel.stop()
        except Exception:
            pass

    def _start(self, asset_id: str, transport: dict, cue_id: str, *, persistent: bool) -> _ActiveSfx | None:
        sound = self.load_sound(asset_id)
        if not sound:
            return None
        try:
            loops = -1 if persistent else 0
            fade_ms = transport["fadeInMs"]
            try:
                channel = sound.play(loops=loops, fade_ms=fade_ms)
            except TypeError:
                channel = sound.play(loops)
            if not channel:
                return None
            channel.set_volume(self._target_volume(transport))
        except Exception:
            return None
        return _ActiveSfx(
            asset_id=asset_id,
            cue_id=cue_id,
            playback_key=build_sfx_playback_key(asset_id, transport, cue_id),
            transport=dict(transport),
            sound=sound,
            channel=channel,
        )

    def prune_finished_one_shots(self) -> None:
        self.one_shots = [entry for entry in self.one_shots if self._is_busy(entry.channel)]

    def play(self, block: dict | None, *, cue_id: object = "") -> bool:
        block = block if isinstance(block, dict) else {}
        asset_id = str(block.get("assetId") or "").strip()
        transport = sanitize_sfx_transport(block)
        safe_cue_id = str(cue_id or block.get("id") or "")
        if not asset_id:
            return False
        self.prune_finished_one_shots()
        if not transport["loop"]:
            entry = self._start(asset_id, transport, safe_cue_id, persistent=False)
            if entry:
                self.one_shots.append(entry)
                return True
            return False

        channel_id = transport["channelId"]
        playback_key = build_sfx_playback_key(asset_id, transport, safe_cue_id)
        current = self.persistent_channels.get(channel_id)
        if current and current.playback_key == playback_key and self._is_busy(current.channel):
            current.transport = dict(transport)
            try:
                current.channel.set_volume(self._target_volume(transport))
            except Exception:
                pass
            return True
        if current:
            self._stop_channel(current.channel, transport["replaceFadeOutMs"])
        entry = self._start(asset_id, transport, safe_cue_id, persistent=True)
        if entry:
            self.persistent_channels[channel_id] = entry
            return True
        self.persistent_channels.pop(channel_id, None)
        return False

    def stop(self, source: dict | None = None) -> None:
        stop = sanitize_sfx_stop(source)
        for channel_id, entry in list(self.persistent_channels.items()):
            if stop["channelId"] in {"all", channel_id}:
                self._stop_channel(entry.channel, stop["fadeOutMs"])
                self.persistent_channels.pop(channel_id, None)
        for entry in list(self.one_shots):
            if stop["channelId"] in {"all", entry.transport["channelId"]}:
                self._stop_channel(entry.channel, stop["fadeOutMs"])
                self.one_shots.remove(entry)

    def update_volumes(self) -> None:
        self.prune_finished_one_shots()
        for entry in [*self.persistent_channels.values(), *self.one_shots]:
            try:
                entry.channel.set_volume(self._target_volume(entry.transport))
            except Exception:
                pass

    def serialize_persistent_channels(self) -> dict:
        return {
            channel_id: {
                "assetId": entry.asset_id,
                "cueId": entry.cue_id,
                **sanitize_sfx_transport({**entry.transport, "loop": True}),
            }
            for channel_id, entry in self.persistent_channels.items()
            if self._is_busy(entry.channel)
        }

    def restore_persistent_channels(self, source: dict | None) -> dict:
        self.stop({"channelId": "all", "fadeOutMs": 0})
        states = sanitize_sfx_channel_state_map(source)
        for state in states.values():
            self.play(state, cue_id=state.get("cueId"))
        return self.serialize_persistent_channels()

    def reset(self) -> None:
        self.stop({"channelId": "all", "fadeOutMs": 0})
