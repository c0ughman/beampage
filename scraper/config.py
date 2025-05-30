"""
Configuration for page instances - hardcoded for simplicity
Each page represents an Instagram account we manage and want to repost content to
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Hardcoded page instances
PAGES = {
    "dobermanzone": {
        "ig_account_name": "dobermanzone",
        "competitors": ["doberman.dobi","doberman_rateow","zakiyathedobie","dobermanmylife","doberman_worldwide","doberman_universe","doberman__life","doberman__army","doberman.empire","doberman_lovers_club","doberman.area"],
        "generic_caption": [
            "This doberman is a good boy 🐕",
            "Beautiful doberman energy right here! 💪",
            "Doberman love at its finest ❤️",
            "What a stunning doberman! 😍",
            "Doberman goals right here 🔥",
            "This is why we love dobermans! 🥰",
            "Pure doberman perfection 👌",
            "Doberman vibes are unmatched ✨",
            "Look at this amazing doberman! 👀",
            "Doberman loyalty and beauty combined 💎"
        ],
        "max_posts_to_fetch": 10,  # Number of latest posts to fetch from each competitor
        "top_posts_count": 3,  # Number of top posts to select from each competitor
        
        # NEW: Total output control
        "max_total_posts_to_schedule": 5,  # Stop when we have this many posts to schedule
        
        "socialbu_account_id": 131236
    },
    "gersheps": {
        "ig_account_name": "gersheps",
        "competitors": ["germanshepherrds","zara_theshepherd⠀","littlecharlieboy_","chief.gsd.nj","german_shepherd.lover","german.shepherd.space","bear_the_gshepherd","german_shepherd_ins","snipertheshepherrd","germanshepherd.universe","germanshepherd.in","shepherdsforever","shepherd_mob","gsd_corner"],
        "generic_caption": [
            "Adorable German Shepherd 🐕",
            "German Shepherd love at its finest ❤️",
            "What a stunning German Shepherd! 😍",
            "German Shepherd goals right here 🔥",
            "This is why we love German Shepherds! 🥰",
            "Pure German Shepherd perfection 👌",
            "German Shepherd vibes are unmatched ✨",
        ],
        "max_posts_to_fetch": 10,  # Number of latest posts to fetch from each competitor
        "top_posts_count": 3,  # Number of top posts to select from each competitor
        
        # NEW: Total output control
        "max_total_posts_to_schedule": 5,  # Stop when we have this many posts to schedule
        
        "socialbu_account_id": 131235
    },
"gersheps": {
        "ig_account_name": "bulldoglovedaily",
        "competitors": "bulldogdays","bulldogofi","blessed.english.bulldog","bulldogstuff","englishbulldog.space","englishbulldog_world","bulldog.l_o_v_e"],
        "generic_caption": [
            "Bulldogs are the best ever"
        ],
        "max_posts_to_fetch": 10,  # Number of latest posts to fetch from each competitor
        "top_posts_count": 3,  # Number of top posts to select from each competitor
        
        # NEW: Total output control
        "max_total_posts_to_schedule": 5,  # Stop when we have this many posts to schedule
        
        "socialbu_account_id": 131234
    },

}

# API Configuration
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")

# SocialBu API Configuration
SOCIALBU_API_TOKEN = os.getenv("SOCIALBU_API_TOKEN", "")

# Scraper settings
APIFY_ACTOR_ID = "apify/instagram-post-scraper"  # Try a different actor ID format 
