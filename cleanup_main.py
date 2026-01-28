"""
Cleanup script to remove old hardcoded data from main.py
"""
import re

# Read main.py
with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "# Persistence for Teams" after the JSON loading
persistence_line = None
for i, line in enumerate(lines):
    if '# Persistence for Teams' in line and i > 260:
        # Check if the previous lines have the JSON loading code
        if any('load_data(BROADCASTS_FILE' in lines[j] for j in range(max(0, i-10), i)):
            persistence_line = i
            break

if persistence_line:
    # Find the next occurrence of "# Persistence for Teams" or "CORE_MEMBERS_FILE"
    next_section = None
    for i in range(persistence_line + 1, len(lines)):
        if 'CORE_MEMBERS_FILE' in lines[i]:
            next_section = i
            break
    
    if next_section:
        # Remove all lines between persistence_line and next_section
        new_lines = lines[:persistence_line+1] + lines[next_section:]
        
        # Write back
        with open('main.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"✓ Removed {next_section - persistence_line - 1} lines of old hardcoded data")
        print(f"  From line {persistence_line+2} to line {next_section}")
    else:
        print("Could not find next section")
else:
    print("Could not find persistence line")

print("\nCleanup complete!")
