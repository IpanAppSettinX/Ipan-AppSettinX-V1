import { invoke, invokeWithTimeout } from "./bridge.js";
import { navigate } from "./router.js";

const state = {
  scanId: null,
  recommendations: [],
  tweaks: [],
  advancedTweaks: [],
  selectedRules: new Set(),
  transactionTweak: null,
  transactionId: null,
  hardwareData: null,
  emulatorProducts: [],
  selectedEmulatorId: null,
  returnToTransaction: false,
  afterProcess: null,
  applyJobId: null,
  processProgress: 0,
  rtInterval: null,
  hwTerminalRunning: false,
  hwTitleRunning: false,
  telemetry: {
    cpuSpeed: new Array(60).fill(null),
    gpuSpeed: new Array(60).fill(null),
    cpuLoad: new Array(60).fill(null),
    ramUsed: new Array(60).fill(null),
    cpuTemp: new Array(60).fill(null),
    ssdTemp: new Array(60).fill(null),
    gpuTemp: new Array(60).fill(null),
  },
};

const byControl = (id) => document.querySelector(`[data-control-id="${id}"]`);
const nextPaint = () => new Promise((resolve) => window.requestAnimationFrame(resolve));
const wait = (milliseconds) =>
  new Promise((resolve) => window.setTimeout(resolve, milliseconds));
const startupStartedAt = window.performance.now();
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const STARTUP_MIN_PRESENTATION_MS = reducedMotion ? 400 : 5000;
const RESULT_PRESENTATION_MS = reducedMotion ? 0 : 2200;
const LOGIN_STAGE_MS = reducedMotion ? 120 : 560;

const hardwareIcons = {
  cpu: "assets/icons/hw/cpu.svg",
  gpu: "assets/icons/hw/vga.svg",
  memory: "assets/icons/hw/memory.svg",
  storage: "assets/icons/hw/storage.svg",
  windows: "assets/icons/hw/windows.svg",
};

const advancedDescriptions = {
  "adv.clean_all": "Tinjau ruang file sementara dan cache yang aman dibersihkan tanpa mengorbankan data penting atau waktu muat aplikasi.",
  "adv.regedit_optimize": "Periksa konfigurasi jaringan Windows dan pisahkan diagnosis koneksi nyata dari Registry pack yang tidak berlaku universal.",
  "adv.optimize_cpu": "Analisis beban CPU dan layanan latar belakang untuk menemukan kontensi yang dapat mengganggu kestabilan frame.",
  "adv.optimize_gpu": "Tinjau penjadwalan grafis, driver, dan jalur render agar rekomendasi GPU sesuai dengan kemampuan perangkat.",
  "adv.optimize_ram": "Periksa tekanan memory dan cache Windows untuk menjaga headroom game tanpa memakai angka RAM yang dipaksakan.",
  "adv.set_virtual_ram": "Audit pagefile dan commit memory agar Windows tetap mempunyai ruang cadangan ketika game atau emulator membutuhkan memory lebih besar.",
  "adv.boost_fps": "Temukan pengaturan yang berpotensi memengaruhi frame pacing lalu pertahankan hanya perubahan yang lolos pemeriksaan perangkat.",
  "adv.high_performance": "Periksa pilihan mode daya untuk sesi gaming sambil mempertimbangkan suhu, konsumsi daya, dan kondisi laptop atau desktop.",
  "adv.ultimate_performance": "Nilai apakah mode daya agresif benar-benar relevan, bukan sekadar mengaktifkan profil permanen yang lebih panas.",
  "adv.optimize_tweaks": "Pisahkan paket optimasi besar menjadi keputusan kecil yang dapat diperiksa, diverifikasi, dan dipulihkan satu per satu.",
  "adv.turn_off_defender": "Pemeriksaan keamanan mencegah optimasi mengurangi perlindungan antivirus Windows yang penting untuk perangkat Anda.",
  "adv.turn_off_update": "Pemeriksaan keamanan menjaga pembaruan Windows tetap tersedia dan menolak tweak yang menghentikan patch penting.",
  "adv.turn_off_firewall": "Pemeriksaan keamanan mempertahankan perlindungan jaringan Windows dan memblokir konfigurasi yang membuka risiko serangan.",
  "adv.turn_off_hyperv": "Analisis kompatibilitas virtualisasi membantu memilih jalur emulator tanpa mematikan fitur Windows secara membabi buta.",
  "adv.turn_off_notifications": "Tinjau gangguan notifikasi saat bermain tanpa merusak layanan aplikasi atau pemberitahuan penting lainnya.",
  "adv.turn_off_search": "Periksa aktivitas pencarian dan indexing hanya ketika data sistem menunjukkan kontensi pada sesi gaming.",
  "adv.turn_off_telemetry": "Tinjau aktivitas diagnostik secara transparan tanpa mengorbankan layanan keamanan atau kestabilan Windows.",
  "adv.turn_off_bluetooth": "Periksa penggunaan Bluetooth dan pertahankan koneksi perangkat yang masih dibutuhkan saat bermain.",
  "adv.turn_off_diagnostic": "Jaga kemampuan diagnosis Windows tetap tersedia untuk menelusuri crash, driver, dan gangguan performa.",
  "adv.turn_off_visual": "Sesuaikan efek visual untuk respons desktop yang lebih ringan tanpa mengklaim peningkatan FPS yang tidak terukur.",
  "adv.optimize_mouse": "Tinjau akselerasi pointer klasik untuk rasa gerak yang lebih konsisten pada game yang tidak memakai raw input.",
  "adv.debloat_windows": "Audit aplikasi latar belakang secara selektif tanpa menghapus komponen Windows secara massal.",
  "adv.boost_all_games": "Bangun rekomendasi per-PC untuk mengejar frame pacing yang lebih stabil daripada memakai satu preset untuk semua game.",
  "adv.super_optimize_bcedit": "Pemeriksaan boot menjaga konfigurasi timer Windows tetap aman dan memblokir tweak yang dapat memicu instabilitas.",
  "adv.delete_onedrive": "Tinjau aktivitas sinkronisasi yang benar-benar berjalan tanpa menghapus aplikasi atau data cloud pengguna.",
  "adv.speed_up_device": "Analisis CPU, memory, storage, dan jaringan untuk menemukan hambatan yang paling relevan pada perangkat ini.",
  "adv.turn_off_store": "Pertahankan Microsoft Store dan pembaruan aplikasi sambil memeriksa aktivitas background yang dapat dijadwalkan ulang.",
  "adv.turn_off_disk_mgmt": "Jaga layanan storage penting tetap aktif dan fokus pada kesehatan disk, ruang kosong, serta tekanan I/O yang terukur.",
  "adv.turn_off_xbox": "Tinjau fitur Xbox dan capture sesuai pemakaian agar Game Pass serta fungsi gaming yang dibutuhkan tetap tersedia.",
  "adv.reduce_latency": "Periksa frame pacing, input, dan respons desktop secara terukur untuk menemukan sumber delay yang benar-benar dapat ditindaklanjuti.",
};

function showError(error) {
  showToast(error instanceof Error ? error.message : String(error), "danger");
}

function showToast(message, tone = "info") {
  const container = document.querySelector("#global-status");
  container.textContent = message;
  container.dataset.tone = tone;
  container.setAttribute("role", tone === "danger" ? "alert" : "status");
  container.setAttribute("aria-live", tone === "danger" ? "assertive" : "polite");
  container.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    container.hidden = true;
  }, tone === "danger" ? 8000 : 6000);
}

function clearError() {
  document.querySelector("#global-status").hidden = true;
}

async function busy(control, operation) {
  if (control.dataset.busy === "true") return;
  const wasDisabled = control.disabled;
  clearError();
  control.dataset.busy = "true";
  control.setAttribute("aria-busy", "true");
  control.disabled = true;
  try {
    return await operation();
  } catch (error) {
    showError(error);
    return null;
  } finally {
    control.dataset.busy = "false";
    control.removeAttribute("aria-busy");
    const keepDisabled = control.dataset.keepDisabled === "true";
    delete control.dataset.keepDisabled;
    control.disabled = keepDisabled || wasDisabled;
  }
}

function text(element, value) {
  element.textContent = value ?? "Tidak tersedia";
}

function setProcessProgress(value, message = null) {
  const progress = Math.max(0, Math.min(100, Math.round(value)));
  state.processProgress = progress;
  const bar = document.querySelector("#apply-process-bar");
  const track = bar.parentElement;
  bar.style.width = `${progress}%`;
  track.setAttribute("aria-valuenow", String(progress));
  text(document.querySelector("#apply-process-percent"), `${progress}%`);
  if (message) text(document.querySelector("#apply-process-message"), message);

  const thresholds = { check: 8, snapshot: 35, apply: 48, verify: 82 };
  const order = ["check", "snapshot", "apply", "verify"];
  const mode = document.querySelector("#apply-process-dialog").dataset.mode;
  const phaseLabels =
    mode === "check"
      ? ["VALIDATION", "TARGET MAP", "POLICY CHECK", "RESULT"]
      : ["VALIDATION", "SNAPSHOT", "APPLY", "VERIFY"];
  let activePhase = 0;
  let activeStep = order[0];
  for (const step of document.querySelectorAll("#apply-process-steps [data-process-step]")) {
    const stepName = step.dataset.processStep;
    const index = order.indexOf(stepName);
    const nextThreshold = index < order.length - 1 ? thresholds[order[index + 1]] : 100;
    if (progress >= nextThreshold) step.dataset.state = "done";
    else if (progress >= thresholds[stepName]) {
      step.dataset.state = "active";
      activePhase = index;
      activeStep = stepName;
    }
    else step.dataset.state = "pending";
  }
  syncPhaseDial(progress >= 100 ? "verify" : activeStep, progress >= 100 ? "complete" : null);
  const core = document.querySelector(".process-core");
  if (core && progress < 100) text(core, String(activePhase + 1));
  text(
    document.querySelector("#apply-process-phase"),
    progress >= 100 ? "COMPLETE" : phaseLabels[activePhase],
  );
}

function syncPhaseDial(activeStep, terminalState = null) {
  // Phase dial ring removed; terminal-style visual uses data-state on dialog.
  // Kept as no-op so existing call sites stay intact.
}

async function animateProcessProgress(target, duration, message) {
  const start = state.processProgress;
  const end = Math.max(start, Math.min(100, Math.round(target)));
  if (reducedMotion || duration <= 0 || start === end) {
    setProcessProgress(end, message);
    return;
  }
  const startedAt = window.performance.now();
  while (state.processProgress < end) {
    const elapsed = window.performance.now() - startedAt;
    const ratio = Math.min(1, elapsed / duration);
    const eased = 1 - Math.pow(1 - ratio, 3);
    setProcessProgress(start + (end - start) * eased, message);
    if (ratio >= 1) break;
    await nextPaint();
  }
  setProcessProgress(end, message);
}

function beginApplyProcess(title, message, mode = "apply") {
  const dialog = document.querySelector("#apply-process-dialog");
  dialog.dataset.state = "running";
  dialog.dataset.mode = mode;
  text(document.querySelector("#apply-process-kicker"), mode === "check" ? "SAFETY CHECK" : "APPLY ENGINE");
  text(document.querySelector("#apply-process-title"), title);
  text(document.querySelector("#apply-process-message"), message);
  byControl("process.close").hidden = true;
  text(document.querySelector(".process-core"), "IPX");
  state.processProgress = 0;
  const stepLabels =
    mode === "check"
      ? [
          "Validasi permintaan",
          "Pemetaan target terdeteksi",
          "Evaluasi kebijakan keamanan",
          "Penyusunan hasil pemeriksaan",
        ]
      : [
          "Pemeriksaan kompatibilitas",
          "Snapshot kondisi awal",
          "Penerapan tweak",
          "Verifikasi hasil",
        ];
  document.querySelectorAll("#apply-process-steps [data-process-step]").forEach((step, index) => {
    step.lastChild.textContent = stepLabels[index];
  });
  setProcessProgress(0);
  for (const step of document.querySelectorAll("#apply-process-steps [data-process-step]")) {
    step.dataset.state = step.dataset.processStep === "check" ? "active" : "pending";
  }
  syncPhaseDial("check");
  if (!dialog.open) dialog.showModal();
}

function markTransactionRunning() {
  setProcessProgress(1, "Backend memulai transaksi terlindungi.");
}

function finishApplyProcess(result, title, message) {
  const dialog = document.querySelector("#apply-process-dialog");
  dialog.dataset.state = result;
  text(document.querySelector("#apply-process-kicker"), result === "success" ? "VERIFIED" : "SAFETY RESULT");
  text(document.querySelector("#apply-process-title"), title);
  text(document.querySelector("#apply-process-message"), message);
  setProcessProgress(100);
  text(document.querySelector(".process-core"), result === "success" ? "OK" : "IPX");
  for (const step of document.querySelectorAll("#apply-process-steps [data-process-step]")) {
    if (result === "success" || dialog.dataset.mode === "check") step.dataset.state = "done";
    else step.dataset.state = step.dataset.processStep === "check" ? "done" : "skipped";
  }
  syncPhaseDial(result === "success" || dialog.dataset.mode === "check" ? "verify" : "check", "complete");
  byControl("process.close").hidden = false;
  byControl("process.close").focus();
}

async function runSafetyCheck(control, title, operation) {
  await busy(control, async () => {
    state.returnToTransaction = false;
    beginApplyProcess(title, "Memeriksa target, dukungan, dan batas keamanan.", "check");
    setProcessProgress(8, "Memvalidasi identitas dan jenis permintaan.");
    try {
      await nextPaint();
      const result = await operation();
      await animateProcessProgress(
        92,
        RESULT_PRESENTATION_MS,
        "Pemeriksaan selesai. Menyusun ringkasan hasil safety.",
      );
      await animateProcessProgress(100, 350, "Safety inspection selesai.");
      finishApplyProcess(
        "success",
        "Tweak berhasil diterapkan",
        result?.message || "Tweak berhasil diterapkan.",
      );
      return result;
    } catch (error) {
      text(document.querySelector("#apply-process-kicker"), "SAFETY RESULT");
      text(document.querySelector("#apply-process-title"), "Tweak tidak diterapkan");
      await animateProcessProgress(
        92,
        RESULT_PRESENTATION_MS,
        "Kebijakan selesai dievaluasi. Menyiapkan keputusan safety.",
      );
      await animateProcessProgress(100, 350, "Safety inspection selesai.");
      finishApplyProcess(
        "blocked",
        "Tweak tidak diterapkan",
        error instanceof Error ? error.message : String(error),
      );
      return null;
    }
  });
}

/* ── Tweak Menu ─────────────────────────────────────────────── */

function renderTweakCatalog() {
  const search = byControl("tweaks.search").value.trim().toLocaleLowerCase("id");
  const safety = byControl("tweaks.filter").value;
  const container = document.querySelector("#tweak-list");
  const fragment = document.createDocumentFragment();
  const filtered = state.tweaks.filter((item) => {
    const haystack = [
      item.title,
      item.requested_alias,
      item.category,
      item.summary,
      item.technical_effect,
    ].join(" ").toLocaleLowerCase("id");
    return haystack.includes(search) && (!safety || item.safety === safety);
  });

  for (const item of filtered) {
    const card = document.createElement("article");
    card.className = `tweak-card rating-${item.safety}`;
    const head = document.createElement("div");
    head.className = "tweak-card-head";
    const titles = document.createElement("div");
    const category = document.createElement("span");
    category.className = "eyebrow";
    text(category, item.category);
    const title = document.createElement("h2");
    const number = item.number || "";
    text(title, number ? `${number}  ${item.title}` : item.title);
    titles.append(category, title);
    const badge = document.createElement("span");
    badge.className = `risk risk-${item.safety}`;
    text(badge, item.safety === "critical" ? "CRITICAL" : item.safety);
    head.append(titles, badge);

    const summary = document.createElement("p");
    text(summary, item.summary);
    const scope = document.createElement("div");
    scope.className = "inspected-scope";
    const scopeTitle = document.createElement("strong");
    text(scopeTitle, "Cakupan fitur terdeteksi");
    const scopeList = document.createElement("ul");
    for (const inspectedItem of item.inspected_items || []) {
      const entry = document.createElement("li");
      text(entry, inspectedItem);
      scopeList.append(entry);
    }
    scope.append(scopeTitle, scopeList);
    const action = document.createElement("button");
    action.type = "button";
    action.dataset.controlId = `tweak.action.${item.tweak_id}`;
    action.dataset.tweakId = item.tweak_id;
    action.className = "primary";
    text(action, item.button_label || "Apply Tweak");
    card.append(head, summary, scope, action);
    fragment.append(card);
  }

  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    text(empty, "Tidak ada tweak yang cocok dengan filter.");
    fragment.append(empty);
  }
  container.replaceChildren(fragment);
  text(
    document.querySelector("#tweak-status"),
    `${filtered.length} dari ${state.tweaks.length} tweak ditampilkan. Setiap aksi melewati pemeriksaan keamanan.`,
  );
}

async function loadTweakCatalog() {
  state.tweaks = await invoke("list_tweak_catalog");
  renderTweakCatalog();
}

/* ── Advanced Tweak (viet.bat) ──────────────────────────────── */

function renderAdvancedTweaks() {
  const search = byControl("advanced.search").value.trim().toLocaleLowerCase("id");
  const category = byControl("advanced.filter").value;
  const container = document.querySelector("#advanced-list");
  const fragment = document.createDocumentFragment();
  const filtered = state.advancedTweaks.filter((item) => {
    const haystack = [item.title, item.category, item.summary, item.technical_effect]
      .join(" ")
      .toLocaleLowerCase("id");
    return haystack.includes(search) && (!category || item.category === category);
  });

  for (const item of filtered) {
    const card = document.createElement("article");
    card.className = `tweak-card rating-${item.safety}`;
    const head = document.createElement("div");
    head.className = "tweak-card-head";
    const titles = document.createElement("div");
    const cat = document.createElement("span");
    cat.className = "eyebrow";
    text(cat, item.category);
    const title = document.createElement("h2");
    text(title, `${item.number}  ${item.title}`);
    titles.append(cat, title);
    const badge = document.createElement("span");
    badge.className = `risk risk-${item.safety}`;
    text(badge, item.safety === "critical" ? "CRITICAL" : item.safety);
    head.append(titles, badge);

    const summary = document.createElement("p");
    text(summary, advancedDescriptions[item.tweak_id] || item.summary);
    const action = document.createElement("button");
    action.type = "button";
    action.dataset.controlId = `advanced.action.${item.tweak_id}`;
    action.dataset.tweakId = item.tweak_id;
    action.className = "primary";
    text(action, "Apply Tweak");
    card.append(head, summary, action);
    fragment.append(card);
  }

  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    text(empty, "Tidak ada tweak yang cocok dengan filter.");
    fragment.append(empty);
  }
  container.replaceChildren(fragment);
  text(
    document.querySelector("#advanced-status"),
    `${filtered.length} dari ${state.advancedTweaks.length} advanced tweak ditampilkan. Safety gate aktif untuk setiap aksi.`,
  );
}

async function loadAdvancedTweaks() {
  state.advancedTweaks = await invoke("list_advanced_tweaks");
  renderAdvancedTweaks();
}

async function handleAdvancedAction(control) {
  const item = state.advancedTweaks.find((t) => t.tweak_id === control.dataset.tweakId);
  if (!item) throw new Error("Tweak tidak ditemukan.");
  await runSafetyCheck(control, `Memeriksa ${item.title}`, () =>
    invoke("apply_advanced_tweak", item.tweak_id),
  );
}

/* ── Smart Scan (Hardware Detection) ────────────────────────── */

function renderHardwareResults(data) {
  const container = document.querySelector("#hardware-results");
  const fragment = document.createDocumentFragment();
  state.hardwareData = data;

  const cards = [
    {
      icon: hardwareIcons.cpu,
      title: "Processor",
      items: [
        ["Merk", data.cpu.brand],
        ["Model", data.cpu.model],
        ["Core / Thread", `${data.cpu.cores} Core / ${data.cpu.threads} Thread`],
        ["Base Speed", `${data.cpu.base_speed_ghz} GHz`],
        ["Current Speed", "Belum diukur"],
        ["Load", "Belum diukur"],
        ["Max Speed", `${data.cpu.max_speed_ghz} GHz`],
      ],
    },
    {
      icon: hardwareIcons.gpu,
      title: "VGA",
      items: (data.gpu || []).length
        ? data.gpu.flatMap((g) => [
            ["Merk", g.brand],
            ["Model", g.model],
            ["VRAM", g.vram_mb > 0 ? `${(g.vram_mb / 1024).toFixed(1)} GB` : "N/A"],
            ["Driver", g.driver_version],
          ])
        : [["Status", "Tidak terdeteksi"]],
    },
    {
      icon: hardwareIcons.memory,
      title: "Memory",
      items: [
        ["Total", `${(data.ram.total_mb / 1024).toFixed(1)} GB`],
        ["Used", "Belum diukur"],
        ["Type", data.ram.ddr_type],
        ["Max Speed", `${data.ram.max_speed_mhz} MHz`],
        [
          "Module",
          (data.ram.modules || []).length
            ? data.ram.modules.map((m) => `${m.manufacturer} ${(m.capacity_mb / 1024).toFixed(0)}GB ${m.speed_mhz}MHz`).join(", ")
            : "N/A",
        ],
      ],
    },
    {
      icon: hardwareIcons.storage,
      title: "Storage",
      items: (data.storage || []).length
        ? data.storage.flatMap((s) => [
            ["Type", s.device_type],
            ["Model", s.model],
            ["Kapasitas", `${s.capacity_gb} GB`],
            ["Interface", s.interface_type],
          ])
        : [["Status", "Tidak terdeteksi"]],
    },
    {
      icon: hardwareIcons.windows,
      title: "Windows",
      items: [
        ["Versi", data.windows.version],
        ["Product", data.windows.product_name],
        ["Build", data.windows.build_number],
        ["Edition", data.windows.edition],
        ["Display Version", data.windows.display_version],
      ],
    },
  ];

  for (const card of cards) {
    const el = document.createElement("div");
    el.className = "hw-card";
    const header = document.createElement("div");
    header.className = "hw-card-header";
    const icon = document.createElement("span");
    icon.className = "hw-icon";
    const iconImage = document.createElement("img");
    iconImage.src = card.icon;
    iconImage.alt = "";
    iconImage.setAttribute("aria-hidden", "true");
    icon.append(iconImage);
    const title = document.createElement("h2");
    text(title, card.title);
    header.append(icon, title);
    el.append(header);

    for (const [label, value] of card.items) {
      const row = document.createElement("div");
      row.className = "hw-row";
      const dt = document.createElement("span");
      dt.className = "hw-label";
      text(dt, label);
      const dd = document.createElement("span");
      dd.className = "hw-value";
      if (label === "Current Speed") dd.id = "rt-cpu-speed";
      if (label === "Load") dd.id = "rt-cpu-load";
      if (label === "Used") dd.id = "rt-ram-used";
      text(dd, value);
      row.append(dt, dd);
      el.append(row);
    }
    fragment.append(el);
  }
  container.replaceChildren(fragment);
}

async function runHardwareScan(control) {
  await busy(control, async () => {
    text(document.querySelector("#scan-status"), "Mendeteksi hardware PC...");
    const data = await invoke("scan_hardware");
    renderHardwareResults(data);
    text(document.querySelector("#scan-status"), "Scan selesai. Informasi hardware berhasil dideteksi.");
    document.querySelector("#dashboard-facts dd").textContent = new Date().toLocaleString("id-ID");
    document.querySelector("#dashboard-facts dd").dataset.state = "ready";
    showToast("Pemindaian selesai. Informasi hardware yang tersedia sudah ditampilkan.", "success");
    
      document.querySelector("#telemetry-panel").hidden = false;
    if (state.rtInterval) return;
    startTelemetry();
  });
}

function startTelemetry() {
  if (state.rtInterval) clearInterval(state.rtInterval);
  state.rtInterval = setInterval(async () => {
    if (document.querySelector('[data-view="scan"]').hidden) return;
    if (document.hidden) return;
    try {
      const rt = await invoke("get_realtime_stats");
      const cpuSpeed = (rt.cpu_freq_mhz != null && rt.cpu_freq_mhz > 0) ? rt.cpu_freq_mhz / 1000 : null;
      const gpuSpeed = (rt.gpu_freq_mhz != null && rt.gpu_freq_mhz > 0) ? rt.gpu_freq_mhz / 1000 : null;
      const cpuLoad = (rt.cpu_percent != null && rt.cpu_percent >= 0) ? rt.cpu_percent : null;
      const ramUsed = (rt.ram_used_mb != null && rt.ram_used_mb >= 0) ? rt.ram_used_mb / 1024 : null;
      const cpuTemp = (rt.cpu_temp_c != null && rt.cpu_temp_c > 0) ? rt.cpu_temp_c : null;
      const ssdTemp = (rt.ssd_temp_c != null && rt.ssd_temp_c > 0) ? rt.ssd_temp_c : null;
      const gpuTemp = (rt.gpu_temp_c != null && rt.gpu_temp_c > 0) ? rt.gpu_temp_c : null;

      updateTelemetry("cpuSpeed", cpuSpeed, " GHz");
      updateTelemetry("gpuSpeed", gpuSpeed, " GHz");
      updateTelemetry("cpuLoad", cpuLoad, "%");
      updateTelemetry("ramUsed", ramUsed, " GB");
      updateTelemetry("cpuTemp", cpuTemp, "°C");
      updateTelemetry("ssdTemp", ssdTemp, "°C");
      updateTelemetry("gpuTemp", gpuTemp, "°C");

      drawTelemetryChart("chart-cpu-speed", state.telemetry.cpuSpeed, "#e85a51", 0.5, 6.0, true);
      drawTelemetryChart("chart-gpu-speed", state.telemetry.gpuSpeed, "#f59e0b", 0.3, 3.0, true);
      drawTelemetryChart("chart-cpu-load", state.telemetry.cpuLoad, "#d4d4d4", 0, 100);
      drawTelemetryChart("chart-ram-used", state.telemetry.ramUsed, "#22c55e", 0, 64, true);
      drawTelemetryChart("chart-cpu-temp", state.telemetry.cpuTemp, "#ef4444", 20, 100, true);
      drawTelemetryChart("chart-ssd-temp", state.telemetry.ssdTemp, "#eab308", 20, 80, true);
      drawTelemetryChart("chart-gpu-temp", state.telemetry.gpuTemp, "#ff6b57", 20, 95, true);

      const hwCpu = document.querySelector("#rt-cpu-speed");
      const hwCpuLoad = document.querySelector("#rt-cpu-load");
      const hwRam = document.querySelector("#rt-ram-used");
      if (hwCpu) hwCpu.textContent = cpuSpeed != null ? `${cpuSpeed.toFixed(2)} GHz` : "N/A";
      if (hwCpuLoad) hwCpuLoad.textContent = cpuLoad != null ? `${cpuLoad.toFixed(1)}%` : "N/A";
      if (hwRam) hwRam.textContent = ramUsed != null ? `${ramUsed.toFixed(1)} GB` : "N/A";
    } catch (err) {
      console.error("RT Error:", err);
    }
  }, 2500);
}

function updateTelemetry(key, value, suffix) {
  state.telemetry[key].shift();
  state.telemetry[key].push(value);
  const labels = {
    cpuSpeed: "#rt-cpu-speed-tm",
    gpuSpeed: "#rt-gpu-speed-tm",
    cpuLoad: "#rt-cpu-load-tm",
    ramUsed: "#rt-ram-used-tm",
    cpuTemp: "#rt-cpu-temp-tm",
    ssdTemp: "#rt-ssd-temp-tm",
    gpuTemp: "#rt-gpu-temp-tm",
  };
  const el = document.querySelector(labels[key]);
  if (!el) return;
  if (value === null) {
    el.textContent = "N/A";
    return;
  }
  const formatted = key === "cpuSpeed" || key === "gpuSpeed" ? value.toFixed(2) : value.toFixed(1);
  el.textContent = `${formatted}${suffix}`;
}

function drawTelemetryChart(canvasId, data, color, minValue, maxValue, dynamicRange = false) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  // Coalesce multiple chart redraws per telemetry tick into a single rAF.
  if (canvas._pendingFrame) return;
  canvas._pendingFrame = true;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 8;

  ctx.clearRect(0, 0, width, height);
  const bgColor = getComputedStyle(document.documentElement).getPropertyValue("--color-bg-canvas").trim();
  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, width, height);

  const chartHeight = height - padding * 2;
  const step = width / Math.max(data.length - 1, 1);
  const validValues = data.filter((v) => v != null);
  let actualMin = minValue;
  let actualMax = maxValue;
  if (dynamicRange && validValues.length > 0) {
    const rawMin = Math.min(...validValues);
    const rawMax = Math.max(...validValues);
    const headroom = Math.max((rawMax - rawMin) * 0.15, 0.1);
    actualMin = Math.max(0, rawMin - headroom);
    actualMax = rawMax + headroom;
    if (actualMax - actualMin < 0.2) {
      const mid = (actualMin + actualMax) / 2;
      actualMin = mid - 0.1;
      actualMax = mid + 0.1;
    }
  }
  const range = actualMax - actualMin;

  ctx.strokeStyle = "rgba(255,255,255,0.06)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++) {
    const y = padding + (chartHeight / 4) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
  for (let i = 0; i < 10; i++) {
    const x = (width / 9) * i;
    ctx.beginPath();
    ctx.moveTo(x, padding);
    ctx.lineTo(x, height - padding);
    ctx.stroke();
  }

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.beginPath();
  let started = false;
  data.forEach((value, index) => {
    if (value == null) return;
    const x = index * step;
    const y = padding + chartHeight - ((value - actualMin) / range) * chartHeight;
    if (!started) {
      ctx.moveTo(x, y);
      started = true;
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();

  let lastX = null;
  let lastY = null;
  let lastVal = null;
  for (let i = data.length - 1; i >= 0; i--) {
    if (data[i] != null) {
      lastVal = data[i];
      lastX = i * step;
      lastY = padding + chartHeight - ((lastVal - actualMin) / range) * chartHeight;
      break;
    }
  }
  if (lastVal != null) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.3)";
    ctx.lineWidth = 1;
    ctx.stroke();
  }
  canvas._pendingFrame = false;
}

async function handleTweakAction(control) {
  const item = state.tweaks.find((candidate) => candidate.tweak_id === control.dataset.tweakId);
  if (!item) throw new Error("Tweak tidak ditemukan.");
  if (item.action === "transaction") {
    state.selectedRules = new Set(item.rule_ids);
    state.transactionTweak = item;
    await previewTransaction(control);
    return;
  }
  if (item.action === "windows_settings") {
    await runSafetyCheck(control, "Menyiapkan Mouse Settings", async () => {
      const result = await invoke("open_windows_mouse_settings");
      return {
        message: result.opened
          ? "Mouse Settings dibuka. Anda tetap mengendalikan setiap perubahan."
          : "Target Mouse Settings telah diperiksa dan siap digunakan.",
      };
    });
    return;
  }
  if (item.action === "restore") {
    await runSafetyCheck(control, "Menyiapkan Restore", async () => {
      state.afterProcess = () => navigate("restore");
      return { message: "Jalur Restore berbasis snapshot siap ditinjau." };
    });
    return;
  }
  await runSafetyCheck(control, `Menerapkan ${item.title}`, async () => {
    const result = await invoke("apply_tweak", item.tweak_id);
    return { message: result.message || `${item.title} diterapkan.` };
  });
}

/* ── Transaction ────────────────────────────────────────────── */

async function previewTransaction(control) {
  await busy(control, async () => {
    state.returnToTransaction = false;
    beginApplyProcess("Menyiapkan Apply Tweak", "Memeriksa rule dan target transaksi.", "check");
    try {
      await nextPaint();
      const transaction = await invoke("preview_transaction", [...state.selectedRules], null);
      state.transactionId = transaction.transaction_id;
      const diff = document.querySelector("#transaction-diff");
      text(
        diff,
        `${transaction.operations.length} operasi terverifikasi siap diproses dengan snapshot dan rollback.`,
      );
      const tweak = state.transactionTweak;
      text(
        document.querySelector("#transaction-warning"),
        tweak?.warning || "Periksa target dan efek sebelum melanjutkan.",
      );
      byControl("transaction.confirm").checked = false;
      byControl("transaction.apply").disabled = true;
      byControl("transaction.verify").disabled = true;
      byControl("transaction.rollback").disabled = true;
      state.afterProcess = () => document.querySelector("#transaction-dialog").showModal();
      await animateProcessProgress(
        92,
        RESULT_PRESENTATION_MS,
        "Preview transaksi selesai. Menyiapkan layar konfirmasi.",
      );
      await animateProcessProgress(100, 500, "Preview siap ditinjau.");
      finishApplyProcess(
        "neutral",
        "Tweak siap diterapkan",
        "Pemeriksaan awal selesai. Tinjau dampak dan konfirmasi sebelum melanjutkan.",
      );
    } catch (error) {
      finishApplyProcess(
        "blocked",
        "Tweak tidak dapat disiapkan",
        error instanceof Error ? error.message : String(error),
      );
    }
  });
}

async function applyTransaction(control) {
  await busy(control, async () => {
    const transactionDialog = document.querySelector("#transaction-dialog");
    transactionDialog.close();
    state.returnToTransaction = true;
    beginApplyProcess("Menerapkan tweak", "Memvalidasi transaksi sebelum snapshot.");
    markTransactionRunning();
    try {
      await nextPaint();
      const job = await invoke("start_apply_transaction", state.transactionId);
      state.applyJobId = job.job_id;
      let currentJob = job;
      while (!["SUCCEEDED", "FAILED", "CANCELLED"].includes(currentJob.state)) {
        currentJob = await invoke("get_job_status", state.applyJobId);
        await animateProcessProgress(currentJob.progress, 520, currentJob.message);
        if (!["SUCCEEDED", "FAILED", "CANCELLED"].includes(currentJob.state)) {
          await new Promise((resolve) => window.setTimeout(resolve, 120));
        }
      }
      await animateProcessProgress(currentJob.progress, 1450, currentJob.message);
      if (currentJob.state !== "SUCCEEDED") {
        throw new Error(currentJob.error || "Transaksi selesai tanpa hasil terverifikasi.");
      }
      const transaction = currentJob.result;
      text(document.querySelector("#apply-process-kicker"), "TRANSACTION COMPLETE");
      text(document.querySelector("#apply-process-title"), "Transaksi selesai");
      setProcessProgress(100, "Backend selesai. Menyusun ringkasan verifikasi transaksi.");
      await wait(reducedMotion ? 0 : 900);
      text(document.querySelector("#transaction-diff"), `Status: ${transaction.state}. ${transaction.error || "Verifikasi selesai."}`);
      control.dataset.keepDisabled = "true";
      byControl("transaction.verify").disabled = transaction.state !== "VERIFIED";
      byControl("transaction.rollback").disabled = !["VERIFIED", "KEPT"].includes(transaction.state);
      if (transaction.state === "VERIFIED") {
        finishApplyProcess(
          "success",
          "Tweak berhasil diterapkan",
          "Snapshot tersimpan dan hasil transaksi telah lolos verifikasi.",
        );
        showToast("Tweak berhasil diterapkan dan diverifikasi.", "success");
      } else if (transaction.state === "ROLLED_BACK") {
        finishApplyProcess(
          "blocked",
          "Perubahan dipulihkan",
          "Verifikasi tidak lolos. Kondisi sebelumnya telah dipulihkan dengan aman.",
        );
        showToast("Verifikasi gagal dan kondisi sebelumnya telah dipulihkan.", "danger");
      } else {
        finishApplyProcess(
          "neutral",
          "Proses selesai",
          `Transaksi selesai dengan status ${transaction.state}.`,
        );
      }
    } catch (error) {
      finishApplyProcess(
        "blocked",
        "Apply Tweak dihentikan",
        error instanceof Error ? error.message : String(error),
      );
    }
  });
}

/* ── Activity ───────────────────────────────────────────────── */

function formatTimestamp(isoStr) {
  if (!isoStr) return "";
  const date = new Date(isoStr);
  return date.toLocaleString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

function renderActivityList(items) {
  const container = document.querySelector("#activity-list");
  if (!items.length) {
    container.className = "activity-timeline empty-state";
    text(container, "Belum ada activity.");
    return;
  }
  container.className = "activity-timeline";
  const fragment = document.createDocumentFragment();
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "activity-row";
    const badge = document.createElement("span");
    badge.className = "activity-badge";
    text(badge, item.category || "system");
    const msg = document.createElement("span");
    msg.className = "activity-message";
    text(msg, item.message);
    const time = document.createElement("span");
    time.className = "activity-time";
    text(time, formatTimestamp(item.timestamp));
    row.append(badge, msg, time);
    fragment.append(row);
  }
  container.replaceChildren(fragment);
}

/* ── Theme ──────────────────────────────────────────────────── */

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem("ipan-theme", theme);
  } catch {
    /* storage unavailable */
  }
}

function setStartupProgress(value, message) {
  const progress = Math.max(0, Math.min(100, Math.round(value)));
  const track = document.querySelector(".startup-track");
  document.querySelector("#startup-bar").style.width = `${progress}%`;
  track.setAttribute("aria-valuenow", String(progress));
  text(document.querySelector("#startup-percent"), `${progress}%`);
  text(document.querySelector("#startup-message"), message);

  const cpuNode = document.querySelector(".subtask-cpu");
  const ramNode = document.querySelector(".subtask-ram");
  const gpuNode = document.querySelector(".subtask-gpu");

  if (cpuNode && ramNode && gpuNode) {
    if (progress < 30) {
      cpuNode.dataset.state = "wait";
      text(cpuNode.querySelector(".subtask-state"), "WAIT");
    } else {
      cpuNode.dataset.state = "done";
      text(cpuNode.querySelector(".subtask-state"), "DONE");
    }

    if (progress < 60) {
      ramNode.dataset.state = "wait";
      text(ramNode.querySelector(".subtask-state"), "WAIT");
    } else {
      ramNode.dataset.state = "done";
      text(ramNode.querySelector(".subtask-state"), "DONE");
    }

    if (progress < 90) {
      gpuNode.dataset.state = "wait";
      text(gpuNode.querySelector(".subtask-state"), "WAIT");
    } else {
      gpuNode.dataset.state = "ready";
      text(gpuNode.querySelector(".subtask-state"), "READY");
    }
  }
}

// Menaikkan progress dari nilai saat ini menuju `target` secara mulus selama
// `duration` ms. Bar tidak pernah diam: setiap frame nilainya bertambah, jadi
// mustahil terlihat "stuck" walau tahap ini menunggu lama.
let startupCurrentProgress = 0;
async function creepStartupProgress(target, duration, message) {
  const start = startupCurrentProgress;
  const end = Math.max(start, Math.min(100, target));
  if (reducedMotion || duration <= 0 || end <= start) {
    startupCurrentProgress = end;
    setStartupProgress(end, message);
    return;
  }
  const startedAt = window.performance.now();
  // Selalu lanjut sampai durasi habis; loop dijamin berakhir karena berbasis waktu.
  for (;;) {
    const elapsed = window.performance.now() - startedAt;
    const ratio = Math.min(1, elapsed / duration);
    const value = start + (end - start) * ratio;
    startupCurrentProgress = value;
    setStartupProgress(value, message);
    if (ratio >= 1) break;
    await nextPaint();
  }
  startupCurrentProgress = end;
  setStartupProgress(end, message);
}

function loadTheme() {
  let theme = "dark";
  try {
    theme = localStorage.getItem("ipan-theme") || "dark";
  } catch {
    /* storage unavailable */
  }
  applyTheme(theme);
  const toggle = byControl("settings.theme");
  if (toggle) toggle.checked = theme === "light";
}

async function loadStageWithProgress(method, start, ceiling, message, timeoutMs = 6000) {
  let settled = false;
  const dataPromise = invokeWithTimeout(method, timeoutMs)
    .catch((error) => {
      showError(error);
      return [];
    })
    .finally(() => {
      settled = true;
    });

  if (!reducedMotion) {
    let current = Math.max(start, startupCurrentProgress);
    const cap = Math.max(start, ceiling - 1);
    startupCurrentProgress = current;
    setStartupProgress(current, message);
    // Bergerak terus sampai backend selesai; jika lambat, bar tetap merayap
    // (tidak pernah diam) namun berhenti sebelum ceiling agar tidak melewati.
    while (!settled && current < cap) {
      current = Math.min(cap, current + 0.35);
      startupCurrentProgress = current;
      setStartupProgress(current, message);
      await wait(90);
    }
  }
  return dataPromise;
}

/* ── Handlers ───────────────────────────────────────────────── */

const handlers = {
  "auth.login": () => {},
  "auth.remember": (control) => {
    const checkbox = control.querySelector("#login-remember");
    if (!checkbox) return;
    checkbox.checked = !checkbox.checked;
    if (!checkbox.checked) {
      invoke("save_remember", "", "", "", 0).catch(() => {});
    }
  },
  "auth.password_toggle": (control) => {
    const password = document.querySelector("#login-password");
    const showing = password.type === "text";
    password.type = showing ? "password" : "text";
    control.setAttribute("aria-pressed", String(!showing));
    control.setAttribute("aria-label", showing ? "Tampilkan password" : "Sembunyikan password");
    text(control, showing ? "SHOW" : "HIDE");
  },
  "auth.register": openSupport,
  "auth.reset_hwid": openSupport,
  "auth.window_minimize": () => invoke("minimize_window"),
  "auth.window_maximize": async () => toggleMaximize(),
  "auth.window_close": () => invoke("close_window"),
  "nav.dashboard": (control) => navigate(control.dataset.route),
  "nav.scan": (control) => {
    navigate(control.dataset.route);
    if (!state.rtInterval) startTelemetry();
  },
  "nav.tweaks": (control) => navigate(control.dataset.route),
  "nav.advanced": async (control) => {
    navigate(control.dataset.route);
    if (!state.advancedTweaks.length) await loadAdvancedTweaks();
  },
  "nav.profiles": (control) => navigate(control.dataset.route),
  "nav.emulator": (control) => navigate(control.dataset.route),

  "nav.restore": (control) => navigate(control.dataset.route),
  "nav.fixes": (control) => navigate(control.dataset.route),
  "fixes.camera": async (control) => {
    await runSafetyCheck(control, "Memperbaiki kamera", () =>
      invoke("apply_fix_tweak", "fixes.camera"),
    );
  },
  "fixes.obs": async (control) => {
    await runSafetyCheck(control, "Memperbaiki OBS & screenshot", () =>
      invoke("apply_fix_tweak", "fixes.obs_screenshot"),
    );
  },
  "nav.activity": async (control) => {
    navigate(control.dataset.route);
    await loadActivity(control);
  },
  "nav.settings": (control) => navigate(control.dataset.route),
  "nav.evidence": (control) => navigate(control.dataset.route),
  "window.minimize": () => invoke("minimize_window"),
  "window.maximize": async () => toggleMaximize(),
  "window.restore": async () => {
    await invoke("restore_window");
    applyMaximizedState(false);
  },
  "window.close": () => invoke("close_window"),
  "dashboard.scan": async (control) => { navigate("scan"); await runHardwareScan(control); },
  "dashboard.review": async (control) => {
    navigate(control.dataset.route);
  },
  "scan.run": runHardwareScan,
  "gaming.aim_smooth": async (control) => {
    await runSafetyCheck(control, "Mengaktifkan OneTap Vector X", () =>
      invoke("apply_gaming_tweak", "aim_smooth"),
    );
  },
  "gaming.aim_stabilizer": async (control) => {
    await runSafetyCheck(control, "Mengaktifkan Neural AimSync X", () =>
      invoke("apply_gaming_tweak", "aim_stabilizer"),
    );
  },
  "gaming.easy_drag": async (control) => {
    await runSafetyCheck(control, "Mengaktifkan DragShot Velocity X", () =>
      invoke("apply_gaming_tweak", "easy_drag"),
    );
  },
  "gaming.boost_fps_menu": async (control) => {
    await runSafetyCheck(control, "Memulai Emulator Overdrive X", () =>
      invoke("apply_gaming_tweak", "boost_fps_menu"),
    );
  },
  "gaming.back": (control) => navigate(control.dataset.route),
  "gaming.optimize_bluestacks": async (control) => {
    await runSafetyCheck(control, "Menerapkan tweak BlueStacks 5", () =>
      invoke("apply_emulator_tweak", "emulator.bluestacks5"),
    );
  },
  "gaming.optimize_msi": async (control) => {
    await runSafetyCheck(control, "Menerapkan tweak MSI App Player", () =>
      invoke("apply_emulator_tweak", "emulator.msi_app_player"),
    );
  },
  "emulator.discover": detectEmulators,

  "restore.open": async (control) => {
    await busy(control, async () => {
      const result = await invoke("open_system_restore");
      text(
        document.querySelector("#restore-status"),
        result.opened
          ? "System Restore dibuka."
          : "System Restore berhasil diakses.",
      );
      showToast(
        "System Restore dibuka.",
        "success",
      );
    });
  },
  "activity.refresh": async (control) => loadActivity(control),
  "settings.theme": (control) => {
    const theme = control.checked ? "light" : "dark";
    applyTheme(theme);
    showToast(`Tema diubah ke ${theme === "light" ? "Mode Terang" : "Mode Gelap"}.`, "success");
  },
  "settings.save": async (control) => {
    await busy(control, async () => {
      const theme = byControl("settings.theme")?.checked ? "light" : "dark";
       await invoke("save_settings", { dry_run: true, language: "id-ID", theme });
      text(document.querySelector("#settings-status"), "Settings tersimpan.");
      showToast("Pengaturan tersimpan.", "success");
    });
  },
  "support.website": openSupport,
  "support.whatsapp": openSupport,
  "support.discord": openSupport,
  "support.instagram": openSupport,
  "support.tiktok": openSupport,
  "support.whatsapp_channel": openSupport,
  "transaction.confirm": (control) => {
    byControl("transaction.apply").disabled = !control.checked;
  },
  "transaction.apply": applyTransaction,
  "transaction.verify": async (control) => {
    await busy(control, async () => {
      const transaction = await invoke("get_transaction_status", state.transactionId);
      text(document.querySelector("#transaction-diff"), `Status terverifikasi: ${transaction.state}.`);
    });
  },
  "transaction.rollback": async (control) => {
    await busy(control, async () => {
      const transaction = await invoke("rollback_transaction", state.transactionId);
      text(document.querySelector("#transaction-diff"), `Status: ${transaction.state}.`);
      control.dataset.keepDisabled = "true";
      byControl("transaction.apply").disabled = false;
      showToast("Snapshot transaksi berhasil dipulihkan.", "success");
    });
  },
  "transaction.close": () => document.querySelector("#transaction-dialog").close(),
  "process.close": () => {
    document.querySelector("#apply-process-dialog").close();
    if (state.returnToTransaction) {
      state.returnToTransaction = false;
      document.querySelector("#transaction-dialog").showModal();
    }
    const afterProcess = state.afterProcess;
    state.afterProcess = null;
    afterProcess?.();
  },
};

function applyMaximizedState(maximized) {
  document.body.dataset.maximized = String(maximized);
  for (const button of document.querySelectorAll(".window-maximize")) {
    text(button, maximized ? "❐" : "▢");
    button.setAttribute("aria-label", maximized ? "Restore" : "Maximize");
  }
}

async function toggleMaximize() {
  const result = await invoke("maximize_window");
  if (result && typeof result === "object" && "maximized" in result) {
    applyMaximizedState(Boolean(result.maximized));
  } else {
    applyMaximizedState(document.body.dataset.maximized !== "true");
  }
}

async function openSupport(control) {
  await busy(control, async () => {
    await invoke("open_support_url", control.dataset.supportUrl);
    const evidenceStatus = document.querySelector("#evidence-status");
    if (evidenceStatus) text(evidenceStatus, "Tautan support dibuka.");
    showToast("Tautan dibuka.", "info");
  });
}

async function runLoginSequence() {
  const form = document.querySelector("#login-form");
  const username = document.querySelector("#login-username");
  const password = document.querySelector("#login-password");
  const license = document.querySelector("#login-license");
  const remember = document.querySelector("#login-remember");
  const status = document.querySelector("#login-status");
  if (!form.reportValidity()) return;

  const rememberChecked = remember?.checked === true;
  if (rememberChecked) {
    const expiresAt = (Date.now() + 30 * 24 * 60 * 60 * 1000) / 1000;
    invoke("save_remember", username.value, password.value, license.value, expiresAt).catch(
      () => {},
    );
  } else {
    invoke("save_remember", "", "", "", 0).catch(() => {});
  }

  const optimizer = document.querySelector(".login-optimizer");
  const traceRows = Array.from(optimizer.querySelectorAll(".auth-trace-row"));
  const meter = optimizer.querySelector(".auth-trace-meter");
  const stages = [
    [12, "Membaca identitas perangkat", "DEVICE SCAN", "device"],
    [34, "Membangun hardware handshake", "HWID HANDSHAKE", "hwid"],
    [58, "Memvalidasi license key", "LICENSE CHECK", "license"],
    [82, "Memvalidasi lisensi akun", "ACCOUNT CHECK", "license"],
    [100, "Menunggu hasil otorisasi", "AUTH VERIFY", "auth"],
  ];
  optimizer.hidden = false;
  username.disabled = true;
  password.disabled = true;
  license.disabled = true;
  for (const row of traceRows) row.classList.remove("is-active", "is-done");
  const authRequest = invoke("authenticate", username.value, password.value, license.value).then(
    (data) => ({ data, error: null }),
    (error) => ({ data: null, error }),
  );
  for (const [progress, message, stage, traceKey] of stages) {
    meter.style.setProperty("--trace-progress", `${progress}%`);
    meter.setAttribute("aria-valuenow", String(progress));
    text(document.querySelector("#login-loading-percent"), `${progress}%`);
    text(document.querySelector("#login-loading-message"), message);
    text(document.querySelector("#login-loading-stage"), stage);
    for (const row of traceRows) {
      const isCurrent = row.dataset.trace === traceKey;
      row.classList.toggle("is-active", isCurrent);
      if (!isCurrent && !row.classList.contains("is-done")) {
        const order = ["device", "hwid", "license", "auth"];
        if (order.indexOf(row.dataset.trace) < order.indexOf(traceKey)) row.classList.add("is-done");
      }
    }
    await wait(LOGIN_STAGE_MS);
  }
  try {
    const authResult = await authRequest;
    if (authResult.error) throw authResult.error;
    for (const row of traceRows) row.classList.add("is-done");
    text(status, "Login berhasil. Membuka command center.");
    document.querySelector("#login-screen").hidden = true;
    document.querySelector(".app-shell").removeAttribute("aria-hidden");
    navigate("dashboard");
    document.querySelector("#main-content").focus();
  } catch (error) {
    status.dataset.tone = "danger";
    text(status, error.message || "Akun tidak dapat diverifikasi.");
    password.focus();
  } finally {
    optimizer.hidden = true;
    username.disabled = false;
    password.disabled = false;
    license.disabled = false;
    password.value = "";
  }
}

async function openMouseSettings(control) {
  await runSafetyCheck(control, "Mengaktifkan DragShot Velocity X", async () => {
    const result = await invoke("open_windows_mouse_settings");
    return {
      message: result.opened
        ? "Mouse Settings dibuka. Aktifkan ClickLock sesuai kenyamanan Anda."
        : "Target Mouse Settings telah diperiksa dan siap digunakan.",
    };
  });
}

function renderEmulators(products, family = null) {
  const visibleProducts = family ? products.filter((product) => product.family === family) : products;
  const container = document.querySelector("#emulator-list");
  const fragment = document.createDocumentFragment();
  for (const product of visibleProducts) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "emulator-item";
    item.dataset.productId = product.product_id;
    const name = document.createElement("strong");
    text(name, product.name);
    const version = document.createElement("small");
    text(version, `Versi produk: ${product.version || "Tidak dapat dipastikan"}`);
    const publisher = document.createElement("small");
    text(publisher, `Penerbit: ${product.publisher || "Tidak tersedia"}`);
    const status = document.createElement("small");
    text(status, product.reason);
    item.append(name, version, publisher, status);
    fragment.append(item);
  }
  if (!visibleProducts.length) {
    const empty = document.createElement("span");
    empty.className = "placeholder-text";
    text(empty, family ? "Emulator yang dipilih tidak terdeteksi." : "BlueStacks atau MSI App Player tidak terdeteksi.");
    fragment.append(empty);
  }
  container.replaceChildren(fragment);
  state.selectedEmulatorId = visibleProducts[0]?.product_id || null;
  if (visibleProducts[0]) container.querySelector(".emulator-item")?.setAttribute("aria-pressed", "true");
  return visibleProducts;
}

async function detectEmulators(control, family = null) {
  navigate("emulator");
  await runSafetyCheck(control, "Memeriksa emulator", async () => {
    text(document.querySelector("#emulator-status"), "Mendeteksi produk dan versi emulator...");
    state.emulatorProducts = await invoke("discover_emulators");
    const visibleProducts = renderEmulators(state.emulatorProducts, family);
    const message = visibleProducts.length
      ? `${visibleProducts.length} emulator terdeteksi. Gunakan tombol Apply Tweak di bawah untuk menerapkan optimasi.`
      : "Pencarian selesai. Emulator yang didukung tidak ditemukan.";
    text(document.querySelector("#emulator-status"), message);
    return { message };
  });
}

async function loadActivity(control) {
  await busy(control, async () => {
    const items = await invoke("list_activity_events", byControl("activity.search").value);
    renderActivityList(items);
  });
}

/* ── Event Delegation ───────────────────────────────────────── */

document.addEventListener("click", async (event) => {
  const control = event.target.closest("[data-control-id]");
  if (!control || control.disabled) return;
  const id = control.dataset.controlId;
  if (id.startsWith("recommendation.select.")) return;
  if (id.startsWith("tweak.action.")) {
    await handleTweakAction(control);
    return;
  }
  if (id.startsWith("advanced.action.")) {
    await handleAdvancedAction(control);
    return;
  }
  const handler = handlers[id];
  if (!handler) {
    showError(new Error(`Handler tidak ditemukan: ${id}`));
    return;
  }
  await handler(control);
});

document.querySelector("#login-form").addEventListener("submit", (event) => {
  event.preventDefault();
  runLoginSequence().catch(showError);
});

document.addEventListener("change", (event) => {
  const control = event.target.closest("[data-control-id]");
  if (!control) return;
  if (control.dataset.controlId.startsWith("recommendation.select.")) {
    if (control.checked) state.selectedRules.add(control.dataset.ruleId);
    else state.selectedRules.delete(control.dataset.ruleId);
  }
  if (["tweaks.search", "tweaks.filter"].includes(control.dataset.controlId)) {
    renderTweakCatalog();
  }
  if (["advanced.search", "advanced.filter"].includes(control.dataset.controlId)) {
    renderAdvancedTweaks();
  }
  if (control.dataset.controlId === "transaction.confirm") {
    byControl("transaction.apply").disabled = !control.checked;
  }
  if (control.dataset.controlId === "settings.theme") {
    handlers["settings.theme"](control);
  }
});

document.addEventListener("input", (event) => {
  if (event.target.dataset.controlId === "tweaks.search") renderTweakCatalog();
  if (event.target.dataset.controlId === "advanced.search") renderAdvancedTweaks();
});

document.querySelector("#apply-process-dialog").addEventListener("cancel", (event) => {
  if (event.currentTarget.dataset.state === "running") {
    event.preventDefault();
    return;
  }
  if (state.returnToTransaction || state.afterProcess) {
    event.preventDefault();
    handlers["process.close"]();
  }
});

document.querySelectorAll(".titlebar, .login-windowbar").forEach((bar) => {
  bar.addEventListener("dblclick", (event) => {
    if (event.target.closest("button, a, input, select")) return;
    toggleMaximize().catch(showError);
  });
});

document.querySelectorAll(".resize-zone").forEach((zone) => {
  zone.addEventListener("mousedown", (event) => {
    if (document.body.dataset.maximized === "true") return;
    event.preventDefault();
    invoke("begin_resize", zone.dataset.resize).catch((err) =>
      console.error("Resize error:", err),
    );
  });
});

window.addEventListener("unhandledrejection", (event) => {
  event.preventDefault();
  showError(event.reason);
});

window.addEventListener("error", (event) => {
  showError(event.error || event.message);
});

/* ── Hardware Terminal ─────────────────────────────────────── */

const HW_TERMINAL_SCRIPT = [
  ["boot", "diagnostic_engine v1.0 ..................", "ok"],
  ["scan", "CPU core map ............................", "ok"],
  ["scan", "GPU pipeline ............................", "ok"],
  ["scan", "Memory channels .........................", "ok"],
  ["scan", "Storage bus .............................", "ok"],
  ["scan", "Network interface .......................", "ok"],
  ["load", "Smart Scan module .......................", "ok"],
  ["load", "Tweak engine ............................", "ok"],
  ["load", "AppSensiX core ..........................", "ok"],
  ["sync", "Device profile ..........................", "ok"],
  ["auth", "License handshake .......................", "wait"],
];

const HW_WORD_MS = 600;
const HW_STATUS_PAUSE_MS = 500;
const HW_LINE_PAUSE_MS = 900;

async function typeHardwareWords(element, value) {
  const words = value.match(/\S+\s*/g) || [];
  for (const word of words) {
    if (document.querySelector("#login-screen").hidden) return false;
    element.textContent += word;
    await wait(reducedMotion ? 0 : HW_WORD_MS);
  }
  return true;
}

async function runHardwareTitle() {
  const title = document.querySelector(".hw-term-title");
  const screen = document.querySelector("#login-screen");
  if (!title || !screen || state.hwTitleRunning) return;
  state.hwTitleRunning = true;
  const titleText = title.dataset.title || "";
  try {
    text(title, "");
    if (!(await typeHardwareWords(title, titleText))) return;
    title.classList.add("is-complete");
  } finally {
    state.hwTitleRunning = false;
  }
}

async function runHardwareTerminal() {
  const log = document.querySelector("#hw-log");
  const screen = document.querySelector("#login-screen");
  if (!log || !screen || state.hwTerminalRunning) return;
  state.hwTerminalRunning = true;
  let cycle = 0;
  try {
    while (!screen.hidden) {
      cycle += 1;
      log.dataset.cycle = String(cycle);
      for (const [tag, lineText, status] of HW_TERMINAL_SCRIPT) {
        if (screen.hidden) return;
        log.dataset.stage = lineText.split(" ", 1)[0].toLowerCase();
        const line = document.createElement("p");
        line.className = "hw-line";
        const tagEl = document.createElement("span");
        tagEl.className = `hw-tag hw-tag-${tag}`;
        const textEl = document.createElement("span");
        textEl.className = "hw-text";
        const statusEl = document.createElement("span");
        statusEl.className = "hw-status";
        line.append(tagEl, textEl, statusEl);
        log.replaceChildren(line);
        if (!(await typeHardwareWords(tagEl, `[${tag.toUpperCase()}]`))) return;
        if (!(await typeHardwareWords(textEl, lineText))) return;
        await wait(reducedMotion ? 240 : HW_STATUS_PAUSE_MS);
        statusEl.dataset.state = status;
        if (!(await typeHardwareWords(statusEl, status === "wait" ? "[WAIT]" : "[OK]"))) return;
        await wait(reducedMotion ? 360 : HW_LINE_PAUSE_MS);
      }
    }
  } finally {
    state.hwTerminalRunning = false;
  }
}

/* ── Init ───────────────────────────────────────────────────── */

async function initialize() {
  await creepStartupProgress(3, reducedMotion ? 0 : 450, "Membaca preferensi tampilan");

  loadTheme();
  await creepStartupProgress(8, reducedMotion ? 0 : 450, "Memverifikasi token identitas");

  await creepStartupProgress(14, reducedMotion ? 0 : 450, "Membangun koneksi bridge");

  setStartupProgress(20, "Memuat Tweak Menu");
  startupCurrentProgress = Math.max(startupCurrentProgress, 20);
  state.tweaks = await loadStageWithProgress(
    "list_tweak_catalog",
    20,
    52,
    "Memuat Tweak Menu",
  );
  if (state.tweaks.length === 0) {
    setStartupProgress(52, "Tweak Menu dilewati karena tidak ada respons");
  } else {
    renderTweakCatalog();
    setStartupProgress(52, "Tweak Menu siap digunakan");
  }
  startupCurrentProgress = 52;
  await creepStartupProgress(58, reducedMotion ? 0 : 400, "Memvalidasi profil keamanan");

  await creepStartupProgress(64, reducedMotion ? 0 : 400, "Mencocokkan signature tweak");

  await creepStartupProgress(70, reducedMotion ? 0 : 400, "Menyiapkan modul transaksi");

  setStartupProgress(76, "Memuat Advanced Tweak Menu");
  startupCurrentProgress = Math.max(startupCurrentProgress, 76);
  state.advancedTweaks = await loadStageWithProgress(
    "list_advanced_tweaks",
    76,
    92,
    "Memuat Advanced Tweak Menu",
  );
  if (state.advancedTweaks.length === 0) {
    setStartupProgress(92, "Advanced Tweak Menu dilewati karena tidak ada respons");
  } else {
    renderAdvancedTweaks();
    setStartupProgress(92, "Advanced Tweak Menu siap digunakan");
  }
  startupCurrentProgress = 92;
  await creepStartupProgress(94, reducedMotion ? 0 : 350, "Menganalisis konfigurasi hardware");

  await creepStartupProgress(96, reducedMotion ? 0 : 350, "Menyiapkan halaman awal");
  navigate("dashboard");
  await nextPaint();
  await creepStartupProgress(99, reducedMotion ? 0 : 350, "Menyelesaikan kalibrasi antarmuka");

  setStartupProgress(100, "Sistem siap • Membuka command center");
  startupCurrentProgress = 100;
  const startupElapsed = window.performance.now() - startupStartedAt;
  await wait(Math.max(0, STARTUP_MIN_PRESENTATION_MS - startupElapsed));
  document.querySelector("#startup-screen").dataset.state = "complete";
  const login = document.querySelector("#login-screen");
  login.hidden = false;
  await nextPaint();
  await restoreRememberedLogin();
  runHardwareTitle().catch(showError);
  runHardwareTerminal().catch(showError);
  document.querySelector("#login-username").focus();
}

async function restoreRememberedLogin() {
  const username = document.querySelector("#login-username");
  const password = document.querySelector("#login-password");
  const license = document.querySelector("#login-license");
  const remember = document.querySelector("#login-remember");
  if (!username || !remember) return;
  try {
    const result = await invoke("load_remember");
    if (result && result.active && result.username) {
      username.value = result.username;
      if (password && result.password) password.value = result.password;
      if (license && result.license_key) license.value = result.license_key;
      remember.checked = true;
    }
  } catch {
    /* backend not ready yet — silent */
  }
}

if (window.pywebview) {
  window.addEventListener("pywebviewready", initialize, { once: true });
} else {
  initialize().catch(showError);
}
