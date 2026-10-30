"""Optional command for controlled visual-reference replacement, for browser Codespaces.
Usage: python -m studio.approve_art <series-id> <character-id> <new-image.png>
"""
import argparse,shutil,json
from PIL import Image
from .util import ROOT,sha,save,read
from .identity import identity_hash

def main():
    p=argparse.ArgumentParser();p.add_argument('series');p.add_argument('character');p.add_argument('image');args=p.parse_args()
    folder=ROOT/'seasons'/args.series
    regpath=folder/'characters/character_registry.json'
    reg=json.loads(regpath.read_text())
    c=next((x for x in reg['characters'] if x['id']==args.character),None)
    if not c:raise ValueError('Unknown character in this series')
    new=ROOT/args.image
    with Image.open(new) as im:
        if im.width<500 or im.height<500:raise ValueError('Approved reference must be at least 500x500')
        dest=folder/'characters'/c['id']/'cloud_reference.png'
        dest.parent.mkdir(parents=True,exist_ok=True)
        im.convert('RGB').save(dest)
    locks=read(f'seasons/{args.series}/characters/cloud_reference_locks.json',{})
    locks[c['id']]=sha(dest);save(f'seasons/{args.series}/characters/cloud_reference_locks.json',locks)
    c.setdefault('assets',{})['reference_status']='USER_APPROVED'
    save(f'seasons/{args.series}/characters/character_registry.json',reg)
    # Asset approval status not part of identity_hash, appearance/voice remain locked.
    print('APPROVED REFERENCE:',dest)
if __name__=='__main__':main()
