# Apify Client Migration Guide

This document explains the changes made to update your code to use the official `apify-client` library instead of raw HTTP requests.

## What Changed

### 1. Dependencies Updated

**Before:** Raw HTTP requests using `requests` library
```python
import requests
```

**After:** Official Apify client library
```python
from apify_client import ApifyClient, ApifyClientAsync
```

**Installation:**
```bash
pip install apify-client
```

### 2. Client Initialization

**Before:** Manual URL construction and headers
```python
def __init__(self):
    self.api_token = APIFY_API_TOKEN
    self.base_url = "https://api.apify.com/v2"
    self.actor_id = APIFY_ACTOR_ID
```

**After:** Clean client initialization
```python
def __init__(self):
    self.api_token = APIFY_API_TOKEN
    self.actor_id = APIFY_ACTOR_ID
    # Initialize the Apify client
    if self.api_token and self.api_token != "your_apify_api_token_here":
        self.apify_client = ApifyClient(self.api_token)
    else:
        self.apify_client = None
```

### 3. Actor Execution

**Before:** Manual run management with polling
```python
# Start the actor
run_url = f"{self.base_url}/acts/{self.actor_id}/runs"
headers = {"Authorization": f"Bearer {self.api_token}"}

response = requests.post(run_url, json=actor_input, headers=headers)
response.raise_for_status()

run_data = response.json()
run_id = run_data["data"]["id"]

# Wait for completion and get results
return self._wait_for_results(run_id)
```

**After:** Simple one-line execution
```python
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
```

### 4. Code Removed

The following methods were **removed** because the Apify client handles them automatically:

- `_wait_for_results()` - The client automatically waits for completion
- Manual status polling logic
- Manual result fetching with HTTP requests

## Key Benefits

### 1. **Simplified Code**
- Reduced from ~50 lines to ~15 lines for actor execution
- No need to manually manage run states
- Automatic error handling and retries

### 2. **Better Reliability**
- Built-in retry logic for network failures
- Proper error handling for various failure scenarios
- UTF-8 encoding handled automatically

### 3. **Async Support**
Added `ApifyServiceAsync` class with async/await support:

```python
# Async usage
apify_service = ApifyServiceAsync()
results = await apify_service.scrape_instagram_posts(usernames, max_posts=5)
```

### 4. **Performance**
- More efficient HTTP connections
- Better connection pooling
- Optimized JSON handling

## Usage Examples

### Synchronous Usage
```python
from scraper.services import ApifyService

apify_service = ApifyService()
results = apify_service.scrape_instagram_posts(["username1", "username2"], max_posts=10)
```

### Asynchronous Usage
```python
import asyncio
from scraper.services import ApifyServiceAsync

async def main():
    apify_service = ApifyServiceAsync()
    results = await apify_service.scrape_instagram_posts(["username1", "username2"], max_posts=10)

asyncio.run(main())
```

## Running Examples

Test the updated implementation:

```bash
python apify_client_examples.py
```

## Migration Checklist

- [x] ✅ Added `apify-client` to requirements.txt
- [x] ✅ Updated imports to use official client
- [x] ✅ Simplified ApifyService class
- [x] ✅ Added ApifyServiceAsync for async support
- [x] ✅ Removed manual polling logic
- [x] ✅ Added better error messages and logging
- [x] ✅ Created example usage scripts
- [x] ✅ Maintained backward compatibility with existing workflow

## API Token Security

The updated implementation maintains the same security practices:

```python
# Your API token should be kept secure
APIFY_API_TOKEN = "apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# The client automatically handles authentication
apify_client = ApifyClient(APIFY_API_TOKEN)
```

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure `apify-client` is installed
   ```bash
   pip install apify-client
   ```

2. **Authentication Error**: Verify your API token is correct
   - Check [Apify Console](https://console.apify.com/settings/integrations)
   - Ensure token has proper permissions

3. **Actor Not Found**: Verify your `APIFY_ACTOR_ID` is correct
   - Should be in format: `username/actor-name` or actor ID

### Testing

Your existing workflow will continue to work without changes. The `BeampageWorkflow` class still uses the same interface:

```python
# This still works exactly the same
workflow = BeampageWorkflow()
results = workflow.run_workflow()
```

---

**Documentation Reference**: [Apify Python Client Docs](https://docs.apify.com/api/client/python/docs/overview/getting-started) 