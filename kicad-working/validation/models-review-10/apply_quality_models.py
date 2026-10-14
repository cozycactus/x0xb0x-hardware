"""Guarded application of the fully audited model-only candidate."""
from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((H/'candidate-model-audit.json').read_text());assert a['passed']
p=json.loads((H/'combined-model-plan.json').read_text());baseline=json.loads((H/'input-manifest.json').read_text())['files']
for rel,h in baseline.items():assert sha(W/rel)==h,('Workspace changed since freeze',rel)
for row in p['files']:
 rel=row['file'];src=H/'candidate'/rel
 assert sha(src)==row['after_sha256']
 assert row['model_nodes_only'] or row['model_metadata_only']
for rel,h in p['new_files'].items():assert not (W/rel).exists() and sha(H/'candidate'/rel)==h
for rel in [row['file'] for row in p['files']]+list(p['new_files']):
 src=H/'candidate'/rel;dest=W/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
(H/'application-record.json').write_text(json.dumps({'passed':True,'updated_instances':p['updated_instance_count'],'changed_existing_files':len(p['files']),'new_files':len(p['new_files']),'guarded_input_files':len(baseline),'all_candidate_hashes_match':True},indent=2)+'\n')
print('Applied reviewed detailed models:',p['updated_instance_count'])
