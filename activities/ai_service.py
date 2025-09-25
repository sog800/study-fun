import requests
import os

API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_ai(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",  # model name
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
