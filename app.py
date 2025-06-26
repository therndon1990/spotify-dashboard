import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from datetime import datetime
import shutil
from urllib.parse import urlencode
import time

st.set_page_config(layout="wide")

st.title('Spotify Streaming History Dashboard')

PROFILE_DIR = 'Profiles'
if not os.path.exists(PROFILE_DIR):
    os.makedirs(PROFILE_DIR)

# --- Profile Management ---
def list_profiles():
    return [d for d in os.listdir(PROFILE_DIR) if os.path.isdir(os.path.join(PROFILE_DIR, d))]

def save_uploaded_files(profile_name, files):
    profile_path = os.path.join(PROFILE_DIR, profile_name)
    os.makedirs(profile_path, exist_ok=True)
    for file in files:
        file.seek(0)
        with open(os.path.join(profile_path, file.name), 'wb') as out:
            out.write(file.read())

def load_profile_data(profile_name):
    profile_path = os.path.join(PROFILE_DIR, profile_name)
    dfs = []
    for fname in os.listdir(profile_path):
        if fname.endswith('.json'):
            with open(os.path.join(profile_path, fname), 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    df = pd.DataFrame(data)
                    df = clean_and_normalize(df)
                    dfs.append(df)
                except Exception as e:
                    st.error(f"Error loading {fname}: {e}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def get_first_available(row, keys, default=None):
    for key in keys:
        if key in row and pd.notnull(row[key]):
            return row[key]
    return default

def clean_and_normalize(df):
    df = df.copy()
    if 'endTime' in df.columns:
        df['ts'] = pd.to_datetime(df['endTime'], errors='coerce')
    elif 'ts' in df.columns:
        df['ts'] = pd.to_datetime(df['ts'], errors='coerce')
    else:
        df['ts'] = pd.NaT
    df['trackName'] = df.apply(lambda row: get_first_available(row, [
        'trackName', 'master_metadata_track_name', 'track', 'song'
    ], default='Unknown'), axis=1)
    df['artistName'] = df.apply(lambda row: get_first_available(row, [
        'artistName', 'master_metadata_album_artist_name', 'artist'
    ], default='Unknown'), axis=1)
    df['albumName'] = df.apply(lambda row: get_first_available(row, [
        'albumName', 'master_metadata_album_album_name', 'album'
    ], default='Unknown'), axis=1)
    df['msPlayed'] = df.apply(lambda row: get_first_available(row, [
        'msPlayed', 'ms_played'
    ], default=0), axis=1)
    df['year'] = df['ts'].dt.year
    return df

# --- Layout: Left (filters), Center (dashboard), Right (profiles) ---
left, center, right = st.columns([3, 7, 3])

# --- Center Panel: Dashboard ---
df = pd.DataFrame()
selected_profile = None
filters_ready = False

# --- Right Panel: Profile Management ---
with right:
    st.header("Profiles")
    st.write("Manage your Spotify data profiles.")
    profile_mode = st.radio("Choose an option:", ["Create a Profile & Upload New Spotify Data", "Select a Pre-Existing Profile"])
    profiles = list_profiles()
    profile_created = False
    if profile_mode == "Create a Profile & Upload New Spotify Data":
        col_profile = st.columns([3, 1])  # Profile name input is 3x wider than Save button
        with col_profile[0]:
            profile_name = st.text_input("Profile Name", key="create_profile_name", label_visibility="visible", placeholder="Enter profile name", help="Required before uploading files.")
        with col_profile[1]:
            st.markdown("""
            <style>
            div[data-testid=\"stButton\"][data-key=\"save_profile_btn\"] {
                display: flex;
                align-items: center;
                height: 2.5em;
            }
            div[data-testid=\"stButton\"][data-key=\"save_profile_btn\"] button {
                font-size: 1em !important;
                height: 2.5em !important;
                line-height: 2.5em !important;
                min-width: 70px !important;
                width: 100% !important;
                margin-top: 0 !important;
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                vertical-align: middle !important;
                box-sizing: border-box !important;
                white-space: nowrap !important;
            }
            </style>
            """, unsafe_allow_html=True)
            save_clicked = st.button("Save", key="save_profile_btn", use_container_width=True)
        if 'show_upload' not in st.session_state:
            st.session_state['show_upload'] = False
        if save_clicked and profile_name:
            st.markdown('<div style="color: green; font-size: 0.9em; margin-top: 0.2em; margin-bottom: 0.5em;">Saved!</div>', unsafe_allow_html=True)
            # Create the profile folder immediately on save
            profile_path = os.path.join(PROFILE_DIR, profile_name)
            os.makedirs(profile_path, exist_ok=True)
            st.session_state['show_upload'] = True
            st.session_state['created_profile'] = profile_name
        elif save_clicked and not profile_name:
            st.warning("Please provide a profile name before saving.")
        if st.session_state['show_upload'] and profile_name:
            uploaded_files = st.file_uploader(
                "Upload Spotify JSON files",
                type=["json"],
                accept_multiple_files=True,
                key="profile_upload"
            )
            if uploaded_files:
                if st.button("Upload Files & Save to Profile", key="upload_files_btn"):
                    save_uploaded_files(profile_name, uploaded_files)
                    st.success("Files Upload Complete & Save to Profile", icon="✅")
                    st.session_state['created_profile'] = profile_name
                    st.session_state['show_upload'] = False
                    st.session_state['uploaded_files'] = True
                    st.session_state['selected_profile'] = profile_name
        if st.session_state.get('created_profile'):
            selected_profile = st.session_state['created_profile']
    elif profile_mode == "Select a Pre-Existing Profile":
        selected_profile_dropdown = st.selectbox("Choose a profile to load", profiles if profiles else ["No profiles found"], key="profile_select")
        # Button row for Select, Delete, Rename
        button_cols = st.columns(3)
        select_clicked = button_cols[0].button("Select Profile", key="select_profile_btn")
        delete_clicked = button_cols[1].button("Delete Profile", key="delete_profile_btn")
        rename_clicked = button_cols[2].button("Rename Profile", key="rename_profile_btn")
        st.markdown("""
        <style>
        div[data-testid="column"] div[data-testid^="stButton"] button {
            width: 100% !important;
            min-width: 0 !important;
            font-size: 1em !important;
            height: 2.5em !important;
        }
        </style>
        """, unsafe_allow_html=True)
        # Loading/Ready visual
        if 'profile_loading' not in st.session_state:
            st.session_state['profile_loading'] = False
        if 'profile_ready' not in st.session_state:
            st.session_state['profile_ready'] = False
        if 'filters_ready' not in st.session_state:
            st.session_state['filters_ready'] = False
        if select_clicked and selected_profile_dropdown and selected_profile_dropdown != "No profiles found":
            st.session_state['selected_profile'] = selected_profile_dropdown
            st.session_state['profile_loading'] = True
            st.session_state['profile_ready'] = False
            st.session_state['filters_ready'] = False
        if delete_clicked and selected_profile_dropdown and selected_profile_dropdown != "No profiles found":
            try:
                shutil.rmtree(os.path.join(PROFILE_DIR, selected_profile_dropdown))
                st.success(f"Profile '{selected_profile_dropdown}' deleted.")
                st.session_state['profile_ready'] = False
                st.session_state['filters_ready'] = False
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error deleting profile: {e}")
        # Show loading or ready notification in the right panel, never both
        if st.session_state['profile_loading'] and not st.session_state['filters_ready']:
            st.markdown('<div style="margin-top:0.5em; margin-bottom:0.5em;">'
                        '<span style="color:#1976d2;font-size:1.1em;">'
                        '<span class="loader"></span> Loading...'
                        '</span></div>'
                        '<style>@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}'
                        '.loader{display:inline-block;width:1em;height:1em;border:2px solid #1976d2;border-radius:50%;border-top:2px solid #fff;animation:spin 1s linear infinite;margin-right:0.5em;vertical-align:middle;}</style>', unsafe_allow_html=True)
            # Simulate loading delay (remove/comment out in production)
            time.sleep(1.2)
            # Load the profile data here (simulate actual loading)
            # df = load_profile_data(st.session_state['selected_profile'])
            st.session_state['profile_loading'] = False
            st.session_state['profile_ready'] = True
            st.session_state['filters_ready'] = True
        elif st.session_state['filters_ready']:
            st.markdown('<div style="margin-top:0.5em; margin-bottom:0.5em;">'
                        '<span style="color:#388e3c;font-size:1.1em;">Ready!</span></div>', unsafe_allow_html=True)

# --- Center Panel: Dashboard ---
with center:
    st.write("""
    Upload your Spotify StreamingHistory or endsong JSON files to explore your listening data. You can segment by year, artist, album, and song.
    """)
    if not df.empty:
        st.success(f"Loaded {len(df)} records from profile '{selected_profile}'.")
        if 'year_filter' not in st.session_state or st.session_state.get('reset_filters', False):
            st.session_state['year_filter'] = []
        if 'artist_filter' not in st.session_state or st.session_state.get('reset_filters', False):
            st.session_state['artist_filter'] = []
        if 'album_filter' not in st.session_state or st.session_state.get('reset_filters', False):
            st.session_state['album_filter'] = []
        if 'song_filter' not in st.session_state or st.session_state.get('reset_filters', False):
            st.session_state['song_filter'] = []
        if 'apply_filters' not in st.session_state or st.session_state.get('reset_filters', False):
            st.session_state['apply_filters'] = False
        st.session_state['reset_filters'] = False
        if st.session_state['apply_filters']:
            filtered_df = df[df['year'].isin(st.session_state['year_filter'])] if st.session_state['year_filter'] else df
            if st.session_state['artist_filter']:
                filtered_df = filtered_df[filtered_df['artistName'].isin(st.session_state['artist_filter'])]
            if st.session_state['album_filter']:
                filtered_df = filtered_df[filtered_df['albumName'].isin(st.session_state['album_filter'])]
            if st.session_state['song_filter']:
                filtered_df = filtered_df[filtered_df['trackName'].isin(st.session_state['song_filter'])]
            st.dataframe(filtered_df.head(100))
            st.header("Visualizations")
            col1, col2 = st.columns(2)
            with col1:
                top_artists = filtered_df['artistName'].value_counts().head(10)
                fig = px.bar(top_artists, x=top_artists.index, y=top_artists.values, labels={'x':'Artist', 'y':'Play Count'}, title='Top 10 Artists')
                st.plotly_chart(fig)
            with col2:
                top_songs = filtered_df['trackName'].value_counts().head(10)
                fig = px.bar(top_songs, x=top_songs.index, y=top_songs.values, labels={'x':'Song', 'y':'Play Count'}, title='Top 10 Songs')
                st.plotly_chart(fig)
            st.subheader("Listening Trends Over Time")
            trend_df = filtered_df.copy()
            trend_df['date'] = trend_df['ts'].dt.date
            daily_counts = trend_df.groupby('date').size().reset_index(name='plays')
            fig = px.line(daily_counts, x='date', y='plays', title='Listening Activity Over Time')
            st.plotly_chart(fig)
            st.subheader("Top Albums")
            top_albums = filtered_df['albumName'].value_counts().head(10)
            fig = px.bar(top_albums, x=top_albums.index, y=top_albums.values, labels={'x':'Album', 'y':'Play Count'}, title='Top 10 Albums')
            st.plotly_chart(fig)
        else:
            st.info("Select your filter options and click 'Apply Filters' to update the dashboard.")
    elif 'selected_profile' in locals() and selected_profile == "No profiles found":
        st.info("No profiles found. Please upload files and create a profile.")
    else:
        st.info("Please select a profile to load your Spotify data.")

# --- Left Panel: Filters ---
with left:
    st.header("Filters")
    # Only show filters if profile is ready and data is loaded
    if st.session_state.get('filters_ready', False):
        # Remove duplicate Ready! notification in left panel
        years = sorted(df['year'].dropna().unique())
        artists = sorted(df['artistName'].dropna().unique())
        albums = sorted(df['albumName'].dropna().unique())
        songs = sorted(df['trackName'].dropna().unique())

        st.markdown("""
        <style>
        .looker-filter-row { margin-bottom: 0.01em; }
        .looker-filter-label { font-weight: 600; font-size: 1em; margin-right: 0.3em; }
        .looker-link {
            font-size: 0.7em;
            color: #1976d2;
            text-decoration: underline;
            cursor: pointer;
            margin-right: 0.2em;
            margin-bottom: 0.01em;
            background: none;
            border: none;
            padding: 0;
            display: inline;
        }
        .looker-link:hover {
            color: #0d47a1;
        }
        .looker-filter-section {
            margin-bottom: 0.08em;
            padding-bottom: 0.01em;
        }
        </style>
        """, unsafe_allow_html=True)

        def filter_links(filter_key, all_label, none_label, all_values):
            col = st.columns([1, 1])
            with col[0]:
                st.markdown(f'<span class="looker-link" onclick="window.dispatchEvent(new CustomEvent(\'selectAll_{filter_key}\'))">{all_label}</span>', unsafe_allow_html=True)
            with col[1]:
                st.markdown(f'<span class="looker-link" onclick="window.dispatchEvent(new CustomEvent(\'deselectAll_{filter_key}\'))">{none_label}</span>', unsafe_allow_html=True)
            st.markdown(f"""
            <script>
            window.addEventListener('selectAll_{filter_key}', function() {{
                window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setComponentValue', key: '{filter_key}_filter', value: {all_values} }}, '*');
            }});
            window.addEventListener('deselectAll_{filter_key}', function() {{
                window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setComponentValue', key: '{filter_key}_filter', value: [] }}, '*');
            }});
            </script>
            """, unsafe_allow_html=True)

        # Year filter
        with st.container():
            st.markdown('<div class="looker-filter-section">', unsafe_allow_html=True)
            st.markdown('<span class="looker-filter-label">Year</span>', unsafe_allow_html=True)
            filter_links('year', 'Select all', 'Deselect all', years)
            year_filter = st.multiselect(
                "",
                options=years,
                default=st.session_state['year_filter'],
                key='year_filter_widget',
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Artist filter
        with st.container():
            st.markdown('<div class="looker-filter-section">', unsafe_allow_html=True)
            st.markdown('<span class="looker-filter-label">Artist</span>', unsafe_allow_html=True)
            filter_links('artist', 'Select all', 'Deselect all', artists)
            artist_filter = st.multiselect(
                "",
                options=artists,
                default=st.session_state['artist_filter'],
                key='artist_filter_widget',
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Album filter
        with st.container():
            st.markdown('<div class="looker-filter-section">', unsafe_allow_html=True)
            st.markdown('<span class="looker-filter-label">Album</span>', unsafe_allow_html=True)
            filter_links('album', 'Select all', 'Deselect all', albums)
            album_filter = st.multiselect(
                "",
                options=albums,
                default=st.session_state['album_filter'],
                key='album_filter_widget',
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Song filter
        with st.container():
            st.markdown('<div class="looker-filter-section">', unsafe_allow_html=True)
            st.markdown('<span class="looker-filter-label">Song</span>', unsafe_allow_html=True)
            filter_links('song', 'Select all', 'Deselect all', songs)
            song_filter = st.multiselect(
                "",
                options=songs,
                default=st.session_state['song_filter'],
                key='song_filter_widget',
                label_visibility="collapsed"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Apply Filters"):
            st.session_state['year_filter'] = year_filter
            st.session_state['artist_filter'] = artist_filter
            st.session_state['album_filter'] = album_filter
            st.session_state['song_filter'] = song_filter
            st.session_state['apply_filters'] = True
        if st.session_state.get('last_profile', None) != selected_profile:
            st.session_state['reset_filters'] = True
            st.session_state['last_profile'] = selected_profile 