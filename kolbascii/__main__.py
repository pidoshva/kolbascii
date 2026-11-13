"""kolbascii command line.

    kolbascii <animation> [--seconds N]
    kolbascii list | random | update | uninstall | --version | --help
"""
import difflib
import os
import random
import shutil
import subprocess
import sys

from . import INSTALL_URL, REPO, __version__
from .animations import ANIMATIONS, load, resolve

LOGO = [
    "██╗  ██╗ ██████╗ ██╗     ██████╗  █████╗ ███████╗ ██████╗██╗██╗",
    "██║ ██╔╝██╔═══██╗██║     ██╔══██╗██╔══██╗██╔════╝██╔════╝██║██║",
    "█████╔╝ ██║   ██║██║     ██████╔╝███████║███████╗██║     ██║██║",
    "██╔═██╗ ██║   ██║██║     ██╔══██╗██╔══██║╚════██║██║     ██║██║",
    "██║  ██╗╚██████╔╝███████╗██████╔╝██║  ██║███████║╚██████╗██║██║",
    "╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝╚═╝",
]
GRADIENT = ((255, 94, 98), (255, 153, 102), (255, 214, 120))

COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def rgb(c, s, bold=False):
    if not COLOR:
        return s
    return "\x1b[%s38;2;%d;%d;%dm%s\x1b[0m" % ("1;" if bold else "", c[0], c[1], c[2], s)


def grad(k):
    k = max(0.0, min(1.0, k)) * (len(GRADIENT) - 1)
    i = min(int(k), len(GRADIENT) - 2)
    f = k - i
    a, b = GRADIENT[i], GRADIENT[i + 1]
    return tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3))


def logo():
    width = shutil.get_terminal_size((80, 24)).columns
    if width < len(LOGO[0]) + 4:
        return "  " + rgb(GRADIENT[0], "k o l b a s c i i", bold=True)
    out = []
    for row, line in enumerate(LOGO):
        chunks = []
        for i, ch in enumerate(line):
            c = grad(i / len(line))
            if ch in "╗╝║═╔╚":
                c = tuple(int(v * 0.55) for v in c)
            chunks.append(rgb(c, ch) if ch != " " else " ")
        out.append("  " + "".join(chunks))
    return "\n".join(out)


DIM = (130, 136, 150)
TEXT = (225, 228, 235)
ACC = (255, 170, 100)


def usage():
    print()
    print(logo())
    print()
    print("  " + rgb(DIM, "animated ASCII decorations for your terminal · v" + __version__))
    print()
    print("  " + rgb(TEXT, "usage", bold=True))
    for cmd, what in (("kolbascii <animation>", "play it full-screen in this window"),
                      ("kolbascii <animation> -s 30", "stop by itself after 30 seconds"),
                      ("kolbascii random", "surprise me"),
                      ("kolbascii list", "what's available"),
                      ("kolbascii update", "get the newest animations"),
                      ("kolbascii uninstall", "remove kolbascii")):
        print("    " + rgb(ACC, cmd.ljust(30)) + rgb(DIM, what))
    print()
    print_list()
    print("  " + rgb(DIM, "while playing:  space pause · r restart · q quit"))
    print()


def print_list():
    print("  " + rgb(TEXT, "animations", bold=True))
    w = max(len(k) for k in ANIMATIONS) + 3
    width = shutil.get_terminal_size((80, 24)).columns
    for k, meta in ANIMATIONS.items():
        print("    " + rgb(ACC, k.ljust(w), bold=True) + rgb(TEXT, meta["title"]))
        about, room = meta["about"], max(20, width - w - 6)
        while about:                                  # wrap the description under the title
            cut = len(about) if len(about) <= room else about.rfind(" ", 0, room)
            cut = cut if cut > 0 else room
            print("    " + " " * w + rgb(DIM, about[:cut].strip()))
            about = about[cut:].strip()
    print()


def fail(msg):
    sys.stderr.write(rgb((255, 95, 95), "kolbascii: ") + msg + "\n")
    sys.exit(2)


def home():
    return os.environ.get("KOLBASCII_HOME", os.path.expanduser("~/.kolbascii"))


def uninstall():
    root = home()
    script = os.path.join(root, "install.sh")
    if os.path.exists(script):    # the installer also removes the PATH line it added
        sys.exit(subprocess.call(["bash", script, "--uninstall"]))
    manifest = os.path.join(root, ".manifest")
    removed = []
    if os.path.exists(manifest):
        with open(manifest) as fh:
            paths = [line.strip() for line in fh if line.strip()]
        for path in paths:
            if os.path.islink(path):
                os.remove(path)
                removed.append(path)
            elif os.path.isfile(path):
                with open(path, errors="ignore") as fh:
                    ours = "kolbascii" in fh.read(400)
                if ours:
                    os.remove(path)
                    removed.append(path)
    if os.path.isdir(root) and os.path.exists(os.path.join(root, "kolbascii", "__main__.py")):
        shutil.rmtree(root)
        removed.append(root)
    if not removed:
        print("Nothing to remove: no kolbascii install found at " + root)
        return
    for p in removed:
        print("  " + rgb((120, 220, 140), "✓") + " removed " + p)
    print("  " + rgb(DIM, "(the PATH line the installer added to your shell rc file, if any, is harmless and can stay)"))


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        usage()
        return
    cmd = args.pop(0)
    if cmd in ("-V", "--version", "version"):
        print("kolbascii " + __version__)
        return
    if cmd in ("list", "ls"):
        print()
        print_list()
        return
    if cmd == "update":
        sys.exit(subprocess.call("curl -fsSL %s | bash" % INSTALL_URL, shell=True))
    if cmd == "uninstall":
        uninstall()
        return

    seconds = frames = None
    while args:
        a = args.pop(0)
        try:
            if a in ("-s", "--seconds"):
                seconds = float(args.pop(0))
            elif a == "--frames":
                frames = int(args.pop(0))
            else:
                fail("unknown option '%s'. Try: kolbascii --help" % a)
        except (IndexError, ValueError):
            fail("%s needs a number" % a)

    key = random.choice(list(ANIMATIONS)) if cmd == "random" else resolve(cmd)
    if key is None:
        names = list(ANIMATIONS) + [a for m in ANIMATIONS.values() for a in m["aliases"]]
        close = difflib.get_close_matches(cmd.lower(), names, n=1)
        hint = (" Did you mean '%s'?" % resolve(close[0])) if close else ""
        fail("no animation called '%s'.%s Run 'kolbascii list' to see them all." % (cmd, hint))
    if not sys.stdout.isatty() and frames is None:
        fail("needs a terminal to draw in (stdout is not a TTY).")

    from .engine import run
    run(load(key), seconds=seconds, frames=frames)


if __name__ == "__main__":
    main()
