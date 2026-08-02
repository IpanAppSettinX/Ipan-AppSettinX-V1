# Design system

Ipan AppSettinX uses a **Premium Dark Gaming Command Center** visual language
built on Microsoft Fluent Design foundations. It targets paying Windows gamers
who expect a trustworthy, high-end utility: deep layered surfaces, purposeful
elevation, rounded geometry, bold typography, navy surfaces, one cyan accent,
and explicit risk/evidence states. The interface avoids fake performance gauges,
generated art, mixed icon families, decorative diagrams, and animation without
state meaning.

Typography uses Segoe UI Variable/Segoe UI/system-ui. Page titles sit in a
24-42 pixel hierarchy with strong negative letter-spacing, controls remain at
14 pixels, and metadata uses 10-12 pixels. Spacing follows an 8-pixel rhythm.
Panels use large radii (`radius-xl`/`radius-2xl`) and layered shadows instead of
decorative gradients or corner accents.

Required tokens are defined only in `frontend/css/tokens.css`. Status must never
be conveyed by color alone. Focus indicators are 2 px and remain visible in
forced-colors. Reduced motion disables non-essential transitions.

Navigation uses the task labels Beranda, Smart Scan, Tweak Menu, Advanced Tweak
Menu, Gaming, Emulator, and Restore. Activity is a secondary system route;
Settings and About Ipan AppSettinX remain footer routes. The active navigation
item uses a Fluent pill highlight with a rounded icon badge.

Short success notifications appear at the top center and use a polite live
region. Urgent failures use an assertive alert. Persistent recovery, restart, or
unsupported-version states remain inline instead of disappearing automatically.

Apply actions use one stateful overlay tied to actual bridge work. Typed
transactions show check, snapshot, apply, and verify stages, then display a
success state only for `VERIFIED`. Analysis-only and prohibited requests use the
same visual language but end in a blocked safety result. The progress interface
uses a stage dial (rotating pointer + four phase nodes) so users can read which
stage is active. Reduced-motion removes orbit and pointer animation.

The main window is frameless with a custom titlebar that includes the brand
lockup and system window controls (minimize, maximize, close). The titlebar is
draggable; window controls are non-draggable and use the same color tokens as
the rest of the interface.

Scrollbars are styled with theme-matched tracks and thumbs so they feel native
to the dark/light surfaces instead of the default browser chrome.

Startup uses a minimum 6.8-second brand presentation at normal motion settings.
The brand mark is the Ipan Store logo, presented inside a multi-ring orbital
loader with a cinematic floating animation. Initialization progress reaches 100
only after both tweak catalogs and the first route are ready; any remaining
interval is explicitly labelled as a ready-state brand intro rather than
additional system work.

Smart Scan doubles as a live telemetry dashboard: CPU speed, CPU load, and RAM
usage are sampled through the bridge and drawn as scrolling canvas charts that
update every second while the route is visible. Reduced motion does not disable
the numeric updates but disables the canvas stroke animation where applicable.
