#!/bin/bash
echo "================================"
echo "   DevScan AI Setup"
echo "================================"
echo ""
echo "Step 1: Pulling AI model (5GB - first time only)..."
ollama pull qwen2.5-coder:7b
echo ""
echo "Step 2: Starting DevScan AI..."
ollama serve &
sleep 3
streamlit run app.py