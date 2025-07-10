#!/usr/bin/env python3
"""
Script to fix the nested k8s/k8s directory structure by moving contents up one level
"""
import os
import shutil


def main():
    base_path = "/Users/bryansparks/projects/ELFAutomations/infrastructure/k8s"
    nested_path = os.path.join(base_path, "k8s")

    if not os.path.exists(nested_path):
        print(f"Nested directory {nested_path} does not exist. Nothing to do.")
        return

    # List all items in the nested k8s directory
    items = os.listdir(nested_path)

    print(f"Found {len(items)} items to move from {nested_path} to {base_path}")

    moved_items = []

    for item in items:
        src = os.path.join(nested_path, item)
        dst = os.path.join(base_path, item)

        # Check if destination already exists
        if os.path.exists(dst):
            print(f"WARNING: {dst} already exists. Skipping {item}")
            continue

        try:
            shutil.move(src, dst)
            moved_items.append(item)
            print(f"Moved: {item}")
        except Exception as e:
            print(f"ERROR moving {item}: {e}")

    # Try to remove the now-empty nested k8s directory
    try:
        os.rmdir(nested_path)
        print(f"\nRemoved empty directory: {nested_path}")
    except OSError as e:
        print(f"\nCould not remove {nested_path}: {e}")

    print(f"\nSuccessfully moved {len(moved_items)} items:")
    for item in sorted(moved_items):
        print(f"  - {item}")

    # Show the final structure
    print(f"\nFinal structure of {base_path}:")
    for item in sorted(os.listdir(base_path)):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            print(f"  - {item}/")
        else:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
