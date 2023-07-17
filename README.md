# Duplicate File and Directory Finder (dup.py)

`dup.py` is a universal command-line tool that helps you find and manage duplicate files and directories. It scans the specified directories, identifies duplicate files and directories based on various comparison criteria, and offers options for deleting or replacing these duplicates. Unlike most similar tools, `dup.py` can find duplicates as efficiently as possible, and not just files, but directories as well.

## Installation
For convenience, this is just one python file that you can download yourself and freely place anywhere.
A script that automatically downloads the `dup.py` file from the repository on GitHub, makes it executable, and places it in the `bin` directory in the home directory:

```bash
mkdir -p "${HOME}/bin" && curl -L "https://raw.githubusercontent.com/NikolayBorisov/dup.py/main/dup.py" -o "${HOME}/bin/dup.py" && chmod +x "${HOME}/bin/dup.py"
```

You can simply copy and paste this command into your console and press Enter. 

Please note that this assumes that the `${HOME}/bin` directory is already in the PATH variable. If not, then you need to add it to PATH, which can be done as follows:

```bash
echo 'export PATH="${HOME}/bin:${PATH}"' >> "${HOME}/.bashrc" && source "${HOME}/.bashrc"
```

Or for zsh users:

```bash
echo 'export PATH="${HOME}/bin:${PATH}"' >> "${HOME}/.zshrc" && source "${HOME}/.zshrc"
```

This needs to be done only once. After that, you will be able to use `dup.py`.

## Usage

```plaintext
dup.py [directories [directories ...]] [options]
```
## Arguments

##### Main

- `directories`: A list of directories to scan for duplicate files and directories. If the directories are not specified, the current working directory is used.
- `-c CHECK`, `--check CHECK`: Specify a set of parameters or presets for comparison. Can be a combination of [epic,full,data,fast,tree,name,dirname,filename,date,size,bytes,firstbytes,lastbytes,count,dircount,filecount,hash]. You can specify multiple values, separated by commas. For example, `--check size,name`
- `-i IGNORE`, `--ignore IGNORE`: Specify a set of parameters or presets to ignore when comparing. Can be a combination of [epic,full,data,fast,tree,name,dirname,filename,date,size,bytes,firstbytes,lastbytes,count,dircount,filecount,hash]. You can specify multiple values, separated by commas. For example, `--ignore date`

##### Operating modes
- `-f`, `--files-only`: Search only for duplicate files and skip directories.
- `-d`, `--dirs-only`: Search only for duplicate directories.

##### Processing filters
Pre-filtering for processing.
- `--include-empty`,
  `--include-empty-dirs`,
  `--include-empty-files`: Process empty directories and/or files.
- `--exclude PATTERNS`,
  `--exclude-dirs DIR_PATTERNS`,
  `--exclude-files FILE_PATTERNS`: Exclude directories and files from comparison that match the given patterns. You can use patterns like `*.bak` or `/dir/**`

#### Final processing
Result filter. These filters are responsible for the final filtering, do not affect the duplicate search process, but affect which files and directories actions will be applied to.

- `-b`, `--brief`: Display brief statistics and perform no further actions.
- `--no-dirs`: Do not display and apply actions to directories in the end
- `--no-files`: Do not display and apply actions to files in the end
- `--dups-count DUPS_COUNT`,
  `--dups-dirs-count DUPS_DIRS_COUNT`,
  `--dups-files-count DUPS_FILES_COUNT`: Minimum number of directory and/or file duplicates in a group
- `--min-size MINSIZE`,
  `--max-size MAXSIZE`,
  `--min-dir-size MIN_DIR_SIZE`,
  `--max-dir-size MAX_DIR_SIZE`,
  `--min-file-size MIN_FILE_SIZE`,
  `--max-file-size MAX_FILE_SIZE`: These arguments set minimum and maximum sizes for files and directories in the final sample. Sizes should be specified as a string with a number and a unit of measurement. For example, `--min-size 10KB` or `--max-dir-size 2GiB`. This filter does not exclude files and directories from comparison, it only filters the final result

##### Actions

- `-S`, `--symlink`: Replace duplicate files and directories with symbolic links.
- `-H`, `--hardlink`: Replace duplicate files and directories with hard links.
- `-D`, `--delete`: Delete duplicates of files and directories.

##### Additional

- `--relative-paths`: Display relative paths of directories and files in the output. Convenient for visual control when absolute paths are too long.

##### Advanced Parameters

It is not recommended to apply these parameters unless you know exactly what you are doing.

- `--follow-links`: Allows following symbolic links when traversing a directory. This may lead to endless execution and errors.
- `--no-combine`: Process all duplicate files and directories without compacting.
- `--no-combine-dirs`: Process all duplicate directories without compacting.
- `--no-combine-files`: Process all files without hiding them in duplicate directories.
- `--bench`: Perform a benchmark to measure execution time.
- `--chunk CHUNK`: Block size for checking the file's `firstbytes` and `lastbytes` in bytes (default: 65536 bytes).
- `--no-cache`: By default, all heavy computations `bytes` and `hash` are cached, so they can be retrieved instantly on subsequent runs of the script. The `--no-cache` option disables this behavior and instructs the script not to use the cache.
- `--reset-cache`: This option clears the existing cache and creates a new one. This is useful if you want to force the script to perform the heavy computations `bytes` and `hash` again, for example, after data changes and you want the cache to reflect the current state of data.

Always remember that using `--no-cache` or `--reset-cache` can significantly increase the script's execution time as it has to compute `bytes` and `hash` from scratch. However, these options may be useful in situations where you want to ensure the script is working with the most up-to-date data.

## Comparison Presets:

1. `epic`: An exhaustive check for duplicates. It performs a comparison of the `date`, `name`, and `data` of the file (which includes `size`, `bytes`, `count`, and `hash`).

2. `full`: A full check for duplicates. Compares `name` and `data` (which includes `size`, `bytes`, `count`, and `hash`).

3. `data`: The default standard check for duplicates. Compares `size`, `bytes`, `count`, and `hash` of files and directories.

4. `fast`: A fast check for duplicates. Compares `size` and `tree` (which includes `name` and `count`) of files.

5. `tree`: A file hierarchy-based check for duplicates. Compares `name` and `count`.

When you use these presets, note that some parameters such as `name`, `data`, `bytes`, and `count` have additional attached parameters (e.g., `name` includes `dirname` and `filename`, `bytes` includes `firstbytes` and `lastbytes`, and `count` includes `dircount` and `filecount`).

You can also use the `--ignore` argument to selectively exclude these parameters from the check.

##### Here are some examples of using `-c` (`--check`) and `-i` (`--ignore`) together:

1. **Exclude some properties from a preset**: Suppose you want to use the `data` preset, but ignore the `size` property. You can use the `--ignore` flag for this:

    ```bash
    dup.py /path/to/directory -c data -i hash
    ```
    This will check for duplicates based on `bytes`, `count`, and `size`, but not `hash`.

2. **Add additional properties to a preset**: Suppose you want to use the `fast` preset, but also include `hash` in the comparison. You can use the `--check` flag to add `hash`:

    ```bash
    dup.py /path/to/directory -c fast,hash
    ```
    This will check for duplicates based on `size`, `tree`, and `hash`.

3. **Using multiple presets and excluding some properties**: If you want to combine multiple presets but ignore certain properties, you can do so like this:

    ```bash
    dup.py /path/to/directory -c full,fast -i size,count
    ```
    This will use both the `full` and `fast` presets but ignore the `size` and `count` properties. It will check for duplicates based on `name`, `bytes`, and `hash` (`full` minus `size` and `count`) and `tree` (`fast` minus `count`).

Remember that the `-c` and `-i` flags can accept a comma-separated list of properties or presets to include or exclude respectively.

## Notes

Use this tool with caution, especially when using the `--delete`, `--symlink`, or `--hardlink` flags as it permanently deletes files. Always review the list of duplicate files before performing any deletion actions. Make sure you have a backup of all important data. Use the `-f` or `-d` options to limit the search to files or directories respectively. Experiment with different flag combinations to tailor it to your specific use case.