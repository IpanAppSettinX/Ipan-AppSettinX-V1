from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TweakCatalogEntry:
    tweak_id: str
    title: str
    requested_alias: str
    category: str
    safety: str
    action: str
    button_label: str
    rule_ids: tuple[str, ...]
    summary: str
    technical_effect: str
    warning: str
    limitation: str
    source_url: str
    provenance: str
    inspected_items: tuple[str, ...]
    number: int = 0

    def as_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rule_ids"] = list(self.rule_ids)
        return payload


TWEAK_CATALOG: tuple[TweakCatalogEntry, ...] = (
    TweakCatalogEntry(
        tweak_id="system.apply_regedit",
        title="APPLY REGEDIT",
        requested_alias="Pemeriksaan respons multimedia",
        category="Performance",
        safety="caution",
        action="apply",
        button_label="Apply Tweak",
        rule_ids=(),
        number=1,
        summary=(
            "Optimalkan respons PC untuk gaming, streaming, dan aplikasi multimedia "
            "agar aktivitas real-time terasa lebih stabil dan konsisten."
        ),
        technical_effect=(
            "Inspeksi menemukan satu penulisan HKLM, satu pembukaan tautan eksternal, "
            "dan satu perintah antarmuka konsol."
        ),
        warning=(
            "Apply dihentikan karena nilai NoLazyMode tidak memiliki kontrak performa "
            "Windows yang cukup untuk diterapkan secara universal."
        ),
        limitation="Tidak ada perubahan Registry atau tautan eksternal yang dijalankan.",
        source_url="",
        provenance="Inspeksi statis artefak lokal; artefak tidak pernah dijalankan.",
        inspected_items=(
            "Menjaga respons audio, video, dan gameplay tetap konsisten saat PC bekerja berat.",
            "Menyesuaikan optimasi dengan kondisi PC agar hasilnya relevan untuk perangkat Anda.",
            "Hanya menerapkan penyesuaian yang aman dan terverifikasi demi "
            "menjaga stabilitas sistem.",
        ),
    ),
    TweakCatalogEntry(
        tweak_id="cleanup.clean_temp_files",
        title="CLEAN TEMP FILES",
        requested_alias="Pembersihan file temporary",
        category="Cleanup",
        safety="critical",
        action="apply",
        button_label="Apply Tweak",
        rule_ids=(),
        number=2,
        summary=(
            "Bersihkan file sementara yang tidak diperlukan untuk melegakan ruang "
            "penyimpanan dan menjaga PC tetap rapi."
        ),
        technical_effect=(
            "Inspeksi menemukan perintah penghapusan paksa untuk seluruh isi folder TEMP."
        ),
        warning=(
            "Apply dihentikan karena penghapusan rekursif tanpa inventaris, snapshot, "
            "dan validasi file dapat menghilangkan data yang masih dibutuhkan."
        ),
        limitation="Tidak ada file pada PC yang dipindai atau dihapus oleh aksi ini.",
        source_url="",
        provenance="Inspeksi statis artefak lokal; artefak tidak pernah dijalankan.",
        inspected_items=(
            "Menemukan file sementara yang aman dibersihkan untuk membantu "
            "menghemat ruang penyimpanan.",
            "Melindungi file yang masih digunakan agar aplikasi dan game tetap berjalan normal.",
            "Memeriksa setiap target sebelum dibersihkan untuk mencegah kehilangan data penting.",
        ),
    ),
    TweakCatalogEntry(
        tweak_id="system.apply_booster",
        title="APPLY BOOSTER",
        requested_alias="Pemeriksaan konfigurasi boot",
        category="System",
        safety="critical",
        action="apply",
        button_label="Apply Tweak",
        rule_ids=(),
        number=3,
        summary=(
            "Tingkatkan kesiapan dan respons PC melalui pemeriksaan performa yang "
            "disesuaikan dengan hardware, driver, dan kebutuhan gaming Anda."
        ),
        technical_effect=(
            "Inspeksi menemukan 20 perubahan BCDEdit untuk timer, menu boot, debug, "
            "virtualisasi, mitigasi, dan topologi prosesor."
        ),
        warning=(
            "Apply dihentikan karena paket BCD universal dapat mengganggu boot, keamanan, "
            "virtualisasi, dan stabilitas perangkat."
        ),
        limitation="Tidak ada konfigurasi boot yang dibaca atau diubah oleh aksi ini.",
        source_url="https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/bcdedit--set",
        provenance="Inspeksi statis artefak lokal dan batas BCDEdit Microsoft.",
        inspected_items=(
            "Memeriksa kesiapan sistem untuk membantu PC memulai sesi kerja dan "
            "gaming secara stabil.",
            "Menilai konsistensi pemrosesan untuk mendukung frame pacing dan respons aplikasi.",
            "Menjaga kompatibilitas emulator, aplikasi, dan fitur penting yang masih digunakan.",
            "Menyesuaikan rekomendasi dengan hardware dan driver, bukan memakai "
            "preset untuk semua PC.",
        ),
    ),
    TweakCatalogEntry(
        tweak_id="recovery.revert_all_changes",
        title="REVERT ALL CHANGES",
        requested_alias="Pemulihan perubahan",
        category="Recovery",
        safety="safe",
        action="restore",
        button_label="Apply Tweak",
        rule_ids=(),
        number=4,
        summary=(
            "Pulihkan pengaturan PC ke kondisi sebelumnya dengan proses yang aman, "
            "terarah, dan sesuai catatan perangkat Anda."
        ),
        technical_effect=(
            "Inspeksi menemukan 87 penulisan Registry hard-coded dan 18 penghapusan "
            "nilai BCD yang diasumsikan sebagai kondisi awal."
        ),
        warning=(
            "Nilai hard-coded tidak dipakai untuk restore karena kondisi awal setiap PC "
            "berbeda dan harus berasal dari snapshot yang tepat."
        ),
        limitation="Tombol mengarahkan ke Restore; paket restore hard-coded tidak dijalankan.",
        source_url=(
            "https://support.microsoft.com/en-us/windows/use-system-restore-"
            "a5ae3ed9-07c4-fd56-45ee-096777ecd14e"
        ),
        provenance="Inspeksi statis artefak lokal dan mekanisme pemulihan Windows.",
        inspected_items=(
            "Mengembalikan hanya pengaturan yang memiliki catatan kondisi awal yang sesuai.",
            "Membantu memulihkan fungsi perangkat, aplikasi, dan input setelah proses optimasi.",
            "Memeriksa kondisi terbaru agar perubahan penting milik pengguna tidak tertimpa.",
            "Menyediakan jalur pemulihan aman saat data kondisi awal belum tersedia.",
        ),
    ),
    TweakCatalogEntry(
        tweak_id="cleanup.clean_log_files",
        title="CLEAN LOG FILES",
        requested_alias="Pembersihan file log",
        category="Cleanup",
        safety="critical",
        action="apply",
        button_label="Apply Tweak",
        rule_ids=(),
        number=5,
        summary=(
            "Rapikan catatan aplikasi yang sudah tidak diperlukan untuk membantu "
            "menghemat ruang tanpa menghilangkan informasi penting."
        ),
        technical_effect=(
            "Inspeksi menemukan dua perintah penghapusan paksa dan rekursif di home pengguna."
        ),
        warning=(
            "Apply dihentikan karena pola *.log pada seluruh home pengguna terlalu luas "
            "dan dapat menghapus bukti diagnosis atau data aplikasi."
        ),
        limitation="Tidak ada log atau file pengguna yang dipindai maupun dihapus.",
        source_url="",
        provenance="Inspeksi statis artefak lokal; artefak tidak pernah dijalankan.",
        inspected_items=(
            "Menemukan catatan aplikasi lama yang aman ditinjau untuk membantu "
            "merapikan penyimpanan.",
            "Menjaga catatan terbaru yang masih berguna untuk pemeriksaan masalah "
            "dan stabilitas aplikasi.",
            "Melindungi data pribadi dengan membatasi pembersihan hanya pada "
            "target yang telah diperiksa.",
        ),
    ),
)


def list_tweak_catalog() -> list[dict[str, object]]:
    return [entry.as_payload() for entry in TWEAK_CATALOG]


def get_tweak(tweak_id: str) -> TweakCatalogEntry:
    for entry in TWEAK_CATALOG:
        if entry.tweak_id == tweak_id:
            return entry
    raise KeyError("Tweak tidak ditemukan.")
