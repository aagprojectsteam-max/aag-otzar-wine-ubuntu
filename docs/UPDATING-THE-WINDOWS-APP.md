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
