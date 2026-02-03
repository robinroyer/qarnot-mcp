#!/usr/bin/env bash
# Send an MCP initialize request to the Qarnot MCP server
# and display the server description.
#
# Usage: ./scripts/test_initialize.sh [BASE_URL]
#   BASE_URL defaults to http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"

curl -s -X POST "${BASE_URL}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {
        "name": "curl-test",
        "version": "1.0.0"
      }
    }
  }'

echo
