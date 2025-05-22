from scrapers.twitter import scrape_tweets
from scrapers.reddit import reddit_search
from config import AMOUNT, KEYWORDS
from utils import SESSION_DIR, save_data
from analysis.classify import process_session
from logger import setup_logger

if __name__ == "__main__":
    logger = setup_logger("scraper", SESSION_DIR)
    raw = SESSION_DIR / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    print(f"Started session: {SESSION_DIR.name}")
    for keyword in KEYWORDS.keys():
        logger.info(f"Scraping Twitter for keyword: {keyword}")
        tweets = scrape_tweets(keyword, AMOUNT)
        save_data(keyword, tweets, "twitter", raw)

        logger.info(f"Scraping Reddit for keyword: {keyword}")
        submissions = reddit_search(keyword, AMOUNT)
        save_data(keyword, submissions, "reddit", raw)
    
    process_session(SESSION_DIR, KEYWORDS)