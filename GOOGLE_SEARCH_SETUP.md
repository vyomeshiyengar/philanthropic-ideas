# Google Custom Search API Setup Guide

This guide will help you set up the Google Custom Search API for talent identification in the Philanthropic Ideas Generator.

## Overview

The Google Custom Search API is used to find potential talent (researchers, practitioners, experts) who could work on philanthropic ideas. It searches for people with relevant expertise in academic and professional contexts.

## Prerequisites

1. **Google Cloud Platform Account**: You need a Google account with access to Google Cloud Platform
2. **Billing Enabled**: Google Custom Search API requires billing to be enabled (though it has a generous free tier)

## Step 1: Enable Google Custom Search API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Library**
4. Search for "Custom Search API"
5. Click on "Custom Search API" and click **Enable**

## Step 2: Create API Credentials

1. In the Google Cloud Console, go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **API Key**
3. Copy the generated API key
4. (Optional) Click on the API key to restrict it to Custom Search API only for security

## Step 3: Create a Custom Search Engine

1. Go to [Google Custom Search Engine](https://cse.google.com/)
2. Click **Create a search engine**
3. Enter any website URL (e.g., `https://www.google.com`) - this is just a placeholder
4. Give your search engine a name (e.g., "Philanthropic Talent Search")
5. Click **Create**
6. In the search engine settings, click **Edit search engine**
7. Under **Sites to search**, select **Search the entire web**
8. Under **Search engine ID**, copy the **Search engine ID** (this is your `cx` parameter)

## Step 4: Configure Environment Variables

1. Open your `.env` file in the project root
2. Add the following lines:

```env
# Google Custom Search API
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your_search_engine_id_here
```

Replace:
- `your_api_key_here` with the API key from Step 2
- `your_search_engine_id_here` with the Search Engine ID from Step 3

## Step 5: Test the Configuration

Run the following command to test your configuration:

```bash
python -c "
import asyncio
from config.settings import settings
print(f'API Key configured: {bool(settings.GOOGLE_API_KEY)}')
print(f'Search Engine ID configured: {bool(settings.GOOGLE_CUSTOM_SEARCH_ENGINE_ID)}')
"
```

## How It Works

The Google Custom Search API is used in the talent identification process:

1. **Search Queries**: For each idea, the system searches for experts in relevant domains
2. **Result Parsing**: Search results are parsed to extract candidate information:
   - Name extraction using regex patterns
   - Organization detection
   - Position/title identification
   - Location extraction
   - Experience estimation
   - Education level detection
3. **Scoring**: Candidates are scored based on:
   - Relevance to the idea domain
   - Academic/professional credentials
   - Organization quality
   - Information completeness

## Search Patterns

The system searches for patterns like:
- `"public health" "malaria" expert researcher professor`
- `"education" "pedagogy" expert researcher professor`
- `"climate change" "carbon removal" expert researcher professor`

## Rate Limits and Costs

- **Free Tier**: 100 queries per day
- **Paid Tier**: $5 per 1000 queries
- **Rate Limiting**: The system includes 1-second delays between requests

## Troubleshooting

### Common Issues

1. **"Google API key not available"**
   - Check that `GOOGLE_API_KEY` is set in your `.env` file
   - Verify the API key is correct and not restricted

2. **"Google Custom Search Engine ID not available"**
   - Check that `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` is set in your `.env` file
   - Verify the Search Engine ID is correct

3. **"Google Custom Search API returned status 403"**
   - Check that billing is enabled on your Google Cloud project
   - Verify the API key has access to Custom Search API

4. **"No candidates found"**
   - This might be normal if search results don't match the parsing patterns
   - Check that your Custom Search Engine is configured to search the entire web

### Testing

To test the functionality:

1. Start the API server: `python run.py` (option 1)
2. Run the prototype pipeline
3. Check the talent identification results in the web interface

## Security Notes

- Keep your API key secure and don't commit it to version control
- Consider restricting the API key to only the Custom Search API
- Monitor your usage to avoid unexpected charges

## Alternative Approaches

If you don't want to use Google Custom Search API:

1. **Mock Data**: The system will fall back to mock data if the API is not configured
2. **Other APIs**: You could modify the code to use other search APIs (Bing, DuckDuckGo, etc.)
3. **Manual Input**: You could implement a manual talent input system

## Support

For issues with:
- **Google Cloud Platform**: Check the [Google Cloud documentation](https://cloud.google.com/docs)
- **Custom Search API**: Check the [Custom Search API documentation](https://developers.google.com/custom-search/v1/overview)
- **This Application**: Check the main README.md or create an issue in the repository
