"""Read-only fresh-file baseline capture before the three nut refinements."""
import bpy,sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from scene_snapshot import capture,sha,write_snapshot
path=Path(bpy.data.filepath);digest=sha(path)
write_snapshot(HERE/'before-scene.json.gz',capture())
assert sha(path)==digest
(HERE/'baseline-record.json').write_text(json.dumps(dict(scene=path.name,sha256=digest,bytes=path.stat().st_size,saved_source_unchanged=True),indent=2)+'\n')
print('Fresh revision9 baseline captured:',digest)
