# Packaging

The main application is a PyInstaller `onedir` build with an `asInvoker`,
Per-Monitor-V2 manifest. The one-shot helper is a separate executable with a
`requireAdministrator` manifest, but its real execution path remains disabled
until the secure IPC and Windows VM mutation suite are approved.

```powershell
python -m PyInstaller installer\ipan_optimizer.spec --clean --noconfirm
python -m PyInstaller installer\helper.spec --clean --noconfirm
ISCC.exe installer\IPANOptimizer.iss
python scripts\release_hashes.py dist --output release-sha256.json
```

The installer is per-user and does not request elevation. It refuses to
continue when WebView2 Evergreen is missing and never downloads it silently.
Release signing requires an organization-controlled certificate; no credential
or signing secret belongs in the repository.

