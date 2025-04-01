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
    # Get just the basename of the file (no directory)
    basename = os.path.basename(filename)
    
    # First, try to find a full date (YYYY-MM-DD) at the end of the filename
    full_date_match = re.search(r'-(\d{4})-(\d{2})-(\d{2})(?=\.[^.]+$)', basename)
    if full_date_match:
        year, month, day = full_date_match.groups()
        return (year, month, day)
    
    # Next, try to find a year-month (YYYY-MM) at the end of the filename
    year_month_match = re.search(r'-(\d{4})-(\d{2})(?=\.[^.]+$)', basename)
    if year_month_match and not full_date_match:  # Avoid matching if we already found a full date
        year, month = year_month_match.groups()
        return (year, month, "01")  # First day of the month
    
    # Finally, try to find just a year (YYYY) at the end of the filename
    year_match = re.search(r'-(\d{4})(?=\.[^.]+$)', basename)
    if year_match and not year_month_match:  # Avoid matching if we already found a year-month
        year = year_match.group(1)
        return (year, "01", "01")  # January 1st
    
    # No date pattern found
    return None

def update_exif_date(file_path, date_tuple):
    """
    Update EXIF date information using exiftool
    date_tuple is (year, month, day)
    """
    year, month, day = date_tuple
    
    # Format date string (YYYY:MM:DD 12:00:00)
    date_string = f"{year}:{month}:{day} 12:00:00"
    
    # Update all relevant date tags
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
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Update EXIF date information based on filenames.')
    parser.add_argument('path', nargs='?', default='.', help='Path to scan for JPG files (default: current directory)')
    args = parser.parse_args()
    
    # Validate path exists
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.")
        sys.exit(1)
    
    # Get all JPG files in specified directory
    search_path = os.path.join(args.path, "*.jpg")
    jpg_files = glob.glob(search_path)
    
    if not jpg_files:
        print(f"No JPG files found in '{args.path}'.")
        return
    
    print(f"Found {len(jpg_files)} JPG files.")
    
    processed = 0
    skipped = 0
    
    for jpg_file in jpg_files:
        # Extract date from filename
        date_tuple = extract_date_from_filename(jpg_file)
        
        if date_tuple:
            year, month, day = date_tuple
            print(f"Extracted date from {jpg_file}: {year}-{month}-{day}")
            
            # Update EXIF data
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