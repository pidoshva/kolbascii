<h1 align="center">kolbascii</h1>

<p align="center">
  <b>Animated ASCII decorations for your terminal.</b><br>
  One command, and the window you're in turns into a little 3D scene built out of characters.
</p>

<p align="center">
  <img src="docs/xmas_tree.gif" alt="kolbascii xmas_tree" width="48%">
  <img src="docs/thanksgiving.gif" alt="kolbascii thanksgiving" width="48%">
</p>

## Quick start

**1. Install** (macOS or Linux, one line):

```sh
curl -fsSL https://raw.githubusercontent.com/pidoshva/kolbascii/main/install.sh | bash
```

**2. Open a new terminal tab**, make the window big, and run:

```sh
kolbascii xmas_tree        # 3D Christmas tree
kolbascii thanksgiving     # Thanksgiving harvest
kolbascii                  # see everything available
```

Press **q** to quit, **space** to pause, **r** to restart.

No dependencies, nothing to configure. Leave it running on a spare monitor or between
builds, show it off on a screen share, or just enjoy it for half a minute.

---

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/pidoshva/kolbascii/main/install.sh | bash
```

That's it. The installer:

1. checks for Python 3.8+ (already on macOS with the developer tools, and on almost every Linux)
2. downloads kolbascii into `~/.kolbascii`
3. adds a `kolbascii` command to `~/.local/bin`
4. puts `~/.local/bin` on your `PATH` if it isn't there yet, inside a clearly marked block in your shell's startup file
5. runs the new command once to make sure it works

<p align="center"><img src="docs/installer.png" alt="the installer" width="70%"></p>

Open a new terminal tab afterwards (or run the `source` line the installer prints) and you're set.

<details>
<summary>Installer options</summary>

Pass options after `bash -s --` when piping:

```sh
curl -fsSL https://raw.githubusercontent.com/pidoshva/kolbascii/main/install.sh | bash -s -- --no-modify-path
```

| Option / variable | What it does |
| --- | --- |
| `--no-modify-path` | Don't touch your shell startup file. The installer prints the `export` line to add yourself. |
| `--uninstall` | Remove everything the installer added. Same as `kolbascii uninstall`. |
| `KOLBASCII_HOME` | Where the files go. Default `~/.kolbascii`. |
| `KOLBASCII_BIN` | Where the command goes. Default `~/.local/bin`. |
| `KOLBASCII_BRANCH` | Install from another branch. Default `main`. |

From a clone, `./install.sh` installs your local copy instead of downloading.

</details>

## Usage

```sh
kolbascii                       # logo, help and the list of animations
kolbascii <animation>           # play it full-screen in this window
kolbascii <animation> -s 30     # stop by itself after 30 seconds
kolbascii random                # surprise me
kolbascii list                  # what's available
kolbascii update                # get the newest version and animations
kolbascii uninstall             # remove kolbascii
```

While an animation plays: **space** pauses, **r** restarts, **q** (or Esc, or Ctrl+C) quits and
gives you your terminal back exactly as it was.

Names are forgiving: `kolbascii xmas`, `kolbascii christmas`, `kolbascii pumpkin` and
`kolbascii turkey` all work, typos get a "did you mean", and `kolbaskii` works as well as
`kolbascii`.

## Animations

### `xmas_tree`

<img src="docs/xmas_tree.png" alt="Christmas tree" width="60%" align="right">

A tall 3D spruce grows out of the snow, layer by layer, with a bright growth front sweeping
up the branches. Then, while it slowly turns:

- a gold tinsel garland spirals up, and a red-and-silver bead garland spirals the other way
- 46 baubles pop on, red, gold, silver and blue, each with a cap and a shine
- striped candy canes hang from the branches
- 220 warm fairy lights switch on one by one, twinkle, and glow onto the needles around them
- presents appear underneath, wrapped plain, striped or dotted, with ribbons and bows
- a star lands on top with a flash
- **MERRY CHRISTMAS** types itself out

Snow falls the whole time, and the branch tips carry a little snow of their own.

<br clear="right">

### `thanksgiving`

<img src="docs/thanksgiving.png" alt="Thanksgiving harvest" width="60%" align="right">

A funnel of autumn leaves spins up out of the ground and winds itself into a big ribbed
pumpkin, one leaf at a time, each one flashing warm as it lands. Then:

- the stem grows, a vine curls around it, and two broad leaves unfold
- a small orange pumpkin, a cream one and a striped gourd pop in beside it
- a cob of multicoloured corn appears kernel by kernel, with its husks
- a tied wheat bundle grows up behind
- **HAPPY THANKSGIVING** types itself out

Leaves keep drifting down, and the ground is covered in them.

<br clear="right">

## Requirements

- **macOS or Linux.** On Windows, use WSL.
- **Python 3.8 or newer.** Standard library only, nothing to `pip install`.
- **A terminal with 24-bit colour** looks best: iTerm2, Ghostty, WezTerm, kitty, Alacritty, the
  VS Code terminal, or Terminal.app on macOS 26+. Other terminals get an automatic
  256-colour fallback.
- **A big window.** The scenes scale to whatever size you give them, and the more cells you
  give them the more detail they draw. Full screen is best.

## How it works

Each scene is a cloud of a few thousand to a few tens of thousands of 3D points: needles,
pumpkin skin, ribbon, kernels, each with a colour, a surface normal and the time it should
appear. Every frame the points are rotated, projected through a perspective camera and
depth-tested into a character grid, one z-buffer per character cell.
Lighting picks both the colour and the character. Brighter surfaces get denser glyphs
(`.:-~=+^v*x%&#W@`), so shading comes from the characters as well as the colour.
After that, overlay passes add things like the light glow, the star and the greeting.
Frames go out as one ANSI string, about 30 times a second.

All of it is plain Python. The engine (`kolbascii/engine.py`) owns the terminal: alternate
screen, hidden cursor, key handling, resizing, frame pacing, and restoring everything on exit.

## Make your own

An animation is one Python file with a `Scene` class:

```python
# kolbascii/animations/fireworks.py
class Scene:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows

    def render(self, t):
        """t is seconds since start. Return (chars, colors): two flat lists of
        length cols*rows. chars[i] is a single character or None, colors[i] an
        (r, g, b) tuple."""
        ...
```

Register it in `kolbascii/animations/__init__.py`:

```python
"fireworks": {
    "module": "kolbascii.animations.fireworks",
    "title": "Fireworks",
    "about": "rockets, bursts and sparkles over a skyline",
    "aliases": ("new_year", "nye"),
},
```

and run it with `python3 -m kolbascii fireworks`. `engine.Canvas` has helpers for the
greeting banner and the bottom-left readout, and the two existing scenes are good templates
for 3D point clouds. Pull requests with new animations are very welcome.

## Uninstall

```sh
kolbascii uninstall
```

This removes `~/.kolbascii`, the `kolbascii` and `kolbaskii` commands, and the marked `PATH`
block in your shell startup file.

## License

[MIT](LICENSE)
