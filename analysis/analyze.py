import json
from pathlib import Path
from collections import defaultdict
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_batch(session_dir: Path, batch_id: str):
    """Analyze batch results with proper UUID mapping"""
    processed_dir = session_dir / "processed"
    processed_dir.mkdir(exist_ok=True)
    
    # download
    batch = client.batches.retrieve(batch_id)
    results_content = client.files.content(batch.output_file_id).text
    results = [json.loads(line) for line in results_content.splitlines()]
    
    # Build classification map
    classifications = {}
    for result in results:
        custom_id = result["custom_id"]
        if result["response"]["status_code"] == 200:
            content = result["response"]["body"]["choices"][0]["message"]["content"].lower().strip()
            classifications[custom_id] = content if content in {"old", "new"} else "unknown"
        else:
            classifications[custom_id] = "error"
    
    # Process all raw files
    summary_stats = defaultdict(lambda: defaultdict(lambda: {
        "total": 0, "old": 0, "new": 0, "unknown": 0, "error": 0
    }))
    
    all_classified = []
    
    for raw_file in (session_dir / "raw").glob("*.json"):
        if not ("_reddit.json" in raw_file.name or "_twitter.json" in raw_file.name):
            continue
            
        platform = "reddit" if "reddit" in raw_file.name else "twitter"
        keyword = raw_file.stem.split("_")[0]
        
        with open(raw_file) as f:
            items = json.load(f)
        
        classified_items = []
        for item in items:
            # Get classification using UUID
            classification = classifications.get(item["uuid"], "error")
            classified_item = {
                **item,
                "platform": platform,
                "classification": classification,
                "keyword": keyword
            }
            classified_items.append(classified_item)
            
            # Update stats
            stats = summary_stats[keyword][platform]
            stats["total"] += 1
            stats[classification] += 1
        
        # Save platform-specific results
        output_file = processed_dir / f"{keyword}_{platform}_classified.json"
        with open(output_file, "w") as f:
            json.dump(classified_items, f, indent=2)
        
        all_classified.extend(classified_items)
    
    # Calculate percentages
    for keyword, platforms in summary_stats.items():
        for platform, stats in platforms.items():
            for cat in ["old", "new", "unknown", "error"]:
                if stats["total"] > 0:
                    stats[f"{cat}_pct"] = round(stats[cat] / stats["total"] * 100, 1)
    
    # Save combined results and summary
    combined_file = processed_dir / "all_classified.json"
    with open(combined_file, "w") as f:
        json.dump(all_classified, f, indent=2)
    
    summary_file = processed_dir / "summary_stats.json"
    with open(summary_file, "w") as f:
        json.dump(summary_stats, f, indent=2)

if __name__ == "__main__":
    from config import OUTPUT_DIR
    session_path = OUTPUT_DIR / "session_20250508-203258"
    analyze_batch(session_path, "batch_681cf8f565b08190abf644fe284d6ee4")