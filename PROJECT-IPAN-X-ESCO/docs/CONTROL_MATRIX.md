# Control matrix

Generated from `docs/control_matrix.source.json`. Do not edit manually.

| control_id | Route/component | Indonesian label | User intent | Handler | Bridge method | Backend operation | Risk/permission | States | Verification | Test IDs |
|---|---|---|---|---|---|---|---|---|---|---|
| `auth.login` | login | Login | Autentikasi Firebase dan validasi binding lisensi perangkat | runLoginSequence | authenticate | Firebase sign-in and atomic Firestore rules device binding | account credential input | ready, loading, validation error, access locked, authorized | shell unlocks only after Firebase token and device binding are accepted | UI-CONTROL-AUTH-LOGIN |
| `auth.remember` | login | Ingat saya dalam 30 hari | Simpan username agar terisi otomatis pada peluncuran berikutnya | restoreRememberedLogin |  | local storage preference | explicit user action | unchecked, checked, remembered | username prefilled and checkbox checked when unexpired remember token exists | UI-CONTROL-AUTH-REMEMBER |
| `auth.password_toggle` | login | Tampilkan password | Tampilkan atau sembunyikan password lokal | auth.password_toggle |  | local input state | explicit user action | shown, hidden | password input type toggled | UI-CONTROL-AUTH-PASSWORD-TOGGLE |
| `auth.register` | login | Daftar Akun | Hubungi Ipan Store untuk membeli dan mendaftarkan akun | openSupport | open_support_url | allowlisted system browser | explicit user action | ready, loading, opened, validated | exact WhatsApp purchase URL | UI-CONTROL-AUTH-REGISTER |
| `auth.reset_hwid` | login | Reset HWID | Hubungi Ipan Store untuk mengajukan reset perangkat | openSupport | open_support_url | allowlisted system browser | explicit user action | ready, loading, opened, validated | exact WhatsApp HWID reset URL | UI-CONTROL-AUTH-RESET-HWID |
| `auth.window_minimize` | login | Minimize | Minimize window dari halaman login | auth.window_minimize | minimize_window | window control | none | ready | window minimized while login is locked | UI-CONTROL-AUTH-WINDOW-MINIMIZE |
| `auth.window_maximize` | login | Maximize/Restore | Maximize atau restore window dari halaman login | auth.window_maximize | maximize_window | window control | none | maximized, restored | maximized state toggles glyph and aria-label | UI-CONTROL-AUTH-WINDOW-MAXIMIZE |
| `auth.window_close` | login | Close | Tutup window dari halaman login | auth.window_close | close_window | window control | explicit user action | ready | window closed while login is locked | UI-CONTROL-AUTH-WINDOW-CLOSE |
| `nav.dashboard` | shell | Dashboard | Buka Dashboard | navigate |  | local route | none | ready, focus | route dashboard visible | UI-CONTROL-NAV-DASHBOARD |
| `nav.scan` | shell | Monitor | Buka Monitor | navigate |  | local route | none | ready, focus | route monitor visible | UI-CONTROL-NAV-SCAN |
| `nav.tweaks` | shell | System Tweaks | Buka System Tweaks | navigate |  | local route | none | ready, focus | route tweaks visible | UI-CONTROL-NAV-TWEAKS |
| `nav.advanced` | shell | Advanced Tweak Menu | Buka Advanced Tweak Menu | navigate |  | local route | none | ready, focus | route advanced visible | UI-CONTROL-NAV-ADVANCED |
| `nav.profiles` | shell | AppSensiX | Buka AppSensiX | navigate |  | local route | none | ready, focus | route profiles visible | UI-CONTROL-NAV-PROFILES |
| `nav.emulator` | shell | Emulator | Buka Emulator | navigate |  | local route | none | ready, focus | route emulator visible | UI-CONTROL-NAV-EMULATOR |
| `nav.restore` | shell | Restore | Buka Restore | navigate |  | local route | none | ready, focus | route restore visible | UI-CONTROL-NAV-RESTORE |
| `nav.activity` | shell | Activity | Buka Activity | navigate |  | local route | none | ready, focus | route activity visible | UI-CONTROL-NAV-ACTIVITY |
| `nav.settings` | shell | Settings | Buka Settings | navigate |  | local route | none | ready, focus | route settings visible | UI-CONTROL-NAV-SETTINGS |
| `nav.evidence` | shell | About | Buka About | navigate |  | local route | none | ready, focus | route evidence visible | UI-CONTROL-NAV-EVIDENCE |
| `dashboard.scan` | dashboard | Mulai Smart Scan | Mulai scan | runScan | scan_system | capability scan | read-only | loading, success, error | scan ID and facts rendered | UI-CONTROL-DASHBOARD-SCAN |
| `dashboard.review` | dashboard | Lihat rekomendasi | Buka Monitor | navigate |  | local route | none | ready | route monitor visible | UI-CONTROL-DASHBOARD-REVIEW |
| `scan.run` | monitor | Jalankan Scan | Jalankan ulang scan | runScan | scan_system | capability scan | read-only | loading, success, error | recommendations rendered | UI-CONTROL-SCAN-RUN |
| `recommendation.select.*` | monitor | Pilih rekomendasi | Pilih rule | recommendation change |  | local state | capability gated | selected, disabled | preview state updated | UI-CONTROL-RECOMMENDATION-SELECT |
| `tweaks.search` | tweaks | Cari tweak | Filter katalog | renderTweakCatalog | list_tweak_catalog | read curated catalog | read-only | empty, results | visible cards match query | UI-CONTROL-TWEAKS-SEARCH |
| `tweaks.filter` | tweaks | Status risiko | Filter risiko | renderTweakCatalog |  | local filter | none | all, filtered | visible cards match safety | UI-CONTROL-TWEAKS-FILTER |
| `tweak.action.*` | tweaks | Apply Tweak | Preview/jalankan tweak | handleTweakAction |  | risk-gated dispatch | catalog action | preview, settings, blocked analysis | action matches catalog execution mode | UI-CONTROL-TWEAK-ACTION |
| `gaming.aim_smooth` | game_boost | ACTIVATE | OneTap Vector X | runSafetyCheck | apply_gaming_tweak | fail-closed gaming safety check | read-only | checking, blocked result | no system operation | UI-CONTROL-GAMING-AIM-SMOOTH |
| `gaming.aim_stabilizer` | game_boost | ENABLE CORE | Neural AimSync X | previewTransaction | preview_transaction | typed pointer transaction preview | conditional | preview, apply, verified, rollback | typed pointer targets verified | UI-CONTROL-GAMING-AIM-STABILIZER |
| `gaming.easy_drag` | game_boost | ENGAGE | DragShot Velocity X | openMouseSettings | open_windows_mouse_settings | allowlisted Windows Settings | explicit user action | loading, opened, validated | fixed settings target | UI-CONTROL-GAMING-EASY-DRAG |
| `gaming.boost_fps_menu` | game_boost | START OVERDRIVE | Emulator Overdrive X | runSafetyCheck | discover_emulators | read-only emulator discovery | read-only | checking, result, route | discovery completes before emulator menu | UI-CONTROL-GAMING-BOOST-FPS-MENU |
| `gaming.optimize_bluestacks` | emulator | Apply Tweak | Deteksi BlueStacks | detectEmulators | discover_emulators | read-only uninstall inventory | read-only | loading, empty, results | family-filtered product and version | UI-CONTROL-GAMING-OPTIMIZE-BLUESTACKS |
| `gaming.optimize_msi` | emulator | Apply Tweak | Deteksi MSI App Player | detectEmulators | discover_emulators | read-only uninstall inventory | read-only | loading, empty, results | family-filtered product and version | UI-CONTROL-GAMING-OPTIMIZE-MSI |
| `emulator.discover` | emulator | Detect Emulator | Deteksi produk emulator | emulator.discover | discover_emulators | read-only discovery | read-only | loading, empty, results, error | product count | UI-CONTROL-EMULATOR-DISCOVER |
| `emulator.profile` | emulator | Profil | Select emulator profile | emulator value |  | profile resolver | conditional | selected | profile ID passed | UI-CONTROL-EMULATOR-PROFILE |
| `emulator.apply` | emulator | Apply Tweak | Preview profile compatibility | emulator.apply | preview_emulator_profile | read-only schema gate | read-only until schema supported | disabled, loading, read-only result | unknown schema makes no change | UI-CONTROL-EMULATOR-APPLY |
| `emulator.low_end` | emulator | Apply Tweak | Free Fire Low-End Mode | runSafetyCheck | preview_emulator_profile | read-only profile check | read-only | checking, blocked result | no system operation | UI-CONTROL-EMULATOR-LOW-END |
| `emulator.max_fps` | emulator | Apply Tweak | Free Fire Max FPS Mode | runSafetyCheck | preview_emulator_profile | read-only profile check | read-only | checking, blocked result | no system operation | UI-CONTROL-EMULATOR-MAX-FPS |
| `nav.fixes` | shell | Fixes | Buka Fixes | navigate |  | local route | none | ready, focus | route fixes visible | UI-CONTROL-NAV-FIXES |
| `fixes.camera` | fixes | Apply Tweak | Pulihkan izin kamera pengguna | previewTransaction | preview_transaction | typed webcam consent transaction preview | conditional | preview, apply, verified, rollback | typed webcam consent target verified | UI-CONTROL-FIXES-CAMERA |
| `fixes.obs` | fixes | Apply Tweak | Pulihkan konfigurasi capture pengguna | previewTransaction | preview_transaction | typed capture transaction preview | conditional | preview, apply, verified, rollback | typed capture targets verified | UI-CONTROL-FIXES-OBS |
| `activity.search` | activity | Cari activity | Filter activity | activity value | list_activity_events | local query | read-only | empty, results | filter passed | UI-CONTROL-ACTIVITY-SEARCH |
| `activity.refresh` | activity | Muat activity | Load activity | loadActivity | list_activity_events | local query | read-only | loading, empty, results | events rendered | UI-CONTROL-ACTIVITY-REFRESH |
| `settings.save` | settings | Simpan settings | Persist settings | settings.save | save_settings | settings persistence | dry-run locked | loading, success, validation error | dry_run true | UI-CONTROL-SETTINGS-SAVE |
| `support.website` | evidence | Website resmi IPAN Store | Buka website resmi | openSupport | open_support_url | allowlisted system browser | explicit user action | loading, opened, validated | exact website URL | UI-CONTROL-SUPPORT-WEBSITE |
| `support.whatsapp` | evidence | WA Admin | Buka WhatsApp admin | openSupport | open_support_url | allowlisted system browser | explicit user action | loading, opened, validated | exact wa.me URL | UI-CONTROL-SUPPORT-WHATSAPP |
| `support.discord` | evidence | Discord | Buka Discord IPAN | openSupport | open_support_url | allowlisted system browser | explicit user action | loading, opened, validated | exact invite URL | UI-CONTROL-SUPPORT-DISCORD |
| `support.instagram` | evidence | Instagram | Buka Instagram IPAN | openSupport | open_support_url | allowlisted system browser | explicit user action | loading, opened, validated | exact profile URL | UI-CONTROL-SUPPORT-INSTAGRAM |
| `support.tiktok` | evidence | TikTok | Buka TikTok IPAN | openSupport | open_support_url | allowlisted system browser | explicit user action | loading, opened, validated | exact profile URL | UI-CONTROL-SUPPORT-TIKTOK |
| `support.whatsapp_channel` | evidence | Saluran WA IPAN | Buka channel WhatsApp | openSupport | open_support_url | allowlisted system browser | explicit user action | loading, opened, validated | exact channel URL | UI-CONTROL-SUPPORT-WHATSAPP-CHANNEL |
| `transaction.confirm` | dialog | Konfirmasi dampak | Akui warning sebelum apply | transaction.confirm |  | local safety gate | explicit acknowledgement | unchecked, checked | apply disabled until checked | UI-CONTROL-TRANSACTION-CONFIRM |
| `transaction.apply` | dialog | Apply Tweak | Apply typed transaction | applyTransaction | start_apply_transaction | background transaction job | safe backend only | 0-100 progress, verified, rolled back, error | job succeeds only with VERIFIED | UI-CONTROL-TRANSACTION-APPLY |
| `transaction.verify` | dialog | Verifikasi | Read transaction status | transaction.verify | get_transaction_status | transaction read | read-only | disabled, loading, result | state rendered | UI-CONTROL-TRANSACTION-VERIFY |
| `transaction.rollback` | dialog | Pulihkan | Rollback transaction | transaction.rollback | rollback_transaction | conflict-aware rollback | snapshot required | disabled, rolling back, conflict, restored | ROLLED_BACK or conflict | UI-CONTROL-TRANSACTION-ROLLBACK |
| `transaction.close` | dialog | Tutup | Close dialog | dialog.close |  | local dialog | none | ready, focus return | dialog closed | UI-CONTROL-TRANSACTION-CLOSE |
| `process.close` | apply process dialog | Tutup | Tutup hasil proses | process.close |  | local dialog and focus flow | none | hidden while running, ready after result | result dialog closes | UI-CONTROL-PROCESS-CLOSE |
| `advanced.search` | tweaks | Cari advanced tweak | Filter advanced tweaks | renderAdvancedCatalog |  | local filter | none | empty, results | visible cards match query | UI-CONTROL-ADVANCED-SEARCH |
| `advanced.filter` | tweaks | Kategori | Filter kategori advanced tweak | renderAdvancedCatalog |  | local filter | none | all, filtered | visible cards match category | UI-CONTROL-ADVANCED-FILTER |
| `advanced.action.*` | tweaks | Apply Tweak | Safety check advanced tweak | handleAdvancedAction | apply_advanced_tweak | fail-closed advanced safety check | read-only | checking, blocked result | no system operation | UI-CONTROL-ADVANCED-ACTION |
| `restore.open` | restore | Buka System Restore | Buka native system restore | restore.open | open_system_restore | call native restore | explicit user action | loading, error | restore opened | UI-CONTROL-RESTORE-OPEN |
| `settings.theme` | settings | Mode Terang | Toggle theme | settings.theme |  | local state | none | checked, unchecked | theme changed | UI-CONTROL-SETTINGS-THEME |
| `window.minimize` | titlebar | Minimize | Minimize window | window.minimize | minimize_window | window control | none | ready | window minimized | UI-CONTROL-WINDOW-MINIMIZE |
| `window.maximize` | titlebar | Maximize | Maximize window | window.maximize | maximize_window | window control | none | ready | window maximized | UI-CONTROL-WINDOW-MAXIMIZE |
| `window.close` | titlebar | Close | Close window | window.close | close_window | window control | none | ready | window closed | UI-CONTROL-WINDOW-CLOSE |

Total canonical controls: **62**.
