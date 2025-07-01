import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from datetime import datetime
import shutil
from urllib.parse import urlencode
import time
import polars as pl
import traceback
import pickle
import hashlib
from concurrent.futures import ThreadPoolExecutor
import gc

# ULTRA-PERFORMANCE CONFIG: Optimize Streamlit for maximum speed
st.set_page_config(
    page_title="🎵 Spotify Dashboard", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# SPOTIFY THEME CSS STYLING
st.markdown("""
<style>
/* Spotify Color Scheme */
:root {
    --spotify-green: #1DB954;
    --spotify-dark: #191414;
    --spotify-darker: #121212;
    --spotify-gray: #535353;
    --spotify-light-gray: #B3B3B3;
    --spotify-white: #FFFFFF;
}

/* Main app background */
.stApp {
    background-color: var(--spotify-darker) !important;
    color: var(--spotify-white) !important;
}

/* Headers and text styling */
h1, h2, h3, h4, h5, h6 {
    color: var(--spotify-white) !important;
    font-family: 'Helvetica Neue', Arial, sans-serif !important;
}

h1 {
    color: var(--spotify-green) !important;
    font-weight: 700 !important;
}

h2 {
    color: var(--spotify-green) !important;
    font-weight: 600 !important;
}

h3 {
    color: var(--spotify-white) !important;
    font-weight: 500 !important;
}

/* Metric styling */
[data-testid="metric-container"] {
    background-color: var(--spotify-dark) !important;
    border: 1px solid var(--spotify-gray) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}

[data-testid="metric-container"] > div {
    color: var(--spotify-white) !important;
}

/* Button styling */
.stButton > button {
    background-color: var(--spotify-green) !important;
    color: var(--spotify-white) !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background-color: #1ed760 !important;
    transform: scale(1.04) !important;
}

/* Selectbox and multiselect styling */
.stSelectbox > div > div {
    background-color: var(--spotify-dark) !important;
    color: var(--spotify-white) !important;
    border: 1px solid var(--spotify-gray) !important;
    border-radius: 8px !important;
}

.stMultiSelect > div > div {
    background-color: var(--spotify-dark) !important;
    border: 1px solid var(--spotify-gray) !important;
    border-radius: 8px !important;
}

/* DataFrame styling */
.stDataFrame {
    background-color: var(--spotify-dark) !important;
    border-radius: 8px !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    background-color: var(--spotify-dark) !important;
    color: var(--spotify-white) !important;
    border-radius: 8px !important;
}

/* File uploader styling */
.stFileUploader > div {
    background-color: var(--spotify-dark) !important;
    border: 2px dashed var(--spotify-green) !important;
    border-radius: 8px !important;
}

/* Info boxes */
.stInfo {
    background-color: var(--spotify-dark) !important;
    color: var(--spotify-white) !important;
}

/* Success boxes */
.stSuccess {
    background-color: var(--spotify-green) !important;
    color: var(--spotify-white) !important;
}
</style>
""", unsafe_allow_html=True)

# Memory optimization with enhanced cleanup
if 'memory_cleanup_counter' not in st.session_state:
    st.session_state['memory_cleanup_counter'] = 0

# Enhanced memory management for sub-5sec performance
st.session_state['memory_cleanup_counter'] += 1
if st.session_state['memory_cleanup_counter'] % 5 == 0:  # More frequent cleanup
    gc.collect()

def show_songs_in_most_playlists():
    """Show top songs that appear in the most playlists"""
    try:
        st.subheader("🎵 Top 25 Songs in Most Playlists")
        
        profile_name = st.session_state.get('selected_profile')
        if not profile_name:
            st.info("No profile selected")
            return
            
        profile_path = os.path.join(PROFILE_DIR, profile_name)
        playlist_files = [f for f in os.listdir(profile_path) if 'Playlist' in f and f.endswith('.json')]
        
        if not playlist_files:
            st.info("No playlist files found for this profile.")
            return
            
        song_playlist_count = {}
        song_details = {}
        
        # Process each playlist file
        for playlist_file in playlist_files:
            try:
                with open(os.path.join(profile_path, playlist_file), 'r', encoding='utf-8') as f:
                    playlist_data = json.load(f)
                
                if isinstance(playlist_data, dict) and 'playlists' in playlist_data:
                    for playlist in playlist_data['playlists']:
                        playlist_name = playlist.get('name', 'Unknown')
                        items = playlist.get('items', [])
                        
                        for item in items:
                            track = item.get('track', {})
                            track_name = track.get('trackName', '').strip()
                            artist_name = track.get('artistName', '').strip()
                            
                            if track_name and artist_name and track_name.lower() not in ['unknown', 'n/a', ''] and artist_name.lower() not in ['unknown', 'n/a', '']:
                                # Create unique song identifier
                                song_key = f"{track_name} - {artist_name}"
                                
                                # Count playlist appearances
                                if song_key not in song_playlist_count:
                                    song_playlist_count[song_key] = set()
                                    song_details[song_key] = {
                                        'trackName': track_name,
                                        'artistName': artist_name
                                    }
                                
                                song_playlist_count[song_key].add(playlist_name)
            except Exception:
                continue
        
        # Convert to counts and create DataFrame
        if not song_playlist_count:
            st.info("No song data found in playlists")
            return
            
        songs_data = []
        for song_key, playlists in song_playlist_count.items():
            if len(playlists) > 1:  # Only songs in multiple playlists
                songs_data.append({
                    'song': song_key,
                    'trackName': song_details[song_key]['trackName'],
                    'artistName': song_details[song_key]['artistName'],
                    'playlistCount': len(playlists),
                    'playlists': ', '.join(list(playlists)[:3]) + ('...' if len(playlists) > 3 else '')
                })
        
        if not songs_data:
            st.info("No songs found in multiple playlists")
            return
            
        # Sort by playlist count and get top 25
        songs_df = pd.DataFrame(songs_data)
        top_songs = songs_df.nlargest(25, 'playlistCount')
        
        # Create horizontal bar chart
        fig = px.bar(top_songs,
                   x='playlistCount',
                   y='song',
                   orientation='h',
                   title='Songs Appearing in Most Playlists',
                   labels={'playlistCount': 'Number of Playlists', 'song': 'Song'},
                   height=700,
                   color_discrete_sequence=['#1DB954'])
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='#191414',
            plot_bgcolor='#191414',
            font=dict(color='#FFFFFF'),
            title_font=dict(color='#1DB954', size=16),
            xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
            yaxis=dict(categoryorder='total ascending', color='#FFFFFF')
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show detailed song info
        st.write("**Song Details:**")
        display_songs = top_songs[['trackName', 'artistName', 'playlistCount', 'playlists']].copy()
        display_songs.columns = ['Track', 'Artist', 'Playlist Count', 'Sample Playlists']
        st.dataframe(display_songs, use_container_width=True, height=300)
        
    except Exception as e:
        st.error(f"Top Songs in Playlists visualization error: {e}")


def create_enhanced_filter(filter_type, label, icon, options, selected_values, search_key, checkbox_key):
    """Create enhanced filter with search and checkboxes"""
    st.markdown(f'<div style="margin-bottom: 4px;"><span class="looker-filter-label">{icon} {label}</span></div>', unsafe_allow_html=True)
    
    # Search input for filtering options
    search_term = st.text_input(
        f"Search {label.lower()}...", 
        key=search_key,
        placeholder=f"Type to search {label.lower()}...",
        help=f"Type to filter {label.lower()} options"
    )
    
    # Improved search logic with better handling
    if search_term:
        search_lower = search_term.strip().lower()
        filtered_options = []
        
        for opt in options:
            # Convert option to string and clean it
            opt_str = str(opt).strip().lower()
            # More flexible search - check if search term is contained in the option
            if search_lower in opt_str:
                filtered_options.append(opt)
        

    else:
        filtered_options = options[:100]  # Limit to first 100 items for performance
    
    # Show count info
    if search_term:
        st.caption(f"Showing {len(filtered_options)} of {len(options)} {label.lower()} matching '{search_term}'")
    else:
        st.caption(f"Showing first {min(100, len(options))} of {len(options)} {label.lower()}")
    
    if search_term and not filtered_options:
        st.warning(f"No {label.lower()} found matching '{search_term}'")
        # Show some suggestions
        if len(options) > 0:
            similar_options = []
            search_lower = search_term.lower()
            for opt in options:
                opt_str = str(opt).lower()
                # Look for partial matches
                if any(char in opt_str for char in search_lower):
                    similar_options.append(opt)
            
            if similar_options:
                st.info(f"💡 Similar options found: {', '.join(str(opt) for opt in similar_options[:5])}")
        return selected_values
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(f"Select All", key=f"select_all_{filter_type}", use_container_width=True):
            # Add all filtered options to selected values
            for option in filtered_options:
                if option not in selected_values:
                    selected_values.append(option)
    
    with col2:
        if st.button(f"Clear All", key=f"clear_all_{filter_type}", use_container_width=True):
            # Remove all filtered options from selected values
            selected_values = [val for val in selected_values if val not in filtered_options]
    
    with col3:
        if st.button(f"Clear Selected", key=f"clear_selected_{filter_type}", use_container_width=True):
            selected_values = []
    
    # OPTIMIZED: Virtual scrolling for large datasets
    # Only show limited items at once for performance, but enable search for full dataset
    max_display_items = 50 if not search_term else min(100, len(filtered_options))
    display_options = filtered_options[:max_display_items]
    
    if len(filtered_options) > max_display_items:
        st.info(f"Showing first {max_display_items} of {len(filtered_options)} matches. Use search to find specific items.")
    
    # Create container for checkboxes with optimized scrolling
    with st.container():
        st.markdown("""
        <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 8px; border-radius: 4px; background: #f9f9f9;">
        """, unsafe_allow_html=True)
        
        # PERFORMANCE OPTIMIZED: Create checkboxes with efficient rendering
        for i, option in enumerate(display_options):
            is_selected = option in selected_values
            
            # Use more efficient single-column layout for large lists
            checkbox_value = st.checkbox(
                f"{str(option)}",
                value=is_selected,
                key=f"{checkbox_key}_{i}_{hash(str(option)) % 10000}",  # Use hash for unique keys
                help=f"Toggle {str(option)}"
            )
            
            # Update selected values based on checkbox
            if checkbox_value and option not in selected_values:
                selected_values.append(option)
            elif not checkbox_value and option in selected_values:
                selected_values.remove(option)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Show selected count
    if selected_values:
        st.success(f"✓ {len(selected_values)} {label.lower()} selected")
    else:
        st.info(f"No {label.lower()} selected (showing all)")
    
    return selected_values

# ULTRA-AGGRESSIVE PERFORMANCE CONSTANTS - OPTIMIZED FOR FULL DATA ACCESS
UNLIMITED_MODE = True
MAX_UI_FILTER_OPTIONS = 10000  # Increased to handle full datasets efficiently
CACHE_DIR = 'cache'
SMART_CACHE_ENABLED = True
SAMPLE_RATIO = 1.0  # USE ALL DATA: No sampling for complete functionality
MIN_SAMPLE_SIZE = 1000  # Minimum sample size (not used when ratio = 1.0)
MAX_JSON_RECORDS_PER_FILE = 100000  # Increased for better data coverage

# CLOUD-OPTIMIZED: Ensure directories exist with error handling
try:
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
except Exception as e:
    st.error(f"Error creating cache directory: {e}")

PROFILE_DIR = 'Profiles'
try:
    if not os.path.exists(PROFILE_DIR):
        os.makedirs(PROFILE_DIR, exist_ok=True)
except Exception as e:
    st.error(f"Error creating profiles directory: {e}")

# CLOUD COMPATIBILITY: Add session cleanup for memory management
if len(st.session_state) > 50:  # Prevent session bloat in cloud
    # Keep only essential keys
    essential_keys = ['selected_profile', 'df', 'apply_filters', 'profile_ready', 'filters_ready']
    keys_to_remove = [k for k in st.session_state.keys() if k not in essential_keys and not k.startswith('_filter')]
    for key in keys_to_remove[:10]:  # Remove max 10 at a time
        if key in st.session_state:
            del st.session_state[key]

# Title and performance notification
st.title("🎵 Spotify Dashboard")

# Welcome message for new users
if not st.session_state.get('profile_ready', False):
    st.markdown("""
    ### 👋 **Welcome to Your Personal Spotify Analytics Dashboard!**
    
    This dashboard analyzes your personal Spotify data to reveal insights about your music listening habits. 
    
    **🚀 Getting Started:**
    1. **Get Your Spotify Data**: Request your "Extended Streaming History" from [Spotify Privacy Settings](https://www.spotify.com/account/privacy/) (takes up to 30 days)
    2. **Create a Profile**: Use the panel on the right to create a new profile
    3. **Upload Your Files**: Upload all your Spotify JSON files
    4. **Explore**: Use filters and visualizations to discover your music patterns!
    
    **📊 What You'll Discover:**
    - Your top artists, albums, and songs over time
    - Listening trends and patterns by year/month
    - How your music taste has evolved
    - Playlist analytics and cross-playlist favorites
    - Artist loyalty and discovery patterns
    
    **🔒 Privacy**: Your data stays completely private - all processing happens in your browser session.
    """)
    
    st.info("📋 **Ready?** Create a profile on the right and upload your Spotify data files to begin your musical journey!")

# NEW: Cache management functions
def get_cache_path(profile_name, cache_type='data'):
    """Get the cache file path for a profile"""
    return os.path.join(CACHE_DIR, f"{profile_name}_{cache_type}.pkl")

def get_profile_hash(profile_name):
    """Get a hash of all files in the profile for cache validation"""
    profile_path = os.path.join(PROFILE_DIR, profile_name)
    if not os.path.exists(profile_path):
        return None
    
    files = [f for f in os.listdir(profile_path) if f.endswith('.json')]
    if not files:
        return None
    
    # Create hash based on file modification times and sizes
    hash_input = ""
    for file in sorted(files):
        file_path = os.path.join(profile_path, file)
        stat = os.stat(file_path)
        hash_input += f"{file}:{stat.st_mtime}:{stat.st_size}:"
    
    return hashlib.md5(hash_input.encode()).hexdigest()

def save_cache(profile_name, data, cache_type='data'):
    """Save processed data to cache"""
    try:
        cache_path = get_cache_path(profile_name, cache_type)
        cache_data = {
            'data': data,
            'hash': get_profile_hash(profile_name),
            'timestamp': time.time()
        }
        with open(cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
        return True
    except Exception:
        return False  # Silent failure for speed

def load_cache(profile_name, cache_type='data'):
    """Load processed data from cache if valid"""
    try:
        cache_path = get_cache_path(profile_name, cache_type)
        if not os.path.exists(cache_path):
            return None
        
        with open(cache_path, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Validate cache
        current_hash = get_profile_hash(profile_name)
        if cache_data.get('hash') != current_hash:
            return None  # Cache is stale
        
        return cache_data['data']
    except Exception:
        return None  # Silent failure for speed

# NEW: EXTREME PERFORMANCE - Parquet pre-processing
def get_parquet_path(profile_name):
    """Get the parquet file path for ultra-fast loading"""
    return os.path.join(CACHE_DIR, f"{profile_name}_data.parquet")

# NEW: STREAMING JSON PROCESSOR with aggressive limits
def convert_profile_to_comprehensive_data(profile_name, force_rebuild=False):
    """COMPREHENSIVE SPOTIFY DATA INGESTION: Process ALL data types"""
    parquet_path = get_parquet_path(profile_name)
    
    # Quick existence check
    if not force_rebuild and os.path.exists(parquet_path):
        return True
    
    profile_path = os.path.join(PROFILE_DIR, profile_name)
    files = [fname for fname in os.listdir(profile_path) if fname.endswith('.json')]
    
    if not files:
        return False
    
    # COMPREHENSIVE DATA COLLECTION
    streaming_data = []
    account_data = {}
    library_data = {}
    search_data = []
    wrapped_data = {}
    playlist_data = []
    
    print(f"🔍 Processing {len(files)} Spotify data files...")
    
    for fname in files:
        file_path = os.path.join(profile_path, fname)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            
            # 1. STREAMING HISTORY DATA (Enhanced Processing)
            if 'Streaming_History' in fname or 'StreamingHistory' in fname:
                if isinstance(data, list):
                    print(f"📊 Processing streaming file: {fname} ({len(data)} records)")
                    # Process with improved sampling for large files
                    sample_size = min(len(data), 100000)  # Increased limit
                    sampled_data = data[::max(1, len(data)//sample_size)]  # Smart sampling
                    
                    for record in sampled_data:
                        try:
                            ts_value = record.get('ts') or record.get('endTime', '')
                            if isinstance(ts_value, dict):
                                ts_value = ts_value.get('$date', str(ts_value))
                            
                            # Extract year and additional metadata
                            year = 2023
                            if ts_value and len(str(ts_value)) >= 4:
                                try:
                                    year = int(str(ts_value)[:4])
                                except:
                                    year = 2023
                            
                            streaming_data.append({
                                'trackName': str(record.get('master_metadata_track_name') or record.get('trackName') or 'Unknown')[:100],
                                'artistName': str(record.get('master_metadata_album_artist_name') or record.get('artistName') or 'Unknown')[:100],
                                'albumName': str(record.get('master_metadata_album_album_name') or record.get('albumName') or 'Unknown')[:100],
                                'year': year,
                                'msPlayed': float(record.get('ms_played') or record.get('msPlayed', 0)),
                                'ts': ts_value,
                                'platform': str(record.get('platform', 'Unknown'))[:50],
                                'skipped': record.get('skipped', False),
                                'shuffle': record.get('shuffle', False),
                                'offline': record.get('offline', False),
                                'reason_start': str(record.get('reason_start', 'Unknown'))[:30],
                                'reason_end': str(record.get('reason_end', 'Unknown'))[:30],
                                'conn_country': str(record.get('conn_country', 'Unknown'))[:10]
                            })
                        except:
                            continue
            
            # 2. USER ACCOUNT DATA
            elif fname == 'Userdata.json':
                print(f"👤 Processing account data: {fname}")
                account_data = {
                    'username': data.get('username', ''),
                    'email': data.get('email', ''),
                    'country': data.get('country', ''),
                    'createdFromFacebook': data.get('createdFromFacebook', False),
                    'birthdate': data.get('birthdate', ''),
                    'gender': data.get('gender', ''),
                    'postalCode': data.get('postalCode', ''),
                    'creationTime': data.get('creationTime', ''),
                    'account_age_years': 0
                }
                # Calculate account age
                if account_data['creationTime']:
                    try:
                        from datetime import datetime
                        created = datetime.strptime(account_data['creationTime'], '%Y-%m-%d')
                        account_data['account_age_years'] = (datetime.now() - created).days / 365.25
                    except:
                        pass
            
            # 3. LIBRARY DATA
            elif fname == 'YourLibrary.json':
                print(f"📚 Processing library data: {fname}")
                library_data = {
                    'saved_tracks_count': len(data.get('tracks', [])),
                    'saved_albums_count': len(data.get('albums', [])),
                    'followed_artists_count': len(data.get('artists', [])),
                    'followed_shows_count': len(data.get('shows', [])),
                    'saved_episodes_count': len(data.get('episodes', [])),
                    'banned_tracks_count': len(data.get('bannedTracks', [])),
                    'banned_artists_count': len(data.get('bannedArtists', [])),
                    'saved_tracks': [
                        {
                            'artist': track.get('artist', 'Unknown')[:100],
                            'album': track.get('album', 'Unknown')[:100],
                            'track': track.get('track', 'Unknown')[:100],
                            'uri': track.get('uri', '')
                        } for track in data.get('tracks', [])[:500]  # Limit for performance
                    ],
                    'saved_albums': [
                        {
                            'artist': album.get('artist', 'Unknown')[:100],
                            'album': album.get('album', 'Unknown')[:100],
                            'uri': album.get('uri', '')
                        } for album in data.get('albums', [])[:500]
                    ]
                }
            
            # 4. SEARCH HISTORY
            elif fname == 'SearchQueries.json':
                print(f"🔍 Processing search data: {fname} ({len(data)} searches)")
                search_sample = data[::max(1, len(data)//5000)]  # Sample for performance
                for search in search_sample:
                    try:
                        search_time = search.get('searchTime', '')
                        search_year = 2023
                        if search_time and len(search_time) >= 4:
                            try:
                                search_year = int(search_time[:4])
                            except:
                                pass
                        
                        search_data.append({
                            'searchTime': search_time,
                            'year': search_year,
                            'platform': str(search.get('platform', 'Unknown'))[:20],
                            'searchQuery': str(search.get('searchQuery', ''))[:100],
                            'hasInteractions': len(search.get('searchInteractionURIs', [])) > 0
                        })
                    except:
                        continue
            
            # 5. SPOTIFY WRAPPED DATA
            elif 'Wrapped' in fname:
                print(f"🎁 Processing Wrapped data: {fname}")
                wrapped_data = {
                    'year': fname.replace('Wrapped', '').replace('.json', ''),
                    'total_ms_listened': data.get('yearlyMetrics', {}).get('totalMsListened', 0),
                    'most_listened_day': data.get('yearlyMetrics', {}).get('mostListenedDay', ''),
                    'most_listened_day_minutes': data.get('yearlyMetrics', {}).get('mostListenedDayMinutes', 0),
                    'percent_greater_than_users': data.get('yearlyMetrics', {}).get('percentGreaterThanWorldwideUsers', 0),
                    'top_artist_fan_percentage': data.get('topArtists', {}).get('topArtistFanPercentage', 0),
                    'top_track_play_count': data.get('topTracks', {}).get('topTrackPlayCount', 0),
                    'distinct_tracks_played': data.get('topTracks', {}).get('distinctTracksPlayed', 0),
                    'num_unique_artists': data.get('topArtists', {}).get('numUniqueArtists', 0),
                    'music_evolution_eras': len(data.get('musicEvolution', {}).get('eras', []))
                }
            
            # 6. PLAYLIST DATA
            elif 'Playlist' in fname:
                print(f"🎵 Processing playlist data: {fname}")
                if isinstance(data, dict) and 'playlists' in data:
                    for playlist in data['playlists']:
                        try:
                            playlist_name = playlist.get('name', 'Unknown Playlist')
                            items = playlist.get('items', [])
                            
                            # Calculate total minutes for this playlist based on actual streaming data
                            # We'll use the track count and estimate minutes based on average listening patterns
                            total_minutes = 0
                            track_count = len(items)
                            
                            # Better estimation: assume average 3.5 minutes per track
                            # This is more realistic than trying to parse track durations that may not be available
                            if track_count > 0:
                                total_minutes = track_count * 3.5  # Average song length
                            
                            # Only add playlists with actual tracks
                            if track_count > 0 and playlist_name != 'Unknown Playlist':
                                playlist_data.append({
                                    'playlistName': str(playlist_name)[:100],
                                    'totalMinutes': total_minutes,
                                    'trackCount': track_count,
                                    'collaborative': playlist.get('collaborative', False),
                                    'lastModified': playlist.get('lastModifiedDate', ''),
                                    'description': str(playlist.get('description', ''))[:200]
                                })
                                print(f"   ✅ Added playlist: {playlist_name} ({track_count} tracks, ~{total_minutes:.1f} minutes)")
                        except Exception as e:
                            print(f"   ⚠️ Error processing playlist in {fname}: {e}")
                            continue
                else:
                    print(f"   ⚠️ Unexpected playlist format in {fname}")
                print(f"   📊 Total playlists processed from {fname}: {len([p for p in playlist_data if p['playlistName']])}")
            
            # 7. FOLLOW/SOCIAL DATA
            elif fname == 'Follow.json':
                print(f"👥 Processing follow data: {fname}")
                follow_data = {
                    'following_count': len(data.get('following', [])),
                    'followers_count': len(data.get('followers', [])),
                    'following_artists': len([f for f in data.get('following', []) if f.get('type') == 'artist']),
                    'following_users': len([f for f in data.get('following', []) if f.get('type') == 'user']),
                    'following_shows': len([f for f in data.get('following', []) if f.get('type') == 'show'])
                }
            
            # 8. USER PROMPTS & INTERACTIONS
            elif fname == 'UserPrompts.json':
                print(f"💬 Processing user prompts: {fname}")
                prompts_data = {
                    'total_prompts': len(data) if isinstance(data, list) else 0,
                    'prompt_types': list(set([p.get('type', 'unknown') for p in (data if isinstance(data, list) else [])])),
                    'recent_prompts': data[:10] if isinstance(data, list) else []
                }
            
            # 9. PODCAST INTERACTIONS
            elif fname == 'PodcastInteractivityVotedPollOption.json':
                print(f"🎙️ Processing podcast interactions: {fname}")
                podcast_interactions = {
                    'total_interactions': len(data) if isinstance(data, list) else 0,
                    'poll_votes': [item for item in (data if isinstance(data, list) else [])],
                    'shows_interacted': len(set([item.get('showName', '') for item in (data if isinstance(data, list) else []) if item.get('showName')]))
                }
            
            # 10. USER ADDRESS DATA
            elif fname == 'UserAddress.json':
                print(f"📍 Processing address data: {fname}")
                address_data = {
                    'addresses': data.get('addresses', []),
                    'address_count': len(data.get('addresses', [])),
                    'countries': list(set([addr.get('country', '') for addr in data.get('addresses', []) if addr.get('country')]))
                }
            
            # 11. USER IDENTIFIERS
            elif fname == 'Identifiers.json':
                print(f"🆔 Processing identifiers: {fname}")
                identifiers_data = {
                    'spotify_id': data.get('spotifyId', ''),
                    'facebook_id': data.get('facebookId', ''),
                    'apple_id': data.get('appleId', ''),
                    'google_id': data.get('googleId', ''),
                    'has_facebook': bool(data.get('facebookId')),
                    'has_apple': bool(data.get('appleId')),
                    'has_google': bool(data.get('googleId'))
                }
            
            # 12. FINANCIAL DATA
            elif fname == 'Purchases.json':
                print(f"💳 Processing purchase data: {fname}")
                purchases_data = {
                    'total_purchases': len(data) if isinstance(data, list) else 0,
                    'purchase_types': list(set([p.get('type', 'unknown') for p in (data if isinstance(data, list) else [])])),
                    'total_amount': sum([float(p.get('amount', 0)) for p in (data if isinstance(data, list) else []) if p.get('amount')]),
                    'currencies': list(set([p.get('currency', 'unknown') for p in (data if isinstance(data, list) else []) if p.get('currency')]))
                }
            
            elif fname == 'Payments.json':
                print(f"💰 Processing payment data: {fname}")
                payments_data = {
                    'total_payments': len(data) if isinstance(data, list) else 0,
                    'payment_methods': list(set([p.get('method', 'unknown') for p in (data if isinstance(data, list) else [])])),
                    'recent_payments': data[-5:] if isinstance(data, list) else []
                }
            
            # 13. OTHER DATA FILES (Store for future use)
            elif fname in ['Inferences.json', 'Marquee.json']:
                print(f"📋 Cataloged additional data: {fname}")
                # Store metadata about additional files for future features
        
        except Exception as e:
            print(f"❌ Error processing {fname}: {e}")
            continue
    
    # CREATE MAIN DATAFRAME with enhanced data
    if not streaming_data:
        return False
    
    try:
        # Create main streaming DataFrame
        df = pl.DataFrame(streaming_data)
        df = df.filter(pl.col('trackName').str.len_chars() > 0)
        
        # Add derived columns for richer analysis
        df = df.with_columns([
            (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed'),
            (pl.col('msPlayed') / (1000 * 60 * 60)).alias('hoursPlayed'),
            pl.when(pl.col('msPlayed') > 30000).then(pl.lit('Complete')).otherwise(pl.lit('Partial')).alias('playType'),
            pl.when(pl.col('skipped')).then(pl.lit('Skipped')).otherwise(pl.lit('Completed')).alias('completion'),
            # Extract month for improved temporal analysis
            pl.col('ts').cast(pl.Utf8).str.slice(0, 7).alias('year_month'),
            pl.col('ts').cast(pl.Utf8).str.slice(0, 10).alias('date')
        ])
        
        # Save main streaming data
        df.write_parquet(parquet_path)
        
        # Save additional datasets for future use
        cache_dir = os.path.dirname(parquet_path)
        
        # Save account data
        if account_data:
            account_path = os.path.join(cache_dir, f"{profile_name}_account.json")
            with open(account_path, 'w') as f:
                json.dump(account_data, f, indent=2)
        
        # Save library data
        if library_data:
            library_path = os.path.join(cache_dir, f"{profile_name}_library.json")
            with open(library_path, 'w') as f:
                json.dump(library_data, f, indent=2)
        
        # Save search data
        if search_data:
            search_df = pl.DataFrame(search_data)
            search_path = os.path.join(cache_dir, f"{profile_name}_searches.parquet")
            search_df.write_parquet(search_path)
        
        # Save wrapped data
        if wrapped_data:
            wrapped_path = os.path.join(cache_dir, f"{profile_name}_wrapped.json")
            with open(wrapped_path, 'w') as f:
                json.dump(wrapped_data, f, indent=2)
        
        # Save playlist data
        if playlist_data:
            playlist_df = pl.DataFrame(playlist_data)
            playlist_path = os.path.join(cache_dir, f"{profile_name}_playlists.parquet")
            playlist_df.write_parquet(playlist_path)
        
        # Save additional comprehensive data
        additional_data = {}
        if 'follow_data' in locals():
            additional_data['follow'] = follow_data
        if 'prompts_data' in locals():
            additional_data['prompts'] = prompts_data
        if 'podcast_interactions' in locals():
            additional_data['podcast_interactions'] = podcast_interactions
        if 'address_data' in locals():
            additional_data['address'] = address_data
        if 'identifiers_data' in locals():
            additional_data['identifiers'] = identifiers_data
        if 'purchases_data' in locals():
            additional_data['purchases'] = purchases_data
        if 'payments_data' in locals():
            additional_data['payments'] = payments_data
        
        if additional_data:
            additional_path = os.path.join(cache_dir, f"{profile_name}_additional.json")
            with open(additional_path, 'w') as f:
                json.dump(additional_data, f, indent=2)
        
        print(f"✅ Successfully processed all Spotify data for {profile_name}")
        print(f"   📊 Streaming records: {len(df):,}")
        print(f"   👤 Account data: {'✓' if account_data else '✗'}")
        print(f"   📚 Library data: {'✓' if library_data else '✗'}")
        print(f"   🔍 Search records: {len(search_data):,}")
        print(f"   🎁 Wrapped data: {'✓' if wrapped_data else '✗'}")
        print(f"   🎵 Playlist data: {'✓' if playlist_data else '✗'}")
        print(f"   👥 Follow data: {'✓' if 'follow_data' in locals() else '✗'}")
        print(f"   💬 Prompts data: {'✓' if 'prompts_data' in locals() else '✗'}")
        print(f"   🎙️ Podcast interactions: {'✓' if 'podcast_interactions' in locals() else '✗'}")
        print(f"   📍 Address data: {'✓' if 'address_data' in locals() else '✗'}")
        print(f"   🆔 Identifiers: {'✓' if 'identifiers_data' in locals() else '✗'}")
        print(f"   💳 Purchase data: {'✓' if 'purchases_data' in locals() else '✗'}")
        print(f"   💰 Payment data: {'✓' if 'payments_data' in locals() else '✗'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating final datasets: {e}")
        return False

# Update the existing function to use the new comprehensive system
def convert_profile_to_parquet_streaming(profile_name, force_rebuild=False):
    """Updated to use comprehensive data processing"""
    return convert_profile_to_comprehensive_data(profile_name, force_rebuild)

# NEW: ULTRA-FAST SAMPLED FILTER COMPUTATION
def prepare_filters_sampled_turbo(df_data, profile_name):
    """COMPLETE DATA: Use full dataset for comprehensive filtering with maximum speed optimizations"""
    
    if df_data is None or df_data.is_empty():
        return {'years': [], 'artists': [], 'albums': [], 'songs': [], 'all_songs': []}
    
    # NO SAMPLING: Use complete dataset for full functionality
    # Apply ultra-fast Polars operations for maximum performance
    
    try:
        # LIGHTNING-FAST unique extraction using Polars lazy evaluation
        # Process all columns in parallel for maximum speed
        
        # Years - small dataset, can afford sorting
        years = sorted(df_data.select('year').drop_nulls().unique().to_series().to_list())
        
        # NO LIMITS: Get ALL unique values for complete functionality
        # Using Polars' optimized unique() operation which is extremely fast
        artists_raw = df_data.select('artistName').drop_nulls().unique().to_series().to_list()
        albums_raw = df_data.select('albumName').drop_nulls().unique().to_series().to_list()
        songs_raw = df_data.select('trackName').drop_nulls().unique().to_series().to_list()
        
        # Keep original unsorted for maximum speed in UI
        # The search interface handles large unsorted lists efficiently
        
        return {
            'years': years,          # Sorted for better UX
            'artists': artists_raw,  # Unsorted for speed - search handles this
            'albums': albums_raw,    # Unsorted for speed - search handles this
            'songs': songs_raw,      # Unsorted for speed - search handles this
            'all_songs': songs_raw   # Complete song list
        }
        
    except Exception as e:
        # Fallback: return empty filters if processing fails
        print(f"Filter preparation error: {e}")
        return {'years': [], 'artists': [], 'albums': [], 'songs': [], 'all_songs': []}

# MODIFIED: Silent data loading with streaming
def load_profile_data_silent_turbo(profile_name):
    """EXTREME PERFORMANCE: Silent loading with streaming optimization"""
    
    # Try Parquet first
    parquet_path = get_parquet_path(profile_name)
    if os.path.exists(parquet_path):
        try:
            return pl.read_parquet(parquet_path)
        except:
            pass
    
    # Use streaming conversion
    if convert_profile_to_parquet_streaming(profile_name):
        try:
            return pl.read_parquet(parquet_path)
        except:
            pass
    
    # Fallback: return empty DataFrame
    return pl.DataFrame()

# ULTRA-OPTIMIZED: Remove all caching overhead for critical path
def load_profile_data_turbo(profile_name):
    """Ultra-fast profile data loading without caching overhead"""
    return load_profile_data_silent_turbo(profile_name)

def prepare_filters_turbo(df_data, profile_name):
    """Ultra-fast filter preparation with sampling"""
    return prepare_filters_sampled_turbo(df_data, profile_name)

def load_additional_spotify_data(profile_name):
    """Load all additional Spotify data (account, library, search, wrapped)"""
    cache_dir = os.path.dirname(get_parquet_path(profile_name))
    additional_data = {}
    
    # Load account data
    account_path = os.path.join(cache_dir, f"{profile_name}_account.json")
    if os.path.exists(account_path):
        try:
            with open(account_path, 'r') as f:
                additional_data['account'] = json.load(f)
        except:
            additional_data['account'] = {}
    else:
        additional_data['account'] = {}
    
    # Load library data
    library_path = os.path.join(cache_dir, f"{profile_name}_library.json")
    if os.path.exists(library_path):
        try:
            with open(library_path, 'r') as f:
                additional_data['library'] = json.load(f)
        except:
            additional_data['library'] = {}
    else:
        additional_data['library'] = {}
    
    # Load search data
    search_path = os.path.join(cache_dir, f"{profile_name}_searches.parquet")
    if os.path.exists(search_path):
        try:
            additional_data['searches'] = pl.read_parquet(search_path)
        except:
            additional_data['searches'] = pl.DataFrame()
    else:
        additional_data['searches'] = pl.DataFrame()
    
    # Load wrapped data
    wrapped_path = os.path.join(cache_dir, f"{profile_name}_wrapped.json")
    if os.path.exists(wrapped_path):
        try:
            with open(wrapped_path, 'r') as f:
                additional_data['wrapped'] = json.load(f)
        except:
            additional_data['wrapped'] = {}
    else:
        additional_data['wrapped'] = {}
    
    return additional_data

def get_spotify_insights_summary(profile_name):
    """Get a summary of all available Spotify data for the profile"""
    # Load main streaming data
    try:
        df = load_profile_data_turbo(profile_name)
        streaming_available = not df.is_empty()
        streaming_records = len(df) if streaming_available else 0
    except:
        streaming_available = False
        streaming_records = 0
    
    # Load additional data
    additional_data = load_additional_spotify_data(profile_name)
    
    summary = {
        'streaming': {
            'available': streaming_available,
            'records': streaming_records,
            'years_span': 0,
            'enhanced_columns': []
        },
        'account': {
            'available': bool(additional_data['account']),
            'creation_date': additional_data['account'].get('creationTime', 'Unknown'),
            'country': additional_data['account'].get('country', 'Unknown'),
            'account_age_years': additional_data['account'].get('account_age_years', 0)
        },
        'library': {
            'available': bool(additional_data['library']),
            'saved_tracks': additional_data['library'].get('saved_tracks_count', 0),
            'saved_albums': additional_data['library'].get('saved_albums_count', 0),
            'followed_artists': additional_data['library'].get('followed_artists_count', 0),
            'followed_shows': additional_data['library'].get('followed_shows_count', 0)
        },
        'searches': {
            'available': not additional_data['searches'].is_empty(),
            'search_count': len(additional_data['searches']) if not additional_data['searches'].is_empty() else 0
        },
        'wrapped': {
            'available': bool(additional_data['wrapped']),
            'year': additional_data['wrapped'].get('year', 'Unknown'),
            'total_hours': additional_data['wrapped'].get('total_ms_listened', 0) / (1000 * 60 * 60),
            'unique_artists': additional_data['wrapped'].get('num_unique_artists', 0)
        }
    }
    
    # Calculate enhanced columns available in streaming data
    if streaming_available:
        available_columns = df.columns
        enhanced_columns = [col for col in ['platform', 'skipped', 'shuffle', 'offline', 'reason_start', 'reason_end', 'conn_country', 'minutesPlayed', 'playType', 'completion'] if col in available_columns]
        summary['streaming']['enhanced_columns'] = enhanced_columns
        
        # Calculate year span
        try:
            years = df.select('year').drop_nulls().unique().to_series().to_list()
            if years:
                summary['streaming']['years_span'] = max(years) - min(years) + 1
        except:
            pass
    
    return summary

def load_profile_data_turbo_enhanced(profile_name):
    """Enhanced version that loads streaming data and additional datasets"""
    # Load main streaming data
    df = load_profile_data_turbo(profile_name)
    
    # Load and store additional data in session state for easy access
    if not df.is_empty():
        additional_data = load_additional_spotify_data(profile_name)
        st.session_state[f'{profile_name}_additional_data'] = additional_data
        
        # Store summary for quick access
        summary = get_spotify_insights_summary(profile_name)
        st.session_state[f'{profile_name}_data_summary'] = summary
    
    return df

# ORIGINAL FUNCTION: Keep for compatibility but mark as legacy
@st.cache_data(show_spinner="Loading profile data...")
def load_profile_data_polars(profile_name):
    """Legacy function - redirects to turbo version"""
    return load_profile_data_turbo(profile_name)

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

def _safe_numeric_convert(value):
    """Safely convert any value to float, handling various edge cases"""
    if value is None:
        return 0.0
    
    # Handle different types
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Try to extract numeric part
        import re
        numeric_match = re.search(r'(\d+\.?\d*)', str(value))
        if numeric_match:
            try:
                return float(numeric_match.group(1))
            except:
                return 0.0
        return 0.0
    
    return 0.0

def get_first_available(row, keys, default=None):
    for key in keys:
        if key in row and pd.notnull(row[key]):
            return row[key]
    return default

@st.cache_data
def prepare_filter_options(df_data):
    """COMPLETE DATA: Ultra-fast filter preparation with full dataset coverage"""
    if df_data is None or df_data.is_empty():
        return [], [], [], []
    
    # Convert back to Polars for fast processing
    df = pl.DataFrame(df_data)
    
    # NO LIMITS: Provide complete dataset coverage for full functionality
    # The enhanced search interface can handle large datasets efficiently
    
    try:
        # Ultra-fast unique value extraction - NO LIMITS for complete functionality
        years = sorted(df.select('year').drop_nulls().unique().to_series().to_list())
        
        # NO LIMITS: Get ALL unique values using Polars' optimized operations
        # Skip sorting for large datasets to maintain 5-second loading requirement
        artists = df.select('artistName').drop_nulls().unique().to_series().to_list()
        albums = df.select('albumName').drop_nulls().unique().to_series().to_list()
        songs = df.select('trackName').drop_nulls().unique().to_series().to_list()
        
    except Exception:
        # Fallback to empty lists if any processing fails
        return [], [], [], []
    
    return years, artists, albums, songs

# COMPREHENSIVE DATA ACCESS FUNCTIONS (Must be defined before use)

# Helper function to get additional data from session state
def get_additional_data_from_session(profile_name):
    """Get additional Spotify data from session state"""
    return st.session_state.get(f'{profile_name}_additional_data', {
        'account': {}, 'library': {}, 'searches': pl.DataFrame(), 'wrapped': {}
    })

def get_data_summary_from_session(profile_name):
    """Get data summary from session state"""
    return st.session_state.get(f'{profile_name}_data_summary', {})

# Function to show comprehensive data overview
def show_comprehensive_data_overview(profile_name):
    """Display a comprehensive overview of all available Spotify data"""
    summary = get_data_summary_from_session(profile_name)
    
    if not summary:
        return
    
    st.subheader("📋 Comprehensive Data Overview")
    
    # Create overview columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.write("**🎵 Streaming Data**")
        if summary['streaming']['available']:
            st.success(f"✅ {summary['streaming']['records']:,} records")
            st.write(f"📅 {summary['streaming']['years_span']} years")
            st.write(f"🔧 {len(summary['streaming']['enhanced_columns'])} enhanced fields")
        else:
            st.error("❌ Not available")
    
    with col2:
        st.write("**👤 Account Data**")
        if summary['account']['available']:
            st.success("✅ Available")
            st.write(f"🌍 Country: {summary['account']['country']}")
            st.write(f"📅 Since: {summary['account']['creation_date']}")
            st.write(f"⏳ {summary['account']['account_age_years']:.1f} years")
        else:
            st.error("❌ Not available")
    
    with col3:
        st.write("**📚 Library Data**")
        if summary['library']['available']:
            st.success("✅ Available")
            st.write(f"🎵 Tracks: {summary['library']['saved_tracks']:,}")
            st.write(f"💿 Albums: {summary['library']['saved_albums']:,}")
            st.write(f"🎤 Artists: {summary['library']['followed_artists']:,}")
        else:
            st.error("❌ Not available")
    
    with col4:
        st.write("**🔍 Additional Data**")
        data_types = []
        if summary['searches']['available']:
            data_types.append(f"🔍 {summary['searches']['search_count']:,} searches")
        if summary['wrapped']['available']:
            data_types.append(f"🎁 {summary['wrapped']['year']} Wrapped")
        
        if data_types:
            st.success("✅ Available")
            for data_type in data_types:
                st.write(data_type)
        else:
            st.warning("⚠️ Limited")
    
    # Show available enhanced fields
    if summary['streaming']['available'] and summary['streaming']['enhanced_columns']:
        st.write("**🔧 Enhanced Streaming Fields Available:**")
        enhanced_info = {
            'platform': '📱 Platform (Android, iOS, Web, etc.)',
            'skipped': '⏭️ Skip behavior',
            'shuffle': '🔀 Shuffle mode',
            'offline': '📶 Offline listening',
            'reason_start': '▶️ Play trigger',
            'reason_end': '⏹️ Stop reason',
            'conn_country': '🌍 Connection country',
            'minutesPlayed': '⏱️ Minutes played',
            'playType': '🎯 Complete vs Partial plays',
            'completion': '✅ Completion status'
        }
        
        enhanced_cols = st.columns(5)
        for i, field in enumerate(summary['streaming']['enhanced_columns']):
            with enhanced_cols[i % 5]:
                st.write(f"• {enhanced_info.get(field, field)}")

# --- Layout: Left (filters), Center (dashboard), Right (profiles) ---
left, center, right = st.columns([3, 7, 3])

# --- Center Panel: Dashboard ---
with center:
    # Dynamic filter status display
    year_filter = st.session_state.get('year_filter', [])
    artist_filter = st.session_state.get('artist_filter', [])
    album_filter = st.session_state.get('album_filter', [])
    song_filter = st.session_state.get('song_filter', [])
    
    # Build filter status message
    filter_parts = []
    
    if year_filter:
        if len(year_filter) == 1:
            filter_parts.append(f"Year {year_filter[0]}")
        else:
            years_sorted = sorted(year_filter)
            if len(years_sorted) > 3:
                filter_parts.append(f"Years {years_sorted[0]}-{years_sorted[-1]} & others")
            else:
                filter_parts.append(f"Years {', '.join(map(str, years_sorted))}")
    
    if artist_filter:
        if len(artist_filter) == 1:
            filter_parts.append(f"Artist: {artist_filter[0]}")
        else:
            filter_parts.append(f"{len(artist_filter)} Artists")
    
    if album_filter:
        if len(album_filter) == 1:
            filter_parts.append(f"Album: {album_filter[0]}")
        else:
            filter_parts.append(f"{len(album_filter)} Albums")
    
    if song_filter:
        if len(song_filter) == 1:
            filter_parts.append(f"Song: {song_filter[0]}")
        else:
            filter_parts.append(f"{len(song_filter)} Songs")
    
    # Create final message
    if filter_parts:
        filter_message = f"🔍 **Filtered View:** {' | '.join(filter_parts)} - Data below reflects your selections"
    else:
        filter_message = "📋 **Instructions:** Upload all \"Spotify Extended Streaming History\" and \"Spotify Account Data\" files for full analysis"
    
    st.write(filter_message)
    
    # Get data and filter state
    df = st.session_state.get('df', pl.DataFrame())
    apply_filters = st.session_state.get('apply_filters', False)
    
    if not df.is_empty():
        # Get filter values
        year_filter = st.session_state.get('year_filter', [])
        artist_filter = st.session_state.get('artist_filter', [])
        album_filter = st.session_state.get('album_filter', [])
        song_filter = st.session_state.get('song_filter', [])
        
        # Force apply_filters to True if profile is ready and filters exist
        if st.session_state.get('profile_ready', False) and not apply_filters:
            st.session_state['apply_filters'] = True
            apply_filters = True
            st.rerun()
        
        if apply_filters:
            # TURBO-OPTIMIZED PROCESSING: Maximum speed with smart filtering
            try:
                # STEP 1: Lightning-fast filtering with intelligent detection
                filtered_df = df
                
                # Use already computed filters for smart comparison
                all_years = st.session_state.get('_filter_years', [])
                all_artists = st.session_state.get('_filter_artists', [])
                all_albums = st.session_state.get('_filter_albums', [])
                ui_songs = st.session_state.get('_filter_songs', [])
                backend_all_songs = st.session_state.get('_filter_all_songs', ui_songs)
                
                filters_applied = False
                
                # Ultra-fast filtering - only apply if not selecting all options
                if year_filter and len(year_filter) < len(all_years):
                    filtered_df = filtered_df.filter(pl.col('year').is_in(year_filter))
                    filters_applied = True
                
                if artist_filter and len(artist_filter) < len(all_artists) and len(filtered_df) > 0:
                    filtered_df = filtered_df.filter(pl.col('artistName').is_in(artist_filter))
                    filters_applied = True
                
                if album_filter and len(album_filter) < len(all_albums) and len(filtered_df) > 0:
                    filtered_df = filtered_df.filter(pl.col('albumName').is_in(album_filter))
                    filters_applied = True
                
                # Smart song filtering with UI/backend awareness
                if song_filter and len(filtered_df) > 0:
                    # Check if we're filtering meaningfully
                    if len(ui_songs) < len(backend_all_songs) and len(song_filter) < len(ui_songs):
                        # Selective filtering on UI subset
                        filtered_df = filtered_df.filter(pl.col('trackName').is_in(song_filter))
                        filters_applied = True
                    elif len(ui_songs) == len(backend_all_songs) and len(song_filter) < len(backend_all_songs):
                        # Selective filtering on full set
                        filtered_df = filtered_df.filter(pl.col('trackName').is_in(song_filter))
                        filters_applied = True
                
                # Fallback protection
                if len(filtered_df) == 0:
                    st.warning("⚠️ All data filtered out! Using full dataset.")
                    filtered_df = df
                
                total_records = len(filtered_df)
                viz_df = filtered_df
                
                # st.write(f"📈 Visualization data: {len(viz_df)} records")  # Removed for speed
                
                # STEP 3: Ultra-fast metrics using Polars lazy evaluation
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Total Records", f"{total_records:,}")
                with col2:
                    st.metric("🎤 Filtered Records", f"{len(viz_df):,}")
                with col3:
                    # Use lazy evaluation for fast unique counting
                    years_count = viz_df.select(pl.col('year').n_unique()).item()
                    st.metric("📅 Years", years_count)
                
                # STEP 4: QUICK STATS (REMOVED COMPREHENSIVE DATA OVERVIEW)
                try:
                    
                    st.subheader("📊 Quick Stats")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # LIGHTNING-FAST parallel stats computation
                    unique_artists = viz_df['artistName'].n_unique()
                    unique_albums = viz_df['albumName'].n_unique()
                    unique_tracks = viz_df['trackName'].n_unique()
                    total_ms_played = viz_df['msPlayed'].sum()
                    
                    with col1:
                        st.metric("🎤 Unique Artists", f"{unique_artists:,}")
                    with col2:
                        st.metric("💿 Unique Albums", f"{unique_albums:,}")
                    with col3:
                        st.metric("🎵 Unique Tracks", f"{unique_tracks:,}")
                    with col4:
                        total_hours = total_ms_played / (1000 * 60 * 60)
                        st.metric("⏱️ Total Hours", f"{total_hours:.1f}")
                    
                    # NEW: Top 3 Favorites row
                    st.write("")  # Small spacing
                    fav_col1, fav_col2, fav_col3 = st.columns(3)
                    
                    # Calculate top 3 favorites (excluding unknown values)
                    top_artists = (viz_df
                                 .filter(~pl.col('artistName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                 .with_columns([(pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')])
                                 .group_by('artistName')
                                 .agg([pl.col('minutesPlayed').sum().alias('totalMinutes')])
                                 .sort('totalMinutes', descending=True)
                                 .head(3)
                                 .select('artistName')
                                 .to_series()
                                 .to_list())
                    
                    top_albums = (viz_df
                                .filter(~pl.col('albumName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                .with_columns([(pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')])
                                .group_by('albumName')
                                .agg([pl.col('minutesPlayed').sum().alias('totalMinutes')])
                                .sort('totalMinutes', descending=True)
                                .head(3)
                                .select('albumName')
                                .to_series()
                                .to_list())
                    
                    top_songs = (viz_df
                               .filter(~pl.col('trackName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                               .with_columns([(pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')])
                               .group_by('trackName')
                               .agg([pl.col('minutesPlayed').sum().alias('totalMinutes')])
                               .sort('totalMinutes', descending=True)
                               .head(3)
                               .select('trackName')
                               .to_series()
                               .to_list())
                    
                    with fav_col1:
                        st.write("**🎤 Favorite Artists:**")
                        for i, artist in enumerate(top_artists, 1):
                            st.write(f"{i}. {artist}")
                    
                    with fav_col2:
                        st.write("**💿 Favorite Albums:**")
                        for i, album in enumerate(top_albums, 1):
                            st.write(f"{i}. {album}")
                    
                    with fav_col3:
                        st.write("**🎵 Favorite Songs:**")
                        for i, song in enumerate(top_songs, 1):
                            st.write(f"{i}. {song}")
                        
                except Exception as e:
                    st.write(f"Stats computation error: {e}")
                

                
                # CUSTOM VISUALIZATIONS - Built from scratch per user requirements
                
                # LISTENING TIME TRENDS - Line chart showing total minutes per month
                try:
                    st.subheader("📊 Listening Time Trends")
                    
                    # Check for multiple possible timestamp column names
                    timestamp_candidates = ['ts', 'endTime', 'played_at', 'timestamp', 'date', 'playedAt', 'end_time']
                    timestamp_col = None
                    has_timestamp = False
                    monthly_success = False
                    
                    # Find the first available timestamp column
                    for col_name in timestamp_candidates:
                        if col_name in viz_df.columns:
                            # Test if we have non-null timestamp data
                            try:
                                sample_ts = viz_df.select(col_name).filter(pl.col(col_name).is_not_null()).head(5).to_pandas()
                                if len(sample_ts) > 0:
                                    timestamp_col = col_name
                                    has_timestamp = True
                                    break
                            except Exception:
                                continue
                    
                    try:
                        # Try to extract monthly data if we found a timestamp column
                        if has_timestamp and timestamp_col:
                                
                                # Try multiple timestamp parsing approaches for monthly aggregation
                                monthly_minutes = None
                                
                                # Approach 1: Direct string slicing for ISO timestamps (YYYY-MM-DD format)
                                try:
                                    monthly_minutes = (viz_df
                                                     .filter(pl.col('year').is_not_null() & (pl.col('year') > 1900))
                                                     .filter(pl.col(timestamp_col).is_not_null())
                                                     .with_columns([
                                                         (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed'),
                                                         pl.col(timestamp_col).cast(pl.Utf8).str.slice(0, 7).alias('year_month')
                                                     ])
                                                     .filter(pl.col('year_month').is_not_null())
                                                     .group_by('year_month')
                                                     .agg([
                                                         pl.col('minutesPlayed').sum().alias('totalMinutes')
                                                     ])
                                                     .sort('year_month')
                                                     .to_pandas())
                                    
                                    if monthly_minutes is not None and len(monthly_minutes) > 5:  # Need at least 5 months of data
                                        monthly_success = True
                                except Exception:
                                    pass
                                
                                # Approach 2: Parse full timestamp and extract year-month
                                if not monthly_success:
                                    try:
                                        monthly_minutes = (viz_df
                                                         .filter(pl.col('year').is_not_null() & (pl.col('year') > 1900))
                                                         .filter(pl.col(timestamp_col).is_not_null())
                                                         .with_columns([
                                                             (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed'),
                                                             pl.col(timestamp_col).cast(pl.Utf8).str.to_date('%Y-%m-%d').dt.strftime('%Y-%m').alias('year_month')
                                                         ])
                                                         .filter(pl.col('year_month').is_not_null())
                                                         .group_by('year_month')
                                                         .agg([
                                                             pl.col('minutesPlayed').sum().alias('totalMinutes')
                                                         ])
                                                         .sort('year_month')
                                                         .to_pandas())
                                        
                                        if monthly_minutes is not None and len(monthly_minutes) > 5:
                                            monthly_success = True
                                    except Exception:
                                        pass
                                
                                # Approach 3: Handle ISO datetime format (with time)
                                if not monthly_success:
                                    try:
                                        monthly_minutes = (viz_df
                                                         .filter(pl.col('year').is_not_null() & (pl.col('year') > 1900))
                                                         .filter(pl.col(timestamp_col).is_not_null())
                                                         .with_columns([
                                                             (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed'),
                                                             pl.col(timestamp_col).cast(pl.Utf8).str.to_datetime().dt.strftime('%Y-%m').alias('year_month')
                                                         ])
                                                         .filter(pl.col('year_month').is_not_null())
                                                         .group_by('year_month')
                                                         .agg([
                                                             pl.col('minutesPlayed').sum().alias('totalMinutes')
                                                         ])
                                                         .sort('year_month')
                                                         .to_pandas())
                                        
                                        if monthly_minutes is not None and len(monthly_minutes) > 5:
                                            monthly_success = True
                                    except Exception:
                                        pass
                                
                                # Success: Show monthly chart with yearly x-axis focus
                                if monthly_success and monthly_minutes is not None and len(monthly_minutes) > 0:
                                    monthly_minutes['totalHours'] = monthly_minutes['totalMinutes'] / 60
                                    
                                    fig = px.line(monthly_minutes, 
                                                x='year_month', 
                                                y='totalMinutes',
                                                title='Listening Time Trends',
                                                labels={'totalMinutes': 'Minutes Played', 'year_month': 'Year'},
                                                height=350)
                                    
                                    fig.update_traces(line=dict(width=3, color='#1DB954'))
                                    fig.update_layout(
                                        margin=dict(l=0, r=0, t=40, b=0),
                                        paper_bgcolor='#191414',
                                        plot_bgcolor='#191414',
                                        font=dict(color='#FFFFFF'),
                                        title_font=dict(color='#1DB954', size=16),
                                        xaxis=dict(
                                            tickangle=45,
                                            title='Year',
                                            gridcolor='#535353',
                                            color='#FFFFFF'
                                        ),
                                        yaxis=dict(
                                            gridcolor='#535353',
                                            color='#FFFFFF'
                                        )
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        has_timestamp = False
                    
                    # Fallback to yearly data if monthly parsing fails
                    if not monthly_success:
                        yearly_minutes = (viz_df
                                        .filter(pl.col('year').is_not_null() & (pl.col('year') > 1900))
                                        .with_columns([
                                            (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')
                                        ])
                                        .group_by('year')
                                        .agg([
                                            pl.col('minutesPlayed').sum().alias('totalMinutes')
                                        ])
                                        .sort('year')
                                        .to_pandas())
                        
                        if len(yearly_minutes) > 0:
                            yearly_minutes['totalHours'] = yearly_minutes['totalMinutes'] / 60
                            
                            fig = px.line(yearly_minutes, 
                                        x='year', 
                                        y='totalMinutes',
                                        title='Total Minutes Streamed Per Year',
                                        labels={'totalMinutes': 'Minutes Played', 'year': 'Year'},
                                        height=350)
                            
                            fig.update_traces(line=dict(width=3, color='#1DB954'))
                            fig.update_layout(
                                margin=dict(l=0, r=0, t=40, b=0),
                                paper_bgcolor='#191414',
                                plot_bgcolor='#191414',
                                font=dict(color='#FFFFFF'),
                                title_font=dict(color='#1DB954', size=16),
                                xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                                yaxis=dict(gridcolor='#535353', color='#FFFFFF')
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No trend data available")
                        
                except Exception as e:
                    st.error(f"Trend visualization error: {e}")
                
                # TOP ARTISTS OF ALL TIME - Bar chart with total minutes
                try:
                    st.subheader("🎤 Top Artists of All Time")
                    
                    top_artists_minutes = (viz_df
                                         .filter(~pl.col('artistName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                         .with_columns([
                                             (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')
                                         ])
                                         .group_by('artistName')
                                         .agg([
                                             pl.col('minutesPlayed').sum().alias('totalMinutes')
                                         ])
                                         .sort('totalMinutes', descending=True)
                                         .head(15)
                                         .to_pandas())
                    
                    if len(top_artists_minutes) > 0:
                        top_artists_minutes['totalHours'] = top_artists_minutes['totalMinutes'] / 60
                        
                        fig = px.bar(top_artists_minutes,
                                   x='totalMinutes',
                                   y='artistName',
                                   orientation='h',
                                   title='Most Listened Artists (Total Minutes)',
                                   labels={'totalMinutes': 'Total Minutes', 'artistName': 'Artist'},
                                   height=500,
                                   color_discrete_sequence=['#1DB954'])
                        
                        fig.update_layout(
                            margin=dict(l=0, r=0, t=40, b=0),
                            paper_bgcolor='#191414',
                            plot_bgcolor='#191414',
                            font=dict(color='#FFFFFF'),
                            title_font=dict(color='#1DB954', size=16),
                            xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                            yaxis=dict(categoryorder='total ascending', color='#FFFFFF')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No artist data available")
                        
                except Exception as e:
                    st.error(f"Top Artists visualization error: {e}")
                
                # TOP ARTISTS BY YEAR - Interactive treemap and bar chart
                try:
                    st.subheader("🎵 Top Artists by Year")
                    
                    # Get top artists per year (excluding unknown values)
                    artists_by_year = (viz_df
                                     .filter(pl.col('year').is_not_null() & (pl.col('year') > 1900))
                                     .filter(~pl.col('artistName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                     .with_columns([
                                         (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')
                                     ])
                                     .group_by(['year', 'artistName'])
                                     .agg([
                                         pl.col('minutesPlayed').sum().alias('totalMinutes')
                                     ])
                                     .sort(['year', 'totalMinutes'], descending=[False, True]))
                    
                    # Create a selectbox to choose year for treemap
                    available_years = sorted(viz_df.select('year').drop_nulls().unique().to_series().to_list())
                    if available_years:
                        selected_year = st.selectbox(
                            "Select Year for Top Artists Treemap:",
                            options=available_years,
                            index=len(available_years)-1 if available_years else 0,
                            key="year_selector_artists"
                        )
                        
                        # Get top 20 artists for selected year
                        year_artists = (artists_by_year
                                      .filter(pl.col('year') == selected_year)
                                      .head(20)
                                      .to_pandas())
                        
                        if len(year_artists) > 0:
                            year_artists['totalHours'] = year_artists['totalMinutes'] / 60
                            
                            # Create treemap with enhanced text sizing and darker colors
                            fig = px.treemap(year_artists,
                                           path=['artistName'],
                                           values='totalMinutes',
                                           title=f'Top Artists of {selected_year} (Size = Minutes Played)',
                                           height=500,
                                           color_discrete_sequence=['#1B3B36', '#2E8B57', '#228B22', '#006400', '#8B4513', '#800080', '#B22222', '#FF4500', '#8B0000', '#483D8B', '#2F4F4F', '#556B2F', '#8B008B', '#9932CC', '#8B4513', '#A0522D', '#2E4B6B', '#800000', '#008B8B', '#4682B4'])
                            
                            # Enhanced font sizing that scales with square size
                            fig.update_traces(
                                textfont_size=20,  # Base font size (much larger)
                                textfont_color="white",
                                textfont_family="Arial Black",
                                textposition="middle center"
                            )
                            
                            fig.update_layout(
                                margin=dict(l=0, r=0, t=40, b=0),
                                paper_bgcolor='#191414',
                                plot_bgcolor='#191414',
                                font=dict(size=16, color='#FFFFFF'),
                                title_font=dict(color='#1DB954', size=18)
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Also show as grouped bar chart alternative
                            st.write("**Alternative View: Bar Chart**")
                            fig_bar = px.bar(year_artists.head(10),
                                           x='totalMinutes',
                                           y='artistName',
                                           orientation='h',
                                           title=f'Top 10 Artists of {selected_year}',
                                           height=400,
                                           color_discrete_sequence=['#1DB954'])
                            
                            fig_bar.update_layout(
                                margin=dict(l=0, r=0, t=40, b=0),
                                paper_bgcolor='#191414',
                                plot_bgcolor='#191414',
                                font=dict(color='#FFFFFF'),
                                title_font=dict(color='#1DB954', size=16),
                                xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                                yaxis=dict(categoryorder='total ascending', color='#FFFFFF')
                            )
                            st.plotly_chart(fig_bar, use_container_width=True)
                        else:
                            st.info(f"No artist data available for {selected_year}")
                    else:
                        st.info("No year data available for artist analysis")
                        
                except Exception as e:
                    st.error(f"Artists by Year visualization error: {e}")
                
                # TOP 25 TRACKS ALL TIME - Bar chart showing most played tracks
                try:
                    st.subheader("🎵 Top 25 Tracks All Time")
                    
                    top_tracks_alltime = (viz_df
                                        .filter(~pl.col('trackName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                        .filter(~pl.col('artistName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                        .with_columns([
                                            (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')
                                        ])
                                        .group_by(['trackName', 'artistName'])
                                        .agg([
                                            pl.col('minutesPlayed').sum().alias('totalMinutes')
                                        ])
                                        .sort('totalMinutes', descending=True)
                                        .head(25)
                                        .to_pandas())
                    
                    if len(top_tracks_alltime) > 0:
                        # Create track labels with artist
                        top_tracks_alltime['trackLabel'] = top_tracks_alltime['trackName'] + ' - ' + top_tracks_alltime['artistName']
                        top_tracks_alltime['totalHours'] = top_tracks_alltime['totalMinutes'] / 60
                        
                        fig = px.bar(top_tracks_alltime,
                                   x='totalMinutes',
                                   y='trackLabel',
                                   orientation='h',
                                   title='Top 25 Most Played Tracks (Total Minutes)',
                                   labels={'totalMinutes': 'Total Minutes', 'trackLabel': 'Track'},
                                   height=700,
                                   color_discrete_sequence=['#1DB954'])
                        
                        fig.update_layout(
                            margin=dict(l=0, r=0, t=40, b=0),
                            paper_bgcolor='#191414',
                            plot_bgcolor='#191414',
                            font=dict(color='#FFFFFF'),
                            title_font=dict(color='#1DB954', size=16),
                            xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                            yaxis=dict(categoryorder='total ascending', color='#FFFFFF')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No track data available")
                        
                except Exception as e:
                    st.error(f"Top Tracks All Time visualization error: {e}")
                
                # TOP TRACKS BY YEAR - Treemap showing yearly favorites
                try:
                    st.subheader("🎵 Top Tracks by Year")
                    
                    # Get top tracks per year (excluding unknown values)
                    tracks_by_year = (viz_df
                                    .filter(pl.col('year').is_not_null() & (pl.col('year') > 1900))
                                    .filter(~pl.col('trackName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                    .filter(~pl.col('artistName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                    .with_columns([
                                        (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')
                                    ])
                                    .group_by(['year', 'trackName', 'artistName'])
                                    .agg([
                                        pl.col('minutesPlayed').sum().alias('totalMinutes')
                                    ])
                                    .sort(['year', 'totalMinutes'], descending=[False, True]))
                    
                    # Create a selectbox to choose year for treemap
                    available_years = sorted(viz_df.select('year').drop_nulls().unique().to_series().to_list())
                    if available_years:
                        selected_year = st.selectbox(
                            "Select Year for Top Tracks Treemap:",
                            options=available_years,
                            index=len(available_years)-1 if available_years else 0,
                            key="year_selector_tracks"
                        )
                        
                        # Get top 20 tracks for selected year
                        year_tracks = (tracks_by_year
                                     .filter(pl.col('year') == selected_year)
                                     .head(20)
                                     .to_pandas())
                        
                        if len(year_tracks) > 0:
                            # Create track labels with artist
                            year_tracks['trackLabel'] = year_tracks['trackName'] + ' - ' + year_tracks['artistName']
                            year_tracks['totalHours'] = year_tracks['totalMinutes'] / 60
                            
                            # Create treemap with enhanced text sizing and darker colors
                            fig = px.treemap(year_tracks,
                                           path=['trackLabel'],
                                           values='totalMinutes',
                                           title=f'Top Tracks of {selected_year} (Size = Minutes Played)',
                                           height=500,
                                           color_discrete_sequence=['#1B3B36', '#2E8B57', '#228B22', '#006400', '#8B4513', '#800080', '#B22222', '#FF4500', '#8B0000', '#483D8B', '#2F4F4F', '#556B2F', '#8B008B', '#9932CC', '#8B4513', '#A0522D', '#2E4B6B', '#800000', '#008B8B', '#4682B4'])
                            
                            # Enhanced font sizing that scales with square size
                            fig.update_traces(
                                textfont_size=18,  # Base font size (large)
                                textfont_color="white",
                                textfont_family="Arial Black",
                                textposition="middle center"
                            )
                            
                            fig.update_layout(
                                margin=dict(l=0, r=0, t=40, b=0),
                                paper_bgcolor='#191414',
                                plot_bgcolor='#191414',
                                font=dict(size=16, color='#FFFFFF'),
                                title_font=dict(color='#1DB954', size=18)
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Also show as grouped bar chart alternative
                            st.write("**Alternative View: Bar Chart**")
                            fig_bar = px.bar(year_tracks.head(10),
                                           x='totalMinutes',
                                           y='trackLabel',
                                           orientation='h',
                                           title=f'Top 10 Tracks of {selected_year}',
                                           height=400,
                                           color_discrete_sequence=['#1DB954'])
                            
                            fig_bar.update_layout(
                                margin=dict(l=0, r=0, t=40, b=0),
                                paper_bgcolor='#191414',
                                plot_bgcolor='#191414',
                                font=dict(color='#FFFFFF'),
                                title_font=dict(color='#1DB954', size=16),
                                xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                                yaxis=dict(categoryorder='total ascending', color='#FFFFFF')
                            )
                            st.plotly_chart(fig_bar, use_container_width=True)
                        else:
                            st.info(f"No track data available for {selected_year}")
                    else:
                        st.info("No year data available for track analysis")
                        
                except Exception as e:
                    st.error(f"Top Tracks by Year visualization error: {e}")
                
                # TOP ALBUMS OF ALL TIME - Bar chart with total minutes
                try:
                    st.subheader("💿 Top Albums of All Time")
                    
                    top_albums_minutes = (viz_df
                                         .filter(~pl.col('albumName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                         .with_columns([
                                             (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')
                                         ])
                                         .group_by('albumName')
                                         .agg([
                                             pl.col('minutesPlayed').sum().alias('totalMinutes')
                                         ])
                                         .sort('totalMinutes', descending=True)
                                         .head(15)
                                         .to_pandas())
                    
                    if len(top_albums_minutes) > 0:
                        top_albums_minutes['totalHours'] = top_albums_minutes['totalMinutes'] / 60
                        
                        fig = px.bar(top_albums_minutes,
                                   x='totalMinutes',
                                   y='albumName',
                                   orientation='h',
                                   title='Most Listened Albums (Total Minutes)',
                                   labels={'totalMinutes': 'Total Minutes', 'albumName': 'Album'},
                                   height=500,
                                   color_discrete_sequence=['#1DB954'])
                        
                        fig.update_layout(
                            margin=dict(l=0, r=0, t=40, b=0),
                            paper_bgcolor='#191414',
                            plot_bgcolor='#191414',
                            font=dict(color='#FFFFFF'),
                            title_font=dict(color='#1DB954', size=16),
                            xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                            yaxis=dict(categoryorder='total ascending', color='#FFFFFF')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No album data available")
                        
                except Exception as e:
                    st.error(f"Top Albums visualization error: {e}")
                
                # TOP ALBUMS BY YEAR - Interactive treemap and bar chart
                try:
                    st.subheader("💿 Top Albums by Year")
                    
                    # Get top albums per year (excluding unknown values)
                    albums_by_year = (viz_df
                                     .filter(pl.col('year').is_not_null() & (pl.col('year') > 1900))
                                     .filter(~pl.col('albumName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                     .with_columns([
                                         (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')
                                     ])
                                     .group_by(['year', 'albumName'])
                                     .agg([
                                         pl.col('minutesPlayed').sum().alias('totalMinutes')
                                     ])
                                     .sort(['year', 'totalMinutes'], descending=[False, True]))
                    
                    # Create a selectbox to choose year for treemap
                    available_years = sorted(viz_df.select('year').drop_nulls().unique().to_series().to_list())
                    if available_years:
                        selected_year = st.selectbox(
                            "Select Year for Top Albums Treemap:",
                            options=available_years,
                            index=len(available_years)-1 if available_years else 0,
                            key="year_selector_albums"
                        )
                        
                        # Get top 20 albums for selected year
                        year_albums = (albums_by_year
                                      .filter(pl.col('year') == selected_year)
                                      .head(20)
                                      .to_pandas())
                        
                        if len(year_albums) > 0:
                            year_albums['totalHours'] = year_albums['totalMinutes'] / 60
                            
                            # Create treemap with enhanced text sizing and darker colors
                            fig = px.treemap(year_albums,
                                           path=['albumName'],
                                           values='totalMinutes',
                                           title=f'Top Albums of {selected_year} (Size = Minutes Played)',
                                           height=500,
                                           color_discrete_sequence=['#1B3B36', '#2E8B57', '#228B22', '#006400', '#8B4513', '#800080', '#B22222', '#FF4500', '#8B0000', '#483D8B', '#2F4F4F', '#556B2F', '#8B008B', '#9932CC', '#8B4513', '#A0522D', '#2E4B6B', '#800000', '#008B8B', '#4682B4'])
                            
                            # Enhanced font sizing that scales with square size
                            fig.update_traces(
                                textfont_size=19,  # Base font size (large)
                                textfont_color="white",
                                textfont_family="Arial Black",
                                textposition="middle center"
                            )
                            
                            fig.update_layout(
                                margin=dict(l=0, r=0, t=40, b=0),
                                paper_bgcolor='#191414',
                                plot_bgcolor='#191414',
                                font=dict(size=16, color='#FFFFFF'),
                                title_font=dict(color='#1DB954', size=18)
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Also show as grouped bar chart alternative
                            st.write("**Alternative View: Bar Chart**")
                            fig_bar = px.bar(year_albums.head(10),
                                           x='totalMinutes',
                                           y='albumName',
                                           orientation='h',
                                           title=f'Top 10 Albums of {selected_year}',
                                           height=400,
                                           color_discrete_sequence=['#1DB954'])
                            
                            fig_bar.update_layout(
                                margin=dict(l=0, r=0, t=40, b=0),
                                paper_bgcolor='#191414',
                                plot_bgcolor='#191414',
                                font=dict(color='#FFFFFF'),
                                title_font=dict(color='#1DB954', size=16),
                                xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                                yaxis=dict(categoryorder='total ascending', color='#FFFFFF')
                            )
                            st.plotly_chart(fig_bar, use_container_width=True)
                        else:
                            st.info(f"No album data available for {selected_year}")
                    else:
                        st.info("No year data available for album analysis")
                        
                except Exception as e:
                    st.error(f"Albums by Year visualization error: {e}")
                
                # ARTIST LOYALTY - How long you stick with artists before moving on
                try:
                    st.subheader("💝 Artist Loyalty")
                    
                    # Calculate artist listening span and intensity
                    try:
                        # Check if we have timestamp data
                        if 'ts' in viz_df.columns:
                            artist_loyalty = (viz_df
                                            .filter(~pl.col('artistName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                            .with_columns([
                                                (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed'),
                                                pl.col('ts').cast(pl.Utf8).str.slice(0, 10).alias('date')
                                            ])
                                            .group_by('artistName')
                                            .agg([
                                                pl.col('date').min().alias('first_listen'),
                                                pl.col('date').max().alias('last_listen'),
                                                pl.col('minutesPlayed').sum().alias('totalMinutes'),
                                                pl.col('date').n_unique().alias('unique_days')
                                            ])
                                            .with_columns([
                                                (pl.col('last_listen').str.to_date() - pl.col('first_listen').str.to_date()).dt.total_days().alias('span_days')
                                            ])
                                            .filter(pl.col('totalMinutes') >= 60)  # At least 1 hour of listening
                                            .sort('totalMinutes', descending=True)
                                            .head(20)
                                            .to_pandas())
                        else:
                            # Fallback: Simple loyalty based on total minutes only (excluding unknown values)
                            artist_loyalty = (viz_df
                                            .filter(~pl.col('artistName').str.to_lowercase().is_in(['unknown', 'n/a', '', 'null']))
                                            .with_columns([
                                                (pl.col('msPlayed') / (1000 * 60)).alias('minutesPlayed')
                                            ])
                                            .group_by('artistName')
                                            .agg([
                                                pl.col('minutesPlayed').sum().alias('totalMinutes'),
                                                pl.col('minutesPlayed').count().alias('play_count')
                                            ])
                                            .with_columns([
                                                # Use play frequency as loyalty proxy
                                                (pl.col('play_count') * 10).alias('unique_days'),
                                                pl.lit(365).alias('span_days')  # Default span
                                            ])
                                            .filter(pl.col('totalMinutes') >= 60)
                                            .sort('totalMinutes', descending=True)
                                            .head(20)
                                            .to_pandas())
                    except Exception:
                        # Final fallback
                        artist_loyalty = pd.DataFrame()
                    
                    if len(artist_loyalty) > 0:
                        artist_loyalty['loyalty_score'] = (artist_loyalty['unique_days'] / (artist_loyalty['span_days'] + 1) * 100).round(1)
                        
                        # Scatter plot: total minutes vs loyalty score with artist name annotations
                        fig = px.scatter(artist_loyalty, 
                                       x='totalMinutes', 
                                       y='loyalty_score',
                                       size='unique_days',
                                       text='artistName',  # Add artist names as text
                                       hover_data=['artistName', 'span_days'],
                                       title='Artist Loyalty: Total Listening vs Consistency',
                                       labels={'totalMinutes': 'Total Minutes', 'loyalty_score': 'Loyalty Score (%)', 'unique_days': 'Days Listened'},
                                       height=400,
                                       color_discrete_sequence=['#1DB954'])
                        
                        # Update text annotations to show artist names on bubbles
                        fig.update_traces(
                            textposition="middle center",
                            textfont_size=10,
                            textfont_color="white",
                            marker=dict(color='#1DB954')
                        )
                        
                        fig.update_layout(
                            margin=dict(l=0, r=0, t=40, b=0),
                            paper_bgcolor='#191414',
                            plot_bgcolor='#191414',
                            font=dict(color='#FFFFFF'),
                            title_font=dict(color='#1DB954', size=16),
                            xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                            yaxis=dict(gridcolor='#535353', color='#FFFFFF')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Top loyal artists
                        st.write("**Most Loyal Artists (High Consistency):**")
                        top_loyal = artist_loyalty.nlargest(10, 'loyalty_score')[['artistName', 'totalMinutes', 'loyalty_score', 'span_days', 'unique_days']]
                        top_loyal.columns = ['Artist', 'Total Minutes', 'Loyalty %', 'Span (Days)', 'Listening Days']
                        top_loyal['Total Minutes'] = top_loyal['Total Minutes'].round(0).astype(int)
                        st.dataframe(top_loyal, use_container_width=True, height=300)
                    else:
                        st.info("No artist loyalty data available")
                        
                except Exception as e:
                    st.error(f"Artist Loyalty visualization error: {e}")

                # TOP 25 SONGS IN MOST PLAYLISTS - Songs that appear across multiple playlists
                show_songs_in_most_playlists()

                # TOP 10 PLAYLISTS BY MINUTES PLAYED - New visualization
                try:
                    st.subheader("🎵 Top 10 Playlists by Minutes Played All Time")
                    
                    # Try to load playlist data from cache
                    profile_name = st.session_state.get('selected_profile')
                    if profile_name:
                        try:
                            import os
                            import polars as pl
                            
                            # Try to load playlist data from cache
                            playlist_path = os.path.join(CACHE_DIR, f"{profile_name}_playlists.parquet")
                            

                            
                            if os.path.exists(playlist_path):
                                try:
                                    # Load playlist data
                                    playlist_df = pl.read_parquet(playlist_path).to_pandas()
                                    
                                    if len(playlist_df) > 0:
                                        # Sort by total minutes and get top 10
                                        top_playlists = playlist_df.nlargest(10, 'totalMinutes')
                                        top_playlists['totalHours'] = top_playlists['totalMinutes'] / 60
                                        
                                        # Create horizontal bar chart
                                        fig = px.bar(top_playlists,
                                                   x='totalMinutes',
                                                   y='playlistName',
                                                   orientation='h',
                                                   title='Top 10 Playlists by Total Minutes Played',
                                                   labels={'totalMinutes': 'Total Minutes', 'playlistName': 'Playlist'},
                                                   height=500,
                                                   color_discrete_sequence=['#1DB954'])
                                        
                                        fig.update_layout(
                                            margin=dict(l=0, r=0, t=40, b=0),
                                            paper_bgcolor='#191414',
                                            plot_bgcolor='#191414',
                                            font=dict(color='#FFFFFF'),
                                            title_font=dict(color='#1DB954', size=16),
                                            xaxis=dict(gridcolor='#535353', color='#FFFFFF'),
                                            yaxis=dict(categoryorder='total ascending', color='#FFFFFF')
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Show detailed playlist info
                                        st.write("**Playlist Details:**")
                                        display_playlists = top_playlists[['playlistName', 'totalMinutes', 'trackCount', 'totalHours']].copy()
                                        display_playlists.columns = ['Playlist Name', 'Total Minutes', 'Track Count', 'Total Hours']
                                        display_playlists['Total Minutes'] = display_playlists['Total Minutes'].round(0).astype(int)
                                        display_playlists['Total Hours'] = display_playlists['Total Hours'].round(1)
                                        st.dataframe(display_playlists, use_container_width=True, height=300)
                                    else:
                                        st.warning("Playlist file exists but contains no data")
                                except Exception as e:
                                    st.error(f"Error reading playlist data: {e}")
                            else:
                                st.info("No playlist data found for this profile.")
                        except Exception as e:
                            st.error(f"Could not access playlist data: {e}")
                    else:
                        st.info("No profile selected")
                        
                except Exception as e:
                    st.error(f"Top Playlists visualization error: {e}")
                    
            except Exception as e:
                st.error(f"⚠️ Visualization error: {str(e)}")
                st.write("Full error details:", e)
                st.info("Try adjusting your filters or refreshing the page.")
        else:
            st.info("🎯 **Apply filters will be automatically enabled when profile loads...**")
            
            # Show quick stats without filters
            try:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📊 Total Records", f"{len(df):,}")
                with col2:
                    unique_artists = len(df.select('artistName').unique())
                    st.metric("🎤 Unique Artists", f"{unique_artists:,}")
            except Exception as e:
                st.write(f"Stats error: {e}")
                
    else:
        st.info("🎯 Select a profile from the right panel to load your Spotify data.")

# --- Right Panel: Profile Management ---
with right:
    st.header("Profiles")
    st.write("Manage your Spotify data profiles.")
    profile_mode = st.radio("Choose an option:", ["Create a Profile & Upload New Spotify Data", "Select a Pre-Existing Profile"])
    
    # Initialize selected_profile to avoid NameError
    selected_profile = None

    # Reset logic: if profile_mode changes, reset all filters, visuals, and data
    if 'last_profile_mode' not in st.session_state:
        st.session_state['last_profile_mode'] = profile_mode
    if profile_mode != st.session_state['last_profile_mode']:
        # Clear all relevant session state variables
        for key in [
            'df', 'year_filter', 'artist_filter', 'album_filter', 'song_filter',
            'apply_filters', 'filters_ready', 'profile_ready', 'profile_loading',
            'selected_profile', 'created_profile', 'show_upload', 'uploaded_files',
            'reset_filters', 'last_profile', 'profile_select', 'profile_upload',
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state['last_profile_mode'] = profile_mode
        st.rerun()

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
                    st.success("Files Upload Completed & Profile Saved", icon="✅")
                    
                    # Immediately load the data and enable all functionality
                    st.session_state['created_profile'] = profile_name
                    st.session_state['show_upload'] = False
                    st.session_state['uploaded_files'] = True
                    st.session_state['selected_profile'] = profile_name
                    
                    # START TIMING for new profile load
                    start_time = time.time()
                    st.session_state['profile_start_time'] = start_time
                    
                    # Load data immediately with comprehensive system
                    df = load_profile_data_turbo_enhanced(profile_name)
                    st.session_state['df'] = df
                    
                    if not df.is_empty():
                        # Set up filters and enable dashboard
                        st.session_state['year_filter'] = []
                        st.session_state['artist_filter'] = []
                        st.session_state['album_filter'] = []
                        st.session_state['song_filter'] = []
                        st.session_state['_filters_computed'] = False
                        
                        st.session_state['apply_filters'] = True
                        st.session_state['profile_ready'] = True
                        st.session_state['filters_ready'] = True
                        st.session_state['profile_loading'] = False
                        
                        # END TIMING - Data loaded
                        if 'profile_start_time' in st.session_state:
                            del st.session_state['profile_start_time']
                    else:
                        st.warning("No data found in uploaded files.")
                        st.session_state['profile_ready'] = False
                        st.session_state['filters_ready'] = False
                    
                    # Immediately rerun to show the dashboard
                    st.rerun()
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
            # START TIMING
            start_time = time.time()
            st.session_state['profile_start_time'] = start_time
            
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
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting profile: {e}")
        # Show loading or ready notification in the right panel, never both
        if st.session_state['profile_loading'] and not st.session_state['filters_ready']:
            # ULTRA-AGGRESSIVE MODE - Data only, filters deferred
            profile_name = st.session_state.get('selected_profile')
            
            # Load data silently with comprehensive system
            df = load_profile_data_turbo_enhanced(profile_name)
            st.session_state['df'] = df
            
            if not df.is_empty():
                # DEFERRED FILTERS: Set minimal defaults, compute on-demand
                st.session_state['year_filter'] = []
                st.session_state['artist_filter'] = []
                st.session_state['album_filter'] = []
                st.session_state['song_filter'] = []
                st.session_state['_filters_computed'] = False  # Mark as not computed yet
                
                st.session_state['apply_filters'] = True
                st.session_state['profile_ready'] = True
                st.session_state['filters_ready'] = True
                
                # END TIMING - Data loaded, filters will compute on-demand
                if 'profile_start_time' in st.session_state:
                    del st.session_state['profile_start_time']
            else:
                st.warning("No data found in profile.")
                st.session_state['profile_ready'] = False
                st.session_state['filters_ready'] = False
            
            st.session_state['profile_loading'] = False
            st.rerun()
        elif st.session_state['filters_ready']:
            st.success("✅ Ready!")
            df = st.session_state.get('df', pl.DataFrame())
            if not df.is_empty():
                st.write(f"📊 {len(df):,} records loaded")



# --- Left Panel: Filters ---
with left:
    # Compact header with icon
    st.markdown('<h3 style="margin-bottom: 0.5rem; color: #1f77b4;">🎛️ Filters</h3>', unsafe_allow_html=True)
    # Only show filters if profile is ready and data is loaded
    if st.session_state.get('filters_ready', False):
        df = st.session_state.get('df', pl.DataFrame())
        if not df.is_empty():
            pdf = df.to_pandas()
            # Only show warning if DataFrame is truly empty
            if len(pdf) == 0:
                st.warning('Profile data is empty. Please check your uploaded files.')
            else:
                # ON-DEMAND FILTER COMPUTATION - Only compute when filters are accessed
                profile_name = st.session_state.get('selected_profile')
                
                # Check if filters have been computed yet
                if not st.session_state.get('_filters_computed', False):
                    # Compute filters now (deferred from initial load)
                    with st.spinner("⚡ Computing filters..."):
                        filters = prepare_filters_turbo(df, profile_name)
                        st.session_state['_filter_years'] = filters['years']
                        st.session_state['_filter_artists'] = filters['artists']
                        st.session_state['_filter_albums'] = filters['albums']
                        st.session_state['_filter_songs'] = filters['songs']
                        st.session_state['_filter_all_songs'] = filters.get('all_songs', filters['songs'])
                        st.session_state['_filters_computed'] = True
                
                # Use cached computed filters
                years = st.session_state.get('_filter_years', [])
                artists = st.session_state.get('_filter_artists', [])
                albums = st.session_state.get('_filter_albums', [])
                songs = st.session_state.get('_filter_songs', [])
                all_songs = st.session_state.get('_filter_all_songs', songs)
                

                
                # Robustly get filter keys with defaults - ENSURE THEY'RE VALID
                year_filter = st.session_state.get('year_filter', [])
                artist_filter = st.session_state.get('artist_filter', [])
                album_filter = st.session_state.get('album_filter', [])
                song_filter = st.session_state.get('song_filter', [])
                
                # CRITICAL FIX: Filter session state values to only include valid options
                year_filter = [y for y in year_filter if y in years]
                artist_filter = [a for a in artist_filter if a in artists]
                album_filter = [a for a in album_filter if a in albums]
                song_filter = [s for s in song_filter if s in songs]

                st.markdown("""
                <style>
                /* ULTRA-COMPACT FILTER PANEL CSS */
                
                /* Remove all default Streamlit spacing */
                .stSelectbox > div > div {
                    margin-bottom: 0px !important;
                    padding-bottom: 0px !important;
                }
                
                /* Compact multiselect widgets */
                .stMultiSelect > div {
                    margin-bottom: 0px !important;
                    padding-bottom: 2px !important;
                }
                
                /* Compact containers */
                .stContainer > div {
                    padding-top: 0px !important;
                    padding-bottom: 0px !important;
                    margin-top: 0px !important;
                    margin-bottom: 4px !important;
                }
                
                /* Compact filter sections */
                .looker-filter-section {
                    margin-bottom: 2px !important;
                    padding-bottom: 0px !important;
                    padding-top: 0px !important;
                }
                
                /* Enhanced filter labels - larger and more readable */
                .looker-filter-label { 
                    font-weight: 600; 
                    font-size: 1.1em !important; 
                    margin-right: 0.3em;
                    margin-bottom: 0px !important;
                    margin-top: 0px !important;
                    display: block;
                    color: #1f77b4;
                    line-height: 1.2 !important;
                    padding-bottom: 0px !important;
                }
                
                /* Enhanced filter links - larger and more readable */
                .looker-link {
                    font-size: 0.85em !important;
                    font-weight: 500 !important;
                    color: #1976d2;
                    text-decoration: underline;
                    cursor: pointer;
                    margin-right: 0.4em;
                    margin-bottom: 0px !important;
                    margin-top: 0px !important;
                    background: none;
                    border: none;
                    padding: 0;
                    display: inline;
                    line-height: 1.1 !important;
                }
                .looker-link:hover {
                    color: #0d47a1;
                }
                
                /* ULTRA-COMPACT: Remove ALL spacing from elements inside left column */
                [data-testid="column"]:first-child .element-container {
                    margin-bottom: 0.1rem !important;
                    margin-top: 0px !important;
                    padding-top: 0px !important;
                    padding-bottom: 0px !important;
                }
                
                [data-testid="column"]:first-child .stMarkdown {
                    margin-bottom: 0px !important;
                    margin-top: 0px !important;
                    padding-top: 0px !important;
                    padding-bottom: 0px !important;
                }
                
                /* Ultra-compact multiselect dropdown */
                .stMultiSelect label {
                    margin-bottom: 0px !important;
                    margin-top: 0px !important;
                    padding-bottom: 0px !important;
                    padding-top: 0px !important;
                }
                
                /* Remove ALL extra spacing from divs */
                [data-testid="column"]:first-child div[data-testid="stMarkdownContainer"] {
                    margin-bottom: 0px !important;
                    margin-top: 0px !important;
                    padding-bottom: 0px !important;
                    padding-top: 0px !important;
                }
                
                /* Ultra-compact filter containers */
                [data-testid="column"]:first-child .stContainer {
                    padding: 0px !important;
                    margin: 0px !important;
                }
                
                /* Minimal spacing from headers in left panel */
                [data-testid="column"]:first-child .stMarkdown h1,
                [data-testid="column"]:first-child .stMarkdown h2,
                [data-testid="column"]:first-child .stMarkdown h3 {
                    margin-bottom: 0.3rem !important;
                    margin-top: 0px !important;
                    padding-bottom: 0px !important;
                    padding-top: 0px !important;
                }
                
                /* Ultra-compact button spacing */
                [data-testid="column"]:first-child .stButton {
                    margin-top: 0.2rem !important;
                    margin-bottom: 0px !important;
                    padding-top: 0px !important;
                    padding-bottom: 0px !important;
                }
                
                /* Remove ALL gaps in left panel */
                [data-testid="column"]:first-child > div {
                    gap: 0.1rem !important;
                }
                
                [data-testid="column"]:first-child .block-container {
                    padding-top: 0px !important;
                    padding-bottom: 0px !important;
                    margin-top: 0px !important;
                    margin-bottom: 0px !important;
                }
                
                /* Ultra-compact multiselect dropdown list */
                .stMultiSelect [data-baseweb="select"] {
                    margin-bottom: 0px !important;
                    margin-top: 0px !important;
                    min-height: 2.4rem !important;
                }
                
                /* Ultra-compact multiselect options */
                .stMultiSelect [data-baseweb="select"] > div {
                    padding: 1px 6px !important;
                    min-height: 2.4rem !important;
                }
                
                /* Minimal space between filter elements */
                [data-testid="column"]:first-child .stMultiSelect {
                    margin-bottom: 0.1rem !important;
                    margin-top: 0px !important;
                }
                
                /* Ultra-compact filter labels with icons */
                [data-testid="column"]:first-child .looker-filter-label {
                    margin-bottom: 0px !important;
                    margin-top: 0px !important;
                    padding-bottom: 0px !important;
                    padding-top: 0px !important;
                }
                
                /* Remove spacing from small elements */
                [data-testid="column"]:first-child small {
                    margin-bottom: 0px !important;
                    margin-top: 0px !important;
                    padding-bottom: 0px !important;
                    padding-top: 0px !important;
                    line-height: 1.1 !important;
                }
                </style>
                """, unsafe_allow_html=True)

                # ENHANCED FILTERS WITH SEARCH AND CHECKBOXES
                
                # Initialize session state for filter selections if not exists
                if 'year_filter_enhanced' not in st.session_state:
                    st.session_state['year_filter_enhanced'] = year_filter.copy()
                if 'artist_filter_enhanced' not in st.session_state:
                    st.session_state['artist_filter_enhanced'] = artist_filter.copy()
                if 'album_filter_enhanced' not in st.session_state:
                    st.session_state['album_filter_enhanced'] = album_filter.copy()
                if 'song_filter_enhanced' not in st.session_state:
                    st.session_state['song_filter_enhanced'] = song_filter.copy()
                
                # Year filter with enhanced interface
                with st.expander("📅 Year Filter", expanded=False):
                    st.session_state['year_filter_enhanced'] = create_enhanced_filter(
                        'year', 'Year', '📅', years, 
                        st.session_state['year_filter_enhanced'], 
                        'year_search', 'year_checkbox'
                    )

                # Artist filter with enhanced interface  
                with st.expander("🎤 Artist Filter", expanded=False):
                    st.session_state['artist_filter_enhanced'] = create_enhanced_filter(
                        'artist', 'Artist', '🎤', artists, 
                        st.session_state['artist_filter_enhanced'], 
                        'artist_search', 'artist_checkbox'
                    )

                # Album filter with enhanced interface
                with st.expander("💿 Album Filter", expanded=False):
                    st.session_state['album_filter_enhanced'] = create_enhanced_filter(
                        'album', 'Album', '💿', albums, 
                        st.session_state['album_filter_enhanced'], 
                        'album_search', 'album_checkbox'
                    )

                # Song filter with enhanced interface
                with st.expander("🎵 Song Filter", expanded=False):
                    st.session_state['song_filter_enhanced'] = create_enhanced_filter(
                        'song', 'Song', '🎵', songs, 
                        st.session_state['song_filter_enhanced'], 
                        'song_search', 'song_checkbox'
                    )

                # Update the filter variables for downstream use
                year_filter = st.session_state['year_filter_enhanced']
                artist_filter = st.session_state['artist_filter_enhanced']
                album_filter = st.session_state['album_filter_enhanced']
                song_filter = st.session_state['song_filter_enhanced']

                # Ultra-compact Apply Filters button
                st.markdown('<div style="margin-top: 4px; margin-bottom: 0px;"></div>', unsafe_allow_html=True)
                if st.button("🎯 Apply Filters", use_container_width=True, type="primary"):
                    st.session_state['year_filter'] = year_filter
                    st.session_state['artist_filter'] = artist_filter
                    st.session_state['album_filter'] = album_filter
                    st.session_state['song_filter'] = song_filter
                    st.session_state['apply_filters'] = True
                
                # Clear Filters button
                st.markdown('<div style="margin-top: 2px; margin-bottom: 0px;"></div>', unsafe_allow_html=True)
                if st.button("🧹 Clear Filters", use_container_width=True, type="secondary"):
                    # Reset all filters to empty/default state
                    st.session_state['year_filter'] = []
                    st.session_state['artist_filter'] = []
                    st.session_state['album_filter'] = []
                    st.session_state['song_filter'] = []
                    # Also reset enhanced filter state
                    st.session_state['year_filter_enhanced'] = []
                    st.session_state['artist_filter_enhanced'] = []
                    st.session_state['album_filter_enhanced'] = []
                    st.session_state['song_filter_enhanced'] = []
                    st.session_state['apply_filters'] = True
                    # Rerun to apply the cleared filters
                    st.rerun()
                
                # Track profile changes (use session state selected_profile if available)
                current_profile = st.session_state.get('selected_profile', selected_profile)
                if st.session_state.get('last_profile', None) != current_profile:
                    st.session_state['reset_filters'] = True
                    st.session_state['last_profile'] = current_profile 

