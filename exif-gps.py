#!/usr/bin/env python3
import os
import subprocess
import argparse
import sys
import re

def validate_coordinates(lat, lon):
    """
    Validate that latitude and longitude are within valid ranges.
    Latitude: -90 to 90
    Longitude: -180 to 180
    """
    if lat is not None and (lat < -90 or lat > 90):
        return False, "Latitude must be between -90 and 90 degrees"
    
    if lon is not None and (lon < -180 or lon > 180):
        return False, "Longitude must be between -180 and 180 degrees"
    
    return True, "Valid coordinates"

def extract_gps_from_image(source_image):
    """
    Extract GPS data from a source image using exiftool.
    Returns a dict with latitude, longitude, and their reference values.
    """
    if not os.path.exists(source_image):
        print(f"Error: Source image '{source_image}' does not exist.")
        return None
    
    # Run exiftool to extract GPS coordinates
    try:
        command = [
            "exiftool",
            "-GPSLatitude",
            "-GPSLongitude",
            "-GPSLatitudeRef",
            "-GPSLongitudeRef",
            "-j",  # Output in JSON format for easier parsing
            "-n",  # Output numeric values
            source_image
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Try to parse the JSON output
        import json
        data = json.loads(result.stdout)
        
        if not data:
            print(f"No data returned from exiftool for '{source_image}'")
            return None
        
        # Extract GPS data
        gps_data = {}
        
        # Check if GPS data exists in the image
        if "GPSLatitude" in data[0] and "GPSLongitude" in data[0]:
            lat = data[0]["GPSLatitude"]
            lon = data[0]["GPSLongitude"]
            
            # Get reference values
            lat_ref = data[0].get("GPSLatitudeRef", "N")
            lon_ref = data[0].get("GPSLongitudeRef", "E")
            
            # Store both the raw values and the reference indicators
            gps_data["latitude"] = lat
            gps_data["longitude"] = lon
            gps_data["latitude_ref"] = lat_ref
            gps_data["longitude_ref"] = lon_ref
            
            # Also calculate the signed values for display purposes
            signed_lat = -lat if lat_ref == "S" else lat
            signed_lon = -lon if lon_ref == "W" else lon
            gps_data["signed_latitude"] = signed_lat
            gps_data["signed_longitude"] = signed_lon
            
            return gps_data
        else:
            print(f"No GPS data found in '{source_image}'")
            return None
        
    except subprocess.CalledProcessError as e:
        print(f"Error extracting GPS data: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"Error parsing exiftool output: {result.stdout}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def update_gps_data(image_path, latitude, longitude, lat_ref=None, lon_ref=None):
    """
    Update GPS data in an image using exiftool.
    Can handle either:
    1. Signed values (negative for S/W) when lat_ref and lon_ref are None
    2. Raw values with explicit reference indicators when lat_ref and lon_ref are provided
    """
    if not os.path.exists(image_path):
        print(f"Error: Image '{image_path}' does not exist.")
        return False
    
    # If reference indicators not provided, derive them from the signed values
    if lat_ref is None or lon_ref is None:
        lat_ref = "N" if latitude >= 0 else "S"
        lon_ref = "E" if longitude >= 0 else "W"
        abs_lat = abs(latitude)
        abs_lon = abs(longitude)
    else:
        # Use the raw values with the provided reference indicators
        abs_lat = latitude
        abs_lon = longitude
    
    try:
        command = [
            "exiftool",
            f"-GPSLatitude={abs_lat}",
            f"-GPSLatitudeRef={lat_ref}",
            f"-GPSLongitude={abs_lon}",
            f"-GPSLongitudeRef={lon_ref}",
            "-overwrite_original",
            image_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"GPS data updated for '{image_path}'")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error updating GPS data: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Update EXIF GPS data in an image.')
    
    # Create a mutually exclusive group for --lat/--lon vs --from
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--lat', type=float, help='Latitude value (-90 to 90)')
    group.add_argument('--from', dest='source_image', help='Source image to copy GPS data from')
    
    # Longitude argument (only required if --lat is used)
    parser.add_argument('--lon', type=float, help='Longitude value (-180 to 180)')
    
    # Target image (required)
    parser.add_argument('image', help='Image file to update with GPS data')
    
    args = parser.parse_args()
    
    # Validate command-line arguments
    if args.lat is not None and args.lon is None:
        parser.error("--lat requires --lon to be specified as well")
    
    # Validate the target image exists
    if not os.path.exists(args.image):
        print(f"Error: Image '{args.image}' does not exist.")
        sys.exit(1)
    
    # Case 1: Using specific lat/lon values
    if args.lat is not None and args.lon is not None:
        # Validate coordinates
        valid, message = validate_coordinates(args.lat, args.lon)
        if not valid:
            print(f"Error: {message}")
            sys.exit(1)
        
        print(f"Setting GPS coordinates for '{args.image}':")
        print(f"  Latitude: {args.lat}")
        print(f"  Longitude: {args.lon}")
        
        # Update GPS data
        if update_gps_data(args.image, args.lat, args.lon):
            print("GPS data updated successfully.")
        else:
            print("Failed to update GPS data.")
            sys.exit(1)
    
    # Case 2: Copy GPS data from another image
    elif args.source_image:
        print(f"Copying GPS data from '{args.source_image}' to '{args.image}'")
        
        # Extract GPS data from source image
        gps_data = extract_gps_from_image(args.source_image)
        
        if gps_data:
            print(f"GPS data found in source image:")
            print(f"  Latitude: {gps_data['latitude']} {gps_data['latitude_ref']}")
            print(f"  Longitude: {gps_data['longitude']} {gps_data['longitude_ref']}")
            print(f"  (Decimal: {gps_data['signed_latitude']}, {gps_data['signed_longitude']})")
            
            # Update target image with the extracted GPS data, preserving reference indicators
            if update_gps_data(args.image, 
                              gps_data['latitude'], 
                              gps_data['longitude'],
                              gps_data['latitude_ref'],
                              gps_data['longitude_ref']):
                print("GPS data copied successfully.")
            else:
                print("Failed to copy GPS data.")
                sys.exit(1)
        else:
            print("No GPS data found in the source image or error reading data.")
            sys.exit(1)

if __name__ == "__main__":
    main()