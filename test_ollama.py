import requests

# Send a message to Ollama running on your laptop
# Port 11434 is where Ollama listens — like a door number
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5-coder:7b",
        "prompt": "Write a Python function that adds two numbers. Keep it short.",
        "stream": False
    }
)

result = response.json()
print(result["response"])