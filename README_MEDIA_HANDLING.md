# 🎬 Enhanced Media Handling System

## Overview

The Beampage workflow now includes a robust and reliable media handling system that seamlessly integrates video uploads with the SocialBu API. This system handles the complete workflow from downloading Instagram videos to scheduling them as posts with proper attribution.

## 🚀 Key Features

### ✅ Complete Video Processing Pipeline
- **Video Download**: Downloads videos from Instagram URLs to temporary files
- **Upload Processing**: 3-step upload process as required by SocialBu API
- **Strategic Scheduling**: Posts at optimal times (10am, 2pm, 6pm)
- **Instagram Reels**: Automatically posts videos as Instagram Reels
- **Attribution**: Adds proper attribution to original creators

### ✅ Robust Error Handling
- **Automatic Retry**: Exponential backoff for failed operations
- **Graceful Degradation**: Posts without media if upload fails
- **Temporary File Cleanup**: Automatic cleanup of downloaded files
- **Comprehensive Logging**: Detailed progress and error reporting
- **Timeout Protection**: Configurable timeouts for all operations

### ✅ SocialBu API Integration
- **3-Step Upload Process**: 
  1. Initialize media upload with metadata
  2. Upload file to signed URL
  3. Wait for processing completion
- **Upload Token Management**: Proper handling of upload tokens
- **Status Monitoring**: Real-time upload status checking

## 📖 How It Works

### 1. Video Processing Workflow

```python
# The complete workflow when scheduling a post with video
result = service.schedule_post_with_strategic_timing(
    content="Amazing content! 🎬✨\n\nOriginal by: @creator",
    accounts=[account_id],
    video_url="https://instagram.com/p/ABC123/",
    media_options={
        "post_as_reel": True,
        "share_reel_to_feed": True,
        "comment": "Reposted with permission"
    }
)
```

### 2. Behind the Scenes Process

```
1. Download video from Instagram URL
   ├── Create temporary file
   ├── Stream download with progress tracking
   └── Detect MIME type

2. Upload to SocialBu
   ├── Initialize upload (POST /upload_media)
   ├── Upload to signed URL (PUT request)
   └── Wait for processing completion

3. Schedule Post
   ├── Get next strategic time slot
   ├── Create post with upload token
   └── Schedule via SocialBu API
```

## 🛠️ Usage Examples

### Basic Usage (Automated Workflow)

```bash
# Run the automated workflow for a specific page
python -m scraper.workflow dobermanzone

# List available configurations
python -m scraper.workflow list
```

### Manual Posting with Media

```python
from scraper.services import SocialBuService

service = SocialBuService()

# Schedule a post with video
result = service.schedule_post_with_strategic_timing(
    content="Check out this amazing video! 🎬✨\n\nOriginal by: @example_creator",
    accounts=[12345],  # Your Instagram account ID
    video_url="https://instagram.com/p/VIDEO_POST_ID/",
    media_options={
        "post_as_reel": True,
        "share_reel_to_feed": True
    }
)

print(f"Post scheduled: {result['success']}")
if result['success']:
    print(f"Scheduled for: {result['schedule_time']}")
```

### Testing Media Upload

```python
# Test the media upload functionality
from scraper.services import SocialBuService

service = SocialBuService()

# Test video download
result = service.download_video("https://example.com/video.mp4")
if result['success']:
    print(f"Downloaded to: {result['file_path']}")
    print(f"MIME type: {result['mime_type']}")
```

## ⚙️ Configuration

### Required Environment Variables

```python
# In config.py
SOCIALBU_API_TOKEN = "your_socialbu_api_token_here"
```

### Page Configuration

```python
# In config.py
PAGES = {
    "your_page": {
        "ig_account": "your_instagram_username",
        "competitors": ["competitor1", "competitor2"],
        "max_posts": 10,
        "top_posts": 3
    }
}
```

### Media Options

```python
media_options = {
    "post_as_reel": True,          # Post video as Instagram Reel
    "share_reel_to_feed": True,    # Share Reel to main feed
    "comment": "Custom comment",   # Optional comment
    "tags": ["tag1", "tag2"]       # Optional tags
}
```

## 🧪 Testing

### Run the Test Suite

```bash
# Test basic media upload functionality
python test_media_upload.py

# Run enhanced workflow demo
python enhanced_workflow_example.py
```

### Test Individual Components

```python
from scraper.services import SocialBuService

service = SocialBuService()

# Test API connection
if service.test_connection():
    print("✅ API connection successful")

# Test strategic scheduling
schedule_info = service.get_strategic_schedule_info()
print(f"Next slot: {schedule_info['next_available_slot']}")

# Test accounts
accounts = service.get_accounts()
print(f"Connected accounts: {len(accounts.get('accounts', []))}")
```

## 🔧 Troubleshooting

### Common Issues

**1. API Connection Failed**
```
❌ SocialBu API connection failed
```
- Check your `SOCIALBU_API_TOKEN` in `config.py`
- Verify the token is active in your SocialBu dashboard

**2. No Instagram Accounts Found**
```
No Instagram accounts found
```
- Connect your Instagram account in the SocialBu dashboard
- Ensure the account has proper permissions

**3. Video Download Failed**
```
Failed to download video from URL
```
- Check if the Instagram post URL is valid
- Ensure the post contains a video (not just images)
- Try a different video URL

**4. Upload Processing Timeout**
```
Upload processing timed out
```
- Large videos may take longer to process
- Check your internet connection
- Try with a smaller video file

### Debug Mode

Enable detailed logging by setting the logging level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Strategic Scheduling

### Optimal Posting Times

The system uses strategic posting times based on engagement data:
- **10:00 AM** - Morning engagement peak
- **2:00 PM** - Afternoon active users
- **6:00 PM** - Evening engagement surge

### Scheduling Logic

```python
# Get next available strategic slot
next_slot = service.strategic_scheduler.get_next_available_slot()

# Check current scheduling status
schedule_info = service.get_strategic_schedule_info()
print(f"Scheduled slots: {len(schedule_info['scheduled_slots'])}")
```

## 🔄 Error Recovery

### Automatic Retry Logic

The system implements intelligent retry mechanisms:

```python
# Automatic retry with exponential backoff
for attempt in range(max_retries):
    try:
        result = upload_operation()
        break
    except Exception as e:
        wait_time = (2 ** attempt) + random.uniform(0, 1)
        time.sleep(wait_time)
```

### Graceful Degradation

If video upload fails, the system will:
1. Log the error details
2. Continue with text-only post
3. Notify about the media upload failure
4. Clean up temporary files

## 📁 File Structure

```
beampage/
├── scraper/
│   ├── services.py          # Enhanced SocialBu service with media handling
│   ├── workflow.py          # Updated workflow with media integration
│   └── config.py           # Configuration settings
├── test_media_upload.py     # Media upload testing script
├── enhanced_workflow_example.py  # Comprehensive demo
└── README_MEDIA_HANDLING.md # This documentation
```

## 🎯 Best Practices

### 1. Content Attribution
Always provide proper attribution:
```python
content = f"Amazing content! 🎬✨\n\nOriginal by: @{original_creator}"
```

### 2. Strategic Timing
Use strategic scheduling for optimal engagement:
```python
# Let the system choose optimal timing
result = service.schedule_post_with_strategic_timing(...)
```

### 3. Error Handling
Always check for success and handle failures:
```python
result = service.schedule_post_with_strategic_timing(...)
if result['success']:
    print(f"✅ Post scheduled for: {result['schedule_time']}")
else:
    print(f"❌ Failed to schedule: {result['error']}")
```

### 4. Resource Management
The system automatically handles cleanup, but you can verify:
```python
# Temporary files are automatically cleaned up
# No manual intervention required
```

## 🚀 Advanced Usage

### Custom Media Options

```python
advanced_options = {
    "post_as_reel": True,
    "share_reel_to_feed": True,
    "reel_cover_image": "custom_thumbnail.jpg",
    "caption": "Custom caption for the reel",
    "location": "Location Name",
    "tags": ["viral", "trending", "content"]
}
```

### Batch Processing

```python
# Process multiple posts with media
posts = [
    {"content": "Post 1", "video_url": "url1"},
    {"content": "Post 2", "video_url": "url2"},
    {"content": "Post 3", "video_url": "url3"}
]

for post in posts:
    result = service.schedule_post_with_strategic_timing(
        content=post["content"],
        accounts=accounts,
        video_url=post["video_url"]
    )
    print(f"Post scheduled: {result['success']}")
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run the test scripts to verify functionality
3. Check the SocialBu API documentation
4. Ensure your API token and account connections are valid

---

*This enhanced media handling system provides a robust, reliable, and user-friendly way to schedule social media posts with video content. The system handles all the complex API interactions, error recovery, and resource management automatically.* 