import json
from pathlib import Path
from typing import Dict, List
from openai import OpenAI
from config import OPENAI_API_KEY, PROMPT_TEMPLATE
from tqdm import tqdm
import time
from tenacity import retry, wait_exponential, stop_after_attempt

client = OpenAI(api_key=OPENAI_API_KEY)

def process_session(session_dir: Path, defs: Dict):
    """Process all items with synchronous API calls"""
    processed_dir = session_dir / "processed"
    processed_dir.mkdir(exist_ok=True)
    
    all_results = {}
    summary_stats = {}

    for raw_file in tqdm(list((session_dir / "raw").glob("*.json")), desc="Processing files"):
        if "_reddit.json" in raw_file.name or "_twitter.json" in raw_file.name:
            keyword, platform, items = process_file(raw_file, defs)
            all_results.setdefault(keyword, {}).setdefault(platform, []).extend(items)
            update_summary(summary_stats, keyword, platform, items)

    save_results(processed_dir, all_results, summary_stats)

def process_file(raw_file: Path, defs: Dict):
    """Process a single file with rate limiting"""
    parts = raw_file.stem.split("_")
    keyword = parts[0]
    platform = parts[1]
    
    with open(raw_file) as f:
        items = json.load(f)

    classified = []
    for item in tqdm(items, desc=f"Processing {platform} {keyword}", leave=False):
        try:
            classification = classify_text(
                text=item["text"],
                keyword=keyword,
                old_def=defs[keyword]["old"],
                new_def=defs[keyword]["new"]
            )
            classified.append({
                **item,
                "classification": classification
            })
        except Exception as e:
            print(f"Error processing {item['id']}: {str(e)[:100]}")
            classified.append({
                **item,
                "classification": "error"
            })
        time.sleep(1.2)
    
    return keyword, platform, classified

@retry(wait=wait_exponential(multiplier=1, min=4, max=60), stop=stop_after_attempt(3))
def classify_text(text: str, keyword: str, old_def: str, new_def: str) -> str:
    """Classify text using OpenAI API with retries"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": PROMPT_TEMPLATE.format(
                keyword=keyword,
                text=text,
                old=old_def,
                new=new_def
            )
        }],
        temperature=0.1,
        max_tokens=1
    )
    
    result = response.choices[0].message.content.strip().lower()
    return result if result in {"old", "new"} else "unknown"

def save_results(processed_dir: Path, all_results: Dict, summary_stats: Dict):
    """Save classified data and summary statistics"""
    
    for keyword, platforms in all_results.items():
        output_file = processed_dir / f"{keyword}_classified.json"
        with open(output_file, "w") as f:
            json.dump(platforms, f, indent=2)

    summary_file = processed_dir / "summary_stats.json"
    with open(summary_file, "w") as f:
        json.dump(summary_stats, f, indent=2)

def update_summary(stats: Dict, keyword: str, platform: str, items: List):
    """Update summary statistics"""
    counts = stats.setdefault(keyword, {}).setdefault(platform, {
        "total": 0,
        "old": 0,
        "new": 0,
        "unknown": 0,
        "error": 0
    })
    
    for item in items:
        counts["total"] += 1
        counts[item["classification"]] += 1

    for cat in ["old", "new", "unknown", "error"]:
        if counts["total"] > 0:
            counts[f"{cat}_pct"] = round(counts[cat] / counts["total"] * 100, 1)

if __name__ == "__main__":
    session_path = Path("tmp/output/session_20250427-201409")
    defs = {
        "slay": {"old": "To kill violently", "new": "To have a strong favorable effect; to be remarkably impressive"},
        "flex": {"old": "To bend something", "new": "An act of bragging or showing off"},
        "lit": {"old": "Past tense of light", "new": "Exciting/awesome, general term of approval"},
        "sigma": {"old": "Greek letter", "new": "Something extremely good/a coolly independent, successful person"}
    }
    process_session(session_path, defs)