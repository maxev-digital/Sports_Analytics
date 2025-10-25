#!/usr/bin/env python3
"""
Organize NCAA Basketball Model Files - FIXED VERSION
Finds files in subdirectories and copies to correct locations
"""

import shutil
import os

print("="*70)
print("NCAA BASKETBALL MODEL - FILE ORGANIZATION (SMART SEARCH)")
print("="*70)

# Search locations for source files
search_paths = [
    ".",  # Current directory
    "backend/scrapers/ncaab",  # Where user downloaded them
    "backend",
]

# File mappings: (filename, destination)
files_to_find = [
    ("run_ncaab_predictions.py", "run_ncaab_predictions.py"),
    ("ncaab_odds_scraper.py", "backend/scrapers/odds/ncaab_odds_scraper.py"),
    ("totals_predictor.py", "backend/models/ncaab/totals_predictor.py"),
    ("ncaab_sheets_uploader.py", "backend/sheets_integration/ncaab_sheets_uploader.py"),
]

def find_file(filename):
    """Search for file in multiple locations"""
    for search_path in search_paths:
        filepath = os.path.join(search_path, filename)
        if os.path.exists(filepath):
            return filepath
    return None

print("\n📁 Creating directory structure...")

# Create necessary directories
directories = [
    "backend/scrapers/odds",
    "backend/models/ncaab",
    "backend/sheets_integration",
    "backend/data/predictions",
    "backend/data/tracking"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"   ✅ {directory}")

print("\n🔍 Searching for files...")

copied = 0
failed = 0

for filename, dest in files_to_find:
    source = find_file(filename)
    
    if source:
        try:
            # Create destination directory if needed
            dest_dir = os.path.dirname(dest)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.copy2(source, dest)
            print(f"   ✅ Found: {source}")
            print(f"      → Copied to: {dest}")
            copied += 1
        except Exception as e:
            print(f"   ❌ {filename}: {str(e)}")
            failed += 1
    else:
        print(f"   ❌ Not found: {filename}")
        print(f"      Searched: {', '.join(search_paths)}")
        failed += 1

# Create __init__.py files
print("\n📦 Creating __init__.py files...")

init_files = [
    "backend/__init__.py",
    "backend/scrapers/__init__.py",
    "backend/scrapers/odds/__init__.py",
    "backend/models/__init__.py",
    "backend/models/ncaab/__init__.py",
    "backend/sheets_integration/__init__.py"
]

for init_file in init_files:
    os.makedirs(os.path.dirname(init_file), exist_ok=True)
    with open(init_file, 'w') as f:
        f.write("")  # Empty file
    print(f"   ✅ {init_file}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"   ✅ Copied: {copied} files")
if failed > 0:
    print(f"   ❌ Failed: {failed} files")

if copied == len(files_to_find):
    print("\n✅ File organization complete!")
    print("\nNext step:")
    print("   python run_ncaab_predictions.py")
else:
    print("\n⚠️  Some files could not be found")
    print("\nMissing files should be in one of these locations:")
    print("   - C:\\Users\\nashr\\")
    print("   - C:\\Users\\nashr\\backend\\scrapers\\ncaab\\")

print("="*70)