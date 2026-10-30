#!/usr/bin/env python3
"""Reads a manually verified and scored 7-day CSV; no fabricated live trends.
Usage: python tools/rank_trends.py data/trend_candidates_TEMPLATE.csv
"""
import csv, sys
from pathlib import Path
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('data/trend_candidates_TEMPLATE.csv')
weights={'momentum_0_25':25,'drama_0_25':25,'ten_episode_0_20':20,'originality_0_15':15,'feasibility_0_10':10,'audience_0_5':5}
rows=[]
with p.open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f):
        try:
            if row['eligible'].strip().lower() not in ('yes','true','1'): continue
            vals={name:float(row[name]) for name in weights}
            if any(v<0 or v>weights[k] for k,v in vals.items()): raise ValueError('out of range')
            score=sum(vals.values())
            rows.append((score,row))
        except (ValueError,TypeError,KeyError) as ex: print(f'SKIP invalid row: {row.get("topic")}: {ex}',file=sys.stderr)
rows.sort(reverse=True,key=lambda x:x[0])
if not rows:
    print('No eligible scored candidates. Gather verified current Google Trends data and score them.');sys.exit(1)
for score,row in rows:
    print(f'{score:5.1f}/100  {row["topic"]} | {row["source"]} | {row["observed_at"]}')
print('WARNING: This ranks only supplied editorial scores; it does not fetch trends, establish freshness, generate series, or publish videos.')
if rows[0][0]<65: print('Top score below threshold: use a fresh verified shortlist or original evergreen fallback.')
