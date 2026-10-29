#!/usr/bin/env python3
"""Promotion must reject unvalidated, mismatched, or mutable releases."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

script = Path(__file__).resolve().parents[1] / 'scripts/promote-release.py'
with tempfile.TemporaryDirectory(prefix='moonbeam-promotion-') as directory:
    root = Path(directory)
    tool = root / 'gh'
    tool.write_text('''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
case=os.environ['TEST_CASE']
if sys.argv[1:3]==['release','create']:
 Path(os.environ['PROMOTED']).write_text(' '.join(sys.argv[1:]));raise SystemExit(0)
if '/actions/runs/' in sys.argv[-1]:
 run={'conclusion':'success','path':'.github/workflows/release-candidate.yml',
 'head_branch':'release/6.2','head_sha':'a'*40,'event':'push','html_url':'https://example.test/run/42'}
 if case=='failed':run['conclusion']='failure'
 if case=='wrong-branch':run['head_branch']='master'
 if case=='pull-request':run['event']='pull_request'
 print(json.dumps(run));raise SystemExit(0)
if '/git/ref/tags/' in sys.argv[-1]:
 if case=='tag-exists':print('{}');raise SystemExit(0)
 print('HTTP 404' if case!='api-failure' else 'HTTP 403',file=sys.stderr);raise SystemExit(1)
raise SystemExit(2)
''')
    tool.chmod(0o755)
    artifact = root / 'portable.tar.gz'
    artifact.write_bytes(b'tested candidate bytes')
    manifest = {'version':'6.2.0-moonbeam.2+gaaaaaaaa', 'base_version':'6.2.0-moonbeam.2',
        'dirty':False, 'commit':'a'*40, 'run_id':42,
        'sha256':{artifact.name:hashlib.sha256(artifact.read_bytes()).hexdigest()}}
    cases = ['success','failed','wrong-branch','pull-request','tag-exists','api-failure',
             'dirty','wrong-sha','wrong-run','tampered','missing-hardware','bad-version']
    for case in cases:
        data = json.loads(json.dumps(manifest))
        if case=='dirty':data['dirty']=True
        if case=='wrong-sha':data['commit']='b'*40
        if case=='wrong-run':data['run_id']=43
        if case=='tampered':data['sha256'][artifact.name]='0'*64
        if case=='bad-version':data['base_version']='invalid/version'
        (root/'candidate.json').write_text(json.dumps(data))
        marker = root / f'promoted-{case}'
        env=dict(os.environ, PATH=str(root)+os.pathsep+os.environ['PATH'], TEST_CASE=case, PROMOTED=str(marker))
        args=['python3',str(script),'--run-id','42','--artifacts',str(root)]
        if case!='missing-hardware':args.append('--hardware-validated')
        result=subprocess.run(args,env=env,capture_output=True,text=True)
        assert (result.returncode==0)==(case=='success'),(case,result.stderr)
        assert marker.exists()==(case=='success'),case
    print(f'PASS: {len(cases)} release promotion scenarios; failed validation never publishes or retags')
