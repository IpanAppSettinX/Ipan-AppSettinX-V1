# Third-party notices

Runtime dependencies currently planned:

- pywebview 6.2.1 - BSD-3-Clause.
- psutil 7.2.2 - BSD-3-Clause.
- Pydantic 2.13.4 - MIT.
- pywin32 311 - PSF license.

Development and packaging tools include pytest, Ruff, mypy, Playwright,
PyInstaller, and their pinned dependencies. They are not application runtime
features; their licenses still require review before redistributing a build
environment or test browser payload.

Social buttons bundle four SVGs from Simple Icons, pinned to commit
`25d6e5b39bc55bc446e147700294628af1734f7e`. The Simple Icons repository is
distributed under CC0-1.0. Its disclaimer notes that CC0 does not waive third
party trademark rights and that individual brand marks may have separate usage
requirements. Product names and marks remain the property of their respective
owners.

The Smart Scan cards bundle six SVGs from Microsoft Fluent System Icons, pinned
to commit `5ecd79ea56f2be0169859b3b881dcc890be932fc`. Copyright (c) 2020 Microsoft
Corporation and distributed under the MIT License. The MIT license permits use,
copying, modification, and distribution while requiring preservation of its
copyright and permission notice. Exact files and hashes are recorded in
`ASSET_PROVENANCE.md`.

No PresentMon binary is bundled in the current development tree. Its required
notices must be added before bundling.
