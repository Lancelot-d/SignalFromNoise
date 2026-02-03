"""Reddit scraper for fetching posts and comments."""

import time
import random
import logging
from typing import Any
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    filename="reddit_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)

# User agents for requests
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
)


class RandomUserAgentSession(Session):
    """Session that uses random user agents for requests."""

    def request(self, *args, **kwargs) -> requests.Response:
        self.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        return super().request(*args, **kwargs)


class RedditScraper:
    """Reddit scraper using Reddit's JSON API."""

    def __init__(self, timeout: int = 10, random_user_agent: bool = True) -> None:
        self.session = RandomUserAgentSession() if random_user_agent else requests.Session()
        self.timeout = timeout
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def fetch_subreddit_posts(
        self,
        subreddit: str,
        limit: int = 10,
        category: str = "hot",
        time_filter: str = "day",
    ) -> list[dict]:
        """Fetch posts from a subreddit."""
        if category not in ["hot", "top", "new"]:
            raise ValueError("Category must be 'hot', 'top', or 'new'")

        LOGGER.info("Fetching posts from r/%s (category: %s, limit: %d, time: %s)",
                    subreddit, category, limit, time_filter)

        batch_size = min(100, limit)
        total_fetched = 0
        after = None
        all_posts = []
        url = f"https://www.reddit.com/r/{subreddit}/{category}.json"

        while total_fetched < limit:
            params = {
                "limit": batch_size,
                "after": after,
                "raw_json": 1,
                "t": time_filter,
            }

            try:
                response = self.session.get(url, timeout=self.timeout, params=params)
                response.raise_for_status()
                LOGGER.info("Successfully fetched batch from r/%s", subreddit)
            except requests.RequestException as e:
                LOGGER.error("Failed to fetch posts from r/%s: %s", subreddit, e)
                print(f"Error fetching posts from r/{subreddit}: {e}")
                break

            data = response.json()
            posts = data.get("data", {}).get("children", [])
            
            if not posts:
                break

            for post in posts:
                post_data = post["data"]
                post_info = {
                    "title": post_data.get("title", ""),
                    "author": post_data.get("author", ""),
                    "subreddit": subreddit,
                    "permalink": post_data.get("permalink", ""),
                    "score": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "created_utc": post_data.get("created_utc", 0),
                    "selftext": post_data.get("selftext", ""),
                }
                
                if post_data.get("post_hint") == "image" and "url" in post_data:
                    post_info["image_url"] = post_data["url"]
                elif "preview" in post_data and "images" in post_data["preview"]:
                    post_info["image_url"] = post_data["preview"]["images"][0]["source"]["url"]
                
                if "thumbnail" in post_data and post_data["thumbnail"] not in ("self", "default"):
                    post_info["thumbnail_url"] = post_data["thumbnail"]

                all_posts.append(post_info)
                total_fetched += 1
                
                if total_fetched >= limit:
                    break

            after = data.get("data", {}).get("after")
            if not after:
                break

            time.sleep(random.uniform(1, 2))

        LOGGER.info("Successfully fetched %d posts from r/%s", len(all_posts), subreddit)
        return all_posts

    def scrape_post_details(self, permalink: str) -> dict[str, Any] | None:
        """Scrape detailed information from a specific post."""
        url = f"https://www.reddit.com{permalink}.json"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            LOGGER.info("Successfully fetched post details: %s", permalink)
        except requests.RequestException as e:
            LOGGER.error("Failed to fetch post details %s: %s", permalink, e)
            print(f"Error fetching post details: {e}")
            return None

        post_data = response.json()
        
        if not isinstance(post_data, list) or len(post_data) < 2:
            LOGGER.warning("Unexpected post data structure for %s", permalink)
            return None

        main_post = post_data[0]["data"]["children"][0]["data"]
        comments = self._extract_comments(post_data[1]["data"]["children"])
        
        return {
            "title": main_post.get("title", ""),
            "body": main_post.get("selftext", ""),
            "comments": comments
        }

    def _extract_comments(self, comments: list) -> list[dict]:
        """Extract comments and replies recursively."""
        extracted_comments = []
        
        for comment in comments:
            if isinstance(comment, dict) and comment.get("kind") == "t1":
                comment_data = comment.get("data", {})
                
                extracted_comment = {
                    "author": comment_data.get("author", ""),
                    "body": comment_data.get("body", ""),
                    "score": comment_data.get("score", 0),
                    "replies": [],
                }

                replies = comment_data.get("replies", "")
                if isinstance(replies, dict):
                    extracted_comment["replies"] = self._extract_comments(
                        replies.get("data", {}).get("children", [])
                    )
                
                extracted_comments.append(extracted_comment)
        
        return extracted_comments


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    cleaned = text.strip()
    if "[deleted]" in cleaned.lower() or "[removed]" in cleaned.lower():
        return ""
    
    return cleaned


def extract_all_comments_text(comments: list[dict]) -> list[str]:
    """Recursively extract all comment text from a comments tree."""
    all_text = []
    
    for comment in comments:
        body = clean_text(comment.get("body", ""))
        if body:
            all_text.append(body)
        
        if comment.get("replies"):
            all_text.extend(extract_all_comments_text(comment["replies"]))
    
    return all_text


def fetch_posts_from_subreddits(
    subreddits: list[str],
    category: str = "hot",
    time_filter: str = "day",
    posts_per_subreddit: int = 10,
    include_comments: bool = True,
    max_comments_per_post: int = 10
) -> list[dict]:
    """Fetch posts from multiple subreddits."""
    scraper = RedditScraper()
    all_posts = []
    
    for subreddit in subreddits:
        time.sleep(random.uniform(5, 20))
        try:
            posts = scraper.fetch_subreddit_posts(
                subreddit=subreddit,
                limit=posts_per_subreddit,
                category=category,
                time_filter=time_filter
            )
            
            if include_comments:
                for post in posts:
                    try:
                        post_details = scraper.scrape_post_details(post['permalink'])
                        if post_details and post_details.get('comments'):
                            comments_text = extract_all_comments_text(
                                post_details['comments'][:max_comments_per_post]
                            )
                            post['top_comments'] = comments_text[:max_comments_per_post]
                        else:
                            post['top_comments'] = []
                    except Exception as e:
                        print(f"   ⚠️  Failed to fetch comments for post: {e}")
                        post['top_comments'] = []
            
            all_posts.extend(posts)
            print(f"✅ Fetched {len(posts)} posts from r/{subreddit}")
        except Exception as e:
            print(f"❌ Error fetching from r/{subreddit}: {e}")
            return all_posts
        
    return all_posts
