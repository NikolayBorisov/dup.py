#!/usr/bin/env python3

import argparse
import re
import datetime
import hashlib
import os
import fnmatch
import shutil
import sys
import tempfile
import pickle
from collections import defaultdict


class Bench:
    """
    A simple benchmarking class to measure the time taken by processes.
    The timer can be enabled or disabled by setting `enable` during initialization.
    """

    def __init__(self, enable=True):
        """
        Initializes the Bench object with an empty list of start times.
        """
        self.bench_times = []
        self.enabled = enable

    def start(self):
        """
        Records the current time and adds it to the stack of start times.
        This method does nothing if the Bench object is not enabled.
        """
        if self.enabled:
            self.bench_times.append(datetime.datetime.now())

    def stop(self):
        """
        Stops the timer and calculates the elapsed time since the last `start` call.
        If the timer is not enabled or there was no corresponding `start` call, this method does nothing.
        """
        if not self.enabled or not self.bench_times:
            return
        start_time = self.bench_times.pop()
        elapsed_time = datetime.datetime.now() - start_time

        hours, rem = divmod(elapsed_time.total_seconds(), 3600)
        minutes, seconds = divmod(rem, 60)

        if hours > 0:
            print(f"Elapsed time: {hours} hours {minutes} minutes")
        elif minutes > 0:
            print(f"Elapsed time: {minutes} minutes {seconds} seconds")
        else:
            print(f"Elapsed time: {round(seconds, 3)} seconds")


class Cache:
    """A class for caching data to a temporary file."""

    def __init__(self, file, enable=True):
        """
        Initialize a new Cache instance.

        Args:
            file (str): The filename for the cache file.
            enable (bool): Whether caching is enabled. Default is True.
        """
        self.enabled = enable
        self.data = {}
        if self.enabled:
            self.file = os.path.join(tempfile.gettempdir(), file)

    def load(self):
        """
        Load data from cache file to the cache dictionary.

        Returns:
            bool: True if cache file exists and data is successfully loaded, False otherwise.
        """
        if self.enabled and os.path.isfile(self.file):
            with open(self.file, "rb") as file:
                self.data = pickle.load(file)
            return True
        return False

    def get(self, key):
        """
        Get a value from the cache.

        Args:
            key (str): The key to retrieve the value for.

        Returns:
            value: The value for the key if key is in the cache, else None.
        """
        return self.data.get(key, None)

    def set(self, key, value):
        """
        Set a value in the cache.

        Args:
            key (str): The key for which to set the value.
            value: The value to set.
        """
        self.data[key] = value

    def save(self):
        """
        Save the cache dictionary to the cache file.

        Returns:
            bool: True if caching is enabled and data is successfully saved, False otherwise.
        """
        if self.enabled:
            with open(self.file, "wb") as file:
                pickle.dump(self.data, file)
            return True
        return False


def parse_size(orig_size_str):
    """
    Parses the size string and converts it to bytes.

    Parameters:
    orig_size_str (str): The size string to parse, such as "2.5GB" or "3.2MiB".

    Returns:
    int: The size in bytes, or raises ValueError if the size string is not recognized.

    Raises:
    ValueError: If the size string cannot be parsed.
    """
    size_str = orig_size_str.upper()
    size_units = {
        None: 1,
        "B": 1,
        "K": 10**3,
        "KB": 10**3,
        "M": 10**6,
        "MB": 10**6,
        "G": 10**9,
        "GB": 10**9,
        "T": 10**12,
        "TB": 10**12,
        "KI": 2**10,
        "KIB": 2**10,
        "MI": 2**20,
        "MIB": 2**20,
        "GI": 2**30,
        "GIB": 2**30,
        "TI": 2**40,
        "TIB": 2**40,
    }

    pattern = r"([0-9.]+)\s*([A-Z]*)?"
    match = re.match(pattern, size_str)

    if match:
        size = float(match.group(1))
        unit = match.group(2)
        if unit in size_units:
            return int(size * size_units[unit])

    raise ValueError(f"Invalid size format: {orig_size_str}")


def format_size(size):
    """
    Formats the given size in bytes to a human-readable format using binary prefixes.

    Parameters:
    size (int): The size in bytes to format.

    Returns:
    str: The size formatted as a string with binary prefixes (e.g., "3.14 KiB"),
         or raises ValueError if the size is negative.

    Raises:
    ValueError: If the size is negative.
    """
    if size < 0:
        raise ValueError("Size must be non-negative")

    power = 2**10
    units_index = 0
    size_format = ["B", "KiB", "MiB", "GiB", "TiB"]

    while size >= power:
        size /= power
        units_index += 1

    return f"{size:.2f} {size_format[units_index]}"


def format_date(timestamp):
    """
    Formats a Unix timestamp into a string representation of date and time.

    Parameters:
    timestamp (int or float): The Unix timestamp to format.

    Returns:
    str: The formatted date and time as a string in the format "YYYY-MM-DD HH:MM:SS".

    Raises:
    ValueError: If the timestamp is not a valid Unix timestamp.
    """

    try:
        return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except Exception as error:
        raise ValueError("Invalid timestamp") from error


def get_hash(data):
    """
    Compute the blake2b hash of the given data.

    Parameters:
    data (str or bytes): The data to hash.

    Returns:
    str: The hexadecimal representation of the hash.
    """
    if isinstance(data, str):
        data = data.encode()
    return hashlib.blake2b(data).hexdigest()


def get_file_hash(file_info, offset=None, size=None):
    """
    Calculates the BLAKE2 hash of a file.

    The function takes the file info and optional offset and size parameters.
    It first tries to retrieve the hash from the cache. If it doesn't exist in the cache,
    it calculates the hash and stores it in the cache for future use.

    Args:
        file_info (dict): A dictionary containing information about the file.
        offset (int, optional): The starting point from which to read the file. Default is None.
        size (int, optional): The number of bytes to read from the file. Default is None.

    Returns:
        str: The calculated hash of the file (or part of the file if offset and size are given).
    """

    # Extract the node value from the file info dictionary.
    node = file_info["node"]

    # Try to get the hash value from the cache first.
    file_hash = cache.get((node, offset, size))
    if file_hash:
        # If the hash value exists in the cache, return it without calculating.
        return file_hash

    # Initialize the hasher.
    hasher = hashlib.blake2b()

    # Open the file to calculate its hash.
    with open(file_info["path"], "rb") as file:
        # If an offset is provided, adjust the file position.
        if offset is not None:
            file.seek(offset, 0 if offset >= 0 else 2)

        # If a size is provided, read only the specified number of bytes from the file.
        if size is not None:
            bytes_read = 0
            for block in iter(lambda: file.read(min(size - bytes_read, 65536)), b""):
                hasher.update(block)
                bytes_read += len(block)
                if bytes_read >= size:
                    break
        else:
            # If no size is specified, read the whole file.
            for block in iter(lambda: file.read(65536), b""):
                hasher.update(block)

    # Calculate the final hash.
    file_hash = hasher.hexdigest()

    # Store the calculated hash in the cache for future use.
    cache.set((node, offset, size), file_hash)

    return file_hash  # Return the calculated hash.


def compact_keys(keys):
    """
    Compacts a large number of keys into a hashed representation.

    Args:
        keys (iterable): The input keys to be compacted if necessary.

    Returns:
        Either the original keys, if the length is less than or equal to 1000, or a hash of the keys if their count is more than 1000.
    """
    # If there are more than 1000 keys, create a hash representation of them.
    # `get_hash` is assumed to be a previously defined function.
    return get_hash(keys) if len(keys) > 1000 else keys


def collect_data(dir_path, followlinks):
    """
    Traverses the given directory path and collects information about files and directories.

    Args:
        dir_path (str): The path of the directory to traverse.
        followlinks (bool): Whether or not to follow symbolic links.

    Returns:
        dict, dict: Two dictionaries containing
        information about directories and files respectively.
    """
    # Start timing the operation for benchmarking
    bench.start()

    res_files = {}
    res_dirs = {}

    stat = os.stat(dir_path)

    # Initialize the result dictionaries with information about the root directory
    res_dirs[dir_path] = {
        "path": dir_path,
        "root": None,
        "name": os.path.basename(dir_path),
        "size": 0,
        "flen": 0,
        "dlen": 0,
        "keys": "",
        "base": dir_path,
        "date": int(stat.st_mtime),
        "node": str(stat.st_dev) + ":" + str(stat.st_ino),
    }

    # Use os.walk to traverse the directory tree
    for root, dirs, files in os.walk(dir_path, followlinks=followlinks):
        for name in dirs:
            path = os.path.join(root, name)
            if os.path.exists(path):
                stat = os.stat(path)
                res_dirs[path] = {
                    "path": path,
                    "root": root,
                    "name": name,
                    "size": 0,
                    "flen": 0,
                    "dlen": 0,
                    "keys": "",
                    "base": dir_path,
                    "date": int(stat.st_mtime),
                    "node": str(stat.st_dev) + ":" + str(stat.st_ino),
                }
            else:
                print(f"Directory {path} not found")
        for name in files:
            path = os.path.join(root, name)
            if os.path.exists(path):
                stat = os.stat(path)
                size = stat.st_size
                res_files[path] = {
                    "path": path,
                    "root": root,
                    "name": name,
                    "size": size,
                    "keys": "",
                    "base": dir_path,
                    "date": int(stat.st_mtime),
                    "node": str(stat.st_dev) + ":" + str(stat.st_ino),
                }
                res_dirs[root]["size"] += size
                res_dirs[root]["flen"] += 1
            else:
                print(f"File {path} not found")

    # Update parent directories with the aggregated sizes and counts of their children
    for _, dir_info in sorted(res_dirs.items(), reverse=True):
        root = dir_info["root"]
        if not root:
            continue
        res_dirs[root]["size"] += dir_info["size"]
        res_dirs[root]["dlen"] += 1

    # Stop timing the operation for benchmarking
    bench.stop()
    return res_dirs, res_files


def collect_all_data(dir_paths, followlinks):
    """
    Collects all file and directory data from given directory paths.

    Parameters:
    dir_paths (list): List of directory paths to collect data from.
    followlinks (bool): Whether to follow symbolic links to directories.

    Returns:
    tuple: A tuple containing two dictionaries - information about all directories and files.
    """

    # Initialize results containers
    res_dirs, res_files = {}, {}
    all_size = 0

    # Iterate over each directory path
    for dir_path in dir_paths:
        root = os.path.abspath(dir_path)

        print(f"Collecting data for the directory: {dir_path}")

        # Collect data for the current directory path
        new_dirs, new_files = collect_data(root, followlinks)

        # Update the results with the new data
        res_dirs.update(new_dirs)
        res_files.update(new_files)

        # Calculate and update total size
        new_size = new_dirs[root]["size"]
        all_size += new_size

        print(
            f"Collected {len(new_dirs)} directories and {len(new_files)} files"
            + f" with a total size of {format_size(new_size)}\n"
        )
        print(
            f"Now have {len(res_dirs)} directories and {len(res_files)} files in total"
        )
        print(f"Total size is {format_size(all_size)}\n")

    return res_dirs, res_files


def remove_unique(root, all_dirs, all_files, all_roots):
    """
    Recursively remove unique directories from the list of directories. The function modifies the
    global variables 'all_dirs', 'all_files', and 'all_roots' in-place.

    Args:
        root (str): The root directory from which to start the deletion process.
    """
    while True:
        if not root or not root in all_dirs:
            break

        if params.dirs_only:
            for path in all_roots[root]:
                if path in all_files:  # If the path is in the list of all files
                    del all_files[path]  # Delete the file

        next_root = all_dirs[root]["root"]  # Get the root of the current root directory
        del all_dirs[root]  # Delete the current root directory
        root = next_root  # Update the root directory for the next iteration


def get_duplicates(func, all_dirs, all_files, all_roots):
    """
    Retrieve directories and files that are duplicates using a function for comparison.

    This function scans through all directories and files, and finds duplicates based on the function provided.
    A dictionary is maintained to keep track of duplicates and the directories/files are updated accordingly.

    Args:
        func (function): A function that takes a file_info dictionary and returns a hashable value.

    Returns:
        tuple: Two dictionaries (dir_dups, file_dups) containing information about duplicate directories and files.
    """

    bench.start()

    # Initial count of directories and files
    dlen, flen = len(all_dirs), len(all_files)

    dir_keys_paths = defaultdict(list)
    file_keys_paths = defaultdict(list)

    dir_dups = defaultdict(list)
    file_dups = defaultdict(list)

    # If not only searching for file duplicates, prepare directory keys
    if not params.files_only:
        for path, dir_info in all_dirs.items():
            dir_info["keys"] = ":"
            if check("dirname"):
                dir_info["keys"] += dir_info["name"] + ":"
            if check("dircount"):
                dir_info["keys"] += str(dir_info["dlen"]) + ":"
            if check("filecount"):
                dir_info["keys"] += str(dir_info["flen"]) + ":"

    # Prepare file keys
    for path, file_info in all_files.items():
        key = func(file_info)
        file_info["keys"] = compact_keys(file_info["keys"] + str(key or ""))
        file_keys_paths[file_info["keys"]].append(path)

    # Handle unique files and update directory keys
    for keys, paths in file_keys_paths.items():
        if len(paths) == 1:
            path = paths[0]
            root = all_files.get(path, {}).get("root")
            if root:
                del all_files[path]
                if not params.files_only:
                    remove_unique(root, all_dirs, all_files, all_roots)
        elif not params.files_only:
            for path in paths:
                root = all_files.get(path, {}).get("root")
                if root and root in all_dirs:
                    all_dirs[root]["keys"] += ":" + keys

    # Handle directories
    if not params.files_only:
        for path, dir_info in sorted(all_dirs.items(), reverse=True):
            root = dir_info["root"]
            if root and root in all_dirs:
                keys = all_dirs[root]["keys"] + "/" + all_dirs[path]["keys"]
                all_dirs[root]["keys"] = compact_keys(keys)

        for path, dir_info in all_dirs.items():
            dir_keys_paths[dir_info["keys"]].append(path)

        for keys, paths in dir_keys_paths.items():
            if len(paths) == 1:
                remove_unique(paths[0], all_dirs, all_files, all_roots)
            else:
                for path in paths:
                    if path in all_dirs:
                        dir_dups[keys].append(all_dirs[path])

    # Prepare file duplicates
    for keys, paths in file_keys_paths.items():
        if len(paths) > 1:
            for path in paths:
                if path in all_files:
                    file_dups[keys].append(all_files[path])

    bench.stop()
    print(f"{dlen - len(all_dirs)} dirs and {flen - len(all_files)} files removed")
    print(f"{len(all_dirs)} dirs and {len(all_files)} files left\n")

    return dir_dups, file_dups


def get_all_duplicates(all_dirs, all_files, all_roots):
    """
    Find all duplicate directories and files based on various checks.

    This function finds duplicate directories and files based on different checks
    like 'filename', 'size', 'date', 'firstbytes', 'lastbytes', 'hash' which are
    defined in global `params`. The function prints the check which is currently
    being used to find duplicates.

    This function applies these checks in order. For every check, it removes directories
    and files that are not duplicates according to that check. It uses the `get_duplicates`
    and `get_file_hash` functions to perform these checks and get the duplicates.

    The function also saves the cache after each operation that modifies it using the
    `cache.save` method.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing two dictionaries.
        The first dictionary contains directory duplicates and the second one contains
        file duplicates. The key is a string which is a common characteristic based on
        which duplicates were found, and the value is a list of directories or files
        which are duplicates of each other.
    """

    if check("filename") or check("size") or check("date"):
        print(
            "Now eliminating candidates based on "
            + ", ".join(filter(None, map(check, ["filename", "size", "date"])))
            + "..."
        )

        dir_dups, file_dups = get_duplicates(
            lambda file: "<" + (str(file["name"]) + "/")
            if check("filename")
            else "" + (str(file["size"]) + "/")
            if check("size")
            else "" + (str(file["date"]) + "/")
            if check("date")
            else "" + ">",
            all_dirs,
            all_files,
            all_roots,
        )

    if check("firstbytes"):
        print("Now eliminating candidates based on first bytes...")

        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file, None, params.chunk)
            if file["size"] > params.chunk
            else get_file_hash(file),
            all_dirs,
            all_files,
            all_roots,
        )
        cache.save()

    if check("lastbytes"):
        print("Now eliminating candidates based on last bytes...")
        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file, -params.chunk)
            if file["size"] > params.chunk * 2
            else None,
            all_dirs,
            all_files,
            all_roots,
        )
        cache.save()

    if check("hash"):
        print("Now eliminating candidates based on hash...")
        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file) if file["size"] > params.chunk else None,
            all_dirs,
            all_files,
            all_roots,
        )
        cache.save()

    print(
        f"Now have {len(dir_dups)} groups of duplicate directories and {len(file_dups)} groups of duplicate files"
    )

    return dir_dups, file_dups


def post_filter(rm_dirs, rm_files, all_dirs, all_files, all_roots):
    """
    Remove directories and files that are in the 'rm_dirs' and 'rm_files' lists
    from the 'all_dirs' and 'all_files' dictionaries respectively.

    Args:
        rm_dirs (dict): The directories to be removed.
        rm_files (dict): The files to be removed.

    Returns:
        rm_dirs (dict): The directories removed.
        rm_files (dict): The files removed.
    """
    if not params.files_only:
        for dir_path in rm_dirs:
            del all_dirs[dir_path]
            if params.dirs_only:
                for file_path in all_roots[dir_path]:
                    rm_files[file_path] = True

    for file_path in rm_files:
        del all_files[file_path]

    print(f"{len(rm_dirs)} dirs and {len(rm_files)} files removed")
    print(f"{len(all_dirs)} dirs and {len(all_files)} files left\n")

    return rm_dirs, rm_files


def filter_empty(all_dirs, all_files, all_roots):
    """
    Filters out empty directories and/or files based on user preference.
    If the 'include_empty_dirs' or 'include_empty_files' parameters are False, the function
    goes through all directories and files and checks if they are empty.
    If a directory or a file is empty, it is added to a list to be removed.

    If the 'files_only' parameter is True, empty directories are not removed.
    """

    if params.include_empty_dirs and params.include_empty_files:
        return

    print("Now remove empty directories and/or files...")

    rm_dirs, rm_files = {}, {}

    if not params.files_only and not params.include_empty_dirs:
        for dir_path, dir_info in all_dirs.items():
            if dir_info["size"] < 1:
                rm_dirs[dir_path] = True

    if not params.include_empty_files:
        for file_path, file_info in all_files.items():
            if file_info["size"] < 1:
                rm_files[file_path] = True

    post_filter(rm_dirs, rm_files, all_dirs, all_files, all_roots)


def filter_exclude(all_dirs, all_files, all_roots):
    """
    Filters out directories and/or files that match the specified exclude patterns.
    The function first checks if there are any exclude patterns for directories or files.
    If there are, it goes through all directories and files and checks if they match any of the exclude patterns.
    If a directory or a file matches an exclude pattern, it is added to a list to be removed.

    If the 'files_only' parameter is True, directories are not checked against the exclude patterns.
    """

    if not params.exclude_dirs and not params.exclude_files:
        return

    print(
        "Now remove directories and/or files that do not match the exclude patterns..."
    )

    rm_dirs, rm_files = {}, {}

    if not params.files_only and params.exclude_dirs:
        for dir_path, _ in all_dirs.items():
            if any(
                fnmatch.fnmatch(dir_path, pattern) for pattern in params.exclude_dirs
            ):
                rm_dirs[dir_path] = True

    if params.exclude_files:
        for file_path, _ in all_files.items():
            if any(
                fnmatch.fnmatch(file_path, pattern) for pattern in params.exclude_files
            ):
                rm_files[file_path] = True

    post_filter(rm_dirs, rm_files, all_dirs, all_files, all_roots)


def filter_files_only(all_files):
    """
    Filters out files that don't fit within the specified minimum and maximum file size if the files_only parameter is True.
    Prints the number of files that are removed and the number of files that are left after the removal.

    This function will do nothing if both the minimum and maximum file sizes are not specified.
    """

    if not params.files_only or (
        params.min_file_size is None and params.max_file_size is None
    ):
        return

    print("Now we are deleting files that exceed the allowed size...")

    rm_files = {}

    for file_path, file_info in all_files.items():
        if (
            params.min_file_size is not None
            and params.min_file_size > file_info["size"]
        ) or (
            params.max_file_size is not None
            and params.max_file_size < file_info["size"]
        ):
            rm_files[file_path] = True

    for file_path in rm_files:
        del all_files[file_path]

    print(f"{len(rm_files)} files removed")
    print(f"{len(all_files)} files left\n")


def filter_subdirs(dir_dups, all_dirs):
    """
    Join duplicate directories based on their root keys.

    This function attempts to join duplicate directories if they share the same root.
    If multiple directories have different roots, they are not joined.

    Parameters:
        dir_dups (dict): A dictionary of directories to check for potential joins.
                         Keys are a combination of directory attributes, and values
                         are lists of dictionaries representing directories.

    Returns:
        dict: A copy of the original 'dir_dups' dictionary where joinable directories
              have been joined, and non-joinable directories removed.
    """

    to_remove = {}

    for keys, dups in dir_dups.items():
        roots = {}
        for dup in dups:
            root_keys = all_dirs.get(dup["root"], {}).get("keys")
            if not root_keys:
                roots = {}
                continue
            roots[root_keys] = True

        if len(roots) == 1:
            to_remove[keys] = True
        else:
            to_remove.update(roots)

    for keys in to_remove:
        del dir_dups[keys]

    return to_remove


def get_roots(files):
    """
    Organize file paths based on their root directories.

    This function creates a dictionary where keys are root directories
    and values are lists of files in these directories.

    Parameters:
        files (dict): A dictionary where keys are file paths and values
                      are dictionaries with file metadata, including the 'root' key.

    Returns:
        dict: A dictionary where keys are root directories and values are lists of files.
    """
    roots = defaultdict(list)
    for path, file in files.items():
        roots[file["root"]].append(path)

    return roots


def check(param):
    """
    Check if a parameter is in the list of parameters to be checked.

    This function is used to decide whether certain operations should be performed
    based on the existence of a parameter in a list.

    Parameters:
        param (str): The parameter to be checked.

    Returns:
        str: The input parameter if it exists in the 'params.check' list, an empty string otherwise.
    """
    return param if param in params.check else ""


def print_groups_summary(rm_len, left_len):
    """
    Prints a summary message about the removal of duplicate groups.

    Args:
        rm_len (int): The number of duplicate groups removed.
        left_len (int): The number of duplicate groups left after removal.
    """

    print(f"{rm_len} groups removed, {left_len} left")


def filter_dups_groups(dups_groups, func):
    """
    Filters duplicate groups (either file or directory) based on a given function.

    Args:
        dups_groups (dict): A dictionary of duplicate groups. Each key is a tuple representing the group's attributes,
                            and the corresponding value is a list of dictionaries, each representing an item
                            (file or directory) in the group.
        func (function): A function that takes a list of items (either files or directories) as input and returns a
                         boolean. The function should return True for the groups that need to be removed.

    Returns:
        to_remove (list): A list of keys of the groups that have been removed.

    The function iterates over the groups in `dups_groups`. For each group, it applies `func` to the group's items.
    If `func` returns True, the function adds the group's keys to `to_remove` and removes the group from `dups_groups`.
    """

    to_remove = []

    for keys, dups in dups_groups.items():
        if func(dups):
            to_remove.append(keys)

    for keys in to_remove:
        del dups_groups[keys]

    return to_remove


def filter_dir_dups_groups(dups_groups, all_dirs):
    """
    Filters duplicate directory groups based on specified criteria such as minimum and maximum size,
    count of duplicates, and whether to combine directories or not.

    Args:
        dups_groups (list): A list of duplicate directory groups. Each group is a list of dictionaries,
                            where each dictionary represents a directory with its attributes.

    Returns:
        res_dups_groups (list): A filtered list of duplicate directory groups. Each group is a list of dictionaries,
                                where each dictionary represents a directory with its attributes.

    The function filters out groups of duplicate directories that don't meet specified criteria. If `params.dups_dirs_count`
    is set, it removes groups with a count of duplicates less than the specified value. If `params.min_dir_size`
    or `params.max_dir_size` are set, it removes groups with directories smaller or larger than the specified sizes,
    respectively.

    If `params.no_combine_dirs` is False, it also removes subdirectories from the groups of duplicates.

    The function does not currently implement the `into` marker (which indicates the directory to keep) as in
    the `filter_file_dups_groups` function.

    The function prints the number of groups removed and the number of remaining groups at several stages of the filtering process.
    """

    if not dups_groups:
        return

    if params.dups_dirs_count:
        print("Filtering groups by dups count in group...")
        removed = filter_dups_groups(
            dups_groups, lambda dups: params.dups_dirs_count > len(dups)
        )
        print_groups_summary(len(removed), len(dups_groups))

    if params.min_dir_size is not None or params.max_dir_size is not None:
        print("Filtering groups by min/max size...")
        removed = filter_dups_groups(
            dups_groups,
            lambda dups: (
                params.min_dir_size is not None
                and params.min_dir_size > dups[0]["size"]
            )
            or (
                params.max_dir_size is not None
                and params.max_dir_size < dups[0]["size"]
            ),
        )
        print_groups_summary(len(removed), len(dups_groups))

    if not params.no_combine_dirs:
        print("Compacting groups of directories...")
        removed = filter_subdirs(dups_groups, all_dirs)
        print_groups_summary(len(removed), len(dups_groups))

    if not dups_groups:
        return

    res_dups_groups = []

    # TODO: Implement `into` marker like in file_dups
    for _, dups in dups_groups.items():
        res_dups_groups.append(dups)

    return res_dups_groups


def filter_file_dups_groups(dups_groups, all_dirs):
    """
    Filters duplicate file groups based on specified criteria such as minimum and maximum size,
    count of duplicates, and whether to combine files or not.

    Args:
        dups_groups (list): A list of duplicate file groups. Each group is a list of dictionaries,
                            where each dictionary represents a file with its attributes.

    Returns:
        res_dups_groups (list): A filtered list of duplicate file groups. Each group is a list of dictionaries,
                                where each dictionary represents a file with its attributes.

    The function filters out groups of duplicate files that don't meet specified criteria. If `params.dups_files_count`
    is set, it removes groups with a count of duplicates less than the specified value. If `params.min_file_size`
    or `params.max_file_size` are set, it removes groups with files smaller or larger than the specified sizes,
    respectively.

    The function also separates duplicates into two lists: `in_dirs` (duplicates that are in directories)
    and `in_free` (duplicates that are not in directories). It then processes these lists separately.

    If `params.files_only` is True, it adds all duplicates to `in_free`. If not, it adds duplicates to `in_dirs`
    if their root is in `all_dirs` (a global variable representing all directories), and to `in_free` otherwise.

    If `in_free` is empty and either `params.no_combine_files` is True or `params.files_only` is True,
    it removes the group of duplicates from `dups_groups`.

    If `in_dirs` is not empty, it marks the first duplicate in the list as "into" (indicating it's the duplicate
    to keep) and adds the rest of the duplicates in `in_dirs` to `dups_act` (a list representing duplicates to act upon),
    also marked as "into". If `in_dirs` is empty, it does the same for `in_free`.

    Finally, the function appends the list `[dup_save] + dups_act` (where `dup_save` is the duplicate to keep)
    to `res_dups_groups` (the list of results), and returns this list.

    The function prints the number of groups removed and the number of remaining groups at several stages of the filtering process.
    """

    if not dups_groups:
        return

    if params.dups_files_count:
        print("Filtering file groups by dups count in group...")
        removed = filter_dups_groups(
            dups_groups, lambda dups: params.dups_files_count > len(dups)
        )
        print_groups_summary(len(removed), len(dups_groups))

    if params.min_file_size is not None or params.max_file_size is not None:
        print("Filtering file groups by min/max size...")
        removed = filter_dups_groups(
            dups_groups,
            lambda dups: (
                params.min_file_size is not None
                and params.min_file_size > dups[0]["size"]
            )
            or (
                params.max_file_size is not None
                and params.max_file_size < dups[0]["size"]
            ),
        )
        print_groups_summary(len(removed), len(dups_groups))

    if not dups_groups:
        return

    res_dups_groups = []
    to_remove = []

    for keys, dups in dups_groups.items():
        in_dirs = []
        in_free = []

        if not params.files_only:
            for dup in dups:
                (in_dirs if dup["root"] in all_dirs else in_free).append(dup)
        else:
            in_free = dups

        if not (in_free or params.no_combine_files or params.files_only):
            to_remove.append(keys)
            continue

        dup_save = None
        dups_act = []

        if in_dirs:
            dup_save = in_dirs[0]
            dup_save["into"] = True

            for dup in in_dirs[1:]:
                dup["into"] = True
                dups_act.append(dup)

        if dup_save:
            for dup in in_free:
                dup["into"] = False
                dups_act.append(dup)
        else:
            dup_save = in_free[0]
            dup_save["into"] = False

            for dup in in_free[1:]:
                dup["into"] = False
                dups_act.append(dup)

        res_dups_groups.append([dup_save] + dups_act)

    if to_remove:
        print("Processed files that are already present in duplicate directories")
        print_groups_summary(len(to_remove), len(res_dups_groups))

    return res_dups_groups


def output_dups_groups(dups_groups, rel=False, is_dir=False):
    """
    Outputs formatted information about duplicate groups to the console. The function provides details
    about each group and each duplicate item in the group. It handles duplicate directories and files differently.

    Args:
        dups_groups (list): A list of duplicate groups. Each group is a list of dictionaries,
                            where each dictionary represents a file or directory with its attributes.
        rel (bool, optional): If True, the function outputs the relative paths of duplicate items.
                              If False, it outputs the absolute paths. Defaults to False.
        is_dir (bool, optional): If True, the function outputs details about duplicate directories.
                                 If False, it outputs details about duplicate files. Defaults to False.
    """

    if not dups_groups:
        return

    if is_dir:
        print("\nDuplicate directories:\n")
    else:
        print("\nDuplicate files:\n")

    for num, dups in enumerate(dups_groups):
        dup = dups[0]
        res = str(num + 1) + "  " if num is not None else ""
        res += format_date(dup["date"]) + "  "
        res += format_size(dup["size"]) + "  "
        if is_dir:
            print(is_dir)
            res += str(dup["dlen"]) + " directories  "
            res += str(dup["flen"]) + " files  "
        res += str(len(dups)) + " items"
        print(res)

        for i, dup in enumerate(dups):
            res = "↳ " if dup.get("into", False) else "  "
            res += "✓ " if (i == 0) else "⨯ "
            res += (
                os.path.join(
                    os.path.basename(dup["base"]),
                    os.path.relpath(dup["path"], dup["base"]),
                )
                if rel
                else dup["path"]
            )
            res += "/" if is_dir else ""
            print(res)


def action_dups_groups(dups_groups):
    """
    Performs actions on duplicate groups based on the command line parameters.
    If the script is set to delete duplicates, it removes duplicate files and directories.
    It also creates symbolic or hard links for duplicates, if specified in the command line parameters.

    Args:
        dups_groups (list): A list of duplicate groups. Each group is a list of dictionaries,
                            where each dictionary represents a file or directory with its attributes.

    Returns:
        bool: True if the operation was successful, False otherwise.
              Returns False if the dups_groups is empty or no action is specified in the command line parameters.
    """

    if not dups_groups or not (params.symlink or params.hardlink or params.delete):
        return False

    for dups in dups_groups:
        dup_save = dups[0]
        for dup in dups[1:]:
            if os.path.isfile(dup["path"]):
                os.remove(dup["path"])
            elif os.path.isdir(dup["path"]):
                shutil.rmtree(dup["path"])
            else:
                print("Invalid path:", dup["path"])

            if params.symlink:
                os.symlink(dup_save["path"], dup["path"])
            elif params.hardlink:
                os.link(dup_save["path"], dup["path"])

    return True


def get_params():
    """
    Parse and return command-line arguments.

    This function uses the argparse module to handle command-line arguments.
    The parsed arguments include various options for specifying the directories to scan, how to
    handle the duplicate files and directories found, and what criteria to use for comparing files
    and directories.

    Returns:
        Namespace: A namespace object populated with arguments from the command line.
    """

    parser = argparse.ArgumentParser(
        description="Find duplicate directories and files."
    )
    parser.add_argument(
        "directories",
        metavar="DIR",
        nargs="*",
        default=[os.getcwd()],
        help="Path to the root directory",
    )

    parser.add_argument(
        "--bench",
        action="store_true",
        help="Perform benchmark for measuring execution time",
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=65536,
        help="Size of the chunk to check in bytes (default: 65536 bytes)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching of directory and file information",
    )
    parser.add_argument(
        "--reset-cache",
        action="store_true",
        help="Do not use cached directory and file information",
    )

    parser.add_argument(
        "--brief",
        "-b",
        action="store_true",
        dest="brief",
        help="Display a brief statistics and do not perform any further action",
    )

    parser.add_argument(
        "--no-combine",
        action="store_true",
        help="Process all duplicate files and directories without compacting",
    )
    parser.add_argument(
        "--no-combine-dirs",
        action="store_true",
        help="Process all duplicate directories without compacting",
    )
    parser.add_argument(
        "--no-combine-files",
        action="store_true",
        help="Process all files without hiding them in duplicate directories",
    )

    parser.add_argument(
        "--dirs-only",
        "-d",
        action="store_true",
        dest="dirs_only",
        help="Search only for duplicate directories",
    )
    parser.add_argument(
        "--files-only",
        "-f",
        action="store_true",
        dest="files_only",
        help="Search only for duplicate files and skip directories",
    )

    parser.add_argument(
        "--no-dirs",
        action="store_true",
        help="Skip directories for output and actions",
    )
    parser.add_argument(
        "--no-files",
        action="store_true",
        help="Skip files for output and actions",
    )

    parser.add_argument(
        "--min-size",
        type=str,
        help="Minimum size for files and directories",
    )
    parser.add_argument(
        "--max-size",
        type=str,
        help="Maximum size for files and directories",
    )
    parser.add_argument(
        "--min-dir-size",
        type=str,
        help="Minimum size for directories",
    )
    parser.add_argument(
        "--max-dir-size",
        type=str,
        help="Maximum size for directories",
    )
    parser.add_argument(
        "--min-file-size",
        type=str,
        help="Minimum size for files",
    )
    parser.add_argument(
        "--max-file-size",
        type=str,
        help="Maximum size for files",
    )

    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Process empty directories and files",
    )
    parser.add_argument(
        "--include-empty-dirs",
        action="store_true",
        help="Process empty directories",
    )
    parser.add_argument(
        "--include-empty-files",
        action="store_true",
        help="Process empty files",
    )

    parser.add_argument(
        "--dups-count",
        type=int,
        default=None,
        help="Колличество дублирующих файлов или директорий в группе",
    )
    parser.add_argument(
        "--dups-dirs-count",
        type=int,
        default=None,
        help="Колличество дублирующих директорий в группе",
    )
    parser.add_argument(
        "--dups-files-count",
        type=int,
        default=None,
        help="Колличество дублирующих файлов в группе",
    )

    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Exclude directories and files that match the given patterns",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="+",
        help="Exclude directories that match the given patterns",
    )
    parser.add_argument(
        "--exclude-files",
        nargs="+",
        help="Exclude files that match the given patterns",
    )

    parser.add_argument(
        "--symlink",
        "-S",
        action="store_true",
        dest="symlink",
        help="Replace duplicate files and directories with symbolic links",
    )
    parser.add_argument(
        "--hardlink",
        "-H",
        action="store_true",
        dest="hardlink",
        help="Replace duplicate files and directories with hard links",
    )
    parser.add_argument(
        "--delete",
        "-D",
        action="store_true",
        dest="delete",
        help="Delete duplicate files and directories",
    )
    # [epic,full,data,fast,tree,
    #  name,dirname,filename,date,size,bytes,firstbytes,lastbytes,count,dircount,filecount,hash]
    parser.add_argument(
        "--check",
        "-c",
        type=str,
        dest="check",
        help="Specify a set of parameters or presets for comparison",
    )
    parser.add_argument(
        "--ignore",
        "-i",
        type=str,
        dest="ignore",
        help="Specify a set of parameters or presets to ignore during comparison",
    )

    parser.add_argument(
        "--follow-links",
        action="store_true",
        help="Allows following symbolic links during directory traversal",
    )

    parser.add_argument(
        "--relative-paths",
        "--rel",
        action="store_true",
        dest="relative_paths",
        help="Display relative paths of directories and files",
    )

    args = parser.parse_args()

    if args.check:
        args.check = set(args.check.lower().split(","))
    else:
        args.check = set(["data"])

    if "epic" in args.check:
        args.check.add("date")
        args.check.add("full")
    if "full" in args.check:
        args.check.add("name")
        args.check.add("data")
    if "data" in args.check:
        args.check.add("size")
        args.check.add("bytes")
        args.check.add("count")
        args.check.add("hash")

    if "fast" in args.check:
        args.check.add("size")
        args.check.add("tree")
    if "tree" in args.check:
        args.check.add("name")
        args.check.add("count")

    if "name" in args.check:
        args.check.add("dirname")
        args.check.add("filename")
    if "bytes" in args.check:
        args.check.add("firstbytes")
        args.check.add("lastbytes")
    if "count" in args.check:
        args.check.add("dircount")
        args.check.add("filecount")

    if args.ignore:
        args.ignore = set(args.ignore.lower().split(","))

        if "name" in args.ignore:
            args.check.discard("dirname")
            args.check.discard("filename")
        if "bytes" in args.ignore:
            args.check.discard("firstbytes")
            args.check.discard("lastbytes")
        if "count" in args.ignore:
            args.check.discard("dircount")
            args.check.discard("filecount")

        args.check = args.check - args.ignore

    if args.max_size:
        args.max_file_size = args.max_size
        args.max_dir_size = args.max_size

    if args.min_size:
        args.min_file_size = args.min_size
        args.min_dir_size = args.min_size

    args.min_file_size = parse_size(args.min_file_size) if args.min_file_size else None
    args.max_file_size = parse_size(args.max_file_size) if args.max_file_size else None
    args.min_dir_size = parse_size(args.min_dir_size) if args.min_dir_size else None
    args.max_dir_size = parse_size(args.max_dir_size) if args.max_dir_size else None

    if args.include_empty:
        args.include_empty_dirs = True
        args.include_empty_files = True

    if args.dups_count:
        args.dups_dirs_count = args.dups_count
        args.dups_files_count = args.dups_count

    if args.no_combine:
        args.no_combine_files = True
        args.no_combine_dirs = True

    if args.exclude:
        args.exclude_dirs = args.exclude_dirs or []
        args.exclude_dirs.extend(args.exclude)

        args.exclude_files = args.exclude_files or []
        args.exclude_files.extend(args.exclude)

    return args


def main():
    """
    The main function for the script. It orchestrates the flow of operations, starting from loading the cache,
    collecting all data, applying various filters, getting all duplicates, filtering duplicate groups,
    and finally outputting and taking action on the duplicates. It also handles conditionals like whether
    directories/files should be excluded and if it should be in brief mode or not.
    """

    if not params.reset_cache:
        cache.load()

    all_dirs, all_files = collect_all_data(params.directories, params.follow_links)
    all_roots = get_roots(all_files)

    filter_empty(all_dirs, all_files, all_roots)
    filter_files_only(all_files)
    filter_exclude(all_dirs, all_files, all_roots)

    dir_dups_groups, file_dups_groups = get_all_duplicates(
        all_dirs, all_files, all_roots
    )

    if not params.files_only:
        res_dir_dups_groups = filter_dir_dups_groups(dir_dups_groups, all_dirs)

    if not params.dirs_only:
        res_file_dups_groups = filter_file_dups_groups(file_dups_groups, all_dirs)

    if params.brief:
        sys.exit()

    if not params.no_dirs and not params.files_only:
        output_dups_groups(res_dir_dups_groups, rel=params.relative_paths, is_dir=True)
        action_dups_groups(res_dir_dups_groups)

    if not params.no_files and not params.dirs_only:
        output_dups_groups(
            res_file_dups_groups, rel=params.relative_paths, is_dir=False
        )
        action_dups_groups(res_file_dups_groups)


state = {}
params = get_params()
bench = Bench(params.bench)
cache = Cache("dup.py.cache.pkl", not params.no_cache)

main()
