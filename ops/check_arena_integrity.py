"""Verify frozen prior experiments and the original website before arena publication."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PDF_SHA='0c2be47ea19f04713c5e59ff5ced07e7b3c68336c1121b8a71bb212ff6fd0486'
BANNER='<p class="nav-note" id="arena-v1-note">这是第一次尝试，其随机世界没有包含黑影里的危险，结论以<a href="arena.html">竞技场页面</a>为准。</p>\n'


def command(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def tree(ref):
    return {line.split('\t',1)[1]:line for line in command('ls-tree','-r',ref).decode().splitlines()}


def check(out):
    protected=json.loads(Path('/root/3d/.memory/r3/protected-r1-r2-git-tree.json').read_text())
    current=tree('HEAD');wrong=[]
    protected_paths={entry.split('\t',1)[1] for entry in protected['entries']}
    for entry in protected['entries']:
        path=entry.split('\t',1)[1]
        if current.get(path)!=entry:wrong.append(path)
    assert not wrong,wrong
    uncommitted=set(command('diff','--name-only','HEAD','--').decode().splitlines())
    protected_pending=sorted(uncommitted & protected_paths)
    assert not protected_pending, f'Uncommitted changes to protected evidence: {protected_pending}'
    assert not command('diff','4d53214','HEAD','--','src'), 'Frozen production source changed'
    assert not command('diff','6043157','HEAD','--','experimental/navigation'), 'Frozen v1 implementation changed'
    assert not command('diff','--','src','experimental/navigation'), 'Uncommitted frozen source changes'
    assert hashlib.sha256((ROOT/'site/media/report.pdf').read_bytes()).hexdigest()==PDF_SHA
    baseline=tree('4201779');site_wrong=[]
    for path,entry in baseline.items():
        if path.startswith('site/') and path!='site/navigation.html' and current.get(path)!=entry:site_wrong.append(path)
    assert not site_wrong,site_wrong
    site_pending=sorted(path for path in uncommitted if path in baseline and path.startswith('site/') and path!='site/navigation.html')
    assert not site_pending, f'Uncommitted changes to the original site: {site_pending}'
    navigation=(ROOT/'site/navigation.html').read_text()
    old=command('show','4201779:site/navigation.html').decode()
    assert navigation.replace(BANNER,'')==old,'Only the specified v1 explanation banner may change'
    result={'passed':True,'protected_original_entries':len(protected['entries']),'protected_differences':wrong,
            'production_source_unchanged':True,'v1_implementation_unchanged':True,'existing_site_differences':site_wrong,
            'uncommitted_protected_differences':protected_pending,'uncommitted_existing_site_differences':site_pending,
            'v1_note_only':True,'pdf_sha256':PDF_SHA,'main':command('rev-parse','HEAD').decode().strip()}
    Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Frozen source, prior evidence, original site and PDF integrity passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();check(args.out)
