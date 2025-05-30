"""
Main workflow orchestrator for the Instagram content scraping and reposting process
"""

import json
import os
from datetime import datetime
import random
from django.core.management.base import BaseCommand
from .config import PAGES
from .services import ApifyService, SocialBuService, ContentAnalyzer


class BeampageWorkflow:
    """Main workflow orchestrator"""
    
    def __init__(self):
        self.apify_service = ApifyService()
        self.socialbu_service = SocialBuService()
        self.content_analyzer = ContentAnalyzer()
        self.results_file = "workflow_results.json"
        self.processed_posts_file = "processed_posts.json"
    
    def _load_processed_posts(self):
        """Load previously processed post IDs"""
        try:
            if os.path.exists(self.processed_posts_file):
                with open(self.processed_posts_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Warning: Could not load processed posts: {e}")
            return {}
    
    def _save_processed_posts(self, processed_posts):
        """Save processed post IDs"""
        try:
            with open(self.processed_posts_file, 'w') as f:
                json.dump(processed_posts, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save processed posts: {e}")
    
    def _filter_duplicate_posts(self, posts):
        """Filter out posts that have already been processed"""
        processed_posts = self._load_processed_posts()
        new_posts = [post for post in posts if post['id'] not in processed_posts]
        return new_posts
    
    def _validate_post_media(self, post):
        """
        Validate if a post has usable video URLs for scheduling.
        Returns True if post has valid video, False otherwise.
        ONLY VIDEOS ALLOWED - NO IMAGES.
        """
        video_url = post.get('video_url')
        
        # Only accept posts with valid video URLs
        if video_url and video_url != "" and not video_url.startswith('https://mock-'):
            return True
            
        # Reject everything else (images, posts without video)
        return False
    
    def _filter_posts_with_valid_media(self, posts):
        """Filter posts to only include those with valid media URLs"""
        valid_posts = []
        skipped_count = 0
        
        for post in posts:
            if self._validate_post_media(post):
                valid_posts.append(post)
            else:
                skipped_count += 1
                print(f"      ⚠️  Skipping post {post.get('id', 'unknown')} - no valid media URLs")
        
        if skipped_count > 0:
            print(f"      📝 Skipped {skipped_count} posts without valid media")
            
        return valid_posts
    
    def _mark_posts_as_processed(self, posts):
        """Mark posts as processed"""
        processed_posts = self._load_processed_posts()
        timestamp = datetime.now().isoformat()
        
        for post in posts:
            post_id = post.get('id')
            if post_id:
                processed_posts[post_id] = timestamp
        
        self._save_processed_posts(processed_posts)
    
    def run_workflow(self, page_name=None):
        """
        Run the complete workflow for a specific page or all pages
        """
        print("🚀 Starting Beampage workflow...")
        
        if page_name:
            if page_name not in PAGES:
                print(f"❌ Page '{page_name}' not found in configuration")
                return
            pages_to_process = {page_name: PAGES[page_name]}
        else:
            pages_to_process = PAGES
        
        all_results = []
        
        for page_name, page_config in pages_to_process.items():
            print(f"\n📄 Processing page: {page_name}")
            result = self._process_page(page_name, page_config)
            all_results.append(result)
        
        # Save results
        self._save_results(all_results)
        
        print(f"\n✅ Workflow completed! Results saved to {self.results_file}")
        return all_results
    
    def _process_page(self, page_name, page_config):
        """Process a single page with total output limit control"""
        result = {
            "page_name": page_name,
            "timestamp": datetime.now().isoformat(),
            "scraped_accounts": {},
            "selected_posts": {},
            "scheduled_posts": [],
            "strategic_schedule_info": {},
            "total_limit_info": {},
            "errors": []
        }
        
        try:
            # Get the total output limit
            max_total_posts = page_config.get('max_total_posts_to_schedule', 999)
            print(f"   🎯 Target: {max_total_posts} posts maximum")
            
            # Step 1: Randomize competitors list for fairness
            competitors = page_config['competitors'].copy()
            random.shuffle(competitors)
            print(f"   🔀 Randomized competitor order: {competitors}")
            
            # Step 2: Scrape posts from competitors until we hit the limit
            print(f"   🔍 Scraping posts from competitors (stopping at {max_total_posts} posts)...")
            
            all_selected_posts = []
            scraped_count = 0
            
            for username in competitors:
                if len(all_selected_posts) >= max_total_posts:
                    print(f"      ✅ Reached target of {max_total_posts} posts - stopping scraping")
                    break
                
                print(f"      📥 Scraping {username}...")
                
                # Scrape posts for this competitor
                user_posts = self.apify_service.scrape_instagram_posts(
                    [username], 
                    page_config['max_posts_to_fetch']
                )
                
                if username in user_posts and user_posts[username]:
                    posts = user_posts[username]
                    result["scraped_accounts"][username] = posts
                    scraped_count += len(posts)
                    
                    # Filter duplicates and validate media
                    new_posts = self._filter_duplicate_posts(posts)
                    valid_posts = self._filter_posts_with_valid_media(new_posts)
                    
                    if valid_posts:
                        # Select top posts for this competitor
                        remaining_slots = max_total_posts - len(all_selected_posts)
                        posts_to_take = min(page_config['top_posts_count'], remaining_slots)
                        
                        top_posts = self.content_analyzer.get_top_posts(valid_posts, posts_to_take)
                        
                        if top_posts:
                            result["selected_posts"][username] = top_posts
                            all_selected_posts.extend(top_posts)
                            print(f"         ✅ Selected {len(top_posts)} posts ({len(all_selected_posts)}/{max_total_posts} total)")
                        else:
                            print(f"         ❌ No valid posts found")
                    else:
                        print(f"         ❌ No posts with valid media")
                else:
                    print(f"         ❌ No posts found")
                    result["scraped_accounts"][username] = []
            
            # Step 3: Show summary
            total_posts_to_schedule = len(all_selected_posts)
            print(f"   📊 Final selection: {total_posts_to_schedule} posts from {len(result['selected_posts'])} competitors")
            
            result["total_limit_info"] = {
                "target_limit": max_total_posts,
                "posts_selected": total_posts_to_schedule,
                "limit_reached": total_posts_to_schedule >= max_total_posts,
                "competitors_checked": len([u for u in competitors if u in result["scraped_accounts"]]),
                "total_competitors": len(competitors)
            }
            
            # Step 4: Schedule all selected posts immediately
            if all_selected_posts:
                print(f"   🚀 Scheduling {total_posts_to_schedule} posts on SocialBu...")
                
                for username, posts in result["selected_posts"].items():
                    for post in posts:
                        scheduled_result = self._schedule_single_post(
                            page_config, 
                            post, 
                            username
                        )
                        result["scheduled_posts"].append(scheduled_result)
                        
                        # Log the scheduled time if available
                        if scheduled_result["schedule_result"].get("scheduled_time"):
                            print(f"      ✅ Post scheduled: {scheduled_result['schedule_result']['scheduled_time']}")
                
                # Step 5: Mark scheduled posts as processed
                self._mark_posts_as_processed(all_selected_posts)
                print(f"   📝 Marked {len(all_selected_posts)} posts as processed")
            else:
                print(f"   ⚠️  No posts to schedule")
            
            # Get strategic scheduling info
            schedule_info = self.socialbu_service.get_strategic_schedule_info()
            # Convert date objects to strings for JSON serialization
            if schedule_info.get('scheduled_slots'):
                schedule_info['scheduled_slots'] = [
                    (date.isoformat() if hasattr(date, 'isoformat') else str(date), hour) 
                    for date, hour in schedule_info['scheduled_slots']
                ]
            result["strategic_schedule_info"] = schedule_info
            
            print(f"   ✅ Page processing completed:")
            print(f"      Target: {max_total_posts} posts")
            print(f"      Selected: {total_posts_to_schedule} posts")
            print(f"      Scheduled: {len(result['scheduled_posts'])} posts")
            print(f"      Competitors checked: {result['total_limit_info']['competitors_checked']}/{result['total_limit_info']['total_competitors']}")
            
        except Exception as e:
            error_msg = f"Error processing page {page_name}: {str(e)}"
            print(f"   ❌ {error_msg}")
            result["errors"].append(error_msg)
        
        return result
    
    def _schedule_single_post(self, page_config, post, original_username):
        """Schedule a single post on SocialBu using strategic time slots"""
        # Create caption with original poster credit
        caption = f"{random.choice(page_config['generic_caption'])}\n\nOriginal by: @{original_username}"
        
        # Determine media URL and type
        video_url = post.get('video_url')
        display_url = post.get('display_url')
        
        # Use video URL if available, otherwise use display URL (image)
        media_url = video_url if (video_url and video_url != "") else display_url
        
        # Prepare Instagram-specific options based on media type
        media_options = {}
        if video_url and video_url != "":
            # This is a video post
            media_options = {
                "post_as_reel": True,  # Post videos as Instagram Reels
                "share_reel_to_feed": True,  # Share to main feed as well
                "comment": f"Original content by @{original_username}"
            }
        elif display_url and display_url != "":
            # This is an image post - no special options needed
            media_options = {
                "comment": f"Original content by @{original_username}"
            }
        
        # Schedule the post using strategic scheduling with media handling
        schedule_result = self.socialbu_service.schedule_post_with_strategic_timing(
            content=caption,
            accounts=[page_config['socialbu_account_id']],
            video_url=media_url,  # SocialBu uses 'video_url' param for both videos and images
            media_options=media_options if media_options else None
        )
        
        return {
            "original_post_id": post['id'],
            "original_username": original_username,
            "media_url": media_url,
            "media_type": "video" if (video_url and video_url != "") else "image",
            "video_url": post.get('video_url'),  # Keep original for compatibility
            "display_url": post.get('display_url'),  # Keep original for tracking
            "caption": caption,
            "engagement_score": post.get('engagement_score', 0),
            "schedule_result": schedule_result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _save_results(self, results):
        """Save workflow results to JSON file"""
        try:
            # Load existing results if file exists
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r') as f:
                    existing_results = json.load(f)
            else:
                existing_results = []
            
            # Append new results
            existing_results.extend(results)
            
            # Keep only last 100 results for cleanup
            if len(existing_results) > 100:
                existing_results = existing_results[-100:]
                print(f"   🧹 Cleaned up old workflow results, keeping last 100 entries")
            
            # Save updated results
            with open(self.results_file, 'w') as f:
                json.dump(existing_results, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save results to file: {e}")
    
    def get_recent_results(self, limit=10):
        """Get recent workflow results"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r') as f:
                    results = json.load(f)
                    return results[-limit:] if len(results) > limit else results
            return []
        except Exception as e:
            print(f"Error reading results file: {e}")
            return []
    
    def get_strategic_schedule_status(self):
        """Get current strategic scheduling status"""
        return self.socialbu_service.get_strategic_schedule_info()
    
    def list_configured_pages(self):
        """List all configured pages"""
        print("📋 Configured pages:")
        for page_name, config in PAGES.items():
            print(f"   - {page_name}")
            print(f"     IG Account: {config['ig_account_name']}")
            print(f"     Competitors: {', '.join(config['competitors'])}")
            print(f"     Max posts to fetch per competitor: {config['max_posts_to_fetch']}")
            print(f"     Top posts count per competitor: {config['top_posts_count']}")
            print(f"     🎯 Total output limit: {config.get('max_total_posts_to_schedule', 'unlimited')}")
            print()
        
        # Show strategic scheduling info
        schedule_info = self.get_strategic_schedule_status()
        print("⏰ Strategic Scheduling Information:")
        print(f"   Strategic posting times: {', '.join(schedule_info['strategic_times'])}")
        print(f"   Next available slot: {schedule_info['next_available_slot']}")
        if schedule_info['scheduled_slots']:
            print(f"   Currently scheduled slots: {len(schedule_info['scheduled_slots'])}")
            for date, hour in schedule_info['scheduled_slots'][-5:]:  # Show last 5
                print(f"     - {date} at {hour}:00")
        else:
            print("   No slots currently scheduled")


def run_workflow_command(page_name=None):
    """Command line entry point for running the workflow"""
    workflow = BeampageWorkflow()
    
    if page_name == "list":
        workflow.list_configured_pages()
        return
    
    if page_name == "status":
        recent_results = workflow.get_recent_results(5)
        print("📊 Recent workflow results:")
        for result in recent_results:
            scheduled_count = len(result.get('scheduled_posts', []))
            limit_info = result.get('total_limit_info', {})
            
            if limit_info:
                target = limit_info.get('target_limit', 'N/A')
                selected = limit_info.get('posts_selected', 0)
                competitors_checked = limit_info.get('competitors_checked', 0)
                total_competitors = limit_info.get('total_competitors', 0)
                print(f"   - {result['timestamp']}: {result['page_name']}")
                print(f"     🎯 Target: {target} | Selected: {selected} | Scheduled: {scheduled_count}")
                print(f"     🔍 Competitors checked: {competitors_checked}/{total_competitors}")
            else:
                # Legacy format
                print(f"   - {result['timestamp']}: {result['page_name']} - {scheduled_count} posts scheduled")
            
            if 'strategic_schedule_info' in result:
                print(f"     📅 Next available slot: {result['strategic_schedule_info']['next_available_slot']}")
        
        # Show current scheduling status
        print("\n⏰ Current Strategic Scheduling Status:")
        schedule_info = workflow.get_strategic_schedule_status()
        print(f"   Strategic posting times: {', '.join(schedule_info['strategic_times'])}")
        print(f"   Next available slot: {schedule_info['next_available_slot']}")
        return
    
    if page_name == "schedule":
        print("⏰ Strategic Scheduling Information:")
        schedule_info = workflow.get_strategic_schedule_status()
        print(f"   Strategic posting times: {', '.join(schedule_info['strategic_times'])}")
        print(f"   Next available slot: {schedule_info['next_available_slot']}")
        if schedule_info['scheduled_slots']:
            print(f"   Currently scheduled slots: {len(schedule_info['scheduled_slots'])}")
            for date, hour in schedule_info['scheduled_slots']:
                print(f"     - {date} at {hour}:00")
        else:
            print("   No slots currently scheduled")
        return
    
    # Run the main workflow
    workflow.run_workflow(page_name) 