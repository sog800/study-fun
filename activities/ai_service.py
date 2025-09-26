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
