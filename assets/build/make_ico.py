"""Packs fav-16/32/48.png into favicon.ico (16, 32, 48 px, like kharidwise)."""

import sys
from pathlib import Path

from PIL import Image

out = Path(sys.argv[1])
images = [Image.open(out / f"fav-{s}.png").convert("RGBA") for s in (16, 32, 48)]
images[-1].save(out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=images[:-1])
for s in (16, 32, 48):
    (out / f"fav-{s}.png").unlink()
print("favicon.ico written:", Image.open(out / "favicon.ico").info.get("sizes"))
