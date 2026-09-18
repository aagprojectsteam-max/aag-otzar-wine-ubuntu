# Architecture

## 1. Host

The reference machine runs Ubuntu 26.04 with GNOME on Wayland. The application itself runs inside Wine 11.17 on a nested Xwayland server at :201.

Host responsibilities:
- provide the Wayland session and GNOME window lifecycle;
- expose the user's licensed content as a read-only mount;
- expose only required licensing metadata to the sandbox;
- provide physical keyboard state from /dev/input;
- own minimize/restore of the outer Xwayland host window.

## 2. Nested display

Xwayland is launched fullscreen at 1920x1200 with no nested window manager. The Windows Electron application renders inside this display.

Why this matters: Electron's native maximize/minimize controls target the inner BrowserWindow, but there is no nested WM to give those state transitions normal desktop semantics. The outer Xwayland surface is what GNOME actually manages.

## 3. Bubblewrap sandbox

The runtime uses bubblewrap to create a bounded namespace:
- /usr is read-only;
- the tested Wine tree is read-only-bound into /opt/wine-devel inside the sandbox;
- the licensed content mount is read-only-bound as /content;
- the writable Wine/app state is bound as /state;
- the Wayland socket is exposed only as /host-wayland;
- selected USB metadata is exposed read-only under /usbmeta;
- temporary files are isolated.

## 4. Wine prefix and application state

The writable prefix lives in DATA, not HOME. The application is expected at the normal Windows path under C:\OtzarApp\OtzarLocal. Content is mapped as D:\otzarDisk.

The local catalog data.db is kept in writable DATA state. The content source remains read-only.

## 5. Application flags

The accepted Electron launch flags are:
- --touch-events=enabled
- --force-device-scale-factor=1.5
- --in-process-gpu
- --disable-gpu-compositing

The nested Xwayland physical size remains 1920x1200. At scale 1.5 Chromium reports a logical viewport near 1280x800 while retaining the full physical raster.

## 6. Keyboard architecture

GNOME handles the host language shortcut. A lost host key-up can leave Wine/Chromium believing Super/Meta is still held. Backspace then arrives with Meta=true and Chromium never emits deleteContentBackward.

The final repair is not a global key remapper. A Wine low-level keyboard hook checks stale Windows modifier state before a non-modifier key. It asks the host bridge for a physical-state certificate. Only modifiers proven physically released are sent as KEYUP, and the triggering key is replayed once.

The bridge combines Linux EVIOCGKEY state and XQueryKeymap modifier state. It never reads typed text.

## 7. Touch

Touch events are enabled natively. The touch-focus helper watches TouchBegin and focuses the Otzar top-level window so typing after touch remains reliable.

## 8. Window controls

Maximize and minimize are intercepted at the Electron IPC layer.

Maximize is translated to the existing fit-native operation, restoring the inner Otzar window to the 1920x1200 nested root.

Minimize is translated to minimizing the outer Xwayland host window in GNOME. The inner BrowserWindow stays alive. Restore therefore returns the existing renderer instead of a stale frozen frame.

## 9. Scale and splitter stability

At devicePixelRatio 1.5, a one-CSS-pixel drag can alternate between integer and half physical pixels. Chromium then re-rasterizes text at alternating phases, visible as shimmer.

The scale patch computes the predicted gutter-left coordinate using clientX minus half the gutter width. Mouse moves that would place the gutter on a fractional physical pixel are suppressed. This is applied to horizontal splitters only.

## 10. Context menus

Native Chromium text-field menus created visible popup flashing in the nested display. Editable fields therefore use an in-page HTML menu providing Copy, Cut, Paste, and Select All through the Clipboard API.

The application's BaseContextMenu intended to close through v-click-outside, but that directive did not dismiss reliably in this environment. A capture-phase outside mousedown closes only visible BaseContextMenu instances.

## 11. Tabs

A small production fallback preserves the accepted tab behavior when the original trigger path fails. It is deliberately scoped and does not replace the application's tab model.

## 12. Direct DATA launch

The GNOME desktop entry points directly to the launcher inside DATA. HOME contains only desktop-integration files such as the .desktop file and icons. The active runtime does not rely on the old HOME Wine prefix or legacy symlinks.
