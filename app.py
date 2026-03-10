import streamlit as st
import pandas as pd
import datetime
import requests
import urllib.parse
from functools import lru_cache

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="My Cinema Dashboard", page_icon="🎥", layout="wide")

st.markdown("""
<style>
    /* Custom Aesthetics */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ff4b4b;
    }
    .metric-label {
        font-size: 1rem;
        color: #a0a0a0;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: 600;
    }
    .poster-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #1e1e1e;
        border-radius: 12px;
        padding: 5px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        transition: transform 0.2s ease-in-out;
    }
    .poster-container:hover {
        transform: scale(1.03);
    }
    .poster-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #fff;
        text-align: center;
        margin-top: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: 100%;
        padding: 0 5px;
    }
    .poster-rating {
        font-size: 0.8rem;
        color: #ffd700;
        text-align: center;
        margin-bottom: 5px;
    }
    .poster-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        justify-content: center;
        padding: 4px 5px 8px 5px;
        width: 100%;
    }
    .poster-tag {
        font-size: 0.65rem;
        color: #fff;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 4px;
        padding: 2px 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 95%;
    }
</style>
""", unsafe_allow_html=True)

CSV_FILE = "movies_data.csv"
TMDB_API_KEY = "a419125f7fa3acf8beb87c35e0ff8ec2" 
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
FALLBACK_POSTER = "https://placehold.co/500x750/1e1e1e/888888?text=No+Poster"

# --- TMDB API LOGIC ---
@st.cache_data(show_spinner=False, ttl=86400) # Cache for 24 hours to deeply respect rate limits
def fetch_movie_poster(title, original_title=None, year=None, api_key=TMDB_API_KEY):
    if not api_key:
        return FALLBACK_POSTER
        
    def search_tmdb(query_str, release_year=None):
        url = f"{TMDB_BASE_URL}/search/movie?api_key={api_key}&query={urllib.parse.quote(query_str)}&language=ja-JP"
        if release_year:
            url += f"&primary_release_year={release_year}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results and results[0].get('poster_path'):
                    return f"{TMDB_IMAGE_BASE_URL}{results[0]['poster_path']}"
        except Exception as e:
            pass
        return None

    # Try original title first as TMDB matching is often better with English titles
    if original_title and str(original_title).strip() and str(original_title) != "nan":
        poster = search_tmdb(str(original_title).strip(), year)
        if poster: return poster
        
    # Fallback to Japanese title
    if title and str(title).strip() and str(title) != "nan":
        # clean up title "映画 - タイトル" etc
        clean_title = str(title).strip()
        poster = search_tmdb(clean_title, year)
        if poster: return poster
        
        # Try without year if year matching failed
        if year:
            poster = search_tmdb(clean_title)
            if poster: return poster

    return FALLBACK_POSTER

@st.cache_data(show_spinner=False, ttl=86400)
def fetch_movie_details(title, original_title=None, year=None, api_key=TMDB_API_KEY):
    if not api_key or api_key == "69018610eb3f8a4e8dca9632eb518172":
        return "APIキーが無効です。", None
        
    def search_and_get_details(query_str, release_year=None):
        url = f"{TMDB_BASE_URL}/search/movie?api_key={api_key}&query={urllib.parse.quote(query_str)}&language=ja-JP"
        if release_year:
            url += f"&primary_release_year={release_year}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    movie_id = results[0]['id']
                    overview = results[0].get('overview', '')
                    
                    # Fetch videos
                    vid_url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos?api_key={api_key}&language=ja-JP"
                    vid_resp = requests.get(vid_url, timeout=5)
                    video_key = None
                    if vid_resp.status_code == 200:
                        vids = vid_resp.json().get('results', [])
                        # Try to find a YouTube trailer
                        for v in vids:
                            if v.get('site') == 'YouTube' and v.get('type') == 'Trailer':
                                video_key = v.get('key')
                                break
                    # Fallback to English videos if no Japanese trailer
                    if not video_key:
                        vid_url_en = f"{TMDB_BASE_URL}/movie/{movie_id}/videos?api_key={api_key}"
                        vid_resp_en = requests.get(vid_url_en, timeout=5)
                        if vid_resp_en.status_code == 200:
                            vids_en = vid_resp_en.json().get('results', [])
                            for v in vids_en:
                                if v.get('site') == 'YouTube' and v.get('type') == 'Trailer':
                                    video_key = v.get('key')
                                    break
                    
                    if not overview:
                        overview = "日本語のあらすじがありません。"
                    return overview, video_key
        except Exception:
            pass
        return None

    # Try original title first
    if original_title and str(original_title).strip() and str(original_title) != "nan":
        res = search_and_get_details(str(original_title).strip(), year)
        if res: return res
        
    # Fallback to Japanese title
    if title and str(title).strip() and str(title) != "nan":
        clean_title = str(title).strip()
        res = search_and_get_details(clean_title, year)
        if res: return res
        
        if year:
            res = search_and_get_details(clean_title)
            if res: return res

    return "映画情報が見つかりませんでした。", None

import os

READ_ONLY_MODE = os.environ.get("READ_ONLY_MODE", "false").lower() == "true"

@st.dialog("映画詳細", width="large")
def show_movie_details(movie):
    st.subheader(f"{movie['邦題']} ({movie.get('公開年', '不明')})")
    if pd.notnull(movie.get('原題')) and str(movie['原題']).strip() and str(movie['原題']) != "nan":
        st.markdown(f"**原題:** {movie['原題']}")
        
    year_str = str(movie["公開年"]).replace('年', '').strip() if pd.notnull(movie["公開年"]) else None
    
    col1, col2 = st.columns([1, 2])
    with col1:
        poster_url = fetch_movie_poster(movie["邦題"], movie["原題"], year_str, TMDB_API_KEY)
        st.image(poster_url, use_container_width=True)
        
        rating_str = f"★ {movie['評価']}" if pd.notnull(movie['評価']) and str(movie['評価']) != "" else "評価なし"
        if movie.get('殿堂入り', False):
            rating_str += " 🏆"
        st.markdown(f"**評価:** {rating_str}")
        
    with col2:
        overview, video_key = fetch_movie_details(movie["邦題"], movie["原題"], year_str, TMDB_API_KEY)
        
        st.markdown("### あらすじ")
        st.write(overview)
        
        st.markdown("### 情報")
        st.markdown(f"**監督:** {movie.get('監督', '不明')}")
        st.markdown(f"**キャスト:** {movie.get('主要キャスト', '不明')}")
        st.markdown(f"**ジャンル:** {movie.get('ジャンル', '不明')}")
        st.markdown(f"**鑑賞日:** {movie.get('鑑賞日', '不明')} / **場所:** {movie.get('鑑賞場所', '不明')} / **方式:** {movie.get('上映方式', '不明')}")
        
    if video_key:
        st.divider()
        st.markdown("### 予告編")
        st.video(f"https://www.youtube.com/watch?v={video_key}")


# --- DATA HANDLING ---
@st.cache_data(show_spinner=False)
def load_data(file_mtime):
    try:
        df = pd.read_csv(CSV_FILE)
        # Ensure 'No' is numeric
        df['No'] = pd.to_numeric(df['No'], errors='coerce')
        # Ensure 殿堂入り is boolean
        df['殿堂入り'] = df['殿堂入り'].astype(bool)
        # Clean up empty strings to handle NaN cleanly
        df.fillna('', inplace=True)
        # Handle cases where the columns might not exist yet
        if '監督' not in df.columns:
            df['監督'] = ''
        if '主要キャスト' not in df.columns:
            df['主要キャスト'] = ''
        if 'ジャンル' not in df.columns:
            df['ジャンル'] = ''
        return df
    except FileNotFoundError:
        st.error(f"データファイルが見つかりません: {CSV_FILE}")
        return pd.DataFrame()

def save_data(df):
    if READ_ONLY_MODE:
        st.error("現在閲覧専用モードのため、データの保存はできません。")
        return
    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

# --- MAIN APP LOGIC ---
def main():
    st.title("🎥 マイ・シネマダッシュボード")
    
    file_mtime = os.path.getmtime(CSV_FILE) if os.path.exists(CSV_FILE) else 0
    df = load_data(file_mtime)
    
    if df.empty:
        st.warning("データがまだ存在しません。新しいデータを登録してください。")
        df = pd.DataFrame(columns=["No", "邦題", "原題", "公開年", "評価", "殿堂入り", "鑑賞日", "鑑賞場所", "上映方式", "ジャンル", "監督", "主要キャスト"])
        
    # --- TABS ---
    if READ_ONLY_MODE:
        tab_dashboard, tab_gallery = st.tabs(["📊 ダッシュボード", "🖼️ ギャラリー"])
    else:
        tab_dashboard, tab_gallery, tab_add_new = st.tabs(["📊 ダッシュボード", "🖼️ ギャラリー", "➕ 新規登録"])
    
    # --- DASHBOARD TAB ---
    with tab_dashboard:
        # Top Search Bar
        search_query = st.text_input("🔍 作品をフリーワード検索 (タイトル・監督・キャスト)", "", placeholder="例: クリストファー・ノーラン", key="main_search")
        
        # SIDEBAR FILTERS
        st.sidebar.header("🔍 絞り込み検索")
        
        # Rating Filter (Range 1-10)
        ratings = [str(r) for r in sorted(pd.to_numeric(df['評価'][df['評価'] != ''], errors='coerce').dropna().unique().astype(int))]
        if not ratings: ratings = [str(i) for i in range(1, 11)]
        selected_ratings = st.sidebar.multiselect("評価点数 (1〜10)", options=[str(i) for i in range(1, 11)], default=[])
        
        # Hall of Fame Filter
        hof_only = st.sidebar.checkbox("殿堂入り作品のみ (*, 🏆)")
        
        # Genre Filter
        all_genres_raw = df["ジャンル"].dropna().astype(str).str.cat(sep='、').split('、')
        genres_list = sorted(list(set([g.strip() for g in all_genres_raw if g.strip()])))
        selected_genres = st.sidebar.multiselect("ジャンル", options=genres_list, default=[])
        
        # Format Filter
        formats = [f for f in df["上映方式"].unique() if f]
        selected_formats = st.sidebar.multiselect("上映方式", options=formats, default=[])
        
        # Apply Filters
        filtered_df = df.copy()
        
        if search_query:
            filtered_df = filtered_df[
                filtered_df["邦題"].str.contains(search_query, case=False, na=False) | 
                filtered_df["原題"].str.contains(search_query, case=False, na=False) |
                filtered_df["監督"].astype(str).str.contains(search_query, case=False, na=False) |
                filtered_df["主要キャスト"].astype(str).str.contains(search_query, case=False, na=False)
            ]
        
        if selected_ratings:
            filtered_df = filtered_df[filtered_df["評価"].astype(str).isin(selected_ratings)]
            
        if hof_only:
            filtered_df = filtered_df[filtered_df["殿堂入り"] == True]
            
        if selected_genres:
            mask = filtered_df["ジャンル"].astype(str).apply(lambda x: any(g in x for g in selected_genres))
            filtered_df = filtered_df[mask]
            
        if selected_formats:
            filtered_df = filtered_df[filtered_df["上映方式"].isin(selected_formats)]
            
        st.markdown(f"**表示件数: {len(filtered_df)} 件**")
        
        # display dataframe
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("📈 鑑賞統計")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**評価ごとの作品数**")
            # Convert to numeric for better sorting
            filtered_numeric_rating = pd.to_numeric(filtered_df["評価"], errors='coerce').dropna()
            if not filtered_numeric_rating.empty:
                rating_counts = filtered_numeric_rating.value_counts().sort_index()
                st.bar_chart(rating_counts)
            else:
                st.info("データがありません")
                
        with col2:
            st.markdown("**年間の鑑賞本数**")
            # Extract year from 鑑賞日 if available, else fallback to 公開年 just to show something
            # Let's try to parse year from 鑑賞日 (e.g. 2024/04/13)
            date_col = filtered_df["鑑賞日"].copy()
            # Extract basic year regex
            years = date_col.str.extract(r'(\d{4})')[0].dropna()
            if not years.empty:
                year_counts = years.value_counts().sort_index()
                st.bar_chart(year_counts)
            else:
                st.info("鑑賞年のデータが十分にありません (鑑賞日が未入力の可能性があります)")
                
    # --- GALLERY TAB ---
    with tab_gallery:
        st.header("🖼️ ポスターギャラリー")
        if TMDB_API_KEY == "69018610eb3f8a4e8dca9632eb518172":
            st.warning("⚠️ 現在のTMDB APIキーはサンプルのため無効です。実際のポスターを表示するには、[TMDB](https://www.themoviedb.org/) で無料のAPIキーを取得し、`app.py`の `TMDB_API_KEY` を更新してください。")
        st.markdown(f"**表示件数: {len(filtered_df)} 件**  *(左サイドバーの絞り込みが適用されています)*")
        
        if filtered_df.empty:
            st.info("表示する映画がありません。「📊 ダッシュボード」の絞り込み条件を変更してください。")
        else:
            # --- Pagination Logic ---
            items_per_page = 48 # 6 columns * 8 rows
            total_items = len(filtered_df)
            total_pages = max(1, (total_items - 1) // items_per_page + 1)
            
            if 'gallery_page' not in st.session_state:
                st.session_state.gallery_page = 1
                
            # Reset page if filter shrinks data
            if st.session_state.gallery_page > total_pages:
                st.session_state.gallery_page = 1
                
            current_page = st.session_state.gallery_page
            start_idx = (current_page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            page_df = filtered_df.iloc[start_idx:end_idx]
            
            # Pagination UI Top
            if total_pages > 1:
                pag_col1, pag_col2, pag_col3 = st.columns([1, 2, 1])
                with pag_col1:
                    if st.button("⬅️ 前のページ", disabled=current_page <= 1, key="prev_top", use_container_width=True):
                        st.session_state.gallery_page -= 1
                        st.rerun()
                with pag_col2:
                    st.markdown(f"<div style='text-align: center; padding-top: 5px; font-weight: bold;'>ページ {current_page} / {total_pages}</div>", unsafe_allow_html=True)
                with pag_col3:
                    if st.button("次のページ ➡️", disabled=current_page >= total_pages, key="next_top", use_container_width=True):
                        st.session_state.gallery_page += 1
                        st.rerun()
            
            st.write("") # Spacing
            
            cols_per_row = 6 # Up to 6 columns for a wide screen layout
            rows = [page_df.iloc[i:i+cols_per_row] for i in range(0, len(page_df), cols_per_row)]
            
            for row_df in rows:
                cols = st.columns(cols_per_row)
                for idx, (_, movie) in enumerate(row_df.iterrows()):
                    with cols[idx]:
                        # Extract 4-digit year for better TMDB searching
                        year_str = str(movie["公開年"]).replace('年', '').strip() if pd.notnull(movie["公開年"]) else None
                        poster_url = fetch_movie_poster(movie["邦題"], movie["原題"], year_str, TMDB_API_KEY)
                        
                        rating_str = f"★ {movie['評価']}" if pd.notnull(movie['評価']) and str(movie['評価']) != "" else "評価なし"
                        if movie.get('殿堂入り', False):
                            rating_str += " 🏆"
                            
                        # HTML card for the poster
                        st.markdown(f"""
                        <div class="poster-container" title="原題: {movie.get('原題', 'なし')} | 公開: {movie.get('公開年', '不明')}">
                            <img src="{poster_url}" class="poster-img" style="width: 100%; aspect-ratio: 2/3; object-fit: cover; border-radius: 8px;" loading="lazy">
                            <div class="poster-title">{movie["邦題"]}</div>
                            <div class="poster-rating">{rating_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("詳細・予告編", key=f"details_btn_{movie['No']}_{idx}_{current_page}", use_container_width=True):
                            show_movie_details(movie)
                            
            # Pagination UI Bottom
            if total_pages > 1:
                st.divider()
                pag_col1_b, pag_col2_b, pag_col3_b = st.columns([1, 2, 1])
                with pag_col1_b:
                    if st.button("⬅️ 前のページ", disabled=current_page <= 1, key="prev_bot", use_container_width=True):
                        st.session_state.gallery_page -= 1
                        st.rerun()
                with pag_col2_b:
                    st.markdown(f"<div style='text-align: center; padding-top: 5px; font-weight: bold;'>ページ {current_page} / {total_pages}</div>", unsafe_allow_html=True)
                with pag_col3_b:
                    if st.button("次のページ ➡️", disabled=current_page >= total_pages, key="next_bot", use_container_width=True):
                        st.session_state.gallery_page += 1
                        st.rerun()
                        
    # --- ADD NEW TAB ---
    if not READ_ONLY_MODE:
        with tab_add_new:
            st.header("新しい鑑賞記録を追加")
            
            # Prepare options for selects
            locations = sorted([loc for loc in df["鑑賞場所"].unique() if loc])
        if "長野グランドシネマズ" not in locations: locations.insert(0, "長野グランドシネマズ")
        if "松本シネマライツ" not in locations: locations.insert(1, "松本シネマライツ")
        
        formats_opt = sorted([f for f in df["上映方式"].unique() if f])
        
        with st.form("add_movie_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            
            with col_a:
                new_title = st.text_input("邦題 *", help="例: インターステラー")
                new_orig_title = st.text_input("原題", help="例: Interstellar")
                new_year = st.text_input("公開年", help="例: 2014年")
                new_rating = st.selectbox("評価 (1〜10) *", options=[str(i) for i in range(1, 11)][::-1], index=4)
                new_genre = st.text_input("ジャンル", help="例: アクション、SF")
                new_director = st.text_input("監督", help="例: クリストファー・ノーラン")
                new_cast = st.text_input("主要キャスト", help="例: マシュー・マコノヒー、アン・ハサウェイ")
                
            with col_b:
                new_date = st.date_input("鑑賞日", value=datetime.date.today())
                
                # Hybrid text/select for location
                loc_col1, loc_col2 = st.columns([2,1])
                with loc_col1:
                    sel_loc = st.selectbox("鑑賞場所", options=["既存リストから選択..."] + locations)
                with loc_col2:
                    txt_loc = st.text_input("その他の鑑賞場所", help="リストにない場合はこちらに入力")
                
                # Hybrid text/select for format
                fmt_col1, fmt_col2 = st.columns([2,1])
                with fmt_col1:
                    sel_fmt = st.selectbox("上映方式", options=["既存リストから選択..."] + formats_opt)
                with fmt_col2:
                    txt_fmt = st.text_input("その他の上映方式", help="リストにない場合はこちらに入力")
                
                new_hof = st.checkbox("殿堂入り作品 (🏆)")
                
            st.markdown("*は必須項目です")
            submitted = st.form_submit_button("登録する", type="primary")
            
            if submitted:
                if not new_title:
                    st.error("邦題は必須入力です！")
                else:
                    # Finalize location and format choices
                    final_loc = txt_loc if txt_loc else (sel_loc if sel_loc != "既存リストから選択..." else "")
                    final_fmt = txt_fmt if txt_fmt else (sel_fmt if sel_fmt != "既存リストから選択..." else "")
                    
                    next_no = int(df['No'].max() + 1) if not df.empty and pd.notnull(df['No'].max()) else 1
                    
                    new_row = {
                        "No": next_no,
                        "邦題": new_title,
                        "原題": new_orig_title,
                        "公開年": new_year,
                        "評価": new_rating,
                        "殿堂入り": new_hof,
                        "鑑賞日": new_date.strftime("%Y/%m/%d"),
                        "鑑賞場所": final_loc,
                        "上映方式": final_fmt,
                        "ジャンル": new_genre,
                        "監督": new_director,
                        "主要キャスト": new_cast
                    }
                    
                    # Append and save
                    new_df = pd.DataFrame([new_row])
                    df_updated = pd.concat([df, new_df], ignore_index=True)
                    save_data(df_updated)
                    
                    # Clear cache so next load gets new data
                    st.cache_data.clear()
                    
                    st.success(f"「{new_title}」を登録しました！")
                    st.rerun()

if __name__ == "__main__":
    main()
