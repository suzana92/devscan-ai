#!/bin/bash
echo "================================"
echo "   DevScan AI - First Time Setup"
echo "================================"
echo ""
echo "Step 1: Starting containers..."
docker compose up -d
echo ""
echo "Step 2: Waiting for Ollama..."
sleep 45
echo ""
echo "Step 3: Downloading AI model (9GB)..."
docker exec devscan-ollama ollama pull qwen2.5-coder:14b
echo ""
echo "Step 4: Restarting app..."
docker compose restart devscan
echo ""
echo "================================"
echo "DevScan AI is ready!"
echo "Open: http://localhost:8501"
echo "================================"