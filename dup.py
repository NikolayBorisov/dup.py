#!/usr/bin/env python3
import os
import sys
import argparse
import hashlib
from collections import defaultdict

PART_OFFSET = 100
PART_SIZE = 50

def remove(file):
    print(f"{file['path']}", end=" ")
    removed_files.append(file)
    if not dry_run and delete_duplicates:
        os.remove(file["path"])
        print(f"(removed)")
    else:
        print(f"(dry run)")

def create_symlink(original_file, duplicate_file):
    print(f"Creating symbolic link for {duplicate_file['path']} to {original_file['path']}")
    if not dry_run:
        os.symlink(original_file['path'], duplicate_file['path'])

def create_hardlink(original_file, duplicate_file):
    print(f"Creating hard link for {duplicate_file['path']} to {original_file['path']}")
    if not dry_run:
        os.link(original_file['path'], duplicate_file['path'])

def get_part(file, offset=0, size=0):
    with open(file["path"], "rb") as f:
        if offset >= 0:
            f.seek(offset)
        else:
            f.seek(offset, 2)
        data = f.read(size)

    return data

def get_hash(file):
    with open(file["path"], "rb") as f:
        data = f.read()

    return hashlib.md5(data).hexdigest()

def get_human_readable_size(size):
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    unit = 0
    while size >= 1024:
        size /= 1024
        unit += 1
    return f"{size:.2f} {units[unit]}"

def get_files(folder, min_size=None, max_size=None, ignore_empty=True):
    files = []
    for root, dirs, filenames in os.walk(folder):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                if ignore_empty and size == 0:
                    continue
                if min_size is not None and size < min_size:
                    continue
                if max_size is not None and size > max_size:
                    continue
                files.append({"path": filepath, "size": size})
            else:
                print(f"File {filepath} not found")
    return files

# Create the argument parser
parser = argparse.ArgumentParser()

# Add the command line arguments
parser.add_argument('folders', nargs='+', help='List of folders')
parser.add_argument('--minsize', type=int, help='Minimum file size')
parser.add_argument('--maxsize', type=int, help='Maximum file size')
parser.add_argument('--includeempty', action='store_true', help='Ignore empty files')
parser.add_argument('--dry', action='store_true', help='Perform a dry run without making any changes')
parser.add_argument('--skipown', action='store_true', help='Skip files from the first folder')
parser.add_argument('--makesymlinks', action='store_true', help='Replace duplicate files with symbolic links')
parser.add_argument('--makehardlinks', action='store_true', help='Replace duplicate files with hard links')
parser.add_argument('--deleteduplicates', action='store_true', help='Delete duplicate files')

# Parse the command line arguments
args = parser.parse_args()

# Extract the values from the arguments
folders = args.folders
min_size = args.minsize
max_size = args.maxsize
ignore_empty = args.ignoreempty
dry_run = args.dry
skip_own = args.skipown
make_symlinks = args.makesymlinks
make_hardlinks = args.makehardlinks
delete_duplicates = args.deleteduplicates

# Initialize data structures
dups = defaultdict(list)
files = []
removed_files = []

# Check if at least one folder is provided
if len(folders) == 0:
    print("Please provide at least one folder path.")
    sys.exit()

# Get files from each folder
first_folder_files = []
other_folders_files = []

for folder in folders:
    print(f"Scanning folder: {folder}")
    folder_files = get_files(folder, min_size, max_size, ignore_empty)
    print(f"Found {len(folder_files)} files in {folder}")

    if folder == folders[0]:
        first_folder_files = folder_files
    else:
        other_folders_files += folder_files

# Calculate total size
total_size = sum(file["size"] for file in first_folder_files + other_folders_files)
print(f"Now have {len(first_folder_files) + len(other_folders_files)} files in total. Total size is {get_human_readable_size(total_size)}.")

# Check if files from other folders have sizes present in the first folder
if len(other_folders_files) > 0:
    original_file_count = len(first_folder_files) + len(other_folders_files)

    # Remove files from other folders that have sizes not present in the first folder
    other_folders_files = [file for file in other_folders_files if file["size"] in {f["size"] for f in first_folder_files}]

    removed_files_count = original_file_count - (len(first_folder_files) + len(other_folders_files))
    print(f"Removed {removed_files_count} files due to unique size not present in the first folder. {len(first_folder_files) + len(other_folders_files)} files left.")

# Combine files from all folders
files = first_folder_files + other_folders_files

# Remove files with unique sizes
original_file_count = len(files)
size_to_files = defaultdict(list)
for file in files:
    size_to_files[file["size"]].append(file)
files = [file for file in files if len(size_to_files[file["size"]]) > 1]
removed_files_count = original_file_count - len(files)
print(f"Removed {removed_files_count} files due to unique sizes from list. {len(files)} files left.")

# Define the portions to check
portions = [
    {"name": "first", "offset": 0},
    {"name": "last", "offset": -PART_OFFSET},
    {"name": "middle", "offset": file['size'] // 2 - PART_SIZE // 2}
]

# Process files by portions
for portion in portions:
    original_file_count = len(files)
    print(f"Now eliminating candidates based on {portion['name']} bytes:")

    # Get the portion for each file
    for file in files:
        if file['size'] > PART_OFFSET:
            file[portion['name']] = get_part(file, portion['offset'], PART_SIZE)

    # Group files by portion
    hash_to_files = defaultdict(list)
    for file in files:
        if portion['name'] in file:  # Check for the presence of the portion key
            hash_to_files[file[portion['name']]].append(file)

    # Remove files with a unique portion
    files = [file for file in files if (portion['name'] in file and len(hash_to_files[file[portion['name']]]) > 1) or file['size'] <= PART_OFFSET]

    removed_files_count = original_file_count - len(files)
    print(f"Removed {removed_files_count} files from list. {len(files)} files left.")

# Process files by checksum
original_file_count = len(files)
print("Now eliminating candidates based on checksum:")

# Get the hash for each file
for file in files:
    file["hash"] = get_hash(file)

# Group files by hash
hash_to_files = defaultdict(list)
for file in files:
    hash_to_files[file["hash"]].append(file)

# Remove files with a unique hash
files = [file for file in files if len(hash_to_files[file["hash"]]) > 1]
removed_files_count = original_file_count - len(files)
print(f"Removed {removed_files_count} files from list. {len(files)} files left.")

# Process files with the same hash
for hash_value, group_files in hash_to_files.items():
    # Check if files are from both folders
    if any(file["path"].startswith(folders[0]) for file in group_files) and any(file["path"].startswith(folder) for folder in folders[1:] for file in group_files):
        print(f"\nProcessing {hash_value} {get_human_readable_size(group_files[0]['size'])}")
        print(f"Files from different folders found. Keep them:")
        other_folder_files = [file for file in group_files if not file["path"].startswith(folders[0])]
        for file in other_folder_files:
            print(f"{file['path']}")
        files_to_remove = [file for file in group_files if file["path"].startswith(folders[0])]
        print("Removing files from the first folder:")
        for file in files_to_remove:
            remove(file)
            if make_symlinks:
                create_symlink(other_folder_files[0], file)
            elif make_hardlinks:
                create_hardlink(other_folder_files[0], file)
        continue

    # Check if files are only from the first folder
    if not skip_own and all(file["path"].startswith(folders[0]) for file in group_files):
        print(f"\nProcessing {hash_value} {get_human_readable_size(group_files[0]['size'])}")
        print(f"Files only from the first folder found. Keeping the file with the shortest name:")
        shortest_filename = min(group_files, key=lambda x: len(os.path.basename(x["path"])))
        print(f"{shortest_filename['path']}")
        print("Removing files from the first folder:")
        for file in group_files:
            if file != shortest_filename:
                remove(file)
                if make_symlinks:
                    create_symlink(shortest_filename, file)
                elif make_hardlinks:
                    create_hardlink(shortest_filename, file)
        continue

total_removed_size = sum(file["size"] for file in removed_files)
print(f"\n\n{len(removed_files)} files were removed.")
print(f"Totally, {get_human_readable_size(total_removed_size)} were reduced.")
