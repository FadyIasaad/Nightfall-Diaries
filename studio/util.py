import json, os, hashlib, subprocess
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parent.parent

def read(path, fallback=None):
    p = ROOT / path
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else fallback

def save(path, obj):
    p = ROOT / path; p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(p)

def utcnow(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def checkpoint(message):
    """Fail before remote side effect if a necessary intent checkpoint cannot be persisted."""
    if os.getenv('GIT_CHECKPOINT') != '1': return
    subprocess.run(['git','add','cloud_data','seasons'], cwd=ROOT, check=True)
    diff = subprocess.run(['git','diff','--cached','--quiet'], cwd=ROOT)
    if diff.returncode == 0: return
    subprocess.run(['git','-c','user.name=Drama Cloud Bot','-c','user.email=drama-bot@users.noreply.github.com','commit','-m',message],cwd=ROOT,check=True)
    subprocess.run(['git','push'],cwd=ROOT,check=True)
