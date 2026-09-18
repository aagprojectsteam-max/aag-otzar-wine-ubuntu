# Test Matrix

## Accepted behavior before burn-in

| Area | Result | Evidence |
| --- | --- | --- |
| Hebrew/English switch via Super+Space | PASS | 6-cycle regression across both directions |
| Alt+Shift / Shift+Alt | PASS | same regression matrix |
| Backspace immediately after layout switch | PASS | 6/6 |
| Caps Lock + Backspace | PASS | 3/3 |
| Tabs + fallback | PASS | UI/bridge checks |
| Touch | PASS | user physical confirmation |
| Touch scrolling | PASS | user physical confirmation |
| Maximize | PASS | automated stress + user physical confirmation |
| Minimize | PASS | automated stress + user physical confirmation |
| Restore after minimize | PASS | automated stress + user physical confirmation |
| Frozen/stale frame after window operation | FIXED | user physical confirmation |
| Scale 1.5 | PASS | DPR/viewport checks + user visual confirmation |
| Main splitter shimmer | FIXED | integer physical-pixel phase + user confirmation |
| Tsiyunim splitter shimmer | FIXED | integer physical-pixel phase + user confirmation |
| Text-field context menu functions | PASS automated | Copy/Cut/Paste/Select All cold-start test |
| Book context-menu outside-click dismissal | PASS automated | open -> outside click -> removed |
| Popup fixes with language/Backspace | PASS | language regression 6/6 |
| Popup fixes with max/min/restore | PASS | regression after patch |

## Production invariants

- No DevTools port in normal production.
- Content mount is read-only.
- Writable app/prefix state is in DATA.
- Active Apps launcher points directly into DATA.
- No active dependency on ~/.wine-otzar-test.
- No active dependency on the old Otzar-Wine-Lab symlink.
- No Wine source patch is required.

## Burn-in policy

During the 1-2 week burn-in, treat any new issue as a regression against this matrix. Preserve the current final package before every new patch and re-run the smallest relevant regression set plus one normal Apps launch.
