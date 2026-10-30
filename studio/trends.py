"""Seven-day observed RSS snapshots; never fabricate trends.
RSS is a current snapshot; seven-day coverage accumulates over 7 days of runs.
"""
import re, math, hashlib, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests
import xml.etree.ElementTree as ET
from .util import read, save, utcnow, ROOT

THEMES = {
 'space':r'\b(space|mars|moon|nasa|astronaut|starship|rocket|asteroid|solar|galaxy)\b',
 'robotics':r'\b(ai|robot|robotics|artificial intelligence|android|machine learning)\b',
 'ocean':r'\b(ocean|sea|coral|whale|dolphin|shark|submarine)\b',
 'animals':r'\b(animal|fox|lion|cat|dog|wildlife|panda|zoo|puppy|kitten)\b',
 'storms':r'\b(storm|weather|rain|snow|aurora|eclipse|thunder)\b',
 'science':r'\b(science|discovery|telescope|fossil|dinosaur|archaeology|physics|planet)\b',
 'sports':r'\b(football|soccer|basketball|olympic|marathon|race|tennis|world cup)\b',
 'music':r'\b(music|festival|concert|singer|song|orchestra|piano)\b',
 'gaming':r'\b(game|gaming|video game|minecraft|esport|console|pokemon)\b',
 'nature':r'\b(forest|tree|flower|mountain|nature|garden|river|island)\b'
}
BLOCK=re.compile(r'\b(election|war|shooting|massacre|killed|death|suicide|tragedy|terror|genocide|abuse|sexual|porn|politic|president|scandal|trial|stock|crypto|fraud|bomb|trump|biden)\b',re.I)

def parse_traffic(value):
    m=re.search(r'([\d,.]+)\s*([KMB]?)',str(value).upper())
    if not m:return 0
    return int(float(m.group(1).replace(',',''))*{'':1,'K':1_000,'M':1_000_000,'B':1_000_000_000}[m.group(2)])

def theme(title):
    if BLOCK.search(title): return None
    for key,regex in THEMES.items():
        if re.search(regex,title,re.I): return key
    return None

def collect(config, client=requests):
    old=read('cloud_data/trend_history.json',{'entries':[],'errors':[]})
    new=[]; problems=[]; checked=utcnow()
    for geo in config['trends']['geo']:
        try:
            r=client.get('https://trends.google.com/trending/rss',params={'geo':geo},timeout=config['trends']['fetch_timeout_seconds'],headers={'User-Agent':'Mozilla/5.0 (DramaUniverse research bot)'})
            r.raise_for_status(); tree=ET.fromstring(r.content)
            entries=tree.findall('.//item')
            if not entries:raise ValueError('No RSS items')
            for entry in entries:
                title=(entry.findtext('title') or '').strip()
                if not title:continue
                traffic=entry.findtext('{https://trends.google.com/trending/rss}approx_traffic') or next((e.text for e in entry if e.tag.endswith('approx_traffic')),'0')
                new.append({'title':title,'geo':geo,'traffic':parse_traffic(traffic),'observed_utc':checked,'source_url':entry.findtext('link') or 'https://trends.google.com/trending/','source':'Google Trends RSS'})
        except Exception as e:
            problems.append(f'{geo}: {type(e).__name__}: {str(e)[:150]}')
    cutoff=datetime.now(timezone.utc)-timedelta(days=7)
    retained=[x for x in old.get('entries',[]) if datetime.fromisoformat(x['observed_utc'])>=cutoff]
    # One observation of each title per country per day, enough for 7-day ranking.
    unique={(x['title'].casefold(),x['geo'],x['observed_utc'][:10]):x for x in retained}
    for x in new: unique[(x['title'].casefold(),x['geo'],checked[:10])]=x
    result={'entries':list(unique.values()),'errors':problems,'last_checked_utc':checked}
    save('cloud_data/trend_history.json',result)
    return result

def rank(trend_data,now=None):
    now=now or datetime.now(timezone.utc)
    cutoff=now-timedelta(days=7)
    grouped={}
    for e in trend_data.get('entries',[]):
        try:
            at=datetime.fromisoformat(e['observed_utc'])
        except (KeyError,ValueError):continue
        if at<cutoff or at>now+timedelta(hours=1):continue
        k=theme(e.get('title',''))
        if not k:continue
        key=e['title'].casefold().strip()
        b=grouped.setdefault(key,{'topic':e['title'],'theme':k,'traffic':0,'observations':0,'regions':set(),'sources':[]})
        b['traffic']=max(b['traffic'],int(e.get('traffic',0)))
        b['observations']+=1;b['regions'].add(e['geo'])
        b['sources'].append({'url':e.get('source_url'),'observed_utc':e['observed_utc'],'geo':e['geo']})
    for b in grouped.values():
        b['score']=round(math.log10(1+b['traffic'])*10 + len(b['regions'])*3 + min(b['observations'],12),2)
        b['regions']=sorted(b['regions'])
    return sorted(grouped.values(),key=lambda b:(-b['score'],b['topic'].casefold()))

def pick_unseen(history,existing_decisions):
    used={x['topic'].casefold() for x in existing_decisions.get('selected',[])}
    return next((x for x in rank(history) if x['topic'].casefold() not in used),None)
