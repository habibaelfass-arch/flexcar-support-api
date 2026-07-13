import os
import time
import praw
from dotenv import load_dotenv

load_dotenv()

_reddit_instance = None


def get_reddit_client() -> praw.Reddit:
    """Return a singleton PRAW Reddit client authenticated as flexcar_sam."""
    global _reddit_instance
    if _reddit_instance is None:
        _reddit_instance = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            username=os.environ["REDDIT_USERNAME"],
            password=os.environ["REDDIT_PASSWORD"],
            user_agent="flexcar_sam_monitor/1.0 (by u/flexcar_sam)",
            ratelimit_seconds=300,
        )
    return _reddit_instance


def safe_reddit_call(fn, *args, retries: int = 3, backoff: float = 5.0, **kwargs):
    """
    Wrap any PRAW call with retry + exponential backoff.
    Handles rate limits (429) and transient network errors.
    """
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except praw.exceptions.RedditAPIException as e:
            if "RATELIMIT" in str(e).upper():
                wait = backoff * (2 ** attempt)
                print(f"[rate limit] waiting {wait}s before retry {attempt + 1}/{retries}")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            if attempt < retries - 1:
                wait = backoff * (2 ** attempt)
                print(f"[error] {e} — retry {attempt + 1}/{retries} in {wait}s")
                time.sleep(wait)
            else:
                raise
    return None
