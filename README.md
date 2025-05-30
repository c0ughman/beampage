# Beampage - Instagram Content Automation Tool

A simple Django-based tool that automates the process of scraping top-performing Instagram posts from competitors and scheduling them for reposting using Apify and SocialBu APIs.

## Features

- **Instagram Scraping**: Uses Apify's Instagram scraper to fetch latest posts from competitor accounts
- **Content Analysis**: Analyzes post engagement (likes, comments, views) to identify top performers
- **Automated Scheduling**: Schedules selected video content to your Instagram accounts via SocialBu
- **Simple Configuration**: Environment variable-based configuration for secure deployment
- **Command Line Interface**: Run workflows directly from terminal
- **Results Tracking**: Saves workflow results to JSON files for tracking
- **Heroku Ready**: Configured for easy deployment to Heroku

## Quick Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Click the button above for one-click deployment to Heroku. You'll need:
- Apify API token
- SocialBu API token

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Local Development Setup

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your API tokens:
```bash
APIFY_API_TOKEN=your_apify_api_token_here
SOCIALBU_API_TOKEN=your_socialbu_api_token_here
DEBUG=True
```

### 3. Configure Your Pages

Edit `scraper/config.py` to set up your page instances:

```python
PAGES = {
    "my_brand_page": {
        "ig_account_name": "your_instagram_handle",
        "competitors": [
            "competitor1_handle",
            "competitor2_handle",
            "competitor3_handle"
        ],
        "generic_caption": [
            "Amazing content! 🔥 #viral #content",
            "This is incredible! 😍 #awesome",
            "Love this energy! ⚡ #vibes",
            "Pure perfection right here! 👌 #goals"
        ],
        "max_posts_to_fetch": 10,
        "top_posts_count": 3,
        "socialbu_account_id": "your_socialbu_account_id"
    }
}
```

**Note**: API tokens are now loaded from environment variables automatically.

### 4. Set Up Django

```bash
# Run initial migration
python manage.py migrate

# Start development server
python manage.py runserver
```

## Usage

### Command Line Interface

Run the complete workflow:
```bash
python manage.py run_beampage
```

Run workflow for a specific page:
```bash
python manage.py run_beampage my_brand_page
```

List configured pages:
```bash
python manage.py run_beampage list
```

Check recent workflow results:
```bash
python manage.py run_beampage status
```

### What Happens During a Workflow Run

1. **Scraping**: Fetches the latest posts from all competitor accounts using Apify
2. **Analysis**: Calculates engagement scores for each post (videos only)
3. **Selection**: Picks the top-performing posts based on engagement
4. **Scheduling**: Schedules selected videos to your Instagram account via SocialBu
5. **Tracking**: Saves results to `workflow_results.json`

### Engagement Score Calculation

Posts are ranked using this formula:
```
engagement_score = (likes + comments * 3 + views * 0.1) / 1000
```

Comments are weighted more heavily as they indicate higher engagement quality.

## API Configuration

### Apify Instagram Scraper

1. Sign up at [Apify.com](https://apify.com)
2. Get your API token from the account settings
3. The tool uses the official `apify/instagram-scraper` actor

### SocialBu API

1. Sign up at [SocialBu.com](https://socialbu.com)
2. Get your API token from account settings
3. Note your account IDs for the Instagram accounts you want to post to

## File Structure

```
beampage/
├── scraper/
│   ├── config.py           # Page and API configuration
│   ├── services.py         # API service classes
│   ├── workflow.py         # Main workflow orchestrator
│   └── management/
│       └── commands/
│           └── run_beampage.py  # Django management command
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
└── workflow_results.json  # Results tracking (auto-generated)
```

## Mock Mode

If API tokens are not configured, the tool runs in mock mode:
- Generates fake Instagram post data for testing
- Simulates SocialBu scheduling without actual API calls
- Perfect for testing the workflow before going live

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the virtual environment and all dependencies are installed
2. **API Failures**: Check your API tokens and account configurations
3. **No Videos Found**: The tool only processes video posts, ensure competitors post video content

### Checking Logs

The tool provides detailed console output during execution. Check for:
- ⚠️ Warning messages for configuration issues
- ❌ Error messages for failures
- ✅ Success messages for completed steps

## Extending the Tool

The modular design makes it easy to extend:

- **Add new APIs**: Create new service classes in `services.py`
- **Change ranking logic**: Modify `ContentAnalyzer.get_top_posts()`
- **Add new workflows**: Extend `BeampageWorkflow` class
- **Custom scheduling**: Modify `_schedule_single_post()` method

## Security Notes

- Keep API tokens secure and never commit them to version control
- Consider using environment variables for production deployments
- The tool respects Instagram's terms of service through Apify's compliant scraper

## License

This project is for educational and personal use. Ensure compliance with Instagram's terms of service and applicable laws. 