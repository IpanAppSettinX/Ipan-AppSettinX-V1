# Manual Windows QA matrix

Manual mutation testing is prohibited on the developer host.

Use disposable checkpoints for Windows 10 22H2, Windows 11 24H2/25H2,
non-admin, WebView2 missing, Hyper-V enabled/disabled, WMI/service missing, and
custom Windows fixtures. Restore the checkpoint after each mutation case.

Dedicated hardware is required for iGPU/dGPU/multi-GPU, battery/thermal,
high-refresh displays, BlueStacks/MSI variants, Free Fire variants, and
PresentMon accuracy. Virtual GPU results are not accepted as representative
performance evidence.

