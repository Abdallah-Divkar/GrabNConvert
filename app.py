import io
import os
import zipfile
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import re
import random
import time
import yt_dlp
from googleapiclient.discovery import build
from flask import url_for, jsonify
from flask import flash
from flask import Flask, request, render_template, flash, redirect, send_file
from downloader import download_video, download_audio
from converter import video_to_audio, audio_to_wav, convert_image_format

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'YOUTUBE_API_KEY')

class QuotaManager:
    def __init__(self, daily_limit=10000):
        self.daily_limit = daily_limit
        self.quota_file = 'quota_usage.json'
        self.cache_file = 'video_cache.json'
        self.load_quota_data()
        self.load_cache()
    
    def load_quota_data(self):
        """Load quota usage from file"""
        try:
            if os.path.exists(self.quota_file):
                with open(self.quota_file, 'r') as f:
                    data = json.load(f)
                    today = datetime.now().strftime('%Y-%m-%d')
                    if data.get('date') == today:
                        self.used_quota = data.get('used', 0)
                    else:
                        self.used_quota = 0  # Reset for new day
            else:
                self.used_quota = 0
        except:
            self.used_quota = 0
    
    def save_quota_data(self):
        """Save quota usage to file"""
        data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'used': self.used_quota
        }
        with open(self.quota_file, 'w') as f:
            json.dump(data, f)
    
    def load_cache(self):
        """Load cached video data"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            else:
                self.cache = {}
        except:
            self.cache = {}
    
    def save_cache(self):
        """Save cache to file"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def can_use_api(self):
        """Check if we can make API calls"""
        return self.used_quota < self.daily_limit
    
    def use_quota(self, amount=1):
        """Record API usage"""
        self.used_quota += amount
        self.save_quota_data()
    
    def get_remaining_quota(self):
        """Get remaining API calls for today"""
        return max(0, self.daily_limit - self.used_quota)

class YouTubeDownloader:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.youtube_api = None
        self.quota_manager = QuotaManager()
        
        # Initialize YouTube API if key exists
        if self.api_key:
            try:
                self.youtube_api = build('youtube', 'v3', developerKey=self.api_key)
            except Exception as e:
                print(f"YouTube API initialization failed: {e}")
        
        # Enhanced yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'sleep_interval': 5,
            'max_sleep_interval': 15,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'force_ipv4': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['hls', 'dash'],
                }
            }
        }
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_metadata(self, video_id):
        """Get video metadata from YouTube API with caching"""
        # Check cache first
        if video_id in self.quota_manager.cache:
            cached_data = self.quota_manager.cache[video_id]
            # Check if cache is still valid (24 hours)
            cache_time = datetime.fromisoformat(cached_data.get('cached_at', '2000-01-01'))
            if datetime.now() - cache_time < timedelta(hours=24):
                return cached_data['data']
        
        # Check if we can use API
        if not self.youtube_api or not self.quota_manager.can_use_api():
            return None
        
        try:
            request = self.youtube_api.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            )
            response = request.execute()
            self.quota_manager.use_quota(1)  # Record API usage
            
            if response['items']:
                video = response['items'][0]
                metadata = {
                    'id': video_id,
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'][:500] + '...',  # Truncate
                    'duration': self.parse_duration(video['contentDetails']['duration']),
                    'view_count': video['statistics'].get('viewCount', 0),
                    'thumbnail': video['snippet']['thumbnails']['high']['url'],
                    'channel': video['snippet']['channelTitle'],
                    'upload_date': video['snippet']['publishedAt'][:10],  # Just date
                    'available': True
                }
                
                # Cache the result
                self.quota_manager.cache[video_id] = {
                    'data': metadata,
                    'cached_at': datetime.now().isoformat()
                }
                self.quota_manager.save_cache()
                
                return metadata
        except Exception as e:
            print(f"API Error: {e}")
        
        return None
    
    def parse_duration(self, duration):
        """Parse ISO 8601 duration to readable format"""
        # Simple parser for PT1H30M45S format
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours, minutes, seconds = match.groups()
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0
            
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        return "Unknown"
    
    def download_audio(self, url):
        """Download audio with enhanced error handling"""
        try:
            # Add random delay to avoid pattern detection
            time.sleep(random.uniform(3, 8))
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return {
                    "success": True,
                    "file_path": ydl.prepare_filename(info),
                    "title": info.get('title', 'Unknown')
                }
        except Exception as e:
            return {"error": f"Download failed: {str(e)}"}

# Initialize the downloader
downloader = YouTubeDownloader()


BASE_OUTPUT_DIR = os.environ.get('BASE_OUTPUT_DIR', 'output')
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

for directory in ['uploads', 'output']:
    os.makedirs(directory, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        
        if not url:
            flash('Please enter a YouTube URL', 'error')
            return redirect(url_for('index'))
        
        # Extract video ID
        video_id = downloader.extract_video_id(url)
        if not video_id:
            flash('Invalid YouTube URL. Please check the URL and try again.', 'error')
            return redirect(url_for('index'))
        
        # Try to get metadata from API first
        metadata = downloader.get_video_metadata(video_id)
        
        if metadata:
            # Show confirmation page with video info
            return render_template('confirm.html', 
                                 metadata=metadata, 
                                 url=url,
                                 quota_remaining=downloader.quota_manager.get_remaining_quota())
        else:
            # Fallback: proceed directly to download
            flash('Could not fetch video info, proceeding with download...', 'warning')
            return redirect(url_for('download_direct', url=url))
    
    # GET request - show main page with quota info
    return render_template('index.html', 
                         quota_remaining=downloader.quota_manager.get_remaining_quota())

@app.route('/confirm/<path:url>')
def confirm_download(url):
    """Show confirmation page with video details"""
    video_id = downloader.extract_video_id(url)
    metadata = downloader.get_video_metadata(video_id)
    
    if metadata:
        return render_template('confirm.html', metadata=metadata, url=url)
    else:
        flash('Video information not available', 'error')
        return redirect(url_for('index'))

@app.route('/download', methods=['POST'])
def download():
    """Handle confirmed download"""
    url = request.form.get('url')
    if not url:
        flash('No URL provided', 'error')
        return redirect(url_for('index'))
    
    # Show loading page
    video_id = downloader.extract_video_id(url)
    metadata = downloader.get_video_metadata(video_id)
    
    return render_template('downloading.html', 
                         metadata=metadata, 
                         url=url)

@app.route('/download_direct/<path:url>')
def download_direct(url):
    """Direct download without confirmation"""
    return render_template('downloading.html', 
                         metadata={'title': 'Preparing download...'}, 
                         url=url)

@app.route('/api/download', methods=['POST'])
def api_download():
    """API endpoint for actual download process"""
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    # Perform download
    result = downloader.download_audio(url)
    
    if 'error' in result:
        return jsonify(result), 400
    
    # Return success with file info
    return jsonify({
        "success": True,
        "message": "Download completed",
        "filename": os.path.basename(result['file_path']),
        "title": result['title']
    })

@app.route('/status')
def status():
    """API endpoint to check system status"""
    return jsonify({
        "quota_remaining": downloader.quota_manager.get_remaining_quota(),
        "quota_used": downloader.quota_manager.used_quota,
        "api_available": downloader.youtube_api is not None,
        "cache_size": len(downloader.quota_manager.cache)
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500


@app.context_processor
def inject_globals():
    """Make variables available to all templates"""
    return {
        'quota_remaining': downloader.quota_manager.get_remaining_quota(),
        'api_available': downloader.youtube_api is not None
    }

if __name__ == '__main__':
    # Create downloads directory if it doesn't exist
    os.makedirs('downloads', exist_ok=True)
    
    # Run the app
    app.run(debug=True)