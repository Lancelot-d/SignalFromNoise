"""Main application entry point for Reddit Build Opportunity Analyzer."""
from datetime import datetime
from config import Config
from llm_client import LLMClient
from email_client import EmailClient
from reddit_scraper import fetch_posts_from_subreddits
import random


class BuildOpportunityAnalyzer:
    """Analyzes Reddit posts for monetizable build opportunities."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm_client = LLMClient(api_key=config.together_api_key)
        self.email_client = EmailClient(
            smtp_server=config.smtp_server,
            smtp_port=config.smtp_port,
            sender_email=config.sender_email,
            sender_password=config.sender_password
        )
    
    def run(self) -> None:
        """Execute the analysis."""
        print("=" * 60)
        print("🚀 Reddit Build Opportunity Analyzer")
        print("=" * 60)
        
        # Fetch posts
        print(f"\n🔍 Fetching from: {', '.join(f'r/{s}' for s in self.config.subreddits)}")
        posts = fetch_posts_from_subreddits(
            subreddits=self.config.subreddits,
            category="top",
            time_filter=self.config.time_filter,
            posts_per_subreddit=self.config.posts_per_subreddit,
            proxy=self.config.proxy
        )
        
        # Shuffle posts for variety
        random.shuffle(posts)
        print(f"📊 Found {len(posts)} posts (shuffled for variety)")
        
        if not posts:
            print("⚠️  No posts found. Exiting.")
            return
        
        # Analyze opportunities
        print("🤖 Analyzing build opportunities...")
        analysis = self.llm_client.analyze_build_opportunity(posts=posts, max_posts=10)
        print("✅ Analysis complete\n")
        
        # Send email
        print(f"📧 Sending to: {', '.join(self.config.recipient_emails)}")
        success = self.email_client.send_analysis(
            recipients=self.config.recipient_emails,
            content=analysis,
            date_str=datetime.now().strftime("%B %d, %Y")
        )
        
        print("=" * 60)
        print("✅ Completed!" if success else "⚠️  Email failed")
        print("=" * 60)


def main():
    """Application entry point."""
    try:
        BuildOpportunityAnalyzer(Config.from_env()).run()
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()

