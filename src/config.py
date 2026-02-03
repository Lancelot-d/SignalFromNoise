"""Configuration module for managing environment variables and settings."""
import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration class."""
    
    subreddits: List[str]
    together_api_key: str
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    recipient_emails: List[str]
    time_filter: str = "day"  # Options: 'hour', 'day', 'week', 'month', 'year', 'all'
    posts_per_subreddit: int = 10
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Load configuration from environment variables.
        
        Returns:
            Config: Configuration instance with loaded values.
            
        Raises:
            ValueError: If required environment variables are missing.
        """
        load_dotenv()
        
        # Subreddits to monitor (comma-separated)
        subreddits_str = os.getenv("SUBREDDITS", "python,technology,programming")
        subreddits = [s.strip() for s in subreddits_str.split(",")]
        
        # LLM API key
        together_api_key = os.getenv("TOGETHER_API_KEY")
        
        # Email configuration
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        recipient_emails_str = os.getenv("RECIPIENT_EMAILS")
        recipient_emails = [email.strip() for email in recipient_emails_str.split(",")] if recipient_emails_str else []
        
        # Optional settings
        time_filter = os.getenv("TIME_FILTER", "day")
        posts_per_subreddit = int(os.getenv("POSTS_PER_SUBREDDIT", "10"))
        
        # Validate required environment variables
        if not together_api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is required")
        if not sender_email:
            raise ValueError("SENDER_EMAIL environment variable is required")
        if not sender_password:
            raise ValueError("SENDER_PASSWORD environment variable is required")
        if not recipient_emails:
            raise ValueError("RECIPIENT_EMAILS environment variable is required")
        
        return cls(
            subreddits=subreddits,
            together_api_key=together_api_key,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            sender_email=sender_email,
            sender_password=sender_password,
            recipient_emails=recipient_emails,
            time_filter=time_filter,
            posts_per_subreddit=posts_per_subreddit
        )

