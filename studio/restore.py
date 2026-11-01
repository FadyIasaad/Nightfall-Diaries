"""Restore original authored scripts from old Git history on the SAME repository."""
import json,subprocess,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
PIN='02f426cb9af1276d78465ff1ec1dbf190153f160'
SERIES=[('S01_the_last_little_fox',12),('S02_the_boy_who_forgot_tomorrow',10)]
def main():
 for series,n in SERIES:
  for i in range(1,n+1):
   p=f'seasons/{series}/scripts/E{i:02d}.json'
   try: data=subprocess.check_output(['git','show',f'{PIN}:{p}'],cwd=ROOT,stderr=subprocess.DEVNULL)
   except subprocess.CalledProcessError: raise SystemExit(f'RESTORE FAILED: original commit unavailable; keep old repository history: {p}')
   script=json.loads(data)
   if len(script.get('scenes',[]))<3:raise SystemExit('Invalid original source '+p)
   target=ROOT/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
   print('RESTORED',p)
if __name__=='__main__': main()
