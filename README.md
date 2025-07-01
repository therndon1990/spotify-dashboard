# 🎵 Spotify Data Analytics Dashboard

A comprehensive, interactive dashboard for analyzing your personal Spotify listening data. Built with Streamlit, this tool provides deep insights into your music habits, preferences, and listening patterns over time.

![Spotify Dashboard](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Polars](https://img.shields.io/badge/Polars-CD792C?style=for-the-badge&logo=polars&logoColor=white)

## 🚀 **Live Demo**

**[🔗 Access the Dashboard Here](https://your-app-name.streamlit.app)** *(Link will be provided after deployment)*

## ✨ **Features**

### 📊 **Comprehensive Analytics**
- **Listening Time Trends** - Monthly patterns and yearly analysis
- **Top Artists, Albums & Songs** - All-time favorites and yearly breakdowns
- **Artist Loyalty Analysis** - How long you stick with artists
- **Playlist Analytics** - Top playlists by minutes played
- **Cross-Playlist Song Analysis** - Songs appearing in multiple playlists

### 🔍 **Advanced Filtering**
- **Smart Search Interface** - Type-to-search across all filters
- **Checkbox Selection** - Easy multi-select with bulk operations
- **Real-time Filtering** - Instant results across all visualizations
- **Complete Data Access** - No sampling, all your data available

### 🎛️ **Filter Options**
- **Years** - Filter by specific years or ranges
- **Artists** - Search and select from all your artists
- **Albums** - Filter by specific albums
- **Songs** - Find and analyze specific tracks

### 📈 **Visualizations**
- Interactive charts powered by Plotly
- Spotify-themed dark UI with signature green accents
- Responsive design for all screen sizes
- Professional data presentation

## 📦 **What You Need**

To use this dashboard, you'll need your personal Spotify data:

### **Required Files:**
1. **Spotify Extended Streaming History** 
   - Files: `StreamingHistory_music_0.json`, `StreamingHistory_music_1.json`, etc.
   - Contains: Detailed listening data with timestamps, duration, and metadata

2. **Spotify Account Data**
   - Files: `Userdata.json`, `YourLibrary.json`, `Playlist1.json`, etc.
   - Contains: Profile info, saved music, playlists, and account details

### **How to Get Your Data:**
1. Go to [Spotify Privacy Settings](https://www.spotify.com/account/privacy/)
2. Request "Extended streaming history" 
3. Wait for email (can take up to 30 days)
4. Download and extract all JSON files

## 🏃‍♂️ **Quick Start**

### **Online Version (Recommended)**
1. Visit the [live dashboard](https://your-app-name.streamlit.app)
2. Create a new profile
3. Upload your Spotify JSON files
4. Start exploring your music data!

### **Local Installation**
```bash
# Clone the repository
git clone https://github.com/yourusername/spotify-dashboard.git
cd spotify-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## 📖 **How to Use**

### **1. Create a Profile**
- Choose "Create a Profile & Upload New Spotify Data"
- Enter a profile name
- Click "Save"

### **2. Upload Your Data**
- Upload all your Spotify JSON files
- The app processes: streaming history, playlists, account data, library data
- Wait for processing to complete

### **3. Explore Your Data**
- Use the enhanced filters to focus on specific time periods, artists, or songs
- All visualizations update in real-time based on your filters
- Search functionality makes it easy to find specific artists or songs

### **4. Filter Options**
- **📅 Year Filter**: Select specific years or ranges
- **🎤 Artist Filter**: Search and select your favorite artists  
- **💿 Album Filter**: Filter by specific albums
- **🎵 Song Filter**: Find and analyze specific tracks

## 🛠️ **Technical Details**

### **Built With:**
- **Streamlit** - Web application framework
- **Polars** - High-performance data processing
- **Plotly** - Interactive visualizations
- **Pandas** - Data manipulation
- **Python 3.8+** - Core language

### **Performance Features:**
- **Ultra-fast loading** - Optimized for datasets with millions of records
- **Efficient filtering** - Complete data access without sampling
- **Smart caching** - Session-based performance optimization
- **Responsive UI** - Works on desktop and mobile

### **Data Processing:**
- Handles multiple file formats and structures
- Comprehensive data validation and cleaning
- Time-based analysis with multiple timestamp formats
- Enhanced metadata extraction

## 🔒 **Privacy & Security**

- **Your data stays private** - All processing happens in your browser session
- **No data persistence** - Data is cleared when you close the browser
- **Local processing** - No data sent to external servers
- **Open source** - Full transparency in data handling

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.

### **Development Setup:**
```bash
git clone https://github.com/yourusername/spotify-dashboard.git
cd spotify-dashboard
pip install -r requirements.txt
streamlit run app.py
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 **Support**

- **Issues**: Report bugs or request features in [GitHub Issues](https://github.com/yourusername/spotify-dashboard/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/yourusername/spotify-dashboard/discussions)

## 🙏 **Acknowledgments**

- Spotify for providing comprehensive data export options
- Streamlit team for the amazing framework
- Polars team for high-performance data processing

---

**Made with ❤️ for music data enthusiasts** 