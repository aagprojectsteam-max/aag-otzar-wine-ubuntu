## Unreleased — 2026-09-22

- Reworked physical touch scrolling for internal book fullscreen.
- Added a bounded seven-page warm pool so crossing a page boundary reuses already-rendered page canvases instead of replacing and redrawing the visible page during the gesture.
- Deferred page-state reconciliation until the visual scroll has settled; one authoritative reconciliation remains at gesture end.
- Removed stale release velocity after a held drag, prevented pointer-cancel from starting inertia, locked the dominant gesture axis, and stopped unrelated focus changes from cancelling touch.
- Fullscreen boundary benchmark improved from a measured ~66.7 ms worst frame with page redraw to ~16.7 ms with zero image redraw calls in the tested touch cases.
- Preserved mouse-wheel scrolling, page navigation, scale 1.5, Chromium compositing, read-only content, and the existing launcher lifecycle.

# Changelog

## Unreleased — 2026-09-22

- Dock launch now owns the full Otzar lifecycle: it starts the Kingston USB Clone and read-only content mount when needed, then tears down only resources it started.
- Added a lifecycle lock so an immediate relaunch waits for the previous shutdown cleanup instead of colliding with input-sync or USB teardown.
- Added systemd ExecStop helper templates for content unmount and Kingston gadget teardown.
- Added a narrowly scoped polkit template allowing the configured desktop user to start/stop only the two Otzar lifecycle services without repeated password prompts.
- Verified locally: passwordless service start/stop, Kingston gadget cleanup, content mount cleanup, and launcher shell syntax.

## v3.3.0-burn-in — 2026-09-20

- Production tree relocated under `/mnt/data/WineApps/Otzar-HaHochma`.
- GNOME Apps launcher now restores/raises an already-running nested Xwayland window.
- Kingston 0951:1666 readiness is checked before a cold application start.
- Added an owned mount lifecycle: a mount created for Otzar is verified, read-only, and automatically unmounted/detached after the application stack exits.
- Added a local `org.freedesktop.Xwayland.desktop` integration pattern so the nested host can use the application name/icon and be pinned to the Dock.
- Restored `autoHeb=0` after migration so host Hebrew/English switching remains authoritative.
- Fullscreen preferences are enforced for every settings object/tab; fullscreen survives book changes.
- Enabled Chromium compositing while retaining `LIBGL_ALWAYS_SOFTWARE=1`; physical wheel testing removed recurring ~166 ms frame stalls seen with `--disable-gpu-compositing`.
- Retained scale 1.5, touch, input filter, popup fixes, window controls, and read-only content architecture.

## v3.2.0-burn-in — 2026-09-18

- Final DATA-first production layout.
- Direct GNOME Apps launch into DATA.
- Wine 11.17 self-contained in DATA.
- Stable Hebrew/English switching and Backspace repair.
- Touch and scrolling accepted.
- Maximize/minimize/restore fixed for fullscreen nested Xwayland.
- Scale 1.5 accepted while retaining physical sharpness.
- Main and Tsiyunim splitter shimmer fixed by physical-pixel phase alignment.
- Text-field native popup flashing replaced by stable in-page context menu.
- Application BaseContextMenu outside-click dismissal repaired.
- Compact burn-in kit replaces large experiment trees for small follow-up fixes.

Public repository contains only AAG-authored interoperability code and documentation.
