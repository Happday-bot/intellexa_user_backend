"""
Migration script to extract hardcoded data from main.py and save to JSON files.
Run this once to populate all JSON files with existing data.
"""
import json
import re

# Read main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Helper function to extract Python list/dict from code
def extract_data_structure(content, var_name):
    pattern = rf'{var_name}\s*=\s*(\[[\s\S]*?\n\])'
    match = re.search(pattern, content)
    if match:
        try:
            # Use eval carefully - only for migration
            data = eval(match.group(1))
            return data
        except:
            print(f"Failed to extract {var_name}")
            return []
    return []

# Extract all data structures
print("Extracting data from main.py...")

events = extract_data_structure(content, 'EVENTS')
news = extract_data_structure(content, 'NEWS_ITEMS')
code_challenges = extract_data_structure(content, 'CODE_QUESTIONS')
hackathons = extract_data_structure(content, 'HACKATHONS')
roadmaps = extract_data_structure(content, 'ROADMAPS')
domains = extract_data_structure(content, 'DOMAINS')
stats = extract_data_structure(content, 'STATS')
meetups = extract_data_structure(content, 'MEETUPS')

# Save to JSON files
files_to_create = {
    'code_challenges.json': code_challenges,
    'domains.json': domains,
    'roadmaps.json': roadmaps,
}

for filename, data in files_to_create.items():
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✓ Created {filename} with {len(data)} items")

print("\nMigration complete! All JSON files have been populated.")
print("You can now update main.py to load from these files.")
