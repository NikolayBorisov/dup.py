# Dup.py - Duplicate File Finder and Manager

`dup.py` is a command-line utility designed to help you find and manage duplicate files in various directories. This script scans through the designated directories, identifies duplicate files based on size and content, and offers options to either delete or replace the duplicate files.

## Usage

```plaintext
dup.py [-h] [--minsize MINSIZE] [--maxsize MAXSIZE] [--includeempty]
       [--dryrun] [--skipfirst] [--makesymlinks] [--makehardlinks]
       directories [directories ...]
```

## Parameters

- `directories`: Directories to scan for duplicate files.

## Optional Parameters

- `--minsize MINSIZE`: Minimum file size (in bytes) to consider. Files smaller than this size will be ignored.
- `--maxsize MAXSIZE`: Maximum file size (in bytes) to consider. Files larger than this size will be ignored.
- `--includeempty`: Include empty files in the search. By default, empty files are ignored.
- `--dryrun`: Perform a dry run without making any changes. Files will be identified and listed, but no actions will be taken.
- `--skipfirst`: Ignore files from the first directory. Duplicate files found in the first directory will not be deleted or replaced.
- `--makesymlinks`: Replace duplicate files with symbolic links to the original file.
- `--makehardlinks`: Replace duplicate files with hard links to the original file.

## File Deletion Options

By default, `dup.py` identifies duplicate files and provides information about them, but does not delete any files. However, you can use the following options to delete duplicate files:

- `--dryrun`: Perform a dry run without making any changes. Duplicate files will be identified and listed, but no actions will be taken.
- `--skipfirst`: Ignore files from the first directory. Duplicate files found in the first directory will not be deleted or replaced.

## File Replacement Options

By default, `dup.py` does not replace duplicate files with symbolic links or hard links. However, you can use the following options to replace duplicate files:

- `--makesymlinks`: Replace duplicate files with symbolic links to the original file.
- `--makehardlinks`: Replace duplicate files with hard links to the original file.

## Examples

1. Scan multiple directories for duplicate files:
   ```plaintext
   dup.py /path/to/directory1 /path/to/directory2 /path/to/directory3
   ```

2. Specify a minimum file size and include empty files in the search:
   ```plaintext
   dup.py /path/to/directory --minsize 1024 --includeempty
   ```

3. Perform a dry run without making any changes:
   ```plaintext
   dup.py /path/to/directory --dryrun
   ```

4. Ignore duplicates found in the first directory:
   ```plaintext
   dup.py /path/to/directory1 /path/to/directory2 --skipfirst
   ```

5. Replace duplicate files with symbolic links:
   ```plaintext
   dup.py /path/to/directory --makesymlinks
   ```

6. Replace duplicate files with hard links:
   ```plaintext
   dup.py /path/to/directory --makehardlinks
   ```

## Notes

- `dup.py` uses the MD5 hash algorithm to compare file contents and identify duplicates.
- Duplicate files are identified based on their size and content. If two files are of the same size and have the same content, they are considered duplicates.
- When replacing duplicate files with symbolic or hard links, the original file is kept while the duplicates are replaced with links to the original. This helps to

 conserve disk space while maintaining file accessibility.
- Be cautious when deleting or replacing files. Be sure to review the list of duplicate files and verify that you have backups of crucial files before proceeding with any removal or replacement operations.
- Use the `--dryrun` option to perform a dry run and preview the actions `dup.py` would take without actually modifying any files.

Feel free to experiment with the `dup.py` script and adjust the parameters according to your needs.
