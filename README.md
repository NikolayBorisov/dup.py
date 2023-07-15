# Duplicate Files and Directories Finder (dup.py)

`dup.py` is a versatile command-line tool that helps you find and manage duplicate files and directories. It scans the specified directories, identifies duplicate files and directories based on various comparison criteria, and provides options to delete or replace these duplicates.

## Usage

```plaintext
dup.py [directories [directories ...]]
       [--check CHECK] [--ignore IGNORE]
       [--symlink] [--hardlink] [--delete]
       [--bench] [--chunk CHUNK] [--no-cache] [--reset-cache]
       [--stat] [--files-only] [--dirs-only] [--no-combine] [--no-combine-dirs] [--no-combine-files]
       [--min-size MINSIZE] [--min-dir-size MIN_DIR_SIZE] [--min-file-size MIN_FILE_SIZE] [--process-empty]
       [--max-size MAXSIZE] [--max-dir-size MAX_DIR_SIZE] [--max-file-size MAX_FILE_SIZE]
       [--exclude PATTERNS] [--exclude-dirs DIR_PATTERNS] [--exclude-files FILE_PATTERNS]
       [--follow-links] [--relative-paths]
```

## Arguments

- `directories`: List of directories to scan for duplicate files and directories. If no directories are specified, the current working directory is used.

- `-c`, `--check CHECK`: Specify a set of parameters or presets for comparison. Can be a combination of [epic,full,data,fast,tree,name,dirname,filename,date,size,bytes,firstbytes,lastbytes,count,dircount,filecount,hash]. You can specify multiple values separated by commas. E.g., `--check size,name`
- `-i`, `--ignore IGNORE`: Specify a set of parameters or presets to ignore during comparison. Can be a combination of [epic,full,data,fast,tree,name,dirname,filename,date,size,bytes,firstbytes,lastbytes,count,dircount,filecount,hash]. You can specify multiple values separated by commas. E.g., `--ignore date`
- `-f`, `--files-only`: Search only for duplicate files and skip directories.
- `-d`, `--dirs-only`: Search only for duplicate directories.
- `--bench`: Perform benchmark for measuring execution time.
- `--chunk CHUNK`: Size of the chunk to check in bytes (default: 65536 bytes).
- `--no-cache`: By default, all heavy computations for 'bytes' and 'hash' are cached so that they can be retrieved instantly on subsequent runs of the script. The `--no-cache` option disables this behavior and instructs the script to not use the cache.
- `--reset-cache`: This option clears the existing cache and creates a new one. This is useful if you want to force the script to perform the heavy computations for 'bytes' and 'hash' again, for example, after the data has been changed and you want the cache to reflect the current state of the data.
- `--stat`: Display a brief statistics and do not perform any further action.
- `--no-combine`: Process all duplicate files and directories without compacting.
- `--no-combine-dirs`: Process all duplicate directories without compacting.
- `--no-combine-files`: Process all files without hiding them in duplicate directories.
- `--min-size MINSIZE`,
`--max-size MAXSIZE`,
`--min-dir-size MIN_DIR_SIZE`,
`--max-dir-size MAX_DIR_SIZE`,
`--min-file-size MIN_FILE_SIZE`,
`--max-file-size MAX_FILE_SIZE`: These arguments set minimum and maximum sizes for files and directories. Sizes should be specified as a string with a number followed by a unit. E.g., `--min-size 10KB` or `--max-dir-size 2GB`
- `--process-empty`: Process empty directories and files.
- `--follow-links`: Allows following symbolic links during directory traversal.
- `--relative-paths`: Display relative paths of directories and files.
- `--exclude PATTERNS`,
`--exclude-dirs DIR_PATTERNS`,
`--exclude-files FILE_PATTERNS`: Exclude directories and files that match the given patterns. Wildcards like `*.bak` or `/dir/**` can be used.
- `-S`, `--symlink`: Replace duplicate files and directories with symbolic links.
- `-H`, `--hardlink`: Replace duplicate files and directories with hard links.
- `-D`, `--delete`: Delete duplicate files and directories.


Always remember that using `--no-cache` or `--reset-cache` can significantly increase the execution time of the script as it has to compute 'bytes' and 'hash' from scratch. However, these options can be useful in situations where you want to ensure the script is working with the most recent data.

## Examples of Usage

1. Find duplicates in the current directory:

    ```
    dup.py
    ```

2. Find duplicates in a specific directory:

    ```
    dup.py /path/to/directory
    ```

3. Find duplicates in multiple directories:

    ```
    dup.py /path/to/directory1 /path/to/directory2
    ```

4. Find duplicates in a specific directory and exclude certain file types:

    ```
    dup.py /path/to/directory --exclude *.bak *.tmp
    ```

5. Find duplicates and replace them with symbolic links:

    ```
    dup.py /path/to/directory --symlink
    ```

6. Find duplicates based on file size and name:

    ```
    dup.py /path/to/directory --check size,name
    ```

7. Ignore duplicates based on file hash:

    ```
    dup.py /path/to/directory --ignore hash
    ```


## Presets for Comparisons:

1. `epic`: An exhaustive check for duplicates. It considers the file 'date', 'name', and 'data' (which further includes 'size', 'bytes', 'count', and 'hash') for comparison.

2. `full`: A comprehensive check for duplicates. It considers 'name' and 'data' (which includes 'size', 'bytes', 'count', and 'hash') for comparison.

3. `data`: A standard **default** check for duplicates. It compares 'size', 'bytes', 'count', and 'hash' of the files and directories.

4. `fast`: A quicker check for duplicates. It compares the 'size' and the 'tree' (which includes 'name' and 'count') of the files.

5. `tree`: A check for duplicates based on the file hierarchy. It considers 'name' and 'count' for comparison.

When using these presets, note that certain parameters like 'name', 'data', 'bytes', and 'count' have further parameters attached to them (e.g., 'name' includes 'dirname' and 'filename', 'bytes' includes 'firstbytes' and 'lastbytes', and 'count' includes 'dircount' and 'filecount'). 

You can also use the `--ignore` argument to selectively remove these parameters from the check.

##### Here are some examples of combined usage of `-c` (`--check`) and `-i` (`--ignore`):

1. **Excluding some properties from a preset**: Suppose you want to use the `data` preset but ignore the 'size' property. You can use the `--ignore` flag to achieve this:

    ```
    dup.py /path/to/directory -c data -i size
    ```
    This will check for duplicates based on 'bytes', 'count', and 'hash', but not 'size'.

2. **Including additional properties to a preset**: Suppose you want to use the `fast` preset but also include 'hash' in the comparison. You can use the `--check` flag to add 'hash':

    ```
    dup.py /path/to/directory -c fast,hash
    ```
    This will check for duplicates based on 'size', 'tree', and 'hash'.

3. **Using multiple presets and excluding some properties**: If you want to combine multiple presets but ignore some properties, you can do so as follows:

    ```
    dup.py /path/to/directory -c full,fast -i size,count
    ```
    This will use both the 'full' and 'fast' presets but ignore the 'size' and 'count' properties. It will check for duplicates based on 'name', 'bytes', and 'hash' ('full' minus 'size' and 'count'), and 'tree' ('fast' minus 'count').

Remember that the `-c` and `-i` flags can accept a comma-separated list of properties or presets to include or exclude, respectively.

## Notes

Use this tool with caution, especially when using the `--delete`, `--symlink` or `--hardlink` flag, as it permanently deletes files. Always review the list of duplicate files before proceeding with any deletion actions. Ensure you have a backup of all essential data. Use the `-f` or `-d` options to restrict the search to files or directories, respectively. Experiment with different combinations of flags to suit your specific use case.

## License

MIT stand for Ukraine License (Modified MIT License)

Copyright (c) 2022 Nikolai Borisov

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The user conditions are:

1. You do not support, justify, or recognize any military actions against Ukraine and the recognition of territories occupied by Russia, including Crimea and Donbass.
2. You do not directly or indirectly support the ideas or ideology of Russian or any other form of fascism.

In case of violation of these conditions, your license to use the Software is immediately revoked.

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
