"""Registry of animations. Add a new one by dropping a module with a ``Scene``
class into this folder and listing it here."""

ANIMATIONS = {
    "xmas_tree": {
        "module": "kolbascii.animations.xmas_tree",
        "title": "Christmas tree",
        "about": "a 3D tree grows from the ground, gets garlands, baubles, lights, presents and a star",
        "aliases": ("xmas", "christmas", "tree", "xmas-tree", "christmas_tree"),
    },
    "thanksgiving": {
        "module": "kolbascii.animations.thanksgiving",
        "title": "Thanksgiving harvest",
        "about": "a vortex of autumn leaves becomes a pumpkin, with gourds, corn and wheat",
        "aliases": ("turkey", "pumpkin", "harvest", "autumn", "fall"),
    },
    "halloween": {
        "module": "kolbascii.animations.halloween",
        "title": "Halloween graveyard",
        "about": "spirits rise into a jack-o'-lantern that carves its own face, with bats, ghosts and lightning",
        "aliases": ("spooky", "jack_o_lantern", "jackolantern", "graveyard", "boo"),
    },
}


def resolve(name):
    key = name.strip().lower().replace("-", "_")
    if key in ANIMATIONS:
        return key
    for k, meta in ANIMATIONS.items():
        if key in (a.replace("-", "_") for a in meta["aliases"]):
            return k
    return None


def load(key):
    import importlib
    return importlib.import_module(ANIMATIONS[key]["module"]).Scene
