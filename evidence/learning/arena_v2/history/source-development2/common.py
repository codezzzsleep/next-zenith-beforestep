import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evidence/learning/arena_v2'
HELDOUT = {f'suite_r2_v4_{s}' for s in ['F0_002','F2_011','F3_005','F0_003','F3_006','F0_006']}
METRICS = ('scale_ratio','hidden_frac','shell_contact','free_intrusion_frac','contour_iou')

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def finite(value):
    if isinstance(value, dict): return {k:finite(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [finite(v) for v in value]
    if isinstance(value,np.ndarray): return finite(value.tolist())
    if isinstance(value,np.generic): return finite(value.item())
    if isinstance(value,float) and not np.isfinite(value): return None
    return value

def rigid(yaw_deg, translation):
    a=np.radians(yaw_deg); c,s=np.cos(a),np.sin(a)
    return np.array([[c,-s,0,translation[0]],[s,c,0,translation[1]],[0,0,1,0],[0,0,0,1.]])

def transform_points(points, matrix):
    return np.asarray(points) @ np.asarray(matrix)[:3,:3].T + np.asarray(matrix)[:3,3]
