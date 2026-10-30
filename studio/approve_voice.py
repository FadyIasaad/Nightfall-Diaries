"""Approve a saved Kokoro audition without altering its fixed voice ID.
Usage: python -m studio.approve_voice S01_the_last_little_fox s01_ember
"""
import argparse,json
from .util import ROOT,save

def main():
    p=argparse.ArgumentParser();p.add_argument('series');p.add_argument('character');a=p.parse_args()
    folder=ROOT/'seasons'/a.series
    sample=folder/'voices'/a.character/'cloud_audition.wav'
    if not sample.exists():raise FileNotFoundError('Audition not yet rendered; run one episode containing this speaker first')
    reg=json.loads((folder/'characters/character_registry.json').read_text())
    c=next((x for x in reg['characters'] if x['id']==a.character),None)
    if not c:raise ValueError('Unknown cast id')
    c.setdefault('assets',{})['voice_status']='USER_APPROVED'
    save(f'seasons/{a.series}/characters/character_registry.json',reg)
    print('VOICE APPROVED:',a.character,c['voice']['voice_id'],'sample:',sample)
if __name__=='__main__':main()
