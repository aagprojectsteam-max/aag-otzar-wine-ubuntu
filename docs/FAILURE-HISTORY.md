# Failure History and Engineering Findings

This file exists so future work does not repeat expensive dead ends.

## Language switching and Backspace

Observed failure: typing worked, language switching worked, but Backspace stopped deleting after a host language switch until the user switched to another Ubuntu window and back.

Key evidence:
- Wine still received Backspace as VK_BACK / scan 0x0e.
- The DOM still had the same focused input and caret.
- Backspace events reached Chromium with Meta/Super=true.
- beforeinput deleteContentBackward was not emitted.
- a real host window switch caused Wine to reconcile a stale VK_LWIN state.

Rejected or incomplete approaches:
- Quick Lang Switch GNOME extension: interfered with normal switching.
- visible focus bounce/run-or-raise: unacceptable UX and not reliable.
- xdotool windowfocus only: insufficient.
- Win32 activation pulse: insufficient.
- host uinput Alt-Tab/workspace bounce: visible and unreliable.
- synthetic X11 FocusIn/KeymapNotify v1.1/v1.2: did not fix physical use.
- simple Windows SendInput modifier release: insufficient by itself.
- Wine source patching: explicitly avoided in the final design.
- hybrid Wine binary mixing: crashed and must not be repeated.

Final principle: repair only stale Wine modifier state when the Linux physical keyboard proves that modifier is no longer held, then replay the triggering key once.

## Automatic Hebrew conversion

The application's own auto-Hebrew option can make English-layout keystrokes appear as Hebrew. This can falsely suggest that the OS layout did not change.

Final state: the application setting autoHeb is disabled through the application's own settings mechanism. GNOME owns the layout switch.

## Maximize/minimize freeze

Root cause:
- nested Xwayland runs fullscreen without a nested window manager;
- native Electron maximize changed the inner window to an incorrect 1600x1200 geometry inside a 1920x1200 root;
- native Electron minimize hid the inner BrowserWindow while the outer Xwayland surface remained visible, producing a frozen/stale image.

Final mapping:
- maximize -> fit inner Otzar window to nested root;
- minimize -> minimize outer Xwayland host in GNOME;
- restore -> normal GNOME restore while inner renderer remains alive.

## Scale shimmer

At scale 1.5, one CSS pixel equals 1.5 physical pixels. Splitter movement could land on half physical pixels and cause visible glyph rasterization shimmer.

Initial filter based only on pointer clientX fixed the main splitter but not the 2px Tsiyunim splitter. Split.js actually positions the gutter from clientX minus gutterSize/2.

Final filter aligns the predicted gutter-left coordinate, not the raw pointer.

## Context menus

Text input: native Chromium/Electron popup surfaces flashed visually under nested Xwayland. Replaced with an in-page menu for editable fields.

Book view: BaseContextMenu had a v-click-outside directive but did not dismiss reliably. Capture-phase outside mousedown now invokes closeMenu/show=false without blocking the user's click.

## Tabs

A scoped fallback was accepted after the original tab trigger path proved unreliable. Do not replace the application's complete tab model.

## General lesson

Do not accept synthetic automated success as proof of physical keyboard/touch behavior. Several early automated tests passed while the user's physical sequence still failed. Final acceptance always distinguishes automated evidence from user physical confirmation.
