# Deployment Guide

## Prerequisites

1. **Heroku CLI** installed on your machine
2. **Git** for version control
3. **Instagram Scraper API tokens** (Apify)
4. **SocialBu API tokens** for social media posting

## Environment Variables

This application requires the following environment variables to be set:

### Required Variables
- `APIFY_API_TOKEN`: Your Apify API token for Instagram scraping
- `SOCIALBU_API_TOKEN`: Your SocialBu API token for social media posting
- `SECRET_KEY`: Django secret key (generate a new one for production)
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (include your Heroku app domain)

### Optional Variables
- `DATABASE_URL`: Automatically provided by Heroku PostgreSQL addon

## Heroku Deployment Steps

### 1. Clone and prepare the repository
```bash
git clone <your-repo-url>
cd beampage
```

### 2. Create a Heroku app
```bash
heroku create your-app-name
```

### 3. Add PostgreSQL addon
```bash
heroku addons:create heroku-postgresql:mini
```

### 4. Set environment variables
```bash
heroku config:set APIFY_API_TOKEN="your_apify_token"
heroku config:set SOCIALBU_API_TOKEN="your_socialbu_token"
heroku config:set SECRET_KEY="your_secret_key"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com,localhost,127.0.0.1"
heroku config:set DJANGO_SETTINGS_MODULE="beampage.settings_heroku"
```

### 5. Deploy to Heroku
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

### 6. Run database migrations
```bash
heroku run python manage.py migrate
```

### 7. Create a superuser (optional)
```bash
heroku run python manage.py createsuperuser
```

## Local Development Setup

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Create .env file**
Copy `.env.example` to `.env` and fill in your actual values:
```bash
cp .env.example .env
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Start development server**
```bash
python manage.py runserver
```

## Important Security Notes

- Never commit `.env` files or files containing actual API tokens
- Always use environment variables for sensitive configuration
- Generate a strong SECRET_KEY for production
- Keep DEBUG=False in production
- Regularly rotate API tokens

## Troubleshooting

### Common Issues

1. **Build failures**: Check that all dependencies in `requirements.txt` are compatible
2. **Database connection errors**: Ensure PostgreSQL addon is attached and DATABASE_URL is set
3. **Static files not loading**: Verify STATIC_ROOT and WhiteNoise configuration
4. **API token errors**: Confirm all required environment variables are set correctly

### Checking logs
```bash
heroku logs --tail
```

### Restarting the app
```bash
heroku restart
``` 