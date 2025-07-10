#!/bin/bash
# Script to fix the nested k8s/k8s directory structure

echo "This script will fix the nested k8s/k8s directory structure"
echo "Moving contents from infrastructure/k8s/k8s/ to infrastructure/k8s/"
echo ""

cd /Users/bryansparks/projects/ELFAutomations/infrastructure/k8s

# Check if nested k8s directory exists
if [ ! -d "k8s" ]; then
    echo "No nested k8s directory found. Nothing to do."
    exit 0
fi

echo "Moving directories..."

# Move each directory
for dir in k8s/*/; do
    if [ -d "$dir" ]; then
        dirname=$(basename "$dir")
        echo "Moving $dirname..."
        mv "$dir" "./"
    fi
done

# Remove the now-empty k8s directory
if [ -d "k8s" ]; then
    rmdir k8s 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Removed empty k8s directory"
    else
        echo "Could not remove k8s directory - it may not be empty"
    fi
fi

echo ""
echo "Done! New structure:"
ls -la

echo ""
echo "Summary of what was moved:"
echo "- data-stores/ (contains qdrant/)"
echo "- infrastructure/ (contains neo4j/, minio/)"
echo "- agentgateway/"
echo "- agents/"
echo "- apps/"
echo "- argocd-apps/"
echo "- base/"
echo "- kagent/"
echo "- mcps/"
echo "- n8n/"
echo "- operators/"
echo "- overlays/"
echo "- production/"
echo "- staging/"
echo "- teams/"
