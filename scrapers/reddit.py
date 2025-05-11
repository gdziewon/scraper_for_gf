from praw import Reddit
from praw.models import Submission
import time
from config import REDDIT_CREDENTIALS
import uuid
from utils import is_valid_text, is_english

def is_too_long(text: str, max_length: int = 500) -> bool:
    return len(text) > max_length

def should_keep_submission(text: str):
    return (
        not is_too_long(text) and
        is_valid_text(text) and
        is_english(text)
    )

def process_submission(submission: Submission):
    return {
            "uuid": str(uuid.uuid4()),
            "id": submission.id,
            "text": f"{submission.title}\n{submission.selftext}".strip(),
            "url": submission.url,
            "created_at": submission.created_utc,
            "username": submission.author.name if submission.author else "[deleted]",
            "subreddit": submission.subreddit.display_name,
        }

def reddit_search(keyword, limit=100):
    reddit = Reddit(
        client_id=REDDIT_CREDENTIALS["client_id"],
        client_secret=REDDIT_CREDENTIALS["client_secret"],
        user_agent=REDDIT_CREDENTIALS["user_agent"],
        username=REDDIT_CREDENTIALS["username"],
        password=REDDIT_CREDENTIALS["password"],
    )

    results = []
    seen_ids = set()
    search_variants = [
        f'{keyword}',
        f'body:"{keyword}"',
        f'title:"{keyword}"',
        f'comment:"{keyword}"',
        keyword
    ]

    # sort_options = ["relevance", "hot", "new", "top", "comments"] might be needed in some time
    time_filters = ["all", "year", "month", "week", "day"]

    for time_filter in time_filters:
        for search_term in search_variants:
            while True:
                print(f"Searching for '{search_term}' in the last {time_filter}...")
                submissions = reddit.subreddit('all').search(
                    query=search_term,
                    time_filter=time_filter,
                    limit=100,
                    sort="relevance",
                )
                current_seen_ids = len(seen_ids)
                for submission in submissions:
                    if submission.id in seen_ids:
                        continue
                    
                    result = process_submission(submission)
                    seen_ids.add(submission.id)
                    if not should_keep_submission(result["text"]):
                        continue
                    
                    results.append(result)

                    print(f"Collected {len(results)}/{limit}")
                    if len(results) >= limit:
                        return results[:limit]
                    
                if len(seen_ids) == current_seen_ids:
                    break
                time.sleep(2)

    return results[:limit]

if __name__ == "__main__":
    keyword = "simp"
    limit = 200
    
    posts = reddit_search(keyword, limit)
    
    print(f"\n{'='*50}")
    print(f"Reddit Research Report for: '{keyword}'")
    print(f"Total collected: {len(posts)}/{limit}")
    print(f"{'='*50}\n")