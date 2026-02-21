from openai import OpenAI
import requests
from config import OPENAI_API_KEY, MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

conversation = []

# === OpenAI ===
def ask_openai(text):
    conversation.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        model=MODEL,
        messages=conversation,
        max_tokens=200
    )

    answer = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": answer})
    return answer


# === Локальная LLM через Ollama ===
def ask_local_llm(text):
    prompt = f"""
Ты домашний голосовой ассистент.
Отвечай кратко.
Отвечай только на русском языке.
Не используй подписи типа "Best regards".
Вопрос пользователя: {text}
Ответ:
"""
    response = requests.post(
        "http://ollama:11434/api/generate",
        json={
            "model": "tinyllama",  #llama3
            "prompt": prompt,
            "stream": False,
             "options": {
                "num_predict": 120,
                "temperature": 0.7
            }
        },
        timeout=180
    )

    data = response.json()
    return data.get("response", "Локальная модель не ответила.")


# === Гибридный метод ===
def ask_ai(text):
    try:
        print("Пробуем OpenAI...")
        return ask_openai(text)

    except Exception as e:
        print("OpenAI недоступен:", e)

        try:
            print("Пробуем локальную LLM...")
            return ask_local_llm(text)

        except Exception as e2:
            print("Локальная LLM тоже недоступна:", e2)
            return "Сервис ИИ временно недоступен."