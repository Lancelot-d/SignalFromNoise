# Reddit Recap - SignalFromNoise

Automatically extracts interesting ideas from Reddit, summarizes them using AI, and delivers a curated recap via email.

## 🎯 Key Features

- **Automated Reddit monitoring** - Fetch top posts from multiple subreddits
- **AI-powered summarization** - Uses Together AI to extract key insights and ideas
- **Email delivery** - Sends beautifully formatted HTML recaps to your inbox
- **Customizable** - Configure subreddits, time filters, and post limits
- **Zero infrastructure** - Run locally or schedule with cron/GitHub Actions

## 🚀 Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Create Reddit App:**
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Choose "script" as the app type
   - Note your `client_id` and `client_secret`

3. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     - Reddit API credentials
     - Together AI API key (from https://api.together.xyz/)
     - Email settings (Gmail recommended - use app-specific password)
     - Subreddits to monitor
     - Recipient email address

4. **Run the application:**
   ```bash
   python src/main.py
   ```

## 📧 Email Configuration

For Gmail users:
1. Enable 2-factor authentication
2. Generate an app-specific password: https://myaccount.google.com/apppasswords
3. Use this password in your `.env` file

## ⚙️ Configuration Options

Edit `.env` to customize:
- `SUBREDDITS` - Comma-separated list of subreddits to monitor
- `TIME_FILTER` - Time period: `hour`, `day`, `week`, `month`, `year`, `all`
- `POSTS_PER_SUBREDDIT` - Number of posts to fetch per subreddit
- Email settings for delivery

## 🤖 How It Works

1. **Fetch** - Retrieves top posts from configured subreddits
2. **Analyze** - Uses AI to extract key insights and categorize ideas
3. **Summarize** - Generates a clean, readable recap
4. **Deliver** - Sends HTML-formatted email with all the highlights

## 🛠️ Tech Stack

- Python 3.10+
- Reddit API (OAuth2)
- Together AI (LLM summarization)
- SMTP (Email delivery)

## 📄 License

See [LICENSE](LICENSE) for details.

