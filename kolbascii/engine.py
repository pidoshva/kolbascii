"""Terminal runner shared by every animation.

An animation module exposes a ``Scene`` class:

    class Scene:
        def __init__(self, cols, rows): ...
        def render(self, t):            # t = seconds since start
            return chars, colors        # flat lists of length cols*rows

``chars[i]`` is a one-character string or None, ``colors[i]`` an (r, g, b)
tuple. The engine owns the terminal: alternate screen, hidden cursor, keys,
resizes, frame pacing and restoring everything on exit.
"""
import math
import os
import platform
import select
import shutil
import sys
import time

BG = (5, 7, 13)
DIM = (96, 104, 122)
ACCENT = (255, 196, 90)
HINT = (70, 76, 92)


def _truecolor():
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return True
    prog = os.environ.get("TERM_PROGRAM", "")
    if prog in ("iTerm.app", "WezTerm", "vscode", "ghostty", "kitty", "Hyper", "Tabby", "rio"):
        return True
    if prog == "Apple_Terminal":        # 24-bit colour arrived in macOS 26
        try:
            return int(platform.mac_ver()[0].split(".")[0]) >= 26
        except ValueError:
            return False
    term = os.environ.get("TERM", "")
    return "kitty" in term or "direct" in term


TRUECOLOR = _truecolor()
_codes = {}


def color_code(c):
    code = _codes.get(c)
    if code is None:
        if TRUECOLOR:
            code = "\x1b[38;2;%d;%d;%dm" % c
        else:                               # nearest colour in the 256-colour cube
            r, g, b = (int(round(v / 255 * 5)) for v in c)
            code = "\x1b[38;5;%dm" % (16 + 36 * r + 6 * g + b)
        _codes[c] = code
    return code


def to_ansi(chs, cos_, cols, rows):
    out = []
    last = None
    for y in range(rows):
        row = []
        base = y * cols
        for x in range(cols):
            ch = chs[base + x]
            if ch is None or ch == " ":
                row.append(" ")
                continue
            c = cos_[base + x]
            if c != last:
                row.append(color_code(c))
                last = c
            row.append(ch)
        out.append("".join(row))
    return "\x1b[H" + "\n".join(out)


class Canvas:
    """Helpers for 2D overlays (text, HUD, banner) on top of a rendered frame."""

    def __init__(self, chs, cos_, cols, rows):
        self.chs, self.cos, self.cols, self.rows = chs, cos_, cols, rows

    def put(self, row, col, ch, rgb):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            i = row * self.cols + col
            self.chs[i], self.cos[i] = ch, rgb

    def text(self, row, col, s, rgb):
        for i, ch in enumerate(s):
            self.put(row, col + i, ch, rgb)

    def clear(self, row, col0, col1):
        if 0 <= row < self.rows:
            for c in range(max(0, col0), min(self.cols, col1)):
                self.chs[row * self.cols + c] = None

    def banner(self, t, start, message, palette, row=None, speed=10.0):
        """Type ``message`` out from time ``start`` with cycling colors."""
        if t <= start:
            return
        row = self.rows - 5 if row is None else row
        x0 = (self.cols - len(message)) // 2
        shown = min(len(message), int((t - start) * speed))
        for rr in (row - 1, row, row + 1):
            self.clear(rr, x0 - 3, x0 + shown + 3)
        for i, ch in enumerate(message[:shown]):
            if ch != " ":
                tint = palette[(i // 2 + int(t * 1.5)) % len(palette)]
                k = 0.85 + 0.15 * math.sin(t * 5 + i)
                self.put(row, x0 + i, ch, tuple(int(v * k) for v in tint))

    def hud(self, t, lines):
        """``lines``: list of rows, each a list of (text, rgb) chunks, drawn bottom-left."""
        rows = self.rows
        all_lines = lines + [[("space pause · r restart · q quit", HINT)]]
        for k, chunks in enumerate(all_lines):
            row = rows - len(all_lines) + k
            col = 1
            for s, rgb in chunks:
                self.text(row, col, s, rgb)
                col += len(s) + 3
        ts = "t %05.1f" % t
        self.text(0, self.cols - len(ts) - 1, ts, ACCENT)


def run(scene_cls, seconds=None, frames=None, fps=30):
    """Play ``scene_cls`` full-screen until q / Esc / Ctrl+C (or ``seconds`` elapse).

    ``frames`` renders that many frames at a fixed step as fast as possible,
    which is what the tests use.
    """
    cols, rows = shutil.get_terminal_size((120, 50))
    scene = scene_cls(cols, rows)
    out = sys.stdout
    tty_mode = None
    interactive = sys.stdin.isatty() and frames is None
    if interactive:
        import termios
        import tty
        fd = sys.stdin.fileno()
        tty_mode = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    bg = ("\x1b[48;2;%d;%d;%dm" % BG) if TRUECOLOR else "\x1b[48;5;233m"
    out.write("\x1b[?1049h\x1b[?25l" + bg + "\x1b[2J")
    t, paused, last, n = 0.0, False, time.time(), 0
    try:
        while True:
            now = time.time()
            dt = 1.0 / fps if frames is not None else min(now - last, 0.1)
            last = now
            if not paused:
                t += dt
            if seconds is not None and t >= seconds:
                return
            if tty_mode is not None:
                while select.select([sys.stdin], [], [], 0)[0]:
                    k = sys.stdin.read(1)
                    if k in ("q", "Q", "\x1b", "\x03"):
                        return
                    if k == " ":
                        paused = not paused
                    if k in ("r", "R"):
                        t = 0.0
            c2, r2 = shutil.get_terminal_size((cols, rows))
            if frames is None and (c2, r2) != (cols, rows):
                cols, rows = c2, r2
                scene = scene_cls(cols, rows)
                out.write("\x1b[2J")
            chs, cos_ = scene.render(t)
            out.write(bg + to_ansi(chs, cos_, cols, rows))
            out.flush()
            n += 1
            if frames is not None:
                if n >= frames:
                    return
                continue
            spent = time.time() - now
            if spent < 1.0 / fps:
                time.sleep(1.0 / fps - spent)
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    finally:
        if tty_mode is not None:
            import termios
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, tty_mode)
        try:
            out.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            out.flush()
        except (BrokenPipeError, OSError):
            # stdout went away (e.g. piped into `head`); don't spew a traceback
            sys.stdout = None
