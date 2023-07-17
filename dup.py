#!/usr/bin/env python3

import argparse
import re
import datetime
import hashlib
import os
import fnmatch
import shutil
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


def remove_unique(root):
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


def get_duplicates(func):
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
                    remove_unique(root)
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
                remove_unique(paths[0])
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


def post_filter(rm_dirs, rm_files):
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


def filter_empty():
    """
    Remove all empty directories and/or files if the corresponding parameters
    are set to True.
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

    post_filter(rm_dirs, rm_files)


def filter_exclude():
    """
    Remove all directories and/or files that do not match the exclude patterns
    if the corresponding parameters are set to True.
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

    post_filter(rm_dirs, rm_files)


def filter_files_only():
    """
    If the files_only parameter is set to True, remove all files that do not
    satisfy the file size condition.
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


def dirs_join(dir_dups):
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
    dir_dups_joint = dir_dups.copy()

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
        del dir_dups_joint[keys]

    return dir_dups_joint


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


def print_dup_head(dups):
    """
    Prints the formatted date and size of a duplicate file.
    """
    # `format_date` and `format_size` are assumed to be predefined functions

    dup = dups[0]
    output = ""
    output += format_date(dup["date"]) + "  "
    output += format_size(dup["size"]) + "  "
    if dup.get("flen"):
        output += str(dup["dlen"]) + " directories  "
        output += str(dup["flen"]) + " files  "
    output += str(len(dups)) + " items"

    print(output)


def print_dup_path(dup, sub=False, save=False, is_dir=False):
    """
    Prints the path of a duplicate file with custom formatting.
    """
    res = "↳ " if sub else "  "  # prepend arrow if `sub` is True
    res += "✓ " if save else "⨯ "  # tick if `save` is True
    # add relative path if `rel` is True, else add absolute path
    res += (
        os.path.join(
            os.path.basename(dup["base"]), os.path.relpath(dup["path"], dup["base"])
        )
        if params.relative_paths
        else dup["path"]
    )
    res += "/" if is_dir else ""  # append slash if `is_dir` is True
    print(res)


def action(dup_save, dups_act):
    """
    Perform an action on duplicate files or directories based on user parameters.

    Parameters:
        dup_save (dict): Information about the file/directory to keep, in a dictionary format with
                         a "path" key referring to its file path.
        dups_act (list): A list of dictionaries. Each dictionary holds information about a duplicate
                         file/directory, including a "path" key for its file path.

    Returns:
        bool: True if an action is performed (delete, symlink, or hardlink), False otherwise.

    Raises:
        Exception: If the provided path is invalid.
    """

    if not (params.symlink or params.hardlink or params.delete):
        return False

    for dup in dups_act:
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


def get_all_duplicates():
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
            else "" + ">"
        )

    if check("firstbytes"):
        print("Now eliminating candidates based on first bytes...")

        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file, None, params.chunk)
            if file["size"] > params.chunk
            else get_file_hash(file)
        )
        cache.save()

    if check("lastbytes"):
        print("Now eliminating candidates based on last bytes...")
        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file, -params.chunk)
            if file["size"] > params.chunk * 2
            else None
        )
        cache.save()

    if check("hash"):
        print("Now eliminating candidates based on hash...")
        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file) if file["size"] > params.chunk else None
        )
        cache.save()

    return dir_dups, file_dups


def filter_dups_by_size(dups_groups, min_size, max_size):
    """
    Filter out duplicate groups based on the size constraints provided.

    Args:
        dups_groups (dict): The dictionary containing duplicate groups. The keys
            represent group identifiers and the values are lists of dictionaries
            containing the duplicate files' information.
        min_size (int or None): The minimum size of the files to be considered.
            If a file size is smaller than min_size, its group will be removed
            from dups_groups. If None, no minimum size filtering will be applied.
        max_size (int or None): The maximum size of the files to be considered.
            If a file size is larger than max_size, its group will be removed
            from dups_groups. If None, no maximum size filtering will be applied.

    Returns:
        list: A list of paths (strings) for files that were removed from dups_groups.

    Note:
        This function modifies the dups_groups dictionary in-place, removing any
        groups that do not satisfy the size constraints.
    """
    if not dups_groups or (min_size is None and max_size is None):
        return

    dups_to_remove = []
    paths_to_remove = []

    for keys, dups in dups_groups.items():
        dup = dups[0]
        if (min_size is not None and min_size > dup["size"]) or (
            max_size is not None and max_size < dup["size"]
        ):
            dups_to_remove.append(keys)
            for dup in dups:
                paths_to_remove.append(dup["path"])

    for keys in dups_to_remove:
        del dups_groups[keys]

    return paths_to_remove


def action_dir_dups(dups_groups):
    """
    Processes the duplicate directory groups.

    This function performs several operations on the provided groups of duplicate directories:
    1. If the global parameters 'files_only', 'stat' and 'no_combine_dirs' are set,
       it simply returns, performing no operations.
    2. It optionally compacts the directory groups based on the 'no_combine_dirs' parameter.
    3. It filters out groups of directories that do not fall within the specified size limits.
    4. Finally, for each remaining group of duplicates, it selects a 'save' directory,
       performs an action on it and prints the results.

    Args:
        dups_groups (dict): A dictionary mapping a unique identifier to each group of duplicate directories.
                            Each group is a list of dictionaries containing directory information.

    Side effects:
        This function directly modifies the provided 'dups_groups' dictionary, potentially removing some keys.
        It also prints out the processing results and may perform filesystem actions based on the global 'action' parameter.
    """

    if params.no_dirs or params.files_only or (params.brief and params.no_combine_dirs):
        return

    if not params.no_combine_dirs:
        print(f"Compacting {len(dups_groups)} groups of directories...")
        dups_groups = dirs_join(dups_groups)
        print(f"Now have {len(dups_groups)} groups of duplicate directories")

    if not dups_groups or params.brief:
        return

    if params.min_dir_size is not None or params.max_dir_size is not None:
        dups_groups_len = len(dups_groups)
        removed_dirs = filter_dups_by_size(
            dups_groups, params.min_dir_size, params.max_dir_size
        )
        print(
            f"Removed {dups_groups_len - len(dups_groups)} groups of duplicate directories"
            + f" contains {len(removed_dirs)} directories due size"
        )
        print(f"Now have {len(dups_groups)} groups of duplicate directories")
        if not dups_groups:
            return

    print("\nDuplicate directories:\n")
    for _, dups in dups_groups.items():
        if params.dups_dirs_count and params.dups_dirs_count > len(dups):
            continue

        dup_save = dups[0]
        dups_act = []

        print_dup_head(dups)
        print_dup_path(dup_save, sub=False, save=True, is_dir=True)

        for dup in dups[1:]:
            dups_act.append(dup)
            print_dup_path(dup, sub=False, save=False, is_dir=True)

        action(dup_save, dups_act)


def action_file_dups(dups_groups):
    """
    Processes the duplicate file groups.

    This function performs several operations on the provided groups of duplicate files:
    1. If the global parameters 'dirs_only', 'stat' are set or no groups are provided,
       it simply returns, performing no operations.
    2. It filters out groups of files that do not fall within the specified size limits.
    3. Finally, for each remaining group of duplicates, it selects a 'save' file,
       performs an action on it and prints the results.

    Args:
        dups_groups (dict): A dictionary mapping a unique identifier to each group of duplicate files.
                            Each group is a list of dictionaries containing file information.

    Side effects:
        This function directly modifies the provided 'dups_groups' dictionary, potentially removing some keys.
        It also prints out the processing results and may perform filesystem actions based on the global 'action' parameter.
    """

    if params.no_files or params.dirs_only or not dups_groups or params.brief:
        return

    if params.min_file_size is not None or params.max_file_size is not None:
        dups_groups_len = len(dups_groups)
        removed_files = filter_dups_by_size(
            dups_groups, params.min_file_size, params.max_file_size
        )
        print(
            f"\nRemoved {dups_groups_len - len(dups_groups)} groups of duplicate files"
            + f" contains {len(removed_files)} files due size"
        )
        print(f"Now have {len(dups_groups)} groups of duplicate files")
        if not dups_groups:
            return

    print("\nDuplicate files:\n")
    for _, dups in dups_groups.items():
        if params.dups_files_count and params.dups_files_count > len(dups):
            continue

        in_dirs = []
        in_free = []

        if not params.files_only:
            for dup in dups:
                (in_dirs if dup["root"] in all_dirs else in_free).append(dup)
        else:
            in_free = dups

        if not (in_free or params.no_combine_files or params.files_only):
            continue

        dup_save = None
        dups_act = []

        if in_dirs:
            dup_save = in_dirs[0]
            print_dup_head(dups)
            print_dup_path(dup_save, sub=True, save=True)

            for dup in in_dirs[1:]:
                dups_act.append(dup)
                print_dup_path(dup, sub=True, save=False)

        if dup_save:
            for dup in in_free:
                dups_act.append(dup)
                print_dup_path(dup, sub=False, save=False)
        else:
            dup_save = in_free[0]
            print_dup_head(dups)
            print_dup_path(dup_save, sub=False, save=True)

            for dup in in_free[1:]:
                dups_act.append(dup)
                print_dup_path(dup, sub=False, save=False)

        action(dup_save, dups_act)


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


params = get_params()

bench = Bench(params.bench)
cache = Cache("dup.py.cache.pkl", not params.no_cache)
if not params.reset_cache:
    cache.load()

all_dirs, all_files = collect_all_data(params.directories, params.follow_links)
all_roots = get_roots(all_files)

filter_empty()
filter_files_only()
filter_exclude()

dir_dups_groups, file_dups_groups = get_all_duplicates()

action_dir_dups(dir_dups_groups)
action_file_dups(file_dups_groups)

cache.save()
