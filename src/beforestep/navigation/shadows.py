"""R3 shadow explanation from known terrain, visible heights and admitted meshes."""
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates

from beforestep import scene as S
from . import map as N

MAX_DISTANCE = 5.0
PADDING = int(round(MAX_DISTANCE / N.RES))


def toward_sun():
    # scene.sun_dir is explicitly the rendered light's propagation direction.
    light = S.sun_dir()
    horizontal = float(np.linalg.norm(light[:2]))
    return -light[:2] / horizontal, float(-light[2] / horizontal)


def terrain_grid(height_file=None):
    x0, y0 = N.X0 - MAX_DISTANCE, N.Y0 - MAX_DISTANCE
    xs = x0 + (np.arange(N.NX + 2 * PADDING) + .5) * N.RES
    ys = y0 + (np.arange(N.NY + 2 * PADDING) + .5) * N.RES
    x, y = np.meshgrid(xs, ys, indexing='ij')
    height = np.load(height_file) if height_file else S.height_map()
    # Original physical heightfield rows descend in y; columns ascend in x.
    row = (S.SPAN - y) * (height.shape[0] - 1) / (2 * S.SPAN)
    column = (x + S.SPAN) * (height.shape[1] - 1) / (2 * S.SPAN)
    ground = map_coordinates(height, [row, column], order=1, mode='nearest')
    return ground, (x0, y0)


def clip_polygon(polygon, axis, boundary, lower):
    result = []
    if not polygon:
        return result
    previous = polygon[-1]
    was_inside = previous[axis] >= boundary if lower else previous[axis] <= boundary
    for point in polygon:
        inside = point[axis] >= boundary if lower else point[axis] <= boundary
        if inside != was_inside:
            fraction = (boundary - previous[axis]) / (point[axis] - previous[axis])
            result.append(previous + fraction * (point - previous))
        if inside:
            result.append(point)
        previous, was_inside = point, inside
    return result


def add_mesh_height(height, mesh, origin):
    """Exact maximum mesh-surface height intersecting each 5cm cell."""
    vertices, faces = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    indices = np.floor((vertices[:, :2] - origin) / N.RES).astype(int)
    valid = (indices[:, 0] >= 0) & (indices[:, 0] < height.shape[0]) & (indices[:, 1] >= 0) & (indices[:, 1] < height.shape[1])
    np.maximum.at(height, (indices[valid, 0], indices[valid, 1]), vertices[valid, 2])
    for face in faces:
        triangle, cells = vertices[face], indices[face]
        if np.all(cells == cells[0]):
            continue
        lo = np.maximum(cells.min(axis=0), 0)
        hi = np.minimum(cells.max(axis=0), np.array(height.shape) - 1)
        for i in range(lo[0], hi[0] + 1):
            for j in range(lo[1], hi[1] + 1):
                polygon = list(triangle)
                for axis, index in ((0, i), (1, j)):
                    edge = origin[axis] + index * N.RES
                    polygon = clip_polygon(polygon, axis, edge, True)
                    polygon = clip_polygon(polygon, axis, edge + N.RES, False)
                if polygon:
                    height[i, j] = max(height[i, j], max(point[2] for point in polygon))
    return height


def shadow_from_height(height, ground, direction, tangent, padding=0):
    shape = ground.shape
    output = np.zeros(shape, dtype=bool)
    ix, iy = np.indices(shape)
    for distance in np.arange(N.RES, MAX_DISTANCE + N.RES / 2, N.RES):
        # Sampling at cell centres after stepping along the rendered sun ray.
        sx = np.floor(ix + .5 + padding + distance * direction[0] / N.RES).astype(int)
        sy = np.floor(iy + .5 + padding + distance * direction[1] / N.RES).astype(int)
        valid = (sx >= 0) & (sy >= 0) & (sx < height.shape[0]) & (sy < height.shape[1])
        output[valid] |= height[sx[valid], sy[valid]] > ground[valid] + distance * tangent
    return output


def predict(zmax, world_meshes, height_file=None):
    import trimesh
    ground, origin = terrain_grid(height_file)
    height = ground.copy()
    interior = (slice(PADDING, PADDING + N.NX), slice(PADDING, PADDING + N.NY))
    if zmax is not None:
        visible = np.asarray(zmax)
        assert visible.shape == (N.NX, N.NY)
        height[interior] = np.maximum(height[interior], visible)
    for path in world_meshes:
        mesh = trimesh.load(Path(path), force='mesh', process=False)
        add_mesh_height(height, mesh, origin)
    direction, tangent = toward_sun()
    shadow = shadow_from_height(height, ground[interior], direction, tangent, PADDING)
    return shadow, height, ground[interior]
