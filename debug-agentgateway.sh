#!/bin/bash

echo "=== Debugging AgentGateway startup ==="
echo "Current working directory:"
pwd
echo ""

echo "Contents of /app/config:"
ls -la /app/config/
echo ""

echo "Contents of config.json:"
cat /app/config/config.json
echo ""

echo "Validating JSON:"
cat /app/config/config.json | jq .
echo ""

echo "Starting AgentGateway with debug output:"
RUST_LOG=debug agentgateway --file /app/config/config.json
