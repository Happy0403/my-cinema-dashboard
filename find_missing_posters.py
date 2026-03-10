import sys
import os
import pandas as pd
import time

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import fetch_movie_poster, FALLBACK_POSTER, TMDB_API_KEY

df = pd.read_csv("movies_data.csv")

missing_posters = []

print("Scanning for missing posters...")
for index, row in df.iterrows():
    jp_title = str(row['邦題']).strip()
    en_title = str(row['原題']).strip()
    year = str(row['公開年']).replace('年', '').strip() if pd.notnull(row['公開年']) else None
    
    # We clear cache internally? st.cache_data is annoying in script mode, let's bypass it by calling the internal logic or just use the cached version.
    
    poster = fetch_movie_poster(jp_title, en_title, year, TMDB_API_KEY)
    
    if poster == FALLBACK_POSTER:
        missing_posters.append((row['No'], jp_title, en_title, year))
        print(f"Missing: No.{row['No']} | JP: {jp_title} | EN: {en_title} | Year: {year}")
        
    # Rate limit sleep
    time.sleep(0.1)

print(f"\nTotal missing posters: {len(missing_posters)}")
