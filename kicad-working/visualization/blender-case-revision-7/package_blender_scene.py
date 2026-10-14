from pathlib import Path
import hashlib,json,zipfile
H=Path(__file__).resolve().parent;out=H.parent/'x0xb0x-blender-case-revision-7.zip';assert not out.exists()
assert json.loads((H/'verification/saved-model-geometry-audit.json').read_text())['passed']
assert json.loads((H/'verification/final-saved-scene-audit.json').read_text())['passed']
assert json.loads((H/'verification/final-render-review.json').read_text())['passed']
assert json.loads((H/'verification/final-front-control-assembly-audit.json').read_text())['passed']
assert json.loads((H/'verification/full-scene-native-bounds-audit.json').read_text())['passed']
exclude={'x0xb0x-inspection.blend','delivery-manifest.json','package-verification.json','harness-routing-study-preview.png','tl1100-manufacturer-cad-review.png','diyaudio-public-thread.html','Same_Sky_MJ-3536N.zip'}
def include(p):
 rel=p.relative_to(H)
 if not p.is_file() or any(x.startswith('.') or x in ['__pycache__','config','cache'] for x in rel.parts):return False
 if rel.parts[:2] in [('board-meshes','mainboard'),('board-meshes','ioboard')]:return False
 if p.name in exclude or p.name.startswith('preview-') or 'experimental' in p.name or p.name.endswith(('.blend1','.log','.pyc','.FCStd1','.lck','.kicad_prl')):return False
 return True
files=sorted(p for p in H.rglob('*') if include(p));manifest={'files':{str(p.relative_to(H)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
meta=H/'delivery-manifest.json';meta.write_text(json.dumps(manifest,indent=2)+'\n');tmp=out.with_suffix('.zip.tmp');prefix='x0xb0x-blender-case-revision-7/'
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files+[meta]:z.write(p,prefix+str(p.relative_to(H)))
with zipfile.ZipFile(tmp) as z:
 assert z.testzip() is None
 for n,r in manifest['files'].items():
  data=z.read(prefix+n);assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],n
assert not out.exists();tmp.replace(out)
r={'archive':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'verified_payload_files':len(files),'zip_crc_ok':True,'all_manifest_hashes_match':True}
(H/'package-verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
