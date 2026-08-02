# Compatibility

V1 target: Windows 10/11 x64, WebView2 Evergreen, at least two logical
processors, 4 GB RAM, and sufficient local storage.

Windows 10 remains technically supported with a non-blocking Indonesian notice
that regular support ended on 14 October 2025. Windows on ARM64 is explicitly
read-only/unsupported for mutation.

Compatibility is capability-based. Missing WMI, services, policies, Windows
components, or unknown emulator schemas produce unavailable or read-only
states, never blind repair.

Automated compatibility uses deterministic fixtures. Real behavior requires
disposable Windows VMs and dedicated hardware QA.

