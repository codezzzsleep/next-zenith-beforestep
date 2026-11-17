"""Render the built PDF to page images plus contact sheets for visual review."""
import sys
from pathlib import Path
import pymupdf
from PIL import Image
pdf = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 80
d = pymupdf.open(pdf); ims = []
for old in out.glob('p*.jpg'): old.unlink()
for i, p in enumerate(d):
    f = out / f'p{i+1:02d}.jpg'; p.get_pixmap(dpi=dpi).save(f); ims.append(Image.open(f))
w, h = ims[0].size
for k in range(0, len(ims), 4):
    s = Image.new('RGB', (w * 4, h), 'white')
    for j, im in enumerate(ims[k:k + 4]): s.paste(im, (j * w, 0))
    s.save(out / f'contact{k // 4 + 1}.jpg', quality=82)
print(len(ims), w, h)
