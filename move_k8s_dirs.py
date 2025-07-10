#!/usr/bin/env python3
import os
import subprocess

base_dir = "/Users/bryansparks/projects/ELFAutomations/infrastructure/k8s"
nested_dir = os.path.join(base_dir, "k8s")

# Use subprocess to run mv command
print("Moving all contents from nested k8s directory...")
cmd = f'mv "{nested_dir}"/* "{base_dir}/"'
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error during move: {result.stderr}")
else:
    print("Move completed successfully")

# Remove the empty directory
print("Removing empty nested directory...")
try:
    os.rmdir(nested_dir)
    print("Directory removed successfully")
except Exception as e:
    print(f"Error removing directory: {e}")

# List the final structure
print("\nFinal structure of infrastructure/k8s/:")
items = sorted(os.listdir(base_dir))
for item in items:
    if os.path.isdir(os.path.join(base_dir, item)):
        print(f"  {item}/")
    else:
        print(f"  {item}")
