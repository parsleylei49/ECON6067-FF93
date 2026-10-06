"""Create a review archive from committed files plus a recoverable Git bundle.

Run only after the repository is clean. This never uploads or publishes.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

root=Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(['git','-C',str(root),*args]).decode()
if git('status','--porcelain').strip():
    raise SystemExit('Commit/review outstanding changes before packaging.')
files=git('ls-files','-z').split('\0')
for filename in files:
    if Path(filename).name in {'monthly_stock.csv','Compustat.csv','CCM.csv','F-F factors and RF.csv','Paper1_FF93.pdf'}:
        raise SystemExit('Restricted input tracked: '+filename)
bundle=root.parent/'ECON6067-FF93-history.bundle'
subprocess.run(['git','-C',str(root),'bundle','create',str(bundle),'--all'],check=True)
subprocess.run(['git','-C',str(root),'bundle','verify',str(bundle)],check=True)
archive=root.parent/'ECON6067-FF93-delivery.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as out:
    for filename in files:
        if filename: out.write(root/filename,'ECON6067-FF93/'+filename)
    out.write(bundle,bundle.name)
with zipfile.ZipFile(archive) as check:
    assert check.testzip() is None
manifest={'archive':archive.name,'bytes':archive.stat().st_size,
          'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
          'git_head':git('rev-parse','HEAD').strip(),
          'git_commits':int(git('rev-list','--count','HEAD')),
          'includes_restricted_raw_data':False,'published_or_submitted':False}
(root.parent/'ECON6067-FF93-delivery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
