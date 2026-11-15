"""Run a higher-quality SHA-locked Ember 2.5D illustrated E01 via free CPU.

Keeps the proven 14 Kokoro voices and old E01 untouched. Separate artifact
namespace, isolated checkpoint and no social publishing.
"""
import argparse
from pathlib import Path

from pilot import e01_cpu_film as film
from studio import painterly_reference_actor as premium


def configure():
    film.OUT = film.ROOT / "output/cpu_painterly_e01"
    film.STATUS = film.OUT / "progress.json"
    film.FILM = film.OUT / "Nightfall_S01_E01_painterly_Ember_25D_UNAPPROVED.mp4"
    film.SCHEMA = premium.SCHEMA
    film.render_frame = premium.render_frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("sample", "full"), required=True)
    args = parser.parse_args()
    configure()
    film.draw(sample=args.mode == "sample")


if __name__ == "__main__":
    main()
