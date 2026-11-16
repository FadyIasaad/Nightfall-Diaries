"""Clean-final Nightfall E01 V4 (opaque realistic Moss shell, no public upload).

Reuses the 14 original voices and 180s script edit but does NOT reuse the
visually invalid V3 video cache. SHA and scene-film checkpoints are isolated.
"""
from pilot import e01_director_v2 as film

def main():
    film.VERSION="nightfall-e01-v4-moss-opaque-shell-20261116"
    film.OUT=film.ROOT/"output/nightfall_e01_director_v4"
    film.STATE=film.OUT/"progress.json"
    film.FINAL=film.OUT/"Nightfall_S01_E01_V4_Clean_180s_FINAL_REVIEW.mp4"
    film.main()

if __name__=="__main__":
    main()
