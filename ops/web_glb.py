"""Produce small web copies of real GLBs, leaving original assets intact."""
import copy
import hashlib
import io
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image
import trimesh

LIMIT = 2_000_000


def parse(data):
    assert data[:4] == b'glTF' and struct.unpack_from('<I', data, 4)[0] == 2
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4E4F534A
    document = json.loads(data[20:20+size])
    offset = 20+size
    length, kind = struct.unpack_from('<II', data, offset)
    assert kind == 0x004E4942
    return document, data[offset+8:offset+8+length]


def encode(document, binary):
    header = json.dumps(document, separators=(',', ':')).encode()
    header += b' ' * (-len(header) % 4)
    binary += b'\0' * (-len(binary) % 4)
    length = 12 + 8 + len(header) + 8 + len(binary)
    return struct.pack('<4sII', b'glTF', 2, length) + struct.pack('<II', len(header), 0x4E4F534A) + header + struct.pack('<II', len(binary), 0x004E4942) + binary


def make_web(source, target):
    source, target = Path(source), Path(target)
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    document, binary = parse(raw)
    assert len(document['buffers']) == 1 and not document['buffers'][0].get('uri')
    views = document['bufferViews']
    image_views = {image['bufferView']: index for index, image in enumerate(document.get('images', []))}
    pieces = [binary[v.get('byteOffset', 0):v.get('byteOffset', 0)+v['byteLength']] for v in views]
    assert not ({a.get('bufferView') for a in document.get('accessors', [])} & set(image_views))
    images = {view: Image.open(io.BytesIO(pieces[view])).copy() for view in image_views}
    original_dimensions = {view: list(image.size) for view, image in images.items()}
    normal_images = {document['textures'][material['normalTexture']['index']]['source']
                     for material in document.get('materials', []) if 'normalTexture' in material}
    encoded = raw
    resized = []
    for maximum in [1024, 768, 512, 384, 256, 192, 128, 64]:
        doc = copy.deepcopy(document)
        new_binary = bytearray()
        resized = []
        for index, view in enumerate(views):
            blob = pieces[index]
            if index in image_views:
                image = images[index].copy()
                image.thumbnail((maximum, maximum), Image.Resampling.LANCZOS)
                has_alpha = 'A' in image.getbands() and image.getchannel('A').getextrema() != (255, 255)
                use_png = has_alpha or image_views[index] in normal_images
                output = io.BytesIO()
                if use_png:
                    image.save(output, format='PNG', compress_level=6)
                    mime = 'image/png'
                else:
                    image.convert('RGB').save(output, format='JPEG', quality=88, optimize=True)
                    mime = 'image/jpeg'
                blob = output.getvalue()
                doc['images'][image_views[index]]['mimeType'] = mime
                resized.append({'image': image_views[index], 'original': original_dimensions[index],
                                'web': list(image.size), 'mime': mime})
            new_binary += b'\0' * (-len(new_binary) % 4)
            doc['bufferViews'][index].update(buffer=0, byteOffset=len(new_binary), byteLength=len(blob))
            new_binary += blob
        doc['buffers'][0]['byteLength'] = len(new_binary)
        encoded = encode(doc, bytes(new_binary))
        if len(encoded) <= LIMIT:
            web_doc, web_binary = parse(encoded)
            for index, piece in enumerate(pieces):
                if index in image_views:
                    continue
                v = web_doc['bufferViews'][index]
                assert web_binary[v['byteOffset']:v['byteOffset']+v['byteLength']] == piece
            representation = 'original_geometry_buffers_exact; textures resized/reencoded only'
            break
    else:
        # Exact triangle positions without UV/texture seam duplication. This is
        # explicitly a geometry preview; the full textured original is retained.
        mesh = trimesh.load(source, force='mesh', process=False)
        triangles = np.asarray(mesh.triangles, dtype=np.float32)
        vertices, inverse = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
        reduced = trimesh.Trimesh(vertices=vertices, faces=inverse.reshape(-1, 3), process=False)
        encoded = reduced.export(file_type='glb')
        assert len(encoded) <= LIMIT, f'Exact geometry exceeds web size limit: {source}'
        reloaded = trimesh.load(io.BytesIO(encoded), file_type='glb', force='mesh', process=False)
        assert np.array_equal(np.asarray(reloaded.triangles, dtype=np.float32), triangles)
        representation = 'triangle_positions_exact_float32; texture omitted in geometry-only preview'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encoded)
    return {'source_sha256': digest, 'source_bytes': len(raw),
            'sha256': hashlib.sha256(encoded).hexdigest(), 'bytes': len(encoded),
            'representation': representation, 'texture_images': resized,
            'original_asset_unchanged': source.read_bytes() == raw}
