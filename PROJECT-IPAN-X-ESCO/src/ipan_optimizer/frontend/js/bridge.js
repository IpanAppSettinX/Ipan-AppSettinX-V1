const fallbackState = {
  scan: null,
  transaction: null,
  session: null,
  benchmark: null,
};

const fallbackTweaks = [
  {
    tweak_id: "system.apply_regedit",
    title: "APPLY REGEDIT",
    requested_alias: "Pemeriksaan respons multimedia",
    category: "Performance",
    safety: "caution",
    action: "blocked",
    button_label: "Apply Tweak",
    rule_ids: [],
    number: 1,
    summary: "Optimalkan respons PC untuk gaming, streaming, dan aplikasi multimedia agar aktivitas real-time terasa lebih stabil dan konsisten.",
    technical_effect: "Inspeksi menemukan satu penulisan HKLM, satu pembukaan tautan eksternal, dan satu perintah antarmuka konsol.",
    warning: "Apply dihentikan karena nilai NoLazyMode tidak memiliki kontrak performa Windows yang cukup untuk diterapkan secara universal.",
    limitation: "Tidak ada perubahan Registry atau tautan eksternal yang dijalankan.",
    inspected_items: ["Menjaga respons audio, video, dan gameplay tetap konsisten saat PC bekerja berat.", "Menyesuaikan optimasi dengan kondisi PC agar hasilnya relevan untuk perangkat Anda.", "Hanya menerapkan penyesuaian yang aman dan terverifikasi demi menjaga stabilitas sistem."],
  },
  {
    tweak_id: "cleanup.clean_temp_files",
    title: "CLEAN TEMP FILES",
    requested_alias: "Pembersihan file temporary",
    category: "Cleanup",
    safety: "critical",
    action: "blocked",
    button_label: "Apply Tweak",
    rule_ids: [],
    number: 2,
    summary: "Bersihkan file sementara yang tidak diperlukan untuk melegakan ruang penyimpanan dan menjaga PC tetap rapi.",
    technical_effect: "Inspeksi menemukan perintah penghapusan paksa untuk seluruh isi folder TEMP.",
    warning: "Apply dihentikan karena penghapusan rekursif tanpa inventaris, snapshot, dan validasi file dapat menghilangkan data yang masih dibutuhkan.",
    limitation: "Tidak ada file pada PC yang dipindai atau dihapus oleh aksi ini.",
    inspected_items: ["Menemukan file sementara yang aman dibersihkan untuk membantu menghemat ruang penyimpanan.", "Melindungi file yang masih digunakan agar aplikasi dan game tetap berjalan normal.", "Memeriksa setiap target sebelum dibersihkan untuk mencegah kehilangan data penting."],
  },
  {
    tweak_id: "system.apply_booster",
    title: "APPLY BOOSTER",
    requested_alias: "Pemeriksaan konfigurasi boot",
    category: "System",
    safety: "critical",
    action: "blocked",
    button_label: "Apply Tweak",
    rule_ids: [],
    number: 3,
    summary: "Tingkatkan kesiapan dan respons PC melalui pemeriksaan performa yang disesuaikan dengan hardware, driver, dan kebutuhan gaming Anda.",
    technical_effect: "Inspeksi menemukan 20 perubahan BCDEdit untuk timer, menu boot, debug, virtualisasi, mitigasi, dan topologi prosesor.",
    warning: "Apply dihentikan karena paket BCD universal dapat mengganggu boot, keamanan, virtualisasi, dan stabilitas perangkat.",
    limitation: "Tidak ada konfigurasi boot yang dibaca atau diubah oleh aksi ini.",
    inspected_items: ["Memeriksa kesiapan sistem untuk membantu PC memulai sesi kerja dan gaming secara stabil.", "Menilai konsistensi pemrosesan untuk mendukung frame pacing dan respons aplikasi.", "Menjaga kompatibilitas emulator, aplikasi, dan fitur penting yang masih digunakan.", "Menyesuaikan rekomendasi dengan hardware dan driver, bukan memakai preset untuk semua PC."],
  },
  {
    tweak_id: "recovery.revert_all_changes",
    title: "REVERT ALL CHANGES",
    requested_alias: "Pemulihan perubahan",
    category: "Recovery",
    safety: "safe",
    action: "restore",
    button_label: "Apply Tweak",
    rule_ids: [],
    number: 4,
    summary: "Pulihkan pengaturan PC ke kondisi sebelumnya dengan proses yang aman, terarah, dan sesuai catatan perangkat Anda.",
    technical_effect: "Inspeksi menemukan 87 penulisan Registry hard-coded dan 18 penghapusan nilai BCD yang diasumsikan sebagai kondisi awal.",
    warning: "Nilai hard-coded tidak dipakai untuk restore karena kondisi awal setiap PC berbeda dan harus berasal dari snapshot yang tepat.",
    limitation: "Tombol mengarahkan ke Restore; paket restore hard-coded tidak dijalankan.",
    inspected_items: ["Mengembalikan hanya pengaturan yang memiliki catatan kondisi awal yang sesuai.", "Membantu memulihkan fungsi perangkat, aplikasi, dan input setelah proses optimasi.", "Memeriksa kondisi terbaru agar perubahan penting milik pengguna tidak tertimpa.", "Menyediakan jalur pemulihan aman saat data kondisi awal belum tersedia."],
  },
  {
    tweak_id: "cleanup.clean_log_files",
    title: "CLEAN LOG FILES",
    requested_alias: "Pembersihan file log",
    category: "Cleanup",
    safety: "critical",
    action: "blocked",
    button_label: "Apply Tweak",
    rule_ids: [],
    number: 5,
    summary: "Rapikan catatan aplikasi yang sudah tidak diperlukan untuk membantu menghemat ruang tanpa menghilangkan informasi penting.",
    technical_effect: "Inspeksi menemukan dua perintah penghapusan paksa dan rekursif di home pengguna.",
    warning: "Apply dihentikan karena pola *.log pada seluruh home pengguna terlalu luas dan dapat menghapus bukti diagnosis atau data aplikasi.",
    limitation: "Tidak ada log atau file pengguna yang dipindai maupun dihapus.",
    inspected_items: ["Menemukan catatan aplikasi lama yang aman ditinjau untuk membantu merapikan penyimpanan.", "Menjaga catatan terbaru yang masih berguna untuk pemeriksaan masalah dan stabilitas aplikasi.", "Melindungi data pribadi dengan membatasi pembersihan hanya pada target yang telah diperiksa."],
  },
];

const fallbackAdvancedTweaks = [
  { tweak_id: "adv.clean_all", number: 1, title: "Clean All", category: "Optimization", safety: "safe", summary: "Menghapus file temp, prefetch, dan cache Windows.", technical_effect: "Membersihkan %TEMP%, Windows\\Temp, Prefetch.", warning: "File cache bisa terhapus." },
  { tweak_id: "adv.regedit_optimize", number: 2, title: "Regedit Optimize", category: "Optimization", safety: "caution", summary: "Optimasi registry TCP/IP dan DNS.", technical_effect: "MaxConnectionsPerServer, TCPNoDelay, DNS cache tuning.", warning: "Mengubah parameter jaringan." },
  { tweak_id: "adv.optimize_cpu", number: 3, title: "Optimize CPU", category: "Optimization", safety: "caution", summary: "Disable telemetry dan error reporting.", technical_effect: "Nonaktifkan Defender telemetry, error reporting.", warning: "Beberapa fitur diagnostik dinonaktifkan." },
  { tweak_id: "adv.optimize_gpu", number: 4, title: "Optimize GPU", category: "Optimization", safety: "caution", summary: "Mengoptimalkan profil multimedia GPU.", technical_effect: "GPU Priority=18, SFIO Priority=High.", warning: "TDR level bisa berubah." },
  { tweak_id: "adv.optimize_ram", number: 5, title: "Optimize RAM", category: "Optimization", safety: "caution", summary: "Optimasi memory management.", technical_effect: "DisablePagingExecutive=1, Disable Prefetcher.", warning: "Waktu boot bisa lebih lama." },
  { tweak_id: "adv.set_virtual_ram", number: 6, title: "Set Virtual RAM", category: "Performance", safety: "caution", summary: "Mengatur ukuran paging file.", technical_effect: "Pagefile.sys = 4096-5096 MB.", warning: "Out-of-memory jika RAM kecil." },
  { tweak_id: "adv.boost_fps", number: 7, title: "Boost FPS", category: "Performance", safety: "caution", summary: "Nonaktifkan prefetcher dan superfetch.", technical_effect: "EnablePrefetcher=0, EnableSuperfetch=0.", warning: "Warm start lebih lambat." },
  { tweak_id: "adv.high_performance", number: 8, title: "High Performance Mode", category: "Performance", safety: "safe", summary: "Aktifkan power plan High Performance.", technical_effect: "powercfg /setactive High Performance.", warning: "Konsumsi daya meningkat." },
  { tweak_id: "adv.ultimate_performance", number: 9, title: "Ultimate Performance Mode", category: "Performance", safety: "caution", summary: "Duplikasi power plan Ultimate Performance.", technical_effect: "powercfg -duplicatescheme Ultimate.", warning: "Hanya Windows Pro/Enterprise." },
  { tweak_id: "adv.optimize_tweaks", number: 10, title: "Optimize Tweaks", category: "Performance", safety: "caution", summary: "Optimasi gabungan CPU, network, multimedia.", technical_effect: "IRQ8Priority, NetworkThrottlingIndex, LargeSystemCache.", warning: "Banyak parameter berubah." },
  { tweak_id: "adv.turn_off_defender", number: 11, title: "Turn Off Defender", category: "Security", safety: "critical", summary: "Menonaktifkan Windows Defender.", technical_effect: "DisableAntiSpyware=1, WinDefend Start=4.", warning: "CRITICAL: PC rentan malware!" },
  { tweak_id: "adv.turn_off_update", number: 12, title: "Turn Off Windows Update", category: "Security", safety: "critical", summary: "Menonaktifkan Windows Update.", technical_effect: "NoAutoUpdate=1, DODownloadMode=0.", warning: "CRITICAL: Tidak ada patch keamanan!" },
  { tweak_id: "adv.turn_off_firewall", number: 13, title: "Turn Off Firewall", category: "Security", safety: "critical", summary: "Menonaktifkan Windows Firewall.", technical_effect: "mpssvc Start=4, EnableFirewall=0.", warning: "CRITICAL: PC terekspos serangan!" },
  { tweak_id: "adv.turn_off_hyperv", number: 14, title: "Turn Off Hyper-V", category: "System", safety: "caution", summary: "Menonaktifkan service Hyper-V.", technical_effect: "HvHost, vmickvpexchange Start=4.", warning: "Virtualisasi tidak tersedia." },
  { tweak_id: "adv.turn_off_notifications", number: 15, title: "Turn Off Notifications", category: "System", safety: "safe", summary: "Menonaktifkan notifikasi Windows.", technical_effect: "WerSvc, WpnService Start=4.", warning: "Notifikasi tidak muncul." },
  { tweak_id: "adv.turn_off_search", number: 16, title: "Turn Off Search", category: "System", safety: "caution", summary: "Menonaktifkan Cortana dan web search.", technical_effect: "AllowCortana=0, DisableWebSearch=1.", warning: "Pencarian Start terbatas." },
  { tweak_id: "adv.turn_off_telemetry", number: 17, title: "Turn Off Telemetry & Data Collection", category: "System", safety: "caution", summary: "Menonaktifkan telemetry Microsoft.", technical_effect: "AllowTelemetry=0.", warning: "Personalisasi terbatas." },
  { tweak_id: "adv.turn_off_bluetooth", number: 18, title: "Turn Off Bluetooth", category: "System", safety: "caution", summary: "Menonaktifkan service Bluetooth.", technical_effect: "BTAGService, bthserv Start=4.", warning: "Bluetooth tidak tersedia." },
  { tweak_id: "adv.turn_off_diagnostic", number: 19, title: "Turn Off Diagnostic Data", category: "System", safety: "safe", summary: "Menonaktifkan pelaporan diagnostik.", technical_effect: "MRT DontReportInfectionInformation=1.", warning: "Tidak ada data diagnostik ke Microsoft." },
  { tweak_id: "adv.turn_off_visual", number: 20, title: "Turn Off Visual Effect", category: "System", safety: "safe", summary: "Optimasi efek visual untuk performa.", technical_effect: "VisualFXSetting=2, Themes disabled.", warning: "Tampilan lebih sederhana." },
  { tweak_id: "adv.optimize_mouse", number: 21, title: "Optimize Sensi Mouse", category: "Gaming", safety: "caution", summary: "Optimasi sensitivitas mouse gaming.", technical_effect: "MouseSpeed=0, Threshold=0, linear curve.", warning: "Rasa pointer berubah." },
  { tweak_id: "adv.debloat_windows", number: 22, title: "Debloat Windows", category: "Gaming", safety: "caution", summary: "Hapus aplikasi bawaan tidak perlu.", technical_effect: "Remove-AppxPackage bloatware.", warning: "Beberapa app tidak bisa diinstal ulang." },
  { tweak_id: "adv.boost_all_games", number: 23, title: "Boost All Games", category: "Gaming", safety: "caution", summary: "Optimasi registry gabungan untuk gaming.", technical_effect: "Kombinasi CPU/GPU/RAM optimization.", warning: "Banyak parameter berubah." },
  { tweak_id: "adv.super_optimize_bcedit", number: 24, title: "Super Optimize BCEDIT", category: "Gaming", safety: "critical", summary: "Mengubah boot configuration Windows.", technical_effect: "useplatformtick, disabledynamictick, TSC.", warning: "CRITICAL: Bisa boot failure!" },
  { tweak_id: "adv.delete_onedrive", number: 25, title: "Delete OneDrive", category: "Gaming", safety: "caution", summary: "Menghapus Microsoft OneDrive.", technical_effect: "Uninstall OneDrive.", warning: "Sync cloud berhenti." },
  { tweak_id: "adv.speed_up_device", number: 26, title: "Speed Up Device", category: "Gaming", safety: "caution", summary: "Gabungan optimasi kecepatan perangkat.", technical_effect: "Network, filesystem, memory tuning.", warning: "Banyak parameter berubah." },
  { tweak_id: "adv.turn_off_store", number: 27, title: "Turn Off Microsoft Store", category: "Gaming", safety: "caution", summary: "Menonaktifkan Microsoft Store.", technical_effect: "Store service disabled.", warning: "Tidak bisa instal dari Store." },
  { tweak_id: "adv.turn_off_disk_mgmt", number: 28, title: "Turn Off Disk Management Services", category: "Gaming", safety: "caution", summary: "Menonaktifkan service disk management.", technical_effect: "VDS, optimization service disabled.", warning: "Disk management terbatas." },
  { tweak_id: "adv.turn_off_xbox", number: 29, title: "Turn Off Xbox Services", category: "Gaming", safety: "safe", summary: "Menonaktifkan Xbox background services.", technical_effect: "Xbox service disabled.", warning: "Game Pass tidak tersedia." },
  { tweak_id: "adv.reduce_latency", number: 30, title: "Reduce Windows Desktop Latency", category: "Gaming", safety: "caution", summary: "Mengurangi latency input desktop.", technical_effect: "MinAnimate=0, IRQ8Priority=1.", warning: "Animasi desktop dinonaktifkan." },
];

function response(data) {
  return {
    success: true,
    data,
    error: null,
    correlation_id: crypto.randomUUID(),
  };
}

const fallbackApi = {
  async authenticate() {
    return {
      success: false,
      data: null,
      error: { user_message: "Login hanya tersedia melalui aplikasi desktop." },
    };
  },
  async scan_system() {
    fallbackState.scan = {
      scan_id: crypto.randomUUID(),
      captured_at: new Date().toISOString(),
      warnings: [],
      capabilities: {
        "os.platform": { state: "AVAILABLE", value: "Windows 11 fixture", reason: "Fake bridge." },
        "webview2.runtime": { state: "AVAILABLE", value: "fixture", reason: "Fake bridge." },
        "memory.total_mb": { state: "AVAILABLE", value: 16384, reason: "Fake bridge." },
      },
    };
    return response(fallbackState.scan);
  },
  async scan_hardware() {
    return response({
      cpu: { brand: "Intel", model: "Intel Core i7-12700H", cores: 14, threads: 20, base_speed_ghz: 2.3, max_speed_ghz: 4.7 },
      gpu: [{ brand: "NVIDIA", model: "NVIDIA GeForce RTX 3060 Laptop", vram_mb: 6144, driver_version: "536.67" }],
      ram: { total_mb: 16384, modules: [{ manufacturer: "Samsung", capacity_mb: 8192, speed_mhz: 4800, ddr_type: "DDR5" }, { manufacturer: "Samsung", capacity_mb: 8192, speed_mhz: 4800, ddr_type: "DDR5" }], max_speed_mhz: 4800, ddr_type: "DDR5" },
      storage: [{ device_type: "SSD", brand: "Samsung", model: "Samsung SSD 980 PRO 512GB", capacity_gb: 476.9, interface_type: "NVMe" }],
      network: [{ adapter_name: "Wi-Fi 6", link_speed_mbps: 1200 }],
      windows: { version: "Windows 11", build_number: "22631", edition: "Professional", display_version: "23H2", product_name: "Windows 11 Pro" },
    });
  },
  async get_realtime_stats() {
    const t = Date.now() / 1000;
    const cpuBase = 3200;
    const cpuVary = Math.sin(t * 1.7) * 400 + Math.sin(t * 3.1) * 200 + Math.sin(t * 0.7) * 300;
    const gpuBase = 1400;
    const gpuVary = Math.sin(t * 2.3) * 200 + Math.sin(t * 1.1) * 150;
    const cpuLoadBase = 25;
    const cpuLoadVary = Math.sin(t * 0.8) * 18 + Math.sin(t * 2.7) * 10;
    const ramBase = 8192;
    const ramVary = Math.sin(t * 0.4) * 512 + Math.sin(t * 1.3) * 256;
    const cpuTempBase = 55;
    const cpuTempVary = Math.sin(t * 0.5) * 12 + Math.sin(t * 1.9) * 6;
    const ssdTempBase = 38;
    const ssdTempVary = Math.sin(t * 0.3) * 5 + Math.sin(t * 0.7) * 3;
    const gpuTempBase = 62;
    const gpuTempVary = Math.sin(t * 0.6) * 10 + Math.sin(t * 2.1) * 5;
    return response({
      cpu_percent: Math.max(2, Math.min(98, Math.round(cpuLoadBase + cpuLoadVary))),
      cpu_freq_mhz: Math.round(cpuBase + cpuVary),
      gpu_freq_mhz: Math.round(Math.max(300, gpuBase + gpuVary)),
      ram_used_mb: Math.round(ramBase + ramVary),
      ram_percent: Math.round(50 + Math.sin(t * 0.4) * 5),
      cpu_temp_c: Math.round(Math.max(30, cpuTempBase + cpuTempVary)),
      ssd_temp_c: Math.round(Math.max(25, ssdTempBase + ssdTempVary)),
      gpu_temp_c: Math.round(Math.max(35, gpuTempBase + gpuTempVary)),
    });
  },
  async list_recommendations() {
    return response([
      {
        recommendation_id: "rec-game-mode",
        rule_id: "windows.game_mode",
        title: "Tinjau Mode Game",
        reason: "Periksa Mode Game untuk sesi bermain.",
        risk: "safe",
        applicability: "SUPPORTED",
        limitation: "Tidak menjamin kenaikan FPS.",
      },
    ]);
  },
  async list_profiles() {
    return response([
      { profile_id: "gaming-balanced", name: "Gaming Balanced" },
      { profile_id: "safe-daily", name: "Safe Daily" },
    ]);
  },
  async list_tweak_catalog() {
    return response(fallbackTweaks);
  },
  async list_advanced_tweaks() {
    return response(fallbackAdvancedTweaks);
  },
  async apply_advanced_tweak(tweakId) {
    throw new Error(`Tweak ${tweakId} hanya tersedia sebagai analisis.`);
  },
  async apply_gaming_tweak(tweakId) {
    throw new Error(`Tweak ${tweakId} dihentikan oleh pemeriksaan keamanan.`);
  },
  async open_system_restore() {
    return response({ opened: false, target: "rstrui.exe" });
  },
  async preview_transaction(ruleIds) {
    fallbackState.transaction = {
      transaction_id: crypto.randomUUID(),
      rule_ids: ruleIds,
      state: "PLANNED",
      dry_run: true,
      operations: [{ operation: "registry_set", operation_id: "fallback.operation" }],
    };
    return response(fallbackState.transaction);
  },
  async apply_transaction() {
    fallbackState.transaction.state = "VERIFIED";
    return response(fallbackState.transaction);
  },
  async start_apply_transaction() {
    fallbackState.job = {
      job_id: crypto.randomUUID(),
      state: "SUCCEEDED",
      progress: 100,
      message: "Operasi selesai dan hasil tersedia.",
      result: { ...fallbackState.transaction, state: "VERIFIED" },
      error: null,
    };
    fallbackState.transaction.state = "VERIFIED";
    return response(fallbackState.job);
  },
  async get_job_status() {
    return response(fallbackState.job);
  },
  async get_transaction_status() {
    return response(fallbackState.transaction);
  },
  async rollback_transaction() {
    fallbackState.transaction.state = "ROLLED_BACK";
    return response(fallbackState.transaction);
  },
  async list_recovery_items() {
    return response([]);
  },
  async start_game_session(profileId, executableId) {
    fallbackState.session = {
      session_id: crypto.randomUUID(),
      profile_id: profileId,
      executable_id: executableId,
      state: "SAFE_SESSION_ACTIVE",
      message: "Sesi disimulasikan.",
    };
    return response(fallbackState.session);
  },
  async stop_game_session() {
    fallbackState.session.state = "RESTORED";
    return response(fallbackState.session);
  },
  async discover_emulators() {
    return response([]);
  },
  async preview_emulator_profile(instanceId, profileId) {
    return response({ instance_id: instanceId, profile_id: profileId, state: "UNKNOWN_READ_ONLY", message: "Schema tidak dikenal." });
  },
  async apply_emulator_profile(instanceId, profileId) {
    return response({ instance_id: instanceId, profile_id: profileId, state: "UNKNOWN_READ_ONLY", message: "Apply ditolak dengan aman." });
  },
  async verify_emulator_profile(instanceId) {
    return response({ instance_id: instanceId, state: "UNKNOWN_READ_ONLY", message: "Tidak ada perubahan." });
  },
  async restore_emulator_profile(instanceId) {
    return response({ instance_id: instanceId, state: "UNKNOWN_READ_ONLY", message: "Tidak ada snapshot." });
  },
  async start_benchmark(config) {
    fallbackState.benchmark = { benchmark_id: crypto.randomUUID(), state: "GUIDED_READY", config, message: "Belum diukur." };
    return response(fallbackState.benchmark);
  },
  async cancel_benchmark() {
    fallbackState.benchmark.state = "CANCELLED";
    return response(fallbackState.benchmark);
  },
  async compare_benchmarks() {
    return response({ state: "INCONCLUSIVE", message: "Tidak ada perubahan bermakna." });
  },
  async list_activity_events() {
    return response([
      { category: "system", message: "Aplikasi dimulai.", timestamp: new Date().toISOString() },
      { category: "scan", message: "Smart Scan hardware dijalankan.", timestamp: new Date(Date.now() - 300000).toISOString() },
    ]);
  },
  async get_settings() {
    return response({ dry_run: true, language: "id-ID", theme: "dark" });
  },
  async save_settings(settings) {
    if (settings.dry_run !== true) throw new Error("Perubahan sistem nyata belum tersedia.");
    return response(settings);
  },
  async export_diagnostic_report() {
    return response({ path: "diagnostic-report.json" });
  },
  async open_evidence_url(url) {
    return response({ opened: false, url });
  },
  async open_windows_mouse_settings() {
    return response({ opened: false, target: "ms-settings:mousetouchpad" });
  },
  async open_support_url(url) {
    return response({ opened: false, url });
  },
  async minimize_window() {
    return response({ minimized: true });
  },
  async maximize_window() {
    return response({ maximized: true });
  },
  async restore_window() {
    return response({ restored: true });
  },
  async close_window() {
    return response({ closed: true });
  },
  async begin_resize(direction) {
    return response({ resizing: false, direction, reason: "browser" });
  },
};

export async function getApi() {
  if (window.pywebview?.api) {
    return window.pywebview.api;
  }
  return fallbackApi;
}

export async function invoke(method, ...args) {
  const api = await getApi();
  if (typeof api[method] !== "function") {
    throw new Error(`Bridge method tidak tersedia: ${method}`);
  }
  const result = await api[method](...args);
  if (!result?.success) {
    throw new Error(result?.error?.user_message || "Bridge mengembalikan error.");
  }
  return result.data;
}

export async function invokeWithTimeout(method, timeoutMs = 6000, ...args) {
  return Promise.race([
    invoke(method, ...args),
    new Promise((_, reject) =>
      window.setTimeout(
        () => reject(new Error(`Bridge ${method} tidak merespons dalam batas waktu.`)),
        timeoutMs,
      ),
    ),
  ]);
}
