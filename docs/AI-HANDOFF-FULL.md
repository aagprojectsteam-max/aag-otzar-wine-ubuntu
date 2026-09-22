# AI Handoff — Reproduce Otzar-Wine on Ubuntu from Zero

## Purpose

This document is an execution contract for an AI agent. The target is to reproduce the accepted Ubuntu runtime without repeating the failed experiments that preceded it.

The user must provide a lawful Windows installation of the application, their own content, and their own licensing mechanism. This repository does not provide or bypass any of those.

## Non-negotiable rules

1. Do not modify or publish the user's book/content volume.
2. Keep the content volume read-only during bring-up and normal use.
3. Keep writable application state in a dedicated DATA directory, not in HOME.
4. Do not patch Wine source unless the user explicitly chooses to abandon this architecture.
5. Do not use a VM as a substitute; this design is Wine + nested Xwayland.
6. Do not claim success from synthetic tests alone. Physical keyboard, touch, window, and visual tests must be distinguished from automation.
7. Before every experiment, make a hash/checkpoint of the currently accepted files.
8. Never overwrite the user's only licensed installation. Work on a copy/state tree.

## Reference platform

- Ubuntu 26.04, GNOME Wayland.
- Wine-devel 11.17.
- Nested Xwayland display :201 at 1920x1200 fullscreen.
- Bubblewrap sandbox.
- Electron application launched with touch enabled and scale factor 1.5.
- Final runtime is designed to live under DATA; HOME is used only for desktop integration when required by GNOME.
## Final component map

Host GNOME -> desktop entry -> DATA launcher -> session supervisor -> bubblewrap sandbox -> Wine 11.17 -> nested Xwayland :201 -> Windows Electron application.

Side components:
- input-filter.exe runs inside the same Wine prefix;
- bridge.py certifies host modifier state using EVIOCGKEY + XQueryKeymap;
- touch-focus.sh keeps touch-to-typing focus reliable;
- touch-scroll-v3.js provides fullscreen finger scrolling with a bounded warm page pool and settled reconciliation;
- window-control bridge redirects maximize/minimize;
- scale patch aligns splitter motion to physical pixels;
- popup patch replaces unstable native text menus and repairs outside-click dismissal.

## Phase 0 — inventory the user's installation

Do not assume paths blindly. Confirm that the user's installation contains the equivalent of:
- C:\OtzarApp\OtzarLocal\launcher\bin\x64\app\otzar.exe
- C:\OtzarApp\OtzarLocal\launcher\bin\x64\dist\index.html
- C:\OtzarApp\OtzarLocal\launcher\bin\x64\dist\js\app.*.js
- C:\OtzarApp\OtzarLocal\launcher\bin\x64\app\resources\app.asar
- a local writable catalog data.db.

Also identify the user's content root. In the reference system the application sees it as D:\otzarDisk, but the host source is a read-only mount.

Record SHA256 hashes of the original app.asar, index.html, application bundle JS, executable, and catalog before changes.

## Phase 1 — create the DATA layout

Recommended root:
/mnt/data/AAG/Otzar-Wine/final/Otzar-Wine-<version>

Recommended children:
- state/ — writable Wine prefix and application state;
- runtime/ — supervisor, bridge, input filter, overlays;
- wine-devel/ — tested Wine tree;
- launch/ — user-facing launcher and helper files;
- compatibility/ — minimal sandbox /etc payload;
- burn-in-kit/ — rollback and regression assets;
- docs/ — local acceptance and cleanup notes.
Do not point production at an old laboratory tree. The production root must be self-contained except for deliberate host integration such as the read-only content mount and the desktop entry.

## Phase 2 — Wine 11.17

Use a known Wine 11.17 tree. Store the tested tree in DATA and bind it into the sandbox as /opt/wine-devel so internal scripts can use a stable path.

Verify:
wine --version == wine-11.17

Do not mix Wine binaries from different builds. A previous hybrid-binary experiment crashed.

## Phase 3 — prepare the writable state

Create a dedicated prefix/state copy from the user's lawful installation. The final production runtime must not depend on ~/.wine-otzar-test.

Map the content drive inside the prefix so the application sees D:\otzarDisk.

Keep the local catalog inside writable DATA state. The reference runtime explicitly verifies that the catalog is a real file and not a symlink.

Preserve the expected application TEMP/TMP path. The application also expects path-hint files used by startup/preflight; reproduce them from the user's own installation rather than inventing values.

## Phase 4 — read-only content mount

Mount the content source read-only on the host, then bind it read-only into the sandbox as /content.

Before launch verify both:
- findmnt reports ro;
- os.statvfs(...).f_flag contains ST_RDONLY.

Never run indexing, search-result writes, or application state writes directly against the content source. Writable search-result cache belongs in DATA state and can be bind-mounted over the specific results directory.
## Phase 5 — apply application compatibility patches

Run scripts/apply-owned-patches.py against the user's own files. It creates patched copies and a manifest; it never needs vendor payload from this repository.

The patcher performs three classes of change:
1. app.asar main process: inject the scoped tab fallback and window-control bridge;
2. outer dist/index.html: inject scale/splitter and popup fixes;
3. app bundle JS: ensure the book-search scrollList path executes doSearch unless searchByIds is active.

The bundle patch is guarded. The accepted patched fragment is:
this.searchByIds||this.doSearch(e)},clearTxt:function

If the expected anchor is not unique, STOP. Do not guess. Inspect the new application version and adapt the patch deliberately.

## Phase 6 — disable application-side auto-Hebrew

Use the application's own setting mechanism to disable automatic Hebrew conversion (autoHeb=0).

Reason: the app can transform English physical keystrokes back into Hebrew, which makes OS language-switch testing misleading.

Configure GNOME language switching normally. The reference system supports Super+Space and Alt+Shift / Shift+Alt.

Do not re-enable the Quick Lang Switch extension used in early experiments; it interfered with switching in this environment.

## Phase 7 — build and install the input filter

Install mingw-w64 and run:
scripts/build-input-filter.sh

Place the resulting input-filter.exe in the runtime overlay exposed inside the Wine namespace.
The filter architecture is intentionally narrow:
- it hooks Windows keyboard events;
- before a non-modifier key, it checks whether Wine believes a modifier is down;
- it asks bridge.py whether Linux physical state proves that modifier is actually released;
- only certified stale modifiers are released;
- the triggering key is replayed once;
- text content is never captured by the host bridge.

bridge.py must run as the same user and target the owned application process. It uses nsenter only to enter the application's user/mount namespace.

## Why the filter exists

During host language switching GNOME can consume part of the Super+Space sequence. Wine/Chromium can retain a stale Meta/Super state even though X11 and the physical keyboard report the key released.

Symptom:
- Backspace arrives in Wine;
- DOM focus and caret remain correct;
- Chromium key event has Meta=true;
- beforeinput deleteContentBackward never appears;
- changing to another host window and back clears the stale modifier.

Do not treat missing Backspace as a generic focus bug unless this evidence changes.

## Phase 8 — touch

Launch Electron with --touch-events=enabled.

Start src/touch-focus.sh inside the nested X11 namespace. It reacts to TouchBegin and focuses the unique Otzar top-level window.

Do not replace this with repeated visible Alt-Tab or workspace switching.
## Phase 9 — nested Xwayland

Start Xwayland :201 fullscreen at 1920x1200. The final reference command includes -shm, -nolisten tcp, -ac, and -terminate.

Do not add a nested window manager unless you are intentionally changing the architecture; maximize/minimize behavior was solved at the application/host boundary instead.

## Phase 10 — Electron flags

Use:
--touch-events=enabled
--force-device-scale-factor=1.5
--in-process-gpu

Do not lower the Xwayland physical resolution merely to make the UI smaller. The accepted result keeps 1920x1200 physical and changes only Chromium's scale factor.

## Phase 11 — splitter shimmer fix

At DPR 1.5, Split.js can place a gutter on half physical pixels. The accepted patch computes:
predictedLeft = clientX - gutterWidth / 2
physicalLeft = predictedLeft * devicePixelRatio

Only moves whose physicalLeft is effectively an integer are forwarded.

This rule applies to horizontal gutters, including the main sidebar and the 2px Tsiyunim splitter.

Do not align only raw clientX; that fixed one splitter but not the 2px splitter.
## Phase 12 — window controls

The nested Xwayland root is fullscreen, but the inner Electron BrowserWindow has no nested WM.

Do not use Electron native maximize/minimize directly.

Final behavior:
- TOGGLEMINMAX -> host request -> fit-native -> inner Otzar window becomes 1920x1200;
- MINIMIZE -> host request -> minimize outer Xwayland GNOME window;
- restore -> normal GNOME restore, while inner BrowserWindow stayed alive.

The reference host used a Run-or-Raise GNOME extension DBus API for outer minimize/restore. If a different host integration is used, preserve the semantic rule: minimize the outer host surface, not the inner BrowserWindow.

## Phase 13 — context menus

Text inputs:
- prevent the native contextmenu event for editable fields;
- render an HTML menu with Copy, Cut, Paste, Select All;
- preserve an existing selection across the right-button press;
- use navigator.clipboard for clipboard operations;
- close on outside mousedown, Escape, or window blur.

Book/application menu:
- identify visible BaseContextMenu instances;
- on outside capture-phase mousedown call closeMenu(), or set show=false as fallback;
- do not consume the user's outside click.

## Phase 14 — sandbox

Use bubblewrap so that:
- application state is writable only where required;
- content is read-only;
- /usr and Wine payload are read-only;
- the user's normal HOME is not used as the Wine prefix;
- the host Wayland socket and required USB metadata are exposed deliberately.
Do not hard-code the reference machine's content UUID or licensing USB VID/PID for another user. Discover and validate the new user's own hardware and lawful licensing path.

## Phase 15 — desktop integration

The .desktop entry should execute the DATA launcher directly. Do not route production through an old HOME symlink or lab wrapper.

HOME may legitimately contain:
- ~/.local/share/applications/aag-otzar-wine.desktop
- icons under ~/.local/share/icons.

Those are GNOME integration files, not application state.

## Phase 16 — acceptance tests

At minimum run:
1. normal launch from Apps with no DevTools port;
2. Hebrew -> English -> Backspace immediately;
3. English -> Hebrew -> Backspace immediately;
4. Super+Space, Alt+Shift, Shift+Alt;
5. Caps Lock then Backspace;
6. touch field -> type;
7. touch/mouse scrolling;
8. maximize -> minimize -> restore;
9. main splitter drag;
10. Tsiyunim splitter drag;
11. right-click text field: stable menu, Copy/Cut/Paste/Select All;
12. right-click book area: menu opens, outside click dismisses;
13. close and relaunch from Apps.

Record which tests are automated and which were physically confirmed by the user.
## Expected production invariants

- normal launch has no --remote-debugging-port;
- no listener on the diagnostic DevTools port;
- input filter reports FILTER_READY;
- the final launcher path is in DATA;
- the final Wine tree is in DATA;
- the final prefix/state is in DATA;
- content remains read-only;
- there is no dependency on ~/.wine-otzar-test;
- there is no dependency on an old Otzar-Wine-Lab symlink;
- app bundle originals are hash-checkpointed before every patch.

## Burn-in strategy

After acceptance, keep a compact burn-in kit for 1-2 weeks:
- current final package;
- one pre-change checkpoint;
- prior stable runtime;
- input/language regression scripts;
- window and scale regression evidence;
- full input audit;
- handoff documentation.

Large cloned prefixes, Wine source/build trees, abandoned compatibility matrices, and emergency relocation experiments are not needed for small burn-in fixes once the compact kit exists.

## If something new breaks

First classify the layer:
- host/Wayland;
- nested Xwayland;
- Wine keyboard/window state;
- Electron main process;
- renderer DOM;
- application state/catalog;
- content mount.

Instrument that layer before changing code. Prefer one causal experiment over many speculative tweaks.
## Rollback discipline

Every accepted patch must have:
- before hashes;
- a rollback copy;
- a narrow diff;
- regression results;
- production launch verification.

Do not delete the last known-good final package during burn-in.

## Files in this repository that an AI should study first

1. docs/ARCHITECTURE.md
2. docs/FAILURE-HISTORY.md
3. docs/TEST-MATRIX.md
4. src/input-filter.c
5. src/bridge.py
6. src/scale15-phase-snap.js
7. src/popup-fix-v2.js
8. src/window-control-bridge.js
9. scripts/apply-owned-patches.py

## Completion condition

The project is complete only when the user's own installation launches from Apps, all acceptance tests pass, the application state is in DATA, content stays read-only, and no production path depends on obsolete experiment trees.

Until then, do not optimize for cleanup at the expense of rollback safety.

## v3.3 burn-in additions

- Prefer a DATA hierarchy such as `/mnt/data/WineApps/<application>/` when several Wine applications coexist.
- On cold start, verify the user's required licensing USB device is present and authorized before launching Wine. The reference Kingston device is identified by VID:PID 0951:1666; do not hard-code a serial number in public automation.
- The nested rootful Xwayland surface is tracked by GNOME as `org.freedesktop.Xwayland.desktop`. A user-local override of that desktop ID can supply the application name/icon and make the nested host pinnable in the Dock.
- Fullscreen settings may be scoped to a settings object/tab. Inject `fullscreen-global-v1.js` so the five `full_screen_*` values are present for each loaded settings object and fullscreen layout is reapplied after a book/tab rebuild.
- Keep `LIBGL_ALWAYS_SOFTWARE=1` and `--in-process-gpu`, but do not use `--disable-gpu-compositing` in the accepted v3.3 runtime.
- Physical mouse-wheel A/B testing showed zero frames above 20 ms with Chromium compositing enabled versus nine approximately 166 ms stalls with `--disable-gpu-compositing` during the comparison run.
- For vendor application updates, follow `docs/UPDATING-THE-WINDOWS-APP.md`; never update the only known-good production tree in place.
