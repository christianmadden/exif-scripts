#!/usr/bin/env python3
import os
import re
import subprocess
import glob
import sys
import argparse

def extract_date_from_filename(filename):
    """
    Extract date from filename patterns like:
    - whatever-1987-08-01.jpg
    - whatever-1987.jpg
    - 1987-03.jpg
    
    Returns a tuple of (year, month, day) or None if no date found
    """
    basename = os.path.basename(filename)
    
    full_date_match = re.search(r'-(\d{4})-(\d{2})-(\d{2})(?=\.[^.]+$)', basename)
    if full_date_match:
        year, month, day = full_date_match.groups()
        return (year, month, day)
    
    year_month_match = re.search(r'-(\d{4})-(\d{2})(?=\.[^.]+$)', basename)
    if year_month_match and not full_date_match:
        year, month = year_month_match.groups()
        return (year, month, "01")
    
    year_match = re.search(r'-(\d{4})(?=\.[^.]+$)', basename)
    if year_match and not year_month_match:
        year = year_match.group(1)
        return (year, "01", "01")
    
    return None

def update_exif_date(file_path, date_tuple):
    """
    Update EXIF date information using exiftool
    """
    year, month, day = date_tuple
    date_string = f"{year}:{month}:{day} 12:00:00"
    
    command = [
        "exiftool",
        "-DateTimeOriginal=" + date_string,
        "-CreateDate=" + date_string,
        "-ModifyDate=" + date_string,
        "-overwrite_original",
        file_path
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    parser = argparse.ArgumentParser(description='Update EXIF date information based on filenames.')
    parser.add_argument('path', nargs='?', default='.', help='Path to scan for JPG/JPEG files (default: current directory)')
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.")
        sys.exit(1)
    
    jpg_files = []
    for ext in ('*.jpg', '*.jpeg', '*.JPG', '*.JPEG'):
        jpg_files.extend(glob.glob(os.path.join(args.path, ext)))
    
    if not jpg_files:
        print(f"No JPG or JPEG files found in '{args.path}'.")
        return
    
    print(f"Found {len(jpg_files)} JPG/JPEG files.")
    
    processed = 0
    skipped = 0
    
    for jpg_file in jpg_files:
        date_tuple = extract_date_from_filename(jpg_file)
        
        if date_tuple:
            year, month, day = date_tuple
            print(f"Extracted date from {jpg_file}: {year}-{month}-{day}")
            
            success, message = update_exif_date(jpg_file, date_tuple)
            if success:
                print(f"Updated {jpg_file} with date {year}-{month}-{day}")
                processed += 1
            else:
                print(f"Failed to update {jpg_file}: {message}")
                skipped += 1
        else:
            print(f"No date found in filename: {jpg_file} - skipping")
            skipped += 1
    
    print(f"\nSummary: Processed {processed} files, skipped {skipped} files.")

if __name__ == "__main__":
    main()