"""LLM client for interacting with Together AI API."""
from typing import List, Dict, Any
from together import Together


class LLMClient:
    """Client for interacting with Together AI's LLM API."""
    
    def __init__(self, api_key: str, model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"):
        """Initialize LLM client."""
        self._client = Together(api_key=api_key)
        self._model = model
    
    def analyze_build_opportunity(self, posts: List[Dict[str, Any]], max_posts: int = 10) -> str:
        """Analyze Reddit posts for monetizable build opportunities."""
        posts_content = []
        
        for i, post in enumerate(posts[:max_posts], 1):
            comments = ""
            if post.get('top_comments'):
                comments = "\nTop Comments:\n" + "\n".join(
                    f"  - {c[:200]}" for c in post['top_comments'][:5]
                )
            
            posts_content.append(
                f"Post #{i}:\n"
                f"Title: {post['title']}\n"
                f"Subreddit: r/{post['subreddit']}\n"
                f"Score: {post['score']} | Comments: {post['num_comments']}\n"
                f"Content: {post.get('selftext', '')[:500] or '(Link post)'}{comments}\n"
                f"URL: {post['permalink']}"
            )
        
        combined_posts = "\n\n".join(posts_content)
        
        prompt = f"""You are a product and monetization strategist helping a solo software developer.
                I will paste multiple Reddit posts. Extract ALL viable build ideas that could generate recurring monthly revenue.

                Context:
                - Solo developer, limited time, prefers simple, shippable products
                - Goal: small tools/services that can earn predictable monthly revenue (SaaS, subscriptions)
                - Comfortable with web apps, APIs, automation, integrations

                Your task:
                Extract EVERY viable build opportunity from the posts. For each idea, provide a 1-2 sentence pitch.

                CRITICAL: Output ONLY clean HTML (no html/head/body tags, just content divs).

                Format EXACTLY like this:

                <div class="opportunities">
                <div class="idea">
                    <h3>💡 [Concrete product name - e.g., "Reddit Post Scheduler API"]</h3>
                    <p><strong>Target:</strong> [Specific user - e.g., "Social media managers handling 5+ clients"]</p>
                    <p><strong>Pitch:</strong> [1-2 sentences explaining what it does and why someone would pay monthly for it]</p>
                    <p><strong>Price:</strong> [$19-79/month or pricing model]</p>
                </div>
                
                <div class="idea">
                    <h3>💡 [Next idea...]</h3>
                    <p><strong>Target:</strong> [...]</p>
                    <p><strong>Pitch:</strong> [...]</p>
                    <p><strong>Price:</strong> [...]</p>
                </div>
                </div>

                Style rules:
                - Extract 3-10 ideas depending on how many viable opportunities exist in the posts
                - Each idea MUST be concrete and specific, not generic
                - Focus on narrow, niche problems over broad "for everyone" ideas
                - Avoid vague "AI-powered platform" wording
                - Don't repeat ideas; each must be unique
                - If the post is irrelevant, skip it
                - Only include ideas that necessarily derive from the posts' content
                - Only include ideas that need development work to build (no content creation ideas)
                - If NO viable opportunities exist, output: <div class="no-ideas"><p>No viable build opportunities found.</p></div>

                Reddit Posts:
                {combined_posts}
                """
                
        return self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content

