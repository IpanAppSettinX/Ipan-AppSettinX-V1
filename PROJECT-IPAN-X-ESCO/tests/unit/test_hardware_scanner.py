from __future__ import annotations

from ipan_optimizer.core.hardware_scanner import (
    _BUS_TYPE_MAP,
    _MEDIA_TYPE_MAP,
    _enum_label,
    _gpu_vram_from_registry,
)


class TestEnumLabel:
    def test_known_media_types(self) -> None:
        assert _enum_label(_MEDIA_TYPE_MAP, 3) == "HDD"
        assert _enum_label(_MEDIA_TYPE_MAP, 4) == "SSD"
        assert _enum_label(_MEDIA_TYPE_MAP, 5) == "SCM"

    def test_unknown_media_type_keeps_raw(self) -> None:
        assert _enum_label(_MEDIA_TYPE_MAP, 99) == "99"

    def test_string_integer_input(self) -> None:
        # win32com sometimes returns enum values as str.
        assert _enum_label(_BUS_TYPE_MAP, "17") == "NVMe"
        assert _enum_label(_BUS_TYPE_MAP, "11") == "SATA"
        assert _enum_label(_BUS_TYPE_MAP, "7") == "USB"

    def test_none_value(self) -> None:
        assert _enum_label(_BUS_TYPE_MAP, None) == "None"

    def test_non_numeric_value(self) -> None:
        assert _enum_label(_BUS_TYPE_MAP, "unknown") == "unknown"


class TestGpuVramFromRegistry:
    def test_empty_pnp_returns_zero(self) -> None:
        assert _gpu_vram_from_registry("") == 0
