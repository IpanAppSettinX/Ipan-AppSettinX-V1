# Asset provenance

## IPAN Store logo

- Bundled file: `src/ipan_optimizer/frontend/assets/ipan-store-logo.png`
- Source: IPAN Store logo supplied directly by the product owner in this workspace session.
- Processing: local background matte removal and alpha crop; the navy source background is not bundled.
- Source supplied by the user:
  `D:\LOGO IPAN STORE\ChatGPT Image Jul 1, 2026, 12_41_23 AM.png`
- Original SHA-256:
  `ACBB593D895FEFB9EA6962714602953329DCBFDEED444A849A332CF5CF0A492D`
- Bundled SHA-256:
  `9B855815FDFE2FB3885292A4151791CED6D6B274B5C8D47B3C1EC7E8C2FD1C90`
- Processing: deterministic resize from 1536x1024 to 768x512 and JPEG quality
  88 for a 26,323-byte offline UI asset. No content was generated or added.
- Rights: supplied for this project by the user; redistribution rights remain
  the user's responsibility.

## Social brand icons

The following SVG brand marks come from Simple Icons at pinned commit
`25d6e5b39bc55bc446e147700294628af1734f7e`, retrieved 2026-07-27:

| File | SHA-256 |
|---|---|
| `icons/discord.svg` | `EF157630D5530CD872823CD212C3A8AA7B7BAF3F502D4D841A14E93440F28785` |
| `icons/instagram.svg` | `ACF0A23ECEED7D9AA4F2BD99ED5D97C43EB4F73E5755F5BD87A292A356767D3C` |
| `icons/tiktok.svg` | `81FB35B92330F083B3818CB39FF52E08C2B3AA2ADC8FD258EF2A7C30EB134505` |
| `icons/whatsapp.svg` | `F75E6E89161947E8DF59FF7EC13C5BEB7851BB0D21BA80D98E88DECDE6F4DFE0` |

Upstream:
`https://github.com/simple-icons/simple-icons/tree/25d6e5b39bc55bc446e147700294628af1734f7e/icons`

Simple Icons is distributed under CC0-1.0, subject to its trademark and legal
disclaimer. The icons are source-controlled SVG vectors, not AI-generated
assets. Product names and marks remain the property of their respective owners.
The local presentation was updated on 2026-07-29 after checking the platforms'
brand resources. WhatsApp uses `#25D366`, Discord uses its documented Blurple
`#5865F2`, Instagram uses its recognized magenta glyph treatment, and TikTok
uses its cyan, red, and dark offset treatment. The Instagram vector was reduced
to the platform's standard camera glyph for legibility at 32 px; the remaining
marks retain the pinned Simple Icons geometry. No external image or network
request is used at runtime.

Brand guidance checked:

- Discord: `https://discord.com/branding`
- WhatsApp and Instagram:
  `https://about.meta.com/brand/resources/`
- TikTok: `https://www.tiktok.com/about/brand-resources/`

## Microsoft Fluent hardware icons

The Smart Scan hardware cards use a local subset of Microsoft Fluent System
Icons from pinned commit `5ecd79ea56f2be0169859b3b881dcc890be932fc`, retrieved
2026-07-28. The upstream repository is licensed under MIT. The only local
modification is changing the fixed path fill from `#212121` to `currentColor` so
the icons follow the application theme; no geometry was generated or redrawn.

| Bundled file | Upstream asset | SHA-256 |
|---|---|---|
| `icons/fluent/cpu-24-regular.svg` | `assets/Developer Board/SVG/ic_fluent_developer_board_24_regular.svg` | `CC135B62992961DB49FD90402D219EF0A0DFD61EFB889B85F80A6F3B708067EA` |
| `icons/fluent/gpu-24-regular.svg` | `assets/FPS 60/SVG/ic_fluent_fps_60_24_regular.svg` | `64B44A3F065355D71FD0BCB3703E5973E6167B87FEA2847FC38D4EF2362B80DB` |
| `icons/fluent/memory-20-regular.svg` | `assets/RAM/SVG/ic_fluent_ram_20_regular.svg` | `0DF3666B777F966BA6245A4F158889760461FD5E276C8CED9E4C2C045937DECC` |
| `icons/fluent/storage-24-regular.svg` | `assets/Hard Drive/SVG/ic_fluent_hard_drive_24_regular.svg` | `E131FC6B29D869A945B48D5A6DA6DA3F5DB0B58C6376F8EEF595D23A75AD6FB2` |
| `icons/fluent/network-24-regular.svg` | `assets/WiFi 1/SVG/ic_fluent_wifi_1_24_regular.svg` | `D9FF2F0BE5A3B4736DDC273F3133DAFBB79045559279D47AF2F58FD303AB1A37` |
| `icons/fluent/windows-24-regular.svg` | `assets/Window Apps/SVG/ic_fluent_window_apps_24_regular.svg` | `FB2812EA785D7C24001BA31C67EDEAAFBA3AA8F1475A92F51B102D19EEF12842` |

Upstream:
`https://github.com/microsoft/fluentui-system-icons/tree/5ecd79ea56f2be0169859b3b881dcc890be932fc/assets`
