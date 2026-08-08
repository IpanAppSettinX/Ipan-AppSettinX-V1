from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AdvancedTweakEntry:
    tweak_id: str
    number: int
    title: str
    category: str
    safety: str
    summary: str
    technical_effect: str
    warning: str


ADVANCED_TWEAK_CATALOG: tuple[AdvancedTweakEntry, ...] = (
    # ── Optimization ──────────────────────────────────────────────
    AdvancedTweakEntry(
        tweak_id="adv.clean_all",
        number=1,
        title="Clean All",
        category="Optimization",
        safety="safe",
        summary="Menghapus file temp, prefetch, dan cache Windows.",
        technical_effect="Membersihkan %TEMP%, Windows\\Temp, Prefetch, dan recent.",
        warning="File cache yang masih dibutuhkan bisa terhapus.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.regedit_optimize",
        number=2,
        title="Regedit Optimize",
        category="Optimization",
        safety="caution",
        summary="Optimasi registry untuk TCP/IP, DNS, dan koneksi jaringan.",
        technical_effect="MaxConnectionsPerServer, TCPNoDelay, Tcp1323Opts, DNS cache tuning.",
        warning="Mengubah parameter jaringan; bisa mempengaruhi konektivitas.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.optimize_cpu",
        number=3,
        title="Optimize CPU",
        category="Optimization",
        safety="caution",
        summary="Disable telemetry, error reporting, SmartScreen, dan service berat.",
        technical_effect="Nonaktifkan Defender telemetry, error reporting, scheduled tasks.",
        warning="Menonaktifkan beberapa fitur keamanan dan diagnostik Windows.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.optimize_gpu",
        number=4,
        title="Optimize GPU",
        category="Optimization",
        safety="caution",
        summary="Mengoptimalkan profil multimedia dan GPU scheduling.",
        technical_effect="GPU Priority=18, SFIO Priority=High, Latency Sensitive=True.",
        warning="TDR level diubah; hang GPU bisa menjadi freeze panjang.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.optimize_ram",
        number=5,
        title="Optimize RAM",
        category="Optimization",
        safety="caution",
        summary="Optimasi memory management, filesystem, dan prefetcher.",
        technical_effect="DisablePagingExecutive=1, Disable Prefetcher/Superfetch, NTFS tuning.",
        warning="Bisa menambah waktu boot pertama setelah restart.",
    ),
    # ── Performance ──────────────────────────────────────────────
    AdvancedTweakEntry(
        tweak_id="adv.set_virtual_ram",
        number=6,
        title="Set Virtual RAM",
        category="Performance",
        safety="caution",
        summary="Mengatur ukuran paging file secara manual.",
        technical_effect="Pagefile.sys diatur ke 4096-5096 MB.",
        warning="Jika RAM fisik kecil, bisa menyebabkan out-of-memory.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.boost_fps",
        number=7,
        title="Boost FPS",
        category="Performance",
        safety="caution",
        summary="Nonaktifkan prefetcher dan superfetch, aktifkan show hidden files.",
        technical_effect="EnablePrefetcher=0, EnableSuperfetch=0, Hidden=1.",
        warning="Warm start aplikasi bisa lebih lambat.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.high_performance",
        number=8,
        title="High Performance Mode",
        category="Performance",
        safety="safe",
        summary="Mengaktifkan power plan High Performance bawaan Windows.",
        technical_effect="powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c.",
        warning="Konsumsi daya meningkat; tidak masalah untuk desktop.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.ultimate_performance",
        number=9,
        title="Ultimate Performance Mode",
        category="Performance",
        safety="caution",
        summary="Menduplikasi power plan Ultimate Performance.",
        technical_effect="powercfg -duplicatescheme e9a42b02-...",
        warning="Hanya tersedia di Windows Pro/Enterprise; konsumsi daya tinggi.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.optimize_tweaks",
        number=10,
        title="Optimize Tweaks",
        category="Performance",
        safety="caution",
        summary="Optimasi gabungan CPU priority, network, dan multimedia profile.",
        technical_effect="IRQ8Priority, NetworkThrottlingIndex=ffffffff, LargeSystemCache.",
        warning="Mengubah banyak parameter sistem sekaligus.",
    ),
    # ── Security (CRITICAL) ──────────────────────────────────────
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_defender",
        number=11,
        title="Turn Off Defender",
        category="Security",
        safety="critical",
        summary="Menonaktifkan Windows Defender dan real-time protection.",
        technical_effect="DisableAntiSpyware=1, WdNisSvc/WinDefend Start=4.",
        warning="CRITICAL: PC tanpa antivirus sangat rentan terhadap malware!",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_update",
        number=12,
        title="Turn Off Windows Update",
        category="Security",
        safety="critical",
        summary="Menonaktifkan Windows Update dan delivery optimization.",
        technical_effect="NoAutoUpdate=1, DODownloadMode=0.",
        warning="CRITICAL: PC tidak menerima patch keamanan penting!",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_firewall",
        number=13,
        title="Turn Off Firewall",
        category="Security",
        safety="critical",
        summary="Menonaktifkan Windows Firewall di semua profil jaringan.",
        technical_effect="mpssvc Start=4, EnableFirewall=0 (semua profil).",
        warning="CRITICAL: PC terekspos ke serangan jaringan tanpa filter!",
    ),
    # ── System ──────────────────────────────────────────────────
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_hyperv",
        number=14,
        title="Turn Off Hyper-V",
        category="System",
        safety="caution",
        summary="Menonaktifkan service Hyper-V dan VM-related.",
        technical_effect="HvHost, vmickvpexchange, vmicshutdown, dst. Start=4.",
        warning="Virtualisasi tidak bisa digunakan sampai diaktifkan kembali.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_notifications",
        number=15,
        title="Turn Off Notifications",
        category="System",
        safety="safe",
        summary="Menonaktifkan service notifikasi dan error reporting.",
        technical_effect="WerSvc, WpnService, WpnUserService Start=4.",
        warning="Notifikasi dari aplikasi tidak akan muncul.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_search",
        number=16,
        title="Turn Off Search",
        category="System",
        safety="caution",
        summary="Menonaktifkan Cortana, Bing search, dan web search.",
        technical_effect="AllowCortana=0, DisableWebSearch=1, BingSearchEnabled=0.",
        warning="Pencarian Start Menu menjadi terbatas.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_telemetry",
        number=17,
        title="Turn Off Telemetry & Data Collection",
        category="System",
        safety="caution",
        summary="Menonaktifkan pengumpulan data telemetry oleh Microsoft.",
        technical_effect="AllowTelemetry=0, AllowDeviceNameInTelemetry=0.",
        warning="Beberapa fitur personalisasi Windows bisa tidak berfungsi.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_bluetooth",
        number=18,
        title="Turn Off Bluetooth",
        category="System",
        safety="caution",
        summary="Menonaktifkan seluruh service Bluetooth.",
        technical_effect="BTAGService, bthserv, BthAvctpSvc Start=4.",
        warning="Perangkat Bluetooth tidak bisa terhubung sampai diaktifkan.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_diagnostic",
        number=19,
        title="Turn Off Diagnostic Data",
        category="System",
        safety="safe",
        summary="Menonaktifkan pelaporan informasi infeksi ke Microsoft.",
        technical_effect="MRT DontReportInfectionInformation=1.",
        warning="Microsoft tidak menerima data diagnostik.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_visual",
        number=20,
        title="Turn Off Visual Effect",
        category="System",
        safety="safe",
        summary="Mengoptimalkan efek visual Windows untuk performa.",
        technical_effect="VisualFXSetting=2, Themes service disabled.",
        warning="Tampilan Windows menjadi lebih sederhana.",
    ),
    # ── Gaming ──────────────────────────────────────────────────
    AdvancedTweakEntry(
        tweak_id="adv.optimize_mouse",
        number=21,
        title="Optimize Sensi Mouse",
        category="Gaming",
        safety="caution",
        summary="Optimasi sensitivitas dan akselerasi mouse untuk gaming.",
        technical_effect="MouseSpeed=0, Threshold=0, Sensitivity=10, linear curve.",
        warning="Rasa pointer desktop berubah sampai di-rollback.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.debloat_windows",
        number=22,
        title="Debloat Windows",
        category="Gaming",
        safety="caution",
        summary="Menghapus aplikasi bawaan Windows yang tidak dibutuhkan.",
        technical_effect=(
            "Hapus AppX bloatware via PackageManager (native, tanpa "
            "powershell.exe): 3DBuilder, Sway, dll."
        ),
        warning="Beberapa app bawaan tidak bisa diinstal ulang dengan mudah.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.boost_all_games",
        number=23,
        title="Boost All Games",
        category="Gaming",
        safety="caution",
        summary="Optimasi gabungan registry untuk semua game.",
        technical_effect="Kombinasi regedit CPU/GPU/RAM + mouse optimization.",
        warning="Banyak parameter berubah; gunakan dengan hati-hati.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.super_optimize_bcedit",
        number=24,
        title="Super Optimize BCEDIT",
        category="Gaming",
        safety="critical",
        summary="Mengubah boot configuration Windows untuk performa.",
        technical_effect="useplatformtick, disabledynamictick, TSC policy.",
        warning="CRITICAL: Bisa menyebabkan boot failure atau instabilitas!",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.delete_onedrive",
        number=25,
        title="Delete OneDrive",
        category="Gaming",
        safety="caution",
        summary="Menghapus instalasi Microsoft OneDrive.",
        technical_effect="Uninstall OneDrive dan hapus folder terkait.",
        warning="Data di OneDrive cloud tidak terpengaruh, tapi sync berhenti.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.speed_up_device",
        number=26,
        title="Speed Up Device",
        category="Gaming",
        safety="caution",
        summary="Gabungan optimasi kecepatan perangkat.",
        technical_effect="Kombinasi network, filesystem, dan memory tuning.",
        warning="Banyak parameter berubah sekaligus.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_store",
        number=27,
        title="Turn Off Microsoft Store",
        category="Gaming",
        safety="caution",
        summary="Menonaktifkan Microsoft Store.",
        technical_effect="Disable Store service dan auto-update apps.",
        warning="Tidak bisa instal atau update app dari Store.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_disk_mgmt",
        number=28,
        title="Turn Off Disk Management Services",
        category="Gaming",
        safety="caution",
        summary="Menonaktifkan service manajemen disk yang tidak perlu.",
        technical_effect="VDS, disk optimization service disabled.",
        warning="Disk management tools mungkin tidak bisa digunakan.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.turn_off_xbox",
        number=29,
        title="Turn Off Xbox Services",
        category="Gaming",
        safety="safe",
        summary="Menonaktifkan service Xbox yang berjalan di background.",
        technical_effect="Xbox service disabled, mengurangi penggunaan resource.",
        warning="Game Pass dan Xbox app tidak bisa digunakan.",
    ),
    AdvancedTweakEntry(
        tweak_id="adv.reduce_latency",
        number=30,
        title="Reduce Windows Desktop Latency",
        category="Gaming",
        safety="caution",
        summary="Mengurangi latency input di desktop Windows.",
        technical_effect="MinAnimate=0, IRQ8Priority=1, HibernateEnabled=0.",
        warning="Beberapa animasi desktop dinonaktifkan.",
    ),
)


def list_advanced_tweaks() -> list[dict[str, object]]:
    return [asdict(entry) for entry in ADVANCED_TWEAK_CATALOG]


def get_advanced_tweak(tweak_id: str) -> AdvancedTweakEntry:
    for entry in ADVANCED_TWEAK_CATALOG:
        if entry.tweak_id == tweak_id:
            return entry
    raise KeyError("Advanced tweak tidak ditemukan.")
