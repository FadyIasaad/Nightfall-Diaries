"""Final E01 v3 clean composition review, retaining canon and real Kokoro."""
from pilot import e01_director_v2 as engine

def main():
    engine.VERSION="nightfall-e01-v3-premium-moss-composed-feather-20261116"
    engine.OUT=engine.ROOT/"output/nightfall_e01_director_v3"
    engine.STATE=engine.OUT/"progress.json"
    engine.FINAL=engine.OUT/"Nightfall_S01_E01_V3_Premium_Moss_Story_180s_REVIEW.mp4"
    engine.main()

if __name__=="__main__":
    main()
