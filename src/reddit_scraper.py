"""Reddit scraper using Bright Data Web Unlocker API."""

import time
import random
import logging
import urllib.parse
from typing import Any
import requests

# Configure logging
logging.basicConfig(
    filename="reddit_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)


class RedditScraper:
    """Reddit scraper using Bright Data Web Unlocker API."""

    def __init__(self, brightdata_api_key: str, timeout: int = 30) -> None:
        if not brightdata_api_key:
            raise ValueError("BRIGHTDATA_API_KEY is required")
        
        self.brightdata_api_key = brightdata_api_key
        self.timeout = timeout
        LOGGER.info("Initialized with Bright Data Web Unlocker")
        print("🌐 Using Bright Data Web Unlocker API")
    
    def _make_request(self, url: str, params: dict = None, max_retries: int = 3) -> dict:
        """Make a request using Bright Data Web Unlocker API."""
        # Build full URL with params
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            param_string = urllib.parse.urlencode(clean_params)
            full_url = f"{url}?{param_string}"
        else:
            full_url = url
        
        headers = {
            "Authorization": f"Bearer {self.brightdata_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "zone": "web_unlocker1",
            "url": full_url,
            "format": "raw"
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://api.brightdata.com/request",
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                    
            except requests.exceptions.RequestException as e:
                LOGGER.warning("Request attempt %d/%d failed: %s", attempt + 1, max_retries, e)
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")

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
        base_url = f"https://www.reddit.com/r/{subreddit}/{category}.json"

        while total_fetched < limit:
            params = {
                "limit": batch_size,
                "after": after,
                "raw_json": 1,
                "t": time_filter,
            }
            
            try:
                data = self._make_request(base_url, params=params)
                LOGGER.info("Successfully fetched batch from r/%s", subreddit)
            except Exception as e:
                LOGGER.error("Failed to fetch posts from r/%s: %s", subreddit, e, exc_info=True)
                print(f"❌ Error fetching posts from r/{subreddit}:")
                print(f"   Type: {type(e).__name__}")
                print(f"   Message: {e}")
                break

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
            post_data = self._make_request(url)
            LOGGER.info("Successfully fetched post details: %s", permalink)
        except Exception as e:
            LOGGER.error("Failed to fetch post details %s: %s", permalink, e, exc_info=True)
            print(f"❌ Error fetching post details: {type(e).__name__}: {e}")
            return None
        
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
    brightdata_api_key: str,
    category: str = "hot",
    time_filter: str = "day",
    posts_per_subreddit: int = 10,
    include_comments: bool = True,
    max_comments_per_post: int = 10
) -> list[dict]:
    """Fetch posts from multiple subreddits using Bright Data."""
    scraper = RedditScraper(brightdata_api_key=brightdata_api_key)
    all_posts = []
    
    for subreddit in subreddits:
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
                        LOGGER.warning("Failed to fetch comments: %s", e)
                        post['top_comments'] = []
            
            all_posts.extend(posts)
            print(f"✅ Fetched {len(posts)} posts from r/{subreddit}")
        except Exception as e:
            print(f"❌ Error fetching from r/{subreddit}: {type(e).__name__}: {e}")
            LOGGER.error("Failed to fetch from r/%s: %s", subreddit, e, exc_info=True)
        
    return all_posts
