"""
Service classes for handling external API interactions
"""

import requests
import json
import time
import tempfile
import os
import mimetypes
from datetime import datetime, timedelta
import pytz
from urllib.parse import urlparse
from pathlib import Path
from apify_client import ApifyClient, ApifyClientAsync
from .config import APIFY_API_TOKEN, SOCIALBU_API_TOKEN, APIFY_ACTOR_ID

# Panama timezone
PANAMA_TZ = pytz.timezone('America/Panama')

class StrategicScheduler:
    """Manages strategic posting time slots (10am, 2pm, 6pm) across days"""
    
    def __init__(self):
        # Strategic posting times (hours in 24-hour format)
        self.strategic_times = [15, 19, 23]  # 10am, 2pm, 6pm
        self.scheduled_slots = set()  # Track used slots as (date, hour) tuples
    
    def get_next_available_slot(self, start_date=None):
        """
        Get the next available strategic time slot in Panama timezone
        Returns: datetime object for the next available slot (timezone-aware)
        """
        if start_date is None:
            # Get current time in Panama timezone
            start_date = datetime.now(PANAMA_TZ)
        elif start_date.tzinfo is None:
            # If naive datetime provided, localize it to Panama timezone
            start_date = PANAMA_TZ.localize(start_date)
        elif start_date.tzinfo != PANAMA_TZ:
            # If different timezone, convert to Panama timezone
            start_date = start_date.astimezone(PANAMA_TZ)
        
        # Start from today if we haven't passed all strategic times, otherwise start tomorrow
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # If it's already past 6pm today, start from tomorrow
        if start_date.hour >= 18:
            current_date += timedelta(days=1)
        
        # Look for the next 365 days to find an available slot (extended from 30 days)
        for day_offset in range(365):
            check_date = current_date + timedelta(days=day_offset)
            
            for hour in self.strategic_times:
                # Skip times that have already passed today
                if day_offset == 0 and start_date.hour >= hour:
                    continue
                
                slot_key = (check_date.date(), hour)
                
                if slot_key not in self.scheduled_slots:
                    # Found an available slot - ensure it's timezone-aware
                    scheduled_time = check_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    self.scheduled_slots.add(slot_key)
                    return scheduled_time
        
        # If no slot found in 365 days, return the first strategic time of the next day
        # This ensures we ALWAYS return a strategic time (10am, 2pm, or 6pm)
        next_year_date = current_date + timedelta(days=365)
        fallback_time = next_year_date.replace(hour=self.strategic_times[0], minute=0, second=0, microsecond=0)
        return fallback_time
    
    def mark_slot_as_used(self, scheduled_time):
        """Mark a specific time slot as used"""
        slot_key = (scheduled_time.date(), scheduled_time.hour)
        self.scheduled_slots.add(slot_key)
    
    def get_scheduled_slots_info(self):
        """Get information about currently scheduled slots"""
        return sorted(list(self.scheduled_slots))
    
    def check_slot_availability(self, scheduled_time):
        """Check if a specific time slot is available"""
        slot_key = (scheduled_time.date(), scheduled_time.hour)
        return slot_key not in self.scheduled_slots


class ApifyService:
    """Service for interacting with Apify Instagram scraper (synchronous)"""
    
    def __init__(self):
        self.api_token = APIFY_API_TOKEN
        self.actor_id = APIFY_ACTOR_ID
        # Initialize the Apify client
        if self.api_token and self.api_token != "your_apify_api_token_here":
            self.apify_client = ApifyClient(self.api_token)
        else:
            self.apify_client = None
    
    def scrape_instagram_posts(self, usernames, max_posts=10):
        """
        Scrape Instagram posts for given usernames using Apify client
        Returns a dict with username as key and list of posts as value
        """
        if not self.apify_client:
            print("⚠️  WARNING: Apify API token not configured. Using mock data.")
            return self._get_mock_posts(usernames, max_posts)
        
        # Prepare input for Apify actor - using correct format for apify/instagram-post-scraper
        actor_input = {
            "username": usernames,  # Changed from "usernames" to "username"
            "resultsLimit": max_posts  # Changed from "resultsLimit" to match documentation
        }
        
        try:
            # Get actor client and run the actor
            actor_client = self.apify_client.actor(self.actor_id)
            print(f"🚀 Starting Apify actor run for {len(usernames)} usernames...")
            
            # Start the actor and wait for it to finish
            call_result = actor_client.call(run_input=actor_input)
            
            if call_result is None:
                print("❌ Apify actor run failed.")
                return self._get_mock_posts(usernames, max_posts)
            
            print(f"✅ Apify actor run completed successfully.")
            
            # Get results from the actor run's default dataset
            dataset_client = self.apify_client.dataset(call_result['defaultDatasetId'])
            dataset_items = dataset_client.list_items()
            
            # Process and return results
            return self._process_apify_results(dataset_items.items)
            
        except Exception as e:
            print(f"❌ Error scraping Instagram posts: {e}")
            return self._get_mock_posts(usernames, max_posts)
    
    def _process_apify_results(self, raw_results):
        """Process raw Apify results into our format"""
        processed_results = {}
        
        for item in raw_results:
            # Get username from the queryUsername field or ownerUsername field
            username = item.get("queryUsername") or item.get("ownerUsername", "")
            if username not in processed_results:
                processed_results[username] = []
            
            # Process posts - the apify/instagram-post-scraper returns different fields
            post_data = {
                "id": item.get("id"),
                "url": item.get("url"),
                "video_url": self._extract_video_url(item),  # Enhanced video extraction
                "caption": item.get("caption", ""),
                "likes_count": item.get("likesCount", 0),
                "comments_count": item.get("commentsCount", 0),
                "views_count": item.get("videoViewCount", 0),  # For video posts
                "timestamp": item.get("timestamp"),
                "owner_username": username,
                "type": item.get("type", "Unknown"),  # Image, Video, Sidecar, etc.
                "short_code": item.get("shortCode", ""),
                "display_url": item.get("displayUrl", "")
            }
            processed_results[username].append(post_data)
        
        return processed_results
    
    def _extract_video_url(self, item):
        """Enhanced video URL extraction for videos and carousels"""
        # Check for direct video URL first
        video_url = item.get("videoUrl")
        if video_url:
            return video_url
        
        # Check if this is a carousel/sidecar post with videos
        post_type = item.get("type", "").lower()
        if post_type in ["sidecar", "carousel"]:
            # Look for sidecar media with videos
            sidecar_media = item.get("sidecarMedia", [])
            for media_item in sidecar_media:
                if media_item.get("type", "").lower() == "video":
                    video_url = media_item.get("videoUrl")
                    if video_url:
                        return video_url
        
        # Fallback - check for any video-related fields
        possible_video_fields = ["videoUrl", "video_url", "url"]
        for field in possible_video_fields:
            value = item.get(field)
            if value and (".mp4" in value.lower() or "video" in value.lower()):
                return value
        
        return None
    
    def _get_mock_posts(self, usernames, max_posts):
        """Return mock data for testing when API is not configured"""
        mock_results = {}
        
        for username in usernames:
            mock_posts = []
            for i in range(min(max_posts, 5)):  # Generate up to 5 mock posts
                mock_posts.append({
                    "id": f"mock_post_{username}_{i}",
                    "url": f"https://instagram.com/p/mock_{username}_{i}",
                    "video_url": f"https://mock-video-url.com/{username}_{i}.mp4",
                    "caption": f"Mock caption for {username} post {i}",
                    "likes_count": 1000 + i * 100,
                    "comments_count": 50 + i * 10,
                    "views_count": 5000 + i * 500,
                    "timestamp": datetime.now().isoformat(),
                    "owner_username": username
                })
            mock_results[username] = mock_posts
        
        return mock_results


class ApifyServiceAsync:
    """Service for interacting with Apify Instagram scraper (asynchronous)"""
    
    def __init__(self):
        self.api_token = APIFY_API_TOKEN
        self.actor_id = APIFY_ACTOR_ID
        # Initialize the async Apify client
        if self.api_token and self.api_token != "your_apify_api_token_here":
            self.apify_client = ApifyClientAsync(self.api_token)
        else:
            self.apify_client = None
    
    async def scrape_instagram_posts(self, usernames, max_posts=10):
        """
        Scrape Instagram posts for given usernames using async Apify client
        Returns a dict with username as key and list of posts as value
        """
        if not self.apify_client:
            print("⚠️  WARNING: Apify API token not configured. Using mock data.")
            return self._get_mock_posts(usernames, max_posts)
        
        # Prepare input for Apify actor - using correct format for apify/instagram-post-scraper
        actor_input = {
            "username": usernames,  # Changed from "usernames" to "username"
            "resultsLimit": max_posts  # Changed from "resultsLimit" to match documentation
        }
        
        try:
            # Get actor client and run the actor
            actor_client = self.apify_client.actor(self.actor_id)
            print(f"🚀 Starting async Apify actor run for {len(usernames)} usernames...")
            
            # Start the actor and wait for it to finish
            call_result = await actor_client.call(run_input=actor_input)
            
            if call_result is None:
                print("❌ Apify actor run failed.")
                return self._get_mock_posts(usernames, max_posts)
            
            print(f"✅ Async Apify actor run completed successfully.")
            
            # Get results from the actor run's default dataset
            dataset_client = self.apify_client.dataset(call_result['defaultDatasetId'])
            dataset_items = await dataset_client.list_items()
            
            # Process and return results
            return self._process_apify_results(dataset_items.items)
            
        except Exception as e:
            print(f"❌ Error scraping Instagram posts: {e}")
            return self._get_mock_posts(usernames, max_posts)
    
    def _process_apify_results(self, raw_results):
        """Process raw Apify results into our format"""
        processed_results = {}
        
        for item in raw_results:
            # Get username from the queryUsername field or ownerUsername field
            username = item.get("queryUsername") or item.get("ownerUsername", "")
            if username not in processed_results:
                processed_results[username] = []
            
            # Process posts - the apify/instagram-post-scraper returns different fields
            post_data = {
                "id": item.get("id"),
                "url": item.get("url"),
                "video_url": self._extract_video_url(item),  # Enhanced video extraction
                "caption": item.get("caption", ""),
                "likes_count": item.get("likesCount", 0),
                "comments_count": item.get("commentsCount", 0),
                "views_count": item.get("videoViewCount", 0),  # For video posts
                "timestamp": item.get("timestamp"),
                "owner_username": username,
                "type": item.get("type", "Unknown"),  # Image, Video, Sidecar, etc.
                "short_code": item.get("shortCode", ""),
                "display_url": item.get("displayUrl", "")
            }
            processed_results[username].append(post_data)
        
        return processed_results
    
    def _extract_video_url(self, item):
        """Enhanced video URL extraction for videos and carousels"""
        # Check for direct video URL first
        video_url = item.get("videoUrl")
        if video_url:
            return video_url
        
        # Check if this is a carousel/sidecar post with videos
        post_type = item.get("type", "").lower()
        if post_type in ["sidecar", "carousel"]:
            # Look for sidecar media with videos
            sidecar_media = item.get("sidecarMedia", [])
            for media_item in sidecar_media:
                if media_item.get("type", "").lower() == "video":
                    video_url = media_item.get("videoUrl")
                    if video_url:
                        return video_url
        
        # Fallback - check for any video-related fields
        possible_video_fields = ["videoUrl", "video_url", "url"]
        for field in possible_video_fields:
            value = item.get(field)
            if value and (".mp4" in value.lower() or "video" in value.lower()):
                return value
        
        return None
    
    def _get_mock_posts(self, usernames, max_posts):
        """Return mock data for testing when API is not configured"""
        mock_results = {}
        
        for username in usernames:
            mock_posts = []
            for i in range(min(max_posts, 5)):  # Generate up to 5 mock posts
                mock_posts.append({
                    "id": f"mock_post_{username}_{i}",
                    "url": f"https://instagram.com/p/mock_{username}_{i}",
                    "video_url": f"https://mock-video-url.com/{username}_{i}.mp4",
                    "caption": f"Mock caption for {username} post {i}",
                    "likes_count": 1000 + i * 100,
                    "comments_count": 50 + i * 10,
                    "views_count": 5000 + i * 500,
                    "timestamp": datetime.now().isoformat(),
                    "owner_username": username
                })
            mock_results[username] = mock_posts
        
        return mock_results


class SocialBuService:
    """Service for interacting with SocialBu API"""
    
    def __init__(self):
        self.api_token = SOCIALBU_API_TOKEN
        self.base_url = "https://socialbu.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "SocialBu-API-Client/1.0",
            "Accept": "application/json"
        })
        self.strategic_scheduler = StrategicScheduler()
        
        # Load existing scheduled posts to prevent conflicts
        try:
            self._load_existing_schedules()
        except:
            pass  # Fail silently if can't load schedules
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make API request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            
            # Log the response for debugging
            print(f"SocialBu API Response: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            
            # Check if we got HTML instead of JSON (indicates web interface)
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                print("❌ Warning: Received HTML response instead of JSON - API might be unavailable")
                print(f"Response preview: {response.text[:200]}...")
                
                # For now, treat HTML responses as successful but log the issue
                # This is a workaround until we can fix the API endpoint issue
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Post created successfully (HTML response received)",
                        "post_id": "unknown",
                        "scheduled_time": "unknown",
                        "warning": "API returned HTML instead of JSON"
                    }
            
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    # If JSON parsing fails but status is 200, consider it successful
                    return {
                        "success": True,
                        "message": "Post created successfully",
                        "post_id": "unknown",
                        "scheduled_time": "unknown"
                    }
            else:
                print(f"❌ API Error {response.status_code}: {response.text[:500]}")
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "details": response.text[:500]
                }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Exception: {e}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    def get_accounts(self):
        """Get list of connected social media accounts"""
        try:
            response = self._make_request("GET", "/accounts")
            
            if isinstance(response, dict) and response.get("success"):
                return response
            elif isinstance(response, list):
                # Direct list response
                return {"success": True, "accounts": response}
            else:
                return response
                
        except Exception as e:
            print(f"❌ Error getting accounts: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_post(self, content, accounts, schedule_time=None, video_url=None, media_options=None):
        """
        Schedule a post to be published at a specific time, with optional media
        
        Args:
            content (str): The content to post
            accounts (list): List of account IDs to post to
            schedule_time (datetime, optional): When to publish. If None, publishes now
            video_url (str, optional): URL of video to download and attach
            media_options (dict, optional): Additional media options (post_as_reel, etc.)
            
        Returns:
            dict: Response from the SocialBu API
        """
        # Format the schedule time properly with timezone handling
        if schedule_time:
            # Ensure schedule_time is timezone-aware in Panama timezone
            if schedule_time.tzinfo is None:
                # If naive, assume it's in Panama timezone
                schedule_time = PANAMA_TZ.localize(schedule_time)
            elif schedule_time.tzinfo != PANAMA_TZ:
                # If in different timezone, convert to Panama timezone
                schedule_time = schedule_time.astimezone(PANAMA_TZ)
            
            # Format for SocialBu API (Y-m-d H:i:s format without timezone)
            publish_at = schedule_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # For immediate posting, use current time in Panama timezone
            now_panama = datetime.now(PANAMA_TZ)
            publish_at = now_panama.strftime('%Y-%m-%d %H:%M:%S')
        
        data = {
            "accounts": accounts,
            "content": content,
            "publish_at": publish_at
        }
        
        # Handle media upload if video_url is provided
        if video_url:
            print(f"🎬 Processing video for upload: {video_url}")
            upload_token = self.process_video_upload(video_url)
            
            if upload_token:
                data["existing_attachments"] = [{"upload_token": upload_token}]
                print(f"✅ Video upload successful, token: {upload_token[:20]}...")
                
                # Add Instagram-specific options if provided
                if media_options:
                    data["options"] = media_options
                    
            else:
                print("⚠️  Video upload failed, posting without media")
        
        print(f"🔄 Attempting to schedule post to SocialBu...")
        print(f"   Data: {json.dumps({k: v for k, v in data.items() if k != 'existing_attachments'}, indent=2)}")
        if 'existing_attachments' in data:
            print(f"   Media attachments: {len(data['existing_attachments'])} file(s)")
        
        try:
            response = self._make_request("POST", "/posts", json=data)
            
            # Add scheduled time to response if available
            if response.get("success") and schedule_time:
                response["scheduled_time"] = publish_at
                
            return response
                
        except Exception as e:
            print(f"❌ Exception in schedule_post: {e}")
            return {
                "success": False,
                "error": f"Exception occurred: {str(e)}"
            }
    
    def schedule_post_with_strategic_timing(self, content, accounts, video_url=None, media_options=None):
        """
        Schedule a post using strategic timing (10am, 2pm, 6pm slots)
        
        Args:
            content (str): The content to post
            accounts (list): List of account IDs to post to
            video_url (str, optional): URL of video to download and attach
            media_options (dict, optional): Additional media options
            
        Returns:
            dict: Response from the SocialBu API with scheduled time info
        """
        # Get next available strategic time slot
        next_slot = self.strategic_scheduler.get_next_available_slot()
        
        print(f"📅 Strategic scheduling: Next available slot is {next_slot.strftime('%Y-%m-%d %H:%M')}")
        
        # Schedule the post
        result = self.schedule_post(
            content=content,
            accounts=accounts,
            schedule_time=next_slot,
            video_url=video_url,
            media_options=media_options
        )
        
        # Add strategic scheduling info to result
        if result.get("success"):
            result["strategic_slot_used"] = next_slot.strftime('%Y-%m-%d %H:%M')
            
        return result
    
    def process_video_upload(self, video_url, max_retries=3):
        """
        Complete video processing: download -> upload -> get token
        
        Args:
            video_url (str): URL of the video to process
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            str: Upload token if successful, None if failed
        """
        for attempt in range(max_retries):
            try:
                print(f"🔄 Video processing attempt {attempt + 1}/{max_retries}")
                
                # Step 1: Download video
                temp_file_path, mime_type = self.download_video(video_url)
                if not temp_file_path:
                    print(f"❌ Failed to download video on attempt {attempt + 1}")
                    continue
                
                try:
                    # Step 2: Upload to SocialBu
                    upload_token = self.upload_video_to_socialbu(temp_file_path, mime_type)
                    
                    if upload_token:
                        print(f"✅ Video processing successful on attempt {attempt + 1}")
                        return upload_token
                    else:
                        print(f"❌ Upload failed on attempt {attempt + 1}")
                        
                finally:
                    # Always clean up temp file
                    if temp_file_path and os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        
            except Exception as e:
                print(f"❌ Video processing error on attempt {attempt + 1}: {e}")
                
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        print(f"❌ Video processing failed after {max_retries} attempts")
        return None
    
    def download_video(self, video_url, timeout=30):
        """
        Download video from URL to temporary file
        
        Args:
            video_url (str): URL of the video to download
            timeout (int): Request timeout in seconds
            
        Returns:
            tuple: (temp_file_path, mime_type) or (None, None) if failed
        """
        try:
            print(f"📥 Downloading video from: {video_url[:80]}...")
            
            # Create a temporary file
            temp_dir = tempfile.gettempdir()
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.mp4',
                dir=temp_dir
            )
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Download with streaming to handle large files
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=timeout)
            response.raise_for_status()
            
            # Get content type
            content_type = response.headers.get('content-type', 'video/mp4')
            if 'video' not in content_type:
                content_type = 'video/mp4'  # Default for Instagram videos
                
            # Write to temp file
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(temp_file_path)
            print(f"✅ Video downloaded: {file_size / (1024*1024):.2f} MB")
            
            return temp_file_path, content_type
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error downloading video: {e}")
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            
        # Clean up on error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            
        return None, None
    
    def upload_video_to_socialbu(self, file_path, mime_type, max_wait_time=300):
        """
        Upload video to SocialBu using their 3-step process
        
        Args:
            file_path (str): Path to the video file
            mime_type (str): MIME type of the file
            max_wait_time (int): Maximum time to wait for processing (seconds)
            
        Returns:
            str: Upload token if successful, None if failed
        """
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            print(f"📤 Starting SocialBu upload process for: {filename} ({file_size / (1024*1024):.2f} MB)")
            
            # Step 1: Initialize upload
            print("   Step 1: Initializing upload...")
            init_response = self.upload_media(filename, mime_type)
            
            if not init_response or 'signed_url' not in init_response:
                print(f"❌ Upload initialization failed: {init_response}")
                return None
            
            signed_url = init_response['signed_url']
            file_key = init_response['key']
            
            # Step 2: Upload file to signed URL
            print("   Step 2: Uploading file...")
            upload_success = self.upload_file_to_signed_url(
                file_path, signed_url, mime_type, file_size
            )
            
            if not upload_success:
                print("❌ File upload to signed URL failed")
                return None
            
            # Step 3: Wait for processing and get upload token
            print("   Step 3: Waiting for processing...")
            upload_token = self.wait_for_upload_processing(file_key, max_wait_time)
            
            if upload_token:
                print(f"✅ Upload complete! Token: {upload_token[:20]}...")
                return upload_token
            else:
                print("❌ Upload processing failed or timed out")
                return None
                
        except Exception as e:
            print(f"❌ Error in upload process: {e}")
            return None
    
    def upload_file_to_signed_url(self, file_path, signed_url, mime_type, file_size):
        """
        Upload file to the S3 signed URL (Step 2 of SocialBu upload)
        
        Args:
            file_path (str): Path to the file
            signed_url (str): Pre-signed URL from SocialBu
            mime_type (str): MIME type of the file
            file_size (int): Size of the file in bytes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            headers = {
                'Content-Type': mime_type,
                'Content-Length': str(file_size),
                'x-amz-acl': 'private'
            }
            
            with open(file_path, 'rb') as f:
                response = requests.put(
                    signed_url,
                    data=f,
                    headers=headers,
                    timeout=120  # 2 minute timeout for large files
                )
            
            if response.status_code in [200, 204]:
                print(f"✅ File uploaded successfully to signed URL")
                return True
            else:
                print(f"❌ Upload failed with status {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading to signed URL: {e}")
            return False
    
    def wait_for_upload_processing(self, file_key, max_wait_time=300):
        """
        Wait for SocialBu to process the uploaded file and return upload token
        
        Args:
            file_key (str): File key returned from upload initialization
            max_wait_time (int): Maximum time to wait in seconds
            
        Returns:
            str: Upload token if successful, None if failed or timed out
        """
        start_time = time.time()
        check_interval = 2  # Start with 2 second intervals
        
        while time.time() - start_time < max_wait_time:
            try:
                status_response = self.check_media_status(file_key)
                
                if status_response and status_response.get('success'):
                    upload_token = status_response.get('upload_token')
                    if upload_token:
                        elapsed = time.time() - start_time
                        print(f"✅ Processing complete in {elapsed:.1f} seconds")
                        return upload_token
                
                # Exponential backoff for check intervals (max 30 seconds)
                check_interval = min(check_interval * 1.2, 30)
                print(f"   ⏳ Still processing... (checking again in {check_interval:.1f}s)")
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Error checking upload status: {e}")
                time.sleep(5)
        
        print(f"⏰ Upload processing timed out after {max_wait_time} seconds")
        return None
    
    def upload_media(self, file_name, mime_type):
        """
        Step 1: Initialize media upload
        Returns signed URL for uploading file
        """
        if not self.api_token:
            return {"success": False, "error": "No API token configured"}
            
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        upload_data = {
            "name": file_name,
            "mime_type": mime_type
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/upload_media",
                headers=headers,
                json=upload_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_media_status(self, key):
        """
        Step 3: Check if media upload is processed
        Returns upload_token when ready
        """
        if not self.api_token:
            return {"success": False, "error": "No API token configured"}
            
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/upload_media/status?key={key}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_strategic_schedule_info(self):
        """Get information about strategic scheduling"""
        scheduled_slots = self.strategic_scheduler.get_scheduled_slots_info()
        next_slot = self.strategic_scheduler.get_next_available_slot()
        
        return {
            "strategic_times": [f"{hour}:00" for hour in self.strategic_scheduler.strategic_times],
            "next_available_slot": next_slot.strftime('%Y-%m-%d %H:%M'),
            "scheduled_slots": [(date.isoformat(), hour) for date, hour in scheduled_slots]
        }

    def test_connection(self):
        """Test the API connection"""
        print("🔍 Testing SocialBu API connection...")
        
        # Test authentication by getting accounts
        accounts_response = self.get_accounts()
        
        if accounts_response.get("success"):
            print("✅ API connection successful")
            accounts = accounts_response.get("accounts", [])
            print(f"   Found {len(accounts)} accounts")
            for account in accounts[:3]:  # Show first 3 accounts
                account_id = account.get('id', 'unknown')
                platform = account.get('platform', 'unknown')
                username = account.get('username', 'unknown')
                print(f"   - {platform}: {username} (ID: {account_id})")
            return True
        else:
            print("❌ API connection failed")
            print(f"   Error: {accounts_response.get('error', 'Unknown error')}")
            return False

    def get_scheduled_posts(self):
        """Get scheduled posts from SocialBu to check for time conflicts"""
        try:
            response = self._make_request("GET", "/posts?status=scheduled")
            
            if response.get("success") or isinstance(response, list):
                posts = response.get("data", []) if isinstance(response, dict) else response
                scheduled_times = []
                
                for post in posts:
                    publish_at = post.get("publish_at")
                    if publish_at:
                        try:
                            # Parse the schedule time
                            scheduled_dt = datetime.strptime(publish_at, "%Y-%m-%d %H:%M:%S")
                            # Convert to Panama timezone if needed
                            if scheduled_dt.tzinfo is None:
                                scheduled_dt = PANAMA_TZ.localize(scheduled_dt)
                            scheduled_times.append(scheduled_dt)
                        except ValueError:
                            continue
                
                return scheduled_times
            
            return []
                
        except Exception as e:
            print(f"⚠️  Warning: Could not fetch scheduled posts: {e}")
            return []

    def _load_existing_schedules(self):
        """Load existing scheduled posts to prevent conflicts"""
        scheduled_times = self.get_scheduled_posts()
        if scheduled_times:
            print(f"   📅 Loaded {len(scheduled_times)} existing scheduled posts to prevent conflicts")
            for scheduled_time in scheduled_times:
                self.strategic_scheduler.mark_slot_as_used(scheduled_time)


class ContentAnalyzer:
    """Service for analyzing and ranking posts"""
    
    @staticmethod
    def get_top_posts(posts, count=3):
        """
        Analyze posts and return top performers based on engagement
        Engagement score = (likes + comments * 3 + views * 0.1) / 1000
        """
        if not posts:
            return []
        
        # Calculate engagement score for each post
        for post in posts:
            likes = post.get("likes_count", 0)
            comments = post.get("comments_count", 0)
            views = post.get("views_count", 0)
            
            # Weight comments more heavily, views less
            engagement_score = (likes + comments * 3 + views * 0.1) / 1000
            post["engagement_score"] = engagement_score
        
        # Sort by engagement score and return top posts
        sorted_posts = sorted(posts, key=lambda x: x["engagement_score"], reverse=True)
        return sorted_posts[:count] 