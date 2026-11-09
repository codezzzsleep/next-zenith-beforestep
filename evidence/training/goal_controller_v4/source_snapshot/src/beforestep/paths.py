"""One explicit root for source, assets, protocols and output."""
from pathlib import Path
import os
ROOT = Path(os.environ.get('BEFORESTEP_ROOT', Path(__file__).resolve().parents[2])).resolve()
