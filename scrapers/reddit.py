from praw import Reddit
from praw.models import Submission
from config import REDDIT_CREDENTIALS
import uuid
from utils import is_valid_text, is_english, save_checkpoint, load_checkpoint, remove_checkpoint, SESSION_DIR
from config import CHECKPOINT_INTERVAL
import time
from logger import setup_logger

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
    logger = setup_logger("reddit", SESSION_DIR)
    logger.info(f"\n{'='*50}")
    logger.info(f"Starting Reddit search for: {keyword}")
    logger.info(f"Target count: {limit}")
    logger.info(f"Checkpoint interval: {CHECKPOINT_INTERVAL}")
    logger.info(f"{'='*50}\n")

    # load existing progress if any
    results, seen_ids = load_checkpoint(keyword, "reddit")
    if len(results) >= limit:
        logger.info(f"Loaded {len(results)} existing results from checkpoint")
        return results[:limit]

    reddit = Reddit(
        client_id=REDDIT_CREDENTIALS["client_id"],
        client_secret=REDDIT_CREDENTIALS["client_secret"],
        user_agent=REDDIT_CREDENTIALS["user_agent"],
        username=REDDIT_CREDENTIALS["username"],
        password=REDDIT_CREDENTIALS["password"],
    )

    search_params = [
        (st, so, tf)
        for st in [keyword, f'body:"{keyword}"', f'title:"{keyword}"',f'comment:"{keyword}"']
        for so in ["relevance", "hot", "new", "top", "comments"]
        for tf in ["all", "year", "month", "week", "day", "hour"]
    ]

    try:
        for search_term, sort_option, time_filter in search_params:

            logger.info(f"Searching: {search_term} ({sort_option}/{time_filter})")
            submissions = reddit.subreddit('all').search(
                query=search_term,
                time_filter=time_filter,
                limit=100,
                sort=sort_option,
            )

            for submission in submissions:
                if submission.id in seen_ids:
                    logger.debug(f"Skipping duplicate: {submission.id}")
                    continue
                
                seen_ids.add(submission.id)
                result = process_submission(submission)
                
                if not should_keep_submission(result["text"]):
                    logger.debug(f"Rejected submission {submission.id} - validation failed")
                    continue
                
                results.append(result)
                logger.info(f"Collected {len(results)}/{limit}")

                if len(results) % CHECKPOINT_INTERVAL == 0:
                    save_checkpoint(keyword, "reddit", results, seen_ids)
                    logger.info(f"Checkpoint saved at {len(results)} items")

                if len(results) >= limit:
                    break

            time.sleep(1)  # avoid hitting reddits rate limit
            if len(results) >= limit:
                 break

    finally:
        if len(results) >= limit:
            remove_checkpoint(keyword, "reddit")
            logger.info("Checkpoint removed - collection complete")
        else:
            save_checkpoint(keyword, "reddit", results, seen_ids)
            logger.info(f"Saved interim checkpoint with {len(results)} items")

    return results[:limit]

if __name__ == "__main__":
    keyword = "simp"
    limit = 200
    
    posts = reddit_search(keyword, limit)
    
    print(f"\n{'='*50}")
    print(f"Reddit Research Report for: '{keyword}'")
    print(f"Total collected: {len(posts)}/{limit}")
    print(f"{'='*50}\n")