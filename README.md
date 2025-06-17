# YouTube Search API - Heroku Deployment

A high-performance Flask-based YouTube search API that provides fast metadata extraction with Telegram bot integration support.

## Features

- **Fast YouTube Search**: Returns video metadata in under 1 second
- **REST API**: Clean JSON responses with proper error handling
- **API Key Authentication**: Secure access control
- **CORS Enabled**: Ready for cross-origin requests
- **Production Ready**: Optimized for Heroku deployment
- **Stream URLs**: Generates dummy stream endpoints for bot integration
- **Live Stream Detection**: Identifies live streams automatically

## API Endpoints

### Search YouTube Videos
```
GET/POST /youtube
```

**Parameters:**
- `query` (required): Search query string
- `video` (optional): Boolean, true for video stream, false for audio stream (default: false)
- `api_key` (required): API authentication key

**Example Response:**
```json
{
  "id": "AEIVhBS6baE",
  "title": "Gerua - Shah Rukh Khan | Kajol | Dilwale",
  "duration": 288,
  "link": "https://youtube.com/watch?v=AEIVhBS6baE",
  "channel": "Sony Music India",
  "views": 598364676,
  "thumbnail": "https://i.ytimg.com/vi_webp/AEIVhBS6baE/maxresdefault.webp",
  "stream_url": "http://your-app.herokuapp.com/stream/AEIVhBS6baE",
  "stream_type": "Audio",
  "is_live": false,
  "response_time": 0.726
}
```

### Health Check
```
GET /health
```

Returns API status and version information.

## Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo>
cd youtube-api-heroku
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file or set these environment variables:
```
SECRET_KEY=your_secret_key_here
API_KEY=your_api_key_here
BASE_DOMAIN=your-app-name.herokuapp.com
```

### 3. Local Development
```bash
python api.py
```

The API will be available at `http://localhost:5000`

## Heroku Deployment

### Prerequisites
- Heroku CLI installed
- Git repository initialized

### Step 1: Create Heroku App
```bash
heroku create your-app-name
```

### Step 2: Set Environment Variables
```bash
heroku config:set SECRET_KEY=your_secret_key_here
heroku config:set API_KEY=your_secure_api_key
heroku config:set BASE_DOMAIN=your-app-name.herokuapp.com
```

### Step 3: Deploy
```bash
git add .
git commit -m "Initial commit"
git push heroku main
```

### Step 4: Verify Deployment
```bash
heroku logs --tail
heroku open
```

## Usage Examples

### cURL Examples
```bash
# Search for a song (audio stream)
curl "https://your-app.herokuapp.com/youtube?query=hello&video=false&api_key=your_api_key"

# Search for a video (video stream)
curl "https://your-app.herokuapp.com/youtube?query=hello&video=true&api_key=your_api_key"

# POST request
curl -X POST https://your-app.herokuapp.com/youtube \
  -H "Content-Type: application/json" \
  -d '{"query":"hello","video":false,"api_key":"your_api_key"}'
```

### Python Example
```python
import requests

url = "https://your-app.herokuapp.com/youtube"
params = {
    "query": "hello world",
    "video": False,
    "api_key": "your_api_key"
}

response = requests.get(url, params=params)
data = response.json()
print(data)
```

### JavaScript Example
```javascript
const response = await fetch('https://your-app.herokuapp.com/youtube', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'hello world',
    video: false,
    api_key: 'your_api_key'
  })
});

const data = await response.json();
console.log(data);
```

## Telegram Bot Integration

This API is designed to work seamlessly with Telegram music bots using libraries like:
- Pyrogram
- Telethon
- python-telegram-bot
- TgCalls

Example integration:
```python
import requests
from pyrogram import Client, filters

@Client.on_message(filters.command("play"))
async def play_music(client, message):
    query = message.text.split(" ", 1)[1]
    
    # Call your API
    response = requests.get(f"https://your-app.herokuapp.com/youtube", 
                          params={"query": query, "video": False, "api_key": "your_key"})
    
    if response.status_code == 200:
        data = response.json()
        # Use data['stream_url'] for your music player
        await message.reply(f"Playing: {data['title']}")
```

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for sessions
- `API_KEY`: API authentication key
- `BASE_DOMAIN`: Your app's domain for stream URLs
- `PORT`: Port number (automatically set by Heroku)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

### Rate Limiting
The API implements basic rate limiting through Heroku's infrastructure. For additional protection, consider adding:
- Redis-based rate limiting
- IP whitelisting
- Request throttling

## Monitoring and Logs

### View Logs
```bash
heroku logs --tail
```

### Monitor Performance
```bash
heroku ps
heroku top
```

### Health Check
The API includes a health check endpoint at `/health` for monitoring services.

## Troubleshooting

### Common Issues
1. **API Key Errors**: Ensure your API key is correctly set in environment variables
2. **Search Failures**: YouTube may block requests; consider implementing retry logic
3. **Timeout Issues**: Increase worker timeout in Procfile if needed
4. **Memory Issues**: Monitor Heroku metrics and upgrade dyno if necessary

### Debug Mode
For local debugging, set:
```bash
export FLASK_ENV=development
python api.py
```

## Performance Optimization

- Uses web scraping for fastest possible response times
- Implements connection pooling and request optimization
- Minimal dependencies for faster cold starts
- Optimized JSON parsing and data extraction

## Security Considerations

- API key authentication required
- CORS properly configured
- No sensitive data logged
- Input validation and sanitization
- Rate limiting recommended for production

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions:
1. Check the logs: `heroku logs --tail`
2. Verify environment variables: `heroku config`
3. Test locally first: `python api.py`
4. Monitor API health: `curl https://your-app.herokuapp.com/health`

---

**Note**: This API uses web scraping techniques and should be used responsibly in accordance with YouTube's terms of service.