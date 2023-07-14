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


def bench_start():
    if not params.bench:
        return
    bench_times.append(datetime.datetime.now())


def bench_stop():
    if not params.bench or not bench_times:
        return
    start_time = bench_times.pop()
    end_time = datetime.datetime.now()
    elapsed_time = end_time - start_time

    if elapsed_time < datetime.timedelta(minutes=1):
        elapsed_seconds = round(elapsed_time.total_seconds(), 3)
        print(f"Elapsed time: {elapsed_seconds} seconds")
    elif elapsed_time < datetime.timedelta(hours=1):
        elapsed_minutes = elapsed_time.total_seconds() // 60
        elapsed_seconds = elapsed_time.total_seconds() % 60
        print(f"Elapsed time: {elapsed_minutes} minutes {elapsed_seconds} seconds")
    else:
        elapsed_hours = elapsed_time.total_seconds() // 3600
        elapsed_minutes = (elapsed_time.total_seconds() % 3600) // 60
        print(f"Elapsed time: {elapsed_hours} hours {elapsed_minutes} minutes")


def save_obj_to_temp_file(pkl, obj):
    temp_dir = tempfile.gettempdir()
    temp_pkl = os.path.join(temp_dir, pkl)
    with open(temp_pkl, "wb") as file:
        pickle.dump(obj, file)
    return temp_pkl


def load_obj_from_file(pkl):
    temp_dir = tempfile.gettempdir()
    temp_pkl = os.path.join(temp_dir, pkl)
    if os.path.isfile(temp_pkl):
        with open(temp_pkl, "rb") as file:
            obj = pickle.load(file)
        return obj
    else:
        return None


def parse_size(orig_size_str):
    """
    Parses the size string and converts it to bytes.
    """
    size_str = orig_size_str.upper()
    size_units = {
        None: 1,
        "K": 10**3,
        "M": 10**6,
        "G": 10**9,
        "T": 10**12,
        "P": 10**15,
        "E": 10**18,
        "KI": 2**10,
        "MI": 2**20,
        "GI": 2**30,
        "TI": 2**40,
        "PI": 2**50,
        "EI": 2**60,
        "KIB": 2**10,
        "MIB": 2**20,
        "GIB": 2**30,
        "TIB": 2**40,
        "PIB": 2**50,
        "EIB": 2**60,
        "B": 1,
        "KB": 10**3,
        "MB": 10**6,
        "GB": 10**9,
        "TB": 10**12,
        "PB": 10**15,
        "EB": 10**18,
    }

    pattern = r"([0-9.]+)\s*([A-Z]+)?"
    match = re.match(pattern, size_str)

    if match:
        size = float(match.group(1))
        unit = match.group(2)
        if unit in size_units:
            return int(size * size_units[unit])

    print(f"Invalid size format: {orig_size_str}")
    return


def format_size(size):
    """
    Formats the given size in bytes to a human-readable format.
    """
    power = 2**10
    num = 0
    size_format = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

    while size >= power:
        size /= power
        num += 1

    return f"{size:.2f} {size_format[num]}"


def format_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def get_hash(data):
    if isinstance(data, str):
        data = data.encode()
    return hashlib.blake2b(data).hexdigest()


def get_file_hash(file_info, offset=None, size=None):
    path = file_info["path"]
    node = file_info["node"]

    if not params.no_cache and not params.reset_cache:
        file_hash = hash_cache.get((node, offset, size))
        if file_hash:
            return file_hash

    hasher = hashlib.blake2b()
    with open(path, "rb") as file:
        if offset is not None:
            file.seek(offset, 0 if offset >= 0 else 2)
        if size is not None:
            bytes_read = 0
            for block in iter(lambda: file.read(min(size - bytes_read, 65536)), b""):
                hasher.update(block)
                bytes_read += len(block)
                if bytes_read >= size:
                    break
        else:
            for block in iter(lambda: file.read(65536), b""):
                hasher.update(block)

    file_hash = hasher.hexdigest()
    if not params.no_cache:
        hash_cache[(node, offset, size)] = file_hash
    return file_hash


def relpath(dup):
    if params.relative_paths:
        return os.path.join(
            os.path.basename(dup["base"]),
            os.path.relpath(dup["path"], dup["base"]),
        )

    return dup["path"]


def compact_keys(keys):
    return get_hash(keys) if len(keys) > 1000 else keys


def collect_all_data(dir_paths):
    res_dirs, res_files = {}, {}
    all_size = 0
    for dir_path in dir_paths:
        root = os.path.abspath(dir_path)
        print(f"Collecting data for the directory: {dir_path}")
        new_dirs, new_files = collect_data(root)

        res_dirs.update(new_dirs)
        res_files.update(new_files)

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


def collect_data(dir_path):
    bench_start()

    res_files = {}
    res_dirs = {}

    stat = os.stat(dir_path)
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
        "node": str(stat.st_dev) + ':' + str(stat.st_ino),
    }
    
    for root, dirs, files in os.walk(dir_path, followlinks=params.follow_links):
        for name in dirs:
            path = os.path.join(root, name)
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
                "node": str(stat.st_dev) + ':' + str(stat.st_ino),
            }
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
                    "node": str(stat.st_dev) + ':' + str(stat.st_ino),
                }
                res_dirs[root]["size"] += size
                res_dirs[root]["flen"] += 1
            else:
                print(f"File {path} not found")

    for _, dir_info in sorted(res_dirs.items(), reverse=True):
        root = dir_info["root"]
        if not root:
            continue
        res_dirs[root]["size"] += dir_info["size"]
        res_dirs[root]["dlen"] += 1

    bench_stop()
    return res_dirs, res_files


def get_duplicates(func):
    bench_start()

    dlen, flen = len(all_dirs), len(all_files)

    dir_keys_paths = defaultdict(list)
    file_keys_paths = defaultdict(list)

    dir_dups = defaultdict(list)
    file_dups = defaultdict(list)

    if not params.files_only:
        for path, dir_info in all_dirs.items():
            dir_info["keys"] = ":"
            if check("dirname"):
                dir_info["keys"] += dir_info["name"] + ":"
            if check("dircount"):
                dir_info["keys"] += str(dir_info["dlen"]) + ":"
            if check("filecount"):
                dir_info["keys"] += str(dir_info["flen"]) + ":"

    for path, file_info in all_files.items():
        key = func(file_info)

        file_info["keys"] = compact_keys(file_info["keys"] + str(key or ""))
        file_keys_paths[file_info["keys"]].append(path)

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

    for keys, paths in file_keys_paths.items():
        if len(paths) > 1:
            for path in paths:
                if path in all_files:
                    file_dups[keys].append(all_files[path])

    bench_stop()
    print(f"{dlen - len(all_dirs)} dirs and {flen - len(all_files)} files removed")
    print(f"{len(all_dirs)} dirs and {len(all_files)} files left\n")

    return dir_dups, file_dups


def remove_unique(root):
    while True:
        if not root or not root in all_dirs:
            break

        if params.dirs_only:
            for path in all_roots[root]:
                if path in all_files:
                    del all_files[path]

        next_root = all_dirs[root]["root"]
        del all_dirs[root]
        root = next_root

    return


def remove_by_size():
    rm_dirs, rm_files = {}, {}

    if not params.files_only and (
        params.min_dir_size is not None or params.max_dir_size is not None
    ):
        for dir_path, dir_info in all_dirs.items():
            if (
                params.min_dir_size is not None
                and params.min_dir_size > dir_info["size"]
            ) or (
                params.max_dir_size is not None
                and params.max_dir_size < dir_info["size"]
            ):
                rm_dirs[dir_path] = True

    if params.min_file_size is not None or params.max_file_size is not None:
        for file_path, file_info in all_files.items():
            if (
                params.min_file_size is not None
                and params.min_file_size > file_info["size"]
            ) or (
                params.max_file_size is not None
                and params.max_file_size < file_info["size"]
            ):
                rm_files[file_path] = True

    if not params.files_only and len(rm_dirs):
        for dir_path in rm_dirs:
            del all_dirs[dir_path]
            if params.dirs_only:
                for file_path in all_roots[dir_path]:
                    rm_files[file_path] = True

    if len(rm_files):
        for file_path in rm_files:
            del all_files[file_path]

    return rm_dirs, rm_files


def remove_by_exclude(all_data, exclude):
    to_remove = []

    for path in all_data:
        if any(fnmatch.fnmatch(path, pattern) for pattern in exclude):
            to_remove.append(path)

    for path in to_remove:
        del all_data[path]

    return to_remove


def dirs_join(dir_dups):
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
    roots = defaultdict(list)
    for path, file in files.items():
        roots[file["root"]].append(path)

    return roots


def check(param):
    return param if param in params.check else ""


def action(dup_save, dups_act):
    if not (params.symlink or params.hardlink or params.delete):
        return False

    for dup in dups_act:
        if os.path.isfile(dup['path']):
            os.remove(dup['path'])
        elif os.path.isdir(dup['path']):
            shutil.rmtree(dup['path'])
        else:
            print("Invalid path:", dup['path'])

        if params.symlink:
            os.symlink(dup_save['path'], dup['path'])
        elif params.hardlink:
            os.link(dup_save['path'], dup['path'])

    return True


def get_params():
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
        "--stat",
        action="store_true",
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
        "--files-only",
        "-f",
        action="store_true",
        dest="files_only",
        help="Search only for duplicate files and skip directories",
    )
    parser.add_argument(
        "--dirs-only",
        "-d",
        action="store_true",
        dest="dirs_only",
        help="Search only for duplicate directories",
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
        "--process-empty",
        action="store_true",
        help="Process empty directories and files",
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

    args.min_file_size = parse_size(args.min_file_size) if args.min_file_size else 1
    args.max_file_size = parse_size(args.max_file_size) if args.max_file_size else None
    args.min_dir_size = parse_size(args.min_dir_size) if args.min_dir_size else 1
    args.max_dir_size = parse_size(args.max_dir_size) if args.max_dir_size else None

    if args.process_empty:
        args.min_dir_size = None
        args.min_file_size = None

    if args.no_combine:
        args.no_combine_files = True
        args.no_combine_dirs = True

    if args.exclude:
        args.exclude_dirs = args.exclude_dirs or []
        args.exclude_dirs.extend(args.exclude)

        args.exclude_files = args.exclude_files or []
        args.exclude_files.extend(args.exclude)

    return args


def init():
    if (
        params.min_dir_size is not None
        or params.max_dir_size is not None
        or params.min_file_size is not None
        or params.max_file_size is not None
    ):
        rm_dirs, rm_files = remove_by_size()
        print(
            f"Removed {len(rm_dirs)} directories and {len(rm_files)} files from list"
            + " that don't fit the size requirement"
        )
        print(f"{len(all_dirs)} dirs and {len(all_files)} files left\n")

    if params.exclude:
        rm_dirs = remove_by_exclude(all_dirs, params.exclude_dirs)
        rm_files = remove_by_exclude(all_files, params.exclude_files)

        print(
            f"Removed {len(rm_dirs)} directories and {len(rm_files)} files from list"
            + " that do not match the exclude patterns"
        )
        print(f"{len(all_dirs)} dirs and {len(all_files)} files left\n")

    print(
        "Now eliminating candidates based on "
        + ", ".join(
            item
            for item in [
                check("filename"),
                check("size"),
                check("date"),
            ]
            if item
        )
        + "..."
    )

    def func(file):
        res_str = "<"
        if check("filename"):
            res_str += str(file["name"]) + "/"
        if check("size"):
            res_str += str(file["size"]) + "/"
        if check("date"):
            res_str += str(file["date"]) + "/"
        res_str += ">"

        return res_str

    dir_dups, file_dups = get_duplicates(func)

    if check("firstbytes"):
        print("Now eliminating candidates based on first bytes...")

        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file, None, params.chunk)
            if file["size"] > params.chunk
            else get_file_hash(file)
        )
        if not params.no_cache:
            save_obj_to_temp_file(HASH_CACHE_FILE, hash_cache)

    if check("lastbytes"):
        print("Now eliminating candidates based on last bytes...")
        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file, -params.chunk)
            if file["size"] > params.chunk * 2
            else None
        )
        if not params.no_cache:
            save_obj_to_temp_file(HASH_CACHE_FILE, hash_cache)

    if check("hash"):
        print("Now eliminating candidates based on hash...")
        dir_dups, file_dups = get_duplicates(
            lambda file: get_file_hash(file) if file["size"] > params.chunk else None
        )
        if not params.no_cache:
            save_obj_to_temp_file(HASH_CACHE_FILE, hash_cache)

    print()

    final_dir_dups = dir_dups

    if not params.files_only:
        if not params.no_combine_dirs:
            print(f"Compacting {len(dir_dups)} groups of directories...")
            final_dir_dups = dirs_join(dir_dups)
            print(f"Now have {len(final_dir_dups)} groups of duplicate directories\n")

        if final_dir_dups and not params.stat:
            print("\n\nDuplicate directories:\n\n")
            for _, dups in final_dir_dups.items():
                dup_save = dups[0]
                dups_act = []

                print(format_date(dup_save["date"]), format_size(dup_save["size"]))
                print("  ✓", relpath(dup_save) + "/")

                for dup in dups[1:]:
                    dups_act.append(dup)
                    print("  ⨯", relpath(dup) + "/")

                action(dup_save, dups_act)
                print()

    if not params.dirs_only and len(file_dups) and not params.stat:
        print("\n\nDuplicate files:\n\n")
        for _, dups in file_dups.items():
            in_dirs = []
            in_free = []

            if not params.files_only:
                for dup in dups:
                    (in_dirs if dup["root"] in all_dirs else in_free).append(dup)
            else:
                in_free = dups

            if in_free or params.no_combine_files or params.files_only:
                dup_save = None
                dups_act = []

                if in_dirs:
                    dup_save = in_dirs[0]
                    print(format_date(dup_save["date"]), format_size(dup_save["size"]))
                    print("↳ ✓", relpath(dup_save))

                    for dup in in_dirs[1:]:
                        dups_act.append(dup)
                        print("↳ ⨯", relpath(dup))

                if dup_save:
                    for dup in in_free:
                        dups_act.append(dup)
                        print("  ⨯", relpath(dup))
                else:
                    dup_save = in_free[0]
                    print(format_date(dup_save["date"]), format_size(dup_save["size"]))
                    print("  ✓", relpath(dup_save))

                    for dup in in_free[1:]:
                        dups_act.append(dup)
                        print("  ⨯", relpath(dup))

                action(dup_save, dups_act)
                print()


params = get_params()

bench_times = []

HASH_CACHE_FILE = "dup.py.cache.pkl"
if not params.no_cache or not params.reset_cache:
    hash_cache = load_obj_from_file(HASH_CACHE_FILE)

if not hash_cache:
    hash_cache = {}

all_dirs, all_files = collect_all_data(params.directories)
all_roots = get_roots(all_files)

init()

if not params.no_cache:
    save_obj_to_temp_file(HASH_CACHE_FILE, hash_cache)
