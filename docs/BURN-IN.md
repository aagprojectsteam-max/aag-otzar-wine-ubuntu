# Burn-in Guide

The reference v3.2.0 package is intentionally treated as final-for-use while remaining under a 1-2 week burn-in period.

## Keep during burn-in

- the full self-contained final package in DATA;
- one checkpoint from immediately before the newest patch family;
- one prior stable runtime for rollback/comparison;
- language/Backspace regression scripts;
- window-control and scale regression evidence;
- input audit tooling;
- the public repository worktree and handoff documentation.

## Do not keep just for burn-in

Large cloned Wine prefixes, full Wine source/build trees, abandoned compatibility matrices, old VM/WinBoat/Bottles experiments, and emergency relocation copies are not required for small fixes once the compact kit above exists.

## Patch procedure

1. Hash the accepted files.
2. Make a rollback copy.
3. Reproduce the issue on diagnostic mode if possible.
4. Identify the layer before modifying code.
5. Make one narrow change.
6. Re-run the relevant automated matrix.
7. Launch normally from Apps with DevTools closed.
8. Obtain physical/visual user confirmation where automation is insufficient.
9. Update the checkpoint and documentation.

Do not delete the last accepted final package during burn-in.
