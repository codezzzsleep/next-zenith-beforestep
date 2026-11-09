"""Deterministic image crops and masked Lux3D input variants."""
import hashlib, json, pathlib
import numpy as np
from beforestep.paths import ROOT

def sha256_file(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _pixel_box(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def _square_crop(box, pad_frac, W, H, min_side):
    x0, y0, x1, y1 = box
    w, h = x1 - x0 + 1, y1 - y0 + 1
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    side = max(w, h) * (1.0 + 2.0 * pad_frac)
    side = max(side, min_side)
    side = min(side, min(W, H))          # 不越界：越界会引入纯色补边
    half = side / 2.0
    x0c = int(round(cx - half)); y0c = int(round(cy - half))
    x0c = max(0, min(W - int(round(side)), x0c))
    y0c = max(0, min(H - int(round(side)), y0c))
    x1c = x0c + int(round(side)); y1c = y0c + int(round(side))
    return [x0c, y0c, x1c, y1c]


def _crop_image(img, box, out_size):
    from PIL import Image
    x0, y0, x1, y1 = box
    return np.asarray(Image.fromarray(img[y0:y1, x0:x1]).resize(
        (int(out_size), int(out_size)), Image.LANCZOS))


def _masked_variant(img, mask, box, out_size, bg=(232, 232, 232)):
    from PIL import Image
    x0, y0, x1, y1 = box
    H, W = img.shape[:2]
    rgb = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.uint8)
    rgb[:, :] = bg
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x1), min(H, y1)
    if sx1 > sx0 and sy1 > sy0:
        m = mask[sy0:sy1, sx0:sx1]
        sub = img[sy0:sy1, sx0:sx1].copy()
        rgb[sy0 - y0:sy0 - y0 + sub.shape[0], sx0 - x0:sx0 - x0 + sub.shape[1]][m] = sub[m]
    return np.asarray(Image.fromarray(rgb).resize((int(out_size), int(out_size)),
                                                  Image.LANCZOS))


def _variants(rgb_gen, mask_gen, box, out_dir, native_h_px, proto):
    """A/B/C 三类输入，全部由同一次真实渲染派生；不重绘、不伪造几何。"""
    from PIL import Image
    vdir = out_dir / 'variants'
    vdir.mkdir(parents=True, exist_ok=True)
    size = int(proto['inputs']['upload_px'])
    rec = {'schema': 'v3-inputs/v1', 'upload_px': size,
           'native_object_height_px': native_h_px, 'variants': {}}
    boxes = {
        'tight': _square_crop(box, float(proto['inputs']['tight_pad_frac']),
                              rgb_gen.shape[1], rgb_gen.shape[0], 64),
        'context': _square_crop(box, float(proto['inputs']['context_pad_frac']),
                                rgb_gen.shape[1], rgb_gen.shape[0], 64),
    }
    imgs = {
        'A': _crop_image(rgb_gen, boxes['tight'], size),
        'B': _masked_variant(rgb_gen, mask_gen, boxes['tight'], size),
        'C': _crop_image(rgb_gen, boxes['context'], size),
    }
    for cls, arr in imgs.items():
        for rep in (1, 2):
            name = f'{cls}{rep}.png'
            Image.fromarray(arr).save(vdir / name)
            # 上传后目标像素高度：按裁剪框内目标高度线性换算
            crop_h = boxes['tight' if cls in 'AB' else 'context'][3] - \
                boxes['tight' if cls in 'AB' else 'context'][1]
            up_h = native_h_px * (size / max(1, crop_h))
            rec['variants'][f'{cls}{rep}'] = {
                'path': str((vdir / name).relative_to(ROOT)),
                'sha256': sha256_file(vdir / name),
                'class': cls, 'repeat_idx': rep - 1,
                'crop_box': boxes['tight' if cls in 'AB' else 'context'],
                'uploaded_object_height_px': round(float(up_h), 1),
            }
    rec['native_ok'] = bool(native_h_px >= float(proto['inputs']['min_native_px']))
    rec['upload_ok'] = bool(all(v['uploaded_object_height_px'] >= proto['inputs']['min_native_px']
                                for v in rec['variants'].values()))
    (vdir / 'variants.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2))
    return rec
