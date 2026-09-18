# Otzar-Wine Ubuntu

Reference implementation and engineering handoff for running a user-owned Windows installation of Otzar HaHochma on Ubuntu through Wine, nested Xwayland, Bubblewrap, and a small set of compatibility fixes.

## Status

- Reference platform: Ubuntu 26.04, GNOME Wayland.
- Tested Wine: wine-devel 11.17.
- Final UI scale: 1.5 on a 1920x1200 nested Xwayland display.
- Final reference runtime: v3.2.0 burn-in.
- This repository contains only AAG-authored glue code, diagnostics, patches, templates, and documentation.

## What is not included

This repository does not contain the commercial application, books, databases, licensing material, vendor binaries, or a Wine prefix copied from a licensed installation. You must supply your own lawful installation and content.

## Solved compatibility issues

- Native touch input and touch-to-typing focus.
- Hebrew/English switching with Super+Space and Alt+Shift.
- Backspace failing after a language switch because Wine/Chromium retained a stale modifier.
- Tab fallback behavior.
- Maximize/minimize/restore inside a fullscreen nested Xwayland session.
- Scale 1.5 while retaining physical sharpness.
- Fractional-pixel text shimmer while dragging split panels.
- Flashing native context menus in text fields.
- Application context menus that did not dismiss on outside click.

## Start here

Read docs/AI-HANDOFF-FULL.md if you want an AI agent to reproduce the setup from a clean machine. Read docs/ARCHITECTURE.md for the component model and docs/FAILURE-HISTORY.md before trying alternative fixes.

## Public source layout

- src/input-filter.c — Wine-side stale-modifier repair filter.
- src/bridge.py — host physical-key certificate bridge.
- src/kernel_modifiers.py — EVIOCGKEY physical modifier snapshots.
- src/xguard.py — X11 modifier guard.
- src/touch-focus.sh — touch-to-focus helper.
- src/scale15-phase-snap.js — physical-pixel-aligned splitter motion.
- src/popup-fix-v2.js — stable HTML text context menu and outside-click dismissal.
- src/window-control-bridge.js — Electron window-control interception.
- src/tab-fallback.js — production tab fallback.
- scripts/build-input-filter.sh — reproducible MinGW build.
- scripts/install-desktop-entry.sh — direct DATA launcher integration.

## Philosophy

The final design avoids a VM, avoids Wine source changes, keeps content read-only, keeps writable application state isolated, and applies the smallest compatibility layer needed around the application.
