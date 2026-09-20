# Updating the Windows Application

Do not run a vendor update directly against the only accepted production tree.

## Safe update model

1. Keep the current accepted DATA package untouched and runnable.
2. Make a new candidate state/prefix from the accepted version.
3. Run the vendor's normal lawful updater only inside that candidate.
4. Inventory and hash the new `otzar.exe`, `app.asar`, `index.html`, application bundle JS, and local schema/version files.
5. Compare the new files with the previous accepted version before applying compatibility patches.
6. Re-run `scripts/apply-owned-patches.py` against the user's updated files.
7. If any guarded anchor is missing or non-unique, STOP; inspect the new vendor version instead of forcing the old patch.

## Reapply the compatibility layer

The current layer includes:
- tab fallback and window-control bridge in `app.asar`;
- scale 1.5 physical-pixel splitter alignment;
- stable context-menu behavior;
- global fullscreen preference enforcement;
- the guarded book-search bundle fix;
- Wine-side stale-modifier input repair;
- touch-focus integration.
## Regression gate

Before promoting an update, verify:
- normal launch from Apps;
- Kingston readiness and lawful licensing path;
- Hebrew/English switching and Backspace;
- touch and touch scrolling;
- mouse-wheel scrolling;
- maximize, minimize, and restore;
- scale 1.5 and both splitter-shimmer fixes;
- fullscreen before and after changing books;
- both context-menu families;
- read-only content mount;
- no DevTools port in production.

## Promotion

Only after the regression gate passes:
1. assign a new final version directory;
2. update the Apps launcher atomically;
3. keep the previous accepted version as rollback during burn-in;
4. update hashes, changelog, handoff, and GitHub release;
5. remove the previous version only after the new burn-in is accepted.

Never let an application update silently overwrite the only known-good production package.

## One-line handoff for a future AI session

When a new vendor version is available, give the AI this repository and say:

> Update my installed Otzar Windows application using `docs/UPDATING-THE-WINDOWS-APP.md`. Preserve the current accepted production tree as rollback, build and test a separate candidate, reapply only guarded compatibility patches, run the complete regression gate, and promote the candidate only if every required test passes.

The AI should also read `docs/AI-HANDOFF-FULL.md`, `docs/ARCHITECTURE.md`, `docs/FAILURE-HISTORY.md`, and the latest `CHANGELOG.md` before changing production.

## Current accepted checkpoint

- Release line: `v3.3.0-burn-in`.
- DATA layout: `/mnt/data/WineApps/Otzar-HaHochma/`.
- Production uses Wine 11.17, scale 1.5, `--in-process-gpu`, software GL, and Chromium compositing.
- The Apps launcher owns the Kingston/content lifecycle only when it created the mount: readiness check -> verified read-only loop/mount -> application -> verified unmount/loop detach on exit.
- Preserve Dock/Apps integration, global fullscreen persistence, language/Backspace repair, popup fixes, touch behavior, and splitter-shimmer fixes.
- Never update the only accepted production tree in place.
