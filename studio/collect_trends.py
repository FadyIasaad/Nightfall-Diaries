"""Low-cost scheduled trend-only observer. Does not create videos or post content."""
from .trends import collect
from .util import read,checkpoint

def main():
    results=collect(read('cloud_config.json'))
    print('Seven-day trend snapshots:',len(results.get('entries',[])),'errors:',results.get('errors',[]))
    checkpoint('v4: daily trend snapshot (no video or upload)')
if __name__=='__main__':main()
