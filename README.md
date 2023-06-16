Вот обновленная документация для скрипта:

```markdown
# Duplicate File Finder

`dup.py` is a Python script for finding and managing duplicate files in a given set of folders.

## Usage

```
dup.py [options] folders...
```

## Options

- `folders`: List of folders to search for duplicate files.

- `--minsize`: Minimum file size in bytes. Only files with sizes greater than or equal to this value will be considered. (default: None)

- `--maxsize`: Maximum file size in bytes. Only files with sizes less than or equal to this value will be considered. (default: None)

- `--includeempty`: Include empty files in the search. By default, empty files are ignored. (default: False)

- `--dry`: Perform a dry run without making any changes. The script will print the files that would be removed without actually removing them. (default: False)

- `--skipown`: Skip files from the first folder that are considered duplicates. Only duplicate files from other folders will be removed. (default: False)

- `--makesymlinks`: Replace duplicate files with symbolic links. Instead of removing the duplicate files, symbolic links are created pointing to the original files. (default: False)

- `--makehardlinks`: Replace duplicate files with hard links. Similar to `--makesymlinks`, duplicate files are replaced with hard links instead of being removed. (default: False)

- `--deleteduplicates`: Delete duplicate files. When enabled, duplicate files will be deleted based on the specified criteria. (default: False)

## Examples

1. Find duplicate files in the specified folders:
```
dup.py /path/to/folder1 /path/to/folder2
```

2. Find duplicate files in the specified folders, excluding empty files:
```
dup.py --includeempty /path/to/folder1 /path/to/folder2
```

3. Find and remove duplicate files in the specified folders:
```
dup.py --deleteduplicates /path/to/folder1 /path/to/folder2
```

4. Find and remove duplicate files, excluding files from the first folder:
```
dup.py --deleteduplicates --skipown /path/to/folder1 /path/to/folder2
```

5. Find and replace duplicate files with symbolic links:
```
dup.py --deleteduplicates --makesymlinks /path/to/folder1 /path/to/folder2
```

6. Find and replace duplicate files with hard links:
```
dup.py --deleteduplicates --makehardlinks /path/to/folder1 /path/to/folder2
```

**Note:** Please exercise caution when using the `--deleteduplicates` option, as it permanently removes files from the specified folders. It is recommended to perform a dry run first using the `--dry` option to preview the actions that would be taken before actually applying them.

## Script

Here's the updated script with the added functionality:

```python
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

def

 create_hardlink(original_file, duplicate_file):
    print(f"Creating hard link for {duplicate_file['path']} to {original_file['path']}")
    if not dry_run:
        os.link(original_file['path'], duplicate_file['path'])

# Rest of the script...
```

Make sure to replace the existing script with this updated version to include the `--deleteduplicates` option.

**Note:** This script performs potentially destructive actions, such as deleting files or creating links. Use it with caution and ensure that you have proper backups before running it.
```
```

