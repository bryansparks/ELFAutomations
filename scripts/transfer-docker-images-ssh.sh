#!/bin/bash
#
# Transfer Docker images via SSH (alternative to SMB mounting)
#

# Configuration - UPDATE THESE!
ARGOCD_HOST="192.168.6.5"  # Or IP address
ARGOCD_USER="bryan"
REMOTE_DIR="~/projects/ELFAutomations"

IMAGES_TO_TRANSFER=(
    "elf-automations/executive-team:latest"
    "elf-automations/general-team:latest"
    "elf-automations/google-drive-watcher:latest"
    "elf-automations/rag-processor-team:latest"
)

echo "🚀 Docker Image Transfer via SSH"
echo "================================"

# Create remote directory
echo "Creating remote directory..."
ssh $ARGOCD_USER@$ARGOCD_HOST "mkdir -p $REMOTE_DIR"

# Transfer each image
for IMAGE in "${IMAGES_TO_TRANSFER[@]}"; do
    echo ""
    echo "📦 Processing: $IMAGE"

    if docker image inspect "$IMAGE" >/dev/null 2>&1; then
        FILENAME=$(echo "$IMAGE" | tr '/:' '-').tar

        echo "   Saving and transferring..."
        # Save and transfer in one command using pipe
        docker save "$IMAGE" | ssh $ARGOCD_USER@$ARGOCD_HOST "cat > $REMOTE_DIR/$FILENAME"

        echo "   ✅ Transferred to $ARGOCD_HOST:$REMOTE_DIR/$FILENAME"

        # Load on remote machine
        echo "   Loading on remote machine..."
        ssh $ARGOCD_USER@$ARGOCD_HOST "docker load < $REMOTE_DIR/$FILENAME"

        # Clean up remote tar file
        ssh $ARGOCD_USER@$ARGOCD_HOST "rm $REMOTE_DIR/$FILENAME"

        echo "   ✅ Image loaded on ArgoCD machine"
    else
        echo "   ⚠️  Image not found locally"
    fi
done

echo ""
echo "✅ All done!"
echo "Verify on ArgoCD machine: docker images | grep elf-automations"
