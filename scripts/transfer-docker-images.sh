#!/bin/bash
#
# Transfer Docker images to ArgoCD machine via shared folder
#

set -e

# Configuration
MOUNT_POINT="/Volumes/argocd-docker-images"
IMAGES_TO_TRANSFER=(
    "elf-automations/executive-team:latest"
    # Add more images here as needed
)

echo "🚀 Docker Image Transfer to ArgoCD Machine"
echo "========================================"

# Step 1: Check if mounted
if ! mount | grep -q "$MOUNT_POINT"; then
    echo "❌ Shared folder not mounted. Running mount script..."
    ./scripts/mount-argocd-share.sh
    if [ $? -ne 0 ]; then
        echo "Failed to mount. Exiting."
        exit 1
    fi
fi

# Step 2: Transfer each image
for IMAGE in "${IMAGES_TO_TRANSFER[@]}"; do
    echo ""
    echo "📦 Processing: $IMAGE"

    # Check if image exists locally
    if docker image inspect "$IMAGE" >/dev/null 2>&1; then
        # Generate filename from image name
        FILENAME=$(echo "$IMAGE" | tr '/:' '-').tar
        FILEPATH="$MOUNT_POINT/$FILENAME"

        echo "   Saving to: $FILEPATH"
        docker save "$IMAGE" -o "$FILEPATH"

        if [ -f "$FILEPATH" ]; then
            SIZE=$(du -h "$FILEPATH" | cut -f1)
            echo "   ✅ Saved successfully ($SIZE)"

            echo ""
            echo "   On ArgoCD machine, run:"
            echo "   docker load < /Users/Shared/docker-images/$FILENAME"
        else
            echo "   ❌ Failed to save image"
        fi
    else
        echo "   ⚠️  Image not found locally, skipping"
    fi
done

# Step 3: Create a loader script for the ArgoCD machine
cat > "$MOUNT_POINT/load-all-images.sh" << 'EOF'
#!/bin/bash
# Run this on the ArgoCD machine to load all images

IMAGES_DIR="/Users/Shared/docker-images"

echo "Loading Docker images from $IMAGES_DIR..."

for tar_file in "$IMAGES_DIR"/*.tar; do
    if [ -f "$tar_file" ]; then
        echo "Loading: $(basename "$tar_file")"
        docker load < "$tar_file"
    fi
done

echo "Done! Verify with: docker images | grep elf-automations"
EOF

chmod +x "$MOUNT_POINT/load-all-images.sh"

echo ""
echo "✅ Transfer complete!"
echo ""
echo "📋 Next steps on ArgoCD machine:"
echo "1. cd /Users/Shared/docker-images"
echo "2. ./load-all-images.sh"
echo "3. kubectl rollout restart deployment/executive-team -n elf-teams"
