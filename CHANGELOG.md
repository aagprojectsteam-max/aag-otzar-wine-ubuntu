# Changelog

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
