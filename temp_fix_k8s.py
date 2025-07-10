import os
import shutil

base_path = "/Users/bryansparks/projects/ELFAutomations/infrastructure/k8s"
nested_path = os.path.join(base_path, "k8s")

# Move each directory individually
directories_to_move = [
    "agentgateway",
    "agents",
    "apps",
    "argocd-apps",
    "base",
    "data-stores",
    "infrastructure",
    "kagent",
    "mcps",
    "n8n",
    "operators",
    "overlays",
    "production",
    "staging",
    "teams",
]

for dir_name in directories_to_move:
    src = os.path.join(nested_path, dir_name)
    dst = os.path.join(base_path, dir_name)

    if os.path.exists(src):
        try:
            shutil.move(src, dst)
            print(f"Moved: {dir_name}")
        except Exception as e:
            print(f"Error moving {dir_name}: {e}")
    else:
        print(f"Source not found: {src}")

# Remove the empty nested directory
try:
    os.rmdir(nested_path)
    print("Removed empty nested k8s directory")
except Exception as e:
    print(f"Error removing directory: {e}")

print("\nFinal structure:")
for item in sorted(os.listdir(base_path)):
    if os.path.isdir(os.path.join(base_path, item)):
        print(f"  {item}/")
    else:
        print(f"  {item}")
