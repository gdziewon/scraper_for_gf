import json
from pathlib import Path
from typing import Dict
from openai import OpenAI
from config import OPENAI_API_KEY, PROMPT_TEMPLATE
from analysis.analyze import analyze_batch
import time

client = OpenAI(api_key=OPENAI_API_KEY)

def create_batch_file(session_dir: Path, defs: Dict) -> str:
    """Create JSONL batch input file using existing UUIDs"""
    jsonl_content = ""
    
    for raw_file in (session_dir / "raw").glob("*.json"):
        if "_reddit.json" in raw_file.name or "_twitter.json" in raw_file.name:
            keyword = raw_file.stem.split("_")[0]
            with open(raw_file, encoding="utf8") as f:
                items = json.load(f)
            
            for item in items:
                jsonl_content += json.dumps({
                    "custom_id": item["uuid"],
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4o-mini",
                        "messages": [{
                            "role": "user",
                            "content": PROMPT_TEMPLATE.format(
                                keyword=keyword,
                                text=item["text"],
                                old=defs[keyword]["old"],
                                new=defs[keyword]["new"]
                            )
                        }],
                        "temperature": 0.1,
                        "max_tokens": 1
                    }
                }) + "\n"
    
    # Upload as proper JSONL
    batch_file = client.files.create(
        file=jsonl_content.encode("utf-8"),
        purpose="batch"
    )
    return batch_file.id

def process_session(session_dir: Path, defs: Dict):
    """Process session using Batch API"""
    processed_dir = session_dir / "processed"
    processed_dir.mkdir(exist_ok=True)
    
    # Create and upload batch
    batch_file_id = create_batch_file(session_dir, defs)
    
    # Start batch job
    batch = client.batches.create(
        input_file_id=batch_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    
    print(f"Batch ID: {batch.id} - Status: {batch.status}")
    print(f"Waiting for batch completion...")

    if wait_for_batch_completion(batch.id):
        analyze_batch(session_dir, batch.id)
        print(f"Batch {batch.id} processed successfully!")
        print(f"Results saved in: {processed_dir}")


    
def wait_for_batch_completion(batch_id: str) -> bool:
    wait_time = 60 * 5
    while True:
        batch = client.batches.retrieve(batch_id)
        print(f"\nBatch Status Check: {batch.status} (Updated at {time.strftime('%Y-%m-%d %H:%M:%S')})")
        if batch.status == 'completed':
            print("\nBatch completed! Analyzing results...")
            return True
        
        elif batch.status in ['failed', 'cancelled', 'canceling', 'expired', ]:
            print(f"\nBatch terminated with status: {batch.status}")
            return False
        
        elif batch.status in ['validating', 'in_progress', 'finalizing']:
            print(f"Status of batch: {batch.status} Next check in {wait_time//60} minutes...")
            time.sleep(wait_time)

        else:
            print(f"Unexpected status: {batch.status}. Waiting...")
            time.sleep(wait_time)

if __name__ == "__main__":
    session_path = Path("tmp/output/session_20250427-201409")
    defs = {
        "slay": {"old": "To kill violently", "new": "To have a strong favorable effect"},
        "flex": {"old": "To bend something", "new": "An act of bragging"},
        "lit": {"old": "Past tense of light", "new": "Exciting/awesome"},
        "sigma": {"old": "Greek letter", "new": "Coolly independent person"},
        "simp": {"old": "A foolish person", "new": "Someone who is overly attentive to someone else"},
    }
    process_session(session_path, defs)