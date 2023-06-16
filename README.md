# Dup.py - Duplicate File Finder and Manager

`dup.py` is a command-line tool that helps you find and manage duplicate files in multiple folders. It scans the specified folders, identifies duplicate files based on their sizes and contents, and provides options to remove or replace duplicate files.

## Usage

```plaintext
dup.py [-h] [--minsize MINSIZE] [--maxsize MAXSIZE] [--includeempty]
       [--dry] [--skipown] [--makesymlinks] [--makehardlinks]
       folders [folders ...]
```

## Arguments

- `folders`: List of folders to scan for duplicate files.

## Optional Arguments

- `--minsize MINSIZE`: Minimum file size (in bytes) to consider. Files smaller than this size will be ignored.
- `--maxsize MAXSIZE`: Maximum file size (in bytes) to consider. Files larger than this size will be ignored.
- `--includeempty`: Include empty files in the search. By default, empty files are ignored.
- `--dry`: Perform a dry run without making any changes. Files will be identified and listed, but no files will be removed or replaced.
- `--skipown`: Skip files from the first folder. Duplicate files found in the first folder will not be removed or replaced.
- `--makesymlinks`: Replace duplicate files with symbolic links. If specified, duplicate files will be replaced with symbolic links pointing to the original file.
- `--makehardlinks`: Replace duplicate files with hard links. If specified, duplicate files will be replaced with hard links to the original file.

## File Removal Options

By default, `dup.py` identifies duplicate files and provides information about them, but it does not remove any files. However, you can use the following options to remove duplicate files:

- `--dry`: Perform a dry run without making any changes. Duplicate files will be identified and listed, but no files will be removed or replaced.
- `--skipown`: Skip files from the first folder. Duplicate files found in the first folder will not be removed or replaced.

## File Replacement Options

By default, `dup.py` does not replace duplicate files with symbolic links or hard links. However, you can use the following options to replace duplicate files:

- `--makesymlinks`: Replace duplicate files with symbolic links. If specified, duplicate files will be replaced with symbolic links pointing to the original file.
- `--makehardlinks`: Replace duplicate files with hard links. If specified, duplicate files will be replaced with hard links to the original file.

## Examples

1. Scan multiple folders for duplicate files:
   ```plaintext
   dup.py /path/to/folder1 /path/to/folder2 /path/to/folder3
   ```

2. Specify a minimum file size and include empty files in the search:
   ```plaintext
   dup.py /path/to/folder --minsize 1024 --includeempty
   ```

3. Perform a dry run without removing any files:
   ```plaintext
   dup.py /path/to/folder --dry
   ```

4. Skip duplicates found in the first folder:
   ```plaintext
   dup.py /path/to/folder1 /path/to/folder2 --skipown
   ```

5. Replace duplicate files with symbolic links:
   ```plaintext
   dup.py /path/to/folder --makesymlinks
   ```

6. Replace duplicate files with hard links:
   ```plaintext
   dup.py /path/to/folder --makehardlinks
   ```

## Notes

- The `dup.py` script uses the MD5 hash algorithm to compare the contents of files and determine duplicates.
- Duplicate files are identified based on their sizes and

 contents. If two files have the same size and the same content, they are considered duplicates.
- When replacing duplicate files with symbolic links or hard links, the original file is preserved, and the duplicate files are replaced with links to the original file. This helps save disk space while maintaining the availability of the files.
- Be cautious when removing or replacing files. Make sure to review the list of duplicate files and verify that you have a backup of important files before proceeding with any removal or replacement actions.
- Use the `--dry` option to perform a dry run and preview the actions that `dup.py` would take without actually modifying any files.

Feel free to experiment with the `dup.py` script and adjust the options based on your needs.
