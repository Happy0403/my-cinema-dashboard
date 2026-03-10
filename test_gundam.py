import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import fetch_movie_poster, TMDB_API_KEY

titles = [
    ("劇場版 機動戦士ガンダム00 -A wakening of the Trailblazer-", "Mobile Suit Gundam 00: A Wakening of the Trailblazer", "2010")
]

for jp, en, year in titles:
    print(f"Testing JP: {jp} | EN: {en} | Year: {year}")
    res = fetch_movie_poster(jp, en, year, TMDB_API_KEY)
    print(f"Result: {res}")
