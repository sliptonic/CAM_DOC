#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""gypsy capture: replay figure recipes in FreeCAD on an off-screen display.

    python3 gypsy/capture.py output/machine/editor-machine-tab     # one recipe
    python3 gypsy/capture.py --all                                 # every recipe
    python3 gypsy/capture.py --all --freecad ~/FreeCAD/build/bin/FreeCAD   # a different build

A recipe is modules/ROOT/images/recipes/<page>/<what>.py. It sets PAGE, ALT and defines
capture(shot); see gypsy/capture_host.py for the shot object. The image is written to
modules/ROOT/images/<page>/<what>.png and its entry in modules/ROOT/images/manifest.yml is
replaced (STYLE.md §10.3).

FreeCAD is the build of gypsy's own tree (gypsy/config.py, gypsy/freecad-tree.sh) unless
--freecad or GYPSY_FREECAD names a different one. It runs on its own Xvfb display with an empty user directory, so the capture uses default
preferences and does not read or change your own FreeCAD settings. Needs Xvfb.
"""
import argparse
import datetime
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMAGES = os.path.join(ROOT, "modules/ROOT/images")
RECIPES = os.path.join(IMAGES, "recipes")
MANIFEST = os.path.join(IMAGES, "manifest.yml")
HOST = os.path.join(HERE, "capture_host.py")
sys.path.insert(0, HERE)
import config  # noqa: E402

DEFAULT_FREECAD = os.environ.get("GYPSY_FREECAD", config.FREECAD_BIN)


def start_xvfb(size):
    r, w = os.pipe()
    proc = subprocess.Popen(
        ["Xvfb", "-displayfd", str(w), "-screen", "0", f"{size}x24", "-nolisten", "tcp"],
        pass_fds=[w], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.close(w)
    with os.fdopen(r) as fh:
        number = fh.readline().strip()
    if not number:
        proc.kill()
        sys.exit("gypsy capture: Xvfb did not start")
    return proc, f":{number}"


def run_recipe(name, freecad, display, timeout, log_dir):
    recipe = os.path.join(RECIPES, name + ".py")
    out = os.path.join(IMAGES, name + ".png")
    if not os.path.exists(recipe):
        return {"ok": False, "error": f"no recipe: {os.path.relpath(recipe, ROOT)}"}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    home = tempfile.mkdtemp(prefix="gypsy-fc-")
    result_file = os.path.join(home, "result.json")
    tmp_out = os.path.join(home, "shot.png")
    env = dict(os.environ)
    env.pop("WAYLAND_DISPLAY", None)
    env.update(
        DISPLAY=display, QT_QPA_PLATFORM="xcb", LIBGL_ALWAYS_SOFTWARE="1",
        LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8",
        FREECAD_USER_HOME=home, FREECAD_USER_DATA=home, FREECAD_USER_TEMP=home,
        GYPSY_RECIPE=recipe, GYPSY_OUT=tmp_out, GYPSY_RESULT=result_file, GYPSY_REPO=ROOT)
    log = os.path.join(log_dir, name.replace("/", "__") + ".log")
    with open(log, "w") as fh:
        try:
            subprocess.run([freecad, "--write-log", "--log-file", log + ".freecad", HOST], env=env, stdout=fh, stderr=subprocess.STDOUT,
                           timeout=timeout, cwd=home)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"FreeCAD did not finish in {timeout} s (a modal dialog?); log: {log}"}
    if not os.path.exists(result_file):
        return {"ok": False, "error": f"FreeCAD wrote no result; log: {log}"}
    with open(result_file, encoding="utf-8") as fh:
        result = json.load(fh)
    if result.get("output"):                 # what the recipe printed
        with open(log, "a") as fh:
            fh.write(result["output"])
    if result["ok"]:
        shutil.move(tmp_out, out)
        result["file"] = name + ".png"
    shutil.rmtree(home, ignore_errors=True)
    return result


def update_manifest(results, prune):
    """Replace the entries of the captured figures. The comment header of the file is kept.
    With prune, entries whose recipe no longer exists are removed."""
    header, data = [], {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as fh:
            text = fh.read()
        for line in text.splitlines(keepends=True):
            if not line.startswith("#"):
                break
            header.append(line)
        data = yaml.safe_load(text) or {}
    figures = {f["file"]: f for f in data.get("figures") or []}
    for name, result in results.items():
        v = result["freecad"]        # FreeCAD.Version(): major, minor, patch, rev, repo, date, branch, hash
        figures[result["file"]] = {
            "file": result["file"],
            "page": result.get("page"),
            "model": result.get("model"),
            "recipe": f"recipes/{name}.py",
            "freecad": v[7][:11] if len(v) > 7 else ".".join(v[0:3]),
            "date": datetime.date.today().isoformat(),
            "alt": result.get("alt"),
        }
    if prune:
        figures = {k: f for k, f in figures.items() if os.path.exists(os.path.join(IMAGES, f["recipe"]))}
    data["figures"] = [figures[k] for k in sorted(figures)]
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.writelines(header)
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=200)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recipes", nargs="*", help="recipe names: <page>/<what>, without .py")
    ap.add_argument("--all", action="store_true", help="replay every recipe")
    ap.add_argument("--freecad", default=DEFAULT_FREECAD, help="FreeCAD GUI executable (or GYPSY_FREECAD)")
    ap.add_argument("--size", default="1920x1200", help="size of the off-screen display")
    ap.add_argument("--timeout", type=int, default=180, help="seconds allowed per recipe")
    a = ap.parse_args()

    names = list(a.recipes)
    if a.all:
        names = sorted(os.path.relpath(p, RECIPES)[:-3]
                       for p in glob.glob(os.path.join(RECIPES, "**/*.py"), recursive=True))
    if not names:
        ap.error("give a recipe name or --all")
    if not shutil.which("Xvfb"):
        sys.exit("gypsy capture: Xvfb is not installed")
    if not os.access(a.freecad, os.X_OK):
        sys.exit(f"gypsy capture: no FreeCAD executable at {a.freecad}; run gypsy/freecad-tree.sh")

    log_dir = tempfile.mkdtemp(prefix="gypsy-capture-")
    xvfb, display = start_xvfb(a.size)
    failed, done = 0, {}
    try:
        for name in names:
            name = name[:-3] if name.endswith(".py") else name
            result = run_recipe(name, a.freecad, display, a.timeout, log_dir)
            if result["ok"]:
                done[name] = result
                print(f"ok      {name}.png")
            else:
                failed += 1
                print(f"FAILED  {name}\n{result['error']}", file=sys.stderr)
    finally:
        xvfb.terminate()
    update_manifest(done, prune=a.all)
    print(f"logs: {log_dir}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
