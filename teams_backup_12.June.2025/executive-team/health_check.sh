#!/bin/bash
# Simple health check for K8s
curl -f http://localhost:8090/health || exit 1
