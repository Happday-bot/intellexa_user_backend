#!/usr/bin/env python
"""
MongoDB Migration Script
Migrates all data from JSON files to MongoDB
Run this script once to migrate existing data
"""

import os
import json
from database import db

def migrate_from_json_files():
    """Migrate data from JSON files to MongoDB collections"""
    
    json_mapping = {
        "events": "events.json",
        "news": "news.json",
        "code_challenges": "code_challenges.json",
        "hackathons": "hackathons.json",
        "roadmaps": "roadmaps.json",
        "domains": "domains.json",
        "stats": "stats.json",
        "meetups": "meetups.json",
        "broadcasts": "broadcasts.json",
        "feedback": "feedback.json",
        "team_finder": "team_finder.json",
        "users": "users.json",
        "core_members": "core_members.json",
        "volunteers": "volunteers.json",
        "progress": "progress.json",
        "tickets": "tickets.json",
        "checkins": "checkins.json"
    }
    
    print("=" * 60)
    print("MongoDB Data Migration from JSON Files")
    print("=" * 60)
    
    for coll_name, file_name in json_mapping.items():
        if os.path.exists(file_name):
            coll = db.get_collection(coll_name)
            existing_count = coll.count_documents({})
            
            if existing_count == 0:
                print(f"\n📥 Migrating {file_name} → {coll_name}...")
                try:
                    with open(file_name, "r", encoding='utf-8') as f:
                        data = json.load(f)
                        
                        if isinstance(data, list) and data:
                            # Insert list of documents
                            result = coll.insert_many(data)
                            print(f"   ✓ Inserted {len(result.inserted_ids)} documents")
                        elif isinstance(data, dict) and data:
                            if coll_name == "progress":
                                # Special handling for progress.json (dict with userId keys)
                                docs = []
                                for uid, progress in data.items():
                                    if isinstance(progress, dict):
                                        progress["userId"] = uid
                                    docs.append(progress)
                                if docs:
                                    result = coll.insert_many(docs)
                                    print(f"   ✓ Inserted {len(result.inserted_ids)} progress documents")
                            else:
                                # Single document (unlikely but handle gracefully)
                                result = coll.insert_one(data)
                                print(f"   ✓ Inserted 1 document")
                        else:
                            print(f"   ⓘ Empty or invalid JSON file")
                except json.JSONDecodeError as e:
                    print(f"   ✗ JSON Parse Error: {e}")
                except Exception as e:
                    print(f"   ✗ Error migrating: {e}")
            else:
                print(f"\n⊘ Skipping {coll_name} ({existing_count} documents already exist)")
        else:
            print(f"\n⊘ Skipping {coll_name} (JSON file not found: {file_name})")
    
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    
    for coll_name in json_mapping.keys():
        count = db.count_documents(coll_name)
        print(f"{coll_name:20} : {count:4} documents")
    
    print("=" * 60)
    print("✓ Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    migrate_from_json_files()
