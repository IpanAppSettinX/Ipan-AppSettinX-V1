# Performance budget

| Measure | Release budget |
|---|---:|
| Initial HTML + CSS + JS | <= 500 KiB uncompressed |
| First-party JavaScript | <= 180 KiB |
| CSS | <= 100 KiB |
| External startup requests | 0 |
| Navigation feedback | <= 100 ms |
| Normal frontend long task | <= 50 ms |
| Cold start after WebView2 ready | P50 <= 2 s; P95 <= 4 s |
| Idle process-tree CPU | median < 0.5% after 30 s |
| Process-tree working set | target <= 180 MB; >250 MB blocks release |

Measurements must record machine fixture, Windows build, WebView2 version,
sample count, and method. Current automated checks cover static asset size and
external resource rejection; runtime budgets require Windows VM measurements.

## Development validation

- The static asset budget and external-request policy are enforced by scripts
  and UI tests. The gaming command-center redesign remains well below the
  500 KiB total budget; exact measurements are recorded by the validation
  script after each UI change.
- A real WebView2/pywebview smoke run at 1280x800 completed with no captured
  console or page errors and produced dashboard and scan screenshots.
- Cold-start, idle CPU, working-set, long-task, and navigation latency budgets
  remain release gates because a controlled Windows VM fixture and repeatable
  sample set were not available in this development workspace.
