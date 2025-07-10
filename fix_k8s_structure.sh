#!/bin/bash

# Fix the nested k8s/k8s directory structure

BASE_DIR="/Users/bryansparks/projects/ELFAutomations/infrastructure/k8s"
NESTED_DIR="$BASE_DIR/k8s"

echo "Moving directories from $NESTED_DIR to $BASE_DIR"

# Move all contents from nested k8s to parent k8s
mv "$NESTED_DIR"/* "$BASE_DIR/" 2>/dev/null

# Remove the now-empty nested directory
rmdir "$NESTED_DIR"

echo "Done! New structure:"
ls -la "$BASE_DIR"
