import os
import logging
import time
import re
import json
from urllib.parse import quote_plus
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key_123")

# Enable CORS for public API usage
CORS(app, origins="*", methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"])

# API key validation
VALID_API_KEY = os.environ.get("API_KEY", "my_secure_key_123")

# Base domain for stream URLs
BASE_DOMAIN = os.environ.get("BASE_DOMAIN", "your-app-name.herokuapp.com")

def parse_duration(duration_str):
    """Parse YouTube duration string to seconds"""
    if not duration_str:
        return 0
    
    try:
        parts = duration_str.split(':')
        if len(parts) == 1:
            return int(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            return 0
    except (ValueError, IndexError):
        return 0

def parse_views(views_str):
    """Parse YouTube views string to integer"""
    if not views_str:
        return 0
    
    try:
        views_clean = views_str.lower().replace('views', '').replace(',', '').strip()
        
        if 'k' in views_clean:
            return int(float(views_clean.replace('k', '')) * 1000)
        elif 'm' in views_clean:
            return int(float(views_clean.replace('m', '')) * 1000000)
        elif 'b' in views_clean:
            return int(float(views_clean.replace('b', '')) * 1000000000)
        else:
            return int(views_clean)
    except (ValueError, AttributeError):
        return 0

def is_live_stream(title, duration):
    """Detect if the video is a live stream"""
    if not title:
        return False
    
    live_indicators = ['live', 'streaming', 'stream', '🔴', 'ao vivo', 'en vivo', 'direct']
    title_lower = title.lower()
    
    for indicator in live_indicators:
        if indicator in title_lower:
            return True
    
    if duration == 0 or duration > 86400:
        return True
    
    return False

def search_youtube_sync(query, limit=1):
    """Perform YouTube search using web scraping"""
    try:
        start_time = time.time()
        
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        script_tags = soup.find_all('script')
        video_data = None
        
        for script in script_tags:
            if script.string and 'var ytInitialData' in script.string:
                script_content = script.string
                start_idx = script_content.find('{')
                end_idx = script_content.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = script_content[start_idx:end_idx]
                    try:
                        data = json.loads(json_str)
                        video_data = extract_video_from_data(data, limit)
                        break
                    except json.JSONDecodeError:
                        continue
        
        search_time = time.time() - start_time
        logger.info(f"YouTube search completed in {search_time:.3f}s")
        
        return video_data
    except Exception as e:
        logger.error(f"YouTube search error: {str(e)}")
        return None

def extract_video_from_data(data, limit=1):
    """Extract video information from YouTube's initial data"""
    try:
        contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
        
        videos = []
        for section in contents:
            if 'itemSectionRenderer' in section:
                items = section['itemSectionRenderer'].get('contents', [])
                for item in items:
                    if 'videoRenderer' in item:
                        video_info = item['videoRenderer']
                        
                        video_id = video_info.get('videoId', '')
                        title = video_info.get('title', {}).get('runs', [{}])[0].get('text', '')
                        
                        duration_info = video_info.get('lengthText', {})
                        duration_text = duration_info.get('simpleText', '0:00') if duration_info else '0:00'
                        
                        channel_info = video_info.get('ownerText', {}).get('runs', [{}])[0]
                        channel_name = channel_info.get('text', 'Unknown Channel') if channel_info else 'Unknown Channel'
                        
                        view_info = video_info.get('viewCountText', {})
                        view_text = view_info.get('simpleText', '0 views') if view_info else '0 views'
                        
                        videos.append({
                            'id': video_id,
                            'title': title,
                            'duration': duration_text,
                            'channel': {'name': channel_name},
                            'viewCount': {'text': view_text}
                        })
                        
                        if len(videos) >= limit:
                            break
                            
                if len(videos) >= limit:
                    break
        
        return {'result': videos} if videos else None
    except Exception as e:
        logger.error(f"Data extraction error: {str(e)}")
        return None

def extract_video_metadata(video_data, video_param=False):
    """Extract and format video metadata from search result"""
    try:
        video_id = video_data.get('id', '')
        title = video_data.get('title', '')
        duration_str = video_data.get('duration', '0:00')
        channel = video_data.get('channel', {}).get('name', 'Unknown Channel')
        views_str = video_data.get('viewCount', {}).get('text', '0 views')
        
        duration = parse_duration(duration_str)
        views = parse_views(views_str)
        
        thumbnail_url = f"https://i.ytimg.com/vi_webp/{video_id}/maxresdefault.webp"
        youtube_link = f"https://youtube.com/watch?v={video_id}"
        stream_url = f"http://{BASE_DOMAIN}/stream/{video_id}"
        
        stream_type = "Video" if video_param else "Audio"
        is_live = is_live_stream(title, duration)
        
        return {
            "id": video_id,
            "title": title,
            "duration": duration,
            "link": youtube_link,
            "channel": channel,
            "views": views,
            "thumbnail": thumbnail_url,
            "stream_url": stream_url,
            "stream_type": stream_type,
            "is_live": is_live
        }
    
    except Exception as e:
        logger.error(f"Metadata extraction error: {str(e)}")
        return None

@app.route('/youtube', methods=['GET', 'POST'])
def youtube_search():
    """YouTube search endpoint"""
    try:
        start_time = time.time()
        
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '')
            video_param = data.get('video', False)
            api_key = data.get('api_key', '')
        else:
            query = request.args.get('query', '')
            video_param = request.args.get('video', '').lower() in ['true', '1', 'yes']
            api_key = request.args.get('api_key', '')
        
        if not query:
            return jsonify({"error": "Missing required parameter: query"}), 400
        
        if not api_key:
            return jsonify({"error": "Missing required parameter: api_key"}), 400
        
        if api_key != VALID_API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        
        logger.info(f"Processing YouTube search: '{query}' (video={video_param})")
        
        search_result = search_youtube_sync(query, limit=1)
        
        if not search_result:
            return jsonify({"error": "No results found for the given query"}), 404
        
        results = search_result.get('result', [])
        if not results:
            return jsonify({"error": "No videos found for the given query"}), 404
        
        video_data = results[0]
        metadata = extract_video_metadata(video_data, video_param)
        
        if not metadata:
            return jsonify({"error": "Failed to extract video metadata"}), 500
        
        total_time = time.time() - start_time
        metadata['response_time'] = round(total_time, 3)
        
        return jsonify(metadata), 200
    
    except Exception as e:
        logger.error(f"YouTube search endpoint error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "YouTube Search API",
        "version": "1.0.0",
        "timestamp": time.time()
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API documentation"""
    return jsonify({
        "message": "YouTube Search and Stream API",
        "version": "1.0.0",
        "endpoints": {
            "/youtube": {
                "methods": ["GET", "POST"],
                "parameters": {
                    "query": "string (required) - Search query",
                    "video": "boolean (optional) - Video stream type, default: false (audio)",
                    "api_key": "string (required) - API authentication key"
                },
                "description": "Search YouTube and get metadata with stream URLs"
            },
            "/health": {
                "methods": ["GET"],
                "description": "Health check endpoint"
            }
        },
        "example_usage": {
            "curl_get": f"curl '{request.host_url}youtube?query=song&video=false&api_key=YOUR_API_KEY'",
            "curl_post": f"curl -X POST {request.host_url}youtube -H 'Content-Type: application/json' -d '{{\"query\":\"song\",\"video\":false,\"api_key\":\"YOUR_API_KEY\"}}'"
        }
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)