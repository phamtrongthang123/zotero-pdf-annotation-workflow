#!/usr/bin/env python3
"""Run an explicit JavaScript file in Zotero's Run JavaScript window.

This is X11 UI automation only. It does not decide what to run and does not
verify Zotero writes. Always run audit_manifest.py after an annotation or tag
payload.
"""

from __future__ import annotations

import argparse
import ctypes
import shutil
import subprocess
import sys
import time
from pathlib import Path


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command is unavailable: {name}")


def find_window(title: str) -> str:
    output = subprocess.check_output(["wmctrl", "-l"], text=True)
    matches = []
    for line in output.splitlines():
        fields = line.split(None, 3)
        if len(fields) == 4 and fields[3].strip() == title:
            matches.append(fields[0])
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one window titled {title!r}; found {len(matches)}"
        )
    return matches[0]


class XTestKeyboard:
    def __init__(self) -> None:
        self.x11 = ctypes.CDLL("libX11.so.6")
        self.xtst = ctypes.CDLL("libXtst.so.6")
        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        self.x11.XStringToKeysym.restype = ctypes.c_ulong
        self.x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x11.XKeysymToKeycode.restype = ctypes.c_uint
        self.x11.XFlush.argtypes = [ctypes.c_void_p]
        self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.xtst.XTestFakeKeyEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        self.display = self.x11.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("Could not open the X11 display")

    def keycode(self, name: str) -> int:
        symbol = self.x11.XStringToKeysym(name.encode())
        code = self.x11.XKeysymToKeycode(self.display, symbol)
        if not code:
            raise RuntimeError(f"Could not resolve X11 key: {name}")
        return code

    def chord(self, key: str, modifiers: tuple[str, ...] = ()) -> None:
        for modifier in modifiers:
            self.xtst.XTestFakeKeyEvent(
                self.display, self.keycode(modifier), 1, 0
            )
        code = self.keycode(key)
        self.xtst.XTestFakeKeyEvent(self.display, code, 1, 0)
        self.xtst.XTestFakeKeyEvent(self.display, code, 0, 0)
        for modifier in reversed(modifiers):
            self.xtst.XTestFakeKeyEvent(
                self.display, self.keycode(modifier), 0, 0
            )
        self.x11.XFlush(self.display)
        time.sleep(0.25)

    def close(self) -> None:
        if self.display:
            self.x11.XCloseDisplay(self.display)
            self.display = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("javascript", type=Path)
    parser.add_argument("--window-title", default="Run JavaScript")
    parser.add_argument("--wait-seconds", type=float, default=10.0)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required acknowledgement that the selected JavaScript may write Zotero",
    )
    args = parser.parse_args()

    source = args.javascript.resolve()
    if not source.is_file():
        raise RuntimeError(f"JavaScript file does not exist: {source}")
    if not args.yes:
        print(f"Refusing to execute without --yes: {source}", file=sys.stderr)
        return 2
    if args.wait_seconds < 0 or args.wait_seconds > 60:
        raise RuntimeError("--wait-seconds must be between 0 and 60")

    require_command("wmctrl")
    require_command("xclip")
    window = find_window(args.window_title)
    payload = source.read_bytes()
    if not payload.strip():
        raise RuntimeError(f"JavaScript file is empty: {source}")

    clipboard = subprocess.Popen(
        ["xclip", "-selection", "clipboard", "-quiet"],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert clipboard.stdin is not None
    clipboard.stdin.write(payload)
    clipboard.stdin.close()

    keyboard = XTestKeyboard()
    try:
        subprocess.run(["wmctrl", "-ia", window], check=True)
        time.sleep(0.5)
        keyboard.chord("a", ("Control_L",))
        keyboard.chord("v", ("Control_L",))
        time.sleep(0.5)
        keyboard.chord("r", ("Control_L",))
        time.sleep(args.wait_seconds)
    finally:
        keyboard.close()
        if clipboard.poll() is None:
            clipboard.terminate()
        try:
            clipboard.wait(timeout=2)
        except subprocess.TimeoutExpired:
            clipboard.kill()
            clipboard.wait(timeout=2)

    print(
        f"Submitted {source} to Zotero window {window}. "
        "This is not verification; run audit_manifest.py next."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
