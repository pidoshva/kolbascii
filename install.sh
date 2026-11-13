#!/usr/bin/env bash
# kolbascii installer
#
#   curl -fsSL https://raw.githubusercontent.com/pidoshva/kolbascii/main/install.sh | bash
#
# Options (when piping, pass them as:  ... | bash -s -- --uninstall):
#   --uninstall        remove kolbascii and the PATH line it added
#   --no-modify-path   don't touch your shell startup file
#
# Environment overrides: KOLBASCII_HOME (default ~/.kolbascii),
# KOLBASCII_BIN (default ~/.local/bin), KOLBASCII_BRANCH (default main).
set -eu

# --- find a Python 3.8+ ------------------------------------------------------
find_python() {
    for c in python3 python3.14 python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python; do
        p=$(command -v "$c" 2>/dev/null) || continue
        # macOS ships a /usr/bin/python3 stub that pops up an installer dialog
        # when the developer tools are missing; don't poke it in that case.
        if [ "$p" = "/usr/bin/python3" ] && [ "$(uname -s)" = "Darwin" ] && ! xcode-select -p >/dev/null 2>&1; then
            continue
        fi
        if "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
            echo "$p"
            return 0
        fi
    done
    return 1
}

if ! PY=$(find_python); then
    printf '\n  \033[1;31m✗\033[0m kolbascii needs Python 3.8 or newer, and none was found.\n\n'
    case "$(uname -s)" in
        Darwin) printf '    Install it with:  \033[1mbrew install python\033[0m   (or: xcode-select --install)\n\n' ;;
        Linux)  printf '    Install it with:  \033[1msudo apt install python3\033[0m   (or your distro'"'"'s package manager)\n\n' ;;
        *)      printf '    Get it from https://www.python.org/downloads/\n\n' ;;
    esac
    exit 1
fi

# When run from a clone (./install.sh), install the files right here instead of downloading.
KOLBASCII_LOCAL_SRC=""
if [ -n "${BASH_SOURCE:-}" ] && [ -f "${BASH_SOURCE[0]:-}" ]; then
    here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
    if [ -f "$here/kolbascii/__main__.py" ]; then
        KOLBASCII_LOCAL_SRC="$here"
    fi
fi
export KOLBASCII_LOCAL_SRC

exec "$PY" - "$@" <<'PYTHON'
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time

REPO = "pidoshva/kolbascii"
BRANCH = os.environ.get("KOLBASCII_BRANCH", "main")
HOME_DIR = os.path.expanduser(os.environ.get("KOLBASCII_HOME", "~/.kolbascii"))
MANIFEST = os.path.join(HOME_DIR, ".kolbascii-manifest.json")


def _path_dirs():
    return [os.path.realpath(os.path.expanduser(p)) for p in os.environ.get("PATH", "").split(os.pathsep) if p]


def _pick_bin():
    """Where the command goes. Prefer a folder that's already on PATH and writable,
    so `kolbascii` works the moment the installer finishes, in this same terminal."""
    if os.environ.get("KOLBASCII_BIN"):
        return os.path.expanduser(os.environ["KOLBASCII_BIN"])
    on_path = _path_dirs()
    for cand in ("~/.local/bin", "~/bin", "/opt/homebrew/bin", "/usr/local/bin"):
        d = os.path.expanduser(cand)
        if os.path.isdir(d) and os.path.realpath(d) in on_path and os.access(d, os.W_OK):
            return d
    return os.path.expanduser("~/.local/bin")


def _read_manifest():
    try:
        import json
        with open(MANIFEST) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


BIN_DIR = _read_manifest().get("bin_dir") if "--uninstall" in sys.argv[1:] else None
BIN_DIR = BIN_DIR or _pick_bin()
TARBALL = os.environ.get("KOLBASCII_TARBALL",
                         "https://codeload.github.com/%s/tar.gz/refs/heads/%s" % (REPO, BRANCH))
LOCAL = os.environ.get("KOLBASCII_LOCAL_SRC") if not os.environ.get("KOLBASCII_TARBALL") else ""
ARGS = sys.argv[1:]
UNINSTALL = "--uninstall" in ARGS
NO_PATH = "--no-modify-path" in ARGS
MARK_START, MARK_END = "# >>> kolbascii >>>", "# <<< kolbascii <<<"

out = sys.stdout
FANCY = out.isatty() and not os.environ.get("NO_COLOR") and os.environ.get("TERM", "") != "dumb"


def _truecolor():
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return True
    prog = os.environ.get("TERM_PROGRAM", "")
    if prog in ("iTerm.app", "WezTerm", "vscode", "ghostty", "kitty", "Hyper", "Tabby", "rio"):
        return True
    if prog == "Apple_Terminal":
        try:
            return int(platform.mac_ver()[0].split(".")[0]) >= 26
        except ValueError:
            return False
    return "kitty" in os.environ.get("TERM", "") or "direct" in os.environ.get("TERM", "")


TRUE = _truecolor()
RESET = "\x1b[0m" if FANCY else ""
BOLD = "\x1b[1m" if FANCY else ""

GRAD = ((255, 94, 98), (255, 153, 102), (255, 214, 120))
DIM = (110, 116, 132)
FAINT = (58, 62, 74)
TEXT = (226, 229, 236)
GREEN = (110, 225, 140)
RED = (255, 95, 95)
WHITE = (255, 255, 255)


def fg(c):
    if not FANCY:
        return ""
    if TRUE:
        return "\x1b[38;2;%d;%d;%dm" % c
    r, g, b = (int(round(v / 255 * 5)) for v in c)
    return "\x1b[38;5;%dm" % (16 + 36 * r + 6 * g + b)


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def grad(k):
    k = max(0.0, min(1.0, k)) * (len(GRAD) - 1)
    i = min(int(k), len(GRAD) - 2)
    return mix(GRAD[i], GRAD[i + 1], k - i)


def paint(c, s):
    return fg(c) + s + RESET


def write(s):
    out.write(s)
    out.flush()


def cols():
    return shutil.get_terminal_size((80, 24)).columns


def tilde(p):
    h = os.path.expanduser("~")
    return "~" + p[len(h):] if p.startswith(h + os.sep) or p == h else p


LOGO = [
    "██╗  ██╗ ██████╗ ██╗     ██████╗  █████╗ ███████╗ ██████╗██╗██╗",
    "██║ ██╔╝██╔═══██╗██║     ██╔══██╗██╔══██╗██╔════╝██╔════╝██║██║",
    "█████╔╝ ██║   ██║██║     ██████╔╝███████║███████╗██║     ██║██║",
    "██╔═██╗ ██║   ██║██║     ██╔══██╗██╔══██║╚════██║██║     ██║██║",
    "██║  ██╗╚██████╔╝███████╗██████╔╝██║  ██║███████║╚██████╗██║██║",
    "╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝╚═╝",
]
SHADOW = set("╗╝║═╔╚")


def logo_frame(front):
    h, w = len(LOGO), len(LOGO[0])
    rows = []
    for y, line in enumerate(LOGO):
        buf = ["\r  "]
        for x, ch in enumerate(line):
            k = front - (x + (h - y) * 2.5)
            if ch == " " or k < 0:
                buf.append(" ")
                continue
            base = grad(x / w)
            if ch in SHADOW:
                base = mix(base, (0, 0, 0), 0.45)
            c = mix(WHITE, base, k / 6.0) if k < 6 else base
            buf.append(fg(c) + ch)
        buf.append(RESET + "\x1b[K\n")
        rows.append("".join(buf))
    return "".join(rows)


def banner(subtitle):
    write("\n")
    if not FANCY:
        write("  kolbascii · " + subtitle + "\n\n")
        return
    if cols() < len(LOGO[0]) + 4:
        write("  " + BOLD + paint(GRAD[0], "k o l b a s c i i") + "\n")
    else:
        h, w = len(LOGO), len(LOGO[0])
        end = w + h * 2.5 + 8
        write("\n" * h)
        steps = 34
        for f in range(steps + 1):
            write("\x1b[%dA" % h + logo_frame(end * f / steps))
            time.sleep(0.016)
    write("\n  ")
    for i, ch in enumerate(subtitle):
        write(paint(mix(DIM, TEXT, 0.25), ch))
        time.sleep(0.006)
    write("\n\n")


class StepFailed(Exception):
    def __init__(self, msg, hint=""):
        Exception.__init__(self, msg)
        self.hint = hint


class Ctx:
    progress = None
    note = ""


SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
LABEL_W = 24


def bar_width():
    return max(10, min(30, cols() - LABEL_W - 52))


def draw(label, frac, state, elapsed, note, tick):
    bw = bar_width()
    if state == "run":
        icon = paint(grad((tick % 30) / 30.0), SPIN[tick % len(SPIN)])
    elif state == "ok":
        icon = paint(GREEN, "✓")
    else:
        icon = paint(RED, "✗")
    halves = int(round(frac * bw * 2))
    full, half = halves // 2, halves % 2
    shimmer = (tick * 0.9) % (bw + 10) - 5 if state == "run" else -99
    cells = []
    for i in range(bw):
        if i < full:
            c = grad(i / max(1, bw - 1))
            if state == "fail":
                c = mix(c, RED, 0.6)
            glow = max(0.0, 1 - abs(i - shimmer) / 3.0)
            if glow:
                c = mix(c, WHITE, 0.45 * glow)
            cells.append(fg(c) + "━")
        elif i == full and half:
            cells.append(fg(grad(i / max(1, bw - 1))) + "╸")
        else:
            cells.append(fg(FAINT) + "━")
    pct = paint(TEXT if state != "fail" else RED, "%3d%%" % int(frac * 100))
    t = paint(DIM, "%4.1fs" % elapsed)
    lab = (BOLD if state == "run" else "") + paint(TEXT if state != "ok" else mix(TEXT, DIM, 0.35),
                                                     label.ljust(LABEL_W)) + RESET
    room = cols() - (bw + LABEL_W + 20)
    if note and len(note) > room:
        note = note[:max(0, room - 1)] + "…" if room > 8 else ""
    tail = "  " + paint(DIM, note) if note and state != "run" else ""
    return "\r\x1b[2K  %s %s %s%s %s  %s%s" % (icon, lab, "".join(cells), RESET, pct, t, tail)


def run_step(i, n, label, fn, min_time=0.32):
    ctx = Ctx()
    result = {}

    def worker():
        try:
            fn(ctx)
        except StepFailed as e:
            result["err"] = e
        except Exception as e:  # noqa: BLE001
            result["err"] = StepFailed(str(e) or e.__class__.__name__)

    start = time.time()
    th = threading.Thread(target=worker)
    th.daemon = True
    th.start()
    if not FANCY:
        th.join()
        el = time.time() - start
        if "err" in result:
            write("  [%d/%d] %s ... failed\n" % (i, n, label))
            raise result["err"]
        write("  [%d/%d] %s ... ok%s\n" % (i, n, label, "  (" + ctx.note + ")" if ctx.note else ""))
        return el
    shown, tick = 0.0, 0
    while True:
        el = time.time() - start
        alive = th.is_alive()
        if "err" in result and not alive:
            write(draw(label, max(shown, 0.05), "fail", el, "", tick) + "\n")
            raise result["err"]
        if not alive and el >= min_time:
            target = 1.0
        elif ctx.progress is not None:
            target = min(0.97, ctx.progress)
        else:
            target = 0.93 * (1 - math.exp(-el / (min_time * 0.6)))
        shown += (target - shown) * (0.38 if target == 1.0 else 0.2)
        if target == 1.0 and shown > 0.99:
            write(draw(label, 1.0, "ok", el, ctx.note, tick) + "\n")
            return el
        write(draw(label, shown, "run", el, "", tick))
        tick += 1
        time.sleep(1 / 45)


def boxed(lines, width=60):
    """lines: list of (text, rgb, bold). Draws a rounded box with a gradient border."""
    w = min(width, cols() - 4)
    inner = w - 2
    if not FANCY:
        for text, _, _ in lines:
            write("  " + text + "\n")
        return

    def edge(left, mid, right):
        s = [fg(grad(0)) + left]
        for i in range(inner):
            s.append(fg(grad(i / inner)) + mid)
        s.append(fg(grad(1)) + right + RESET)
        return "  " + "".join(s)

    write(edge("╭", "─", "╮") + "\n")
    time.sleep(0.03)
    for text, c, bold in lines:
        pad = inner - 3 - len(text)
        body = (BOLD if bold else "") + paint(c, text) + RESET + " " * max(0, pad)
        write("  " + paint(grad(0), "│") + "   " + body + paint(grad(1), "│") + "\n")
        time.sleep(0.03)
    write(edge("╰", "─", "╯") + "\n")


def fail_box(err):
    write("\n")
    lines = [("✗  " + str(err), RED, True)]
    if getattr(err, "hint", ""):
        for h in err.hint.split("\n"):
            lines.append(("   " + h, TEXT, False))
    boxed(lines, width=max(60, max(len(t) for t, _, _ in lines) + 8))
    write("\n")


# ---------------------------------------------------------------- install steps
state = {}


def step_check(ctx):
    v = sys.version_info
    if not LOCAL and not shutil.which("curl"):
        raise StepFailed("curl is needed to download kolbascii.", "Install curl and run the installer again.")
    for d in (os.path.dirname(HOME_DIR.rstrip("/")) or "/", os.path.dirname(BIN_DIR.rstrip("/")) or "/"):
        if os.path.isdir(d) and not os.access(d, os.W_OK):
            raise StepFailed("Can't write to " + tilde(d) + ".",
                             "Set KOLBASCII_HOME / KOLBASCII_BIN to folders you own.")
    ctx.note = "python %d.%d.%d · %s" % (v[0], v[1], v[2], "macOS" if sys.platform == "darwin" else platform.system())


def step_download(ctx):
    tmp = tempfile.mkdtemp(prefix="kolbascii-")
    state["tmp"] = tmp
    if LOCAL:
        src = os.path.join(LOCAL, "kolbascii")
        shutil.copytree(src, os.path.join(tmp, "src", "kolbascii"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "._*", ".DS_Store"))
        shutil.copy2(os.path.join(LOCAL, "install.sh"), os.path.join(tmp, "src", "install.sh"))
        state["src"] = os.path.join(tmp, "src")
        ctx.note = "from local checkout"
        return
    tgz = os.path.join(tmp, "kolbascii.tar.gz")
    proc = subprocess.Popen(["curl", "-fsSL", "--retry", "2", "-o", tgz, TARBALL],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    expected = 40 * 1024
    while proc.poll() is None:
        if os.path.exists(tgz):
            ctx.progress = min(0.95, os.path.getsize(tgz) / expected)
        time.sleep(0.05)
    if proc.returncode != 0:
        err = proc.stderr.read().decode(errors="ignore").strip()
        raise StepFailed("Download failed: " + (err or "curl exited with %d" % proc.returncode),
                         "Check your connection and try again.")
    size = os.path.getsize(tgz)
    with tarfile.open(tgz) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(os.path.join(tmp, "x"), filter="data")
        else:
            tar.extractall(os.path.join(tmp, "x"))
    for root, dirs, files in os.walk(os.path.join(tmp, "x")):
        if os.path.basename(root) == "kolbascii" and "__main__.py" in files:
            state["src"] = os.path.dirname(root)
            break
    else:
        raise StepFailed("The download didn't contain kolbascii.")
    ctx.note = "%d KB from GitHub" % max(1, size // 1024)


def step_files(ctx):
    src = state["src"]
    dest = os.path.join(HOME_DIR, "kolbascii")
    os.makedirs(HOME_DIR, exist_ok=True)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(os.path.join(src, "kolbascii"), dest,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "._*", ".DS_Store"))
    if os.path.exists(os.path.join(src, "install.sh")):          # kept for `kolbascii uninstall`
        shutil.copy2(os.path.join(src, "install.sh"), os.path.join(dest, "install.sh"))
    import compileall
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        compileall.compile_dir(dest, quiet=2)
    m = re.search(r'__version__\s*=\s*"([^"]+)"', open(os.path.join(dest, "__init__.py")).read())
    state["version"] = m.group(1) if m else "?"
    n = sum(1 for _, _, fs in os.walk(dest) for f in fs if f.endswith(".py") and not f.startswith("._"))
    ctx.note = "%d modules → %s" % (n, tilde(HOME_DIR))


LAUNCHER = """#!/bin/sh
# kolbascii launcher, written by the kolbascii installer.
KOLBASCII_HOME="${KOLBASCII_HOME:-%(home)s}"
export KOLBASCII_HOME
PY="%(py)s"
[ -x "$PY" ] || PY=$(command -v python3)
PYTHONPATH="$KOLBASCII_HOME${PYTHONPATH:+:$PYTHONPATH}" exec "$PY" -m kolbascii "$@"
"""


def step_command(ctx):
    for old in _read_manifest().get("files", []):           # launchers from an earlier install elsewhere
        if os.path.dirname(old) != BIN_DIR and (os.path.islink(old) or (
                os.path.isfile(old) and "kolbascii launcher" in open(old, errors="ignore").read(400))):
            os.remove(old)
    os.makedirs(BIN_DIR, exist_ok=True)
    path = os.path.join(BIN_DIR, "kolbascii")
    with open(path, "w") as fh:
        fh.write(LAUNCHER % {"home": HOME_DIR, "py": sys.executable})
    os.chmod(path, 0o755)
    alias = os.path.join(BIN_DIR, "kolbaskii")              # forgiving spelling
    if os.path.islink(alias) or not os.path.exists(alias):
        if os.path.islink(alias):
            os.remove(alias)
        os.symlink(path, alias)
    import json
    with open(MANIFEST, "w") as fh:
        json.dump({"bin_dir": BIN_DIR, "files": [path, alias], "no_modify_path": NO_PATH}, fh, indent=1)
    state["launcher"] = path
    ctx.note = tilde(path)


def rc_file():
    shell = os.path.basename(os.environ.get("SHELL", ""))
    home = os.path.expanduser("~")
    if shell == "zsh":
        return os.path.join(os.environ.get("ZDOTDIR", home), ".zshrc"), "sh"
    if shell == "fish":
        return os.path.join(home, ".config", "fish", "config.fish"), "fish"
    if shell == "bash":
        if platform.system() == "Darwin":
            return os.path.join(home, ".bash_profile"), "sh"
        return os.path.join(home, ".bashrc"), "sh"
    return os.path.join(home, ".profile"), "sh"


def step_path(ctx):
    on_path = any(os.path.realpath(p) == os.path.realpath(BIN_DIR)
                  for p in os.environ.get("PATH", "").split(os.pathsep) if p)
    if on_path:
        ctx.note = "already on PATH · ready now"
        state["ready_now"] = True
        return
    if NO_PATH:
        ctx.note = "skipped (--no-modify-path)"
        state["reload"] = "export PATH=\"%s:$PATH\"" % BIN_DIR
        return
    rc, kind = rc_file()
    bin_expr = BIN_DIR.replace(os.path.expanduser("~"), "$HOME", 1)
    line = 'fish_add_path -g "%s"' % bin_expr if kind == "fish" else 'export PATH="%s:$PATH"' % bin_expr
    existing = open(rc).read() if os.path.exists(rc) else ""
    if MARK_START not in existing:
        os.makedirs(os.path.dirname(rc), exist_ok=True)
        with open(rc, "a") as fh:
            fh.write("\n%s\n%s\n%s\n" % (MARK_START, line, MARK_END))
    state["reload"] = "source " + tilde(rc)
    ctx.note = "added " + tilde(BIN_DIR) + " to " + tilde(rc)


def step_verify(ctx):
    res = subprocess.run([state["launcher"], "--version"], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, timeout=20)
    text = res.stdout.decode(errors="ignore").strip()
    if res.returncode != 0 or not text.startswith("kolbascii"):
        raise StepFailed("The installed command didn't run: " + (text or "exit %d" % res.returncode))
    names = subprocess.run([state["launcher"], "list"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=20).stdout.decode(errors="ignore")
    count = len(re.findall(r"^\s{4}\S", re.sub(r"\x1b\[[0-9;]*m", "", names), re.M))
    state["count"] = count
    ctx.note = "%s · %d animations" % (text, count)


# -------------------------------------------------------------- uninstall steps
def step_remove_cmd(ctx):
    paths = list(_read_manifest().get("files", []))
    paths += [os.path.join(BIN_DIR, "kolbascii"), os.path.join(BIN_DIR, "kolbaskii")]
    removed = 0
    for p in dict.fromkeys(paths):
        if os.path.islink(p):
            os.remove(p)
            removed += 1
        elif os.path.isfile(p) and "kolbascii launcher" in open(p, errors="ignore").read(400):
            os.remove(p)
            removed += 1
    ctx.note = "%d launcher%s removed" % (removed, "" if removed == 1 else "s")


def step_remove_files(ctx):
    pkg = os.path.join(HOME_DIR, "kolbascii")
    if not os.path.exists(os.path.join(pkg, "__main__.py")):
        ctx.note = "nothing at " + tilde(HOME_DIR)
        return
    shutil.rmtree(pkg)                         # only our own files, never the whole folder
    if os.path.exists(MANIFEST):
        os.remove(MANIFEST)
    try:
        os.rmdir(HOME_DIR)                     # succeeds only if nothing else lives there
        ctx.note = tilde(HOME_DIR) + " removed"
    except OSError:
        ctx.note = "kolbascii files removed from " + tilde(HOME_DIR)


def step_clean_path(ctx):
    cleaned = []
    home = os.path.expanduser("~")
    for rc in (".zshrc", ".bashrc", ".bash_profile", ".profile", ".config/fish/config.fish"):
        p = os.path.join(os.environ.get("ZDOTDIR", home) if rc == ".zshrc" else home, rc)
        if not os.path.exists(p):
            continue
        text = open(p).read()
        if MARK_START not in text:
            continue
        new = re.sub(r"\n?%s\n.*?%s\n?" % (re.escape(MARK_START), re.escape(MARK_END)), "\n", text, flags=re.S)
        with open(p, "w") as fh:
            fh.write(new)
        cleaned.append(tilde(p))
    ctx.note = ("cleaned " + ", ".join(cleaned)) if cleaned else "nothing to clean"


# ------------------------------------------------------------------------ main
def main():
    if FANCY:
        write("\x1b[?25l")
    try:
        t0 = time.time()
        if UNINSTALL:
            banner("uninstalling · sorry to see you go")
            steps = [("Removing the command", step_remove_cmd),
                     ("Removing files", step_remove_files),
                     ("Cleaning up your PATH", step_clean_path)]
        else:
            banner("animated ASCII decorations for your terminal")
            steps = [("Checking your system", step_check),
                     ("Downloading kolbascii", step_download),
                     ("Installing files", step_files),
                     ("Creating the command", step_command),
                     ("Setting up your PATH", step_path),
                     ("Verifying the install", step_verify)]
        for i, (label, fn) in enumerate(steps, 1):
            run_step(i, len(steps), label, fn)
        took = time.time() - t0
        write("\n")
        if UNINSTALL:
            boxed([("✓  kolbascii has been removed", GREEN, True),
                   ("", TEXT, False),
                   ("Thanks for decorating with us.", DIM, False)])
        else:
            lines = [("✓  kolbascii %s is installed" % state.get("version", ""), GREEN, True),
                     ("", TEXT, False),
                     ("Run it right now, in this window:" if state.get("ready_now") else "Try it:", DIM, False),
                     ("  kolbascii halloween", GRAD[1], True),
                     ("  kolbascii thanksgiving", GRAD[1], True),
                     ("  kolbascii xmas_tree", GRAD[1], True),
                     ("  kolbascii list", GRAD[1], True)]
            if state.get("reload"):
                lines += [("", TEXT, False),
                          ("Open a new terminal tab first, or run:", DIM, False),
                          ("  " + state["reload"], TEXT, False)]
            boxed(lines)
        write("\n  " + paint(DIM, "done in %.1fs" % took)
              + ("" if UNINSTALL else paint(DIM, "  ·  remove any time with: ") + paint(TEXT, "kolbascii uninstall"))
              + "\n\n")
    except StepFailed as e:
        fail_box(e)
        sys.exit(1)
    except KeyboardInterrupt:
        write("\n\n  " + paint(DIM, "cancelled.") + "\n\n")
        sys.exit(130)
    finally:
        if state.get("tmp"):
            shutil.rmtree(state["tmp"], ignore_errors=True)
        if FANCY:
            write("\x1b[?25h" + RESET)


main()
PYTHON
