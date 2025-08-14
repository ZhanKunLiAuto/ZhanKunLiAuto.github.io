# Google Scholar Integration

This Jekyll site now includes automatic Google Scholar statistics fetching functionality.

## Features

- Automatically fetches and displays:
  - Total number of papers
  - Total citations
  - h-index
  - i10-index
- Caches results for 24 hours to avoid excessive API requests
- Graceful error handling with fallback values

## Configuration

1. Add your Google Scholar ID to `_config.yml`:

   ```yaml
   google_scholar_id: YOUR_SCHOLAR_ID
   ```

   You can find your Scholar ID in your Google Scholar profile URL:
   `https://scholar.google.com/citations?user=YOUR_SCHOLAR_ID&hl=en`

2. The plugin is already installed in `_plugins/google-scholar-stats.rb`

## Usage

The plugin can be used either as a Liquid **filter** or **tag**.

### Filter style

```liquid
{% raw %}
{% assign scholar_stats = site.google_scholar_id | google_scholar_stats %}

- Papers: {% scholar_stat scholar_stats papers %} - Citations: {% scholar_stat scholar_stats citations %} - h-index: {% scholar_stat scholar_stats h_index %} - i10-index: {% scholar_stat scholar_stats i10_index %}
{% endraw %}
```

### Tag style

```liquid
{% raw %}
{% capture scholar_stats %}{% google_scholar_stats site.google_scholar_id %}{% endcapture %}

- Papers: {% scholar_stat scholar_stats papers %} - Citations: {% scholar_stat scholar_stats citations %} - h-index: {% scholar_stat scholar_stats h_index %} - i10-index: {% scholar_stat scholar_stats i10_index %}
{% endraw %}
```

## Cache Management

- The plugin caches results in `.google_scholar_cache.json`
- Cache expires after 24 hours
- The cache file is automatically excluded from git

## Testing

To test the Google Scholar integration locally:

1. Make sure you have Ruby and required gems installed
2. Run the test script: `ruby test_google_scholar.rb`

## Troubleshooting

If the stats show "N/A":

1. Check your Google Scholar ID is correct
2. Ensure your profile is public
3. Check for rate limiting (wait a few minutes and try again)
4. Look for error messages in the Jekyll build output

## Notes

- Google Scholar may rate-limit requests, so the plugin includes random delays
- The plugin fetches up to 100 papers (Google Scholar's maximum per page)
- Statistics are from the "All" column in Google Scholar (not "Since 2019")
