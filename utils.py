import re
from langdetect import detect, LangDetectException
import json
import os
from config import CHECKPOINT_DIR, OUTPUT_DIR, AMOUNT, KEYWORDS
from datetime import datetime

def is_valid_text(text: str) -> bool:
    cleaned_text = re.sub(r'http\S+|\n|[^\w\s]', ' ', text, flags=re.IGNORECASE) # Remove URLs
    words = re.findall(r'\b[a-z]+\b', cleaned_text, flags=re.IGNORECASE)
    return len(words) > 1

def is_english(text: str) -> bool:
    try:
        # Require at least 3 characters for reliable detection
        if len(text.strip()) < 3:
            return False
        return detect(text) == 'en'
    except LangDetectException:
        return False
    
def contains_keyword(text: str, keyword: str) -> bool:
    """Check if text contains the keyword"""
    return re.search(rf'\b{re.escape(keyword)}\b', text, re.IGNORECASE) is not None

def load_checkpoint(keyword, platform):
    """Load existing progress from checkpoint file"""
    file = CHECKPOINT_DIR / f"{keyword}_{platform}.json"
    if os.path.exists(file):
        with open(file, 'r') as f:
            data = json.load(f)
            return data['results'], set(data['seen_ids'])
    return [], set()

def save_checkpoint(keyword, platform, results, seen_ids):
    """Save current progress to checkpoint file"""
    file = CHECKPOINT_DIR / f"{keyword}_{platform}.json"
    with open(file, 'w') as f:
        json.dump({'results': results, 'seen_ids': list(seen_ids)}, f)

def remove_checkpoint(keyword, platform):
    """Remove checkpoint file"""
    file = CHECKPOINT_DIR / f"{keyword}_{platform}.json"
    if os.path.exists(file):
        os.remove(file)

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
        "keywords": KEYWORDS,
        "target_amount": AMOUNT
    }
    with (session_dir / "session_meta.json").open("w") as f:
        json.dump(metadata, f)
    
    return session_dir

SESSION_DIR = create_session_dir() # created every time the script is run