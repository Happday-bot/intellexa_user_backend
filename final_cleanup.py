"""
Final cleanup script to remove remaining hardcoded data from main.py
"""
import re

# Read main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the block from line 474 to 745 approximately
# We look for EVENTS = [ and go until # API Endpoints or # --- Domains CRUD ---
pattern = re.compile(r'EVENTS = \[\s*\{[\s\S]*?TEAM_FINDER_POSTS = \[\s*\{[\s\S]*?\}\s*\]\n', re.MULTILINE)

new_content = pattern.sub('', content)

if new_content != content:
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✓ Successfully removed hardcoded data block (EVENTS through TEAM_FINDER_POSTS)")
else:
    print("! Could not find the hardcoded data block using regex")
    # Fallback to line-based removal if needed
    lines = content.splitlines(keepends=True)
    start_line = -1
    end_line = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('EVENTS = ['):
            start_line = i
        if '# --- Domains CRUD ---' in line or '# API Endpoints' in line:
            if start_line != -1:
                end_line = i
                break
    
    if start_line != -1 and end_line != -1:
        new_lines = lines[:start_line] + lines[end_line:]
        with open('main.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"✓ Removed hardcoded data from line {start_line+1} to {end_line}")
    else:
        print("! Fallback line-based detection also failed")

print("\nFinal cleanup complete!")
