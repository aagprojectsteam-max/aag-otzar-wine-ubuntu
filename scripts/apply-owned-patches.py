#!/usr/bin/env python3
"""Patch only a user's own extracted Otzar installation.

This script intentionally contains no vendor payload. It copies the supplied
files, injects AAG-authored compatibility blocks, and aborts on ambiguity.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def one_replace(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)
def patch_bundle(src: Path, dst: Path) -> None:
    text = src.read_text(errors="strict")
    patched = "this.searchByIds||this.doSearch(e)},clearTxt:function"
    if patched in text:
        dst.write_text(text)
        return
    old = "this.searchByIds},clearTxt:function"
    text = one_replace(text, old, patched, "book-search input compatibility")
    dst.write_text(text)

def patch_index(src: Path, dst: Path) -> None:
    text = src.read_text(errors="strict")
    blocks = []
    for name, marker in [
        ("scale15-phase-snap.js", "__AAG_SCALE15_DRAG_SNAP_PHASE__"),
        ("popup-fix-v2.js", "__AAG_POPUP_FIX_V2__"),
        ("fullscreen-global-v1.js", "__AAG_FULLSCREEN_GLOBAL_V1__"),
        ("touch-scroll-v3.js", "AAG_TOUCH_SCROLL_V3_20260922"),
    ]:
        if marker not in text:
            blocks.append("<script>\n" + (SRC / name).read_text() + "</script>\n")
    if blocks:
        text = one_replace(text, "<head>", "<head>" + "".join(blocks), "HTML head")
    dst.write_text(text)

def patch_asar(src: Path, dst: Path) -> None:
    if not shutil.which("asar"):
        raise SystemExit("asar CLI is required")
    with tempfile.TemporaryDirectory(prefix="aag-otzar-asar-") as td:
        tree = Path(td) / "tree"
        subprocess.run(["asar", "extract", str(src), str(tree)], check=True)
        main = tree / "main.js"
        if not main.is_file():
            raise SystemExit("main.js not found in app.asar")
        text = main.read_text(errors="strict")
        anchor = 'const bytenode = require("./bn");'
        inserts = []
        for name, marker in [
            ("tab-fallback.js", "AAG_PRODUCTION_TAB_FALLBACK_20260915"),
            ("window-control-bridge.js", "AAG_WINDOW_CONTROL_BRIDGE_V1_20260918"),
        ]:
            if marker not in text:
                inserts.append((SRC / name).read_text() + "\n")
        if inserts:
            if text.count(anchor) != 1:
                raise SystemExit("app.asar main.js anchor is not unique")
            text = text.replace(anchor, "\n".join(inserts) + anchor, 1)
            main.write_text(text)
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["asar", "pack", str(tree), str(dst)], check=True)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-asar", type=Path, required=True)
    ap.add_argument("--index-html", type=Path, required=True)
    ap.add_argument("--bundle-js", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ns = ap.parse_args()
    for p in (ns.app_asar, ns.index_html, ns.bundle_js):
        if not p.is_file():
            raise SystemExit(f"missing input: {p}")
    ns.out_dir.mkdir(parents=True, exist_ok=True)

    out_asar = ns.out_dir / "app.asar"
    out_index = ns.out_dir / ns.index_html.name
    out_bundle = ns.out_dir / ns.bundle_js.name
    patch_asar(ns.app_asar, out_asar)
    patch_index(ns.index_html, out_index)
    patch_bundle(ns.bundle_js, out_bundle)

    manifest = {
        "inputs": {str(p): sha(p) for p in (ns.app_asar, ns.index_html, ns.bundle_js)},
        "outputs": {str(p): sha(p) for p in (out_asar, out_index, out_bundle)},
    }
    (ns.out_dir / "patch-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
