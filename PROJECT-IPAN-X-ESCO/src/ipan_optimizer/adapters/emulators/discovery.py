from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EmulatorProduct:
    product_id: str
    family: str
    name: str
    version: str | None
    install_location: str | None
    publisher: str | None
    applicability: str
    reason: str


class EmulatorDiscovery:
    """Read-only uninstall inventory; no vendor path or drive is assumed."""

    def discover(self) -> list[EmulatorProduct]:
        if sys.platform != "win32":
            return []
        import winreg

        locations = (
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                winreg.KEY_WOW64_64KEY,
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                winreg.KEY_WOW64_32KEY,
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                0,
            ),
        )
        products: dict[str, EmulatorProduct] = {}
        for hive, subkey, view in locations:
            try:
                root = winreg.OpenKey(
                    hive,
                    subkey,
                    0,
                    winreg.KEY_ENUMERATE_SUB_KEYS | winreg.KEY_QUERY_VALUE | view,
                )
            except OSError:
                continue
            with root:
                for index in range(winreg.QueryInfoKey(root)[0]):
                    try:
                        child_name = winreg.EnumKey(root, index)
                        with winreg.OpenKey(root, child_name, 0, winreg.KEY_QUERY_VALUE) as child:
                            display_name = _query_string(child, "DisplayName")
                            if not display_name:
                                continue
                            folded = display_name.casefold()
                            if "bluestacks" not in folded and "msi app player" not in folded:
                                continue
                            family = (
                                "msi_app_player" if "msi app player" in folded else "bluestacks"
                            )
                            version = _query_string(child, "DisplayVersion")
                            location = _query_string(child, "InstallLocation")
                            publisher = _query_string(child, "Publisher")
                            product_id = f"{family}:{child_name}".casefold()
                            reason = (
                                "Produk ditemukan; schema instance belum divalidasi."
                                if not location or not Path(location).is_dir()
                                else "Produk dan lokasi instalasi ditemukan."
                            )
                            products[product_id] = EmulatorProduct(
                                product_id=product_id,
                                family=family,
                                name=display_name,
                                version=version,
                                install_location=location,
                                publisher=publisher,
                                applicability="UNKNOWN_READ_ONLY",
                                reason=reason,
                            )
                    except OSError:
                        continue
        return sorted(products.values(), key=lambda product: product.name.casefold())


def _query_string(key: Any, name: str) -> str | None:
    import winreg

    try:
        value, value_type = winreg.QueryValueEx(key, name)
    except OSError:
        return None
    if value_type not in {winreg.REG_SZ, winreg.REG_EXPAND_SZ}:
        return None
    return str(value)
