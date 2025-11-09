# Social Media Auto-Posting System

## Twitter Auto Poster

**Script:** `twitter_auto_poster.py`

### Features
- ✅ Posts fresh tweets every 6 hours (not quote tweets)
- ✅ Automatically uploads images from `twitter_images/` folder
- ✅ Rotates through 8 different tweet templates
- ✅ Fetches real-time member count from API
- ✅ Runs until Sunday 11/10/2025 6:00 AM UTC
- ✅ Auto-posts "Beta Closed" tweet when deadline passes

### How It Works

1. **Every 6 hours**, the bot:
   - Fetches current beta member count
   - Selects a tweet template (rotates based on member count)
   - Selects an image from `twitter_images/` folder (rotates)
   - Posts tweet with image to Twitter/X

2. **At deadline**, the bot:
   - Posts final "Beta Closed" tweet
   - Shuts down automatically

### Adding New Images

1. Save your images to: `C:\Users\nashr\backend\social_media\twitter_images\`
2. Supported formats: `.jpg`, `.jpeg`, `.png`
3. Recommended size: 1200x675px (Twitter recommended)
4. The bot will automatically include new images in rotation
5. **No need to restart the bot** - it checks for images each time

### Current Images

1. `01_extension.jpg` - Browser extension screenshot
2. `02_gamecard_nfl.jpg` - NFL game card
3. `03_analytics.jpg` - Analytics dashboard
4. `04_strategies.jpg` - Strategies page
5. `05_pricing_banner.jpg` - Pricing banner

### Tweet Templates

The bot rotates through 8 different messages covering:
- Product features (live odds, alerts, auto-betting)
- Social proof (member count, ROI stats)
- Urgency (beta deadline, price increase)
- Specific strategies (Goalie Pull, Quarter Reversal)

### Running the Bot

**Start the bot:**
```bash
cd C:\Users\nashr\backend\social_media
python twitter_auto_poster.py
```

**Run in background (Windows):**
```bash
start /B python twitter_auto_poster.py > twitter_bot.log 2>&1
```

**Check if running:**
```bash
tasklist | findstr python
```

**View logs:**
```bash
type twitter_bot.log
```

**Stop the bot:**
Close the terminal or use Task Manager to kill the Python process.

### Testing Before Launch

**Test single post (see `test_twitter_post.py`):**
```bash
python test_twitter_post.py
```

This will post ONE tweet so you can verify:
- Tweet text looks good
- Image uploads correctly
- Links work
- Hashtags display properly

### Posting Schedule

- **Posts per day:** 4 (every 6 hours)
- **Total posts until Sunday:** ~12 posts
- **Cost:** $0 (free Twitter API)

### Expected Performance

Based on industry averages:
- **Reach:** Your followers + hashtag discovery
- **Engagement rate:** 1-3% typical for organic posts
- **Click-through rate:** 0.5-2% to pricing page

### Monitoring

Check Twitter to see:
- Are posts going live every 6 hours?
- Are images displaying correctly?
- Are hashtags working?
- Any engagement (likes, retweets, clicks)?

### Troubleshooting

**Bot not posting:**
- Check if Python process is still running
- Check internet connection
- Verify Twitter API credentials are valid
- Look for error messages in console/log

**Images not uploading:**
- Verify images exist in `twitter_images/` folder
- Check file formats are .jpg, .jpeg, or .png
- Ensure images aren't corrupted
- Check file permissions

**API rate limits:**
- Twitter allows 300 posts per 3 hours
- At 1 post every 6 hours, you're well within limits

---

## Future: Multi-Platform Posting

### Coming Soon

**Facebook Auto-Poster:**
- Requires Facebook Business account
- Will post to Facebook Page
- Same images/messages as Twitter

**Instagram Auto-Poster:**
- Requires Instagram Business account linked to Facebook
- Optimized image sizes (1080x1080)
- Hashtag optimization for Instagram

### Not Recommended Yet

**TikTok:**
- API too restrictive for small businesses
- Better to post manually for now
- Focus on short video content (15-60 seconds)

---

## Configuration

### Twitter API Credentials
Located in `twitter_auto_poster.py` lines 8-12

### Beta Deadline
Line 15: `BETA_DEADLINE = "2025-11-10T06:00:00Z"`

### Images Folder
Line 19: `IMAGES_FOLDER = os.path.join(SCRIPT_DIR, "twitter_images")`

### Posting Interval
Line 294: `time.sleep(6 * 3600)` (6 hours in seconds)

To post more frequently, change to:
- `time.sleep(3 * 3600)` for 3 hours
- `time.sleep(1 * 3600)` for 1 hour
- `time.sleep(30 * 60)` for 30 minutes

---

## Beta Campaign Stats to Track

After launching, track these metrics:

**Twitter Analytics (analytics.twitter.com):**
- Impressions (how many people saw tweets)
- Engagements (likes, retweets, clicks)
- Link clicks (traffic to pricing page)
- Follower growth

**Website Analytics:**
- Traffic from Twitter (source/medium: twitter / social)
- Conversions from Twitter traffic
- Time on site for Twitter visitors

**Business Metrics:**
- Beta signups correlated with tweet times
- Cost per signup: $0 (organic)
- ROI: Infinite (no ad spend)

---

**Last Updated:** November 7, 2025
