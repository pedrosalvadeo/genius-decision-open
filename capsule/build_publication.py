#!/usr/bin/env python3
"""Build a reproducible source edition from an explicit reviewed source index."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(out):
    if out.exists(): raise ValueError('Output must be a new directory')
    index = json.loads((ROOT/'capsule/publication/source-index.json').read_text())
    files = {}
    for record in index['files']:
        path = record['path']; p = ROOT/path
        if p.is_symlink() or not p.resolve().is_relative_to(ROOT) or not p.is_file():
            raise ValueError('Invalid source path: '+path)
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != record['sha256']: raise ValueError('Source changed: '+path)
        files[path] = raw
    for p in sorted((ROOT/'capsule').rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or p.suffix == '.pyc' or p.is_relative_to(ROOT/'capsule/evidence'):
            continue
        files[p.relative_to(ROOT).as_posix()] = p.read_bytes()
    files['README.md'] = (ROOT/'capsule/publication/README.public.md').read_bytes()
    files['LICENSE'] = (ROOT/'capsule/publication/LICENSE').read_bytes()
    files['NOTICE'] = (ROOT/'capsule/publication/NOTICE').read_bytes()
    files['.github/workflows/capsule.yml'] = (ROOT/'capsule/publication/ci.yml').read_bytes()
    files['.github/workflows/publish-mcp-registry.yml'] = (ROOT/'capsule/publication/mcp-registry-publish.yml').read_bytes()
    files['twin/docs/PRODUCT_ROADMAP.md'] = ('# Genius pleno\n\nEl trabajo incluye casos reales, matemática, motor, observaciones, interpretación, interoperabilidad y colaboración.\n\nVer [misión](../../capsule/HOST_MISSION.md), [frentes abiertos](../../capsule/workstreams.json) y [continuidad](../../capsule/NEXT_WORK.md). Las capacidades actuales son una base, no un techo.\n').encode()
    # Bind the exported index to exported bytes so this edition can rebuild itself.
    for record in index['files']:
        raw = files[record['path']]
        digest = hashlib.sha256(raw).hexdigest()
        if record['sha256'] != digest:
            record.setdefault('origin_sha256', record['sha256'])
            record.setdefault('origin_git_blob', record['git_blob'])
            record['sha256'] = digest
            record['git_blob'] = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    files['capsule/publication/source-index.json'] = (json.dumps(index,indent=2)+'\n').encode()
    patterns = [rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
                rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{40,}',
                rb'AKIA[A-Z0-9]{16}', rb'sk-proj-[A-Za-z0-9_-]{30,}']
    findings = []
    for name, raw in files.items():
        candidates = [(name, raw)]
        if name.endswith('.docx'):
            with zipfile.ZipFile(io.BytesIO(raw)) as doc:
                candidates += [(name+':'+member,doc.read(member)) for member in doc.namelist() if member.endswith('.xml')]
        for member, content in candidates:
            if any(re.search(pattern,content) for pattern in patterns): findings.append(member)
    if findings: raise ValueError('Credential pattern review required in: '+', '.join(findings))
    manifest = {'format':'genius-publication-files/1','base_revision':index['base_revision'],
                'status':'SOURCE_EDITION','repository_url':'https://github.com/pedrosalvadeo/genius-decision-open',
                'files':{n:hashlib.sha256(v).hexdigest() for n,v in sorted(files.items())}}
    files['PUBLICATION_MANIFEST.json'] = (json.dumps(manifest,indent=2)+'\n').encode()
    out.mkdir(parents=True)
    for name, data in files.items():
        p=out/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w',format=tarfile.PAX_FORMAT) as archive:
        for name,data in sorted(files.items()):
            entry=tarfile.TarInfo('genius-decision-open/'+name);entry.size=len(data);entry.mode=0o644;entry.mtime=0
            archive.addfile(entry,io.BytesIO(data))
    raw=buffer.getvalue();(out/'genius-source.tar').write_bytes(raw)
    compressed=gzip.compress(raw,mtime=0);(out/'genius-source.tar.gz').write_bytes(compressed)
    zip_path=out/'genius-source.zip'
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(files.items()):
            entry=zipfile.ZipInfo('genius-decision-open/'+name,date_time=(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr=0o100644<<16;archive.writestr(entry,data)
    artifacts={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in (out/'genius-source.tar',out/'genius-source.tar.gz',zip_path)}
    report={'files':len(files),'artifacts':artifacts,'credential_pattern_findings':[],
            'scan_scope':'Known private-key and credential patterns; not a proof of absence of every possible secret',
            'source_index_entries':len(index['files'])}
    (out/'build-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    print(json.dumps(build(p.parse_args().out),indent=2))
