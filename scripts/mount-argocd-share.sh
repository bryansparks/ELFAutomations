#!/bin/bash
#
# Mount ArgoCD machine's shared folder for Docker image transfer
#

# Configuration - UPDATE THESE!
ARGOCD_HOST="mac-mini.local"  # Or use IP like "192.168.1.100"
ARGOCD_USER="your-username"    # Username on ArgoCD machine
SHARE_NAME="docker-images"     # Name of the shared folder
LOCAL_MOUNT="/Volumes/argocd-docker-images"

echo "🔗 Mounting ArgoCD shared folder..."

# Create mount point if it doesn't exist
if [ ! -d "$LOCAL_MOUNT" ]; then
    echo "Creating mount point: $LOCAL_MOUNT"
    sudo mkdir -p "$LOCAL_MOUNT"
fi

# Check if already mounted
if mount | grep -q "$LOCAL_MOUNT"; then
    echo "✅ Already mounted at $LOCAL_MOUNT"
else
    # Mount the share
    echo "Mounting //$ARGOCD_HOST/$SHARE_NAME to $LOCAL_MOUNT"

    # Option 1: With password prompt
    mount_smbfs //$ARGOCD_USER@$ARGOCD_HOST/$SHARE_NAME "$LOCAL_MOUNT"

    # Option 2: With password in command (less secure)
    # mount_smbfs //$ARGOCD_USER:password@$ARGOCD_HOST/$SHARE_NAME "$LOCAL_MOUNT"

    if [ $? -eq 0 ]; then
        echo "✅ Successfully mounted!"
        ls -la "$LOCAL_MOUNT"
    else
        echo "❌ Mount failed. Check hostname/IP and credentials."
        exit 1
    fi
fi

echo ""
echo "📦 To transfer Docker images:"
echo "1. Save image: docker save elf-automations/executive-team:latest > $LOCAL_MOUNT/executive-team.tar"
echo "2. On ArgoCD machine: docker load < /Users/Shared/docker-images/executive-team.tar"
