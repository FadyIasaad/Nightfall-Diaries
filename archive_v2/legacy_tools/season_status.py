#!/usr/bin/env python3
"""Shows the next allowed work item; does not pretend to publish or query trends."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
reg=json.loads((P/'data/series_registry.json').read_text(encoding='utf-8'))
for s in reg['series']:
    if not s['complete']:
        print(f'NEXT SERIES: {s["title"]} [{s["id"]}], {s["episode_count"]} episodes.')
        print('Produce approved cast images and audition WAVs, then 3-episode buffer, then publish sequentially.')
        print('Trend selection is BLOCKED until both launch series final episodes are confirmed published.')
        break
else:
    print('Both starter series completed. Now verify the last seven days of trends and draft an ALL-NEW original series of 10+ episodes.')
