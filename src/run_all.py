"""One-command raw-input reproduction. Never installs packages automatically."""
import argparse
from pathlib import Path
import subprocess
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--data-root',type=Path,default=Path.home()/'Downloads')
parser.add_argument('--audit',action='store_true',help='Also repeat the expensive input/hash audit')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
jobs=[]
if args.audit: jobs.append(['audit_inputs.py','--data-root',str(args.data_root)])
jobs.extend([['replicate.py','--data-root',str(args.data_root)],['validate.py'],['build_report.py']])
for script,*arguments in jobs:
    subprocess.run([sys.executable,str(root/'src'/script),*arguments],cwd=root,check=True)
print('Empirical outputs, validation and Markdown report regenerated. Optional web companion requires its separate documented build.')
