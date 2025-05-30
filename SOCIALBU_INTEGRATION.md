# SocialBu Instagram Posting Integration

This document explains the updated SocialBu integration that follows the official SocialBu API documentation for Instagram posting.

## Key Changes Made

### 1. Authentication Flow
- **Before**: Used API token directly
- **After**: Proper email/password authentication to get auth token
- **Method**: `authenticate(email, password)` returns access token

### 2. Media Upload Process
The SocialBu API requires a 3-step process for media uploads:

#### Step 1: Initialize Upload
```python
upload_result = service.upload_media(file_name, mime_type)
```
Returns:
- `signed_url`: Pre-signed URL for file upload
- `key`: File identifier for status checking
- `url`: Final file URL

#### Step 2: Upload to Signed URL
```python
service.upload_file_to_signed_url(signed_url, file_path, mime_type)
```
Must include headers:
- `Content-Type`: File MIME type
- `Content-Length`: File size in bytes
- `x-amz-acl`: Set to "private"

#### Step 3: Wait for Processing
```python
upload_token = service.check_media_status(key)
```
Poll until you get an `upload_token` - this is required for posting.

### 3. Instagram Post Structure
Updated to match the `InstagramPostRequest` schema:

```python
post_data = {
    "accounts": [account_ids],  # Array of account IDs
    "content": caption,
    "publish_at": "2025-04-14 15:30:00",  # Y-m-d H:i:s format (UTC)
    "existing_attachments": [
        {"upload_token": "token_from_media_upload"}
    ],
    "options": {
        "post_as_reel": True,      # For video posts
        "post_as_story": True,     # For story posts
        "comment": "First comment" # Optional
    }
}
```

## New Classes

### `InstagramPostingWorkflow`
Complete workflow handler that manages the entire process:

```python
from scraper.services import InstagramPostingWorkflow

# Initialize with credentials
workflow = InstagramPostingWorkflow(
    email="your_email@socialbu.com",
    password="your_password"
)

# Post a video
result = workflow.post_video_to_instagram(
    account_ids=[12345, 67890],
    video_file_path="/path/to/video.mp4",
    caption="Check out this video! #instagram",
    publish_at="2025-04-14 15:30:00",  # Optional
    post_as_reel=True,
    post_as_story=False
)

# Post an image
result = workflow.post_image_to_instagram(
    account_ids=[12345],
    image_file_path="/path/to/image.jpg",
    caption="Beautiful photo! #photography",
    post_as_story=False
)
```

### Updated `SocialBuService`
Enhanced with proper API methods:

- `authenticate(email, password)` - Get auth token
- `upload_media(file_name, mime_type)` - Initialize upload
- `upload_file_to_signed_url()` - Upload file
- `check_media_status(key)` - Get upload token
- `schedule_instagram_post()` - Create Instagram post

## Required Configuration

### 1. Environment Variables
Update your `.env` file:
```env
# SocialBu credentials (not API token anymore)
SOCIALBU_EMAIL=your_email@example.com
SOCIALBU_PASSWORD=your_password

# OR if you have an API token for authentication bypass
SOCIALBU_API_TOKEN=your_api_token
```

### 2. Account IDs
You need your Instagram account IDs from SocialBu dashboard:
1. Log into SocialBu
2. Go to Connected Accounts
3. Note the ID numbers for your Instagram accounts
4. Use these in the `account_ids` parameter

## Instagram-Specific Features

### Video Posts
```python
options = {
    "post_as_reel": True,           # Post as Instagram Reel
    "post_as_story": False,         # Don't post as story
    "share_reel_to_feed": True,     # Share reel to main feed
    "comment": "First comment!",    # Add initial comment
    "thumbnail": {                  # Custom thumbnail (optional)
        "upload_token": "thumb_token"
    }
}
```

### Image Posts
```python
options = {
    "post_as_story": True,         # Post as Instagram Story
    "comment": "Check this out!"   # Add initial comment
}
```

## Error Handling

The integration includes comprehensive error handling:

```python
result = workflow.post_video_to_instagram(...)

if result["success"]:
    print(f"✅ Post created successfully!")
    print(f"Posts: {result['posts']}")
else:
    print(f"❌ Error: {result['error']}")
```

Common errors:
- Authentication failure
- Media upload timeout
- Invalid account IDs
- File format not supported
- API rate limits

## Best Practices

### 1. File Formats
- **Videos**: MP4 format recommended
- **Images**: JPG/JPEG or PNG
- **Max sizes**: Check SocialBu limits

### 2. Scheduling
- Use UTC timezone for `publish_at`
- Format: "YYYY-MM-DD HH:MM:SS"
- Leave `None` for immediate posting

### 3. Captions
- Include relevant hashtags
- Keep within Instagram limits
- Use emojis for engagement

### 4. Rate Limiting
- Don't post too frequently
- SocialBu has API rate limits
- Implement delays between posts

## Migration from Old Code

If you have existing code using the old method:

### Before:
```python
service = SocialBuService()
result = service.schedule_post(
    account_id=12345,
    video_url="http://example.com/video.mp4",
    caption="Caption",
    schedule_time="2025-04-14 15:30:00"
)
```

### After:
```python
workflow = InstagramPostingWorkflow(
    email="your_email@socialbu.com",
    password="your_password"
)
result = workflow.post_video_to_instagram(
    account_ids=[12345],
    video_file_path="/local/path/to/video.mp4",
    caption="Caption",
    publish_at="2025-04-14 15:30:00"
)
```

## Additional SocialBu Features

The API also supports:

### Content Generation
```python
service = SocialBuService()
service.authenticate(email, password)

# Generate AI content
content_data = {
    "type": "instagram_caption",
    "topic": "your topic here",
    "acccount_id": 12345
}
# Call /generated_content endpoint
```

### Account Management
```python
# Get connected accounts
# Call /accounts endpoint

# Connect new accounts
# Call /accounts POST endpoint
```

### Analytics
```python
# Get post metrics
# Call /insights/posts/metrics endpoint

# Get account metrics  
# Call /insights/accounts/metrics endpoint
```

## Testing

Use the provided `example_usage.py` file to test your integration:

```bash
python example_usage.py
```

Remember to update the credentials and file paths in the example before running. 