from twitter import scrape_tweets
from reddit import reddit_search
from config import OUTPUT_DIR
import json
from datetime import datetime
from classify import process_session

def save_data(keyword, results, scraper_name, directory):    
    json_path = directory / f"{keyword}_{scraper_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def create_session_dir():
    """Create a unique directory for this scraping session"""
    session_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir =  OUTPUT_DIR / f"session_{session_time}"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "start_time": session_time,
        "keywords": keywords,
        "target_amount": amount
    }
    with (session_dir / "session_meta.json").open("w") as f:
        json.dump(metadata, f)
    
    return session_dir

if __name__ == "__main__":
    keywords = {
        "slay": {
            "old": "To kill violently",
            "new": "To have a strong favorable effect; to be remarkably impressive",
        },
        "flex": {
            "old": "To bend muscles",
            "new": "An act of bragging or showing off",
        },
        "lit": {
            "old": "Past tense of light",
            "new": "Exciting/awesome, general term of approval",
        },
        "sigma": {
            "old": "Greek letter",
            "new": "Something extremely good/a coolly independent, successful person",
        }
    }
    amount = 5
    session_dir = create_session_dir()

    raw = session_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    for keyword in keywords.keys():
        print(f"Scraping Twitter for keyword: {keyword}")
        tweets = scrape_tweets(keyword, amount)
        save_data(keyword, tweets, "twitter", raw)

        print(f"Scraping Reddit for keyword: {keyword}")
        submissions = reddit_search(keyword, amount)
        save_data(keyword, submissions, "reddit", raw)
    
    process_session(session_dir, keywords)